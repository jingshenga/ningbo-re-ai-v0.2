import csv
import gzip
import hashlib
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.validate_sample_set import (MAX_MANIFEST_BYTES, REQUIRED_COLUMNS,
                                         _duplicate_column_names,
                                         _normalize_ambiguous_candidate, validate_manifest)


def build_manifest(root: Path):
    raw_root = root / 'data/raw-pages'
    raw_root.mkdir(parents=True)
    manifest = root / 'manifest.csv'
    rows = []
    for source, host in (('beike', 'nb.ke.com'), ('anjuke', 'ningbo.anjuke.com')):
        for index in range(5):
            if index == 0:
                status, tags, listing_id, community, price, candidates = 'active', '', 'id-1', '小区', '400', ''
            elif index == 1:
                status, tags, listing_id, community, price, candidates = 'withdrawn', '', 'id-2', '小区', '390', ''
            elif index == 2:
                status, tags, listing_id, community, price, candidates = 'active', 'missing_fields', 'id-3', '', '380', ''
            elif index == 3:
                status, tags, listing_id, community, price, candidates = 'active', 'multiple_prices', 'id-4', '小区', '', '360|370'
            else:
                status, tags, listing_id, community, price, candidates = 'unknown', 'unknown_id|missing_fields', '', '', '350', ''

            relative = Path('data/raw-pages') / f'{source}-{index}.html'
            content = f'<html>{source}-{index}</html>'.encode()
            (root / relative).write_bytes(content)
            if index == 4:
                source_url = (f'https://{host}/ershoufang/list' if source == 'beike'
                              else f'https://{host}/sale/list')
            else:
                url_id = f'1234567{index}'
                source_url = (f'https://{host}/ershoufang/{url_id}.html' if source == 'beike'
                              else f'https://{host}/sale/{url_id}')
                listing_id = url_id
            rows.append({
                'sample_id': f'{source}-{index}',
                'source': source,
                'html_path': relative.as_posix(),
                'sha256': hashlib.sha256(content).hexdigest(),
                'source_url': source_url,
                'captured_at': '2026-11-10T10:00:00+08:00',
                'permission_reference': 'permission-record-1',
                'permission_scope': 'offline parsing evaluation',
                'source_status': status,
                'scenario_tags': tags,
                'source_listing_id': listing_id,
                'title': f'{source} {index} 标题' if index != 2 else '',
                'community_name': community,
                'district': '鄞州',
                'area_sqm': '120',
                'bedrooms': '3',
                'floor_text': '高楼层',
                'decoration': '精装',
                'asking_price_wan': price,
                'price_candidates_wan': candidates,
                'source_listing_id_candidates': '',
                'community_candidates': '',
                'area_candidates_sqm': '',
                'bedroom_candidates': '',
                'invalid_bedroom_candidates': '',
                'district_candidates': '',
                'floor_candidates': '',
                'decoration_candidates': '',
                'reviewed_by': 'operator-1',
                'reviewed_at': '2026-11-10T11:00:00+08:00',
            })
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)
    return manifest, rows


def test_validates_both_sources_and_required_label_coverage(tmp_path):
    manifest, _ = build_manifest(tmp_path)

    errors, counts = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert errors == []
    assert counts == {'beike': 5, 'anjuke': 5}


@pytest.mark.parametrize('scenario', ['oral_prices', 'transaction_prices'])
def test_non_listing_price_scenario_can_explain_missing_listing_price(tmp_path, scenario):
    manifest, rows = build_manifest(tmp_path)
    rows[0]['asking_price_wan'] = ''
    rows[0]['scenario_tags'] = scenario
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, counts = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert errors == []
    assert counts == {'beike': 5, 'anjuke': 5}


def test_non_exact_area_scenario_requires_one_numeric_area_candidate(tmp_path):
    manifest, rows = build_manifest(tmp_path)
    rows[0]['area_sqm'] = ''
    rows[0]['scenario_tags'] = 'non_exact_areas'
    rows[0]['area_candidates_sqm'] = '100'
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, counts = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert errors == []
    assert counts == {'beike': 5, 'anjuke': 5}


