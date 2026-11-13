"""Enrich one operator-supplied local video: FFmpeg → ASR/OCR → hints → dry-run or API.

Example (offline closed loop, no API):
    python scripts/enrich_local_video.py /path/to/listing.mp4 --asr-script transcript.txt

Example (submit to the existing video row on the NAS-local API):
    APP_API_KEY=... python scripts/enrich_local_video.py listing.mp4 \\
        --video-id <uuid> --submit

The API key is read ONLY from the APP_API_KEY environment variable (matching
the existing operator scripts) and never printed, logged or written to disk.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Support the documented direct invocation from any working directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.media_pipeline import (MediaPipelineError, build_asr_engine,
                                build_ocr_engine, run_pipeline,
                                submit_enrichment)

EXIT_OK = 0
EXIT_INVALID = 2
EXIT_PROCESSING = 3
EXIT_SUBMIT = 4


def _error_json(kind: str, detail: str) -> str:
    return json.dumps({'ok': False, 'error': {'kind': kind, 'detail': detail}},
                      ensure_ascii=False)


def _read_communities(path: str | None) -> list[str] | None:
    if path is None:
        return None
    try:
        lines = Path(path).read_text(encoding='utf-8').splitlines()
    except OSError as exc:
        raise MediaPipelineError('invalid_input',
                                 'cannot read community name file: ' + type(exc).__name__) from exc
    return [line.strip() for line in lines if line.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Process one local video into transcript/OCR evidence and optional enrichment',
    )
    parser.add_argument('video', type=Path, help='local media file (mp4/mov/mkv/...)')
    parser.add_argument('--video-id', default=None,
                        help='existing video row UUID; required with --submit')
    parser.add_argument('--submit', action='store_true',
                        help='PATCH /api/videos/{video_id}/enrichment after processing')
    parser.add_argument('--api-url', default='http://127.0.0.1:8788',
                        help='API base URL (default NAS-local)')
    parser.add_argument('--allow-private-network', action='store_true',
                        help='opt-in for private IP API targets')
    parser.add_argument('--asr', choices=['auto', 'mock', 'funasr'], default='auto')
    parser.add_argument('--asr-script', default=None,
                        help='manual transcript file for the mock ASR engine')
    parser.add_argument('--ocr', choices=['auto', 'mock', 'rapidocr'], default='auto')
    parser.add_argument('--ocr-text', default=None,
                        help='manual OCR text (assigned to the first sampled frame) for the mock engine')
    parser.add_argument('--known-communities', default=None,
                        help='optional file of community names, one per line')
    parser.add_argument('--keep-work', default=None, metavar='DIR',
                        help='keep audio/frames in this directory instead of a temp dir')
    parser.add_argument('--json-out', default=None, metavar='FILE',
                        help='also write the result JSON to this file')
    args = parser.parse_args(argv)

    if args.submit and not args.video_id:
        print(_error_json('invalid_input', '--submit requires --video-id'), file=sys.stderr)
        return EXIT_INVALID

    try:
        communities = _read_communities(args.known_communities)
        asr_engine = build_asr_engine(args.asr, script_file=args.asr_script)
        ocr_engine = build_ocr_engine(
            args.ocr, text_map={0: args.ocr_text} if args.ocr_text else None)
        evidence = run_pipeline(
            args.video,
            asr_engine=asr_engine,
            ocr_engine=ocr_engine,
            work_dir=args.keep_work,
            keep_work=bool(args.keep_work),
            known_community_names=communities,
        )
    except MediaPipelineError as exc:
        print(_error_json(exc.kind, exc.detail), file=sys.stderr)
        return EXIT_PROCESSING if exc.kind.startswith(('ffmpeg', 'media')) else EXIT_INVALID
    except (OSError, UnicodeError, ValueError) as exc:
        print(_error_json('invalid_input',
                          'could not read configured processing input: ' + type(exc).__name__),
              file=sys.stderr)
        return EXIT_INVALID

    result = evidence.as_dict()
    result['ok'] = True
    result['submitted'] = False
    if args.submit:
        transcript = (evidence.transcript.text or '').strip() or None
        ocr_text = '\n'.join(item.text for item in evidence.ocr.items).strip() or None
        if transcript is None and ocr_text is None:
            print(_error_json(
                'empty_enrichment',
                'no transcript or OCR text is available; the video was not marked enriched',
            ), file=sys.stderr)
            return EXIT_SUBMIT
        api_key = os.environ.get('APP_API_KEY')
        if not api_key:
            print(_error_json('invalid_input', 'set APP_API_KEY to submit enrichment'),
                  file=sys.stderr)
            return EXIT_SUBMIT
        try:
            server_response = submit_enrichment(
                api_base=args.api_url, api_key=api_key, video_id=args.video_id,
                transcript=transcript,
                ocr_text=ocr_text,
                allow_private_network=args.allow_private_network,
            )
        except MediaPipelineError as exc:
            print(_error_json(exc.kind, exc.detail), file=sys.stderr)
            return EXIT_SUBMIT
        result['submitted'] = True
        result['server'] = server_response

    output = json.dumps(result, ensure_ascii=False, indent=2)
    print(output)
    if args.json_out:
        try:
            Path(args.json_out).write_text(output, encoding='utf-8')
        except OSError as exc:
            print(_error_json('submit_failed', 'cannot write --json-out: ' + type(exc).__name__),
                  file=sys.stderr)
            return EXIT_SUBMIT
    return EXIT_OK


if __name__ == '__main__':
    sys.exit(main())
