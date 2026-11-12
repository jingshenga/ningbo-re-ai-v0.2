from datetime import timezone
import httpx
import pytest

from app.dtk import (PAGE_SIZE, DtkClient, _unwrap_envelope, parse_page,
                     normalize_post, normalize_datetime, DtkError)


def test_sync_page():
    b={'data':{'items':[{'id':'123456'}],'cursor':'next1','has_more':True},'meta':{'guest_fallback':True}}
    result=parse_page(b)
    assert result.items[0]['id']=='123456'
    assert result.next_cursor=='next1'
    assert result.has_more
    assert result.guest_fallback


def test_page_with_cursor_but_no_has_more_flag_is_treated_as_paginated():
    result = parse_page({'data': {'items': [], 'cursor': 'next-page'}})

    assert result.next_cursor == 'next-page'
    assert result.has_more is True


def test_explicit_has_more_false_overrides_a_cursor():
    result = parse_page({'data': {'items': [], 'cursor': 'stale', 'has_more': False}})

    assert result.next_cursor == 'stale'
    assert result.has_more is False


@pytest.mark.parametrize('body', [
    {'data': {'items': [], 'cursor': '   ', 'has_more': True}},
    {'data': {'items': [], 'result_meta': {'cursor': {'next': '\t'}}, 'has_more': True}},
])
def test_page_rejects_whitespace_only_cursors(body):
    with pytest.raises(DtkError, match='cursor must not be blank'):
        parse_page(body)


def test_page_preserves_zero_as_a_numeric_cursor():
    result = parse_page({'data': {'items': [], 'cursor': 0, 'has_more': True}})

    assert result.next_cursor == '0'
    assert result.has_more is True


def test_empty_metadata_cursor_is_treated_as_no_next_cursor():
    result = parse_page({
        'data': {'items': [], 'result_meta': {'cursor': {'next': ''}}, 'has_more': False},
    })

    assert result.next_cursor is None
    assert result.has_more is False


def test_task_page():
    b={'data':{'state':'done','data':{'items':[{'aweme_id':'5555'}],'cursor':'old','has_more':False},
               'result_meta':{'guest_fallback':False}}}
    result=parse_page(b)
    assert not result.has_more
    assert len(result.items)==1


def test_page_accepts_requested_item_limit():
    result = parse_page({'data': {'items': [{'id': str(i)} for i in range(20)]}})

    assert len(result.items) == 20


def test_page_rejects_items_beyond_requested_limit():
    body = {'data': {'items': [{'id': str(i)} for i in range(21)]}}

    with pytest.raises(DtkError, match='exceeds requested limit'):
        parse_page(body)


def test_nested_task_page_rejects_items_beyond_requested_limit():
    body = {'data': {'state': 'done', 'data': {'items': [{'id': str(i)} for i in range(21)]}}}

    with pytest.raises(DtkError, match='exceeds requested limit'):
        parse_page(body)


def test_author_posts_requests_the_page_size_limit():
    requests = []

    class FakeHttp:
        def get(self, path, **kwargs):
            requests.append((path, kwargs))
            request = httpx.Request('GET', 'https://dtk.test' + path)
            return httpx.Response(200, request=request,
                                  json={'success': True, 'data': {'items': []}})

    client = DtkClient.__new__(DtkClient)
    client.client = FakeHttp()

    assert client.author_posts('author-1').items == []
    assert requests[0][1]['params']['count'] == PAGE_SIZE


def test_author_posts_recognizes_https_profile_url_case_insensitively():
    requests = []

    class FakeHttp:
        def get(self, path, **kwargs):
            requests.append(kwargs)
            request = httpx.Request('GET', 'https://dtk.test' + path)
            return httpx.Response(200, request=request,
                                  json={'success': True, 'data': {'items': []}})

    client = DtkClient.__new__(DtkClient)
    client.client = FakeHttp()

    client.author_posts('HTTPS://www.douyin.com/user/ABC')

    assert requests[0]['params']['url'] == 'HTTPS://www.douyin.com/user/ABC'
    assert 'sec_user_id' not in requests[0]['params']


