"""Shared source URL allowlist and structural validation."""

import re
from urllib.parse import urlsplit


ALLOWED_HOSTS = {'beike': 'nb.ke.com', 'anjuke': 'ningbo.anjuke.com'}


class CollectionError(ValueError):
    """Invalid or unprocessable collection input."""


def check_source_url(source: str, url: str) -> str:
    """Allow only a Ningbo source HTTPS host; no credentials/custom ports."""
    if source not in ALLOWED_HOSTS:
        raise CollectionError('Unsupported collection source')
    if not isinstance(url, str) or not 12 <= len(url) <= 2000:
        raise CollectionError('Collection URL must be between 12 and 2000 characters')
    if any(char.isspace() or ord(char) < 0x20 or 0x7f <= ord(char) <= 0x9f
           for char in url):
        raise CollectionError('Collection URL must not contain whitespace or control characters')
    try:
        parsed = urlsplit(url)
    except ValueError as exc:
        raise CollectionError('Malformed collection URL') from exc
    host = (parsed.hostname or '').lower()
    if host.endswith('.'):
        host = host[:-1]
    expected_host = ALLOWED_HOSTS[source]
    try:
        port = parsed.port
    except ValueError as exc:
        raise CollectionError('Malformed URL port') from exc
    if '?' in url or '#' in url:
        raise CollectionError('Collection URL must omit query and fragment data')
    if (parsed.scheme != 'https' or not host or parsed.username is not None or parsed.password is not None or
            port not in (None, 443) or host != expected_host):
        raise CollectionError(
            f'Expected HTTPS URL on {expected_host} without credentials or custom port')
    return url


def source_page_key(source: str, url: str) -> tuple[str, str, str]:
    """Return a comparison key for equivalent source page URLs."""
    check_source_url(source, url)
    parsed = urlsplit(url)
    host = (parsed.hostname or '').lower().rstrip('.')

    def normalize_escape(match):
        value = int(match.group(1), 16)
        char = chr(value)
        if char.isascii() and (char.isalnum() or char in '-._~'):
            return char
        return f'%{value:02X}'

    path = re.sub(r'%([0-9a-fA-F]{2})', normalize_escape, parsed.path or '/')
    try:
        path = ''.join(char if char.isascii() else ''.join(
            f'%{byte:02X}' for byte in char.encode('utf-8')) for char in path)
    except UnicodeEncodeError as exc:
        raise CollectionError('Collection URL path must contain valid Unicode text') from exc
    return parsed.scheme.lower(), host, path
