"""Extract same-source detail URLs from a locally saved listing-page snapshot."""
import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.collectors.discovery_state import load_state, read_seen_ids, record_failure, save_state
from app.collectors.url_policy import CollectionError, source_page_key


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', choices=('beike', 'anjuke'), required=True)
    parser.add_argument('--page-url',
                        help='HTTPS source URL where this local snapshot was saved')
    parser.add_argument('--html', type=Path, required=True, help='local HTML file; no network access')
    state_options = parser.add_mutually_exclusive_group()
    state_options.add_argument('--seen-ids', type=Path,
                               help='UTF-8 file with one already-discovered listing ID per line')
    state_options.add_argument('--state-file', type=Path,
                               help='optional local JSON state; reuses the saved next page URL')
    args = parser.parse_args()
    if args.state_file:
        try:
            same_file = args.state_file.samefile(args.html)
        except OSError:
            same_file = args.state_file.resolve() == args.html.resolve()
        if same_file:
            parser.error('--state-file must be different from --html')
    from app.collectors.discovery import MAX_HTML_BYTES, discover_listing_links

    state = None
    state_to_save = None
    page_url = args.page_url
    try:
        state = load_state(args.state_file, args.source) if args.state_file else None
    except OSError:
        parser.error('Discovery state could not be read')
    except ValueError as exc:
        parser.error(str(exc))
    page_url = args.page_url or (state and state.get('next_page_url'))
    if not page_url:
        parser.error('--page-url is required unless --state-file has a next page URL')

    def report_failure(message, error):
        if state is not None and not record_failure(
                args.state_file, state, args.source, page_url, error):
            message += '; discovery retry state could not be saved'
        parser.error(message)

    try:
        with args.html.open('rb') as sample:
            raw = sample.read(MAX_HTML_BYTES + 1)
        if len(raw) > MAX_HTML_BYTES:
            raise ValueError('HTML sample exceeds 1000000 byte limit')
        html = raw.decode('utf-8-sig', errors='strict')
    except OSError as exc:
        report_failure('HTML sample could not be read', exc)
    except UnicodeError as exc:
        report_failure('HTML sample is not valid UTF-8', exc)
    except ValueError as exc:
        report_failure(str(exc), exc)
    try:
        seen_ids = (read_seen_ids(args.seen_ids, args.source)
                    if args.seen_ids else set(state['seen_ids']) if state else set())
    except OSError:
        parser.error('Seen IDs input could not be read')
    except ValueError as exc:
        parser.error(str(exc))
    try:
        result = discover_listing_links(args.source, page_url, html, seen_ids)
    except (CollectionError, ValueError) as exc:
        report_failure(str(exc), exc)

    if state is not None:
        state['seen_ids'] = sorted(seen_ids | {item.source_listing_id for item in result.listings})
        visited = state['visited_page_urls']
        page_key = source_page_key(args.source, page_url)
        if all(source_page_key(args.source, old_url) != page_key for old_url in visited):
            visited.append(page_url)
        state['last_page_url'] = page_url
        state['last_attempted_page_url'] = page_url
        state['last_error_type'] = None
        next_page_url = result.next_page_url
        warnings = list(result.warnings)
        if (next_page_url and any(
                source_page_key(args.source, old_url) == source_page_key(args.source, next_page_url)
                for old_url in visited)):
            next_page_url = None
            warnings.append('pagination_loop')
        state['next_page_url'] = next_page_url
        state_to_save = state
    else:
        next_page_url = result.next_page_url
        warnings = list(result.warnings)

    try:
        print(json.dumps({
            'source': args.source,
            'page_url': page_url,
            'listings': [
                {'source_listing_id': item.source_listing_id, 'url': item.url}
                for item in result.listings
            ],
            'next_page_url': next_page_url,
            'warnings': warnings,
            'network_accessed': False,
        }, ensure_ascii=False, indent=2))
        sys.stdout.flush()
    except OSError:
        parser.exit(1, 'Discovery result output failed; state was not advanced\n')

    if state_to_save is not None:
        try:
            save_state(args.state_file, state_to_save)
        except OSError:
            parser.error('Discovery state could not be saved')
        except ValueError as exc:
            parser.error(str(exc))


if __name__ == '__main__':
    main()
