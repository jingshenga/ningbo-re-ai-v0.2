"""Run real RapidOCR over operator-authorized annotated listing videos.

Each row in the annotation CSV names a local file; this tool does not fetch
media from any platform or submit enrichment to the application database.
It writes reproducible result JSON and resource logs beside the source video.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CLI = REPO / 'scripts' / 'enrich_local_video.py'
VIDEO_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,100}\Z')
SUPPORTED_VIDEO_EXTS = frozenset(('.mp4', '.mov', '.mkv', '.m4v', '.webm', '.avi',
                                  '.flv', '.ts', '.mpg', '.mpeg', '.3gp'))


def _write_atomic(path: Path, content: str) -> None:
    """Replace only the result entry, never follow an existing symlink."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w', encoding='utf-8', dir=path.parent,
            prefix='.' + path.name + '.', delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _video_path(folder: Path, video_id: str) -> Path:
    if not VIDEO_ID.fullmatch(video_id):
        raise ValueError('video_id must use only letters, digits, underscores or hyphens')
    videos = [candidate for candidate in sorted(folder.glob(video_id + '.*'))
              if candidate.suffix.lower() in SUPPORTED_VIDEO_EXTS
              and candidate.is_file() and not candidate.is_symlink()]
    if not videos:
        raise ValueError('authorized local video not found')
    if len(videos) != 1:
        raise ValueError('ambiguous video_id; use a unique video basename')
    return videos[0]


def _execute(command: list[str], timeout: float) -> tuple[int, str, str, float]:
    """Kill the entire process group on timeout, including FFmpeg children."""
    start = time.monotonic()
    process = subprocess.Popen(
        command, shell=False, cwd=str(REPO), stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate()
        raise TimeoutError('video processing exceeded the per-video timeout') from None
    return process.returncode, stdout, stderr, time.monotonic() - start


def _resource_command(video: Path, communities: Path, out: Path) -> list[str]:
    script = [sys.executable, str(CLI), str(video), '--ocr', 'rapidocr',
              '--known-communities', str(communities), '--json-out', str(out)]
    timer = Path('/usr/bin/time')
    if timer.is_file():
        return [str(timer), '-l' if sys.platform == 'darwin' else '-v'] + script
    return script


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Run real RapidOCR against authorized, annotated local videos')
    parser.add_argument('--csv', required=True, type=Path)
    parser.add_argument('--dir', required=True, type=Path)
    parser.add_argument('--known-communities', required=True, type=Path)
    parser.add_argument('--timeout', type=float, default=900,
                        help='single-video subprocess timeout in seconds (default 900)')
    args = parser.parse_args(argv)
    if not 1 <= args.timeout <= 3600:
        parser.error('--timeout must be between 1 and 3600 seconds')

    try:
        with args.csv.open(encoding='utf-8', newline='') as handle:
            rows = list(csv.DictReader(handle))
    except (OSError, UnicodeError, csv.Error) as exc:
        parser.error('cannot read annotation csv: ' + type(exc).__name__)
    if not rows:
        parser.error('annotation csv has no rows')
    try:
        video_dir = args.dir.expanduser().resolve(strict=True)
        communities = args.known_communities.expanduser().resolve(strict=True)
    except OSError as exc:
        parser.error('required input path unavailable: ' + type(exc).__name__)
    if not video_dir.is_dir() or not communities.is_file():
        parser.error('--dir must be a directory and --known-communities a readable file')

    failures = []
    processed = 0
    for row in rows:
        video_id = (row.get('video_id') or '').strip()
        if not video_id:
            failures.append(('(blank)', 'missing video_id'))
            continue
        if (video_id == 'listing_01'
                and (row.get('source_note') or '').startswith('示例')):
            continue  # only skip the explicitly labeled template example
        # Clear stale measurements before validating this run. Otherwise a
        # missing video can accidentally reuse an earlier successful JSON.
        if VIDEO_ID.fullmatch(video_id):
            for suffix in ('.result.json', '.time.log'):
                old_result = video_dir / (video_id + suffix)
                if old_result.is_symlink() or old_result.is_file():
                    old_result.unlink()
        if not (row.get('source_note') or '').strip():
            failures.append((video_id, 'missing source/rights note'))
            continue
        try:
            video = _video_path(video_dir, video_id)
        except ValueError as exc:
            failures.append((video_id[:100], str(exc)))
            continue

        processed += 1
        result_json = video_dir / (video_id + '.result.json')
        time_log = video_dir / (video_id + '.time.log')
        start = time.monotonic()
        try:
            code, _, stderr, elapsed = _execute(
                _resource_command(video, communities, result_json),
                args.timeout,
            )
            _write_atomic(time_log, stderr + '\nreal ' + format(elapsed, '.4f') + '\n')
            if code != 0:
                failures.append((video_id, 'CLI exit ' + str(code)))
                continue
            if not result_json.is_file() or result_json.is_symlink():
                failures.append((video_id, 'CLI did not produce safe result JSON'))
                continue
            result = json.loads(result_json.read_text(encoding='utf-8'))
            ocr = result.get('ocr') or {}
            if (result.get('ok') is not True or ocr.get('status') != 'ok'
                    or ocr.get('engine') != 'rapidocr'):
                failures.append((video_id, 'real RapidOCR did not succeed'))
                continue
            print(video_id, '-> real OCR processed', flush=True)
        except (OSError, UnicodeError, json.JSONDecodeError, TimeoutError) as exc:
            _write_atomic(time_log, 'real ' + format(time.monotonic() - start, '.4f') + '\n')
            failures.append((video_id, type(exc).__name__))

    if not processed:
        failures.append(('(all)', 'no actual authorized videos processed'))
    for video_id, reason in failures:
        print('FAILED', video_id, ':', reason, file=sys.stderr)
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