def test_missing_items_does_not_silently_succeed():
    try:
        parse_page({'data':{'message':'upstream schema changed'}})
        assert False
    except DtkError:
        pass


def test_normalize_post_common_keys():
    post=normalize_post({'aweme_id':'7290000000000000000','desc':'东湖花园 160㎡ 365万',
                         'author':{'nickname':'示例作者'},'create_time':1794000000})
    assert post['source_post_id']=='7290000000000000000'
    assert post['author_name']=='示例作者'
    assert post['published_at'].tzinfo is timezone.utc
    assert post['source_url'].startswith('https://www.douyin.com/video/')


@pytest.mark.parametrize('item', [
    {'id': '123456', 'title': 'title\x00suffix'},
    {'id': '123456', 'description': 'description\x00suffix'},
    {'id': '123456', 'author': {'nickname': 'author\x00suffix'}},
    {'id': '123456', 'poi_name': 'location\x00suffix'},
    {'id': '123\x00456'},
    {'id': '123456', 'title': 'title\ud800suffix'},
    {'id': '123\ud800456'},
])
def test_normalize_post_rejects_unpersistable_text(item):
    with pytest.raises(DtkError, match='PostgreSQL cannot store'):
        normalize_post(item)


@pytest.mark.parametrize('item', [
    {'id': 'x' * 221},
    {'id': '123456', 'title': 't' * 2001},
    {'id': '123456', 'author_name': 'a' * 201},
    {'id': '123456', 'poi_name': 'l' * 301},
])
def test_normalize_post_rejects_fields_over_api_storage_limits(item):
    with pytest.raises(DtkError, match='supported storage lengths'):
        normalize_post(item)


def test_missing_stable_post_id_is_skipped():
    assert normalize_post({'desc':'A house without ID'}) is None


def test_naive_timestamp_string_not_guessed():
    assert normalize_datetime('2026-11-09 09:00:00') is None
    assert normalize_datetime('2026-11-09T09:00:00+08:00') is not None


@pytest.mark.parametrize('body', [[], None, 'not-an-object'])
def test_non_object_page_payload_raises_dtk_error(body):
    with pytest.raises(DtkError, match='response must be an object'):
        parse_page(body)


def test_page_rejects_wrong_metadata_and_boolean_types():
    with pytest.raises(DtkError, match='data must be an object'):
        parse_page({'data': []})
    with pytest.raises(DtkError, match='has_more must be a boolean'):
        parse_page({'data': {'items': [], 'has_more': 'false'}})
    with pytest.raises(DtkError, match='guest_fallback must be a boolean'):
        parse_page({'data': {'items': []}, 'meta': {'guest_fallback': 'false'}})


@pytest.mark.parametrize(('body', 'message'), [
    ({'data': {'data': []}}, 'nested data must be an object'),
    ({'data': {'items': [], 'result_meta': []}}, 'result_meta must be an object'),
    ({'data': {'items': []}, 'meta': []}, 'meta must be an object'),
    ({'data': {'items': [], 'result_meta': {'cursor': []}}}, 'cursor metadata must be an object'),
    ({'data': {'items': [], 'cursor': {}}}, 'cursor must be a string or integer'),
])
def test_page_rejects_malformed_nested_metadata(body, message):
    with pytest.raises(DtkError, match=message):
        parse_page(body)


@pytest.mark.parametrize('body', [[], {'success': False, 'error': 'upstream error'}])
def test_malformed_dtk_envelope_raises_dtk_error(body):
    with pytest.raises(DtkError):
        _unwrap_envelope(httpx.Response(200, json=body))


def test_malformed_nested_share_url_falls_back_to_post_url():
    post = normalize_post({'id': '123456', 'url': {'url_list': None}})
    assert post['source_url'] == 'https://www.douyin.com/video/123456'


