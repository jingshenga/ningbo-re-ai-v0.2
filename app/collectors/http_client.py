"""Fail-closed public HTML fetcher.

Online collection requires explicit operator approval + global enable + robots permission.
Never attempts login circumvention, CAPTCHA solving, rotating proxies, or private APIs.
"""
from __future__ import annotations

from typing import Callable
from urllib.parse import urlsplit
import ipaddress
import socket
from urllib.robotparser import RobotFileParser

import httpx

from app.collectors.parser import CollectionError
from app.collectors.url_policy import check_source_url

USER_AGENT = 'NingboHousingResearchBot/0.2 (operator-controlled; respect robots)'
MAX_PAGE_BYTES = 1_000_000
MAX_ROBOTS_BYTES = 256_000
READ_CHUNK_BYTES = 64 * 1024
ACCESS_CHALLENGE_MARKERS = (
    'callback.58.com/antibot/verifycode', 'captcha', '验证码', '滑动验证',
    '人机验证', '访问验证', 'verify you are human', 'unusual traffic',
)


class CollectionBlocked(CollectionError):
    def __init__(self, reason: str, category: str = 'blocked_policy', http_status: int | None = None):
        super().__init__(reason)
        self.category = category
        self.http_status = http_status


def _is_access_challenge(html: str) -> bool:
    text = html.casefold()
    return any(marker in text for marker in ACCESS_CHALLENGE_MARKERS)


def _read_limited(response: httpx.Response, limit: int, category: str, message: str) -> bytes:
    content_length = response.headers.get('content-length')
    if content_length and content_length.isdecimal():
        declared_size = content_length.lstrip('0') or '0'
        limit_text = str(limit)
        if (len(declared_size) > len(limit_text)
                or (len(declared_size) == len(limit_text) and declared_size > limit_text)):
            raise CollectionBlocked(message, category, response.status_code)
    chunks = []
    size = 0
    for chunk in response.iter_bytes(chunk_size=READ_CHUNK_BYTES):
        size += len(chunk)
        if size > limit:
            raise CollectionBlocked(message, category, response.status_code)
        chunks.append(chunk)
    return b''.join(chunks)


def fetch_public_html(source: str, source_url: str, *, client: httpx.Client | None = None,
                      min_delay_seconds: int = 30,
                      before_page_request: Callable[[], None] | None = None) -> str:
    """Fetch one detail page when called AFTER source permission checks in services.

    URL allowlist, strict robots checks, no redirects, no retries on restriction responses.
    """
    check_source_url(source, source_url)
    uri = urlsplit(source_url)
    robots_url = f'{uri.scheme}://{uri.hostname}/robots.txt'
    own_client = client is None
    if own_client:
        try:
            ips = [ipaddress.ip_address(r[4][0]) for r in socket.getaddrinfo(
                uri.hostname, 443, type=socket.SOCK_STREAM)]
        except (socket.gaierror, ValueError, OSError) as exc:
            raise CollectionBlocked('DNS resolution failed; no online fetch', 'blocked_policy') from exc
        if not ips or any(not ip.is_global for ip in ips):
            raise CollectionBlocked('Target resolved to a non-public IP', 'blocked_policy')
        client = httpx.Client(timeout=12, follow_redirects=False, trust_env=False,
                              headers={'User-Agent': USER_AGENT})
    try:
        try:
            with client.stream('GET', robots_url) as robots:
                if robots.status_code != 200:
                    # Do not infer permission when robots is missing, blocked or redirects.
                    raise CollectionBlocked('robots.txt did not return HTTP 200; no online fetch',
                                            'blocked_robots', robots.status_code)
                robots_bytes = _read_limited(
                    robots, MAX_ROBOTS_BYTES, 'blocked_robots', 'robots.txt unexpectedly large')
        except httpx.HTTPError as exc:
            raise CollectionBlocked('robots.txt unavailable; failing closed', 'blocked_robots') from exc
        parser = RobotFileParser()
        parser.parse(robots_bytes.decode('utf-8', errors='replace').splitlines())
        if not parser.can_fetch(USER_AGENT, source_url):
            raise CollectionBlocked('robots.txt disallows this page', 'blocked_robots')
        delay = parser.crawl_delay(USER_AGENT)
        if delay is not None and delay > min_delay_seconds:
            raise CollectionBlocked('robots crawl-delay exceeds worker interval', 'blocked_robots')
        rate = parser.request_rate(USER_AGENT)
        if rate is not None and rate.requests > 0 and rate.seconds / rate.requests > min_delay_seconds:
            raise CollectionBlocked('robots request-rate exceeds worker interval', 'blocked_robots')
        if before_page_request is not None:
            before_page_request()
        try:
            with client.stream('GET', source_url) as response:
                if response.status_code in (401, 403, 429) or 300 <= response.status_code < 400:
                    raise CollectionBlocked('Source rejected or redirected request; no bypass',
                                            'blocked_upstream', response.status_code)
                if response.status_code != 200:
                    raise CollectionBlocked(f'Source HTTP status {response.status_code}',
                                            'failed', response.status_code)
                if 'text/html' not in response.headers.get('content-type', '').lower():
                    raise CollectionBlocked('Unexpected response content type', 'failed', response.status_code)
                page_bytes = _read_limited(
                    response, MAX_PAGE_BYTES, 'failed', 'Page size over configured maximum')
                page = page_bytes.decode(response.encoding or 'utf-8', errors='replace')
        except httpx.HTTPError as exc:
            raise CollectionBlocked('HTML fetch failed', 'failed') from exc
        if _is_access_challenge(page):
            raise CollectionBlocked('Source returned an access verification challenge; no bypass',
                                    'blocked_upstream', response.status_code)
        return page
    finally:
        if own_client:
            client.close()
