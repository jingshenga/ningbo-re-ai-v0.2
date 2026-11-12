#!/usr/bin/env python3
"""Evaluate offline parser accuracy and coverage against a validated sample manifest."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from decimal import Decimal, InvalidOperation
from io import StringIO
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.collectors import parse_listing_html
from app.collectors.parser import CollectionError, PARSER_VERSION
from app.collectors.text_normalization import normalize_text_for_comparison
from scripts.validate_sample_set import (AMBIGUOUS_FIELD_CANDIDATE_COLUMNS,
                                         AMBIGUOUS_FIELD_SCENARIOS, LABEL_FIELDS, SOURCES,
                                         NON_EXACT_AREA_SCENARIO, PRICE_CONTEXT_SCENARIOS, STATUSES,
                                         NON_EXACT_AREA_RANGE_SCENARIO,
                                         NON_EXACT_PRICE_RANGE_SCENARIO,
                                         TITLE_SOURCE_CONFLICT_SCENARIO,
                                         MAX_MANIFEST_BYTES, SampleFileError,
                                         _parse_numeric_candidate, read_sample_file,
                                         validate_manifest)

NUMERIC_FIELDS = {'area_sqm', 'asking_price_wan'}
REVIEW_REQUIRED_FIELDS = {
    'source_listing_id', 'community_name', 'area_sqm', 'asking_price_wan',
}
PRODUCTION_MINIMUM_PER_SOURCE = 20
PRODUCTION_PRECISION_TARGET_PCT = 95
NON_EXACT_PRICE_SCENARIO = 'non_exact_prices'
NON_EXACT_RANGE_SCENARIO_WARNINGS = {
    NON_EXACT_PRICE_RANGE_SCENARIO: 'non_exact_asking_price',
    NON_EXACT_AREA_RANGE_SCENARIO: 'non_exact_area_sqm',
}
NON_EXACT_EVIDENCE_QUALIFIER = re.compile(
    r'(?:>=|<=|>|<|≥|≤|≧|≦|大约|约|大概|参考|估算|估计|预估|在|左右|上下|出头|附近|大于|超过|高于|多于|'
    r'小于|低于|不满|以上|以下|以内|不到|不足|不超过|不高于|不低于|至少|至多|最低|最高|'
    r'封顶|起售房源|起售|起价|起步价|起始价|起步|[+＋]|'
    r'起(?=$|[\s，,。；;：:、（）()]))'
)
SCENARIOS = ('missing_fields', 'multiple_prices', NON_EXACT_PRICE_SCENARIO,
             NON_EXACT_AREA_SCENARIO,
             'unknown_id', *PRICE_CONTEXT_SCENARIOS,
             *AMBIGUOUS_FIELD_SCENARIOS, TITLE_SOURCE_CONFLICT_SCENARIO)


def _sha256_file(path: Path, maximum_bytes: int = MAX_MANIFEST_BYTES) -> str:
    digest = hashlib.sha256()
    size = 0
    try:
        with path.open('rb') as stream:
            while True:
                chunk = stream.read(min(64 * 1024, maximum_bytes + 1 - size))
                if not chunk:
                    break
                size += len(chunk)
                if size > maximum_bytes:
                    raise ValueError('manifest exceeds 2000000 byte limit')
                digest.update(chunk)
    except OSError as exc:
        raise ValueError('manifest cannot be read') from exc
    return digest.hexdigest()


def _normalize(field: str, value):
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if field in NUMERIC_FIELDS:
        return _parse_numeric_candidate(field, str(value))
    if field == 'bedrooms':
        try:
            number = Decimal(str(value))
            return int(number) if number.is_finite() and number == number.to_integral_value() else None
        except InvalidOperation:
            return None
    return normalize_text_for_comparison(str(value))


def _has_qualified_evidence(mention: dict) -> bool:
    quote = mention.get('quote')
    candidate = mention.get('candidate_value')
    return (isinstance(quote, str) and candidate is not None
            and str(candidate) in quote
            and NON_EXACT_EVIDENCE_QUALIFIER.search(quote) is not None)


def _expected_fields(row: dict, tags: set[str]):
    expected = {}
    for field in LABEL_FIELDS:
        value = (row.get(field) or '').strip()
        if value:
            expected[field] = value
        elif any(tag in tags and scenario_field == field
                 for tag, (scenario_field, _) in AMBIGUOUS_FIELD_SCENARIOS.items()):
            expected[field] = None
        elif field == 'asking_price_wan' and 'multiple_prices' in tags:
            continue
        elif field == 'asking_price_wan' and NON_EXACT_PRICE_SCENARIO in tags:
            expected[field] = None
        elif field == 'area_sqm' and NON_EXACT_AREA_SCENARIO in tags:
            expected[field] = None
        elif field == 'asking_price_wan' and any(tag in tags for tag in PRICE_CONTEXT_SCENARIOS):
            expected[field] = None
        elif 'missing_fields' in tags:
            expected[field] = None
        elif field == 'source_listing_id' and 'unknown_id' in tags:
            expected[field] = None
    return expected


def _percent(numerator: int, denominator: int):
    return round(numerator / denominator * 100, 2) if denominator else None


def evaluate_manifest(manifest: Path, root: Path,
                      minimum_per_source: int = PRODUCTION_MINIMUM_PER_SOURCE):
    try:
        with manifest.open('rb') as stream:
            manifest_content = stream.read(MAX_MANIFEST_BYTES + 1)
    except OSError as exc:
        raise ValueError('manifest cannot be read') from exc
    if len(manifest_content) > MAX_MANIFEST_BYTES:
        raise ValueError('manifest exceeds 2000000 byte limit')
    manifest_sha256 = hashlib.sha256(manifest_content).hexdigest()
    errors, counts = validate_manifest(
        manifest, root, minimum_per_source, manifest_content=manifest_content)
    if errors:
        raise ValueError('; '.join(errors))

    metrics = {
        source: {
            field: {'labeled': 0, 'covered': 0, 'correct': 0, 'present_correct': 0}
            for field in LABEL_FIELDS
        }
        for source in SOURCES
    }
    scenario_counts = {
        source: {tag: {'samples': 0, 'passed': 0} for tag in SCENARIOS}
        for source in SOURCES
    }
    sample_composition = {
        source: {
            'statuses': {status: 0 for status in sorted(STATUSES)},
            'scenarios': {tag: 0 for tag in SCENARIOS},
        }
        for source in SOURCES
    }

    with StringIO(manifest_content.decode('utf-8-sig'), newline='') as stream:
        for row in csv.DictReader(stream):
            source = row['source'].strip()
            tags = {tag.strip() for tag in (row.get('scenario_tags') or '').split('|') if tag.strip()}
            sample_composition[source]['statuses'][row['source_status'].strip()] += 1
            for tag in tags:
                sample_composition[source]['scenarios'][tag] += 1
            html_path = root / row['html_path'].strip()
            try:
                stored_content, content = read_sample_file(html_path)
                if hashlib.sha256(stored_content).hexdigest() != row['sha256'].strip().lower():
                    raise ValueError(f"{row['sample_id']}: saved HTML changed during evaluation")
                html = content.decode('utf-8')
                parsed = parse_listing_html(source, row['source_url'].strip(), html)
            except (OSError, UnicodeDecodeError, SampleFileError, CollectionError) as exc:
                raise ValueError(f"{row['sample_id']}: saved HTML could not be parsed") from exc

            fields = parsed.fields
            for field, expected in _expected_fields(row, tags).items():
                metric = metrics[source][field]
                predicted = _normalize(field, fields.get(field))
                truth = _normalize(field, expected)
                metric['labeled'] += 1
                metric['covered'] += predicted is not None
                metric['correct'] += predicted == truth
                metric['present_correct'] += predicted is not None and predicted == truth

            if 'missing_fields' in tags:
                missing = [field for field in LABEL_FIELDS
                           if not (row.get(field) or '').strip()
                           and not (field == 'area_sqm' and NON_EXACT_AREA_SCENARIO in tags)
                           and not (field == 'asking_price_wan' and 'multiple_prices' in tags)]
                scenario_counts[source]['missing_fields']['samples'] += 1
                scenario_counts[source]['missing_fields']['passed'] += bool(
                    missing and all(fields.get(field) is None for field in missing)
                    and (not REVIEW_REQUIRED_FIELDS.intersection(missing)
                         or not parsed.ready_for_review)
                    and 'visible_text_truncated' not in parsed.warnings)
            if 'multiple_prices' in tags:
                scenario_counts[source]['multiple_prices']['samples'] += 1
                price_evidence = fields.get('field_evidence', {}).get('asking_price_wan', {})
                price_mentions = price_evidence.get('mentions', [])
                parsed_prices = {
                    _normalize('asking_price_wan', mention.get('candidate_value'))
                    for mention in price_mentions
                }
                expected_prices = {
                    _normalize('asking_price_wan', value)
                    for value in (row.get('price_candidates_wan') or '').split('|')
                    if value.strip()
                }
                scenario_counts[source]['multiple_prices']['passed'] += (
                    fields.get('asking_price_wan') is None
                    and not parsed.ready_for_review
                    and 'multiple_price_mentions' in parsed.warnings
                    and bool(price_mentions)
                    and not price_evidence.get('mentions_truncated', True)
                    and None not in parsed_prices
                    and parsed_prices == expected_prices)
            if NON_EXACT_PRICE_SCENARIO in tags:
                scenario_counts[source][NON_EXACT_PRICE_SCENARIO]['samples'] += 1
                price_evidence = fields.get('field_evidence', {}).get('asking_price_wan', {})
                price_mentions = price_evidence.get('mentions', [])
                parsed_prices = {
                    _normalize('asking_price_wan', mention.get('candidate_value'))
                    for mention in price_mentions
                }
                expected_prices = {
                    _normalize('asking_price_wan', value)
                    for value in (row.get('price_candidates_wan') or '').split('|')
                    if value.strip()
                }
                scenario_counts[source][NON_EXACT_PRICE_SCENARIO]['passed'] += (
                    fields.get('asking_price_wan') is None
                    and not parsed.ready_for_review
                    and 'non_exact_asking_price' in parsed.warnings
                    and 'visible_text_truncated' not in parsed.warnings
                    and bool(price_mentions)
                    and all(mention.get('is_non_exact') is True
                            for mention in price_mentions)
                    and all(_has_qualified_evidence(mention)
                            for mention in price_mentions)
                    and not price_evidence.get('mentions_truncated', True)
                    and None not in parsed_prices
                    and parsed_prices == expected_prices)
            if NON_EXACT_AREA_SCENARIO in tags:
                scenario_counts[source][NON_EXACT_AREA_SCENARIO]['samples'] += 1
                area_evidence = fields.get('field_evidence', {}).get('area_sqm', {})
                area_mentions = area_evidence.get('mentions', [])
                parsed_areas = {
                    _normalize('area_sqm', mention.get('candidate_value'))
                    for mention in area_mentions
                }
                expected_areas = {
                    _normalize('area_sqm', value)
                    for value in (row.get('area_candidates_sqm') or '').split('|')
                    if value.strip()
                }
                scenario_counts[source][NON_EXACT_AREA_SCENARIO]['passed'] += (
                    fields.get('area_sqm') is None
                    and not parsed.ready_for_review
                    and 'non_exact_area_sqm' in parsed.warnings
                    and 'visible_text_truncated' not in parsed.warnings
                    and bool(area_mentions)
                    and all(mention.get('is_non_exact') is True
                            for mention in area_mentions)
                    and all(_has_qualified_evidence(mention)
                            for mention in area_mentions)
                    and not area_evidence.get('mentions_truncated', True)
                    and None not in parsed_areas
                    and parsed_areas == expected_areas)
            if 'unknown_id' in tags:
                scenario_counts[source]['unknown_id']['samples'] += 1
                scenario_counts[source]['unknown_id']['passed'] += (
                    fields.get('source_listing_id') is None
                    and not parsed.ready_for_review)
            for tag in PRICE_CONTEXT_SCENARIOS:
                if tag in tags:
                    scenario_counts[source][tag]['samples'] += 1
                    expected_price = _normalize('asking_price_wan', row.get('asking_price_wan'))
                    predicted_price = _normalize('asking_price_wan', fields.get('asking_price_wan'))
                    price_result_is_clean = (
                        'multiple_price_mentions' not in parsed.warnings
                        and 'visible_text_truncated' not in parsed.warnings
                    )
                    if expected_price is None:
                        price_result_is_clean = (
                            price_result_is_clean
                            and 'missing_asking_price_wan' in parsed.warnings
                            and not parsed.ready_for_review
                        )
                    scenario_counts[source][tag]['passed'] += (
                        predicted_price == expected_price and price_result_is_clean)
            if TITLE_SOURCE_CONFLICT_SCENARIO in tags:
                scenario_counts[source][TITLE_SOURCE_CONFLICT_SCENARIO]['samples'] += 1
                title_evidence = fields.get('field_evidence', {}).get('title', {})
                ambiguous_sources = {
                    warning.split(':', 1)[1] for warning in parsed.warnings
                    if warning.startswith('ambiguous_title_source:')
                }
                scenario_counts[source][TITLE_SOURCE_CONFLICT_SCENARIO]['passed'] += (
                    _normalize('title', fields.get('title'))
                    == _normalize('title', row.get('title'))
                    and bool(ambiguous_sources)
                    and title_evidence.get('source') not in ambiguous_sources)
            for tag, (field, warning) in AMBIGUOUS_FIELD_SCENARIOS.items():
                if tag in tags:
                    scenario_counts[source][tag]['samples'] += 1
                    candidate_column = AMBIGUOUS_FIELD_CANDIDATE_COLUMNS[tag]
                    evidence = fields.get('field_evidence', {}).get(field, {})
                    mentions = evidence.get('mentions', [])
                    parsed_candidates = {
                        _normalize(field, mention.get('candidate_value'))
                        for mention in mentions
                    }
                    expected_candidates = {
                        _normalize(field, value)
                        for value in (row.get(candidate_column) or '').split('|')
                        if value.strip()
                    }
                    range_candidates = {
                        candidate for candidate in expected_candidates
                        if isinstance(candidate, tuple)
                    } if tag in NON_EXACT_RANGE_SCENARIO_WARNINGS else set()
                    qualified_range_mentions = [
                        mention for mention in mentions
                        if (tag not in NON_EXACT_RANGE_SCENARIO_WARNINGS
                            or _normalize(field, mention.get('candidate_value'))
                            in range_candidates)
                        and (mention.get('is_non_exact') is True
                             or (isinstance(mention.get('quote'), str)
                                 and NON_EXACT_EVIDENCE_QUALIFIER.search(
                                     mention['quote']) is not None))
                    ] if tag in {'area_ranges', 'price_ranges',
                                 *NON_EXACT_RANGE_SCENARIO_WARNINGS} else []
                    range_mentions = [
                        mention for mention in mentions
                        if _normalize(field, mention.get('candidate_value')) in range_candidates
                    ] if range_candidates else []
                    non_exact_range_evidence_is_valid = (
                        tag not in NON_EXACT_RANGE_SCENARIO_WARNINGS
                        or (bool(range_mentions)
                            and len(qualified_range_mentions) == len(range_mentions)
                            and NON_EXACT_RANGE_SCENARIO_WARNINGS[tag] in parsed.warnings
                            and all(mention.get('is_non_exact') is True
                                    and _has_qualified_evidence(mention)
                                    for mention in range_mentions))
                    )
                    scenario_counts[source][tag]['passed'] += (
                        fields.get(field) is None
                        and (field not in REVIEW_REQUIRED_FIELDS
                             or not parsed.ready_for_review)
                        and warning in parsed.warnings
                        and (not qualified_range_mentions
                             or (tag in NON_EXACT_RANGE_SCENARIO_WARNINGS
                                 or (field == 'asking_price_wan'
                                     and 'non_exact_asking_price' in parsed.warnings)
                                 or (field == 'area_sqm'
                                     and 'non_exact_area_sqm' in parsed.warnings))
                                 and all(mention.get('is_non_exact') is True
                                         and _has_qualified_evidence(mention)
                                         for mention in qualified_range_mentions))
                        and non_exact_range_evidence_is_valid
                        and bool(mentions)
                        and not evidence.get('mentions_truncated', True)
                        and None not in parsed_candidates
                        and parsed_candidates == expected_candidates)

    if _sha256_file(manifest) != manifest_sha256:
        raise ValueError('manifest changed during parser evaluation')

    report = {
        'parser_version': PARSER_VERSION,
        'manifest_sha256': manifest_sha256,
        'sample_counts': counts,
        'sample_composition': sample_composition,
        'sample_requirements': {
            source: {
                'required': PRODUCTION_MINIMUM_PER_SOURCE,
                'observed': counts[source],
                'met': counts[source] >= PRODUCTION_MINIMUM_PER_SOURCE,
            }
            for source in SOURCES
        },
        'fields': {},
        'scenarios': {},
        'metric_definitions': {
            'accuracy_pct': 'exact matches divided by labeled values; textual fields use Unicode NFC and collapsed whitespace; title and structured listing fields are included; explicit missing and ambiguous fields plus unknown IDs are included; unresolved multiple prices are evaluated as a separate scenario',
            'coverage_pct': 'non-empty parser outputs divided by labeled values',
            'precision_pct': 'exact matches divided by non-empty parser outputs',
            'precision_target_met': 'true when exact correct and extracted counts meet the 95% target; displayed percentage is rounded and sample-count adequacy is reported separately',
        },
        'authorization_notice': 'Manifest checks validate metadata only; they do not establish legal authorization.',
    }
    for source in SOURCES:
        report['fields'][source] = {}
        for field, values in metrics[source].items():
            precision_pct = _percent(values['present_correct'], values['covered'])
            report['fields'][source][field] = {
                **values,
                'accuracy_pct': _percent(values['correct'], values['labeled']),
                'coverage_pct': _percent(values['covered'], values['labeled']),
                'precision_pct': precision_pct,
                'precision_target_pct': PRODUCTION_PRECISION_TARGET_PCT,
                'precision_target_met': (values['covered'] > 0
                                         and values['present_correct'] * 100
                                         >= values['covered'] * PRODUCTION_PRECISION_TARGET_PCT),
            }
        report['scenarios'][source] = {
            tag: {
                **values,
                'pass_rate_pct': _percent(values['passed'], values['samples']),
            }
            for tag, values in scenario_counts[source].items()
        }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=Path('data/sample-manifest.csv'))
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--minimum-per-source', type=int,
                        default=PRODUCTION_MINIMUM_PER_SOURCE)
    args = parser.parse_args()
    try:
        report = evaluate_manifest(args.manifest, args.root, args.minimum_per_source)
    except ValueError as exc:
        print(f'Evaluation refused: {exc}')
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