@pytest.mark.parametrize('url', [
    'javascript:alert(1)',
    'data:text/html,<script>alert(1)</script>',
    'http://www.douyin.com/video/123456',
    'https://user:pass@www.douyin.com/video/123456',
    'https://douyin.com.example/video/123456',
    'https://douyin.com../video/123456',
    'https://www.iesdouyin.com.../share/video/123456',
    '\thttps://www.douyin.com/video/123456',
    'https://www.douyin.com/video/123456\n',
    'https://www.douyin.com/video/123456\x1f',
    'https://www.douyin.com/video/12 3456',
    'https://www.douyin.com/video/12\t3456',
    '\x85https://www.douyin.com/video/123456',
    'https://www.douyin.com/video/123456\x85',
    'https://www.douyin.com/video/\ud800',
    'https://example.com/video/123456',
])
def test_unsafe_share_url_falls_back_to_canonical_post_url(url):
    post = normalize_post({'id': '123456', 'share_url': url})

    assert post['source_url'] == 'https://www.douyin.com/video/123456'


def test_overlong_share_url_falls_back_to_canonical_post_url():
    post = normalize_post({
        'id': '123456', 'share_url': 'https://www.douyin.com/video/' + 'x' * 2000,
    })

    assert post['source_url'] == 'https://www.douyin.com/video/123456'


def test_post_url_fallback_encodes_id_as_one_path_segment():
    post = normalize_post({'id': 'abc/def', 'share_url': 'javascript:alert(1)'})

    assert post['source_url'] == 'https://www.douyin.com/video/abc%2Fdef'


def test_https_share_url_is_trimmed():
    post = normalize_post({'id': '123456', 'share_url': ' https://v.douyin.com/abc123/ '})

    assert post['source_url'] == 'https://v.douyin.com/abc123/'


def test_iesdouyin_share_host_is_accepted():
    post = normalize_post({'id': '123456', 'share_url': 'https://www.iesdouyin.com/share/video/123456'})

    assert post['source_url'] == 'https://www.iesdouyin.com/share/video/123456'


def test_douyin_share_host_allows_one_dns_root_dot():
    post = normalize_post({'id': '123456', 'share_url': 'https://www.douyin.com./video/123456'})

    assert post['source_url'] == 'https://www.douyin.com./video/123456'


def test_unstable_post_id_type_is_skipped():
    assert normalize_post({'id': {'value': '123'}}) is None


def test_malformed_text_fields_are_not_stringified_as_payload_repr():
    post = normalize_post({
        'id': '123456',
        'author': {'nickname': ['unexpected']},
        'author_name': '示例作者',
        'title': {'unexpected': 'payload'},
        'desc': '有效标题',
        'description': ['unexpected'],
        'poi_name': {'unexpected': 'payload'},
    })

    assert post['author_name'] == '示例作者'
    assert post['title'] == '有效标题'
    assert post['description'] == '有效标题'
    assert post['raw_location'] is None


def test_boolean_is_not_a_datetime_timestamp():
    assert normalize_datetime(True) is None


@pytest.mark.parametrize('value', [1_000_000_000_000, '1000000000000'])
def test_millisecond_timestamp_threshold_is_inclusive(value):
    assert normalize_datetime(value).isoformat() == '2001-09-09T01:46:40+00:00'


@pytest.mark.parametrize('value', [10 ** 400, '²', '9' * 5000])
def test_unrepresentable_numeric_timestamp_is_treated_as_unknown(value):
    assert normalize_datetime(value) is None


def test_task_polling_obeys_wall_clock_deadline(monkeypatch):
    class Clock:
        now = 0.0

        def monotonic(self):
            return self.now

        def sleep(self, seconds):
            self.now += seconds

    clock = Clock()
    poll_timeouts = []

    class FakeHttp:
        def get(self, path, **kwargs):
            request = httpx.Request('GET', 'https://dtk.test' + path)
            if path == '/api/v1/douyin/user/posts':
                return httpx.Response(202, request=request,
                                      json={'success': True, 'data': {'task_id': 'task-1'}})
            timeout = kwargs.get('timeout')
            poll_timeouts.append(timeout)
            clock.now += min(20.0, timeout if timeout is not None else 30.0)
            return httpx.Response(200, request=request,
                                  json={'success': True, 'data': {'state': 'running'}})

    monkeypatch.setattr('app.dtk.time.monotonic', clock.monotonic)
    monkeypatch.setattr('app.dtk.time.sleep', clock.sleep)
    client = DtkClient.__new__(DtkClient)
    client.client = FakeHttp()

    with pytest.raises(DtkError, match='did not finish within'):
        client.author_posts('author-1')

    assert len(poll_timeouts) == 3
    assert all(timeout is not None and timeout <= 30 for timeout in poll_timeouts)


