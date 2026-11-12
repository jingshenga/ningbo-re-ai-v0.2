"""Bounded, atomic local state for offline listing-page discovery."""
import json
import os
from pathlib import Path
import re
import tempfile

from app.collectors.url_policy import CollectionError, check_source_url, source_page_key

MAX_STATE_BYTES = 2_000_000


def _validate_state_path(path: Path):
    if path.is_symlink():
        raise ValueError('Discovery state must not be a symlink')
    if path.exists() and not path.is_file():
        raise ValueError('Discovery state must be a regular file')


def new_state(source: str):
    return {'version': 1, 'source': source, 'seen_ids': [],
            'last_page_url': None, 'next_page_url': None, 'visited_page_urls': [],
            'last_attempted_page_url': None, 'last_error_type': None,
            'failed_attempts': 0}


def read_seen_ids(path: Path, source: str) -> set[str]:
    if source not in ('beike', 'anjuke'):
        raise ValueError('Seen IDs source is unsupported')
    if path.is_symlink():
        raise ValueError('Seen IDs input must not be a symlink')
    if path.exists() and not path.is_file():
        raise ValueError('Seen IDs input must be a regular file')
    with path.open('rb') as stream:
        raw = stream.read(MAX_STATE_BYTES + 1)
    if len(raw) > MAX_STATE_BYTES:
        raise ValueError('Seen IDs file exceeds 2000000 byte limit')
    try:
        lines = raw.decode('utf-8').splitlines()
    except UnicodeError as exc:
        raise ValueError('Seen IDs file is not valid UTF-8') from exc
    minimum_length = 8 if source == 'beike' else 7
    pattern = re.compile(rf'[0-9]{{{minimum_length},220}}')
    seen_ids = set()
    for line in lines:
        value = line.strip()
        if not value:
            continue
        if not pattern.fullmatch(value):
            raise ValueError('Seen IDs file contains an invalid listing ID')
        seen_ids.add(value)
    return seen_ids


def load_state(path: Path, source: str):
    _validate_state_path(path)
    if not path.exists():
        return new_state(source)
    with path.open('rb') as stream:
        raw = stream.read(MAX_STATE_BYTES + 1)
    if len(raw) > MAX_STATE_BYTES:
        raise ValueError('Discovery state exceeds 2000000 byte limit')
    try:
        state = json.loads(raw.decode('utf-8'))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError('Discovery state is not valid UTF-8 JSON') from exc
    if (not isinstance(state, dict) or type(state.get('version')) is not int
            or state.get('version') != 1 or state.get('source') != source
            or not isinstance(state.get('seen_ids'), list)
            or not isinstance(state.get('visited_page_urls', []), list)
            or type(state.get('failed_attempts', 0)) is not int
            or state.get('failed_attempts', 0) < 0
            or (state.get('last_error_type') is not None
                and (not isinstance(state['last_error_type'], str)
                     or not state['last_error_type'].isidentifier()
                     or len(state['last_error_type']) > 80))
            or any(not isinstance(value, str)
                   or not re.fullmatch(rf'[0-9]{{{8 if source == "beike" else 7},220}}', value)
                   for value in state['seen_ids'])):
        raise ValueError('Discovery state has an invalid schema or source')
    state.setdefault('visited_page_urls', [state['last_page_url']]
                     if state.get('last_page_url') else [])
    state.setdefault('last_attempted_page_url', None)
    state.setdefault('last_error_type', None)
    state.setdefault('failed_attempts', 0)
    page_urls = [state.get('last_page_url'), state.get('next_page_url'),
                 state.get('last_attempted_page_url'), *state['visited_page_urls']]
    for value in page_urls:
        if value is not None:
            try:
                check_source_url(source, value)
            except CollectionError as exc:
                raise ValueError('Discovery state contains an invalid page URL') from exc
    next_page_url = state.get('next_page_url')
    if next_page_url:
        next_page_key = source_page_key(source, next_page_url)
        if any(value is not None and source_page_key(source, value) == next_page_key
               for value in (state.get('last_page_url'), *state['visited_page_urls'])):
            raise ValueError('Discovery state contains a pagination loop')
    return state


def save_state(path: Path, state: dict):
    content = (json.dumps(state, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    if len(content) > MAX_STATE_BYTES:
        raise ValueError('Discovery state exceeds 2000000 byte limit')
    _validate_state_path(path)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f'.{path.name}.',
                                         suffix='.tmp', delete=False) as stream:
            temp_path = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def record_failure(path: Path | None, state: dict | None, source: str,
                   page_url: str | None, error: Exception) -> bool:
    """Record a retryable failure; return false if the state could not be saved."""
    if state is None or page_url is None:
        return True
    try:
        check_source_url(source, page_url)
    except CollectionError:
        return True
    page_key = source_page_key(source, page_url)
    visited = (state.get('last_page_url'), *state.get('visited_page_urls', []))
    if all(value is None or source_page_key(source, value) != page_key for value in visited):
        state['next_page_url'] = page_url
    state['last_attempted_page_url'] = page_url
    state['last_error_type'] = type(error).__name__
    state['failed_attempts'] += 1
    if path is None:
        return False
    try:
        save_state(path, state)
    except (OSError, ValueError):
        return False
    return True