@pytest.mark.parametrize('candidates', ['', '100|120', '100-120', '0', '20001'])
def test_non_exact_area_scenario_rejects_invalid_candidate_evidence(tmp_path, candidates):
    manifest, rows = build_manifest(tmp_path)
    rows[0]['area_sqm'] = ''
    rows[0]['scenario_tags'] = 'non_exact_areas'
    rows[0]['area_candidates_sqm'] = candidates
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('non_exact_areas requires one numeric area_candidates_sqm value'
               in error for error in errors)


def test_non_exact_price_scenario_requires_one_qualified_price_candidate(tmp_path):
    manifest, rows = build_manifest(tmp_path)
    rows[0]['asking_price_wan'] = ''
    rows[0]['scenario_tags'] = 'non_exact_prices'
    rows[0]['price_candidates_wan'] = '200'
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, counts = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert errors == []
    assert counts == {'beike': 5, 'anjuke': 5}


@pytest.mark.parametrize('candidates', ['', '200|300', '300万-320万', '0', '200001'])
def test_non_exact_price_scenario_rejects_invalid_candidate_evidence(tmp_path, candidates):
    manifest, rows = build_manifest(tmp_path)
    rows[0]['asking_price_wan'] = ''
    rows[0]['scenario_tags'] = 'non_exact_prices'
    rows[0]['price_candidates_wan'] = candidates
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('non_exact_prices requires one numeric price_candidates_wan value'
               in error for error in errors)


def test_rejects_html_content_reused_across_sources(tmp_path):
    manifest, rows = build_manifest(tmp_path)
    for index in range(5):
        beike = rows[index]
        anjuke = rows[index + 5]
        content = (tmp_path / beike['html_path']).read_bytes()
        (tmp_path / anjuke['html_path']).write_bytes(content)
        anjuke['sha256'] = hashlib.sha256(content).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, counts = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('duplicate HTML content across the sample set' in error for error in errors)
    assert counts == {'beike': 5, 'anjuke': 5}


def test_ambiguous_bedroom_candidates_can_record_out_of_range_page_mention(tmp_path):
    manifest, rows = build_manifest(tmp_path)
    rows[0]['bedrooms'] = ''
    rows[0]['scenario_tags'] = 'multiple_bedrooms'
    rows[0]['bedroom_candidates'] = '3|21'
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert errors == []


def test_invalid_bedroom_scenario_requires_one_out_of_range_candidate(tmp_path):
    manifest, rows = build_manifest(tmp_path)
    rows[0]['bedrooms'] = ''
    rows[0]['scenario_tags'] = 'invalid_bedrooms'
    rows[0]['invalid_bedroom_candidates'] = '21'
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert errors == []


@pytest.mark.parametrize('candidate', ['20', '21|22', '100', '2.5'])
def test_invalid_bedroom_scenario_rejects_wrong_candidate_shape(tmp_path, candidate):
    manifest, rows = build_manifest(tmp_path)
    rows[0]['bedrooms'] = ''
    rows[0]['scenario_tags'] = 'invalid_bedrooms'
    rows[0]['invalid_bedroom_candidates'] = candidate
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('invalid_bedroom_candidates requires one integer bedroom candidate above 20' in error
               for error in errors)


def test_invalid_and_multiple_bedroom_scenarios_cannot_be_combined(tmp_path):
    manifest, rows = build_manifest(tmp_path)
    rows[0]['bedrooms'] = ''
    rows[0]['scenario_tags'] = 'invalid_bedrooms|multiple_bedrooms'
    rows[0]['invalid_bedroom_candidates'] = '21'
    rows[0]['bedroom_candidates'] = '3|21'
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('invalid_bedrooms and multiple_bedrooms cannot be used together' in error
               for error in errors)


def test_sample_manifest_template_matches_validator_columns():
    template = Path(__file__).resolve().parents[1] / 'docs' / 'SAMPLE_MANIFEST_TEMPLATE.csv'
    with template.open(encoding='utf-8', newline='') as stream:
        columns = next(csv.reader(stream))

    assert len(columns) == len(set(columns))
    assert set(columns) == REQUIRED_COLUMNS


