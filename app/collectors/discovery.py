"""Offline extraction of source listing links from operator-saved HTML pages."""

from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup, Tag

from app.collectors.anjuke import extract_source_id as extract_anjuke_source_id
from app.collectors.beike import extract_source_id as extract_beike_source_id
from app.collectors.parser import (
    _inline_content_visibility_hidden, _inline_css_value, _inline_display_none,
    _inline_display_overrides_hidden, _inline_opacity_zero,
)
from app.collectors.url_policy import CollectionError, check_source_url, source_page_key


MAX_HTML_BYTES = 1_000_000
SOURCE_ID_EXTRACTORS = {
    'beike': extract_beike_source_id,
    'anjuke': extract_anjuke_source_id,
}


@dataclass(frozen=True)
class DiscoveredListing:
    source_listing_id: str
    url: str


@dataclass(frozen=True)
class DiscoveryResult:
    listings: tuple[DiscoveredListing, ...]
    observed_listings: tuple[DiscoveredListing, ...]
    next_page_url: str | None
    warnings: tuple[str, ...]


def _visible_anchors(soup: BeautifulSoup) -> list[Tag]:
    anchors = []
    pending = [(soup, False, False, False)]
    while pending:
        parent, inherited_hidden, ancestor_opacity_zero, ancestor_content_hidden = pending.pop()
        if (isinstance(parent, Tag) and parent.name == 'a' and parent.has_attr('href')
                and not inherited_hidden and not ancestor_opacity_zero
                and not ancestor_content_hidden):
            anchors.append(parent)
        if isinstance(parent, Tag) and parent.name == 'details' and not parent.has_attr('open'):
            summary = next((child for child in parent.contents
                            if isinstance(child, Tag) and child.name == 'summary'), None)
            children = (summary,) if summary else ()
        else:
            children = parent.contents
        for child in reversed(children):
            if not isinstance(child, Tag):
                continue
            visibility = _inline_css_value(child.get('style', ''), 'visibility')
            if visibility in ('hidden', 'collapse'):
                hidden = True
            elif visibility in ('visible', 'initial'):
                hidden = False
            else:
                hidden = inherited_hidden
            opacity_zero = ancestor_opacity_zero or _inline_opacity_zero(child.get('style', ''))
            content_hidden = (ancestor_content_hidden
                              or _inline_content_visibility_hidden(child.get('style', '')))
            if opacity_zero or content_hidden:
                continue
            pending.append((child, hidden, opacity_zero, content_hidden))
    return anchors


def _safe_same_source_url(source: str, page_url: str, href: str) -> str | None:
    if (not isinstance(href, str) or not href
            or any(char.isspace() or ord(char) < 0x20 or 0x7f <= ord(char) <= 0x9f
                   for char in href)):
        return None
    try:
        resolved = urljoin(page_url, href)
        parsed = urlsplit(resolved)
        if parsed.query or parsed.fragment:
            return None
        check_source_url(source, resolved)
    except (CollectionError, ValueError):
        return None
    return resolved


def discover_listing_links(source: str, page_url: str, html: str,
                           seen_ids: set[str] | None = None) -> DiscoveryResult:
    """Extract unique same-source detail links without making network requests."""
    if source not in SOURCE_ID_EXTRACTORS:
        raise CollectionError('Unsupported collection source')
    check_source_url(source, page_url)
    if not isinstance(html, str):
        raise CollectionError('HTML must be text')
    if len(html) > MAX_HTML_BYTES:
        raise CollectionError('HTML must not exceed 1000000 UTF-8 bytes')
    try:
        size = len(html.encode('utf-8'))
    except UnicodeEncodeError as exc:
        raise CollectionError('HTML must be valid UTF-8 text') from exc
    if size > MAX_HTML_BYTES:
        raise CollectionError('HTML must not exceed 1000000 UTF-8 bytes')

    parser = BeautifulSoup(html, 'html.parser')
    for tag in parser(['script', 'style', 'template', 'nav', 'menu', 'aside', 'footer', 'noscript',
                       'svg', 'iframe', 'object', 'embed', 'canvas', 'form', 'button',
                       'select', 'textarea']):
        if tag.parent is not None:
            tag.decompose()
    for tag in parser.find_all('dialog'):
        if tag.parent is not None and not tag.has_attr('open'):
            tag.decompose()
    for tag in parser.select('[hidden]'):
        if tag.parent is None:
            continue
        hidden_value = str(tag.get('hidden', '')).strip().lower()
        if (hidden_value == 'until-found'
                or not _inline_display_overrides_hidden(tag.get('style', ''))):
            tag.decompose()
    for tag in parser.find_all(style=True):
        if tag.parent is not None and _inline_display_none(tag.get('style', '')):
            tag.decompose()
    extractor = SOURCE_ID_EXTRACTORS[source]
    page_ids = set(seen_ids or ())
    observed_ids = set()
    listings = []
    observed_listings = []
    next_urls = {}
    rejected_next = False

    head = parser.head
    for link in (head.find_all('link') if head else []):
        rel = link.get('rel', [])
        if isinstance(rel, str):
            rel = rel.split()
        if not any(token.lower() == 'next' for token in rel):
            continue
        safe_url = _safe_same_source_url(source, page_url, link.get('href'))
        if safe_url:
            next_urls.setdefault(source_page_key(source, safe_url), safe_url)
        else:
            rejected_next = True

    for anchor in _visible_anchors(parser):
        href = anchor.get('href')
        safe_url = _safe_same_source_url(source, page_url, href)
        rel = anchor.get('rel', [])
        if isinstance(rel, str):
            rel = rel.split()
        if any(token.lower() == 'next' for token in rel):
            if safe_url:
                next_urls.setdefault(source_page_key(source, safe_url), safe_url)
            else:
                rejected_next = True
            continue
        if safe_url is None:
            continue
        try:
            listing_id = extractor(safe_url)
        except CollectionError:
            continue
        if listing_id is None or listing_id in observed_ids:
            continue
        observed_ids.add(listing_id)
        discovered = DiscoveredListing(listing_id, safe_url)
        observed_listings.append(discovered)
        if listing_id not in page_ids:
            page_ids.add(listing_id)
            listings.append(discovered)

    warnings = []
    next_page_url = None
    if len(next_urls) == 1:
        next_page_url = next(iter(next_urls.values()))
        if source_page_key(source, next_page_url) == source_page_key(source, page_url):
            next_page_url = None
            warnings.append('pagination_loop')
    elif len(next_urls) > 1:
        warnings.append('conflicting_next_page_links')
    if rejected_next:
        warnings.append('unsupported_next_page_url')
    return DiscoveryResult(tuple(listings), tuple(observed_listings), next_page_url,
                           tuple(warnings))
