from datetime import datetime, timedelta, timezone
from decimal import Decimal
from contextlib import contextmanager

import pytest
from fastapi import HTTPException

import app.services as services
from app.services import opportunities, same_listing_price_drop


def price(days_ago, price, quote_type='platform_listed'):
    return {
        'observed_at': datetime(2026, 11, 10, tzinfo=timezone.utc) - timedelta(days=days_ago),
        'price_wan': Decimal(str(price)),
        'quote_type': quote_type,
        'evidence_url': 'https://example.test/listing',
    }


def test_price_drop_uses_only_platform_listed_rows_in_closed_window():
    through = datetime(2026, 11, 10, tzinfo=timezone.utc)
    cutoff = through - timedelta(days=30)
    history = [
        price(10, 400),
        price(5, 200, 'agent_claim'),
        price(1, 360),
        price(-1, 100),
        price(31, 1000),
    ]

    drop = same_listing_price_drop(history, cutoff, through)
    assert drop['pct'] == 10.0
    assert drop['amount_wan'] == Decimal('40')
    assert drop['from_price_wan'] == Decimal('400')
    assert drop['to_price_wan'] == Decimal('360')
    assert drop['to_observed_at'] == through - timedelta(days=1)
    assert drop['evidence_url'] == 'https://example.test/listing'


def test_price_drop_uses_first_and_latest_in_window_and_never_reports_increase():
    through = datetime(2026, 11, 10, tzinfo=timezone.utc)
    cutoff = through - timedelta(days=30)
    history = [price(20, 400), price(10, 380), price(2, 390)]

    assert same_listing_price_drop(history, cutoff, through)['pct'] == 2.5
    assert same_listing_price_drop([price(20, 300), price(2, 350)], cutoff, through) is None


def test_price_drop_requires_two_platform_listed_observations():
    through = datetime(2026, 11, 10, tzinfo=timezone.utc)
    cutoff = through - timedelta(days=30)
    assert same_listing_price_drop([price(1, 300)], cutoff, through) is None
    assert same_listing_price_drop([price(1, 300, 'agent_claim')], cutoff, through) is None


def test_opportunities_only_accepts_product_windows():
    with pytest.raises(HTTPException) as exc:
        opportunities(days=365)

    assert exc.value.status_code == 422


def test_opportunities_sql_excludes_agent_listings_and_nonplatform_quotes(monkeypatch):
    now = datetime.now(timezone.utc)
    statements = []
    listing = {
        'id': 'listing-1', 'property_id': 'property-1', 'source': 'beike', 'source_listing_id': 'bk-1',
        'title': '样本', 'asking_price_wan': Decimal('360'),
        'last_observed_at': now, 'listing_url': None, 'area_sqm': Decimal('120'),
        'bedrooms': 3, 'community_id': 'community-1',
        'community_name': '小区', 'district': '鄞州',
    }
    history = [
        {'listing_id': 'listing-1', 'price_wan': Decimal('400'),
         'observed_at': now - timedelta(days=10), 'quote_type': 'platform_listed',
         'evidence_url': 'https://example.test/price-old'},
        {'listing_id': 'listing-1', 'price_wan': Decimal('200'),
         'observed_at': now - timedelta(days=5), 'quote_type': 'agent_claim',
         'evidence_url': 'https://example.test/agent-claim'},
        {'listing_id': 'listing-1', 'price_wan': Decimal('360'),
         'observed_at': now, 'quote_type': 'platform_listed',
         'evidence_url': 'https://example.test/price-current'},
    ]

    class Cursor:
        def __init__(self, rows):
            self.rows = rows

        def fetchall(self):
            return self.rows

    class Connection:
        def execute(self, query, params=()):
            sql = ' '.join(query.split())
            statements.append(sql)
            return Cursor([listing] if 'FROM source_listings' in sql else history)

    @contextmanager
    def fake_session():
        yield Connection()

    monkeypatch.setattr(services, 'session', fake_session)
    result = opportunities()

    assert result[0]['drop_pct_in_window'] == 10.0
    assert result[0]['drop_amount_wan'] == Decimal('40')
    assert result[0]['drop_from_price_wan'] == Decimal('400')
    assert result[0]['drop_to_price_wan'] == Decimal('360')
    assert result[0]['drop_evidence_url'] == 'https://example.test/price-current'
    assert any("l.source<>'agent'" in sql for sql in statements)
    assert any("quote_type='platform_listed'" in sql and 'observed_at <= %s' in sql
               for sql in statements)


