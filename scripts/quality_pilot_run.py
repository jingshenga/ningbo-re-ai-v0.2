"""Run real-OCR over annotated listing videos: one CLI pass per video.

Reads the annotation CSV (docs/VIDEO_ANNOTATION_GUIDE.md), runs
scripts/enrich_local_video.py with --ocr rapidocr for each listed video and
records the result JSON plus /usr/bin/time resource stats next to the video.
No collection from any platform: videos must be operator-supplied files with
documented rights (source_note column).
"""
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CLI = REPO / 'scripts' / 'enrich_local_video.py'


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Run the real-OCR CLI over an annotated listing-video set')
    parser.add_argument('--csv', required=True, type=Path,
                        help='annotation CSV per docs/VIDEO_ANNOTATION_GUIDE.md')
    parser.add_argument('--dir', required=True, type=Path,
                        help='directory holding the videos named by video_id')
    parser.add_argument('--known-communities', required=True, type=Path,
                        help='community name list, one per line')
    parser.add_argument('--ocr', choices=['auto', 'rapidocr'], default='rapidocr')
    args = parser.parse_args(argv)

    try:
        rows = list(csv.DictReader(args.csv.open(encoding='utf-8')))
    except OSError as exc:
        parser.error('cannot read annotation csv: ' + type(exc).__name__)
    if not rows:
        parser.error('annotation csv has no rows')

    failures = []
    for row in rows:
        video_id = (row.get('video_id') or '').strip()
        if not video_id or video_id == 'listing_01':  # template example row
            continue
        video = args.dir / video_id
        if not video.is_file():
            candidates = sorted(str(p.name) for p in args.dir.glob(video_id + '.*'))
            if not candidates:
                failures.append((video_id, 'video file not found'))
                continue
            video = args.dir / candidates[0]
        result_json = args.dir / (video_id + '.result.json')
        time_log = args.dir / (video_id + '.time.log')
        proc = subprocess.run(
            ['/usr/bin/time', '-l', 'env', 'PYTHONPATH=.',
             str(REPO / '.venv' / 'bin' / 'python'), str(CLI), str(video),
             '--ocr', args.ocr, '--known-communities', str(args.known_communities),
             '--json-out', str(result_json)],
            shell=False, cwd=str(REPO), capture_output=True, text=True, check=False)
        time_log.write_text(proc.stderr, encoding='utf-8')
        status = 'ok' if proc.returncode == 0 else 'exit ' + str(proc.returncode)
        print(video_id, '->', status, flush=True)
        if proc.returncode != 0:
            failures.append((video_id, proc.stderr.strip()[:200]))

    for video_id, reason in failures:
        print('FAILED', video_id, ':', reason, file=sys.stderr)
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
