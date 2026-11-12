"""Run a synthetic collection/review/listing workflow against an isolated API."""
import argparse
import asyncio
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import secrets
import time
from urllib.parse import urlsplit

import httpx


ALLOWED_API_HOSTS = {'api', 'localhost', '127.0.0.1', '::1'}


def validate_api_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme != 'http' or parsed.hostname not in ALLOWED_API_HOSTS or parsed.port not in (None, 8000):
        raise ValueError('API URL must point to the local test API (api, localhost, or loopback)')
    return value.rstrip('/')


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(len(ordered) * pct) - 1)
    return round(ordered[index], 2)


def sample_payload(sequence: int, run_id: int) -> dict:
    if not 1 <= sequence < 1_000_000:
        raise ValueError('sequence must be within the six-digit per-run limit')
    listing_id = f'{run_id:06d}{sequence:06d}'
    html = f'''<!doctype html><html lang="zh"><head><meta charset="utf-8">
      <meta property="og:title" content="合成负载样本 {sequence}"></head><body><main>
      <h1>合成负载样本 {sequence}</h1><p>小区：东湖花园</p><p>所在区域：鄞州</p>
      <p>建筑面积：158.60㎡</p><p>户型：4室2厅</p><p>总价：365万</p>
      <p>负载编号：{sequence}</p></main></body></html>'''
    return {
        'source': 'beike',
        'source_url': f'https://nb.ke.com/ershoufang/{listing_id}.html',
        'html': html,
        'note': 'synthetic isolated load test; no source website request',
    }


async def request(client, base_url, headers, operation, method, path, samples):
    started = time.perf_counter()
    try:
        response = await client.request(method, base_url + path, headers=headers)
    except Exception as exc:
        samples[operation].append((time.perf_counter() - started) * 1000)
        raise RuntimeError(type(exc).__name__) from None
    samples[operation].append((time.perf_counter() - started) * 1000)
    if response.status_code != 200:
        raise RuntimeError(f'HTTP {response.status_code}')
    return response.json()


async def post(client, base_url, headers, operation, path, payload, samples, params=None):
    started = time.perf_counter()
    try:
        request_options = {'headers': headers, 'params': params}
        if payload is not None:
            request_options['json'] = payload
        response = await client.post(base_url + path, **request_options)
    except Exception as exc:
        samples[operation].append((time.perf_counter() - started) * 1000)
        raise RuntimeError(type(exc).__name__) from None
    samples[operation].append((time.perf_counter() - started) * 1000)
    if response.status_code != 200:
        raise RuntimeError(f'HTTP {response.status_code}')
    return response.json()


async def workflow(client, base_url, headers, sequence, run_id, samples):
    payload = sample_payload(sequence, run_id)
    staged = await post(client, base_url, headers, 'import', '/api/collection/pages', payload, samples)
    candidate_id = staged['candidate']['id']
    pending = await request(client, base_url, headers, 'pending_candidates', 'GET',
                            '/api/collection/candidates?status=pending&source=beike&limit=200', samples)
    if not any(row['id'] == candidate_id for row in pending):
        raise RuntimeError('candidate_not_listed')

    reviewed = await post(client, base_url, headers, 'approve',
                          f'/api/collection/candidates/{candidate_id}/review', None, samples,
                          params={'decision': 'approve', 'note': 'synthetic load review'})
    listing_id = reviewed['listing_id']
    listings = await request(client, base_url, headers, 'listings', 'GET',
                             '/api/listings?limit=100', samples)
    source_listing_id = payload['source_url'].rsplit('/', 1)[-1].removesuffix('.html')
    if not any(row['source_listing_id'] == source_listing_id for row in listings):
        raise RuntimeError('approved_listing_not_listed')
    prices = await request(client, base_url, headers, 'price_history', 'GET',
                           f'/api/listings/{listing_id}/prices', samples)
    if not prices:
        raise RuntimeError('price_history_missing')
    health = await request(client, base_url, headers, 'health_metrics', 'GET',
                           '/api/collection/health', samples)
    beike = next((row for row in health if row['source'] == 'beike'), None)
    if not beike or beike['online_enabled'] or beike['global_online_enabled']:
        raise RuntimeError('collection_gate_unexpected')


async def run(args):
    base_url = validate_api_url(args.api_url)
    api_key = os.getenv('APP_API_KEY')
    if not api_key:
        raise ValueError('APP_API_KEY environment variable is required')
    headers = {'X-API-Key': api_key}
    samples = defaultdict(list)
    errors = Counter()
    completed = 0
    run_started_at = datetime.now(timezone.utc)
    started = time.monotonic()
    deadline = started + args.duration_seconds
    sequence = 0
    run_id = secrets.randbelow(900_000) + 100_000
    sequence_lock = asyncio.Lock()
    abort = asyncio.Event()

    async with httpx.AsyncClient(timeout=args.timeout_seconds) as client:
        async def worker():
            nonlocal sequence, completed
            while time.monotonic() < deadline and not abort.is_set():
                async with sequence_lock:
                    sequence += 1
                    current = sequence
                try:
                    await workflow(client, base_url, headers, current, run_id, samples)
                    completed += 1
                except Exception as exc:
                    errors[str(exc)] += 1
                    abort.set()

        await asyncio.gather(*(worker() for _ in range(args.concurrency)))

    elapsed = time.monotonic() - started
    endpoint_stats = {
        name: {
            'requests': len(values),
            'p50_ms': percentile(values, 0.50),
            'p95_ms': percentile(values, 0.95),
            'max_ms': round(max(values), 2) if values else None,
        }
        for name, values in sorted(samples.items())
    }
    report = {
        'started_at': run_started_at.isoformat(),
        'duration_seconds': round(elapsed, 2),
        'concurrency': args.concurrency,
        'completed_workflows': completed,
        'failed_workflows': sum(errors.values()),
        'error_counts': dict(errors),
        'requests': sum(len(values) for values in samples.values()),
        'endpoint_stats': endpoint_stats,
        'data_note': 'Synthetic fixture values only; source URLs were stored in the isolated DB and never fetched.',
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if errors else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--api-url', default='http://api:8000')
    parser.add_argument('--duration-seconds', type=int, default=1800)
    parser.add_argument('--concurrency', type=int, default=4)
    parser.add_argument('--timeout-seconds', type=float, default=30)
    parser.add_argument('--report', type=Path, default=Path('/tmp/collection-load-report.json'))
    args = parser.parse_args()
    if args.duration_seconds < 1 or args.concurrency < 1 or args.timeout_seconds <= 0:
        parser.error('duration, concurrency, and timeout must be positive')
    try:
        args.api_url = validate_api_url(args.api_url)
        raise SystemExit(asyncio.run(run(args)))
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
