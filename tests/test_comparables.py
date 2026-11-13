from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import app.comparables as comparables


class FakeConnection:
    def __init__(self, community=None, summary=None, listings=None, history=None):
        self.community = community
        self.summary = summary or {'sample_count': 0, 'p25': None, 'median': None,
                                   'p75': None, 'minimum': None, 'maximum': None}
        self.listings = listings or []
        self.history = history or []
        self.calls = []

    def execute(self, query, params=()):
        self.calls.append((query, params))
        if 'FROM communities c' in query:
            return FakeCursor([self.community] if self.community else [])
        if 'percentile_disc' in query:
            return FakeCursor([self.summary])
        if 'FROM source_listings l' in query:
            return FakeCursor(self.listings)
        if 'FROM (' in query and 'price_history' in query:
            return FakeCursor(self.history)
        raise AssertionError('unexpected SQL: ' + query)


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows


def use_connection(monkeypatch, connection):
    @contextmanager
    def fake_session():
        yield connection
    monkeypatch.setattr(comparables, 'session', fake_session)


def test_unknown_community_returns_insufficient_data_without_estimate(monkeypatch):
    connection = FakeConnection()
    use_connection(monkeypatch, connection)

    result = comparables.analyze_listings(
        '不存在的小区', Decimal('160'), asking_price_wan=Decimal('365')
    )

    assert result['status'] == 'insufficient_data'
    assert result['sample_count'] == 0
    assert result['comparable_asking_price_band_wan'] is None
    assert result['asking_price_position'] is None
    assert len(connection.calls) == 1


def test_below_minimum_sample_count_does_not_create_reference_band(monkeypatch):
    community = {'id': uuid4(), 'name': '东湖花园', 'district': '鄞州', 'verified': True}
    summary = {'sample_count': 4, 'p25': Decimal('2.1'), 'median': Decimal('2.2'),
               'p75': Decimal('2.3'), 'minimum': Decimal('2.0'), 'maximum': Decimal('2.5')}
    connection = FakeConnection(community=community, summary=summary)
    use_connection(monkeypatch, connection)

    result = comparables.analyze_listings(
        '东湖花园', Decimal('160'), asking_price_wan=Decimal('365')
    )

    assert result['status'] == 'insufficient_data'
    assert result['sample_count'] == 4
    assert result['unit_price_distribution_wan_per_sqm']['median'] == Decimal('2.2')
    assert result['comparable_asking_price_band_wan'] is None
    assert result['asking_price_position'] is None


def test_five_platform_listings_return_traceable_iqr_and_price_position(monkeypatch):
    community_id = uuid4()
    community = {'id': community_id, 'name': '东湖花园', 'district': '鄞州', 'verified': True}
    now = datetime(2026, 11, 13, tzinfo=timezone.utc)
    listing_id = uuid4()
    listing = {
        'listing_id': listing_id, 'source': 'beike', 'source_listing_id': '12345678',
        'title': '东湖花园样本', 'listing_url': 'https://example.test/listing',
        'asking_price_wan': Decimal('350'), 'status': 'available',
        'last_observed_at': now, 'area_sqm': Decimal('160'), 'bedrooms': 3,
        'floor_text': None, 'decoration': None,
        'asking_price_per_sqm_wan': Decimal('2.1875'),
        'area_deviation_pct': Decimal('0'),
    }
    history = [
        {'listing_id': listing_id, 'price_wan': Decimal('370'),
         'observed_at': datetime(2026, 10, 1, tzinfo=timezone.utc),
         'evidence_url': 'https://example.test/old'},
        {'listing_id': listing_id, 'price_wan': Decimal('350'),
         'observed_at': now, 'evidence_url': 'https://example.test/new'},
    ]
    summary = {'sample_count': 5, 'p25': Decimal('2.1'), 'median': Decimal('2.25'),
               'p75': Decimal('2.4'), 'minimum': Decimal('1.9'), 'maximum': Decimal('2.6')}
    connection = FakeConnection(community, summary, [listing], history)
    use_connection(monkeypatch, connection)

    result = comparables.analyze_listings(
        '东湖花园', Decimal('160'), 3, Decimal('10'), Decimal('365'), 30
    )

    assert result['status'] == 'sufficient_listing_evidence'
    assert result['sample_count'] == 5
    assert result['comparable_asking_price_band_wan'] == {
        'low': Decimal('336.00'), 'high': Decimal('384.00'),
        'basis': 'same_community_comparable_listing_interquartile_band',
        'is_transaction_estimate': False,
    }
    assert result['asking_price_position']['premium_to_comparable_median_pct'] == Decimal('1.39')
    assert result['comparables'][0]['retained_history_change']['change_wan'] == Decimal('-20')
    assert result['comparables'][0]['price_history'][0]['price_type'] == 'platform_listed_asking_price'
    history_sql, history_params = connection.calls[-1]
    assert "quote_type='platform_listed'" in history_sql
    assert 'agent_claim' not in history_sql
    assert history_params[0] == [listing_id]


def test_comparable_query_uses_bound_filters_and_exact_bedroom(monkeypatch):
    community = {'id': uuid4(), 'name': '东湖花园', 'district': '鄞州', 'verified': True}
    connection = FakeConnection(community=community)
    use_connection(monkeypatch, connection)

    comparables.analyze_listings("东湖花园' OR 1=1 --", Decimal('160'), 3,
                                 Decimal('10'), limit=7)

    community_sql, community_params = connection.calls[0]
    assert "东湖花园' OR 1=1 --" not in community_sql
    assert community_params == ("东湖花园' OR 1=1 --", "东湖花园' OR 1=1 --")
    aggregate_sql, aggregate_params = connection.calls[1]
    assert 'l.status NOT IN' in aggregate_sql
    assert 'l.source IN' in aggregate_sql
    assert 'p.bedrooms=%s' in aggregate_sql
    assert aggregate_params[-1] == 3
    listing_sql, listing_params = connection.calls[2]
    assert listing_params[-1] == 7
    assert 'LIMIT %s' in listing_sql


def test_reference_band_rounds_to_database_price_scale():
    assert comparables._money(Decimal('2.123') * Decimal('160')) == Decimal('339.68')
