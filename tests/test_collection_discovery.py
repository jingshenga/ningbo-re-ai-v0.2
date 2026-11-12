import pytest
from bs4.element import Tag
from app.collectors.discovery import discover_listing_links
from app.collectors.url_policy import CollectionError, source_page_key


@pytest.mark.parametrize(('source', 'page_url', 'detail_url', 'listing_id', 'expected_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/',
     '/ershoufang/109900001234.html', '109900001234',
     'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/',
     '/sale/1234567.html', '1234567',
     'https://ningbo.anjuke.com/sale/1234567.html'),
])
def test_discovery_extracts_same_source_listing_links(
        source, page_url, detail_url, listing_id, expected_url):
    result = discover_listing_links(
        source, page_url,
        f'<main><a href="{detail_url}">listing</a></main>')

    assert [(item.source_listing_id, item.url) for item in result.listings] == [
        (listing_id, expected_url)
    ]
    assert result.next_page_url is None
    assert result.warnings == ()


def test_discovery_deduplicates_by_source_listing_id_and_prior_ids():
    result = discover_listing_links('beike', 'https://nb.ke.com/ershoufang/', '''
      <a href="/ershoufang/109900001234.html">first</a>
      <a href="/ershoufang/109900001234.html/">duplicate</a>
      <a href="/ershoufang/109900005678.html">seen</a>
    ''', seen_ids={'109900005678'})

    assert [item.source_listing_id for item in result.listings] == ['109900001234']
    assert [item.source_listing_id for item in result.observed_listings] == [
        '109900001234', '109900005678'
    ]


def test_discovery_reports_seen_ids_separately_from_new_detail_queue():
    result = discover_listing_links('beike', 'https://nb.ke.com/ershoufang/',
                                    '<a href="/ershoufang/109900001234.html">seen</a>',
                                    seen_ids={'109900001234'})

    assert result.listings == ()
    assert [item.source_listing_id for item in result.observed_listings] == ['109900001234']


def test_discovery_ignores_external_query_and_non_detail_links():
    result = discover_listing_links('beike', 'https://nb.ke.com/ershoufang/', '''
      <a href="https://evil.example/ershoufang/109900001234.html">external</a>
      <a href="/ershoufang/109900001234.html?token=secret">query</a>
      <a href="/ershoufang/">not a detail page</a>
    ''')

    assert result.listings == ()


def test_discovery_ignores_hidden_and_non_content_links():
    result = discover_listing_links('beike', 'https://nb.ke.com/ershoufang/', '''
      <nav><a href="/ershoufang/109900001234.html">navigation</a></nav>
      <aside><a href="/ershoufang/109900005678.html">recommendation</a></aside>
      <div hidden><a href="/ershoufang/109900009999.html">hidden</a></div>
      <div style="display:none"><a href="/ershoufang/109900008888.html">hidden</a></div>
      <div style="visibility:hidden"><a href="/ershoufang/109900006666.html">hidden</a>
        <a style="visibility:visible" href="/ershoufang/109900006667.html">visible child</a></div>
      <div style="opacity:0"><a href="/ershoufang/109900006668.html">transparent</a></div>
      <div style="content-visibility:hidden"><a href="/ershoufang/109900006669.html">skipped</a></div>
      <details><summary><a href="/ershoufang/109900006670.html">summary</a></summary>
        <a href="/ershoufang/109900006671.html">collapsed content</a></details>
      <main><a aria-hidden="true" href="/ershoufang/109900007777.html">visible link</a></main>
    ''')

    assert [item.source_listing_id for item in result.listings] == [
        '109900006667', '109900006670', '109900007777']


def test_discovery_walks_existing_contents_without_copying_children(monkeypatch):
    def copied_children_is_forbidden(_tag):
        raise AssertionError('discovery should read the existing contents list')

    monkeypatch.setattr(Tag, 'children', property(copied_children_is_forbidden))
    result = discover_listing_links('beike', 'https://nb.ke.com/ershoufang/', '''
      <main><a href="/ershoufang/109900001234.html">listing</a></main>
      <details><summary><a href="/ershoufang/109900005678.html">summary</a></summary>
        <a href="/ershoufang/109900009999.html">collapsed</a></details>
    ''')

    assert [item.source_listing_id for item in result.listings] == [
        '109900001234', '109900005678']


