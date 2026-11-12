from contextlib import contextmanager
import gzip
import hashlib
from pathlib import Path

import pytest
from fastapi import HTTPException

from app import collection_service
from app.collectors.parser import PARSER_VERSION
from app.collection_models import CandidateCorrection


class FakeResult:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self, rows):
        self.rows = iter(rows)
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))
        return FakeResult(next(self.rows))


def fake_session(connection):
    @contextmanager
    def session_context():
        yield connection
    return session_context


def fake_session_sequence(*connections):
    remaining = iter(connections)

    @contextmanager
    def session_context():
        yield next(remaining)
    return session_context


@pytest.fixture(autouse=True)
def mock_listing_observation_persistence(monkeypatch):
    queue = {}
    staged_ids = set()

    def record(target, state, page_url, html, listings):
        state['sweep_seen_ids'] = sorted(
            set(state['sweep_seen_ids']) | {item.source_listing_id for item in listings})

    def finish(target_id, state):
        state['completed_sweeps'] += 1
        state['sweep_active'] = False
        return state

    monkeypatch.setattr(collection_service, '_record_listing_observations', record)
    monkeypatch.setattr(collection_service, '_finish_discovery_sweep', finish)
    monkeypatch.setattr(collection_service, '_staged_listing_ids',
                        lambda _target_id, ids: set(ids) & staged_ids)
    monkeypatch.setattr(collection_service, '_mark_discovery_listing_staged', lambda *_: False)

    def enqueue(target, page_url, listings):
        for item in listings:
            if item.source_listing_id not in staged_ids:
                queue.setdefault(item.source_listing_id, {
                    'source_listing_id': item.source_listing_id,
                    'listing_url': item.url,
                })

    monkeypatch.setattr(collection_service, '_enqueue_discovery_listings', enqueue)
    monkeypatch.setattr(
        collection_service, '_next_discovery_queue_item',
        lambda _target_id, attempted: next(
            (item for item in queue.values()
             if item['source_listing_id'] not in attempted), None))
    monkeypatch.setattr(collection_service, '_delete_discovery_queue_item',
                        lambda _target_id, listing_id: (
                            queue.pop(listing_id, None), staged_ids.add(listing_id)))
    monkeypatch.setattr(collection_service, '_record_discovery_queue_failure',
                        lambda *_: None)


@pytest.mark.parametrize('stored_content', [
    b'corrupt gzip', gzip.compress(b'<html>different evidence</html>'),
])
def test_save_html_repairs_invalid_existing_content_addressed_file(
        tmp_path, monkeypatch, stored_content):
    html = '<html><body>synthetic evidence</body></html>'
    digest = hashlib.sha256(html.encode('utf-8')).hexdigest()
    folder = tmp_path / 'raw-pages'
    folder.mkdir()
    evidence = folder / f'{digest}.html.gz'
    evidence.write_bytes(stored_content)
    monkeypatch.setattr(collection_service, 'RAW_HTML_DIR', str(folder))

    saved_path = collection_service._save_html(digest, html)

    assert gzip.decompress(Path(saved_path).read_bytes()) == html.encode('utf-8')


def test_save_html_replaces_symlink_at_content_addressed_path(tmp_path, monkeypatch):
    html = '<html><body>synthetic evidence</body></html>'
    digest = hashlib.sha256(html.encode('utf-8')).hexdigest()
    folder = tmp_path / 'raw-pages'
    folder.mkdir()
    outside = tmp_path / 'outside.html.gz'
    outside.write_bytes(gzip.compress(html.encode('utf-8')))
    evidence = folder / f'{digest}.html.gz'
    evidence.symlink_to(outside)
    monkeypatch.setattr(collection_service, 'RAW_HTML_DIR', str(folder))

    saved_path = Path(collection_service._save_html(digest, html))

    assert not saved_path.is_symlink()
    assert gzip.decompress(saved_path.read_bytes()) == html.encode('utf-8')


def test_save_html_refuses_symlinked_storage_directory(tmp_path, monkeypatch):
    external = tmp_path / 'external'
    external.mkdir()
    folder = tmp_path / 'raw-pages'
    folder.symlink_to(external, target_is_directory=True)
    monkeypatch.setattr(collection_service, 'RAW_HTML_DIR', str(folder))

    with pytest.raises(collection_service.CollectionError, match='must not be a symlink'):
        collection_service._save_html('a' * 64, '<html><body>evidence</body></html>')

    assert list(external.iterdir()) == []


@pytest.mark.parametrize('global_enabled,source_enabled,policy_status,reference', [
    (False, True, 'approved', 'permission-id'),
    (True, False, 'approved', 'permission-id'),
    (True, True, 'not_reviewed', 'permission-id'),
    (True, True, 'approved', '   '),
])
def test_online_target_is_blocked_before_fetch_without_full_permission_gate(
        monkeypatch, global_enabled, source_enabled, policy_status, reference):
    policy_row = {'online_enabled': source_enabled,
                  'online_policy_status': policy_status,
                  'policy_reference': reference}
    connection = FakeConnection(([None, None] if not global_enabled
                                 else [policy_row, None, None]))
    monkeypatch.setattr(collection_service, 'session', fake_session(connection))
    monkeypatch.setattr(collection_service, 'ENABLE_ONLINE_COLLECTION', global_enabled)
    fetch_calls = []

    def fetch(*args, **kwargs):
        fetch_calls.append((args, kwargs))
        raise AssertionError('fetch must not run when policy gate is closed')

    monkeypatch.setattr(collection_service, 'fetch_public_html', fetch)
    target = {
        'id': 'target-1', 'source': 'beike',
        'url': 'https://nb.ke.com/ershoufang/109900001234.html',
        'source_enabled': source_enabled,
        'online_policy_status': policy_status,
        'policy_reference': reference,
    }

    assert collection_service.run_collection_target(target) == 'blocked_policy'
    assert fetch_calls == []
    run_call = next(call for call in connection.calls if 'INSERT INTO collection_runs' in call[0])
    assert run_call[1][3] == 'blocked_policy'


def test_revoked_policy_after_target_claim_blocks_fetch(monkeypatch):
    policy_connection = FakeConnection([{
        'online_enabled': False,
        'online_policy_status': 'revoked',
        'policy_reference': 'old-permission-id',
    }])
    log_connection = FakeConnection([None, None])
    connections = iter((policy_connection, log_connection))

    @contextmanager
    def session_factory():
        connection = next(connections)
        connection.active = True
        try:
            yield connection
        finally:
            connection.active = False

    monkeypatch.setattr(collection_service, 'session', session_factory)
    monkeypatch.setattr(collection_service, 'ENABLE_ONLINE_COLLECTION', True)
    fetch_calls = []

    def fetch(*args, **kwargs):
        fetch_calls.append((args, kwargs))
        raise AssertionError('revoked permission must block the stale target')

    monkeypatch.setattr(collection_service, 'fetch_public_html', fetch)
    target = {
        'id': 'target-1', 'source': 'beike',
        'url': 'https://nb.ke.com/ershoufang/109900001234.html',
        'source_enabled': True,
        'online_policy_status': 'approved',
        'policy_reference': 'old-permission-id',
    }

    assert collection_service.run_collection_target(target) == 'blocked_policy'
    assert fetch_calls == []
    assert 'FOR SHARE' not in policy_connection.calls[0][0]
    assert log_connection.calls[0][1][3] == 'blocked_policy'


