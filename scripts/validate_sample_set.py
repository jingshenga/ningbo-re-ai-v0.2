#!/usr/bin/env python3
"""Validate local provenance and annotation metadata for authorized HTML samples."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
from io import BytesIO, StringIO
import re
import sys
import zlib
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.collectors import extract_source_id
from app.collectors.parser import NUMERIC_RANGE_SEPARATOR, NUMERIC_TEXT_PATTERN
from app.collectors.text_normalization import normalize_text_for_comparison
from app.collectors.url_policy import CollectionError

SOURCES = ('beike', 'anjuke')
STATUSES = {'active', 'withdrawn', 'sold', 'unknown'}
PRICE_CONTEXT_SCENARIOS = ('oral_prices', 'transaction_prices')
NON_EXACT_PRICE_SCENARIO = 'non_exact_prices'
NON_EXACT_PRICE_RANGE_SCENARIO = 'non_exact_price_ranges'
NON_EXACT_AREA_SCENARIO = 'non_exact_areas'
NON_EXACT_AREA_RANGE_SCENARIO = 'non_exact_area_ranges'
SCENARIO_TAGS = {'missing_fields', 'multiple_prices', 'unknown_id',
                 NON_EXACT_PRICE_SCENARIO, NON_EXACT_AREA_SCENARIO} | set(PRICE_CONTEXT_SCENARIOS)
TITLE_SOURCE_CONFLICT_SCENARIO = 'title_source_conflict'
AMBIGUOUS_FIELD_SCENARIOS = {
    'source_id_conflict': ('source_listing_id', 'canonical_source_id_mismatch'),
    'multiple_communities': ('community_name', 'multiple_community_mentions'),
    'multiple_areas': ('area_sqm', 'multiple_area_mentions'),
    'area_ranges': ('area_sqm', 'multiple_area_mentions'),
    NON_EXACT_AREA_RANGE_SCENARIO: ('area_sqm', 'multiple_area_mentions'),
    'price_ranges': ('asking_price_wan', 'multiple_price_mentions'),
    NON_EXACT_PRICE_RANGE_SCENARIO: ('asking_price_wan', 'multiple_price_mentions'),
    'multiple_bedrooms': ('bedrooms', 'multiple_bedrooms_mentions'),
    'invalid_bedrooms': ('bedrooms', 'invalid_bedrooms_mentions'),
    'multiple_districts': ('district', 'multiple_district_mentions'),
    'multiple_floors': ('floor_text', 'multiple_floor_mentions'),
    'multiple_decorations': ('decoration', 'multiple_decoration_mentions'),
}
AMBIGUOUS_FIELD_CANDIDATE_COLUMNS = {
    'source_id_conflict': 'source_listing_id_candidates',
    'multiple_communities': 'community_candidates',
    'multiple_areas': 'area_candidates_sqm',
    'area_ranges': 'area_candidates_sqm',
    NON_EXACT_AREA_RANGE_SCENARIO: 'area_candidates_sqm',
    'price_ranges': 'price_candidates_wan',
    NON_EXACT_PRICE_RANGE_SCENARIO: 'price_candidates_wan',
    'multiple_bedrooms': 'bedroom_candidates',
    'invalid_bedrooms': 'invalid_bedroom_candidates',
    'multiple_districts': 'district_candidates',
    'multiple_floors': 'floor_candidates',
    'multiple_decorations': 'decoration_candidates',
}
SCENARIO_TAGS.update(AMBIGUOUS_FIELD_SCENARIOS)
SCENARIO_TAGS.add(TITLE_SOURCE_CONFLICT_SCENARIO)
REQUIRED_SCENARIO_TAGS = {'missing_fields', 'multiple_prices', 'unknown_id'}
REQUIRED_COLUMNS = {
    'sample_id', 'source', 'html_path', 'sha256', 'source_url', 'captured_at',
    'permission_reference', 'permission_scope', 'source_status', 'scenario_tags',
    'source_listing_id', 'title', 'community_name', 'district', 'area_sqm', 'bedrooms',
    'floor_text', 'decoration', 'asking_price_wan', 'price_candidates_wan',
    'reviewed_by', 'reviewed_at',
} | set(AMBIGUOUS_FIELD_CANDIDATE_COLUMNS.values())
LABEL_FIELDS = ('source_listing_id', 'title', 'community_name', 'district', 'area_sqm',
                'bedrooms', 'floor_text', 'decoration', 'asking_price_wan')
MAX_HTML_BYTES = 1_000_000
MAX_COMPRESSED_SAMPLE_BYTES = 2_000_000
MAX_MANIFEST_BYTES = 2_000_000


class SampleFileError(ValueError):
    pass


def read_sample_file(path: Path) -> tuple[bytes, bytes]:
    """Read a bounded saved sample, returning its stored and decoded bytes."""
    compressed = path.suffix.lower() == '.gz'
    limit = MAX_COMPRESSED_SAMPLE_BYTES if compressed else MAX_HTML_BYTES
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        if compressed:
            raise SampleFileError('compressed sample exceeds 2000000 byte limit')
        raise SampleFileError('HTML sample exceeds 1000000 byte limit')
    if not compressed:
        return raw, raw
    try:
        with gzip.GzipFile(fileobj=BytesIO(raw)) as stream:
            content = stream.read(MAX_HTML_BYTES + 1)
    except (OSError, EOFError, zlib.error) as exc:
        raise SampleFileError('gzip sample cannot be decompressed') from exc
    if len(content) > MAX_HTML_BYTES:
        raise SampleFileError('HTML sample exceeds 1000000 byte limit')
    return raw, content


def _parse_timestamp(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None and parsed.utcoffset() is not None else None


def _parse_decimal_number(value: str) -> Decimal | None:
    if not re.fullmatch(NUMERIC_TEXT_PATTERN, value):
        return None
    try:
        number = Decimal(value.replace(',', ''))
        return number if number.is_finite() else None
    except (InvalidOperation, ValueError):
        return None


def _parse_numeric_candidate(field: str, value: str):
    number = _parse_decimal_number(value)
    if number is not None:
        maximum = Decimal('20000') if field == 'area_sqm' else Decimal('200000')
        return number if field in {'area_sqm', 'asking_price_wan'} and 0 < number <= maximum else None
    if field == 'area_sqm':
        pattern = (rf'^\s*({NUMERIC_TEXT_PATTERN})\s*(?:㎡|m²|平米|平方米)?\s*'
                   rf'{NUMERIC_RANGE_SEPARATOR}\s*({NUMERIC_TEXT_PATTERN})\s*(?:㎡|m²|平米|平方米)\s*$')
        minimum, maximum = Decimal('0'), Decimal('20000')
    elif field == 'asking_price_wan':
        pattern = (rf'^\s*({NUMERIC_TEXT_PATTERN})\s*万?\s*{NUMERIC_RANGE_SEPARATOR}\s*'
                   rf'({NUMERIC_TEXT_PATTERN})\s*万\s*$')
        minimum, maximum = Decimal('0'), Decimal('200000')
    else:
        return None
    match = re.fullmatch(pattern, value, re.IGNORECASE)
    if match is None:
        return None
    lower = _parse_decimal_number(match.group(1))
    upper = _parse_decimal_number(match.group(2))
    if (lower is None or upper is None or not minimum < lower <= maximum
            or not minimum < upper <= maximum):
        return None
    return ('range', lower, upper)


def _number_in_range(value: str, minimum: Decimal, maximum: Decimal) -> bool:
    number = _parse_decimal_number(value)
    return number is not None and minimum < number <= maximum


def _bedroom_count_is_valid(value: str) -> bool:
    try:
        number = Decimal(value)
        return number.is_finite() and number == number.to_integral_value() and 0 <= number <= 20
    except (InvalidOperation, ValueError):
        return False


def _source_listing_id_is_valid(value: str, source: str) -> bool:
    minimum = 8 if source == 'beike' else 7
    return bool(re.fullmatch(rf'[0-9]{{{minimum},220}}', value))


def _ambiguous_candidate_is_valid(field: str, value: str, source: str) -> bool:
    if field == 'source_listing_id':
        return _source_listing_id_is_valid(value, source)
    if field == 'community_name':
        return 2 <= len(value) <= 28
    if field == 'area_sqm':
        return _parse_numeric_candidate(field, value) is not None
    if field == 'asking_price_wan':
        return _parse_numeric_candidate(field, value) is not None
    if field == 'bedrooms':
        try:
            number = Decimal(value)
            return (number.is_finite() and number == number.to_integral_value()
                    and 0 <= number <= 99)
        except (InvalidOperation, ValueError):
            return False
    return 2 <= len(value) <= 20


def _normalize_ambiguous_candidate(field: str, value: str):
    if field in {'area_sqm', 'asking_price_wan'}:
        return _parse_numeric_candidate(field, value)
    if field == 'bedrooms':
        return Decimal(value)
    return normalize_text_for_comparison(value)


def _has_symlink_component(path: Path, root: Path) -> bool:
    current = path
    while current != root and current != current.parent:
        if current.is_symlink():
            return True
        current = current.parent
    return False


def _diagnostic_text(value: str) -> str:
    return ''.join(
        f'\\u{ord(char):04x}' if ord(char) < 0x20 or 0x7f <= ord(char) <= 0x9f else char
        for char in value
    )


def _duplicate_column_names(fieldnames: list[str]) -> list[str]:
    seen = set()
    duplicates = set()
    for name in fieldnames:
        if name in seen:
            duplicates.add(name)
        else:
            seen.add(name)
    return sorted(duplicates)


def _validate_manifest(manifest: Path, root: Path, minimum_per_source: int = 20,
                       manifest_content: bytes | None = None):
    errors: list[str] = []
    counts = {source: 0 for source in SOURCES}
    statuses = {source: set() for source in SOURCES}
    coverage = {source: set() for source in SOURCES}
    sample_ids: set[str] = set()
    content_hashes: set[str] = set()
    root = root.resolve()
    raw_root = root / 'data/raw-pages'

    if minimum_per_source < 1:
        return ['minimum_per_source must be at least 1'], counts
    if manifest_content is None:
        try:
            with manifest.open('rb') as source:
                manifest_content = source.read(MAX_MANIFEST_BYTES + 1)
        except OSError:
            return [f'manifest cannot be read: {manifest.name}'], counts
    if len(manifest_content) > MAX_MANIFEST_BYTES:
        return [f'manifest exceeds {MAX_MANIFEST_BYTES} byte limit'], counts
    stream = StringIO(manifest_content.decode('utf-8-sig'), newline='')

    with stream:
        reader = csv.DictReader(stream, strict=True)
        fieldnames = reader.fieldnames or []
        if any(not name for name in fieldnames):
            return ['header contains an empty column name'], counts
        duplicate_columns = _duplicate_column_names(fieldnames)
        if duplicate_columns:
            safe_columns = [_diagnostic_text(name) for name in duplicate_columns]
            return [f"duplicate columns: {', '.join(safe_columns)}"], counts
        columns = set(fieldnames)
        missing_columns = sorted(REQUIRED_COLUMNS - columns)
        unsupported_columns = sorted(columns - REQUIRED_COLUMNS)
        if missing_columns:
            errors.append(f"missing columns: {', '.join(missing_columns)}")
        if unsupported_columns:
            safe_columns = [_diagnostic_text(name) for name in unsupported_columns]
            errors.append(f"unsupported columns: {', '.join(safe_columns)}")
        if errors:
            return errors, counts

        for line_number, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                errors.append(f'line {line_number}: row has a different number of fields than the header')
                continue
            raw_sample_id = row.get('sample_id') or ''
            sample_id = raw_sample_id.strip()
            label = _diagnostic_text(sample_id) or f'line {line_number}'
            source = (row.get('source') or '').strip()
            tags = {tag.strip() for tag in (row.get('scenario_tags') or '').split('|') if tag.strip()}

            def error(message: str):
                errors.append(f'{label}: {message}')

            if not sample_id:
                error('sample_id is required')
            elif sample_id in sample_ids:
                error('duplicate sample_id')
            if any(ord(char) < 0x20 or 0x7f <= ord(char) <= 0x9f
                   for char in raw_sample_id):
                error('sample_id must not contain control characters')
            sample_ids.add(sample_id)

            if source not in SOURCES:
                error('source must be beike or anjuke')
                continue
            counts[source] += 1

            path_value = row.get('html_path') or ''
            if any(ord(char) < 0x20 or 0x7f <= ord(char) <= 0x9f for char in path_value):
                error('html_path must not contain control characters')
            else:
                relative_path = Path(path_value.strip())
                if not relative_path.name.lower().endswith(('.html', '.html.gz')):
                    error('html_path must end with .html or .html.gz')
                if relative_path.is_absolute() or '..' in relative_path.parts:
                    error('html_path must be relative and stay under data/raw-pages')
                else:
                    html_path = root / relative_path
                    if (_has_symlink_component(html_path, root)
                            or _has_symlink_component(raw_root, root)):
                        error('symlinks are not allowed in sample paths')
                    else:
                        html_path = html_path.resolve()
                        if not html_path.is_relative_to(raw_root) or not html_path.is_file():
                            error('HTML file is missing or outside data/raw-pages')
                        else:
                            try:
                                raw_html, content = read_sample_file(html_path)
                            except SampleFileError as exc:
                                error(str(exc))
                            except OSError:
                                error('HTML file cannot be read')
                            else:
                                try:
                                    decoded_html = content.decode('utf-8')
                                except UnicodeDecodeError:
                                    error('HTML sample must be valid UTF-8')
                                else:
                                    if '\x00' in decoded_html:
                                        error('HTML sample must not contain a NUL character')
                                actual_hash = hashlib.sha256(raw_html).hexdigest()
                                expected_hash = (row.get('sha256') or '').strip().lower()
                                if not re.fullmatch(r'[0-9a-f]{64}', expected_hash) or actual_hash != expected_hash:
                                    error('sha256 does not match the local HTML file')
                                content_hash = hashlib.sha256(content).hexdigest()
                                if content_hash in content_hashes:
                                    error('duplicate HTML content across the sample set')
                                content_hashes.add(content_hash)

            source_url = row.get('source_url') or ''
            if not 12 <= len(source_url) <= 2000:
                error('source_url must be between 12 and 2000 characters')
            else:
                try:
                    url_listing_id = extract_source_id(source, source_url)
                except CollectionError as exc:
                    message = str(exc)
                    if 'query and fragment' in message:
                        error('source_url must omit query and fragment data')
                    elif 'whitespace or control' in message:
                        error('source_url must not contain whitespace or control characters')
                    elif message.startswith('Malformed'):
                        error('source_url is malformed')
                    else:
                        error('source_url must use the HTTPS Ningbo host without credentials or custom port')
                else:
                    labeled_id = (row.get('source_listing_id') or '').strip()
                    if ('source_id_conflict' in tags and url_listing_id
                            and url_listing_id not in {
                                value.strip() for value in
                                (row.get('source_listing_id_candidates') or '').split('|')
                            }):
                        error('source_listing_id_candidates must include the recognized URL ID')
                    elif ('source_id_conflict' not in tags and url_listing_id
                          and url_listing_id != labeled_id):
                        error('manual source_listing_id conflicts with the recognized URL ID')
                    if url_listing_id and 'unknown_id' in tags:
                        error('unknown_id tag conflicts with an ID recognized from source_url')

            for field in ('permission_reference', 'permission_scope', 'reviewed_by'):
                if not (row.get(field) or '').strip():
                    error(f'{field} is required')
            timestamps = {}
            for field in ('captured_at', 'reviewed_at'):
                timestamps[field] = _parse_timestamp((row.get(field) or '').strip())
                if timestamps[field] is None:
                    error(f'{field} must be an ISO-8601 timestamp with timezone')
            if (timestamps['captured_at'] is not None
                    and timestamps['reviewed_at'] is not None
                    and timestamps['reviewed_at'] < timestamps['captured_at']):
                error('reviewed_at must not be earlier than captured_at')

            title = (row.get('title') or '').strip()
            if len(title) > 500:
                error('title must be at most 500 characters')
            area = (row.get('area_sqm') or '').strip()
            if area and not _number_in_range(area, Decimal('0'), Decimal('20000')):
                error('area_sqm must be a finite number greater than 0 and at most 20000')
            bedrooms = (row.get('bedrooms') or '').strip()
            if bedrooms and not _bedroom_count_is_valid(bedrooms):
                error('bedrooms must be an integer from 0 to 20')

            status = (row.get('source_status') or '').strip()
            if status not in STATUSES:
                error('source_status must be active, withdrawn, sold, or unknown')
            else:
                statuses[source].add(status)
            unknown_id = 'unknown_id' in tags
            labeled_source_id = (row.get('source_listing_id') or '').strip()
            if len(labeled_source_id) > 220:
                error('source_listing_id must not exceed 220 characters')
            if (labeled_source_id and not _source_listing_id_is_valid(
                    labeled_source_id, source)):
                error('source_listing_id must contain only digits and match the source format')
            source_id_conflict = 'source_id_conflict' in tags
            if unknown_id and source_id_conflict:
                error('unknown_id and source_id_conflict cannot be used together')
            if 'invalid_bedrooms' in tags and 'multiple_bedrooms' in tags:
                error('invalid_bedrooms and multiple_bedrooms cannot be used together')
            source_id_unresolved = unknown_id or source_id_conflict
            if source_id_unresolved != (not bool((row.get('source_listing_id') or '').strip())):
                error('source_listing_id must be blank exactly when tagged unknown_id or source_id_conflict')
            if tags - SCENARIO_TAGS:
                error('scenario_tags contains unsupported values')
            coverage[source].update(tags)

            for field in LABEL_FIELDS:
                if ((row.get(field) or '').strip() or 'missing_fields' in tags
                        or (field == 'source_listing_id' and 'unknown_id' in tags)
                        or (field == 'asking_price_wan' and 'multiple_prices' in tags)
                        or (field == 'asking_price_wan' and NON_EXACT_PRICE_SCENARIO in tags)
                        or (field == 'area_sqm' and NON_EXACT_AREA_SCENARIO in tags)
                        or (field == 'asking_price_wan'
                            and any(tag in tags for tag in PRICE_CONTEXT_SCENARIOS))
                        or any(tag in tags and scenario_field == field
                               for tag, (scenario_field, _) in AMBIGUOUS_FIELD_SCENARIOS.items())):
                    continue
                error('blank manual labels must have a matching scenario tag')

            for tag, (field, _) in AMBIGUOUS_FIELD_SCENARIOS.items():
                if tag in tags and (row.get(field) or '').strip():
                    error(f'{field} must be blank when tagged {tag}')

            for tag, (field, _) in AMBIGUOUS_FIELD_SCENARIOS.items():
                candidate_column = AMBIGUOUS_FIELD_CANDIDATE_COLUMNS[tag]
                raw_candidates = (row.get(candidate_column) or '').split('|')
                candidates = [value.strip() for value in raw_candidates]
                if tag not in tags:
                    if any(candidates):
                        allowed_tags = {candidate_tag for candidate_tag, column
                                        in AMBIGUOUS_FIELD_CANDIDATE_COLUMNS.items()
                                        if column == candidate_column}
                        if candidate_column == 'price_candidates_wan':
                            allowed_tags.update({'multiple_prices', NON_EXACT_PRICE_SCENARIO})
                        elif candidate_column == 'area_candidates_sqm':
                            allowed_tags.add(NON_EXACT_AREA_SCENARIO)
                        if not allowed_tags & tags:
                            error(f'{candidate_column} requires scenario tag {tag}')
                    continue
                if tag == 'invalid_bedrooms':
                    if (len(candidates) != 1
                            or not _ambiguous_candidate_is_valid(field, candidates[0], source)
                            or Decimal(candidates[0]) <= 20):
                        error('invalid_bedroom_candidates requires one integer bedroom candidate above 20')
                    continue
                if tag in {'area_ranges', NON_EXACT_AREA_RANGE_SCENARIO,
                           'price_ranges', NON_EXACT_PRICE_RANGE_SCENARIO}:
                    normalized = [_normalize_ambiguous_candidate(field, value)
                                  for value in candidates
                                  if _ambiguous_candidate_is_valid(field, value, source)]
                    if (not candidates or len(normalized) != len(candidates)
                            or not any(isinstance(value, tuple) and value[0] == 'range'
                                       for value in normalized)):
                        error(f'{candidate_column} requires at least one valid numeric range candidate')
                    continue
                if (len(candidates) < 2 or any(not value for value in candidates)
                        or any(not _ambiguous_candidate_is_valid(field, value, source)
                               for value in candidates)):
                    error(f'{candidate_column} requires at least two valid distinct candidates')
                    continue
                normalized = [_normalize_ambiguous_candidate(field, value)
                              for value in candidates]
                if len(set(normalized)) < 2:
                    error(f'{candidate_column} requires at least two valid distinct candidates')

            if 'missing_fields' in tags and not any(
                    not (row.get(field) or '').strip()
                    and not (field == 'area_sqm'
                             and {NON_EXACT_AREA_SCENARIO,
                                  NON_EXACT_AREA_RANGE_SCENARIO} & tags)
                    and not (field == 'asking_price_wan'
                             and {'multiple_prices', NON_EXACT_PRICE_SCENARIO,
                                  NON_EXACT_PRICE_RANGE_SCENARIO} & tags)
                    for field in LABEL_FIELDS):
                error('missing_fields tag requires a blank label beyond unresolved multiple_prices')
            if NON_EXACT_AREA_SCENARIO in tags:
                candidates = [value.strip() for value in (row.get('area_candidates_sqm') or '').split('|')]
                candidate_value = (_parse_numeric_candidate('area_sqm', candidates[0])
                                   if len(candidates) == 1 else None)
                if (len(candidates) != 1 or not isinstance(candidate_value, Decimal)):
                    error('non_exact_areas requires one numeric area_candidates_sqm value')
                if {'multiple_areas', 'area_ranges', NON_EXACT_AREA_RANGE_SCENARIO} & tags:
                    error('non_exact_areas cannot be combined with multiple_areas or area range scenarios')
                if (row.get('area_sqm') or '').strip():
                    error('area_sqm must be blank when tagged non_exact_areas')
            if 'multiple_prices' in tags:
                candidates = [value.strip() for value in (row.get('price_candidates_wan') or '').split('|')
                              if value.strip()]
                candidate_values = [_parse_numeric_candidate('asking_price_wan', value)
                                    for value in candidates]
                if (len(candidates) < 2 or len(candidate_values) != len(candidates)
                        or any(value is None for value in candidate_values)
                        or len(set(candidate_values)) < 2):
                    error('multiple_prices requires at least two distinct price_candidates_wan values in (0, 200000]')
                if (row.get('asking_price_wan') or '').strip():
                    error('asking_price_wan must be blank when multiple_prices is unresolved')
            if NON_EXACT_PRICE_SCENARIO in tags:
                candidates = [value.strip() for value in (row.get('price_candidates_wan') or '').split('|')]
                candidate_value = (_parse_numeric_candidate('asking_price_wan', candidates[0])
                                   if len(candidates) == 1 else None)
                if (len(candidates) != 1 or not isinstance(candidate_value, Decimal)):
                    error('non_exact_prices requires one numeric price_candidates_wan value')
                if {'multiple_prices', 'price_ranges', NON_EXACT_PRICE_RANGE_SCENARIO} & tags:
                    error('non_exact_prices cannot be combined with multiple_prices or price range scenarios')
                if (row.get('asking_price_wan') or '').strip():
                    error('asking_price_wan must be blank when tagged non_exact_prices')
            elif ((row.get('asking_price_wan') or '').strip()
                  and not _number_in_range(row['asking_price_wan'].strip(), Decimal('0'), Decimal('200000'))):
                error('asking_price_wan must be a finite number greater than 0 and at most 200000')

    for source in SOURCES:
        if counts[source] < minimum_per_source:
            errors.append(f'{source}: {counts[source]} samples; requires {minimum_per_source}')
        if not {'active', 'withdrawn'} <= statuses[source]:
            errors.append(f'{source}: coverage must include active and withdrawn listings')
        if not REQUIRED_SCENARIO_TAGS <= coverage[source]:
            missing = ', '.join(sorted(REQUIRED_SCENARIO_TAGS - coverage[source]))
            errors.append(f'{source}: missing scenario coverage: {missing}')
    return errors, counts


def validate_manifest(manifest: Path, root: Path, minimum_per_source: int = 20,
                      *, manifest_content: bytes | None = None):
    try:
        return _validate_manifest(manifest, root, minimum_per_source, manifest_content)
    except UnicodeDecodeError:
        return ['manifest must be valid UTF-8'], {source: 0 for source in SOURCES}
    except csv.Error:
        return ['manifest CSV is malformed'], {source: 0 for source in SOURCES}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=Path('data/sample-manifest.csv'))
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--minimum-per-source', type=int, default=20)
    args = parser.parse_args()

    errors, counts = validate_manifest(args.manifest, args.root, args.minimum_per_source)
    for error in errors:
        print(f'ERROR: {error}')
    for source, count in counts.items():
        print(f'{source}: {count} samples')
    if errors:
        print('Metadata validation failed; this does not determine legal authorization.')
        return 1
    print('Metadata validation passed; this does not determine legal authorization.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