def test_opportunities_sql_excludes_future_listings(monkeypatch):
    statements = []

    class Cursor:
        def fetchall(self):
            return []

    class Connection:
        def execute(self, query, params=()):
            statements.append(' '.join(query.split()))
            return Cursor()

    @contextmanager
    def fake_session():
        yield Connection()

    monkeypatch.setattr(services, 'session', fake_session)

    assert opportunities() == []
    listing_query = next(sql for sql in statements if 'FROM source_listings' in sql)
    assert 'l.last_observed_at <= now()' in listing_query


def test_opportunities_load_price_history_once_for_multiple_listings(monkeypatch):
    now = datetime.now(timezone.utc)
    listings = [
        {**target_listing(), 'id': f'listing-{index}', 'property_id': f'property-{index}',
         'last_observed_at': now}
        for index in range(3)
    ]
    history_queries = []

    class Cursor:
        def __init__(self, rows):
            self.rows = rows

        def fetchall(self):
            return self.rows

    class Connection:
        def execute(self, query_text, params=()):
            if 'FROM price_history' in query_text:
                history_queries.append(query_text)
            return Cursor(listings if 'FROM source_listings' in query_text else [])

    @contextmanager
    def fake_session():
        yield Connection()

    monkeypatch.setattr(services, 'session', fake_session)
    opportunities()

    assert len(history_queries) == 1


def run_opportunities_with_listings(monkeypatch, listings):
    class Cursor:
        def __init__(self, rows):
            self.rows = rows

        def fetchall(self):
            return self.rows

    class Connection:
        def execute(self, query, params=()):
            return Cursor(listings if 'FROM source_listings' in query else [])

    @contextmanager
    def fake_session():
        yield Connection()

    monkeypatch.setattr(services, 'session', fake_session)
    return opportunities()


def target_listing():
    now = datetime.now(timezone.utc)
    return {
        'id': 'target-listing', 'property_id': 'target-property', 'source': 'beike',
        'source_listing_id': 'target', 'title': '目标', 'asking_price_wan': Decimal('70'),
        'last_observed_at': now, 'listing_url': None, 'area_sqm': Decimal('100'),
        'bedrooms': 3, 'community_id': 'community-1', 'community_name': '小区',
        'district': '鄞州',
    }


def test_opportunities_require_five_distinct_comparable_properties(monkeypatch):
    target = target_listing()
    comparables = [
        {**target, 'id': f'listing-{index}', 'property_id': f'property-{index // 2}',
         'source_listing_id': f'listing-{index}', 'asking_price_wan': Decimal('100')}
        for index in range(1, 6)
    ]

    assert run_opportunities_with_listings(monkeypatch, [target, *comparables]) == []


def test_opportunities_do_not_compare_listings_with_unknown_bedroom_counts(monkeypatch):
    target = target_listing()
    target['bedrooms'] = None
    comparables = [
        {**target, 'id': f'comparable-{index}', 'property_id': f'property-{index}',
         'source_listing_id': f'comparable-{index}', 'asking_price_wan': Decimal('100')}
        for index in range(5)
    ]

    assert run_opportunities_with_listings(monkeypatch, [target, *comparables]) == []


@pytest.mark.parametrize(('area', 'include_target'), [
    (Decimal('89.99'), False), (Decimal('90'), True),
    (Decimal('110'), True), (Decimal('110.01'), False),
])
def test_comparable_area_threshold_uses_exact_ten_percent_boundary(monkeypatch, area, include_target):
    target = target_listing()
    comparables = [
        {**target, 'id': f'comparable-{index}', 'property_id': f'property-{index}',
         'source_listing_id': f'comparable-{index}', 'area_sqm': area,
         'asking_price_wan': area}
        for index in range(5)
    ]

    result = run_opportunities_with_listings(monkeypatch, [target, *comparables])

    target_opportunities = [item for item in result if item['listing_id'] == target['id']]
    assert bool(target_opportunities) is include_target
    if include_target:
        assert target_opportunities[0]['comparable_sample_count'] == 5
        assert target_opportunities[0]['discount_vs_raw_listing_median_pct'] > 0


def test_opportunities_weight_each_property_once(monkeypatch):
    target = target_listing()
    duplicate_property = [
        {**target, 'id': f'duplicate-{index}', 'property_id': 'duplicate-property',
         'source_listing_id': f'duplicate-{index}', 'asking_price_wan': Decimal(str(500 + index * 20))}
        for index in range(10)
    ]
    other_properties = [
        {**target, 'id': f'other-{index}', 'property_id': f'other-property-{index}',
         'source_listing_id': f'other-{index}', 'asking_price_wan': Decimal('100')}
        for index in range(4)
    ]

    result = run_opportunities_with_listings(monkeypatch, [target, *duplicate_property, *other_properties])

    assert result[0]['listing_id'] == 'target-listing'
    assert result[0]['comparable_sample_count'] == 5
    assert result[0]['discount_vs_raw_listing_median_pct'] == 30.0


