import json
from pathlib import Path
import subprocess
import sys


def test_discovery_cli_reads_local_snapshot_and_filters_seen_ids(tmp_path):
    root = Path(__file__).resolve().parents[1]
    sample = tmp_path / 'list.html'
    sample.write_text('''
      <a href="/ershoufang/109900001234.html">new listing</a>
      <a href="/ershoufang/109900005678.html">seen listing</a>
      <a rel="next" href="/ershoufang/page2">next page</a>
    ''', encoding='utf-8')
    seen = tmp_path / 'seen.txt'
    seen.write_text('109900005678\n', encoding='utf-8')

    result = subprocess.run(
        [sys.executable, str(root / 'scripts/discover_listing_urls.py'),
         '--source', 'beike', '--page-url', 'https://nb.ke.com/ershoufang/',
         '--html', str(sample), '--seen-ids', str(seen)],
        cwd=root, capture_output=True, text=True, check=False,
    )

    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output['network_accessed'] is False
    assert [row['source_listing_id'] for row in output['listings']] == ['109900001234']
    assert output['next_page_url'] == 'https://nb.ke.com/ershoufang/page2'


def test_discovery_cli_rejects_oversized_html_before_full_read(tmp_path):
    root = Path(__file__).resolve().parents[1]
    sample = tmp_path / 'oversized.html'
    sample.write_bytes(b'x' * 1_000_001)

    result = subprocess.run(
        [sys.executable, str(root / 'scripts/discover_listing_urls.py'),
         '--source', 'beike', '--page-url', 'https://nb.ke.com/ershoufang/',
         '--html', str(sample)],
        cwd=root, capture_output=True, text=True, check=False,
    )

    assert result.returncode == 2
    assert 'HTML sample exceeds 1000000 byte limit' in result.stderr


def test_discovery_uses_safe_head_link_next_page():
    from app.collectors.discovery import discover_listing_links

    result = discover_listing_links(
        'beike', 'https://nb.ke.com/ershoufang/',
        '<html><head><link rel="prev NEXT" href="/ershoufang/page2"></head>'
        '<body><main>列表页</main></body></html>')

    assert result.next_page_url == 'https://nb.ke.com/ershoufang/page2'
    assert not result.warnings


def test_discovery_rejects_unsafe_head_link_next_page():
    from app.collectors.discovery import discover_listing_links

    result = discover_listing_links(
        'beike', 'https://nb.ke.com/ershoufang/',
        '<html><head><link rel="next" href="https://other.example/page2"></head>'
        '<body><main>列表页</main></body></html>')

    assert result.next_page_url is None
    assert result.warnings == ('unsupported_next_page_url',)


def test_discovery_rejects_oversized_character_count_before_utf8_encoding():
    import pytest

    from app.collectors.discovery import discover_listing_links
    from app.collectors.url_policy import CollectionError

    class OversizedHtml(str):
        def encode(self, *args, **kwargs):
            raise AssertionError('oversized input must be rejected before encoding')

    html = OversizedHtml('x' * 1_000_001)

    with pytest.raises(CollectionError, match='UTF-8 bytes'):
        discover_listing_links('beike', 'https://nb.ke.com/ershoufang/', html)


def test_discovery_stops_self_referential_next_page():
    from app.collectors.discovery import discover_listing_links

    result = discover_listing_links(
        'beike', 'https://nb.ke.com/ershoufang/',
        '<html><head><link rel="next" href="/ershoufang/"></head>'
        '<body><main>列表页</main></body></html>')

    assert result.next_page_url is None
    assert result.warnings == ('pagination_loop',)


def test_discovery_ignores_menu_detail_links_but_keeps_listing_links():
    from app.collectors.discovery import discover_listing_links

    result = discover_listing_links(
        'beike', 'https://nb.ke.com/ershoufang/',
        '<html><body><menu><a href="/ershoufang/109900001234.html">menu</a></menu>'
        '<main><article><a href="/ershoufang/109900005678.html">listing</a></article>'
        '</main></body></html>')

    assert [item.source_listing_id for item in result.listings] == ['109900005678']