@pytest.mark.parametrize('over_limit', [False, True])
def test_manifest_size_limit_matches_parser_evaluator(tmp_path, over_limit):
    manifest, _ = build_manifest(tmp_path)
    content = manifest.read_bytes()
    padding_size = MAX_MANIFEST_BYTES - len(content) + int(over_limit)
    manifest.write_bytes(content + b'\n' * padding_size)

    errors, counts = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    if over_limit:
        assert errors == [f'manifest exceeds {MAX_MANIFEST_BYTES} byte limit']
        assert counts == {'beike': 0, 'anjuke': 0}
    else:
        assert errors == []
        assert counts == {'beike': 5, 'anjuke': 5}


def test_duplicate_column_detection_does_not_rescan_the_header():
    class CountForbidden(list):
        def count(self, value):
            raise AssertionError('duplicate detection must use one pass')

    assert _duplicate_column_names(CountForbidden(['z', 'a', 'z', 'b', 'a'])) == ['a', 'z']


@pytest.mark.parametrize(('tag', 'field', 'candidate_column', 'candidates'), [
    ('source_id_conflict', 'source_listing_id', 'source_listing_id_candidates',
     '12345670|12345670'),
    ('multiple_communities', 'community_name', 'community_candidates',
     '东湖花园|东湖花园'),
    ('multiple_areas', 'area_sqm', 'area_candidates_sqm', '120|120.0'),
    ('multiple_districts', 'district', 'district_candidates', '鄞州|鄞州'),
])
def test_ambiguous_field_scenarios_require_distinct_manual_candidates(
        tmp_path, tag, field, candidate_column, candidates):
    manifest, rows = build_manifest(tmp_path)
    rows[0][field] = ''
    rows[0]['scenario_tags'] = tag
    rows[0][candidate_column] = candidates
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any(f'{candidate_column} requires at least two valid distinct candidates' in error
               for error in errors)


@pytest.mark.parametrize(('row_index', 'source_url', 'labeled_id'), [
    (0, 'https://nb.ke.com/ershoufang/list', 'listing-123'),
    (5, 'https://ningbo.anjuke.com/sale/list', 'listing-123'),
    (0, 'https://nb.ke.com/ershoufang/list', '1234567'),
    (5, 'https://ningbo.anjuke.com/sale/list', '123456'),
    (0, 'https://nb.ke.com/ershoufang/list', '１２３45678'),
])
def test_regular_source_listing_id_must_match_source_numeric_format(
        tmp_path, row_index, source_url, labeled_id):
    manifest, rows = build_manifest(tmp_path)
    rows[row_index]['source_url'] = source_url
    rows[row_index]['source_listing_id'] = labeled_id
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('source_listing_id must contain only digits and match the source format'
               in error for error in errors)


@pytest.mark.parametrize('candidates', ['0|120', '120|20000.1', 'NaN|120'])
def test_area_candidates_must_be_finite_and_within_area_range(tmp_path, candidates):
    manifest, rows = build_manifest(tmp_path)
    rows[0]['area_sqm'] = ''
    rows[0]['scenario_tags'] = 'multiple_areas'
    rows[0]['area_candidates_sqm'] = candidates
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('area_candidates_sqm requires at least two valid distinct candidates' in error
               for error in errors)


def test_validator_accepts_well_formed_grouped_area_and_price_candidates(tmp_path):
    manifest, rows = build_manifest(tmp_path)
    rows[0]['area_sqm'] = ''
    rows[0]['scenario_tags'] = 'multiple_areas'
    rows[0]['area_candidates_sqm'] = '1,234|1,235'
    rows[3]['scenario_tags'] = 'multiple_prices'
    rows[3]['asking_price_wan'] = ''
    rows[3]['price_candidates_wan'] = '1,234|1,235'
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert errors == []


