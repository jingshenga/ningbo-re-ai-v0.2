"""DTK v5 author-post REST adapter: documented API, no platform-request implementation."""
from dataclasses import dataclass
from datetime import datetime, timezone
import time
from urllib.parse import quote, urlsplit
import httpx

PAGE_SIZE = 20


def _has_unpersistable_text(value) -> bool:
    return isinstance(value, str) and (
        '\x00' in value or any(0xD800 <= ord(char) <= 0xDFFF for char in value)
    )


class DtkError(RuntimeError):
    pass


@dataclass
class Page:
    items: list[dict]
    next_cursor: str | None
    has_more: bool
    guest_fallback: bool = False


def normalize_datetime(value):
    if value is None or value == '':
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
        try:
            timestamp = float(value)
        except (OverflowError, ValueError):
            return None
        if timestamp >= 1e12:
            timestamp /= 1000
        try:
            return datetime.fromtimestamp(timestamp, timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return parsed if parsed.tzinfo is not None else None
        except ValueError:
            return None
    return None


def _first_text(*values):
    return next((value for value in values if isinstance(value, str) and value.strip()), '')


def _safe_post_url(value, post_id: str) -> str:
    fallback = f'https://www.douyin.com/video/{quote(post_id, safe="")}'
    if not isinstance(value, str) or _has_unpersistable_text(value):
        return fallback
    if any(ord(char) < 0x20 or 0x7f <= ord(char) <= 0x9f for char in value):
        return fallback
    candidate = value.strip()
    if not candidate or len(candidate) > 2000 or any(char.isspace() for char in candidate):
        return fallback
    try:
        parts = urlsplit(candidate)
        port = parts.port
    except ValueError:
        return fallback
    hostname = parts.hostname
    host = hostname.lower() if hostname else ''
    if host.endswith('.'):
        host = host[:-1]
    allowed_host = any(host == domain or host.endswith('.' + domain)
                       for domain in ('douyin.com', 'iesdouyin.com'))
    if (parts.scheme.lower() != 'https' or not hostname or any(char.isspace() for char in hostname)
            or not allowed_host or parts.username is not None or parts.password is not None
            or port not in (None, 443)):
        return fallback
    return candidate


def normalize_post(item: dict) -> dict | None:
    """Accept common normalized post keys. Unknown payloads are skipped + logged, not guessed."""
    if not isinstance(item, dict):
        return None
    post_id = item.get('aweme_id') or item.get('post_id') or item.get('id') or item.get('video_id')
    if isinstance(post_id, bool) or not isinstance(post_id, (str, int)) or not str(post_id).strip():
        return None
    post_id = str(post_id).strip()
    author = item.get('author') or {}
    if not isinstance(author, dict):
        author = {}
    text_values = (post_id, author.get('nickname'), item.get('author_name'), item.get('title'),
                   item.get('desc'), item.get('description'), item.get('poi_name'))
    if any(_has_unpersistable_text(value) for value in text_values):
        raise DtkError('DTK post contains text that PostgreSQL cannot store')
    title = _first_text(item.get('title'), item.get('desc'), item.get('description'))
    published = (item.get('published_at') or item.get('created_at') or
                 item.get('create_time') or item.get('publish_time'))
    url = item.get('web_url') or item.get('share_url') or item.get('url')
    if isinstance(url, dict):
        url_list = url.get('url_list')
        url = url.get('url') or (url_list[0] if isinstance(url_list, list) and url_list else None)
    url = _safe_post_url(url, post_id)
    record = {
        'platform': 'douyin',
        'source_post_id': str(post_id),
        'source_url': str(url),
        'author_name': _first_text(author.get('nickname'), item.get('author_name')),
        'title': title,
        'description': _first_text(item.get('description'), item.get('desc')),
        'published_at': normalize_datetime(published),
        'raw_location': item.get('poi_name') if isinstance(item.get('poi_name'), str) else None,
        'permission_note': 'Imported from operator-controlled DTK instance; verify platform and reuse rights.',
    }
    field_limits = {'source_post_id': 220, 'author_name': 200, 'title': 2000, 'raw_location': 300}
    oversized_fields = [field for field, limit in field_limits.items()
                        if record[field] is not None and len(record[field]) > limit]
    if oversized_fields:
        raise DtkError('DTK post fields exceed supported storage lengths')
    return record


def _unwrap_envelope(response: httpx.Response) -> dict:
    try:
        body = response.json()
    except ValueError as exc:
        response.raise_for_status()
        raise DtkError('DTK returned non-JSON response') from exc
    if not isinstance(body, dict):
        raise DtkError('DTK response must be an object')
    if body.get('success') is not True:
        err = body.get('error')
        if not isinstance(err, dict):
            err = {}
        raise DtkError(f"DTK: {err.get('code', 'unknown')} {err.get('message', '')}")
    response.raise_for_status()
    result = body.get('data')
    if not isinstance(result, dict):
        raise DtkError('DTK response missing data object')
    return body


def parse_page(body: dict) -> Page:
    """Parse completed query (`data.items`) or task result (`data.data.items`)."""
    if not isinstance(body, dict):
        raise DtkError('DTK response must be an object')
    wrapper = body.get('data')
    if wrapper is None:
        wrapper = {}
    if not isinstance(wrapper, dict):
        raise DtkError('DTK response data must be an object')
    task_meta = wrapper.get('result_meta')
    if task_meta is None:
        task_meta = {}
    if not isinstance(task_meta, dict):
        raise DtkError('DTK result_meta must be an object')
    nested_data = wrapper.get('data')
    if nested_data is not None and not isinstance(nested_data, dict):
        raise DtkError('DTK nested data must be an object')
    payload = nested_data if isinstance(nested_data, dict) else wrapper
    items = payload.get('items')
    if not isinstance(items, list):
        raise DtkError('DTK returned no items list; check upstream schema/version')
    if len(items) > PAGE_SIZE:
        raise DtkError('DTK page exceeds requested limit')
    meta = body.get('meta')
    if meta is None:
        meta = {}
    if not isinstance(meta, dict):
        raise DtkError('DTK meta must be an object')
    cursor_meta = task_meta.get('cursor')
    if cursor_meta is None:
        cursor_meta = meta.get('cursor')
    if cursor_meta is None:
        cursor_meta = {}
    if not isinstance(cursor_meta, dict):
        raise DtkError('DTK cursor metadata must be an object')
    next_cursor = payload.get('cursor')
    if next_cursor in (None, ''):
        next_cursor = cursor_meta.get('next')
    if next_cursor == '':
        next_cursor = None
    if next_cursor is not None and (isinstance(next_cursor, bool) or not isinstance(next_cursor, (str, int))):
        raise DtkError('DTK cursor must be a string or integer')
    if isinstance(next_cursor, str) and not next_cursor.strip():
        raise DtkError('DTK cursor must not be blank')
    has_more = payload.get('has_more')
    if has_more is None:
        has_more = cursor_meta.get('has_more')
    if has_more is None:
        has_more = next_cursor is not None
    if not isinstance(has_more, bool):
        raise DtkError('DTK has_more must be a boolean')
    guest_fallback = task_meta.get('guest_fallback')
    if guest_fallback is None:
        guest_fallback = meta.get('guest_fallback', False)
    if guest_fallback is None:
        guest_fallback = False
    if not isinstance(guest_fallback, bool):
        raise DtkError('DTK guest_fallback must be a boolean')
    return Page(items, str(next_cursor) if next_cursor is not None else None, has_more, guest_fallback)


class DtkClient:
    def __init__(self, base_url: str, api_key: str):
        if not base_url or not api_key:
            raise DtkError('DTK_BASE_URL / DTK_API_KEY not configured')
        self.client = httpx.Client(base_url=base_url, headers={'X-API-Key': api_key}, timeout=30)

    def close(self):
        self.client.close()

    def author_posts(self, account_ref: str, cursor: str | None = None) -> Page:
        params = {'count': PAGE_SIZE, 'wait': 15}
        if urlsplit(account_ref).scheme.lower() == 'https':
            params['url'] = account_ref
        else:
            params['sec_user_id'] = account_ref
        if cursor:
            params['cursor'] = cursor
        resp = self.client.get('/api/v1/douyin/user/posts', params=params)
        body = _unwrap_envelope(resp)
        if resp.status_code == 202 or ('task_id' in body['data'] and 'items' not in body['data']):
            task_id = body['data'].get('task_id')
            if isinstance(task_id, bool) or not isinstance(task_id, (str, int)) or not str(task_id).strip():
                raise DtkError('DTK task response has missing or invalid task_id')
            task_id = quote(str(task_id).strip(), safe='')
            deadline = time.monotonic() + 52.5
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                time.sleep(min(1.5, remaining))
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                task_body = _unwrap_envelope(self.client.get(
                    f'/api/v1/tasks/{task_id}', timeout=min(30.0, remaining)))
                task = task_body['data']
                state = task.get('state')
                if not isinstance(state, str) or not state.strip():
                    raise DtkError('DTK task state is missing or invalid')
                state = state.strip()
                if state == 'done':
                    return parse_page(task_body)
                if state == 'failed':
                    raise DtkError('DTK task failed')
            raise DtkError('DTK task did not finish within 52 seconds')
        return parse_page(body)