def test_approved_policy_lock_is_released_before_fetch_and_staging(monkeypatch):
    policy_connection = FakeConnection([{
        'online_enabled': True,
        'online_policy_status': 'approved',
        'policy_reference': 'written-permission-id',
    }])
    log_connection = FakeConnection([None, None])
    connections = iter((policy_connection, log_connection))

    @contextmanager
    def session_factory():
        connection = next(connections)
        connection.active = True
        try:
            yield connection
        finally:
            connection.active = False

    monkeypatch.setattr(collection_service, 'session', session_factory)
    monkeypatch.setattr(collection_service, 'ENABLE_ONLINE_COLLECTION', True)
    fetch_calls = []
    stage_calls = []

    def fetch(*args, **kwargs):
        assert policy_connection.active is False
        fetch_calls.append((args, kwargs))
        return '<html>synthetic approved-source response</html>'

    def stage(source, url, html, method):
        assert policy_connection.active is False
        stage_calls.append((source, url, html, method))
        return {'candidate': {'id': 'candidate-1'}}

    monkeypatch.setattr(collection_service, 'fetch_public_html', fetch)
    monkeypatch.setattr(collection_service, 'stage_html', stage)
    target = {
        'id': 'target-1', 'source': 'beike',
        'url': 'https://nb.ke.com/ershoufang/109900001234.html',
    }

    assert collection_service.run_collection_target(target) == 'success'
    assert len(fetch_calls) == 1
    assert stage_calls[0][3] == 'public_page_collection'
    assert 'FOR SHARE' not in policy_connection.calls[0][0]
    assert policy_connection.active is False
    assert log_connection.calls[0][1][3] == 'success'


def test_policy_revocation_stops_the_next_discovery_request(monkeypatch):
    policy_rows = [
        {'online_enabled': True, 'online_policy_status': 'approved',
         'policy_reference': 'permission-record'},
        {'online_enabled': True, 'online_policy_status': 'approved',
         'policy_reference': 'permission-record'},
        {'online_enabled': True, 'online_policy_status': 'approved',
         'policy_reference': 'permission-record'},
        {'online_enabled': False, 'online_policy_status': 'revoked',
         'policy_reference': 'permission-record'},
    ]
    log_connection = FakeConnection([None, None])
    active_connections = []

    @contextmanager
    def session_factory():
        if policy_rows:
            connection = FakeConnection([policy_rows.pop(0)])
            connection.active = True
            active_connections.append(connection)
        else:
            connection = log_connection
        try:
            yield connection
        finally:
            if connection is not log_connection:
                connection.active = False

    monkeypatch.setattr(collection_service, 'session', session_factory)
    monkeypatch.setattr(collection_service, 'ENABLE_ONLINE_COLLECTION', True)
    list_url = 'https://nb.ke.com/ershoufang/'
    detail_one = 'https://nb.ke.com/ershoufang/109900001234.html'
    detail_two = 'https://nb.ke.com/ershoufang/109900001235.html'
    page = (f'<main><a href="{detail_one}">one</a>'
            f'<a href="{detail_two}">two</a></main>')
    fetch_calls = []
    saved_states = []

    def fetch(source, url, **kwargs):
        assert all(connection.active is False for connection in active_connections)
        kwargs['before_page_request']()
        fetch_calls.append(url)
        return page if url == list_url else '<main>detail</main>'

    monkeypatch.setattr(collection_service, 'fetch_public_html', fetch)
    monkeypatch.setattr(collection_service, 'stage_html',
                        lambda *args: {'candidate': {'id': 'candidate-1'}})
    def save_state(target_id, payload):
        saved = payload.model_dump()
        saved['revision'] += 1
        saved_states.append(saved)
        return saved

    monkeypatch.setattr(collection_service, 'get_discovery_state', lambda _, **kwargs: {
        'version': 1, 'revision': 0, 'source': 'beike', 'seen_ids': [],
        'last_page_url': None, 'next_page_url': None, 'visited_page_urls': [],
        'last_attempted_page_url': None, 'last_error_type': None, 'failed_attempts': 0,
    })
    monkeypatch.setattr(collection_service, 'save_discovery_state', save_state)

    status = collection_service.run_collection_target(
        {'id': 'target-1', 'source': 'beike', 'url': list_url})

    assert status == 'blocked_policy'
    assert fetch_calls == [list_url]
    assert len(saved_states) == 1
    assert saved_states[0]['sweep_number'] == 1
    assert saved_states[0]['sweep_active'] is True
    assert saved_states[0]['next_page_url'] == list_url
    assert saved_states[0]['seen_ids'] == []
    assert saved_states[0]['sweep_seen_ids'] == ['109900001234', '109900001235']
    assert len(active_connections) == 4
    assert all(connection.active is False for connection in active_connections)
    assert log_connection.calls[0][1][3] == 'blocked_policy'


def test_approved_list_target_paginates_and_stages_detail_pages(monkeypatch):
    log_connection = FakeConnection([None, None])

    @contextmanager
    def session_factory():
        yield log_connection

    monkeypatch.setattr(collection_service, 'session', session_factory)
    monkeypatch.setattr(collection_service, '_require_online_policy', lambda *_: None)
    monkeypatch.setattr(collection_service, 'ENABLE_ONLINE_COLLECTION', True)
    list_url = 'https://nb.ke.com/ershoufang/'
    page_two = 'https://nb.ke.com/ershoufang/page2'
    listing_urls = [
        'https://nb.ke.com/ershoufang/109900001234.html',
        'https://nb.ke.com/ershoufang/109900001235.html',
    ]
    pages = {
        list_url: (f'<main><a href="{listing_urls[0]}">listing 1</a>'
                   f'<a href="{page_two}" rel="next">next</a></main>'),
        page_two: f'<main><a href="{listing_urls[1]}">listing 2</a></main>',
        listing_urls[0]: '<main>detail 1</main>',
        listing_urls[1]: '<main>detail 2</main>',
    }
    fetch_calls = []
    staged_urls = []
    saved_states = []

    def fetch(source, url, **kwargs):
        fetch_calls.append(url)
        return pages[url]

    def stage(source, url, html, method):
        staged_urls.append((url, method))
        return {'candidate': {'id': f'candidate-{len(staged_urls)}'}}

    def save_state(target_id, payload):
        saved = payload.model_dump()
        saved['revision'] += 1
        saved_states.append(saved)
        return saved

    monkeypatch.setattr(collection_service, 'get_discovery_state', lambda _, **kwargs: {
        'version': 1, 'revision': 0, 'source': 'beike', 'seen_ids': [],
        'last_page_url': None, 'next_page_url': None, 'visited_page_urls': [],
        'last_attempted_page_url': None, 'last_error_type': None, 'failed_attempts': 0,
    })
    monkeypatch.setattr(collection_service, 'save_discovery_state', save_state)
    monkeypatch.setattr(collection_service, 'fetch_public_html', fetch)
    monkeypatch.setattr(collection_service, 'stage_html', stage)
    target = {'id': 'target-1', 'source': 'beike', 'url': list_url}

    assert collection_service.run_collection_target(target) == 'success'
    assert fetch_calls == [list_url, listing_urls[0], page_two, listing_urls[1]]
    assert staged_urls == [(url, 'public_page_collection') for url in listing_urls]
    assert len(saved_states) == 2
    assert saved_states[-1]['last_page_url'] == page_two
    assert saved_states[-1]['next_page_url'] is None
    assert saved_states[-1]['visited_page_urls'] == [list_url, page_two]
    assert saved_states[-1]['seen_ids'] == ['109900001234', '109900001235']
    assert log_connection.calls[0][1][3] == 'success'


