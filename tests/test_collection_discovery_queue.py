from app import collection_service
from app.collectors.discovery import DiscoveryResult, DiscoveredListing
from app.collectors.http_client import CollectionBlocked
import pytest


def test_failed_detail_stays_queued_while_list_pagination_continues(monkeypatch):
    target = {
        'id': 'target-1',
        'source': 'beike',
        'url': 'https://nb.ke.com/ershoufang/',
    }
    state = collection_service._discovery_state('beike')
    stored_state = {}
    queue = {}
    staged = set()
    attempted_urls = []
    fail_first_detail = True
    listings = (
        DiscoveredListing('109900001234', 'https://nb.ke.com/ershoufang/109900001234.html'),
        DiscoveredListing('109900005678', 'https://nb.ke.com/ershoufang/109900005678.html'),
    )

    def fetch(source, url):
        nonlocal fail_first_detail
        attempted_urls.append(url)
        if url == listings[0].url and fail_first_detail:
            fail_first_detail = False
            raise OSError('temporary detail timeout')
        return '<html><body>saved page</body></html>'

    def next_item(target_id, attempted_ids):
        return next((item for item in queue.values()
                     if item['source_listing_id'] not in attempted_ids), None)

    def enqueue(target_arg, page_url, found):
        for listing in found:
            if listing.source_listing_id not in staged:
                queue.setdefault(listing.source_listing_id, {
                    'source_listing_id': listing.source_listing_id,
                    'listing_url': listing.url,
                })

    def save(target_id, current):
        current['revision'] += 1
        stored_state.clear()
        stored_state.update(current)
        return current

    def finish(target_id, current):
        current['completed_sweeps'] += 1
        current['sweep_active'] = False
        return save(target_id, current)

    monkeypatch.setattr(collection_service, 'get_discovery_state',
                        lambda *_args, **_kwargs: dict(stored_state) if stored_state else dict(state))
    monkeypatch.setattr(collection_service, '_fetch_approved_html', fetch)
    monkeypatch.setattr(collection_service, 'discover_listing_links',
                        lambda *_args: DiscoveryResult(listings, listings, None, ()))
    monkeypatch.setattr(collection_service, '_record_listing_observations', lambda *_: None)
    monkeypatch.setattr(collection_service, '_staged_listing_ids',
                        lambda _target_id, ids: set(ids) & staged)
    monkeypatch.setattr(collection_service, '_enqueue_discovery_listings', enqueue)
    monkeypatch.setattr(collection_service, '_next_discovery_queue_item', next_item)
    monkeypatch.setattr(collection_service, '_delete_discovery_queue_item',
                        lambda _target_id, listing_id: queue.pop(listing_id, None))
    monkeypatch.setattr(collection_service, '_record_discovery_queue_failure',
                        lambda _target_id, listing_id, _error:
                        queue[listing_id].update(attempt_count=1,last_error_type='OSError'))
    monkeypatch.setattr(collection_service, '_mark_discovery_listing_staged',
                        lambda _target_id, listing_id: staged.add(listing_id) or True)
    monkeypatch.setattr(collection_service, 'stage_html', lambda *_: {'candidate': {'id': 'candidate'}})
    monkeypatch.setattr(collection_service, '_save_target_discovery_state', save)
    monkeypatch.setattr(collection_service, '_finish_discovery_sweep', finish)

    first = collection_service._run_discovery_target(target)

    assert first[0] == 'failed'
    assert 'detail_failures=1' in first[2]
    assert attempted_urls == [target['url'], listings[0].url, listings[1].url]
    assert set(queue) == {listings[0].source_listing_id}
    assert stored_state['next_page_url'] is None
    assert stored_state['completed_sweeps'] == 1

    attempted_urls.clear()
    second = collection_service._run_discovery_target(target)

    assert second[0] == 'success'
    assert attempted_urls == [
        listings[0].url,
        target['url'],
    ]
    assert queue == {}
    assert staged == {item.source_listing_id for item in listings}
    assert stored_state['completed_sweeps'] == 2


@pytest.mark.parametrize('http_status', [403, 429])
def test_upstream_restriction_stops_detail_queue_without_retrying_other_urls(
        monkeypatch, http_status):
    target = {'id': 'target-1', 'source': 'beike'}
    state = collection_service._discovery_state('beike')
    queue = [
        {'source_listing_id': '109900001234',
         'listing_url': 'https://nb.ke.com/ershoufang/109900001234.html'},
        {'source_listing_id': '109900005678',
         'listing_url': 'https://nb.ke.com/ershoufang/109900005678.html'},
    ]
    fetches = []
    failures = []
    cursor_failures = []

    def blocked_fetch(_source, url):
        fetches.append(url)
        raise CollectionBlocked('upstream restriction', 'blocked_upstream', http_status)

    monkeypatch.setattr(collection_service, '_next_discovery_queue_item',
                        lambda *_: queue[0])
    monkeypatch.setattr(collection_service, '_staged_listing_ids', lambda *_: set())
    monkeypatch.setattr(collection_service, '_fetch_approved_html', blocked_fetch)
    monkeypatch.setattr(collection_service, '_record_discovery_queue_failure',
                        lambda _target_id, listing_id, error:
                        failures.append((listing_id,type(error).__name__)))
    monkeypatch.setattr(collection_service, '_record_target_discovery_failure',
                        lambda _target_id, _state, page_url, error:
                        cursor_failures.append((page_url,type(error).__name__)))

    attempts, staged, failed, blocked = collection_service._drain_discovery_detail_queue(
        target,state,'https://nb.ke.com/ershoufang/',set(),20)

    assert attempts == 0
    assert staged == 0
    assert failed == 0
    assert blocked.category == 'blocked_upstream'
    assert fetches == [queue[0]['listing_url']]
    assert failures == [('109900001234','CollectionBlocked')]
    assert cursor_failures == [('https://nb.ke.com/ershoufang/','CollectionBlocked')]
