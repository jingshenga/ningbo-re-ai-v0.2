"""Real FFmpeg/RapidOCR API acceptance for the isolated NAS UAT container."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

import httpx
import psycopg

API_BASE = os.getenv('MEDIA_UPLOAD_API_BASE', 'http://127.0.0.1:8000').rstrip('/')
API_KEY = os.getenv('APP_API_KEY', '')
DATABASE_URL = os.getenv('DATABASE_URL', '')
SOURCE_VIDEO = Path(os.getenv(
    'NBRE_MEDIA_UAT_VIDEO',
    '/data/uat-media/nbre-nas-uat-zh-listing.mp4',
))
EXPECTED_SHA256 = os.getenv(
    'NBRE_MEDIA_UAT_VIDEO_SHA256',
    '3459916d8dadd12ab6056ac22ee47b3ef99a94cbfaf0ce56042d3363cbe1fe53',
)


def fail(message: str) -> None:
    raise SystemExit(message)


def protected_table_counts() -> dict[str, int]:
    if not DATABASE_URL:
        fail('DATABASE_URL is not configured for read-only isolation assertions')
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        conn.execute('SET default_transaction_read_only = on')
        database = conn.execute('SELECT current_database()').fetchone()[0]
        if database != 'rehouse_uat':
            fail('refusing to run against a non-UAT database')
        return {
            table: conn.execute('SELECT count(*) FROM ' + table).fetchone()[0]
            for table in ('videos', 'source_listings', 'price_history')
        }


def main() -> None:
    if not API_KEY:
        fail('APP_API_KEY is not configured')
    if not SOURCE_VIDEO.is_file() or SOURCE_VIDEO.is_symlink():
        fail('authorized synthetic MP4 is missing or unsafe: ' + str(SOURCE_VIDEO))
    source_sha = hashlib.sha256(SOURCE_VIDEO.read_bytes()).hexdigest()
    if EXPECTED_SHA256 and source_sha != EXPECTED_SHA256:
        fail('synthetic MP4 SHA-256 does not match the expected value')

    before = protected_table_counts()
    marker = uuid.uuid4().hex
    with tempfile.TemporaryDirectory(prefix='media-upload-uat-') as temp:
        video_file = Path(temp) / ('synthetic-' + marker + '.mp4')
        subprocess.run([
            'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
            '-i', str(SOURCE_VIDEO), '-map', '0', '-c', 'copy',
            '-metadata', 'comment=uat-' + marker, '-movflags', '+faststart',
            str(video_file),
        ], check=True, timeout=60, capture_output=True)

        headers = {'X-API-Key': API_KEY}
        form = {
            'source_type': 'operator_local',
            'permission_note': 'NAS隔离验收中使用本机生成的合成视频，不含真实房源素材。',
            'title': 'NAS隔离OCR合成验收 ' + marker[:8],
        }
        with httpx.Client(timeout=httpx.Timeout(30, read=600)) as client:
            with video_file.open('rb') as stream:
                uploaded = client.post(
                    API_BASE + '/api/media/uploads', headers=headers, data=form,
                    files={'file': (video_file.name, stream, 'video/mp4')},
                )
            if uploaded.status_code != 202:
                fail('upload rejected: HTTP %s %s' % (uploaded.status_code, uploaded.text[:300]))
            accepted = uploaded.json()
            if accepted.get('status') != 'queued':
                fail('uploaded job did not enter queued status')
            upload_id = accepted['upload_id']

            deadline = time.monotonic() + 600
            while time.monotonic() < deadline:
                response = client.get(
                    API_BASE + '/api/media/uploads/' + upload_id, headers=headers
                )
                response.raise_for_status()
                job = response.json()
                if job['status'] in ('completed', 'failed', 'failed_unavailable_ocr'):
                    break
                time.sleep(1)
            else:
                fail('upload processing did not reach a terminal status within 600 seconds')
            if job['status'] != 'completed':
                fail('media processing ended with %s: %s' % (job['status'], job.get('error')))

            result = job['result']
            if result['ocr']['status'] != 'ok' or result['ocr']['engine'] != 'rapidocr':
                fail('real RapidOCR was not used successfully')
            ocr_text = '\n'.join(item['text'] for item in result['ocr']['items'])
            hints = result['hints']
            assertions = {
                'community': '东湖花园' in ocr_text or '东湖花园' in hints['community_mentions'],
                'price': 365.0 in hints['price_mentions_wan'],
                'area': 160.0 in hints['area_mentions_sqm'],
                'bedrooms': 3 in hints['bedroom_mentions'],
                'uncalibrated': hints['confidence_status'] == 'not_calibrated',
            }
            if not all(assertions.values()):
                fail('OCR field assertions failed: ' + json.dumps(assertions, ensure_ascii=False))

            frame_url = result['ocr']['items'][0]['frame_url']
            if frame_url.startswith('/'):
                frame_url = API_BASE + frame_url
            frame = client.get(frame_url, headers=headers)
            if frame.status_code != 200 or not frame.content.startswith(b'\\xff\\xd8'):
                fail('authenticated OCR frame evidence was not readable')

            with video_file.open('rb') as duplicate_stream:
                duplicate = client.post(
                    API_BASE + '/api/media/uploads',
                    headers=headers,
                    data=form,
                    files={'file': (video_file.name, duplicate_stream, 'video/mp4')},
                )
            if (duplicate.status_code != 409 or
                    duplicate.json().get('error', {}).get('code') != 'duplicate_sha256'):
                fail('duplicate upload did not return duplicate_sha256')

    after = protected_table_counts()
    if before != after:
        fail('video upload changed videos/listings/price_history tables')
    print(json.dumps({
        'status': job['status'], 'initial_status': accepted['status'],
        'upload_id': upload_id, 'source_sha256': source_sha,
        'size_bytes': job['size_bytes'], 'ocr_engine': result['ocr']['engine'],
        'ocr_items': len(result['ocr']['items']), 'ocr_text': ocr_text,
        'hints': hints, 'field_assertions': assertions,
        'frame_evidence_http': frame.status_code, 'duplicate_http': duplicate.status_code,
        'protected_table_counts_unchanged': after,
        'price_handling': 'not_calibrated; no formal listing or transaction row created',
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