def test_approved_list_target_stops_on_cross_page_loop_without_completing_sweep(monkeypatch):
    log_connection = FakeConnection([None, None])

    @contextmanager
    def session_factory():
        yield log_connection

    monkeypatch.setattr(collection_service, 'session', session_factory)
    monkeypatch.setattr(collection_service, '_require_online_policy', lambda *_: None)
    monkeypatch.setattr(collection_service, 'ENABLE_ONLINE_COLLECTION', True)
    page_one = 'https://nb.ke.com/ershoufang/page1'
    page_two = 'https://nb.ke.com/ershoufang/page2'
    pages = {
        page_one: f'<main><a rel="next" href="{page_two}">next</a></main>',
        page_two: f'<main><a rel="next" href="{page_one}">back</a></main>',
    }
    fetch_calls = []
    saved_states = []

    def save_state(target_id, payload):
        saved = payload.model_dump()
        saved['revision'] += 1
        saved_states.append(saved)
        return saved

    monkeypatch.setattr(collection_service, 'get_discovery_state', lambda _, **kwargs: {
        'version': 1, 'revision': 0, 'source': 'beike', 'seen_ids': [],
        'last_page_url': None, 'next_page_url': None, 'visited_page_urls': [],
        'last_attempted_page_url': None, 'last_error_type': None, 'failed_attempts': 0,
    })
    monkeypatch.setattr(collection_service, 'save_discovery_state', save_state)

    def fetch(source, url, **kwargs):
        fetch_calls.append(url)
        return pages[url]

    monkeypatch.setattr(collection_service, 'fetch_public_html', fetch)
    target = {'id': 'target-1', 'source': 'beike', 'url': page_one}

    assert collection_service.run_collection_target(target) == 'success'
    assert fetch_calls == [page_one, page_two]
    assert saved_states[-2]['visited_page_urls'] == [page_one, page_two]
    assert saved_states[-2]['next_page_url'] is None
    assert saved_states[-1]['sweep_active'] is False
    assert saved_states[-1]['completed_sweeps'] == 0
    assert 'pagination_loop' in log_connection.calls[0][1][6]
    assert 'sweep_incomplete' in log_connection.calls[0][1][6]


def test_approved_list_target_advances_page_when_detail_limit_is_reached(monkeypatch):
    log_connection = FakeConnection([None, None])

    @contextmanager
    def session_factory():
        yield log_connection

    monkeypatch.setattr(collection_service, 'session', session_factory)
    monkeypatch.setattr(collection_service, '_require_online_policy', lambda *_: None)
    monkeypatch.setattr(collection_service, 'ENABLE_ONLINE_COLLECTION', True)
    list_url = 'https://nb.ke.com/ershoufang/'
    listing_urls = [f'https://nb.ke.com/ershoufang/{109900000000 + index}.html'
                    for index in range(21)]
    html = '<main>' + ''.join(f'<a href="{url}">listing</a>' for url in listing_urls) + '</main>'
    fetch_calls = []
    saved_states = []

    def fetch(source, url, **kwargs):
        fetch_calls.append(url)
        return html if url == list_url else '<main>detail</main>'

    def save_state(target_id, payload):
        saved = payload.model_dump()
        saved['revision'] += 1
        saved_states.append(saved)
        return saved

    monkeypatch.setattr(collection_service, 'get_discovery_state', lambda _, **kwargs: {
        'version': 1, 'revision': 0, 'source': 'beike', 'seen_ids': [],
        'last_page_url': None, 'next_page_url': None, 'visited_page_urls': [],
        'last_attempted_page_url': None, 'last_error_type': None, 'failed_attempts': 0,
    })
    monkeypatch.setattr(collection_service, 'save_discovery_state', save_state)
    monkeypatch.setattr(collection_service, 'fetch_public_html', fetch)
    monkeypatch.setattr(collection_service, 'stage_html', lambda *args: {'candidate': {'id': 'candidate'}})
    target = {'id': 'target-1', 'source': 'beike', 'url': list_url}

    assert collection_service.run_collection_target(target) == 'success'
    assert len(fetch_calls) == 1 + collection_service.MAX_DISCOVERY_DETAILS_PER_RUN
    assert len(saved_states) == 1
    assert saved_states[0]['next_page_url'] is None
    assert saved_states[0]['visited_page_urls'] == [list_url]
    assert len(saved_states[0]['seen_ids']) == collection_service.MAX_DISCOVERY_DETAILS_PER_RUN