def test_discovery_cli_persists_cursor_and_seen_ids(tmp_path):
    root = Path(__file__).resolve().parents[1]
    state = tmp_path / 'discovery-state.json'
    first_page = tmp_path / 'first.html'
    first_page.write_text(
        '<html><head><link rel="next" href="/ershoufang/page2"></head><body>'
        '<a href="/ershoufang/109900001234.html">first</a></body></html>', encoding='utf-8')

    first = subprocess.run(
        [sys.executable, str(root / 'scripts/discover_listing_urls.py'),
         '--source', 'beike', '--page-url', 'https://nb.ke.com/ershoufang/',
         '--html', str(first_page), '--state-file', str(state)],
        cwd=root, capture_output=True, text=True, check=False,
    )

    assert first.returncode == 0, first.stderr
    saved = json.loads(state.read_text(encoding='utf-8'))
    assert saved['seen_ids'] == ['109900001234']
    assert saved['next_page_url'] == 'https://nb.ke.com/ershoufang/page2'

    second_page = tmp_path / 'second.html'
    second_page.write_text(
        '<html><body><a href="/ershoufang/109900001234.html">duplicate</a>'
        '<a href="/ershoufang/109900005678.html">second</a></body></html>', encoding='utf-8')
    second = subprocess.run(
        [sys.executable, str(root / 'scripts/discover_listing_urls.py'),
         '--source', 'beike', '--html', str(second_page), '--state-file', str(state)],
        cwd=root, capture_output=True, text=True, check=False,
    )

    assert second.returncode == 0, second.stderr
    output = json.loads(second.stdout)
    assert output['page_url'] == 'https://nb.ke.com/ershoufang/page2'
    assert [item['source_listing_id'] for item in output['listings']] == ['109900005678']
    saved = json.loads(state.read_text(encoding='utf-8'))
    assert saved['seen_ids'] == ['109900001234', '109900005678']
    assert saved['next_page_url'] is None


def test_discovery_cli_refuses_state_for_another_source(tmp_path):
    root = Path(__file__).resolve().parents[1]
    state = tmp_path / 'discovery-state.json'
    state.write_text(json.dumps({
        'version': 1, 'source': 'anjuke', 'seen_ids': [],
        'last_page_url': None, 'next_page_url': None,
    }), encoding='utf-8')
    sample = tmp_path / 'list.html'
    sample.write_text('<html><body><main>本地列表快照</main></body></html>', encoding='utf-8')

    result = subprocess.run(
        [sys.executable, str(root / 'scripts/discover_listing_urls.py'),
         '--source', 'beike', '--page-url', 'https://nb.ke.com/ershoufang/',
         '--html', str(sample), '--state-file', str(state)],
        cwd=root, capture_output=True, text=True, check=False,
    )

    assert result.returncode == 2
    assert 'invalid schema or source' in result.stderr


def test_discovery_cli_stops_when_pagination_returns_to_a_visited_page(tmp_path):
    root = Path(__file__).resolve().parents[1]
    state = tmp_path / 'discovery-state.json'
    first_page = tmp_path / 'first.html'
    first_page.write_text(
        '<html><body><a rel="next" href="/ershoufang/page2">next</a></body></html>',
        encoding='utf-8')
    first = subprocess.run(
        [sys.executable, str(root / 'scripts/discover_listing_urls.py'),
         '--source', 'beike', '--page-url', 'https://nb.ke.com/ershoufang/',
         '--html', str(first_page), '--state-file', str(state)],
        cwd=root, capture_output=True, text=True, check=False,
    )
    assert first.returncode == 0, first.stderr

    second_page = tmp_path / 'second.html'
    second_page.write_text(
        '<html><body><a rel="next" href="/ershoufang/">back</a></body></html>',
        encoding='utf-8')
    second = subprocess.run(
        [sys.executable, str(root / 'scripts/discover_listing_urls.py'),
         '--source', 'beike', '--html', str(second_page), '--state-file', str(state)],
        cwd=root, capture_output=True, text=True, check=False,
    )

    assert second.returncode == 0, second.stderr
    output = json.loads(second.stdout)
    assert output['next_page_url'] is None
    assert 'pagination_loop' in output['warnings']


