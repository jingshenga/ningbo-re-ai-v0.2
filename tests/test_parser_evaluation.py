import csv
import gzip
import hashlib
import io
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from scripts import evaluate_parser as evaluator_module
from scripts.evaluate_parser import evaluate_manifest
from scripts.validate_sample_set import AMBIGUOUS_FIELD_CANDIDATE_COLUMNS, REQUIRED_COLUMNS


def test_price_context_scenarios_have_stable_report_order():
    assert evaluator_module.SCENARIOS.index('oral_prices') < (
        evaluator_module.SCENARIOS.index('transaction_prices'))


def build_eval_manifest(root: Path, samples_per_source=5):
    raw_root = root / 'data/raw-pages'
    raw_root.mkdir(parents=True)
    manifest = root / 'manifest.csv'
    rows = []
    for source, host in (('beike', 'nb.ke.com'), ('anjuke', 'ningbo.anjuke.com')):
        for index in range(samples_per_source):
            listing_id = f'1099000000{index:02d}' if source == 'beike' else f'123456700{index:02d}'
            url = (f'https://{host}/ershoufang/{listing_id}.html' if source == 'beike'
                   else f'https://{host}/sale/{listing_id}')
            status, tags = 'active', ''
            community, district, area, bedrooms, price, candidates = '东湖花园', '鄞州', '120', '3', '400', ''
            text = ['小区：东湖花园', '所在区域：鄞州', '建筑面积：120㎡', '户型：3室',
                    '楼层：高楼层', '装修：精装', '总价：400万']
            if index == 1:
                status = 'withdrawn'
            elif index == 2:
                tags, area = 'missing_fields', ''
                text = [part for part in text if not part.startswith(('建筑面积：', '总价：'))]
                text.append('总价：400万')
            elif index == 3:
                tags, price, candidates = 'multiple_prices', '', '360|370'
                text = [part for part in text if not part.startswith('总价：')]
                text.extend(('总价：360万', '总价：370万'))
            elif index == 4:
                status, tags = 'unknown', 'unknown_id|missing_fields'
                url = f'https://{host}/ershoufang/' if source == 'beike' else f'https://{host}/sale/'
                listing_id = ''

            html = (f'<html><body><h1>虚构样本 {source} {index}</h1><main>'
                    + ' '.join(text) + '</main></body></html>').encode('utf-8')
            relative = Path('data/raw-pages') / f'{source}-{index}.html'
            (root / relative).write_bytes(html)
            rows.append({
                'sample_id': f'{source}-{index}', 'source': source,
                'html_path': relative.as_posix(), 'sha256': hashlib.sha256(html).hexdigest(),
                'source_url': url, 'captured_at': '2026-11-10T10:00:00+08:00',
                'permission_reference': 'synthetic-test-only',
                'permission_scope': 'synthetic test fixture only',
                'source_status': status, 'scenario_tags': tags,
                'source_listing_id': listing_id,
                'title': f'虚构样本 {source} {index}', 'community_name': community,
                'district': district, 'area_sqm': area, 'bedrooms': bedrooms,
                'floor_text': '高楼层', 'decoration': '精装',
                'asking_price_wan': price, 'price_candidates_wan': candidates,
                'source_listing_id_candidates': '', 'community_candidates': '',
                'area_candidates_sqm': '',
                'bedroom_candidates': '', 'district_candidates': '',
                'invalid_bedroom_candidates': '',
                'floor_candidates': '', 'decoration_candidates': '',
                'reviewed_by': 'synthetic-test', 'reviewed_at': '2026-11-10T11:00:00+08:00',
            })
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)
    return manifest, rows


def test_evaluator_reports_accuracy_coverage_and_scenario_safety(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path)
    original = tmp_path / rows[0]['html_path']
    compressed = original.with_suffix(original.suffix + '.gz')
    compressed.write_bytes(gzip.compress(original.read_bytes()))
    original.unlink()
    rows[0]['html_path'] += '.gz'
    rows[0]['sha256'] = hashlib.sha256(compressed.read_bytes()).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert report['parser_version'] == evaluator_module.PARSER_VERSION
    assert report['sample_requirements']['beike'] == {
        'required': 20, 'observed': 5, 'met': False,
    }
    assert report['sample_requirements']['anjuke'] == {
        'required': 20, 'observed': 5, 'met': False,
    }
    assert report['sample_composition']['beike']['statuses'] == {
        'active': 3, 'sold': 0, 'unknown': 1, 'withdrawn': 1,
    }
    assert report['sample_composition']['beike']['scenarios']['missing_fields'] == 2
    assert report['sample_composition']['beike']['scenarios']['multiple_prices'] == 1
    assert report['sample_composition']['beike']['scenarios']['unknown_id'] == 1
    beike_area = report['fields']['beike']['area_sqm']
    assert beike_area['labeled'] == 5
    assert beike_area['correct'] == 5
    assert beike_area['accuracy_pct'] == 100.0
    assert beike_area['coverage_pct'] == 80.0
    assert beike_area['precision_pct'] == 100.0
    assert beike_area['precision_target_pct'] == 95.0
    assert beike_area['precision_target_met'] is True
    assert report['fields']['beike']['floor_text']['correct'] == 5
    assert report['fields']['beike']['decoration']['correct'] == 5
    assert report['fields']['anjuke']['source_listing_id']['coverage_pct'] == 80.0
    assert report['scenarios']['beike']['multiple_prices']['pass_rate_pct'] == 100.0
    assert report['scenarios']['anjuke']['unknown_id']['pass_rate_pct'] == 100.0
    assert 'do not establish legal authorization' in report['authorization_notice']
    assert report['manifest_sha256'] == hashlib.sha256(manifest.read_bytes()).hexdigest()


@pytest.mark.parametrize('source', ['beike', 'anjuke'])
@pytest.mark.parametrize('scenario', ['oral_prices', 'transaction_prices'])
def test_evaluator_reports_null_rate_for_scenarios_without_samples(tmp_path, source, scenario):
    manifest, _ = build_eval_manifest(tmp_path)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert report['scenarios'][source][scenario] == {
        'samples': 0, 'passed': 0, 'pass_rate_pct': None,
    }