def test_validator_accepts_numeric_ranges_as_single_ambiguity_candidates(tmp_path):
    manifest, rows = build_manifest(tmp_path)
    rows[0]['area_sqm'] = ''
    rows[0]['scenario_tags'] = 'multiple_areas'
    rows[0]['area_candidates_sqm'] = '120㎡-130㎡|125'
    rows[3]['asking_price_wan'] = ''
    rows[3]['scenario_tags'] = 'multiple_prices'
    rows[3]['price_candidates_wan'] = '300万-320万|310'
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert errors == []


def test_validator_accepts_range_only_candidate_scenarios(tmp_path):
    manifest, rows = build_manifest(tmp_path)
    rows[0]['area_sqm'] = ''
    rows[0]['scenario_tags'] = 'area_ranges'
    rows[0]['area_candidates_sqm'] = '120㎡-130㎡'
    rows[1]['area_sqm'] = ''
    rows[1]['scenario_tags'] = 'non_exact_area_ranges'
    rows[1]['area_candidates_sqm'] = '100㎡-120㎡'
    rows[3]['scenario_tags'] = 'multiple_prices|non_exact_price_ranges'
    rows[3]['price_candidates_wan'] = '300万-320万|310'
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert errors == []


def test_missing_fields_tag_cannot_reuse_multiple_price_blank(tmp_path):
    manifest, rows = build_manifest(tmp_path)
    rows[0]['asking_price_wan'] = ''
    rows[0]['scenario_tags'] = 'missing_fields|multiple_prices'
    rows[0]['price_candidates_wan'] = '300|310'
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('missing_fields tag requires a blank label beyond unresolved multiple_prices'
               in error for error in errors)


@pytest.mark.parametrize(('field', 'tag', 'column', 'value'), [
    ('area_sqm', 'area_ranges', 'area_candidates_sqm', '120|130'),
    ('area_sqm', 'non_exact_area_ranges', 'area_candidates_sqm', '120|130'),
    ('asking_price_wan', 'price_ranges', 'price_candidates_wan', '300|320'),
    ('asking_price_wan', 'non_exact_price_ranges', 'price_candidates_wan', '300|320'),
])
def test_validator_requires_a_range_candidate_for_range_scenarios(
        tmp_path, field, tag, column, value):
    manifest, rows = build_manifest(tmp_path)
    row = rows[0 if field == 'area_sqm' else 3]
    row[field] = ''
    row['scenario_tags'] = tag
    row[column] = value
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any(f'{column} requires at least one valid numeric range candidate' in error
               for error in errors)


@pytest.mark.parametrize(('field', 'tag', 'column', 'value'), [
    ('area_sqm', 'multiple_areas', 'area_candidates_sqm', '120-130|125'),
    ('area_sqm', 'multiple_areas', 'area_candidates_sqm', '20000㎡-20001㎡|125'),
    ('asking_price_wan', 'multiple_prices', 'price_candidates_wan', '300-320|310'),
    ('asking_price_wan', 'multiple_prices', 'price_candidates_wan', '300万-200001万|310'),
])
def test_validator_rejects_malformed_or_out_of_range_numeric_ranges(
        tmp_path, field, tag, column, value):
    manifest, rows = build_manifest(tmp_path)
    row = rows[0 if tag == 'multiple_areas' else 3]
    row[field] = ''
    row['scenario_tags'] = tag
    row[column] = value
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    expected = ('multiple_prices requires' if tag == 'multiple_prices'
                else f'{column} requires')
    assert any(expected in error for error in errors)


@pytest.mark.parametrize(('field', 'scenario', 'candidate_field', 'candidates'), [
    ('area_sqm', 'multiple_areas', 'area_candidates_sqm', '12,34|1,235'),
    ('asking_price_wan', 'multiple_prices', 'price_candidates_wan', '1,234|12,34'),
])
def test_validator_rejects_malformed_grouped_numeric_candidates(
        tmp_path, field, scenario, candidate_field, candidates):
    manifest, rows = build_manifest(tmp_path)
    row = rows[0 if scenario == 'multiple_areas' else 3]
    row[field] = ''
    row['scenario_tags'] = scenario
    row[candidate_field] = candidates
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    expected = ('multiple_prices requires at least' if scenario == 'multiple_prices'
                else f'{candidate_field} requires')
    assert any(expected in error for error in errors)