def test_discovery_cli_records_failed_page_and_retries_same_cursor(tmp_path):
    root = Path(__file__).resolve().parents[1]
    page_url = 'https://nb.ke.com/ershoufang/page2'
    state = tmp_path / 'discovery-state.json'
    sample = tmp_path / 'second.html'

    failed = subprocess.run(
        [sys.executable, str(root / 'scripts/discover_listing_urls.py'),
         '--source', 'beike', '--page-url', page_url, '--html', str(sample),
         '--state-file', str(state)],
        cwd=root, capture_output=True, text=True, check=False,
    )

    assert failed.returncode == 2
    assert 'HTML sample could not be read' in failed.stderr
    saved = json.loads(state.read_text(encoding='utf-8'))
    assert saved['next_page_url'] == page_url
    assert saved['last_attempted_page_url'] == page_url
    assert saved['last_error_type'] == 'FileNotFoundError'
    assert saved['failed_attempts'] == 1

    sample.write_text('<html><body><main>本地第二页快照</main></body></html>', encoding='utf-8')
    retried = subprocess.run(
        [sys.executable, str(root / 'scripts/discover_listing_urls.py'),
         '--source', 'beike', '--html', str(sample), '--state-file', str(state)],
        cwd=root, capture_output=True, text=True, check=False,
    )

    assert retried.returncode == 0, retried.stderr
    output = json.loads(retried.stdout)
    assert output['page_url'] == page_url
    saved = json.loads(state.read_text(encoding='utf-8'))
    assert saved['next_page_url'] is None
    assert saved['last_error_type'] is None
    assert saved['failed_attempts'] == 1


def test_discovery_cli_refuses_symlink_state_without_changing_target(tmp_path):
    root = Path(__file__).resolve().parents[1]
    target = tmp_path / 'state-target.json'
    target.write_text(json.dumps({
        'version': 1, 'source': 'beike', 'seen_ids': [],
        'last_page_url': None, 'next_page_url': None,
    }), encoding='utf-8')
    original = target.read_bytes()
    state = tmp_path / 'state-link.json'
    state.symlink_to(target)
    sample = tmp_path / 'list.html'
    sample.write_text('<html><body><main>本地列表快照</main></body></html>', encoding='utf-8')

    result = subprocess.run(
        [sys.executable, str(root / 'scripts/discover_listing_urls.py'),
         '--source', 'beike', '--page-url', 'https://nb.ke.com/ershoufang/',
         '--html', str(sample), '--state-file', str(state)],
        cwd=root, capture_output=True, text=True, check=False,
    )

    assert result.returncode == 2
    assert 'must not be a symlink' in result.stderr
    assert state.is_symlink()
    assert target.read_bytes() == original


def test_discovery_cli_refuses_state_path_aliasing_an_input(tmp_path):
    root = Path(__file__).resolve().parents[1]
    html = tmp_path / 'list.html'
    html.write_text('<html><body><main>本地列表快照</main></body></html>', encoding='utf-8')
    state_alias = tmp_path / 'state.json'

    # A hard link exercises file identity even when the path strings differ.
    state_alias.hardlink_to(html)
    original = html.read_bytes()
    result = subprocess.run(
        [sys.executable, str(root / 'scripts/discover_listing_urls.py'),
         '--source', 'beike', '--page-url', 'https://nb.ke.com/ershoufang/',
         '--html', str(html), '--state-file', str(state_alias)],
        cwd=root, capture_output=True, text=True, check=False,
    )

    assert result.returncode == 2
    assert 'must be different from --html' in result.stderr
    assert html.read_bytes() == original
    assert state_alias.read_bytes() == original


