from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from app import collection_service


class FakeConnection:
    def execute(self, query):
        assert "FROM source_registry s" in query
        assert "JOIN collection_health_metrics m" in query
        return self

    def fetchall(self):
        return [
            {'source': 'beike', 'success_count': 2, 'failure_count': 1,
             'blocked_count': 3, 'parse_attempt_count': 4,
             'parse_success_count': 3, 'complete_field_count': 2,
             'pending_count': 4, 'approved_count': 5,
             'rejected_count': 6, 'listing_count': 7, 'latest_status': 'blocked_policy'},
            {'source': 'anjuke', 'success_count': 0, 'failure_count': 0,
             'blocked_count': 0, 'parse_attempt_count': 0,
             'parse_success_count': 0, 'complete_field_count': 0,
             'pending_count': 0, 'approved_count': 0,
             'rejected_count': 0, 'listing_count': 0, 'latest_status': None},
        ]


def test_health_metrics_returns_per_source_counts_and_global_gate():
    @contextmanager
    def fake_session():
        yield FakeConnection()

    with patch.object(collection_service, 'session', fake_session), \
            patch.object(collection_service, 'ENABLE_ONLINE_COLLECTION', False):
        rows = collection_service.health_metrics()

    assert [row['source'] for row in rows] == ['beike', 'anjuke']
    assert rows[0]['pending_count'] == 4
    assert rows[0]['latest_status'] == 'blocked_policy'
    assert rows[1]['listing_count'] == 0
    assert all(row['global_online_enabled'] is False for row in rows)
    assert rows[0]['collection_success_rate_pct'] == 66.67
    assert rows[0]['parse_success_rate_pct'] == 75.0
    assert rows[0]['field_complete_rate_pct'] == 66.67
    assert rows[0]['approval_rate_pct'] == 45.45
    assert rows[1]['collection_success_rate_pct'] is None
    assert rows[1]['parse_success_rate_pct'] is None
    assert rows[1]['field_complete_rate_pct'] is None
    assert rows[1]['approval_rate_pct'] is None


def test_required_listing_fields_define_completeness():
    complete = {
        'source_listing_id': '109900001234', 'community_name': '东湖花园',
        'asking_price_wan': 350, 'area_sqm': 120,
    }
    assert collection_service._required_fields_complete(complete)
    assert not collection_service._required_fields_complete(
        {**complete, 'community_name': '  '})
    assert not collection_service._required_fields_complete(
        {key: value for key, value in complete.items() if key != 'area_sqm'})


def test_each_required_listing_field_is_mandatory():
    complete = {
        'source_listing_id': '109900001234', 'community_name': '东湖花园',
        'asking_price_wan': 350, 'area_sqm': 120,
    }
    for field in collection_service.REQUIRED_LISTING_FIELDS:
        assert not collection_service._required_fields_complete(
            {key: value for key, value in complete.items() if key != field})
        incomplete = {**complete, field: None}
        assert not collection_service._required_fields_complete(incomplete)
        if isinstance(complete[field], str):
            assert not collection_service._required_fields_complete(
                {**complete, field: '   '})


def test_parse_attempt_ledger_blocks_update_delete_and_truncate():
    migration = (Path(__file__).resolve().parents[1]
                 / 'sql' / '011_parse_attempts_append_only.sql').read_text()

    assert 'BEFORE UPDATE OR DELETE ON collection_parse_attempts' in migration
    assert 'BEFORE TRUNCATE ON collection_parse_attempts' in migration
    assert "RAISE EXCEPTION 'collection_parse_attempts is append-only'" in migration
