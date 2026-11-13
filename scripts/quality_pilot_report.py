"""Compare annotated truth against real-OCR pipeline results (quality report).

Consumes the annotation CSV and the *.result.json / *.time.log files produced
by scripts/quality_pilot_run.py; prints a per-video and aggregate table using
the pilot counting rules (whitespace-stripped, unit-equivalent line hits;
field pass = hints candidate set equals the truth set). Never writes to the
database and never claims real-video accuracy when inputs are missing.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

TIME_LINE = re.compile(r'\s*([\d.]+)\s+(real|user|sys)')
RSS_LINE = re.compile(r'\s*(\d+)\s+maximum resident set size')


def normalize(text: str) -> str:
    return (text.replace(' ', '')
            .replace('㎡', 'M2').replace('m²', 'M2'))


def parse_time(log_text: str) -> dict:
    stats = {}
    for value, key in TIME_LINE.findall(log_text):
        stats[key] = float(value)
    match = RSS_LINE.search(log_text)
    if match:
        stats['max_rss_mb'] = round(int(match.group(1)) / 1024 / 1024, 1)
    return stats


def split_truth(raw: str) -> list[float]:
    return [float(part) for part in (raw or '').replace(';', ',').split(',') if part.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Build the annotated-video OCR quality comparison table')
    parser.add_argument('--csv', required=True, type=Path)
    parser.add_argument('--dir', required=True, type=Path)
    args = parser.parse_args(argv)

    rows = [row for row in csv.DictReader(args.csv.open(encoding='utf-8'))
            if (row.get('video_id') or '').strip() and row['video_id'] != 'listing_01']
    if not rows:
        parser.error('annotation csv has no real rows')

    field_totals = {'price': [0, 0], 'area': [0, 0], 'bedroom': [0, 0], 'community': [0, 0]}
    for row in rows:
        video_id = row['video_id'].strip()
        result_path = args.dir / (video_id + '.result.json')
        if not result_path.is_file():
            print(video_id, 'SKIPPED: no result json (run quality_pilot_run.py first)')
            continue
        result = json.loads(result_path.read_text(encoding='utf-8'))
        stats = parse_time((args.dir / (video_id + '.time.log')).read_text(encoding='utf-8'))
        hints = result.get('hints') or {}

        checks = {
            'price': (split_truth(row.get('price_truth_wan')), hints.get('price_mentions_wan') or []),
            'area': (split_truth(row.get('area_truth_sqm')), hints.get('area_mentions_sqm') or []),
            'bedroom': (split_truth(row.get('bedroom_truth')), [float(v) for v in (hints.get('bedroom_mentions') or [])]),
            'community': ([v for v in (row.get('community_truth') or '').split(';') if v],
                          [v for v in (hints.get('community_mentions') or [])]),
        }
        marks = []
        for name, (expected, actual) in checks.items():
            if name == 'price' and expected:
                # Multi-price screens legitimately keep every price as a clue;
                # the current asking price just has to be among them.
                passed = all(str(v) in [str(a) for a in actual] for v in expected)
            else:
                passed = (not expected and not actual) or (
                    sorted(str(v) for v in actual) == sorted(str(v) for v in expected))
            field_totals[name][0] += 1 if passed else 0
            field_totals[name][1] += 1
            marks.append(name + ('=OK' if passed else '=FAIL(' + str(actual) + ')'))
        other = [part for part in (row.get('other_prices_truth') or '').split(';') if part]
        other_leak = [part for part in other
                      if part and float(part.split(':')[0]) not in (hints.get('price_mentions_wan') or [])]
        print('%s | %s | other_prices_missing=%s | real=%.2fs rss=%sMB | status=%s' % (
            video_id, ' '.join(marks), other_leak or 'none',
            stats.get('real', 0.0), stats.get('max_rss_mb', '?'),
            result.get('ocr', {}).get('status')))

    print('\nAGGREGATE:', ' '.join(
        '%s %d/%d' % (name, ok, total) for name, (ok, total) in field_totals.items()))
    return 0


if __name__ == '__main__':
    sys.exit(main())