@pytest.mark.parametrize(('scenario', 'candidate_field', 'candidates'), [
    ('multiple_areas', 'area_candidates_sqm', '1,234|1234.0'),
    ('multiple_prices', 'price_candidates_wan', '1,234|1234.0'),
])
def test_validator_detects_equivalent_grouped_numeric_candidates(
        tmp_path, scenario, candidate_field, candidates):
    manifest, rows = build_manifest(tmp_path)
    row = rows[0 if scenario == 'multiple_areas' else 3]
    row['scenario_tags'] = scenario
    row[candidate_field] = candidates
    if scenario == 'multiple_areas':
        row['area_sqm'] = ''
    else:
        row['asking_price_wan'] = ''
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    if scenario == 'multiple_areas':
        assert any('area_candidates_sqm requires at least two valid distinct candidates' in error
                   for error in errors)
    else:
        assert any('multiple_prices requires at least two distinct price_candidates_wan values' in error
                   for error in errors)


def test_text_ambiguous_candidates_normalize_canonical_unicode():
    assert _normalize_ambiguous_candidate('community_name', 'Cafe\u0301') == \
        _normalize_ambiguous_candidate('community_name', 'Café')


def test_validator_rejects_canonically_equivalent_text_candidates(tmp_path):
    manifest, rows = build_manifest(tmp_path)
    rows[0]['scenario_tags'] = 'multiple_communities'
    rows[0]['community_name'] = ''
    rows[0]['community_candidates'] = 'Cafe\u0301|Café'
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('community_candidates requires at least two valid distinct candidates' in error
               for error in errors)


@pytest.mark.parametrize(('candidate_column', 'tag', 'candidates'), [
    ('source_listing_id_candidates', 'source_id_conflict', '12345670|12345671'),
    ('community_candidates', 'multiple_communities', '东湖花园|锦港府'),
    ('invalid_bedroom_candidates', 'invalid_bedrooms', '21'),
    ('area_candidates_sqm', 'multiple_areas', '120|125'),
    ('floor_candidates', 'multiple_floors', '高楼层|低楼层'),
])
def test_ambiguous_candidate_values_require_the_matching_scenario_tag(
        tmp_path, candidate_column, tag, candidates):
    manifest, rows = build_manifest(tmp_path)
    rows[0][candidate_column] = candidates
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any(f'{candidate_column} requires scenario tag {tag}' in error
               for error in errors)


def test_source_id_conflict_candidates_must_include_source_url_id(tmp_path):
    manifest, rows = build_manifest(tmp_path)
    rows[0]['source_listing_id'] = ''
    rows[0]['scenario_tags'] = 'source_id_conflict'
    rows[0]['source_listing_id_candidates'] = '12345671|12345672'
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('source_listing_id_candidates must include the recognized URL ID' in error
               for error in errors)


def test_rejects_duplicate_manifest_columns(tmp_path):
    manifest, _ = build_manifest(tmp_path)
    lines = manifest.read_text(encoding='utf-8').splitlines()
    lines[0] = lines[0].replace('source,', 'source,source,', 1)
    manifest.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    errors, counts = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert errors == ['duplicate columns: source']
    assert counts == {'beike': 0, 'anjuke': 0}


def test_escapes_control_characters_in_duplicate_column_diagnostics(tmp_path):
    manifest = tmp_path / 'manifest.csv'
    manifest.write_text('bad\x1b[2J,bad\x1b[2J\n', encoding='utf-8')

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert errors == ['duplicate columns: bad\\u001b[2J']
    assert all(not any(ord(char) < 0x20 or 0x7f <= ord(char) <= 0x9f for char in error)
               for error in errors)


def test_escapes_control_characters_in_unsupported_column_diagnostics(tmp_path):
    manifest, _ = build_manifest(tmp_path)
    lines = manifest.read_text(encoding='utf-8').splitlines()
    lines[0] += ',contact\x1b[2J'
    manifest.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('unsupported columns: contact\\u001b[2J' in error for error in errors)
    assert all(not any(ord(char) < 0x20 or 0x7f <= ord(char) <= 0x9f for char in error)
               for error in errors)