@pytest.mark.parametrize('price_label', ['挂牌总价', '挂牌价', '出售总价'])
def test_evaluator_scores_supported_listing_price_label_aliases(tmp_path, price_label):
    manifest, rows = build_eval_manifest(tmp_path)
    html_path = tmp_path / rows[0]['html_path']
    html = html_path.read_text(encoding='utf-8').replace('总价：400万', f'{price_label}：400万')
    html_path.write_text(html, encoding='utf-8')
    rows[0]['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    metric = report['fields']['beike']['asking_price_wan']
    assert metric['accuracy_pct'] == 100.0
    assert metric['precision_pct'] == 100.0


@pytest.mark.parametrize('qualified_label', [
    '口播:挂牌总价', '交易总价', '合同总价', '签约总价',
])
@pytest.mark.parametrize('source', ['beike', 'anjuke'])
def test_evaluator_keeps_qualified_price_out_of_listing_price(tmp_path, qualified_label, source):
    manifest, rows = build_eval_manifest(tmp_path)
    row = next(row for row in rows if row['source'] == source)
    row['asking_price_wan'] = ''
    row['scenario_tags'] = 'missing_fields'
    html_path = tmp_path / row['html_path']
    html = html_path.read_text(encoding='utf-8').replace('总价：400万', f'{qualified_label}：400万')
    html_path.write_text(html, encoding='utf-8')
    row['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    metric = report['fields'][source]['asking_price_wan']
    assert metric['correct'] == metric['labeled']
    assert report['scenarios'][source]['missing_fields']['pass_rate_pct'] == 100.0


@pytest.mark.parametrize('source', ['beike', 'anjuke'])
def test_evaluator_counts_unit_price_as_missing_total_price(tmp_path, source):
    manifest, rows = build_eval_manifest(tmp_path)
    row = next(row for row in rows if row['source'] == source)
    row['asking_price_wan'] = ''
    row['scenario_tags'] = 'missing_fields'
    html_path = tmp_path / row['html_path']
    html = html_path.read_text(encoding='utf-8').replace(
        '总价：400万', '挂牌价：2万／㎡')
    html_path.write_text(html, encoding='utf-8')
    row['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    metric = report['fields'][source]['asking_price_wan']
    assert metric['correct'] == metric['labeled']
    assert metric['precision_pct'] == 100.0
    assert report['scenarios'][source]['missing_fields']['pass_rate_pct'] == 100.0


@pytest.mark.parametrize('source', ['beike', 'anjuke'])
@pytest.mark.parametrize(('qualifier', 'before_amount'), [
    ('约', False), ('大约', False), ('大概', False), ('左右', False),
    ('上下', False), ('出头', False), ('以上', False), ('以下', False),
    ('以内', False), ('附近', False), ('不到', False), ('不足', False),
    ('不超过', False), ('不高于', False), ('不低于', False), ('起', False),
    ('起价', False), ('起售', False), ('起售房源', False), ('起步', False),
    ('起步价', False), ('起始价', False), ('封顶', False), ('+', False),
    ('＋', False),
    ('约', True), ('大约', True), ('大概', True), ('参考', True),
    ('估算', True), ('预估', True), ('约为', True), ('在', True),
    ('左右', True), ('上下', True),
    ('出头', True), ('以上', True), ('以下', True), ('以内', True),
    ('不到', True), ('不足', True), ('不超过', True), ('不高于', True),
    ('不低于', True), ('至少', True), ('至多', True), ('最低', True),
    ('最高', True), ('起步价', True), ('起始价', True),
])
def test_evaluator_counts_approximate_price_as_missing_exact_total(
        tmp_path, source, qualifier, before_amount):
    manifest, rows = build_eval_manifest(tmp_path)
    row = next(row for row in rows if row['source'] == source)
    row['asking_price_wan'] = ''
    row['scenario_tags'] = 'missing_fields'
    html_path = tmp_path / row['html_path']
    price = f'{qualifier}200万' if before_amount else f'200万{qualifier}'
    html = html_path.read_text(encoding='utf-8').replace(
        '总价：400万', f'挂牌价：{price}')
    html_path.write_text(html, encoding='utf-8')
    row['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    metric = report['fields'][source]['asking_price_wan']
    assert metric['correct'] == metric['labeled']
    assert metric['precision_pct'] == 100.0
    assert report['scenarios'][source]['missing_fields']['pass_rate_pct'] == 100.0


@pytest.mark.parametrize('source', ['beike', 'anjuke'])
@pytest.mark.parametrize('qualified_price', [
    '挂牌价：约200万', '总价：不超过200万', '挂牌价：200万左右',
    '挂牌价：≥200万', '总价：≤200万',
])
def test_evaluator_requires_warning_and_evidence_for_non_exact_price(
        tmp_path, source, qualified_price):
    manifest, rows = build_eval_manifest(tmp_path)
    row = next(row for row in rows if row['source'] == source)
    row['asking_price_wan'] = ''
    row['scenario_tags'] = 'non_exact_prices'
    row['price_candidates_wan'] = '200'
    html_path = tmp_path / row['html_path']
    html = html_path.read_text(encoding='utf-8').replace('总价：400万', qualified_price)
    html_path.write_text(html, encoding='utf-8')
    row['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    metric = report['fields'][source]['asking_price_wan']
    scenario = report['scenarios'][source]['non_exact_prices']
    assert metric['correct'] == metric['labeled']
    assert scenario['samples'] == 1
    assert scenario['passed'] == 1
    assert scenario['pass_rate_pct'] == 100.0
    parsed = evaluator_module.parse_listing_html(source, row['source_url'], html)
    assert parsed.fields['field_evidence']['asking_price_wan']['mentions'][0][
        'quote'] == qualified_price


def test_evaluator_rejects_non_exact_price_evidence_quote_missing_qualifier(
        tmp_path, monkeypatch):
    manifest, rows = build_eval_manifest(tmp_path)
    row = next(row for row in rows if row['source'] == 'beike')
    row['asking_price_wan'] = ''
    row['scenario_tags'] = 'non_exact_prices'
    row['price_candidates_wan'] = '200'
    html_path = tmp_path / row['html_path']
    html = html_path.read_text(encoding='utf-8').replace('总价：400万', '挂牌价：200万左右')
    html_path.write_text(html, encoding='utf-8')
    row['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    parse = evaluator_module.parse_listing_html

    def truncated_quote_parser(*args, **kwargs):
        result = parse(*args, **kwargs)
        result.fields['field_evidence']['asking_price_wan']['mentions'][0][
            'quote'] = '挂牌价：200万'
        return result

    monkeypatch.setattr(evaluator_module, 'parse_listing_html', truncated_quote_parser)
    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    scenario = report['scenarios']['beike']['non_exact_prices']
    assert scenario['samples'] == 1
    assert scenario['passed'] == 0
    assert scenario['pass_rate_pct'] == 0.0


def test_evaluator_rejects_non_exact_area_evidence_quote_missing_qualifier(
        tmp_path, monkeypatch):
    manifest, rows = build_eval_manifest(tmp_path)
    row = next(row for row in rows if row['source'] == 'beike')
    row['area_sqm'] = ''
    row['scenario_tags'] = 'non_exact_areas'
    row['area_candidates_sqm'] = '100'
    html_path = tmp_path / row['html_path']
    html = html_path.read_text(encoding='utf-8').replace('建筑面积：120㎡', '建筑面积：100㎡左右')
    html_path.write_text(html, encoding='utf-8')
    row['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    parse = evaluator_module.parse_listing_html

    def truncated_quote_parser(*args, **kwargs):
        result = parse(*args, **kwargs)
        mentions = result.fields['field_evidence'].get('area_sqm', {}).get('mentions', [])
        for mention in mentions:
            if mention.get('is_non_exact') is True:
                mention['quote'] = '建筑面积：100㎡'
        return result

    monkeypatch.setattr(evaluator_module, 'parse_listing_html', truncated_quote_parser)
    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    scenario = report['scenarios']['beike']['non_exact_areas']
    assert scenario['samples'] == 1
    assert scenario['passed'] == 0
    assert scenario['pass_rate_pct'] == 0.0


@pytest.mark.parametrize('source', ['beike', 'anjuke'])
@pytest.mark.parametrize('area_text', [
    '建筑面积：100㎡左右', '建筑面积：100㎡起', '建筑面积：大于100㎡',
    '建筑面积：100㎡封顶', '建筑面积：100㎡起步', '建筑面积：在100㎡左右',
    '建筑面积：参考100㎡', '建筑面积：估算100㎡', '建筑面积：估计100㎡',
    '建筑面积：预估100㎡', '建筑面积：100㎡参考', '建筑面积：100㎡估算',
    '建筑面积：100㎡估计', '建筑面积：100㎡预估', '约建筑面积：100㎡',
    '估算建面：100㎡', '参考建筑面积：100㎡', '建筑面积：100㎡+',
    '建筑面积：≥100㎡', '建筑面积：&lt;=100㎡',
])
def test_evaluator_requires_warning_and_complete_evidence_for_non_exact_area(
        tmp_path, source, area_text):
    manifest, rows = build_eval_manifest(tmp_path)
    row = next(row for row in rows if row['source'] == source)
    row['area_sqm'] = ''
    row['scenario_tags'] = 'non_exact_areas'
    row['area_candidates_sqm'] = '100'
    html_path = tmp_path / row['html_path']
    html = html_path.read_text(encoding='utf-8').replace('建筑面积：120㎡', area_text)
    html_path.write_text(html, encoding='utf-8')
    row['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    metric = report['fields'][source]['area_sqm']
    scenario = report['scenarios'][source]['non_exact_areas']
    assert metric['correct'] == metric['labeled']
    assert scenario['samples'] == 1
    assert scenario['passed'] == 1
    assert scenario['pass_rate_pct'] == 100.0


def test_evaluator_fails_non_exact_area_scenario_without_qualifier_warning(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path)
    row = next(row for row in rows if row['source'] == 'beike')
    row['area_sqm'] = ''
    row['scenario_tags'] = 'non_exact_areas'
    row['area_candidates_sqm'] = '120'
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    scenario = report['scenarios']['beike']['non_exact_areas']
    assert scenario['samples'] == 1
    assert scenario['passed'] == 0
    assert scenario['pass_rate_pct'] == 0.0


def test_evaluator_fails_non_exact_area_scenario_when_evidence_is_truncated(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path)
    row = next(row for row in rows if row['source'] == 'beike')
    row['area_sqm'] = ''
    row['scenario_tags'] = 'non_exact_areas'
    row['area_candidates_sqm'] = '100'
    html_path = tmp_path / row['html_path']
    html = html_path.read_text(encoding='utf-8').replace(
        '建筑面积：120㎡', ' '.join(['建筑面积：100㎡左右'] * 21))
    html_path.write_text(html, encoding='utf-8')
    row['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    scenario = report['scenarios']['beike']['non_exact_areas']
    assert scenario['samples'] == 1
    assert scenario['passed'] == 0
    assert scenario['pass_rate_pct'] == 0.0


@pytest.mark.parametrize('scenario', ['non_exact_areas', 'non_exact_prices'])
def test_evaluator_rejects_non_exact_candidate_ready_for_review(
        tmp_path, monkeypatch, scenario):
    manifest, rows = build_eval_manifest(tmp_path)
    row = next(row for row in rows if row['source'] == 'beike')
    html_path = tmp_path / row['html_path']
    html = html_path.read_text(encoding='utf-8')
    if scenario == 'non_exact_areas':
        row['area_sqm'] = ''
        row['area_candidates_sqm'] = '100'
        html = html.replace('建筑面积：120㎡', '建筑面积：100㎡左右')
    else:
        row['asking_price_wan'] = ''
        row['price_candidates_wan'] = '200'
        html = html.replace('总价：400万', '总价：200万左右')
    row['scenario_tags'] = scenario
    html_path.write_text(html, encoding='utf-8')
    row['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    parse = evaluator_module.parse_listing_html

    def parse_as_ready(*args, **kwargs):
        result = parse(*args, **kwargs)
        return SimpleNamespace(fields=result.fields, warnings=result.warnings,
                               ready_for_review=True)

    monkeypatch.setattr(evaluator_module, 'parse_listing_html', parse_as_ready)
    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert report['scenarios']['beike'][scenario]['passed'] == 0


@pytest.mark.parametrize(('scenario', 'field', 'original', 'replacement', 'candidates'), [
    ('source_id_conflict', 'source_listing_id', '<html><body>',
     '<html><head><link rel="canonical" '
     'href="https://nb.ke.com/ershoufang/999999999999.html"></head><body>',
     '109900000000|999999999999'),
    ('multiple_communities', 'community_name', '小区：东湖花园',
     '小区：东湖花园 小区：锦港府', '东湖花园|锦港府'),
    ('multiple_areas', 'area_sqm', '建筑面积：120㎡',
     '建筑面积：120㎡ 建面：110㎡', '120|110'),
    ('area_ranges', 'area_sqm', '建筑面积：120㎡',
     '建筑面积：120㎡-130㎡', '120㎡-130㎡'),
    ('price_ranges', 'asking_price_wan', '总价：400万',
     '总价：300万-320万', '300万-320万'),
])
def test_evaluator_rejects_core_field_conflict_ready_for_review(
        tmp_path, monkeypatch, scenario, field, original, replacement, candidates):
    manifest, rows = build_eval_manifest(tmp_path)
    row = next(row for row in rows if row['source'] == 'beike')
    row[field] = ''
    row['scenario_tags'] = scenario
    column = AMBIGUOUS_FIELD_CANDIDATE_COLUMNS[scenario]
    row[column] = candidates
    html_path = tmp_path / row['html_path']
    html = html_path.read_text(encoding='utf-8').replace(original, replacement)
    html_path.write_text(html, encoding='utf-8')
    row['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    parse = evaluator_module.parse_listing_html

    def parse_as_ready(*args, **kwargs):
        result = parse(*args, **kwargs)
        return SimpleNamespace(fields=result.fields, warnings=result.warnings,
                               ready_for_review=True)

    monkeypatch.setattr(evaluator_module, 'parse_listing_html', parse_as_ready)
    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert report['scenarios']['beike'][scenario]['passed'] == 0


@pytest.mark.parametrize('scenario', [
    'multiple_prices', 'unknown_id', 'missing_fields', 'oral_prices',
])
def test_evaluator_rejects_required_field_missing_ready_for_review(
        tmp_path, monkeypatch, scenario):
    manifest, rows = build_eval_manifest(tmp_path)
    row = next(row for row in rows if row['source'] == 'beike')
    html_path = tmp_path / row['html_path']
    html = html_path.read_text(encoding='utf-8')
    if scenario == 'multiple_prices':
        row['asking_price_wan'] = ''
        row['price_candidates_wan'] = '360|370'
        html = html.replace('总价：400万', '总价：360万 总价：370万')
    elif scenario == 'oral_prices':
        row['asking_price_wan'] = ''
        html = html.replace('总价：400万', '口播总价：300万')
    elif scenario == 'unknown_id':
        row['source_listing_id'] = ''
        row['source_url'] = 'https://nb.ke.com/ershoufang/'
    else:
        row['area_sqm'] = ''
        html = html.replace('建筑面积：120㎡', '')
    row['scenario_tags'] = scenario
    html_path.write_text(html, encoding='utf-8')
    row['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    parse = evaluator_module.parse_listing_html

    def parse_as_ready(*args, **kwargs):
        result = parse(*args, **kwargs)
        return SimpleNamespace(fields=result.fields, warnings=result.warnings,
                               ready_for_review=True)

    monkeypatch.setattr(evaluator_module, 'parse_listing_html', parse_as_ready)
    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert report['scenarios']['beike'][scenario]['passed'] == 0


def test_evaluator_fails_non_exact_price_scenario_without_qualifier_warning(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path)
    row = next(row for row in rows if row['source'] == 'beike')
    row['asking_price_wan'] = ''
    row['scenario_tags'] = 'non_exact_prices'
    row['price_candidates_wan'] = '200'
    html_path = tmp_path / row['html_path']
    html = html_path.read_text(encoding='utf-8').replace(
        '总价：400万', '挂牌价：200万')
    html_path.write_text(html, encoding='utf-8')
    row['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    scenario = report['scenarios']['beike']['non_exact_prices']
    assert scenario['samples'] == 1
    assert scenario['passed'] == 0
    assert scenario['pass_rate_pct'] == 0.0


def test_evaluator_fails_non_exact_price_scenario_when_evidence_is_truncated(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path)
    row = next(row for row in rows if row['source'] == 'beike')
    row['asking_price_wan'] = ''
    row['scenario_tags'] = 'non_exact_prices'
    row['price_candidates_wan'] = '200'
    html_path = tmp_path / row['html_path']
    html = html_path.read_text(encoding='utf-8').replace(
        '总价：400万', ' '.join(['挂牌价约200万'] * 21))
    html_path.write_text(html, encoding='utf-8')
    row['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    parsed = evaluator_module.parse_listing_html('beike', row['source_url'], html)
    assert 'non_exact_asking_price' in parsed.warnings
    assert parsed.fields['field_evidence']['asking_price_wan']['mentions_truncated'] is True

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    scenario = report['scenarios']['beike']['non_exact_prices']
    assert scenario['samples'] == 1
    assert scenario['passed'] == 0
    assert scenario['pass_rate_pct'] == 0.0


def test_evaluator_rejects_exact_price_inside_non_exact_price_evidence(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path)
    row = next(row for row in rows if row['source'] == 'beike')
    row['asking_price_wan'] = ''
    row['scenario_tags'] = 'non_exact_prices'
    row['price_candidates_wan'] = '200'
    html_path = tmp_path / row['html_path']
    html = html_path.read_text(encoding='utf-8').replace(
        '总价：400万', '挂牌价约200万 总价200万')
    html_path.write_text(html, encoding='utf-8')
    row['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    parsed = evaluator_module.parse_listing_html('beike', row['source_url'], html)
    assert parsed.fields['asking_price_wan'] is None
    assert 'non_exact_asking_price' in parsed.warnings
    mentions = parsed.fields['field_evidence']['asking_price_wan']['mentions']
    assert [mention['is_non_exact'] for mention in mentions] == [True, False]

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    scenario = report['scenarios']['beike']['non_exact_prices']
    assert scenario['samples'] == 1
    assert scenario['passed'] == 0
    assert scenario['pass_rate_pct'] == 0.0


@pytest.mark.parametrize('source', ['beike', 'anjuke'])
def test_evaluator_keeps_exact_price_before_folded_start_summary(tmp_path, source):
    manifest, rows = build_eval_manifest(tmp_path)
    row = next(row for row in rows if row['source'] == source)
    html_path = tmp_path / row['html_path']
    html = html_path.read_text(encoding='utf-8').replace(
        '总价：400万</main>',
        '总价：400万<details><summary>起始摘要</summary>'
        '<p>折叠内容</p></details></main>')
    html_path.write_text(html, encoding='utf-8')
    row['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    metric = report['fields'][source]['asking_price_wan']
    assert metric['correct'] == metric['labeled']
    assert metric['precision_pct'] == 100.0


@pytest.mark.parametrize(('scenario', 'qualified_label'), [
    ('oral_prices', '口播总价'),
    ('oral_prices', '口播的总价'),
    ('oral_prices', '口播 的 总价'),
    ('transaction_prices', '交易总价'),
    ('transaction_prices', '合同中的挂牌价'),
    ('transaction_prices', '合同 中 的 挂牌价'),
    ('transaction_prices', '交易中的总价'),
    ('transaction_prices', '交易 中 的 总价'),
    ('transaction_prices', '签约里的出售总价'),
    ('transaction_prices', '签约 里的 出售总价'),
    ('transaction_prices', '合同总价'),
    ('transaction_prices', '签约总价'),
])
@pytest.mark.parametrize('source', ['beike', 'anjuke'])
def test_evaluator_reports_non_listing_price_scenarios(
        tmp_path, scenario, qualified_label, source):
    manifest, rows = build_eval_manifest(tmp_path)
    row = next(row for row in rows if row['source'] == source)
    row['asking_price_wan'] = ''
    row['scenario_tags'] = scenario
    html_path = tmp_path / row['html_path']
    html = html_path.read_text(encoding='utf-8').replace(
        '总价：400万', f'{qualified_label}：300万')
    html_path.write_text(html, encoding='utf-8')
    row['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    result = report['scenarios'][source][scenario]
    assert result['samples'] == 1
    assert result['passed'] == 1
    assert result['pass_rate_pct'] == 100.0


@pytest.mark.parametrize(('scenario', 'qualified_label'), [
    ('oral_prices', '口播 的 总价'),
    ('transaction_prices', '合同 中 的 挂牌价'),
    ('transaction_prices', '交易 中 的 总价'),
    ('transaction_prices', '签约 里的 出售总价'),
])
@pytest.mark.parametrize('source', ['beike', 'anjuke'])
def test_evaluator_excludes_linked_non_listing_price_ranges(
        tmp_path, scenario, qualified_label, source):
    manifest, rows = build_eval_manifest(tmp_path)
    row = next(row for row in rows if row['source'] == source)
    row['asking_price_wan'] = ''
    row['scenario_tags'] = scenario
    html_path = tmp_path / row['html_path']
    html = html_path.read_text(encoding='utf-8').replace(
        '总价：400万', f'{qualified_label}：300万-320万')
    html_path.write_text(html, encoding='utf-8')
    row['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    result = report['scenarios'][source][scenario]
    assert result['samples'] == 1
    assert result['passed'] == 1
    assert result['pass_rate_pct'] == 100.0


@pytest.mark.parametrize(('scenario', 'qualified_label'), [
    ('oral_prices', '口播总价'),
    ('transaction_prices', '合同总价'),
])
@pytest.mark.parametrize('source', ['beike', 'anjuke'])
def test_evaluator_keeps_explicit_listing_price_in_non_listing_price_scenario(
        tmp_path, scenario, qualified_label, source):
    manifest, rows = build_eval_manifest(tmp_path)
    row = next(row for row in rows if row['source'] == source)
    row['scenario_tags'] = scenario
    html_path = tmp_path / row['html_path']
    html = html_path.read_text(encoding='utf-8').replace(
        '总价：400万', f'总价：400万 {qualified_label}：300万')
    html_path.write_text(html, encoding='utf-8')
    row['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    result = report['scenarios'][source][scenario]
    assert result['samples'] == 1
    assert result['passed'] == 1
    assert result['pass_rate_pct'] == 100.0


@pytest.mark.parametrize(('scenario', 'qualified_label'), [
    ('oral_prices', '口播总价'),
    ('transaction_prices', '合同总价'),
])
def test_price_context_scenario_fails_if_non_listing_price_is_promoted(
        tmp_path, monkeypatch, scenario, qualified_label):
    manifest, rows = build_eval_manifest(tmp_path)
    row = rows[0]
    row['asking_price_wan'] = ''
    row['scenario_tags'] = scenario
    html_path = tmp_path / row['html_path']
    html = html_path.read_text(encoding='utf-8').replace(
        '总价：400万', f'{qualified_label}：300万')
    html_path.write_text(html, encoding='utf-8')
    row['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    parse = evaluator_module.parse_listing_html

    def promote_qualified_price(source, url, content):
        result = parse(source, url, content)
        if source == 'beike' and qualified_label in content:
            result.fields['asking_price_wan'] = 300
        return result

    monkeypatch.setattr(evaluator_module, 'parse_listing_html', promote_qualified_price)
    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    result = report['scenarios']['beike'][scenario]
    assert result['samples'] == 1
    assert result['passed'] == 0
    assert result['pass_rate_pct'] == 0.0
    price_metric = report['fields']['beike']['asking_price_wan']
    assert price_metric['labeled'] == 4
    assert price_metric['correct'] == 3
    assert price_metric['accuracy_pct'] == 75.0
    assert price_metric['precision_pct'] == 75.0


@pytest.mark.parametrize('mutate_sample', [False, True])
def test_evaluator_refuses_input_changes_after_validation(tmp_path, monkeypatch, mutate_sample):
    manifest, rows = build_eval_manifest(tmp_path)
    original_validate = evaluator_module.validate_manifest

    def validate_then_mutate(manifest_path, root, minimum_per_source, *, manifest_content):
        result = original_validate(
            manifest_path, root, minimum_per_source, manifest_content=manifest_content)
        if mutate_sample:
            sample_path = root / rows[0]['html_path']
            sample_path.write_text(sample_path.read_text(encoding='utf-8') + ' ', encoding='utf-8')
        else:
            manifest_path.write_bytes(manifest_path.read_bytes() + b'\n')
        return result

    monkeypatch.setattr(evaluator_module, 'validate_manifest', validate_then_mutate)
    expected_error = 'saved HTML changed during evaluation' if mutate_sample else 'manifest changed during parser evaluation'

    with pytest.raises(ValueError, match=expected_error):
        evaluator_module.evaluate_manifest(manifest, tmp_path, minimum_per_source=5)


def test_evaluator_rejects_oversized_manifest_before_validation(tmp_path, monkeypatch):
    manifest = tmp_path / 'manifest.csv'
    manifest.write_bytes(b'x' * (evaluator_module.MAX_MANIFEST_BYTES + 1))

    def validation_must_not_run(*args, **kwargs):
        pytest.fail('oversized manifest must be rejected before parsing')

    monkeypatch.setattr(evaluator_module, 'validate_manifest', validation_must_not_run)

    with pytest.raises(ValueError, match='manifest exceeds 2000000 byte limit'):
        evaluate_manifest(manifest, tmp_path, minimum_per_source=5)


@pytest.mark.parametrize(('invalid_manifest', 'expected_error'), [
    (b'\xff', 'manifest must be valid UTF-8'),
    (b'"unterminated', 'manifest CSV is malformed'),
])
def test_evaluator_reports_invalid_csv_without_leaking_parser_exception(
        tmp_path, invalid_manifest, expected_error):
    manifest = tmp_path / 'manifest.csv'
    manifest.write_bytes(invalid_manifest)

    with pytest.raises(ValueError, match=expected_error):
        evaluate_manifest(manifest, tmp_path, minimum_per_source=5)


@pytest.mark.parametrize(('invalid_manifest', 'expected_error'), [
    (b'\xff', 'manifest must be valid UTF-8'),
    (b'"unterminated', 'manifest CSV is malformed'),
])
def test_evaluator_cli_reports_invalid_manifest_without_traceback(
        tmp_path, invalid_manifest, expected_error):
    root = Path(__file__).resolve().parents[1]
    manifest = tmp_path / 'manifest.csv'
    manifest.write_bytes(invalid_manifest)

    result = subprocess.run(
        [sys.executable, str(root / 'scripts/evaluate_parser.py'), '--manifest', str(manifest)],
        cwd=root, capture_output=True, text=True, check=False,
    )

    assert result.returncode == 1
    assert f'Evaluation refused: {expected_error}' in result.stdout
    assert result.stderr == ''


def test_manifest_at_size_limit_can_be_hashed(tmp_path):
    manifest = tmp_path / 'manifest.csv'
    content = b'x' * evaluator_module.MAX_MANIFEST_BYTES
    manifest.write_bytes(content)

    assert evaluator_module._sha256_file(manifest) == hashlib.sha256(content).hexdigest()


def test_manifest_hash_refuses_content_over_size_limit(tmp_path):
    manifest = tmp_path / 'manifest.csv'
    manifest.write_bytes(b'x' * (evaluator_module.MAX_MANIFEST_BYTES + 1))

    with pytest.raises(ValueError, match='manifest exceeds 2000000 byte limit'):
        evaluator_module._sha256_file(manifest)


def test_manifest_hash_reads_only_one_byte_past_size_limit():
    class TrackingStream(io.BytesIO):
        bytes_read = 0

        def read(self, size=-1):
            content = super().read(size)
            self.bytes_read += len(content)
            return content

    class TrackingPath:
        def __init__(self, stream):
            self.stream = stream

        def open(self, mode):
            assert mode == 'rb'
            return self.stream

    maximum = evaluator_module.MAX_MANIFEST_BYTES
    stream = TrackingStream(b'x' * (maximum + 100_000))

    with pytest.raises(ValueError, match='manifest exceeds 2000000 byte limit'):
        evaluator_module._sha256_file(TrackingPath(stream))

    assert stream.bytes_read == maximum + 1


def test_evaluator_rejects_manifest_that_grows_during_evaluation(tmp_path, monkeypatch):
    manifest, _ = build_eval_manifest(tmp_path)
    original_validate = evaluator_module.validate_manifest

    def validate_then_grow(manifest_path, root, minimum_per_source, *, manifest_content):
        result = original_validate(
            manifest_path, root, minimum_per_source, manifest_content=manifest_content)
        with manifest_path.open('ab') as stream:
            stream.write(b'x' * (evaluator_module.MAX_MANIFEST_BYTES + 1))
        return result

    monkeypatch.setattr(evaluator_module, 'validate_manifest', validate_then_grow)

    with pytest.raises(ValueError, match='manifest exceeds 2000000 byte limit'):
        evaluate_manifest(manifest, tmp_path, minimum_per_source=5)


def test_evaluator_uses_manifest_snapshot_if_file_is_replaced_then_restored(tmp_path, monkeypatch):
    manifest, rows = build_eval_manifest(tmp_path)
    original_content = manifest.read_bytes()
    original_validate = evaluator_module.validate_manifest

    def validate_with_temporary_change(manifest_path, root, minimum_per_source, *, manifest_content):
        result = original_validate(
            manifest_path, root, minimum_per_source, manifest_content=manifest_content)
        manifest_path.write_bytes(manifest_content.replace('东湖花园'.encode(), '其他小区'.encode()))
        return result

    monkeypatch.setattr(evaluator_module, 'validate_manifest', validate_with_temporary_change)

    def restore_before_final_fingerprint(path):
        path.write_bytes(original_content)
        return hashlib.sha256(original_content).hexdigest()

    monkeypatch.setattr(evaluator_module, '_sha256_file', restore_before_final_fingerprint)

    report = evaluator_module.evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert report['manifest_sha256'] == hashlib.sha256(original_content).hexdigest()
    assert report['fields']['beike']['area_sqm']['correct'] == 5
    assert report['fields']['beike']['community_name']['correct'] == 5


def test_multiple_price_scenario_requires_matching_annotated_candidates(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path)
    rows[3]['price_candidates_wan'] = '360|371'
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    scenario = report['scenarios']['beike']['multiple_prices']
    assert scenario['samples'] == 1
    assert scenario['passed'] == 0


def test_evaluator_matches_grouped_price_candidates_by_numeric_value(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path)
    rows[3]['price_candidates_wan'] = '1234|1235'
    html_path = tmp_path / rows[3]['html_path']
    html = html_path.read_text(encoding='utf-8')
    html = html.replace('总价：360万', '总价：1,234万').replace('总价：370万', '总价：1,235万')
    html_path.write_text(html, encoding='utf-8')
    rows[3]['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert report['scenarios']['beike']['multiple_prices']['pass_rate_pct'] == 100.0


def test_evaluator_matches_price_range_as_one_conflict_candidate(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path)
    rows[3]['price_candidates_wan'] = '300万-320万|310'
    html_path = tmp_path / rows[3]['html_path']
    html = html_path.read_text(encoding='utf-8').replace(
        '总价：360万 总价：370万', '总价：300万-320万 总价：310万')
    html_path.write_text(html, encoding='utf-8')
    rows[3]['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert report['scenarios']['beike']['multiple_prices']['pass_rate_pct'] == 100.0


def test_multiple_price_scenario_fails_when_price_evidence_is_truncated(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path)
    html_path = tmp_path / rows[3]['html_path']
    html = html_path.read_text(encoding='utf-8')
    html = html.replace('</main>', ' ' + ' '.join('总价：360万' for _ in range(19)) + '</main>')
    html_path.write_text(html, encoding='utf-8')
    rows[3]['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    scenario = report['scenarios']['beike']['multiple_prices']
    assert scenario['samples'] == 1
    assert scenario['passed'] == 0


def test_multiple_price_scenario_fails_when_second_price_is_after_text_limit(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path)
    html_path = tmp_path / rows[3]['html_path']
    html = html_path.read_text(encoding='utf-8')
    html = html.replace('总价：360万 总价：370万',
                        '总价：360万 ' + '说明' * 18000 + ' 总价：370万')
    html_path.write_text(html, encoding='utf-8')
    rows[3]['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    scenario = report['scenarios']['beike']['multiple_prices']
    assert scenario['samples'] == 1
    assert scenario['passed'] == 0


def test_missing_fields_scenario_fails_when_labeled_field_is_after_text_limit(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path)
    html_path = tmp_path / rows[2]['html_path']
    html = html_path.read_text(encoding='utf-8')
    html = html.replace('</main>', ' ' + '说明' * 18_000 + ' 建筑面积：120㎡</main>')
    html_path.write_text(html, encoding='utf-8')
    rows[2]['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    scenario = report['scenarios']['beike']['missing_fields']
    assert scenario['samples'] == 2
    assert scenario['passed'] == 1


def test_evaluator_marks_exactly_20_samples_as_meeting_production_requirement(tmp_path):
    manifest, _ = build_eval_manifest(tmp_path, samples_per_source=20)

    report = evaluate_manifest(manifest, tmp_path)

    assert report['sample_requirements']['beike'] == {
        'required': 20, 'observed': 20, 'met': True,
    }
    assert report['sample_requirements']['anjuke'] == {
        'required': 20, 'observed': 20, 'met': True,
    }


@pytest.mark.parametrize(('mismatches', 'precision', 'meets_target'), [
    (1, 95.0, True),
    (2, 90.0, False),
])
def test_evaluator_reports_extracted_value_precision_target(
        tmp_path, mismatches, precision, meets_target):
    manifest, rows = build_eval_manifest(tmp_path, samples_per_source=20)
    for row in rows[:mismatches]:
        row['floor_text'] = '低楼层'
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path)
    metric = report['fields']['beike']['floor_text']

    assert metric['precision_pct'] == precision
    assert metric['precision_target_pct'] == 95.0
    assert metric['precision_target_met'] is meets_target
    assert report['sample_requirements']['beike']['met'] is True


def test_evaluator_precision_target_does_not_round_up_to_95_percent(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path, samples_per_source=1999)
    for row in rows[:100]:
        row['floor_text'] = '低楼层'
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path)
    metric = report['fields']['beike']['floor_text']

    assert metric['correct'] == 1899
    assert metric['covered'] == 1999
    assert metric['precision_pct'] == 95.0
    assert metric['precision_target_met'] is False


def test_evaluator_does_not_meet_precision_target_without_any_extractions(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path)
    for row in rows:
        html_path = tmp_path / row['html_path']
        html = html_path.read_text(encoding='utf-8')
        html = html.replace('建筑面积：120㎡', '')
        html_path.write_text(html, encoding='utf-8')
        row['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    metric = report['fields']['beike']['area_sqm']
    assert metric['labeled'] == 5
    assert metric['covered'] == 0
    assert metric['coverage_pct'] == 0.0
    assert metric['precision_pct'] is None
    assert metric['precision_target_met'] is False


def test_evaluator_counts_false_positive_on_labeled_missing_field_against_precision(
        tmp_path, monkeypatch):
    manifest, rows = build_eval_manifest(tmp_path)
    parse = evaluator_module.parse_listing_html

    def add_incorrect_missing_area(source, source_url, html):
        result = parse(source, source_url, html)
        if source == 'beike' and '虚构样本 beike 2' in html:
            fields = {**result.fields, 'area_sqm': 120}
            return SimpleNamespace(fields=fields, warnings=result.warnings)
        return result

    monkeypatch.setattr(evaluator_module, 'parse_listing_html', add_incorrect_missing_area)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    metric = report['fields']['beike']['area_sqm']
    assert metric['labeled'] == 5
    assert metric['covered'] == 5
    assert metric['correct'] == 4
    assert metric['accuracy_pct'] == 80.0
    assert metric['coverage_pct'] == 100.0
    assert metric['precision_pct'] == 80.0
    assert metric['precision_target_met'] is False
    assert report['scenarios']['beike']['missing_fields']['passed'] == 1


def test_evaluator_uses_unambiguous_canonical_source_listing_id(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path)
    rows[0]['source_url'] = 'https://nb.ke.com/ershoufang/'
    html_path = tmp_path / rows[0]['html_path']
    html = html_path.read_text(encoding='utf-8')
    canonical = f"<link rel=\"canonical\" href=\"/ershoufang/{rows[0]['source_listing_id']}.html\">"
    html = html.replace('<html><body>', f'<html><head>{canonical}</head><body>', 1)
    html_path.write_text(html, encoding='utf-8')
    rows[0]['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert report['fields']['beike']['source_listing_id']['correct'] == 5
    assert report['fields']['beike']['source_listing_id']['accuracy_pct'] == 100.0
    assert report['fields']['beike']['source_listing_id']['coverage_pct'] == 80.0


@pytest.mark.parametrize('field,truth', [
    ('area_sqm', '120.004'),
    ('asking_price_wan', '400.004'),
])
def test_evaluator_does_not_round_numeric_mismatches_into_exact_matches(tmp_path, field, truth):
    manifest, rows = build_eval_manifest(tmp_path)
    rows[0][field] = truth
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)
    metric = report['fields']['beike'][field]

    assert metric['correct'] == metric['labeled'] - 1
    assert metric['accuracy_pct'] == round(metric['correct'] / metric['labeled'] * 100, 2)


@pytest.mark.parametrize('tag,field,original,conflict', [
    ('multiple_communities', 'community_name', '小区：东湖花园', '小区：锦港府'),
    ('multiple_areas', 'area_sqm', '建筑面积：120㎡', '建面：110㎡'),
    ('multiple_districts', 'district', '所在区域：鄞州', '所在区域：海曙'),
    ('multiple_bedrooms', 'bedrooms', '户型：3室', '户型：2室'),
    ('multiple_floors', 'floor_text', '楼层：高楼层', '楼层：低楼层'),
    ('multiple_decorations', 'decoration', '装修：精装', '装修：简装'),
])
def test_evaluator_scores_ambiguous_optional_field_and_checks_warning(
        tmp_path, tag, field, original, conflict):
    manifest, rows = build_eval_manifest(tmp_path)
    rows[0][field] = ''
    rows[0]['scenario_tags'] = tag
    candidate_column = AMBIGUOUS_FIELD_CANDIDATE_COLUMNS[tag]
    rows[0][candidate_column] = ('东湖花园|锦港府' if tag == 'multiple_communities' else
                                 '120|110' if tag == 'multiple_areas' else
                                 '鄞州|海曙' if tag == 'multiple_districts' else
                                 '3|2' if tag == 'multiple_bedrooms' else
                                 '高楼层|低楼层' if tag == 'multiple_floors' else
                                 '精装|简装')
    html_path = tmp_path / rows[0]['html_path']
    html = html_path.read_text(encoding='utf-8').replace(original, f'{original} {conflict}')
    html_path.write_text(html, encoding='utf-8')
    rows[0]['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert report['fields']['beike'][field]['labeled'] == 5
    assert report['fields']['beike'][field]['correct'] == 5
    assert report['fields']['beike'][field]['coverage_pct'] == (
        60.0 if field == 'area_sqm' else 80.0)
    assert report['scenarios']['beike'][tag]['pass_rate_pct'] == 100.0


def test_evaluator_matches_grouped_area_candidates_by_numeric_value(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path)
    rows[0]['area_sqm'] = ''
    rows[0]['scenario_tags'] = 'multiple_areas'
    rows[0]['area_candidates_sqm'] = '1234|1235'
    html_path = tmp_path / rows[0]['html_path']
    html = html_path.read_text(encoding='utf-8').replace(
        '建筑面积：120㎡', '建筑面积：1,234㎡ 建面：1,235㎡')
    html_path.write_text(html, encoding='utf-8')
    rows[0]['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert report['scenarios']['beike']['multiple_areas']['pass_rate_pct'] == 100.0


def test_evaluator_matches_area_range_as_one_conflict_candidate(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path)
    rows[0]['area_sqm'] = ''
    rows[0]['scenario_tags'] = 'multiple_areas'
    rows[0]['area_candidates_sqm'] = '120㎡-130㎡|125'
    html_path = tmp_path / rows[0]['html_path']
    html = html_path.read_text(encoding='utf-8').replace(
        '建筑面积：120㎡', '建筑面积：120㎡-130㎡ 建面：125㎡')
    html_path.write_text(html, encoding='utf-8')
    rows[0]['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert report['scenarios']['beike']['multiple_areas']['pass_rate_pct'] == 100.0


def test_evaluator_checks_single_area_range_evidence(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path)
    rows[0]['area_sqm'] = ''
    rows[0]['scenario_tags'] = 'area_ranges'
    rows[0]['area_candidates_sqm'] = '120㎡-130㎡'
    html_path = tmp_path / rows[0]['html_path']
    html = html_path.read_text(encoding='utf-8').replace(
        '建筑面积：120㎡', '建筑面积：120㎡-130㎡')
    html_path.write_text(html, encoding='utf-8')
    rows[0]['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert report['scenarios']['beike']['area_ranges']['pass_rate_pct'] == 100.0


@pytest.mark.parametrize('range_text', [
    '建筑面积：100㎡-120㎡左右',
    '建筑面积：100㎡-120㎡以上',
    '建筑面积：约100㎡-120㎡',
    '建筑面积估算100㎡-120㎡',
    '建筑面积约：100㎡-120㎡',
    '建筑面积估算：100㎡-120㎡',
    '约建筑面积：100㎡-120㎡',
    '参考建筑面积：100㎡-120㎡',
])
def test_evaluator_accepts_qualified_area_range_evidence(tmp_path, range_text):
    manifest, rows = build_eval_manifest(tmp_path)
    row = next(row for row in rows if row['source'] == 'beike')
    row['area_sqm'] = ''
    row['scenario_tags'] = 'non_exact_area_ranges'
    row['area_candidates_sqm'] = '100㎡-120㎡'
    html_path = tmp_path / row['html_path']
    html = html_path.read_text(encoding='utf-8').replace('建筑面积：120㎡', range_text)
    html_path.write_text(html, encoding='utf-8')
    row['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert report['scenarios']['beike']['non_exact_area_ranges']['pass_rate_pct'] == 100.0


@pytest.mark.parametrize('failure', [
    'exact_flag', 'missing_warning', 'truncated_quote', 'all_signals',
])
def test_qualified_area_range_requires_non_exact_evidence_contract(
        tmp_path, monkeypatch, failure):
    manifest, rows = build_eval_manifest(tmp_path)
    row = next(row for row in rows if row['source'] == 'beike')
    row['area_sqm'] = ''
    row['scenario_tags'] = 'non_exact_area_ranges'
    row['area_candidates_sqm'] = '100㎡-120㎡'
    html_path = tmp_path / row['html_path']
    html = html_path.read_text(encoding='utf-8').replace(
        '建筑面积：120㎡', '建筑面积：100㎡-120㎡左右')
    html_path.write_text(html, encoding='utf-8')
    row['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    parse = evaluator_module.parse_listing_html

    def faulty_qualified_area_range_parser(*args, **kwargs):
        result = parse(*args, **kwargs)
        if '100㎡-120㎡左右' in args[2]:
            evidence = result.fields['field_evidence']['area_sqm']
            mention = evidence['mentions'][0]
            if failure == 'exact_flag':
                mention['is_non_exact'] = False
            elif failure == 'missing_warning':
                result.warnings.remove('non_exact_area_sqm')
            elif failure == 'truncated_quote':
                mention['quote'] = '建筑面积：100㎡-120㎡'
            else:
                mention['is_non_exact'] = False
                mention['quote'] = '建筑面积：100㎡-120㎡'
                result.warnings.remove('non_exact_area_sqm')
        return result

    monkeypatch.setattr(evaluator_module, 'parse_listing_html', faulty_qualified_area_range_parser)
    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    scenario = report['scenarios']['beike']['non_exact_area_ranges']
    assert scenario['samples'] == 1
    assert scenario['passed'] == 0


def test_evaluator_checks_single_price_range_evidence(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path)
    rows[0]['asking_price_wan'] = ''
    rows[0]['scenario_tags'] = 'price_ranges'
    rows[0]['price_candidates_wan'] = '300万-320万'
    html_path = tmp_path / rows[0]['html_path']
    html = html_path.read_text(encoding='utf-8').replace(
        '总价：400万', '总价：300万-320万')
    html_path.write_text(html, encoding='utf-8')
    rows[0]['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert report['scenarios']['beike']['price_ranges']['pass_rate_pct'] == 100.0


@pytest.mark.parametrize(('price_text', 'candidate'), [
    ('挂牌价：300-320万左右', '300-320万'),
    ('挂牌价：300万-320万以上', '300万-320万'),
    ('挂牌价约：300-320万', '300-320万'),
    ('总价估算：300万-320万', '300万-320万'),
])
def test_evaluator_accepts_qualified_price_range_evidence(tmp_path, price_text, candidate):
    manifest, rows = build_eval_manifest(tmp_path)
    row = next(row for row in rows if row['source'] == 'beike')
    row['asking_price_wan'] = ''
    row['scenario_tags'] = 'non_exact_price_ranges'
    row['price_candidates_wan'] = candidate
    html_path = tmp_path / row['html_path']
    html = html_path.read_text(encoding='utf-8').replace('总价：400万', price_text)
    html_path.write_text(html, encoding='utf-8')
    row['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert report['scenarios']['beike']['non_exact_price_ranges']['pass_rate_pct'] == 100.0


@pytest.mark.parametrize('failure', [
    'exact_flag', 'missing_warning', 'truncated_quote', 'all_signals',
])
def test_qualified_price_range_requires_non_exact_evidence_contract(
        tmp_path, monkeypatch, failure):
    manifest, rows = build_eval_manifest(tmp_path)
    row = next(row for row in rows if row['source'] == 'beike')
    row['asking_price_wan'] = ''
    row['scenario_tags'] = 'non_exact_price_ranges'
    row['price_candidates_wan'] = '300-320万'
    html_path = tmp_path / row['html_path']
    html = html_path.read_text(encoding='utf-8').replace(
        '总价：400万', '挂牌价：300-320万左右')
    html_path.write_text(html, encoding='utf-8')
    row['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    parse = evaluator_module.parse_listing_html

    def faulty_qualified_price_range_parser(*args, **kwargs):
        result = parse(*args, **kwargs)
        if '300-320万左右' in args[2]:
            evidence = result.fields['field_evidence']['asking_price_wan']
            mention = evidence['mentions'][0]
            if failure == 'exact_flag':
                mention['is_non_exact'] = False
            elif failure == 'missing_warning':
                result.warnings.remove('non_exact_asking_price')
            elif failure == 'truncated_quote':
                mention['quote'] = '挂牌价：300-320万'
            else:
                mention['is_non_exact'] = False
                mention['quote'] = '挂牌价：300-320万'
                result.warnings.remove('non_exact_asking_price')
        return result

    monkeypatch.setattr(evaluator_module, 'parse_listing_html', faulty_qualified_price_range_parser)
    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    scenario = report['scenarios']['beike']['non_exact_price_ranges']
    assert scenario['samples'] == 1
    assert scenario['passed'] == 0


def test_evaluator_checks_price_range_evidence_with_another_quote(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path)
    rows[3]['scenario_tags'] = 'multiple_prices|price_ranges'
    rows[3]['price_candidates_wan'] = '300万-320万|310'
    html_path = tmp_path / rows[3]['html_path']
    html = html_path.read_text(encoding='utf-8').replace(
        '总价：360万 总价：370万', '总价：300万-320万 总价：310万')
    html_path.write_text(html, encoding='utf-8')
    rows[3]['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert report['scenarios']['beike']['multiple_prices']['pass_rate_pct'] == 100.0
    assert report['scenarios']['beike']['price_ranges']['pass_rate_pct'] == 100.0


def test_evaluator_matches_qualified_ranges_and_other_exact_mentions(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path)
    row = next(row for row in rows if row['source'] == 'beike')
    row['area_sqm'] = ''
    row['asking_price_wan'] = ''
    row['scenario_tags'] = (
        'multiple_areas|non_exact_area_ranges|multiple_prices|non_exact_price_ranges')
    row['area_candidates_sqm'] = '100㎡-120㎡|110'
    row['price_candidates_wan'] = '300-320万|310'
    html_path = tmp_path / row['html_path']
    html = html_path.read_text(encoding='utf-8').replace(
        '建筑面积：120㎡', '建筑面积约：100㎡-120㎡ 建面：110㎡').replace(
        '总价：400万', '总价估算：300-320万 挂牌价：310万')
    html_path.write_text(html, encoding='utf-8')
    row['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    for scenario in ('multiple_areas', 'non_exact_area_ranges',
                     'multiple_prices', 'non_exact_price_ranges'):
        assert report['scenarios']['beike'][scenario]['pass_rate_pct'] == 100.0


@pytest.mark.parametrize(('field', 'tag', 'candidate_column', 'range_value', 'replacement'), [
    ('area_sqm', 'area_ranges', 'area_candidates_sqm', '120㎡-130㎡',
     ' '.join('建筑面积：120㎡-130㎡' for _ in range(21))),
    ('asking_price_wan', 'price_ranges', 'price_candidates_wan', '300万-320万',
     ' '.join(['总价：300万-320万'] * 21 + ['总价：310万'])),
])
def test_range_scenario_fails_when_range_evidence_is_truncated(
        tmp_path, field, tag, candidate_column, range_value, replacement):
    manifest, rows = build_eval_manifest(tmp_path)
    row = rows[0 if field == 'area_sqm' else 3]
    row[field] = ''
    row['scenario_tags'] = tag if field == 'area_sqm' else 'multiple_prices|price_ranges'
    row[candidate_column] = (range_value if field == 'area_sqm'
                             else f'{range_value}|310')
    html_path = tmp_path / row['html_path']
    html = html_path.read_text(encoding='utf-8')
    if field == 'area_sqm':
        html = html.replace('建筑面积：120㎡', replacement)
    else:
        html = html.replace('总价：360万 总价：370万', replacement)
    html_path.write_text(html, encoding='utf-8')
    row['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    scenario = report['scenarios']['beike'][tag]
    assert scenario['samples'] == 1
    assert scenario['passed'] == 0


def test_evaluator_matches_out_of_range_bedroom_candidate_evidence(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path)
    rows[0]['bedrooms'] = ''
    rows[0]['scenario_tags'] = 'multiple_bedrooms'
    rows[0]['bedroom_candidates'] = '3|21'
    html_path = tmp_path / rows[0]['html_path']
    html = html_path.read_text(encoding='utf-8').replace(
        '户型：3室', '户型：3室 户型：21室')
    html_path.write_text(html, encoding='utf-8')
    rows[0]['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert report['fields']['beike']['bedrooms']['coverage_pct'] == 80.0
    assert report['scenarios']['beike']['multiple_bedrooms']['pass_rate_pct'] == 100.0


def test_evaluator_reports_single_invalid_bedroom_as_its_own_scenario(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path)
    rows[0]['bedrooms'] = ''
    rows[0]['scenario_tags'] = 'invalid_bedrooms'
    rows[0]['invalid_bedroom_candidates'] = '21'
    html_path = tmp_path / rows[0]['html_path']
    html = html_path.read_text(encoding='utf-8').replace('户型：3室', '户型：21室')
    html_path.write_text(html, encoding='utf-8')
    rows[0]['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert report['fields']['beike']['bedrooms']['coverage_pct'] == 80.0
    assert report['scenarios']['beike']['invalid_bedrooms']['pass_rate_pct'] == 100.0


@pytest.mark.parametrize(('tag', 'field', 'candidate_column', 'original', 'actual_candidates',
                          'expected_candidates'), [
    ('multiple_communities', 'community_name', 'community_candidates',
     '小区：东湖花园', '小区：东湖花园 小区：海曙印象城', '东湖花园|锦港府'),
    ('multiple_areas', 'area_sqm', 'area_candidates_sqm',
     '建筑面积：120㎡', '建筑面积：120㎡ 建面：110㎡', '120|115'),
    ('multiple_districts', 'district', 'district_candidates',
     '所在区域：鄞州', '所在区域：鄞州 所在区域：海曙', '鄞州|江北'),
])
def test_evaluator_rejects_ambiguous_field_candidates_that_do_not_match_page(
        tmp_path, tag, field, candidate_column, original, actual_candidates,
        expected_candidates):
    manifest, rows = build_eval_manifest(tmp_path)
    rows[0][field] = ''
    rows[0]['scenario_tags'] = tag
    rows[0][candidate_column] = expected_candidates
    html_path = tmp_path / rows[0]['html_path']
    html = html_path.read_text(encoding='utf-8').replace(original, actual_candidates)
    html_path.write_text(html, encoding='utf-8')
    rows[0]['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    scenario = report['scenarios']['beike'][tag]
    assert scenario['samples'] == 1
    assert scenario['passed'] == 0


@pytest.mark.parametrize(('tag', 'field', 'candidate_column', 'label', 'candidates'), [
    ('multiple_communities', 'community_name', 'community_candidates',
     '小区：东湖花园', '小区：东湖花园|锦港府'),
    ('multiple_areas', 'area_sqm', 'area_candidates_sqm',
     '建筑面积：120㎡', '120|110'),
    ('multiple_districts', 'district', 'district_candidates',
     '所在区域：鄞州', '鄞州|海曙'),
])
def test_evaluator_fails_ambiguous_scenario_when_candidate_evidence_is_truncated(
        tmp_path, tag, field, candidate_column, label, candidates):
    manifest, rows = build_eval_manifest(tmp_path)
    rows[0][field] = ''
    rows[0]['scenario_tags'] = tag
    rows[0][candidate_column] = candidates
    html_path = tmp_path / rows[0]['html_path']
    repeated = label + ('花园' if field == 'community_name' else '东湖')
    html = html_path.read_text(encoding='utf-8').replace(
        label, label + ' ' + ' '.join(repeated for _ in range(20)))
    html_path.write_text(html, encoding='utf-8')
    rows[0]['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    scenario = report['scenarios']['beike'][tag]
    assert scenario['samples'] == 1
    assert scenario['passed'] == 0


def test_evaluator_scores_conflicting_source_id_evidence(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path)
    row = rows[0]
    url_id = row['source_listing_id']
    canonical_id = url_id[:-1] + ('1' if url_id[-1] != '1' else '2')
    row['source_listing_id'] = ''
    row['scenario_tags'] = 'source_id_conflict'
    row['source_listing_id_candidates'] = f'{url_id}|{canonical_id}'
    html_path = tmp_path / row['html_path']
    html = html_path.read_text(encoding='utf-8').replace(
        '<html><body>',
        f'<html><head><link rel="canonical" href="/ershoufang/{canonical_id}.html"></head><body>')
    html_path.write_text(html, encoding='utf-8')
    row['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert report['fields']['beike']['source_listing_id']['labeled'] == 5
    assert report['fields']['beike']['source_listing_id']['correct'] == 5
    assert report['scenarios']['beike']['source_id_conflict']['pass_rate_pct'] == 100.0


def test_evaluator_rejects_conflicting_source_id_candidate_mismatch(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path)
    row = rows[0]
    url_id = row['source_listing_id']
    canonical_id = url_id[:-1] + ('1' if url_id[-1] != '1' else '2')
    wrong_id = url_id[:-1] + ('3' if url_id[-1] != '3' else '4')
    row['source_listing_id'] = ''
    row['scenario_tags'] = 'source_id_conflict'
    row['source_listing_id_candidates'] = f'{url_id}|{wrong_id}'
    html_path = tmp_path / row['html_path']
    html = html_path.read_text(encoding='utf-8').replace(
        '<html><body>',
        f'<html><head><link rel="canonical" href="/ershoufang/{canonical_id}.html"></head><body>')
    html_path.write_text(html, encoding='utf-8')
    row['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    scenario = report['scenarios']['beike']['source_id_conflict']
    assert scenario['samples'] == 1
    assert scenario['passed'] == 0


def test_evaluator_fails_conflicting_source_ids_when_evidence_is_truncated(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path)
    row = rows[0]
    url_id = row['source_listing_id']
    candidates = [f'1099000001{index:02d}' for index in range(20)]
    row['source_listing_id'] = ''
    row['scenario_tags'] = 'source_id_conflict'
    row['source_listing_id_candidates'] = f'{url_id}|{candidates[0]}'
    html_path = tmp_path / row['html_path']
    canonicals = ''.join(
        f'<link rel="canonical" href="/ershoufang/{candidate}.html">'
        for candidate in candidates)
    html = html_path.read_text(encoding='utf-8').replace(
        '<html><body>', f'<html><head>{canonicals}</head><body>')
    html_path.write_text(html, encoding='utf-8')
    row['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    scenario = report['scenarios']['beike']['source_id_conflict']
    assert scenario['samples'] == 1
    assert scenario['passed'] == 0


def test_evaluator_refuses_invalid_manifest_hash(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path)
    rows[0]['sha256'] = '0' * 64
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    with pytest.raises(ValueError, match='sha256 does not match'):
        evaluate_manifest(manifest, tmp_path, minimum_per_source=5)


def test_evaluator_reports_corrupt_compressed_sample(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path)
    html_path = tmp_path / rows[0]['html_path']
    compressed_path = html_path.with_suffix(html_path.suffix + '.gz')
    compressed_path.write_bytes(b'not a gzip stream')
    html_path.unlink()
    rows[0]['html_path'] += '.gz'
    rows[0]['sha256'] = hashlib.sha256(compressed_path.read_bytes()).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    with pytest.raises(ValueError, match='gzip sample cannot be decompressed'):
        evaluate_manifest(manifest, tmp_path, minimum_per_source=5)


def test_evaluator_refuses_non_utf8_sample_before_parsing(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path)
    sample_path = tmp_path / rows[0]['html_path']
    content = b'<html><body>\xffinvalid</body></html>'
    sample_path.write_bytes(content)
    rows[0]['sha256'] = hashlib.sha256(content).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    with pytest.raises(ValueError, match='HTML sample must be valid UTF-8'):
        evaluate_manifest(manifest, tmp_path, minimum_per_source=5)


def test_evaluator_refuses_oversized_compressed_sample(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path)
    original = tmp_path / rows[0]['html_path']
    compressed = original.with_suffix(original.suffix + '.gz')
    compressed.write_bytes(gzip.compress(b'x' * 1_000_001))
    original.unlink()
    rows[0]['html_path'] += '.gz'
    rows[0]['sha256'] = hashlib.sha256(compressed.read_bytes()).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    with pytest.raises(ValueError, match='HTML sample exceeds 1000000 byte limit'):
        evaluate_manifest(manifest, tmp_path, minimum_per_source=5)


def test_documented_evaluator_command_has_cli_help():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, str(root / 'scripts/evaluate_parser.py'), '--help'],
        cwd=root, capture_output=True, text=True, check=False,
    )

    assert result.returncode == 0
    assert '--manifest' in result.stdout


def test_evaluator_reports_title_accuracy_and_coverage(tmp_path):
    manifest, rows = build_eval_manifest(tmp_path)
    for row in rows:
        source = row['source']
        index = row['sample_id'].rsplit('-', 1)[-1]
        row['title'] = f'虚构样本 {source} {index}'
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert report['fields']['beike']['title']['labeled'] == 5
    assert report['fields']['beike']['title']['correct'] == 5
    assert report['fields']['beike']['title']['accuracy_pct'] == 100.0


def test_text_field_evaluation_normalizes_canonical_unicode():
    decomposed = 'Cafe\u0301 房源'
    composed = 'Café 房源'

    assert evaluator_module._normalize('title', decomposed) == \
        evaluator_module._normalize('title', composed)


def test_evaluator_counts_canonically_equivalent_title_as_correct(tmp_path, monkeypatch):
    manifest, rows = build_eval_manifest(tmp_path)
    for row in rows:
        row['title'] = 'Café 房源'
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    monkeypatch.setattr(
        evaluator_module, 'parse_listing_html',
        lambda *args: SimpleNamespace(
            fields={'title': 'Cafe\u0301 房源'}, warnings=[],
            ready_for_review=False))

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert report['fields']['beike']['title']['correct'] == 5
    assert report['fields']['beike']['title']['accuracy_pct'] == 100.0
    assert report['fields']['beike']['title']['precision_pct'] == 100.0


@pytest.mark.parametrize('correct_title_label', [True, False])
def test_evaluator_checks_title_source_conflict_fallback(tmp_path, correct_title_label):
    manifest, rows = build_eval_manifest(tmp_path)
    rows[0]['scenario_tags'] = 'title_source_conflict'
    if not correct_title_label:
        rows[0]['title'] = '错误标题'
    html_path = tmp_path / rows[0]['html_path']
    html = html_path.read_text(encoding='utf-8').replace(
        '<html><body>',
        '<html><head><meta property="og:title" content="推荐房源">'
        '<meta property="og:title" content="附近热销房源"></head><body>')
    html_path.write_text(html, encoding='utf-8')
    rows[0]['sha256'] = hashlib.sha256(html.encode('utf-8')).hexdigest()
    with manifest.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)

    report = evaluate_manifest(manifest, tmp_path, minimum_per_source=5)

    assert report['scenarios']['beike']['title_source_conflict']['pass_rate_pct'] == (
        100.0 if correct_title_label else 0.0)
    assert report['fields']['beike']['title']['correct'] == (
        5 if correct_title_label else 4)