def test_exact_detail_limit_preserves_next_page_and_resumes_without_duplicates(monkeypatch):
    log_connection = FakeConnection([None, None, None, None])

    @contextmanager
    def session_factory():
        yield log_connection

    monkeypatch.setattr(collection_service, 'session', session_factory)
    monkeypatch.setattr(collection_service, '_require_online_policy', lambda *_: None)
    monkeypatch.setattr(collection_service, 'ENABLE_ONLINE_COLLECTION', True)
    page_one = 'https://nb.ke.com/ershoufang/page1'
    page_two = 'https://nb.ke.com/ershoufang/page2'
    listing_urls = [
        f'https://nb.ke.com/ershoufang/{109900001000 + index}.html'
        for index in range(collection_service.MAX_DISCOVERY_DETAILS_PER_RUN)
    ]
    next_listing = 'https://nb.ke.com/ershoufang/109900009999.html'
    pages = {
        page_one: ('<main>'
                   + ''.join(f'<a href="{url}">listing</a>' for url in listing_urls)
                   + f'<a rel="next" href="{page_two}">next</a></main>'),
        page_two: f'<main><a href="{next_listing}">next listing</a></main>',
    }
    persisted_states = []
    fetch_calls = []
    staged_urls = []

    def get_state(_, **kwargs):
        if persisted_states:
            return persisted_states[-1].copy()
        return {
            'version': 1, 'revision': 0, 'source': 'beike', 'seen_ids': [],
            'last_page_url': None, 'next_page_url': None, 'visited_page_urls': [],
            'last_attempted_page_url': None, 'last_error_type': None, 'failed_attempts': 0,
        }

    def save_state(target_id, payload):
        saved = payload.model_dump()
        saved['revision'] += 1
        persisted_states.append(saved)
        return saved

    def finish_sweep(target_id, state):
        state['completed_sweeps'] += 1
        state['sweep_active'] = False
        state['revision'] += 1
        persisted_states.append(state.copy())
        return state

    def fetch(source, url, **kwargs):
        fetch_calls.append(url)
        return pages[url] if url in pages else '<main>detail</main>'

    def stage(source, url, html, method):
        staged_urls.append(url)
        return {'candidate': {'id': f'candidate-{len(staged_urls)}'}}

    monkeypatch.setattr(collection_service, 'get_discovery_state', get_state)
    monkeypatch.setattr(collection_service, 'save_discovery_state', save_state)
    monkeypatch.setattr(collection_service, '_finish_discovery_sweep', finish_sweep)
    monkeypatch.setattr(collection_service, 'fetch_public_html', fetch)
    monkeypatch.setattr(collection_service, 'stage_html', stage)
    target = {'id': 'target-1', 'source': 'beike', 'url': page_one}

    assert collection_service.run_collection_target(target) == 'success'
    first_run_state = persisted_states[-1]
    assert first_run_state['next_page_url'] == page_two
    assert first_run_state['sweep_active'] is True
    assert first_run_state['completed_sweeps'] == 0
    assert first_run_state['seen_ids'] == [url.rsplit('/', 1)[-1][:-5]
                                            for url in listing_urls]
    assert staged_urls == listing_urls

    assert collection_service.run_collection_target(target) == 'success'
    final_state = persisted_states[-1]
    assert fetch_calls == [page_one, *listing_urls, page_two, next_listing]
    assert staged_urls == [*listing_urls, next_listing]
    assert final_state['next_page_url'] is None
    assert final_state['sweep_active'] is False
    assert final_state['completed_sweeps'] == 1, persisted_states
    assert final_state['sweep_seen_ids'] == sorted(
        [url.rsplit('/', 1)[-1][:-5] for url in listing_urls] + ['109900009999'])


def test_page_limit_detail_limit_and_policy_retry_preserve_seen_ids(monkeypatch):
    from app.collectors.http_client import CollectionBlocked

    monkeypatch.setattr(collection_service, 'MAX_DISCOVERY_PAGES_PER_RUN', 1)
    monkeypatch.setattr(collection_service, 'MAX_DISCOVERY_DETAILS_PER_RUN', 2)
    monkeypatch.setattr(collection_service, 'ENABLE_ONLINE_COLLECTION', True)
    monkeypatch.setattr(collection_service, '_require_online_policy', lambda *_: None)
    log_connection = FakeConnection([None] * 6)

    @contextmanager
    def session_factory():
        yield log_connection

    monkeypatch.setattr(collection_service, 'session', session_factory)
    page_one = 'https://nb.ke.com/ershoufang/page1'
    page_two = 'https://nb.ke.com/ershoufang/page2'
    first_page_listings = [
        'https://nb.ke.com/ershoufang/109900001001.html',
        'https://nb.ke.com/ershoufang/109900001002.html',
    ]
    second_page_listings = [
        'https://nb.ke.com/ershoufang/109900001003.html',
        'https://nb.ke.com/ershoufang/109900001004.html',
    ]
    pages = {
        page_one: ('<main>'
                   + ''.join(f'<a href="{url}">listing</a>'
                             for url in first_page_listings)
                   + f'<a rel="next" href="{page_two}">next</a></main>'),
        page_two: ('<main>'
                   + ''.join(f'<a href="{url}">listing</a>'
                             for url in second_page_listings)
                   + '</main>'),
    }
    persisted_states = []
    fetch_calls = []
    staged_urls = []
    block_second_page_detail = {'enabled': True}

    def get_state(_, **kwargs):
        if persisted_states:
            return persisted_states[-1].copy()
        return {
            'version': 1, 'revision': 0, 'source': 'beike', 'seen_ids': [],
            'last_page_url': None, 'next_page_url': None, 'visited_page_urls': [],
            'last_attempted_page_url': None, 'last_error_type': None, 'failed_attempts': 0,
        }

    def save_state(target_id, payload):
        saved = payload.model_dump()
        saved['revision'] += 1
        persisted_states.append(saved)
        return saved

    def finish_sweep(target_id, state):
        state['completed_sweeps'] += 1
        state['sweep_active'] = False
        state['revision'] += 1
        persisted_states.append(state.copy())
        return state

    def fetch(source, url, **kwargs):
        fetch_calls.append(url)
        if url in pages:
            return pages[url]
        if url == second_page_listings[1] and block_second_page_detail['enabled']:
            raise CollectionBlocked('policy revoked', 'blocked_policy')
        return '<main>detail</main>'

    def stage(source, url, html, method):
        staged_urls.append(url)
        return {'candidate': {'id': f'candidate-{len(staged_urls)}'}}

    monkeypatch.setattr(collection_service, 'get_discovery_state', get_state)
    monkeypatch.setattr(collection_service, 'save_discovery_state', save_state)
    monkeypatch.setattr(collection_service, '_finish_discovery_sweep', finish_sweep)
    monkeypatch.setattr(collection_service, 'fetch_public_html', fetch)
    monkeypatch.setattr(collection_service, 'stage_html', stage)
    target = {'id': 'target-1', 'source': 'beike', 'url': page_one}

    assert collection_service.run_collection_target(target) == 'success'
    first_run_state = persisted_states[-1]
    assert first_run_state['next_page_url'] == page_two
    assert first_run_state['sweep_active'] is True
    assert first_run_state['completed_sweeps'] == 0
    assert first_run_state['seen_ids'] == [url.rsplit('/', 1)[-1][:-5]
                                            for url in first_page_listings]

    assert collection_service.run_collection_target(target) == 'blocked_policy'
    blocked_state = persisted_states[-1]
    assert blocked_state['next_page_url'] == page_two
    assert blocked_state['last_page_url'] == page_one
    assert blocked_state['seen_ids'] == [
        url.rsplit('/', 1)[-1][:-5] for url in first_page_listings + second_page_listings[:1]
    ]
    assert blocked_state['sweep_active'] is True
    assert blocked_state['completed_sweeps'] == 0

    block_second_page_detail['enabled'] = False
    assert collection_service.run_collection_target(target) == 'success'
    final_state = persisted_states[-1]
    assert fetch_calls == [page_one, *first_page_listings, page_two,
                           *second_page_listings[:1], second_page_listings[1],
                           second_page_listings[1], page_two]
    assert staged_urls == first_page_listings + second_page_listings
    assert final_state['seen_ids'] == sorted(
        url.rsplit('/', 1)[-1][:-5]
        for url in first_page_listings + second_page_listings)
    assert final_state['sweep_seen_ids'] == final_state['seen_ids']
    assert final_state['completed_sweeps'] == 1
    assert final_state['sweep_active'] is False


