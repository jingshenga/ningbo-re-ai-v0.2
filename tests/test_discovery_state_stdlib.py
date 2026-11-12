import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

from app.collectors.discovery_state import (
    load_state, new_state, read_seen_ids, record_failure, save_state,
)

SCRIPT_PATH = Path(__file__).resolve().parents[1] / 'scripts' / 'discover_listing_urls.py'
SCRIPT_SPEC = importlib.util.spec_from_file_location('discovery_cli', SCRIPT_PATH)
discovery_cli = importlib.util.module_from_spec(SCRIPT_SPEC)
SCRIPT_SPEC.loader.exec_module(discovery_cli)


class DiscoveryStateTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.path = self.root / 'state.json'

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_rejects_next_page_alias_of_visited_page(self):
        page = 'https://nb.ke.com/ershoufang/page1'
        state = new_state('beike')
        state['visited_page_urls'] = [page]
        state['next_page_url'] = 'https://nb.ke.com.:443/ershoufang/page1'
        self.path.write_text(json.dumps(state), encoding='utf-8')

        with self.assertRaisesRegex(ValueError, 'pagination loop'):
            load_state(self.path, 'beike')

    def test_load_rejects_unicode_iri_next_page_alias_of_visited_page(self):
        page = 'https://nb.ke.com/ershoufang/小区'
        state = new_state('beike')
        state['visited_page_urls'] = [page]
        state['next_page_url'] = 'https://nb.ke.com/ershoufang/%E5%B0%8F%E5%8C%BA'
        self.path.write_text(json.dumps(state), encoding='utf-8')

        with self.assertRaisesRegex(ValueError, 'pagination loop'):
            load_state(self.path, 'beike')

    def test_new_state_defaults_and_atomic_round_trip(self):
        state = new_state('beike')
        self.assertEqual(state['seen_ids'], [])
        self.assertEqual(state['visited_page_urls'], [])
        save_state(self.path, state)

        self.assertEqual(load_state(self.path, 'beike'), state)
        self.assertEqual(list(self.root.iterdir()), [self.path])

    def test_legacy_state_defaults_visited_and_retry_fields(self):
        self.path.write_text(json.dumps({
            'version': 1, 'source': 'beike', 'seen_ids': [],
            'last_page_url': 'https://nb.ke.com/ershoufang/',
            'next_page_url': 'https://nb.ke.com/ershoufang/page2',
        }), encoding='utf-8')

        state = load_state(self.path, 'beike')

        self.assertEqual(state['visited_page_urls'], ['https://nb.ke.com/ershoufang/'])
        self.assertEqual(state['failed_attempts'], 0)
        self.assertIsNone(state['last_error_type'])

    def test_rejects_wrong_source_id_format_and_unsafe_page_url(self):
        for value in (
            {'version': 1, 'source': 'anjuke', 'seen_ids': [],
             'last_page_url': None, 'next_page_url': None},
            {'version': 1, 'source': 'beike', 'seen_ids': ['bad'],
             'last_page_url': None, 'next_page_url': None},
            {'version': 1, 'source': 'beike', 'seen_ids': [],
             'last_page_url': None, 'next_page_url': 'https://other.example/page'},
        ):
            self.path.write_text(json.dumps(value), encoding='utf-8')
            with self.subTest(value=value), self.assertRaises(ValueError):
                load_state(self.path, 'beike')

    def test_rejects_symlink_without_changing_target(self):
        target = self.root / 'target.json'
        target.write_text(json.dumps(new_state('beike')), encoding='utf-8')
        before = target.read_bytes()
        self.path.symlink_to(target)

        with self.assertRaisesRegex(ValueError, 'symlink'):
            load_state(self.path, 'beike')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            save_state(self.path, new_state('beike'))

        self.assertEqual(target.read_bytes(), before)

    def test_rejects_directory_as_state_path(self):
        directory = self.root / 'state-directory'
        directory.mkdir()
        with self.assertRaisesRegex(ValueError, 'regular file'):
            load_state(directory, 'beike')
        with self.assertRaisesRegex(ValueError, 'regular file'):
            save_state(directory, new_state('beike'))

    def test_failed_page_is_saved_as_retry_cursor_without_error_text(self):
        state = new_state('beike')
        page_url = 'https://nb.ke.com/ershoufang/'

        record_failure(self.path, state, 'beike', page_url,
                       FileNotFoundError('/private/user/path/list.html'))
        saved = load_state(self.path, 'beike')
        raw = self.path.read_text(encoding='utf-8')

        self.assertEqual(saved['next_page_url'], page_url)
        self.assertEqual(saved['last_attempted_page_url'], page_url)
        self.assertEqual(saved['failed_attempts'], 1)
        self.assertEqual(saved['last_error_type'], 'FileNotFoundError')
        self.assertNotIn('/private/user/path', raw)

    def test_record_failure_reports_state_write_failure(self):
        state = new_state('beike')
        with mock.patch('app.collectors.discovery_state.save_state',
                        side_effect=PermissionError('permission denied')):
            saved = record_failure(self.path, state, 'beike',
                                   'https://nb.ke.com/ershoufang/',
                                   FileNotFoundError('snapshot missing'))

        self.assertFalse(saved)
        self.assertEqual(state['failed_attempts'], 1)

    def test_record_failure_reports_missing_state_path(self):
        state = new_state('beike')

        saved = record_failure(None, state, 'beike',
                               'https://nb.ke.com/ershoufang/',
                               FileNotFoundError('snapshot missing'))

        self.assertFalse(saved)
        self.assertEqual(state['failed_attempts'], 1)

    def test_failed_replay_of_visited_page_does_not_poison_retry_cursor(self):
        first_page = 'https://nb.ke.com/ershoufang/'
        next_page = 'https://nb.ke.com/ershoufang/page2'
        state = new_state('beike')
        state['last_page_url'] = first_page
        state['visited_page_urls'] = [first_page]
        state['next_page_url'] = next_page
        save_state(self.path, state)

        record_failure(self.path, state, 'beike', first_page,
                       FileNotFoundError('snapshot missing'))
        saved = load_state(self.path, 'beike')

        self.assertEqual(saved['next_page_url'], next_page)
        self.assertEqual(saved['last_error_type'], 'FileNotFoundError')
        self.assertEqual(saved['failed_attempts'], 1)

    def test_save_rejects_oversized_state(self):
        state = new_state('beike')
        state['extra'] = 'x' * 2_000_001
        with self.assertRaisesRegex(ValueError, '2000000 byte limit'):
            save_state(self.path, state)
        self.assertFalse(self.path.exists())

    def test_seen_ids_file_is_bounded_and_requires_utf8(self):
        seen_path = self.root / 'seen.txt'
        seen_path.write_text('109900001234\n109900005678\n109900001234\n', encoding='utf-8')
        self.assertEqual(read_seen_ids(seen_path, 'beike'), {'109900001234', '109900005678'})

        seen_path.write_bytes(b'x' * 2_000_001)
        with self.assertRaisesRegex(ValueError, '2000000 byte limit'):
            read_seen_ids(seen_path, 'beike')

        seen_path.write_bytes(b'\xff')
        with self.assertRaisesRegex(ValueError, 'valid UTF-8'):
            read_seen_ids(seen_path, 'beike')

    def test_seen_ids_validate_source_specific_listing_id_format(self):
        seen_path = self.root / 'seen.txt'
        seen_path.write_text(' 109900001234 \n\n', encoding='utf-8')
        self.assertEqual(read_seen_ids(seen_path, 'beike'), {'109900001234'})
        seen_path.write_text('1234567\n', encoding='utf-8')
        self.assertEqual(read_seen_ids(seen_path, 'anjuke'), {'1234567'})

        for source, invalid_id in (
            ('beike', '1234567'), ('anjuke', '123456'), ('beike', 'id-109900001234'),
            ('anjuke', '1' * 221),
        ):
            seen_path.write_text(invalid_id + '\n', encoding='utf-8')
            with self.subTest(source=source, invalid_id=invalid_id), \
                    self.assertRaisesRegex(ValueError, 'invalid listing ID'):
                read_seen_ids(seen_path, source)

        with self.assertRaisesRegex(ValueError, 'unsupported'):
            read_seen_ids(seen_path, 'other')

    def test_seen_ids_rejects_non_regular_file(self):
        fifo = self.root / 'seen.pipe'
        os.mkfifo(fifo)
        with self.assertRaisesRegex(ValueError, 'regular file'):
            read_seen_ids(fifo, 'beike')

    def test_seen_ids_rejects_symlink_without_changing_target(self):
        target = self.root / 'target.txt'
        target.write_text('109900001234' + chr(10), encoding='utf-8')
        before = target.read_bytes()
        link = self.root / 'seen-link.txt'
        link.symlink_to(target)

        with self.assertRaisesRegex(ValueError, 'symlink'):
            read_seen_ids(link, 'beike')

        self.assertEqual(target.read_bytes(), before)

    def test_collector_dispatch_keeps_lightweight_imports_lazy(self):
        result = subprocess.run(
            [sys.executable, '-c',
             "import sys; import app.collectors; "
             "assert 'app.collectors.parser' not in sys.modules"],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def run_cli(self, args, stdout_stream=None):
        discovery = types.ModuleType('app.collectors.discovery')
        discovery.MAX_HTML_BYTES = 1_000_000

        def discover(source, page_url, html, seen_ids):
            fields = dict(part.split('=', 1) for part in html.split(';') if '=' in part)
            ids = [value for value in fields.get('ids', '').split(',') if value]
            listings = tuple(
                type('Listing', (), {'source_listing_id': value, 'url': f'https://{source}.test/{value}'})()
                for value in ids if value not in seen_ids
            )
            return type('Discovery', (), {
                'listings': listings,
                'next_page_url': fields.get('next') or None,
                'warnings': (),
            })()

        discovery.discover_listing_links = discover
        stdout, stderr = stdout_stream or io.StringIO(), io.StringIO()
        argv = ['discover_listing_urls.py', *map(str, args)]
        with mock.patch.dict(sys.modules, {'app.collectors.discovery': discovery}), \
                mock.patch.object(sys, 'argv', argv), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                discovery_cli.main()
            except SystemExit as exc:
                return exc.code, None, stderr.getvalue()
        return 0, json.loads(stdout.getvalue()), stderr.getvalue()

    def test_cli_resumes_cursor_and_deduplicates_ids(self):
        page_one = self.root / 'one.html'
        page_two = self.root / 'two.html'
        page_one.write_text(
            'ids=109900001234;next=https://nb.ke.com/ershoufang/page2', encoding='utf-8')
        page_two.write_text('ids=109900001234,109900005678', encoding='utf-8')

        code, first, _ = self.run_cli([
            '--source', 'beike', '--page-url', 'https://nb.ke.com/ershoufang/',
            '--html', page_one, '--state-file', self.path,
        ])
        self.assertEqual(code, 0)
        self.assertEqual(first['next_page_url'], 'https://nb.ke.com/ershoufang/page2')

        code, second, _ = self.run_cli([
            '--source', 'beike', '--html', page_two, '--state-file', self.path,
        ])
        self.assertEqual(code, 0)
        self.assertEqual(second['page_url'], 'https://nb.ke.com/ershoufang/page2')
        self.assertEqual([item['source_listing_id'] for item in second['listings']],
                         ['109900005678'])

    def test_cli_does_not_advance_state_when_result_output_fails(self):
        class BrokenPipeOnFlush:
            def write(self, value):
                return len(value)

            def flush(self):
                raise BrokenPipeError()

        first, second = self.root / 'first.html', self.root / 'second.html'
        first.write_text(
            'ids=109900001234;next=https://nb.ke.com/ershoufang/page2', encoding='utf-8')
        second.write_text('ids=109900005678', encoding='utf-8')
        args = ['--source', 'beike', '--page-url', 'https://nb.ke.com/ershoufang/',
                '--html', first, '--state-file', self.path]
        self.assertEqual(self.run_cli(args)[0], 0)
        before = load_state(self.path, 'beike')

        args = ['--source', 'beike', '--html', second, '--state-file', self.path]
        code, output, error = self.run_cli(args, BrokenPipeOnFlush())
        self.assertEqual(code, 1)
        self.assertIsNone(output)
        self.assertIn('state was not advanced', error)
        after = load_state(self.path, 'beike')
        self.assertEqual(after, before)

        code, retry, _ = self.run_cli(args)
        self.assertEqual(code, 0)
        self.assertEqual([item['source_listing_id'] for item in retry['listings']],
                         ['109900005678'])

    def test_cli_records_failed_first_page_then_retries_without_url_argument(self):
        sample = self.root / 'first.html'
        page_url = 'https://nb.ke.com/ershoufang/'
        code, _, error = self.run_cli([
            '--source', 'beike', '--page-url', page_url,
            '--html', sample, '--state-file', self.path,
        ])
        self.assertEqual(code, 2)
        self.assertIn('HTML sample could not be read', error)
        self.assertEqual(load_state(self.path, 'beike')['next_page_url'], page_url)

        sample.write_text('ids=109900001234', encoding='utf-8')
        code, output, _ = self.run_cli([
            '--source', 'beike', '--html', sample, '--state-file', self.path,
        ])
        self.assertEqual(code, 0)
        self.assertEqual(output['page_url'], page_url)

    def test_cli_reports_when_retry_state_cannot_be_saved(self):
        sample = self.root / 'missing.html'
        with mock.patch.object(discovery_cli, 'record_failure', return_value=False):
            code, _, error = self.run_cli([
                '--source', 'beike', '--page-url', 'https://nb.ke.com/ershoufang/',
                '--html', sample, '--state-file', self.path,
            ])

        self.assertEqual(code, 2)
        self.assertIn('HTML sample could not be read', error)
        self.assertIn('discovery retry state could not be saved', error)

    def test_cli_reports_seen_ids_input_errors_without_mislabelling_html(self):
        sample = self.root / 'page.html'
        sample.write_text('ids=109900001234', encoding='utf-8')
        seen_path = self.root / 'missing-seen.txt'
        args = ['--source', 'beike', '--page-url', 'https://nb.ke.com/ershoufang/',
                '--html', sample, '--seen-ids', seen_path]

        code, _, error = self.run_cli(args)
        self.assertEqual(code, 2)
        self.assertIn('Seen IDs input could not be read', error)
        self.assertNotIn('HTML sample could not be read', error)

        seen_path.write_text('invalid-id\n', encoding='utf-8')
        code, _, error = self.run_cli(args)
        self.assertEqual(code, 2)
        self.assertIn('invalid listing ID', error)
        self.assertNotIn('HTML sample could not be read', error)

    def test_cli_stops_stateful_pagination_cycle(self):
        first, second = self.root / 'first.html', self.root / 'second.html'
        first.write_text('next=https://nb.ke.com/ershoufang/page2', encoding='utf-8')
        second.write_text('next=https://nb.ke.com/ershoufang/', encoding='utf-8')
        self.assertEqual(self.run_cli([
            '--source', 'beike', '--page-url', 'https://nb.ke.com/ershoufang/',
            '--html', first, '--state-file', self.path,
        ])[0], 0)

        code, output, _ = self.run_cli([
            '--source', 'beike', '--html', second, '--state-file', self.path,
        ])
        self.assertEqual(code, 0)
        self.assertIsNone(output['next_page_url'])
        self.assertIn('pagination_loop', output['warnings'])


if __name__ == '__main__':
    unittest.main()
