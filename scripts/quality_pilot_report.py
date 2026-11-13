"""Evaluate real RapidOCR results against manually approved video annotations.

Missing or failed runs count as failures, never vanish from denominators.
A passing current-price check only confirms a textual price clue; it never
validates a signed transaction, listing provenance or price category.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

TIME_LINE = re.compile(r'\s*([\d.]+)\s+(real|user|sys)')
MAC_RSS_LINE = re.compile(r'\s*(\d+)\s+maximum resident set size')
GNU_RSS_LINE = re.compile(r'Maximum resident set size \(kbytes\):\s*(\d+)')


def normalize(text: str) -> str:
    text = re.sub(r'\s+', '', text).lower()
    for unit in ('㎡', 'm²', 'm2', '平米'):
        text = text.replace(unit, 'm2')
    return text


def parse_time(log_text: str) -> dict:
    stats = {}
    for value, key in TIME_LINE.findall(log_text):
        stats[key] = float(value)
    mac = MAC_RSS_LINE.search(log_text)
    gnu = GNU_RSS_LINE.search(log_text)
    if mac:
        stats['max_rss_mb'] = round(int(mac.group(1)) / 1024 / 1024, 1)
    elif gnu:
        stats['max_rss_mb'] = round(int(gnu.group(1)) / 1024, 1)
    return stats


def split_truth(raw: str) -> list[float]:
    return [float(x) for x in (raw or '').replace(';', ',').split(',') if x.strip()]


def _other_prices(raw: str) -> list[float]:
    prices = []
    for term in (raw or '').split(';'):
        if not term.strip():
            continue
        if ':' not in term:
            raise ValueError('other_prices_truth needs value:type entries')
        prices.append(float(term.split(':', 1)[0]))
    return prices


def _field_checks(row: dict, result: dict) -> tuple[dict[str, bool], list[float], tuple[int, int]]:
    hints = result.get('hints') or {}
    actual_price = {float(x) for x in (hints.get('price_mentions_wan') or [])}
    actual_area = {float(x) for x in (hints.get('area_mentions_sqm') or [])}
    actual_bedrooms = {float(x) for x in (hints.get('bedroom_mentions') or [])}
    actual_community = {str(x).strip() for x in (hints.get('community_mentions') or [])}
    expected_communities = {v.strip() for v in (row.get('community_truth') or '').split(';') if v.strip()}
    current_price = set(split_truth(row.get('price_truth_wan')))
    other_price = set(_other_prices(row.get('other_prices_truth')))
    ocr = result.get('ocr') or {}
    if result.get('ok') is not True or ocr.get('status') != 'ok' or ocr.get('engine') != 'rapidocr':
        return ({k: False for k in ('price', 'area', 'bedroom', 'community', 'other_prices', 'lines')},
                sorted(other_price), (0, 0))
    expected_lines = [x for x in (row.get('on_screen_text_truth') or '').split('|') if x.strip()]
    ocr_lines = [normalize(item.get('text') or '') for item in (ocr.get('items') or [])]
    matched_lines = sum(1 for expected in expected_lines
                        if any(normalize(expected) in line for line in ocr_lines))
    checks = {
        'price': current_price.issubset(actual_price) if current_price else not actual_price,
        'area': set(split_truth(row.get('area_truth_sqm'))) == actual_area,
        'bedroom': set(split_truth(row.get('bedroom_truth'))) == actual_bedrooms,
        'community': expected_communities == actual_community,
        'other_prices': other_price.issubset(actual_price),
        'lines': matched_lines == len(expected_lines),
    }
    return checks, sorted(other_price - actual_price), (matched_lines, len(expected_lines))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Evaluate real OCR quality against authorized video ground truth')
    parser.add_argument('--csv', required=True, type=Path)
    parser.add_argument('--dir', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        with args.csv.open(encoding='utf-8', newline='') as handle:
            rows = [row for row in csv.DictReader(handle)
                    if not (row.get('video_id') == 'listing_01'
                            and (row.get('source_note') or '').startswith('示例'))]
    except (OSError, UnicodeError, csv.Error) as exc:
        parser.error('cannot read annotation CSV: ' + type(exc).__name__)
    if not rows:
        parser.error('annotation CSV has no actual video rows')

    keys = ('price', 'area', 'bedroom', 'community', 'other_prices', 'lines')
    counts = {key: [0, 0] for key in keys}
    errors = 0
    total_lines = hits = 0
    for row in rows:
        video_id = (row.get('video_id') or '').strip()
        reasons = []
        checks = dict.fromkeys(keys, False)
        missing = []
        line_hits = (0, 0)
        stats = {}
        status = 'not_run'
        if not video_id:
            reasons.append('missing_video_id')
        elif not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,100}', video_id):
            reasons.append('unsafe_video_id')
        elif not (row.get('source_note') or '').strip():
            reasons.append('missing_source_note')
        else:
            result_path = args.dir / (video_id + '.result.json')
            stats_path = args.dir / (video_id + '.time.log')
            if not result_path.is_file() or result_path.is_symlink():
                reasons.append('missing_result_json')
            else:
                try:
                    result = json.loads(result_path.read_text(encoding='utf-8'))
                    checks, missing, line_hits = _field_checks(row, result)
                    status = str((result.get('ocr') or {}).get('status') or 'missing_ocr')
                    if status != 'ok' or (result.get('ocr') or {}).get('engine') != 'rapidocr':
                        reasons.append('real_ocr_not_ok')
                except (OSError, UnicodeError, ValueError, TypeError, KeyError) as exc:
                    reasons.append('invalid_result_' + type(exc).__name__)
            if stats_path.is_file() and not stats_path.is_symlink():
                try:
                    stats = parse_time(stats_path.read_text(encoding='utf-8'))
                except (OSError, UnicodeError, ValueError):
                    reasons.append('invalid_time_log')
            else:
                reasons.append('missing_time_log')
        if reasons:
            checks = dict.fromkeys(keys, False)
        for key in keys:
            counts[key][1] += 1
            counts[key][0] += int(checks[key])
        hits += line_hits[0]
        total_lines += line_hits[1]
        if not all(checks.values()):
            errors += 1
        marks = ' '.join(f'{key}={"OK" if checks[key] else "FAIL"}' for key in keys)
        print(f'{video_id or "(blank)"} | {marks} | other_prices_missing={missing or "none"}'
              f' | lines={line_hits[0]}/{line_hits[1]}'
              f' | real={stats.get("real", "?")}s rss={stats.get("max_rss_mb", "?")}MB'
              f' | status={status} | issues={reasons or "none"}')
    print('\nAGGREGATE:', ' '.join(
        f'{key} {ok}/{total}' for key, (ok, total) in counts.items()),
        f'line_hits {hits}/{total_lines}', f'failed_videos {errors}/{len(rows)}')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