def test_rejects_unsupported_manifest_columns(tmp_path):
    manifest, rows = build_manifest(tmp_path)
    columns = sorted(REQUIRED_COLUMNS | {'contact_phone'})
    for row in rows:
        row['contact_phone'] = '13900000000'
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert 'unsupported columns: contact_phone' in errors


def test_reports_non_utf8_manifest_without_traceback(tmp_path):
    manifest = tmp_path / 'manifest.csv'
    manifest.write_bytes(b'\xff,source\n')

    errors, counts = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert errors == ['manifest must be valid UTF-8']
    assert counts == {'beike': 0, 'anjuke': 0}


@pytest.mark.parametrize('sample_id', [
    'bad\x1b[2Jid', 'bad\r\nid', 'bad\u009bid', '\nbad-id', 'bad-id\r', '\tbad-id\t',
    '\u009bbad-id', 'bad-id\u009b',
])
def test_sample_id_control_characters_do_not_reach_diagnostics(tmp_path, sample_id):
    manifest, rows = build_manifest(tmp_path)
    rows[0]['sample_id'] = sample_id
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('sample_id must not contain control characters' in error for error in errors)
    assert all(not any(ord(char) < 0x20 or 0x7f <= ord(char) <= 0x9f for char in error)
               for error in errors)


def test_rejects_malformed_csv_quoting(tmp_path):
    manifest, _ = build_manifest(tmp_path)
    text = manifest.read_text(encoding='utf-8')
    assert ',小区,' in text
    manifest.write_text(text.replace(',小区,', ',"小区"ignored,', 1), encoding='utf-8')

    errors, counts = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert errors == ['manifest CSV is malformed']
    assert counts == {'beike': 0, 'anjuke': 0}


@pytest.mark.parametrize('row_width', ['extra', 'missing'])
def test_rejects_manifest_rows_with_wrong_field_count(tmp_path, row_width):
    manifest, rows = build_manifest(tmp_path)
    columns = sorted(REQUIRED_COLUMNS)
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(columns)
        values = [rows[0][column] for column in columns]
        writer.writerow(values + ['unexpected'] if row_width == 'extra' else values[:-1])
        for row in rows[1:]:
            writer.writerow([row[column] for column in columns])

    errors, counts = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('row has a different number of fields than the header' in error
               for error in errors)
    assert counts['beike'] == 4
    assert counts['anjuke'] == 5


@pytest.mark.parametrize('control', ['\n', '\x00', '\x85'])
def test_rejects_control_characters_in_html_path(tmp_path, control):
    manifest, rows = build_manifest(tmp_path)
    rows[0]['html_path'] += control
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('html_path must not contain control characters' in error for error in errors)


def test_rejects_blank_manual_label_without_scenario_tag(tmp_path):
    manifest, rows = build_manifest(tmp_path)
    rows[0]['district'] = ''
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('blank manual labels must have a matching scenario tag' in error
               for error in errors)


def test_rejects_hash_mismatch_and_query_data_in_source_url(tmp_path):
    manifest, rows = build_manifest(tmp_path)
    rows[0]['source_url'] += '?tracking=private'
    rows[0]['sha256'] = '0' * 64
    rows[1]['source_url'] = rows[1]['source_url'].replace('nb.ke.com', 'sh.ke.com')
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('sha256 does not match' in error for error in errors)
    assert any('query and fragment' in error for error in errors)


@pytest.mark.parametrize('source,url', [
    ('beike', 'https://sh.ke.com/ershoufang/12345670.html'),
    ('anjuke', 'https://hangzhou.anjuke.com/sale/12345670'),
])
def test_rejects_non_ningbo_source_hosts(tmp_path, source, url):
    manifest, rows = build_manifest(tmp_path)
    row = next(row for row in rows if row['source'] == source and row['sample_id'].endswith('-0'))
    row['source_url'] = url
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('HTTPS Ningbo host' in error for error in errors)


