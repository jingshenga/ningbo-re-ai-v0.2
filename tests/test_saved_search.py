from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.models import SavedSearchIn
from app.services import listing_matches_search, saved_search_match_reasons


def search(**values):
    return SavedSearchIn(name='测试', **values).model_dump()


def listing(**values):
    row = {
        'district': '鄞州', 'community_name': '东湖花园',
        'asking_price_wan': Decimal('350'), 'area_sqm': Decimal('120'),
        'bedrooms': 3, 'last_observed_at': datetime.now(timezone.utc),
    }
    row.update(values)
    return row


def test_saved_search_hard_filters_and_exclusions():
    criteria = search(districts=['鄞州', '海曙'], max_price_wan=400,
                      min_area_sqm=100, min_bedrooms=3,
                      excluded_communities=['东湖花园'])
    assert not listing_matches_search(criteria, listing())
    assert listing_matches_search(criteria, listing(community_name='锦港府', district='海曙'))
    assert not listing_matches_search(criteria, listing(district='江北'))
    assert not listing_matches_search(criteria, listing(asking_price_wan=Decimal('401')))
    assert not listing_matches_search(criteria, listing(bedrooms=None))


def test_preferred_community_does_not_block_hard_match():
    criteria = search(preferred_communities=['锦港府'])
    assert listing_matches_search(criteria, listing(community_name='东湖花园'))
    assert listing_matches_search(criteria, listing(community_name='锦港府'))


def test_listing_freshness_uses_last_observed_time():
    criteria = search(max_listing_age_days=30)
    assert listing_matches_search(criteria, listing(last_observed_at=datetime.now(timezone.utc)-timedelta(days=29)))
    assert not listing_matches_search(criteria, listing(last_observed_at=datetime.now(timezone.utc)-timedelta(days=31)))


def test_saved_search_match_reasons_explain_applied_filters_and_preference():
    criteria = search(districts=['鄞州', '海曙'], community_name='东湖花园', max_price_wan=400,
                      min_area_sqm=100, min_bedrooms=3,
                      max_listing_age_days=30, preferred_communities=['东湖花园'])
    row = listing()

    assert saved_search_match_reasons(criteria, row) == [
        '区域匹配：鄞州',
        '小区匹配：东湖花园',
        '总价350万元，不超过上限400万元',
        '面积120㎡，达到下限100㎡',
        '户型3室，达到至少3室',
        '最近30天内有更新',
        '命中偏好小区：东湖花园',
    ]


def test_saved_search_match_reasons_have_generic_reason_without_constraints():
    assert saved_search_match_reasons(search(), listing()) == ['符合当前条件单筛选项']