def test_approved_list_target_records_blocked_detail_for_retry(monkeypatch):
    from app.collectors.http_client import CollectionBlocked

    log_connection = FakeConnection([None, None])

    @contextmanager
    def session_factory():
        yield log_connection

    monkeypatch.setattr(collection_service, 'session', session_factory)
    monkeypatch.setattr(collection_service, '_require_online_policy', lambda *_: None)
    monkeypatch.setattr(collection_service, 'ENABLE_ONLINE_COLLECTION', True)
    list_url = 'https://nb.ke.com/ershoufang/'
    page_two = 'https://nb.ke.com/ershoufang/page2'
    first_url = 'https://nb.ke.com/ershoufang/109900001234.html'
    blocked_url = 'https://nb.ke.com/ershoufang/109900001235.html'
    html = f'<main><a href="{first_url}">first</a><a href="{blocked_url}">blocked</a></main>'
    saved_states = []
    fetch_calls = []

    def fetch(source, url, **kwargs):
        fetch_calls.append(url)
        if url == blocked_url:
            raise CollectionBlocked('blocked', 'blocked_upstream', 429)
        return html if url == list_url else '<main>detail</main>'

    def save_state(target_id, payload):
        saved = payload.model_dump()
        saved['revision'] += 1
        saved_states.append(saved)
        return saved

    monkeypatch.setattr(collection_service, 'get_discovery_state', lambda _, **kwargs: {
        'version': 1, 'revision': 0, 'source': 'beike', 'seen_ids': [],
        'last_page_url': page_two, 'next_page_url': None,
        'visited_page_urls': [list_url, page_two],
        'last_attempted_page_url': None, 'last_error_type': None, 'failed_attempts': 0,
    })
    monkeypatch.setattr(collection_service, 'save_discovery_state', save_state)
    monkeypatch.setattr(collection_service, 'fetch_public_html', fetch)
    monkeypatch.setattr(collection_service, 'stage_html', lambda *args: {'candidate': {'id': 'candidate'}})

    status = collection_service.run_collection_target(
        {'id': 'target-1', 'source': 'beike', 'url': list_url})

    assert status == 'blocked_upstream'
    assert fetch_calls == [list_url, first_url, blocked_url]
    assert saved_states[0]['seen_ids'] == ['109900001234']
    assert saved_states[0]['next_page_url'] == list_url
    assert saved_states[0]['last_page_url'] is None
    assert saved_states[0]['visited_page_urls'] == []
    assert saved_states[0]['last_error_type'] == 'CollectionBlocked'
    assert saved_states[0]['failed_attempts'] == 1
    assert log_connection.calls[0][1][3] == 'blocked_upstream'
    assert log_connection.calls[0][1][4] == 429
    target_update = next(call for call in log_connection.calls
                         if 'UPDATE collection_targets' in call[0])
    assert "WHEN %s IN ('blocked_robots','blocked_upstream') THEN FALSE" in target_update[0]
    assert target_update[1][2] == 'blocked_upstream'


def test_policy_revoked_after_staged_detail_persists_completed_id(monkeypatch):
    from app.collectors.http_client import CollectionBlocked

    log_connection = FakeConnection([None, None, None, None])
    monkeypatch.setattr(collection_service, 'session', fake_session(log_connection))
    monkeypatch.setattr(collection_service, 'ENABLE_ONLINE_COLLECTION', True)
    list_url = 'https://nb.ke.com/ershoufang/'
    first_url = 'https://nb.ke.com/ershoufang/109900001234.html'
    revoked_url = 'https://nb.ke.com/ershoufang/109900001235.html'
    html = f'<main><a href="{first_url}">first</a><a href="{revoked_url}">second</a></main>'
    saved_states = []
    fetch_calls = []
    staged_urls = []
    permission_revoked = {'value': True}

    def fetch(source, url):
        fetch_calls.append(url)
        if url == list_url:
            return html
        if url == revoked_url and permission_revoked['value']:
            raise CollectionBlocked('permission revoked', 'blocked_policy')
        return '<main>detail</main>'

    def save_state(target_id, payload):
        saved = payload.model_dump()
        saved['revision'] += 1
        saved_states.append(saved)
        return saved

    monkeypatch.setattr(collection_service, '_fetch_approved_html', fetch)
    initial_state = {
        'version': 1, 'revision': 0, 'source': 'beike', 'seen_ids': [],
        'last_page_url': None, 'next_page_url': None, 'visited_page_urls': [],
        'last_attempted_page_url': None, 'last_error_type': None, 'failed_attempts': 0,
    }
    monkeypatch.setattr(collection_service, 'get_discovery_state',
                        lambda _, **kwargs: dict(saved_states[-1]) if saved_states
                        else dict(initial_state))
    monkeypatch.setattr(collection_service, 'save_discovery_state', save_state)
    monkeypatch.setattr(collection_service, 'stage_html',
                        lambda source, url, html, method: staged_urls.append(url))

    status = collection_service.run_collection_target(
        {'id': 'target-1', 'source': 'beike', 'url': list_url})

    assert status == 'blocked_policy'
    assert fetch_calls == [list_url, first_url, revoked_url]
    assert staged_urls == [first_url]
    assert len(saved_states) == 1
    assert saved_states[0]['seen_ids'] == ['109900001234']
    assert saved_states[0]['next_page_url'] == list_url
    assert saved_states[0]['last_attempted_page_url'] == list_url
    assert saved_states[0]['failed_attempts'] == 0

    permission_revoked['value'] = False
    assert collection_service.run_collection_target(
        {'id': 'target-1', 'source': 'beike', 'url': list_url}) == 'success'
    assert fetch_calls == [list_url, first_url, revoked_url, revoked_url, list_url]
    assert staged_urls == [first_url, revoked_url]
    assert saved_states[-1]['seen_ids'] == ['109900001234', '109900001235']


def test_list_target_remains_network_disabled_without_policy_approval(monkeypatch):
    connection = FakeConnection([None, None])
    monkeypatch.setattr(collection_service, 'session', fake_session(connection))
    monkeypatch.setattr(collection_service, 'ENABLE_ONLINE_COLLECTION', False)
    monkeypatch.setattr(collection_service, 'get_discovery_state',
                        lambda *_: (_ for _ in ()).throw(AssertionError('state must not load')))
    fetch_calls = []
    monkeypatch.setattr(collection_service, 'fetch_public_html',
                        lambda *args, **kwargs: fetch_calls.append(args))

    status = collection_service.run_collection_target({
        'id': 'target-1', 'source': 'beike', 'url': 'https://nb.ke.com/ershoufang/'})

    assert status == 'blocked_policy'
    assert fetch_calls == []