def test_discovery_returns_safe_rel_next_path_and_warns_on_unsupported_cursor():
    result = discover_listing_links('beike', 'https://nb.ke.com/ershoufang/page1', '''
      <a rel="next" href="/ershoufang/page2">next</a>
      <a rel="next" href="/ershoufang/page3?cursor=secret">unsupported</a>
      <a href="/ershoufang/109900001234.html">listing</a>
    ''')

    assert result.next_page_url == 'https://nb.ke.com/ershoufang/page2'
    assert result.warnings == ('unsupported_next_page_url',)


@pytest.mark.parametrize('next_url', [
    'https://NB.KE.COM:443/ershoufang/page1',
    'https://nb.ke.com./ershoufang/page1',
    'https://nb.ke.com/ershoufang/%70age1',
])
def test_discovery_detects_pagination_loops_across_authority_aliases(next_url):
    result = discover_listing_links(
        'beike', 'https://nb.ke.com/ershoufang/page1',
        f'<head><link rel="next" href="{next_url}"></head>')

    assert result.next_page_url is None
    assert result.warnings == ('pagination_loop',)


def test_discovery_deduplicates_equivalent_next_page_authorities():
    result = discover_listing_links(
        'beike', 'https://nb.ke.com/ershoufang/page1',
        '<head><link rel="next" href="https://NB.KE.COM:443/ershoufang/page2">'
        '<link rel="next" href="https://nb.ke.com./ershoufang/page2"></head>')

    assert result.next_page_url == 'https://NB.KE.COM:443/ershoufang/page2'
    assert result.warnings == ()


def test_discovery_deduplicates_unicode_iri_and_utf8_encoded_next_urls():
    result = discover_listing_links(
        'beike', 'https://nb.ke.com/ershoufang/page1',
        '<head><link rel="next" href="/ershoufang/%E5%B0%8F%E5%8C%BA">'
        '<link rel="next" href="/ershoufang/小区"></head>')

    assert result.next_page_url == 'https://nb.ke.com/ershoufang/%E5%B0%8F%E5%8C%BA'
    assert result.warnings == ()


def test_discovery_detects_unicode_iri_and_utf8_encoded_pagination_loop():
    result = discover_listing_links(
        'beike', 'https://nb.ke.com/ershoufang/小区',
        '<head><link rel="next" href="/ershoufang/%E5%B0%8F%E5%8C%BA"></head>')

    assert result.next_page_url is None
    assert result.warnings == ('pagination_loop',)


def test_source_page_key_rejects_invalid_unicode_path():
    with pytest.raises(CollectionError, match='valid Unicode text'):
        source_page_key('beike', 'https://nb.ke.com/ershoufang/\ud800')


@pytest.mark.parametrize('next_url', [
    'https://nb.ke.com/ershoufang/PAGE1',
    'https://nb.ke.com/ershoufang/page%2F1',
])
def test_discovery_keeps_case_and_reserved_path_octets_distinct(next_url):
    result = discover_listing_links(
        'beike', 'https://nb.ke.com/ershoufang/page1',
        f'<head><link rel="next" href="{next_url}"></head>')

    assert result.next_page_url == next_url
    assert result.warnings == ()


@pytest.mark.parametrize(('source', 'page_url', 'html'), [
    ('unknown', 'https://nb.ke.com/ershoufang/', '<html></html>'),
    ('beike', 'https://evil.example/ershoufang/', '<html></html>'),
])
def test_discovery_rejects_unsupported_source_or_page_url(source, page_url, html):
    with pytest.raises(CollectionError):
        discover_listing_links(source, page_url, html)


def test_discovery_rejects_oversized_html():
    with pytest.raises(CollectionError, match='1000000 UTF-8 bytes'):
        discover_listing_links('beike', 'https://nb.ke.com/ershoufang/', 'x' * 1_000_001)


def test_discovery_rejects_utf8_oversized_html_below_character_limit():
    html = '界' * 333_334
    assert len(html) < 1_000_000

    with pytest.raises(CollectionError, match='1000000 UTF-8 bytes'):
        discover_listing_links('beike', 'https://nb.ke.com/ershoufang/', html)