def test_opportunities_explain_comparable_discount_and_data_time(monkeypatch):
    target = target_listing()
    comparables = [
        {**target, 'id': f'comparable-{index}', 'property_id': f'property-{index}',
         'source_listing_id': f'comparable-{index}', 'asking_price_wan': Decimal('100')}
        for index in range(5)
    ]

    result = run_opportunities_with_listings(monkeypatch, [target, *comparables])

    assert len(result) == 1
    opportunity = result[0]
    assert opportunity['listing_id'] == 'target-listing'
    assert opportunity['unit_price_wan_per_sqm'] == 0.7
    assert opportunity['comparable_median_wan_per_sqm'] == 1.0
    assert opportunity['comparable_sample_count'] == 5
    assert opportunity['last_observed_at'] == target['last_observed_at']
    assert any('挂牌单价0.70万元/㎡' in reason and '5套' in reason
               for reason in opportunity['signal_reasons'])


@pytest.mark.parametrize(('target_area', 'target_price', 'peer_area', 'peer_price'), [
    (Decimal('100'), Decimal('100'), Decimal('105'), Decimal('115.5')),
    (Decimal('105'), Decimal('105'), Decimal('100'), Decimal('110')),
    (Decimal('7'), Decimal('100'), Decimal('7'), Decimal('110')),
])
def test_cross_platform_price_gap_uses_low_quote_baseline_and_inclusive_threshold(
        monkeypatch, target_area, target_price, peer_area, peer_price):
    target = target_listing()
    target.update({'area_sqm': target_area, 'asking_price_wan': target_price})
    peer = {
        **target, 'id': 'anjuke-listing', 'property_id': 'anjuke-property',
        'source': 'anjuke', 'source_listing_id': 'aj-1',
        'area_sqm': peer_area, 'asking_price_wan': peer_price,
        'last_observed_at': target['last_observed_at'] - timedelta(hours=1),
        'listing_url': 'https://example.test/anjuke',
    }

    result = run_opportunities_with_listings(monkeypatch, [target, peer])

    assert len(result) == 2
    for opportunity in result:
        assert 'cross_platform_price_gap' in opportunity['signals']
        gap = opportunity['cross_platform_price_gaps'][0]
        assert gap['unit_price_gap_pct'] == 10.0
        expected_area_gap = abs(target_area-peer_area)/min(target_area,peer_area)*100
        assert gap['area_difference_pct'] == round(float(expected_area_gap), 2)
        assert gap['verification_status'] == 'candidate'
        assert '待核实' in next(reason for reason in opportunity['signal_reasons']
                               if '跨平台' in reason)


def test_cross_platform_price_gap_excludes_value_just_below_ten_percent(monkeypatch):
    target = target_listing()
    target.update({'area_sqm': Decimal('100'), 'asking_price_wan': Decimal('100')})
    peer = {
        **target, 'id': 'anjuke-listing', 'property_id': 'anjuke-property',
        'source': 'anjuke', 'source_listing_id': 'aj-1',
        'asking_price_wan': Decimal('109.999'),
    }

    assert run_opportunities_with_listings(monkeypatch, [target, peer]) == []


def test_cross_platform_gap_excludes_same_source_wrong_bedrooms_area_or_small_gap(monkeypatch):
    target = target_listing()
    excluded = [
        {**target, 'id': 'same-source', 'source_listing_id': 'same-source',
         'asking_price_wan': Decimal('70')},
        {**target, 'id': 'wrong-bedroom', 'property_id': 'wrong-bedroom', 'source': 'anjuke',
         'bedrooms': 2, 'asking_price_wan': Decimal('90')},
        {**target, 'id': 'area-mismatch', 'property_id': 'area-mismatch', 'source': 'anjuke',
         'area_sqm': Decimal('106'), 'asking_price_wan': Decimal('95')},
        {**target, 'id': 'small-gap', 'property_id': 'small-gap', 'source': 'anjuke',
         'asking_price_wan': Decimal('74')},
        {**target, 'id': 'unknown-bedroom', 'property_id': 'unknown-bedroom', 'source': 'anjuke',
         'bedrooms': None, 'asking_price_wan': Decimal('90')},
    ]

    assert run_opportunities_with_listings(monkeypatch, [target, *excluded]) == []


def test_cross_platform_gap_excludes_other_communities(monkeypatch):
    target = target_listing()
    other_community = {
        **target, 'id': 'other-community-listing', 'property_id': 'other-community-property',
        'source': 'anjuke', 'source_listing_id': '1000001', 'community_id': 'community-2',
        'asking_price_wan': Decimal('100'),
    }

    assert run_opportunities_with_listings(monkeypatch, [target, other_community]) == []