def test_approved_list_target_stops_at_page_limit_with_cursor_saved(monkeypatch):
    log_connection = FakeConnection([None, None])

    @contextmanager
    def session_factory():
        yield log_connection

    monkeypatch.setattr(collection_service, 'session', session_factory)
    monkeypatch.setattr(collection_service, '_require_online_policy', lambda *_: None)
    monkeypatch.setattr(collection_service, 'ENABLE_ONLINE_COLLECTION', True)
    pages = [f'https://nb.ke.com/ershoufang/page{index}' for index in range(1, 7)]
    page_html = {
        page: (f'<html><head><link rel="next" href="/ershoufang/page{index + 1}"></head>'
               '<body><main>no listing links</main></body></html>')
        for index, page in enumerate(pages[:-1], start=1)
    }
    fetch_calls = []
    saved_states = []

    def fetch(source, url, **kwargs):
        fetch_calls.append(url)
        return page_html[url]

    def save_state(target_id, payload):
        saved = payload.model_dump()
        saved['revision'] += 1
        saved_states.append(saved)
        return saved

    monkeypatch.setattr(collection_service, 'get_discovery_state', lambda _, **kwargs: {
        'version': 1, 'revision': 0, 'source': 'beike', 'seen_ids': [],
        'last_page_url': None, 'next_page_url': None, 'visited_page_urls': [],
        'last_attempted_page_url': None, 'last_error_type': None, 'failed_attempts': 0,
    })
    monkeypatch.setattr(collection_service, 'save_discovery_state', save_state)
    monkeypatch.setattr(collection_service, 'fetch_public_html', fetch)
    target = {'id': 'target-1', 'source': 'beike', 'url': pages[0]}

    assert collection_service.run_collection_target(target) == 'success'
    assert fetch_calls == pages[:collection_service.MAX_DISCOVERY_PAGES_PER_RUN]
    assert len(saved_states) == collection_service.MAX_DISCOVERY_PAGES_PER_RUN
    assert saved_states[-1]['last_page_url'] == pages[4]
    assert saved_states[-1]['next_page_url'] == pages[5]
    assert log_connection.calls[0][1][6].endswith('; page_limit_reached')


def test_duplicate_candidate_reparse_updates_only_pending_unmodified_rows(tmp_path, monkeypatch):
    row = {
        'id': 'candidate-1', 'review_status': 'pending',
        'parser_version': 'generic-labelled-v0.2.123',
        'raw_sha256': '0' * 64,
        'extracted_fields': {
            'source_listing_id': '109900001234', 'community_name': '东湖花园',
            'area_sqm': 160, 'asking_price_wan': 300,
        },
        'warnings': ['human_review_required'],
    }

    class ReparseConnection:
        def __init__(self):
            self.calls = []

        def execute(self, query, params=None):
            self.calls.append((query, params))
            if 'INSERT INTO collection_candidates' in query:
                row.update({
                    'parser_version': params[6],
                    'raw_sha256': params[4],
                    'raw_storage_path': params[5],
                    'extracted_fields': params[7].obj,
                    'warnings': params[8].obj + row['warnings'],
                })
                return FakeResult(row)
            return FakeResult(None)

    connection = ReparseConnection()
    monkeypatch.setattr(collection_service, 'session', fake_session_sequence(
        FakeConnection([None]), connection))
    monkeypatch.setattr(collection_service, 'RAW_HTML_DIR', str(tmp_path / 'raw-pages'))

    result = collection_service.stage_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><h1>东湖花园 4室2厅</h1>'
        '<main>小区：东湖花园 建筑面积：160㎡ 合同总价：300万</main></body></html>',
        'manual_html_snapshot')

    query, params = connection.calls[0]
    fields = params[7].obj
    assert result['candidate'] == row
    assert result['ready_for_review'] is False
    assert params[6] == PARSER_VERSION
    assert row['parser_version'] == PARSER_VERSION
    assert fields['community_name'] == '东湖花园'
    assert fields['asking_price_wan'] is None
    assert 'missing_asking_price_wan' in params[8].obj
    community_evidence = fields['field_evidence']['community_name']
    assert community_evidence['value'] == fields['community_name']
    assert community_evidence['mention_count'] == 1
    assert community_evidence['mentions'][0]['quote'] == '小区：东湖花园'
    assert fields['field_evidence']['area_sqm']['value'] == fields['area_sqm']
    assert fields['field_evidence']['title'] == {
        'value': '东湖花园 4室2厅', 'source': 'h1',
        'quote': '东湖花园 4室2厅',
    }
    assert 'parser_version=EXCLUDED.parser_version' in query
    assert 'extracted_fields=EXCLUDED.extracted_fields' in query
    assert "collection_candidates.review_status='pending'" in query
    assert "collection_candidates.extracted_fields ? 'manually_corrected'" in query
    assert "LIKE 'operator_note:%%'" in query


def test_duplicate_old_parser_does_not_overwrite_manual_price_correction(
        tmp_path, monkeypatch):
    row = {
        'id': 'candidate-1', 'review_status': 'pending',
        'parser_version': 'generic-labelled-v0.2.123',
        'raw_sha256': '0' * 64,
        'extracted_fields': {
            'source_listing_id': '109900001234', 'community_name': '东湖花园',
            'area_sqm': 160, 'asking_price_wan': 315,
            'manually_corrected': True,
        },
        'warnings': ['human_review_required'],
    }

    class CorrectedCandidateConnection:
        def __init__(self):
            self.calls = []

        def execute(self, query, params=None):
            self.calls.append((query, params))
            if 'INSERT INTO collection_candidates' in query:
                return FakeResult(None)
            return FakeResult(row)

    connection = CorrectedCandidateConnection()
    monkeypatch.setattr(collection_service, 'session', fake_session_sequence(
        FakeConnection([None]), connection))
    monkeypatch.setattr(collection_service, 'RAW_HTML_DIR', str(tmp_path / 'raw-pages'))

    result = collection_service.stage_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 合同总价：300万'
        '</main></body></html>', 'manual_html_snapshot')

    insert_query, insert_params = connection.calls[0]
    assert len(connection.calls) == 2
    assert "collection_candidates.extracted_fields ? 'manually_corrected'" in insert_query
    assert insert_params[7].obj['asking_price_wan'] is None
    assert result['candidate']['parser_version'] == 'generic-labelled-v0.2.123'
    assert result['candidate']['extracted_fields']['asking_price_wan'] == 315
    assert result['candidate']['extracted_fields']['manually_corrected'] is True


def test_truncated_parse_warning_persists_and_blocks_review_ready(tmp_path, monkeypatch):
    html = ('<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 '
            + '说明' * 18000 + ' 总价：900万</main></body></html>')
    parsed = collection_service.parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)
    row = {
        'id': 'candidate-1', 'review_status': 'pending',
        'parser_version': parsed.parser_version, 'raw_sha256': parsed.sha256,
        'extracted_fields': parsed.fields, 'warnings': parsed.warnings,
    }
    connection = FakeConnection([row])
    monkeypatch.setattr(collection_service, 'session', fake_session_sequence(
        FakeConnection([None]), connection))
    monkeypatch.setattr(collection_service, 'RAW_HTML_DIR', str(tmp_path / 'raw-pages'))

    result = collection_service.stage_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html,
        'manual_html_snapshot')

    persisted_warnings = connection.calls[0][1][8].obj
    assert 'visible_text_truncated' in persisted_warnings
    assert result['candidate']['review_status'] == 'pending'
    assert result['ready_for_review'] is False