def test_sample_manifest_accepts_one_dns_root_dot(tmp_path):
    manifest, rows = build_manifest(tmp_path)
    row = next(row for row in rows if row['source'] == 'beike' and row['sample_id'].endswith('-0'))
    row['source_url'] = row['source_url'].replace('nb.ke.com/', 'nb.ke.com./', 1)
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert errors == []


def test_rejects_whitespace_in_source_url(tmp_path):
    manifest, rows = build_manifest(tmp_path)
    rows[0]['source_url'] += '\n'
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('whitespace or control characters' in error for error in errors)


def test_rejects_sample_files_with_unsupported_extension(tmp_path):
    manifest, rows = build_manifest(tmp_path)
    original = tmp_path / rows[0]['html_path']
    unsupported = original.with_suffix('.txt')
    original.rename(unsupported)
    rows[0]['html_path'] = unsupported.relative_to(tmp_path).as_posix()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('html_path must end with .html or .html.gz' in error for error in errors)


def test_rejects_invalid_numeric_labels_and_duplicate_price_candidates(tmp_path):
    manifest, rows = build_manifest(tmp_path)
    rows[0]['area_sqm'] = 'Infinity'
    rows[1]['bedrooms'] = '2.5'
    rows[3]['price_candidates_wan'] = '360|360.0'
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('area_sqm must be a finite number' in error for error in errors)
    assert any('bedrooms must be an integer' in error for error in errors)
    assert any('multiple_prices requires at least two distinct' in error for error in errors)


def test_rejects_source_listing_id_longer_than_model_limit(tmp_path):
    manifest, rows = build_manifest(tmp_path)
    listing_id = '1' * 221
    rows[0]['source_listing_id'] = listing_id
    rows[0]['source_url'] = f'https://nb.ke.com/ershoufang/{listing_id}.html'
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('source_listing_id must not exceed 220 characters' in error for error in errors)


def test_source_url_id_over_model_limit_can_be_labeled_unknown(tmp_path):
    manifest, rows = build_manifest(tmp_path)
    listing_id = '1' * 221
    for row in rows:
        if row['scenario_tags'] == 'unknown_id|missing_fields':
            host = 'nb.ke.com' if row['source'] == 'beike' else 'ningbo.anjuke.com'
            path = 'ershoufang' if row['source'] == 'beike' else 'sale'
            suffix = '.html' if row['source'] == 'beike' else ''
            row['source_url'] = f'https://{host}/{path}/{listing_id}{suffix}'
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert errors == []


def test_rejects_source_url_longer_than_api_limit(tmp_path):
    manifest, rows = build_manifest(tmp_path)
    rows[0]['source_url'] = 'https://nb.ke.com/' + 'a' * 2000
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('source_url must be between 12 and 2000 characters' in error
               for error in errors)


def test_rejects_review_timestamp_before_capture_timestamp(tmp_path):
    manifest, rows = build_manifest(tmp_path)
    rows[0]['reviewed_at'] = '2026-11-10T01:00:00Z'
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('reviewed_at must not be earlier than captured_at' in error for error in errors)


def test_rejects_same_html_compressed_with_different_gzip_headers(tmp_path):
    manifest, rows = build_manifest(tmp_path)
    original = tmp_path / rows[0]['html_path']
    duplicate = tmp_path / 'data/raw-pages/beike-duplicate.html.gz'
    duplicate.write_bytes(gzip.compress(original.read_bytes(), mtime=1))
    rows[1]['html_path'] = 'data/raw-pages/beike-duplicate.html.gz'
    rows[1]['sha256'] = hashlib.sha256(duplicate.read_bytes()).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('duplicate HTML content across the sample set' in error for error in errors)


def test_rejects_corrupt_gzip_html_sample(tmp_path):
    manifest, rows = build_manifest(tmp_path)
    compressed = tmp_path / 'data/raw-pages/beike-corrupt.html.gz'
    compressed.write_bytes(b'not a gzip stream')
    rows[0]['html_path'] = 'data/raw-pages/beike-corrupt.html.gz'
    rows[0]['sha256'] = hashlib.sha256(compressed.read_bytes()).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('gzip sample cannot be decompressed' in error for error in errors)


