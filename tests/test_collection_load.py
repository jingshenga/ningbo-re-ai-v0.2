import asyncio
import json
from types import SimpleNamespace

import pytest

from app.collectors import parse_listing_html
from scripts import collection_load
from scripts.collection_load import percentile, sample_payload, validate_api_url


def test_load_script_restricts_target_to_local_api():
    assert validate_api_url('http://api:8000/') == 'http://api:8000'
    assert validate_api_url('http://127.0.0.1:8000') == 'http://127.0.0.1:8000'
    with pytest.raises(ValueError):
        validate_api_url('https://example.com')
    with pytest.raises(ValueError):
        validate_api_url('http://example.com:8000')


def test_synthetic_payload_is_unique_and_reviewable():
    first = sample_payload(1, 123456)
    second = sample_payload(2, 123456)
    assert first['source_url'] != second['source_url']
    parsed = parse_listing_html(first['source'], first['source_url'], first['html'])
    assert parsed.ready_for_review
    assert parsed.fields['source_listing_id'] == '123456000001'
    assert parsed.fields['community_name'] == '东湖花园'


def test_percentile_uses_nearest_rank_and_empty_samples():
    assert percentile([1, 2, 3, 4], 0.50) == 2
    assert percentile([1, 2, 3, 4], 0.95) == 4
    assert percentile([], 0.95) is None


def test_load_stops_workers_after_first_failed_workflow(tmp_path, monkeypatch):
    monkeypatch.setenv('APP_API_KEY', 'synthetic-test-key')

    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return False

    calls = 0

    async def fail(*_):
        nonlocal calls
        calls += 1
        raise RuntimeError('synthetic_failure')

    monkeypatch.setattr(collection_load.httpx, 'AsyncClient', lambda **_: Client())
    monkeypatch.setattr(collection_load, 'workflow', fail)
    report_path = tmp_path / 'report.json'
    args = SimpleNamespace(api_url='http://api:8000', timeout_seconds=1,
                           duration_seconds=30, concurrency=4, report=report_path)

    assert asyncio.run(collection_load.run(args)) == 1
    assert calls == 1
    assert json.loads(report_path.read_text())['failed_workflows'] == 1