def test_range_conflict_evidence_persists_and_blocks_review_ready(tmp_path, monkeypatch):
    html = ('<html><body><main>小区：东湖花园 建筑面积：120㎡-130㎡ '
            '建筑面积：125㎡ 总价：365万</main></body></html>')
    parsed = collection_service.parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)
    row = {
        'id': 'candidate-1', 'review_status': 'pending',
        'parser_version': parsed.parser_version, 'raw_sha256': parsed.sha256,
        'extracted_fields': parsed.fields, 'warnings': parsed.warnings,
    }
    candidate_connection = FakeConnection([row])
    monkeypatch.setattr(collection_service, 'session', fake_session_sequence(
        FakeConnection([None]), candidate_connection))
    monkeypatch.setattr(collection_service, 'RAW_HTML_DIR', str(tmp_path / 'raw-pages'))

    result = collection_service.stage_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html,
        'manual_html_snapshot')

    params = candidate_connection.calls[0][1]
    persisted_fields = params[7].obj
    persisted_warnings = params[8].obj
    assert persisted_fields['area_sqm'] is None
    assert persisted_fields['field_evidence']['area_sqm']['value'] is None
    assert [mention['candidate_value'] for mention in
            persisted_fields['field_evidence']['area_sqm']['mentions']] == [
                '120㎡-130㎡', '125']
    assert 'multiple_area_mentions' in persisted_warnings
    assert 'missing_area_sqm' in persisted_warnings
    assert result['ready_for_review'] is False


def test_unresolved_inline_visibility_warning_persists_and_blocks_review_ready(
        tmp_path, monkeypatch):
    html = ('<html><body><main style="display:var(--listing-display)">'
            '小区：东湖花园 建筑面积：160㎡ 总价：365万'
            '</main></body></html>')
    parsed = collection_service.parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)
    row = {
        'id': 'candidate-1', 'review_status': 'pending',
        'parser_version': parsed.parser_version, 'raw_sha256': parsed.sha256,
        'extracted_fields': parsed.fields, 'warnings': parsed.warnings,
    }
    connection = FakeConnection([row])
    monkeypatch.setattr(collection_service, 'session', fake_session_sequence(
        FakeConnection([None]), connection))
    monkeypatch.setattr(collection_service, 'RAW_HTML_DIR', str(tmp_path / 'raw-pages'))

    result = collection_service.stage_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html,
        'manual_html_snapshot')

    persisted_warnings = connection.calls[0][1][8].obj
    assert 'unresolved_inline_visibility' in persisted_warnings
    assert result['candidate']['review_status'] == 'pending'
    assert result['ready_for_review'] is False


def test_unresolved_stylesheet_visibility_warning_persists_and_blocks_review_ready(
        tmp_path, monkeypatch):
    html = ('<html><head><style>.recommendation{display:none}</style></head>'
            '<body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 '
            '<span class="recommendation">推荐挂牌总价：365万</span>'
            '</main></body></html>')
    parsed = collection_service.parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)
    row = {
        'id': 'candidate-1', 'review_status': 'pending',
        'parser_version': parsed.parser_version, 'raw_sha256': parsed.sha256,
        'extracted_fields': parsed.fields, 'warnings': parsed.warnings,
    }
    connection = FakeConnection([row])
    monkeypatch.setattr(collection_service, 'session', fake_session_sequence(
        FakeConnection([None]), connection))
    monkeypatch.setattr(collection_service, 'RAW_HTML_DIR', str(tmp_path / 'raw-pages'))

    result = collection_service.stage_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html,
        'manual_html_snapshot')

    persisted_warnings = connection.calls[0][1][8].obj
    assert 'unresolved_stylesheet_visibility' in persisted_warnings
    assert result['candidate']['review_status'] == 'pending'
    assert result['ready_for_review'] is False


def test_numeric_precision_warnings_persist_and_block_review_ready(tmp_path, monkeypatch):
    html = ('<html><body><main>小区：东湖花园 建筑面积：160.005㎡ 总价：365.005万'
            '</main></body></html>')
    parsed = collection_service.parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)
    row = {
        'id': 'candidate-1', 'review_status': 'pending',
        'parser_version': parsed.parser_version, 'raw_sha256': parsed.sha256,
        'extracted_fields': parsed.fields, 'warnings': parsed.warnings,
    }
    connection = FakeConnection([row])
    monkeypatch.setattr(collection_service, 'session', fake_session_sequence(
        FakeConnection([None]), connection))
    monkeypatch.setattr(collection_service, 'RAW_HTML_DIR', str(tmp_path / 'raw-pages'))

    result = collection_service.stage_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html,
        'manual_html_snapshot')

    persisted_warnings = connection.calls[0][1][8].obj
    assert 'numeric_precision_requires_correction:area_sqm' in persisted_warnings
    assert 'numeric_precision_requires_correction:asking_price_wan' in persisted_warnings
    assert result['candidate']['review_status'] == 'pending'
    assert result['ready_for_review'] is False


def test_duplicate_reviewed_candidate_is_retrieved_without_parser_update(tmp_path, monkeypatch):
    existing = {
        'id': 'candidate-1', 'review_status': 'approved', 'parser_version': 'old-parser',
        'raw_sha256': '0' * 64,
        'extracted_fields': {'community_name': '更正后名称'},
        'warnings': ['missing_source_listing_id'],
    }
    connection = FakeConnection([None, existing])
    monkeypatch.setattr(collection_service, 'session', fake_session_sequence(
        FakeConnection([None]), connection))
    monkeypatch.setattr(collection_service, 'RAW_HTML_DIR', str(tmp_path / 'raw-pages'))

    result = collection_service.stage_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body>小区：东湖花园 建筑面积：160㎡ 总价：365万</body></html>',
        'manual_html_snapshot')

    assert result['candidate'] == existing
    assert result['ready_for_review'] is False
    assert len(connection.calls) == 2
    assert 'INSERT INTO collection_candidates' in connection.calls[0][0]
    assert 'SELECT * FROM collection_candidates' in connection.calls[1][0]
    assert connection.calls[1][1] == ('beike',
        'https://nb.ke.com/ershoufang/109900001234.html', connection.calls[0][1][4])


