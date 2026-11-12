"""Conservative, evidence-first, per-source collection adapters."""
from __future__ import annotations

from typing import TYPE_CHECKING

from app.collectors.url_policy import ALLOWED_HOSTS, CollectionError, check_source_url

if TYPE_CHECKING:
    from app.collectors.parser import ParseResult


def _parse_beike(source_url: str, html: str):
    from app.collectors.beike import parse_listing_html
    return parse_listing_html(source_url, html)


def _parse_anjuke(source_url: str, html: str):
    from app.collectors.anjuke import parse_listing_html
    return parse_listing_html(source_url, html)


def _extract_beike(source_url: str) -> str | None:
    from app.collectors.beike import extract_source_id
    return extract_source_id(source_url)


def _extract_anjuke(source_url: str) -> str | None:
    from app.collectors.anjuke import extract_source_id
    return extract_source_id(source_url)


PARSERS = {'beike': _parse_beike, 'anjuke': _parse_anjuke}
SOURCE_ID_EXTRACTORS = {'beike': _extract_beike, 'anjuke': _extract_anjuke}
__all__ = ['ALLOWED_HOSTS', 'CollectionError', 'PARSERS', 'SOURCE_ID_EXTRACTORS',
           'check_source_url', 'extract_source_id', 'parse_listing_html', 'ParseResult']


def __getattr__(name: str):
    if name == 'ParseResult':
        from app.collectors.parser import ParseResult
        return ParseResult
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')


def parse_listing_html(source: str, source_url: str, html: str) -> ParseResult:
    parser = PARSERS.get(source)
    if parser is None:
        raise CollectionError('Unsupported collection source')
    return parser(source_url, html)


def extract_source_id(source: str, source_url: str) -> str | None:
    extractor = SOURCE_ID_EXTRACTORS.get(source)
    if extractor is None:
        raise CollectionError('Unsupported collection source')
    return extractor(source_url)
