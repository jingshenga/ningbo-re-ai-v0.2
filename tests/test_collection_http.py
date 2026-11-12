import httpx
import pytest
from app.collectors.http_client import (MAX_PAGE_BYTES, MAX_ROBOTS_BYTES, READ_CHUNK_BYTES,
                                       CollectionBlocked, fetch_public_html)
from app.collectors.parser import CollectionError

URL='https://nb.ke.com/ershoufang/109900001234.html'


class CountingStream(httpx.SyncByteStream):
    def __init__(self, size, chunk_size=64 * 1024):
        self.size = size
        self.chunk_size = chunk_size
        self.bytes_yielded = 0

    def __iter__(self):
        remaining = self.size
        while remaining:
            chunk = b'x' * min(remaining, self.chunk_size)
            remaining -= len(chunk)
            self.bytes_yielded += len(chunk)
            yield chunk


def test_robots_disallow_blocks_page_fetch():
    seen=[]
    def handler(req):
        seen.append(str(req.url))
        return httpx.Response(200,text='User-agent: *\nDisallow: /ershoufang/',
                              headers={'content-type':'text/plain'})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(CollectionBlocked) as err:
            fetch_public_html('beike',URL,client=client)
    assert err.value.category=='blocked_robots'
    assert seen==['https://nb.ke.com/robots.txt']


def test_403_never_retries_or_bypasses():
    seen=[]
    def handler(req):
        seen.append(str(req.url))
        if req.url.path=='/robots.txt':
            return httpx.Response(200,text='User-agent: *\nAllow: /',
                                  headers={'content-type':'text/plain'})
        return httpx.Response(403,text='blocked')
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(CollectionBlocked) as err:
            fetch_public_html('beike',URL,client=client)
    assert err.value.category=='blocked_upstream'
    assert err.value.http_status==403
    assert len(seen)==2


def test_policy_recheck_can_block_page_request_after_robots_fetch():
    seen=[]

    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(200, text='User-agent: *\nAllow: /',
                              headers={'content-type':'text/plain'})

    def policy_revoked():
        raise CollectionBlocked('Online collection disabled or source permission is not approved',
                                'blocked_policy')

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(CollectionBlocked) as err:
            fetch_public_html('beike', URL, client=client,
                              before_page_request=policy_revoked)

    assert err.value.category == 'blocked_policy'
    assert seen == ['https://nb.ke.com/robots.txt']


def test_http_200_antibot_challenge_is_blocked_without_retry():
    seen=[]
    def handler(req):
        seen.append(str(req.url))
        if req.url.path=='/robots.txt':
            return httpx.Response(200,text='User-agent: *\nAllow: /',
                                  headers={'content-type':'text/plain'})
        return httpx.Response(
            200,
            text='<html><title>访问验证</title><script src="https://callback.58.com/antibot/verifycode"></script></html>',
            headers={'content-type':'text/html; charset=utf-8'})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(CollectionBlocked) as err:
            fetch_public_html('beike',URL,client=client)
    assert err.value.category=='blocked_upstream'
    assert err.value.http_status==200
    assert 'callback.58.com' not in str(err.value)
    assert 'verifycode' not in str(err.value)
    assert seen==['https://nb.ke.com/robots.txt',URL]


def test_http_200_captcha_page_is_blocked():
    def handler(req):
        if req.url.path=='/robots.txt':
            return httpx.Response(200,text='User-agent: *\nAllow: /',
                                  headers={'content-type':'text/plain'})
        return httpx.Response(200,text='<html><body>请完成滑动验证</body></html>',
                              headers={'content-type':'text/html; charset=utf-8'})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(CollectionBlocked) as err:
            fetch_public_html('beike',URL,client=client)
    assert err.value.category=='blocked_upstream'
    assert err.value.http_status==200


def test_permitted_sample_downloads_html():
    def handler(req):
        if req.url.path=='/robots.txt':
            return httpx.Response(200,text='User-agent: *\nAllow: /',
                                  headers={'content-type':'text/plain'})
        return httpx.Response(200,text='<html><body>demo</body></html>',
                              headers={'content-type':'text/html; charset=utf-8'})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        html=fetch_public_html('beike',URL,client=client)
    assert '<html>' in html


@pytest.mark.parametrize(('oversized_path', 'expected_category', 'limit'), [
    ('/ershoufang/109900001234.html', 'failed', MAX_PAGE_BYTES),
    ('/robots.txt', 'blocked_robots', MAX_ROBOTS_BYTES),
])
def test_oversized_response_stops_streaming_at_bounded_read(
        oversized_path, expected_category, limit):
    streams = []

    def handler(request):
        if request.url.path == oversized_path:
            stream = CountingStream(8_000_000)
            streams.append(stream)
            return httpx.Response(200, stream=stream, headers={
                'content-type': 'text/html' if oversized_path != '/robots.txt' else 'text/plain'
            })
        return httpx.Response(200, text='User-agent: *\nAllow: /',
                              headers={'content-type': 'text/plain'})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(CollectionBlocked) as err:
            fetch_public_html('beike', URL, client=client)

    assert err.value.category == expected_category
    assert len(streams) == 1
    assert streams[0].bytes_yielded <= limit + READ_CHUNK_BYTES


def test_oversized_content_length_is_rejected_without_integer_conversion():
    stream = CountingStream(10)

    def handler(request):
        return httpx.Response(200, stream=stream, headers={
            'content-type': 'text/plain', 'content-length': '9' * 5000,
        })

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(CollectionBlocked) as err:
            fetch_public_html('beike', URL, client=client)

    assert err.value.category == 'blocked_robots'
    assert stream.bytes_yielded == 0


def test_missing_robots_fails_closed():
    with httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(404))) as client:
        with pytest.raises(CollectionBlocked) as err:
            fetch_public_html('beike',URL,client=client)
    assert err.value.category=='blocked_robots'


@pytest.mark.parametrize('suffix', ['?token=private', '#tracking-fragment'])
def test_sensitive_url_suffix_is_rejected_before_network_request(suffix):
    seen=[]
    with httpx.Client(transport=httpx.MockTransport(
            lambda request: seen.append(str(request.url)) or httpx.Response(200))) as client:
        with pytest.raises(CollectionError, match='query and fragment'):
            fetch_public_html('beike', URL + suffix, client=client)
    assert seen == []


@pytest.mark.parametrize('suffix', [' ', '\n', '\t', '\x00', '\x7f'])
def test_whitespace_or_control_url_is_rejected_before_network_request(suffix):
    seen=[]
    with httpx.Client(transport=httpx.MockTransport(
            lambda request: seen.append(str(request.url)) or httpx.Response(200))) as client:
        with pytest.raises(CollectionError, match='whitespace or control'):
            fetch_public_html('beike', URL + suffix, client=client)
    assert seen == []


def test_robots_crawl_delay_over_interval_blocks():
    def handler(req):
        if req.url.path=='/robots.txt':
            return httpx.Response(200,text='User-agent: *\nAllow: /\nCrawl-delay: 120',
                                  headers={'content-type':'text/plain'})
        return httpx.Response(200,text='<html>demo</html>',
                              headers={'content-type':'text/html'})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(CollectionBlocked) as err:
            fetch_public_html('beike',URL,client=client,min_delay_seconds=30)
    assert err.value.category=='blocked_robots'