def test_manual_correction_relabels_field_evidence_as_operator_review(monkeypatch):
    row = {
        'id': 'candidate-1', 'review_status': 'pending',
        'extracted_fields': {
            'title': '自动识别标题', 'community_name': '旧识别值', 'area_sqm': 160.0,
            'asking_price_wan': None,
            'field_evidence': {
                'title': {'value': '自动识别标题', 'source': 'h1', 'quote': '自动识别标题'},
                'community_name': {'value': '旧识别值', 'source': 'visible_listing_text',
                                   'mentions': [{'candidate_value': '旧识别值',
                                                 'source': 'visible_listing_text',
                                                 'quote': '小区：旧识别值',
                                                 'start_char': 0, 'end_char': 8}],
                                   'mention_count': 1, 'mentions_truncated': False},
                'area_sqm': {'value': 160.0,
                             'mentions': [{'candidate_value': '160',
                                           'source': 'visible_listing_text',
                                           'quote': '面积：160㎡',
                                           'start_char': 9, 'end_char': 16}],
                             'mention_count': 1, 'mentions_truncated': False},
                'asking_price_wan': {'value': None,
                                     'mentions': [{'candidate_value': '200',
                                                   'source': 'visible_listing_text',
                                                   'quote': '挂牌价约200万',
                                                   'start_char': 17, 'end_char': 27,
                                                   'is_non_exact': True}],
                                     'mention_count': 1, 'mentions_truncated': False},
            },
        },
        'warnings': ['non_exact_asking_price'],
    }
    connection = FakeConnection([row, row])
    monkeypatch.setattr(collection_service, 'session', fake_session(connection))

    collection_service.correct_candidate('candidate-1', CandidateCorrection(
        title='人工复核标题', community_name='人工复核小区', asking_price_wan=200,
        review_note='对照保存页面确认'))

    fields = connection.calls[1][1][0].obj
    assert fields['title'] == '人工复核标题'
    assert fields['field_evidence']['title'] == {
        'value': '人工复核标题', 'source': 'manual_review', 'mentions': [],
        'mention_count': 0, 'mentions_truncated': False}
    assert fields['community_name'] == '人工复核小区'
    assert fields['field_evidence']['community_name'] == {
        'value': '人工复核小区', 'source': 'manual_review', 'mentions': [],
        'mention_count': 0, 'mentions_truncated': False}
    assert fields['asking_price_wan'] == 200
    assert fields['field_evidence']['asking_price_wan'] == {
        'value': 200, 'source': 'manual_review', 'mentions': [],
        'mention_count': 0, 'mentions_truncated': False}
    assert 'non_exact_asking_price' in connection.calls[1][1][1].obj
    assert fields['field_evidence']['area_sqm']['mentions'][0]['source'] == 'visible_listing_text'


def test_approval_requires_correction_of_unrepresentable_parser_numbers(monkeypatch):
    row = {
        'id': 'candidate-1', 'review_status': 'pending', 'source': 'beike',
        'source_url': 'https://nb.ke.com/ershoufang/109900001234.html',
        'captured_at': None,
        'extracted_fields': {
            'source_listing_id': '109900001234', 'community_name': '东湖花园',
            'area_sqm': 160.005, 'asking_price_wan': 365.005,
        },
        'warnings': ['numeric_precision_requires_correction:area_sqm',
                     'numeric_precision_requires_correction:asking_price_wan'],
    }
    connection = FakeConnection([row])
    monkeypatch.setattr(collection_service, 'session', fake_session(connection))

    with pytest.raises(HTTPException) as error:
        collection_service.review_candidate('candidate-1', 'approve', '已核对原始页面')

    assert error.value.status_code == 409
    assert error.value.detail['fields'] == ['area_sqm', 'asking_price_wan']
    assert len(connection.calls) == 1


def test_approval_returns_conflict_for_legacy_candidate_with_invalid_numeric_scale(monkeypatch):
    row = {
        'id': 'candidate-1', 'review_status': 'pending', 'source': 'beike',
        'source_url': 'https://nb.ke.com/ershoufang/109900001234.html',
        'captured_at': None,
        'extracted_fields': {
            'source_listing_id': '109900001234', 'community_name': '东湖花园',
            'area_sqm': 160.005, 'asking_price_wan': 365.00,
        },
        'warnings': [],
    }
    connection = FakeConnection([row])
    monkeypatch.setattr(collection_service, 'session', fake_session(connection))

    with pytest.raises(HTTPException) as error:
        collection_service.review_candidate('candidate-1', 'approve', '已核对原始页面')

    assert error.value.status_code == 409
    assert error.value.detail['fields'] == ['area_sqm']
    assert len(connection.calls) == 1


def test_manual_numeric_correction_clears_only_matching_precision_warning(monkeypatch):
    row = {
        'id': 'candidate-1', 'review_status': 'pending',
        'extracted_fields': {'area_sqm': 160.005, 'asking_price_wan': 365.005},
        'warnings': ['numeric_precision_requires_correction:area_sqm',
                     'numeric_precision_requires_correction:asking_price_wan'],
    }
    connection = FakeConnection([row, row])
    monkeypatch.setattr(collection_service, 'session', fake_session(connection))

    collection_service.correct_candidate('candidate-1', CandidateCorrection(
        area_sqm='160.00', review_note='按页面人工核实面积'))

    warnings = connection.calls[1][1][1].obj
    assert 'numeric_precision_requires_correction:area_sqm' not in warnings
    assert 'numeric_precision_requires_correction:asking_price_wan' in warnings


def test_beike_candidate_correction_requires_eight_digit_source_id(monkeypatch):
    row = {
        'id': 'candidate-1', 'source': 'beike', 'review_status': 'pending',
        'extracted_fields': {'source_listing_id': '109900001234'}, 'warnings': [],
    }
    connection = FakeConnection([row])
    monkeypatch.setattr(collection_service, 'session', fake_session(connection))

    with pytest.raises(HTTPException) as error:
        collection_service.correct_candidate('candidate-1', CandidateCorrection(
            source_listing_id='1234567', review_note='依据页面人工核对'))

    assert error.value.status_code == 422
    assert 'source ID format' in error.value.detail
    assert len(connection.calls) == 1


def test_anjuke_candidate_correction_accepts_seven_digit_source_id(monkeypatch):
    row = {
        'id': 'candidate-1', 'source': 'anjuke', 'review_status': 'pending',
        'extracted_fields': {}, 'warnings': [],
    }
    connection = FakeConnection([row, row])
    monkeypatch.setattr(collection_service, 'session', fake_session(connection))

    collection_service.correct_candidate('candidate-1', CandidateCorrection(
        source_listing_id='1234567', review_note='依据页面人工核对'))

    saved_fields = connection.calls[1][1][0].obj
    assert saved_fields['source_listing_id'] == '1234567'
    assert saved_fields['field_evidence']['source_listing_id']['source'] == 'manual_review'


def test_invalid_legacy_source_id_cannot_be_approved(monkeypatch):
    row = {
        'id': 'candidate-1', 'review_status': 'pending', 'source': 'beike',
        'source_url': 'https://nb.ke.com/ershoufang/109900001234.html',
        'captured_at': None,
        'extracted_fields': {
            'source_listing_id': 'listing-1', 'community_name': '东湖花园',
            'area_sqm': 120, 'asking_price_wan': 365,
        },
        'warnings': [],
    }
    connection = FakeConnection([row])
    monkeypatch.setattr(collection_service, 'session', fake_session(connection))

    with pytest.raises(HTTPException) as error:
        collection_service.review_candidate('candidate-1', 'approve', '已核对原始页面')

    assert error.value.status_code == 409
    assert error.value.detail['fields'] == ['source_listing_id']
    assert len(connection.calls) == 1