@pytest.mark.parametrize('state', [None, [], 1, ''])
def test_task_poll_rejects_missing_or_invalid_state(monkeypatch, state):
    class Clock:
        now = 0.0

        def monotonic(self):
            return self.now

        def sleep(self, seconds):
            self.now += seconds

    clock = Clock()

    class FakeHttp:
        def get(self, path, **kwargs):
            request = httpx.Request('GET', 'https://dtk.test' + path)
            if path == '/api/v1/douyin/user/posts':
                return httpx.Response(202, request=request,
                                      json={'success': True, 'data': {'task_id': 'task-1'}})
            return httpx.Response(200, request=request,
                                  json={'success': True, 'data': {'state': state}})

    monkeypatch.setattr('app.dtk.time.monotonic', clock.monotonic)
    monkeypatch.setattr('app.dtk.time.sleep', clock.sleep)
    client = DtkClient.__new__(DtkClient)
    client.client = FakeHttp()

    with pytest.raises(DtkError, match='task state is missing or invalid'):
        client.author_posts('author-1')


def test_failed_task_with_malformed_error_uses_safe_dtk_error(monkeypatch):
    class FakeHttp:
        def get(self, path, **kwargs):
            request = httpx.Request('GET', 'https://dtk.test' + path)
            if path == '/api/v1/douyin/user/posts':
                return httpx.Response(202, request=request,
                                      json={'success': True, 'data': {'task_id': 'task-1'}})
            return httpx.Response(200, request=request, json={
                'success': True, 'data': {'state': 'failed', 'error': ['untrusted detail']},
            })

    monkeypatch.setattr('app.dtk.time.sleep', lambda _: None)
    client = DtkClient.__new__(DtkClient)
    client.client = FakeHttp()

    with pytest.raises(DtkError, match='DTK task failed') as exc_info:
        client.author_posts('author-1')
    assert 'untrusted detail' not in str(exc_info.value)


@pytest.mark.parametrize('task_id', [True, {'unexpected': 'object'}, '   '])
def test_task_id_must_be_a_nonempty_scalar(monkeypatch, task_id):
    class FakeHttp:
        def get(self, path, **kwargs):
            request = httpx.Request('GET', 'https://dtk.test' + path)
            if path == '/api/v1/douyin/user/posts':
                return httpx.Response(202, request=request,
                                      json={'success': True, 'data': {'task_id': task_id}})
            return httpx.Response(200, request=request, json={
                'success': True,
                'data': {'state': 'done', 'data': {'items': []}},
            })

    monkeypatch.setattr('app.dtk.time.sleep', lambda _: None)
    client = DtkClient.__new__(DtkClient)
    client.client = FakeHttp()

    with pytest.raises(DtkError, match='missing or invalid task_id'):
        client.author_posts('author-1')


def test_task_id_is_encoded_as_one_path_segment(monkeypatch):
    paths = []

    class FakeHttp:
        def get(self, path, **kwargs):
            paths.append(path)
            request = httpx.Request('GET', 'https://dtk.test' + path)
            if path == '/api/v1/douyin/user/posts':
                return httpx.Response(200, request=request,
                                      json={'success': True, 'data': {'task_id': 'id/a?b'}})
            return httpx.Response(200, request=request, json={
                'success': True,
                'data': {'state': 'done', 'data': {'items': []}},
            })

    monkeypatch.setattr('app.dtk.time.sleep', lambda _: None)
    client = DtkClient.__new__(DtkClient)
    client.client = FakeHttp()

    assert client.author_posts('author-1').items == []
    assert paths[1] == '/api/v1/tasks/id%2Fa%3Fb'
