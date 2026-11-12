import pytest
from pydantic import ValidationError

from app.collection_models import DiscoveryStateIn


def test_discovery_state_deduplicates_ids_and_visited_pages_preserving_order():
    state = DiscoveryStateIn(
        source='beike', revision=0,
        seen_ids=['109900001234', '109900005678', '109900001234'],
        visited_page_urls=[
            'https://nb.ke.com/ershoufang/page1',
            'https://nb.ke.com/ershoufang/page2',
            'https://nb.ke.com/ershoufang/page1',
        ],
    )

    assert state.seen_ids == ['109900001234', '109900005678']
    assert state.visited_page_urls == [
        'https://nb.ke.com/ershoufang/page1',
        'https://nb.ke.com/ershoufang/page2',
    ]


@pytest.mark.parametrize('field,value', [
    ('revision', True),
    ('failed_attempts', True),
    ('version', True),
])
def test_discovery_state_rejects_boolean_in_integer_fields(field, value):
    with pytest.raises(ValidationError):
        DiscoveryStateIn(source='beike', **{field: value})


def test_discovery_state_error_field_accepts_type_names_only():
    with pytest.raises(ValidationError):
        DiscoveryStateIn(source='beike', last_error_type='timeout: /private/path')


def test_discovery_state_rejects_next_page_self_loop():
    page = 'https://nb.ke.com/ershoufang/page2'
    with pytest.raises(ValidationError, match='next_page_url must not repeat last_page_url'):
        DiscoveryStateIn(source='beike', revision=0,
                         last_page_url=page, next_page_url=page)


def test_discovery_state_rejects_next_page_authority_alias_loop():
    with pytest.raises(ValidationError, match='next_page_url must not repeat last_page_url'):
        DiscoveryStateIn(
            source='beike', revision=0,
            last_page_url='https://nb.ke.com/ershoufang/page1',
            next_page_url='https://NB.KE.COM:443/ershoufang/page1')


def test_discovery_state_allows_retry_cursor_after_failed_page():
    page = 'https://nb.ke.com/ershoufang/page2'
    state = DiscoveryStateIn(
        source='beike', revision=0,
        last_page_url='https://nb.ke.com/ershoufang/page1',
        next_page_url=page, last_attempted_page_url=page,
        last_error_type='TimeoutError', failed_attempts=1,
    )

    assert state.next_page_url == state.last_attempted_page_url