@pytest.mark.parametrize('compressed', [False, True])
def test_rejects_non_utf8_html_sample(tmp_path, compressed):
    manifest, rows = build_manifest(tmp_path)
    raw = b'<html><body>\xffinvalid</body></html>'
    stored = gzip.compress(raw) if compressed else raw
    relative = Path('data/raw-pages/beike-invalid-encoding.html')
    if compressed:
        relative = relative.with_suffix(relative.suffix + '.gz')
    path = tmp_path / relative
    path.write_bytes(stored)
    rows[0]['html_path'] = relative.as_posix()
    rows[0]['sha256'] = hashlib.sha256(stored).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('HTML sample must be valid UTF-8' in error for error in errors)


@pytest.mark.parametrize('compressed', [False, True])
def test_rejects_html_sample_with_nul_character(tmp_path, compressed):
    manifest, rows = build_manifest(tmp_path)
    raw = b'<html><body>page\x00content</body></html>'
    stored = gzip.compress(raw) if compressed else raw
    relative = Path('data/raw-pages/beike-nul.html')
    if compressed:
        relative = relative.with_suffix(relative.suffix + '.gz')
    (tmp_path / relative).write_bytes(stored)
    rows[0]['html_path'] = relative.as_posix()
    rows[0]['sha256'] = hashlib.sha256(stored).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('HTML sample must not contain a NUL character' in error for error in errors)


@pytest.mark.parametrize('compressed', [False, True])
def test_rejects_html_exceeding_uncompressed_size_limit(tmp_path, compressed):
    manifest, rows = build_manifest(tmp_path)
    html = b'x' * 1_000_001
    relative = Path('data/raw-pages/beike-oversized.html.gz' if compressed
                    else 'data/raw-pages/beike-oversized.html')
    sample = gzip.compress(html) if compressed else html
    sample_path = tmp_path / relative
    sample_path.write_bytes(sample)
    rows[0]['html_path'] = relative.as_posix()
    rows[0]['sha256'] = hashlib.sha256(sample).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('HTML sample exceeds 1000000 byte limit' in error for error in errors)


def test_rejects_sample_file_symlink(tmp_path):
    manifest, rows = build_manifest(tmp_path)
    raw_root = tmp_path / 'data/raw-pages'
    target = raw_root / 'unlisted-sample.html'
    content = b'<html>separate local sample</html>'
    target.write_bytes(content)
    link = raw_root / 'linked-sample.html'
    link.symlink_to(target)
    rows[0]['html_path'] = link.relative_to(tmp_path).as_posix()
    rows[0]['sha256'] = hashlib.sha256(content).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('symlinks are not allowed' in error for error in errors)


def test_rejects_symlinked_raw_pages_root(tmp_path):
    manifest, rows = build_manifest(tmp_path)
    data_dir = tmp_path / 'data'
    raw_root = data_dir / 'raw-pages'
    external_root = tmp_path / 'redirected-pages'
    raw_root.rename(external_root)
    raw_root.symlink_to(external_root, target_is_directory=True)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('symlinks are not allowed' in error for error in errors)


def test_documented_cli_entrypoint_loads_project_package():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, str(root / 'scripts/validate_sample_set.py'), '--help'],
        cwd=root, capture_output=True, text=True, check=False,
    )

    assert result.returncode == 0
    assert '--minimum-per-source' in result.stdout


def test_title_annotation_is_limited_to_parser_output_size(tmp_path):
    manifest, rows = build_manifest(tmp_path)
    rows[0]['title'] = '标题' * 251
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('title must be at most 500 characters' in error for error in errors)


def test_title_is_a_required_manual_label_unless_marked_missing(tmp_path):
    manifest, rows = build_manifest(tmp_path)
    rows[0]['title'] = ''
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    errors, _ = validate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert any('blank manual labels must have a matching scenario tag' in error for error in errors)
