from pathlib import Path
import random
import re
import tracemalloc
import pytest
from bs4 import BeautifulSoup
from bs4.element import Tag
from app.collectors import (check_source_url, extract_source_id,
                            parse_listing_html)
from app.collectors import parser as parser_module
from app.collectors.parser import (PARSER_VERSION, CollectionError, _inline_display_none,
                                   _inline_opacity_zero,
                                   _first_unique, _text_with_inline_boundaries,
                                   _unique_text_values)

ROOT=Path(__file__).resolve().parents[1]


def test_text_field_candidates_treat_canonical_unicode_as_same_value():
    first = 'Cafe\u0301'
    equivalent = 'Café'

    value, candidates = _first_unique(r'小区：([^|]+)', f'小区：{first}|小区：{equivalent}')

    assert value == first
    assert candidates == [first]


def test_field_ambiguity_scan_stops_after_two_distinct_values(monkeypatch):
    original_finditer = re.finditer
    match_visits = 0

    def count_matches(pattern, text, flags=0):
        nonlocal match_visits
        for match in original_finditer(pattern, text, flags):
            match_visits += 1
            yield match

    monkeypatch.setattr(re, 'finditer', count_matches)
    repeated_text = '小区：甲花园|小区：乙花园|' + '小区：甲花园|' * 1000
    value, candidates = _first_unique(r'小区：([^|]+)', repeated_text)

    assert value is None
    assert candidates == ['甲花园', '乙花园']
    assert match_visits == 2

    match_visits = 0
    repeated_numeric = '总价：365万|总价：390万|' + '总价：365万|' * 1000
    value, candidates = parser_module._first_unique_numeric(
        r'总价：([0-9]+)万', repeated_numeric)

    assert value is None
    assert [str(candidate) for candidate in candidates] == ['365', '390']
    assert match_visits == 2


def test_title_source_candidates_treat_canonical_unicode_and_spacing_as_same_value():
    first = 'Cafe\u0301  房源'

    assert _unique_text_values([f' {first} ', 'Café 房源']) == [first]


@pytest.mark.parametrize(('text', 'limit'), [
    ('abc def', 3),
    ('ab  cd', 4),
    ('ab\tcd', 5),
    ('\n a \t b\n', 5),
    ('', 0),
    ('x', 0),
])
def test_normalize_text_prefix_matches_full_whitespace_collapse(text, limit):
    normalized = re.sub(r'\s+', ' ', text)

    assert parser_module._normalize_text_prefix(text, limit) == (
        normalized[:limit], len(normalized) > limit)


def test_normalize_text_prefix_matches_re_sub_for_seeded_unicode_inputs():
    rng = random.Random(20261112)
    alphabet = ('字', 'x', ' ', '\t', '\n', '\r', '\u00a0', '\u2003',
                '\u2028', '\ufeff', '\u200b')

    for _ in range(1000):
        text = ''.join(rng.choice(alphabet) for _ in range(rng.randrange(512)))
        limit = rng.randrange(256)
        normalized = re.sub(r'\s+', ' ', text)

        assert parser_module._normalize_text_prefix(text, limit) == (
            normalized[:limit], len(normalized) > limit)


def test_normalize_text_prefix_matches_re_sub_for_every_unicode_whitespace():
    whitespace = [chr(codepoint) for codepoint in range(0x110000)
                  if re.fullmatch(r'\s', chr(codepoint))]

    for character in whitespace:
        text = f'a{character}{character}b{character}c'
        normalized = re.sub(r'\s+', ' ', text)
        for limit in range(len(normalized) + 2):
            assert parser_module._normalize_text_prefix(text, limit) == (
                normalized[:limit], len(normalized) > limit)


@pytest.mark.parametrize(('source', 'source_url', 'fixture'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html', 'beike_demo.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890', 'anjuke_demo.html'),
])
def test_source_parser_dispatch_uses_conservative_generic_baseline(source, source_url, fixture):
    html = (ROOT / 'fixtures' / fixture).read_text('utf-8')

    result = parse_listing_html(source, source_url, html)

    assert result.fields['source_listing_id'] is not None
    assert result.fields['community_name'] is not None
    assert result.fields['area_sqm'] is not None
    assert result.fields['asking_price_wan'] is not None
    assert result.parser_version == PARSER_VERSION
    assert 'human_review_required' in result.warnings


def test_source_parser_dispatch_rejects_unknown_source():
    with pytest.raises(CollectionError, match='Unsupported collection source'):
        parse_listing_html('other', 'https://example.com/listing/1', '<html>valid page</html>')


@pytest.mark.parametrize(('source', 'source_url', 'fixture', 'expected_id'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html',
     'beike_unavailable_synthetic.html', '109900001234'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/',
     'anjuke_missing_fields_synthetic.html', None),
])
def test_synthetic_unavailable_and_missing_pages_do_not_invent_fields(
        source, source_url, fixture, expected_id):
    html = (ROOT / 'fixtures' / fixture).read_text('utf-8')

    result = parse_listing_html(source, source_url, html)

    assert result.fields['source_listing_id'] == expected_id
    assert result.fields['community_name'] is None
    assert result.fields['area_sqm'] is None
    assert result.fields['asking_price_wan'] is None
    assert not result.ready_for_review
    assert 'missing_community_name' in result.warnings
    assert 'missing_area_sqm' in result.warnings
    assert 'missing_asking_price_wan' in result.warnings
    if expected_id is None:
        assert 'missing_source_listing_id' in result.warnings


def test_beike_sample_is_review_candidate():
    html=(ROOT/'fixtures/beike_demo.html').read_text('utf-8')
    result=parse_listing_html('beike','https://nb.ke.com/ershoufang/109900001234.html',html)
    assert result.fields['source_listing_id']=='109900001234'
    assert result.fields['community_name']=='东湖花园'
    assert result.fields['area_sqm']==158.6
    assert result.fields['asking_price_wan']==365.0
    assert result.fields['bedrooms']==4
    assert result.ready_for_review
    assert 'human_review_required' in result.warnings
    id_mention = result.fields['field_evidence']['source_listing_id']['mentions'][0]
    assert id_mention['source'] == 'source_url'
    assert id_mention['quote'][id_mention['start_char']:id_mention['end_char']] == '109900001234'


def test_parser_preserves_community_names_longer_than_28_characters():
    community = '东湖花园' + '南' * 25
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        f'<html><body><main>小区：{community} 建筑面积：160㎡ 总价：365万'
        '</main></body></html>')

    assert result.fields['community_name'] == community


def test_parser_stops_community_name_before_adjacent_inline_field_label():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：<span>东湖花园</span><span>建筑面积：</span>'
        '<span>160㎡</span><span>总价：</span><span>365万</span>'
        '</main></body></html>')

    assert result.fields['community_name'] == '东湖花园'


def test_parser_marks_adjacent_community_labels_as_ambiguous():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园<span>小区：</span><span>锦港府</span>'
        '建筑面积：160㎡ 总价：365万</main></body></html>')

    assert result.fields['community_name'] is None
    assert 'multiple_community_mentions' in result.warnings


def test_parser_does_not_truncate_community_name_over_model_limit():
    community = '南' * 181
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        f'<html><body><main>小区：{community} 建筑面积：160㎡ 总价：365万'
        '</main></body></html>')

    assert result.fields['community_name'] is None
    assert 'missing_community_name' in result.warnings


def test_parser_stops_floor_value_before_adjacent_decoration_label():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万'
        '<span>楼层：</span><span>高楼层</span><span>装修：</span><span>精装</span>'
        '</main></body></html>')

    assert result.fields['floor_text'] == '高楼层'
    assert result.fields['decoration'] == '精装'


def test_parser_preserves_floor_and_decoration_values_over_20_characters():
    floor = '高楼层' + '东' * 20
    decoration = '精装' + '品质' * 10
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 '
        f'楼层：{floor} 装修：{decoration}'
        '</main></body></html>')

    assert result.fields['floor_text'] == floor
    assert result.fields['decoration'] == decoration


def test_parser_preserves_floor_level_and_total_floor_with_spaces():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 '
        '楼层：高楼层 14/18层 装修：精装</main></body></html>')

    assert result.fields['floor_text'] == '高楼层 14/18层'
    assert result.fields['decoration'] == '精装'
    floor_evidence = result.fields['field_evidence']['floor_text']
    assert floor_evidence['value'] == '高楼层 14/18层'
    assert floor_evidence['mentions'][0]['candidate_value'] == '高楼层 14/18层'
    assert floor_evidence['mentions'][0]['quote'] == '楼层：高楼层 14/18层'


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
def test_separate_total_floor_label_does_not_conflict_with_floor_level(source, source_url):
    result = parse_listing_html(source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：120㎡ 总价：300万 '
        '所在楼层：中楼层 总楼层：18层</main></body></html>')

    assert result.fields['floor_text'] == '中楼层'
    assert 'multiple_floor_mentions' not in result.warnings


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
def test_total_floor_without_listing_level_is_not_used_as_floor_text(source, source_url):
    result = parse_listing_html(source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：120㎡ 总价：300万 '
        '总楼层：18层</main></body></html>')

    assert result.fields['floor_text'] is None


def test_parser_stops_floor_value_at_ideographic_comma():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 '
        '楼层：高楼层、装修：精装</main></body></html>')

    assert result.fields['floor_text'] == '高楼层'


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize(('label', 'value'), [
    ('装修情况', '精装'),
    ('装修状况', '简装'),
    ('装修状态', '毛坯'),
])
def test_extended_decoration_labels_preserve_the_value(source, source_url, label, value):
    result = parse_listing_html(source, source_url,
        f'<html><body><main>小区：东湖花园 建筑面积：120㎡ 总价：300万 '
        f'{label}：{value}</main></body></html>')

    assert result.fields['decoration'] == value
    assert 'multiple_decoration_mentions' not in result.warnings
    evidence = result.fields['field_evidence']['decoration']
    assert evidence['value'] == value
    mention = evidence['mentions'][0]
    assert mention['candidate_value'] == value
    assert mention['quote'] == f'{label}：{value}'
    excerpt = result.fields['evidence_excerpt']
    assert excerpt[mention['start_char']:mention['end_char']] == mention['quote']


def test_parser_ignores_menu_listing_details_that_conflict_with_main_content():
    html = ('''<html><body><main>
      <div>小区：东湖花园</div><div>建筑面积：160㎡</div><div>总价：365万</div>
      <menu><li>小区：月湖花园</li><li>建筑面积：99㎡</li><li>总价：888万</li></menu>
    </main></body></html>''')

    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['community_name'] == '东湖花园'
    assert result.fields['area_sqm'] == 160
    assert result.fields['asking_price_wan'] == 365
    assert 'multiple_price_mentions' not in result.warnings
    assert not any(warning.startswith('multiple_') for warning in result.warnings)


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize('area_sqm', ['0.1', '9.99'])
def test_parser_accepts_positive_areas_below_ten_square_metres(
        source, source_url, area_sqm):
    html = (f'<html><body><main>小区：东湖花园 建筑面积：{area_sqm}㎡ '
            '总价：365万</main></body></html>')

    result = parse_listing_html(source, source_url, html)

    assert result.fields['area_sqm'] == float(area_sqm)
    assert 'missing_area_sqm' not in result.warnings
    assert result.ready_for_review


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
def test_parser_accepts_ping_as_a_square_metre_area_unit(source, source_url):
    result = parse_listing_html(source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：100平 总价：365万'
        '</main></body></html>')

    assert result.fields['area_sqm'] == 100
    assert 'missing_area_sqm' not in result.warnings
    assert result.ready_for_review


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize('area_text', [
    '约100㎡', '大约100平方米', '100㎡左右', '100㎡以上', '100㎡起',
    '不超过100㎡', '100㎡以内', '大于100㎡', '超过100㎡', '高于100㎡',
    '多于100㎡', '小于100㎡', '低于100㎡', '不满100㎡', '100㎡封顶',
    '100㎡起步', '100㎡+', '100㎡＋', '在100㎡左右', '参考100㎡',
    '估算100㎡', '估计100㎡', '预估100㎡',
    '100㎡参考', '100㎡估算', '100㎡估计', '100㎡预估',
])
def test_non_exact_area_is_left_blank_with_complete_evidence(
        source, source_url, area_text):
    result = parse_listing_html(source, source_url,
        f'<html><body><main>小区：东湖花园 建筑面积：{area_text} 总价：365万'
        '</main></body></html>')

    assert result.fields['area_sqm'] is None
    assert 'non_exact_area_sqm' in result.warnings
    assert 'missing_area_sqm' in result.warnings
    assert result.ready_for_review is False
    evidence = result.fields['field_evidence']['area_sqm']
    assert evidence['value'] is None
    assert evidence['mentions'][0]['candidate_value'] in area_text
    assert evidence['mentions'][0]['quote'] == f'建筑面积：{area_text}'
    assert evidence['mentions'][0]['is_non_exact'] is True


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize(('area_markup', 'area_text'), [
    ('≥100㎡', '≥100㎡'),
    ('&gt;=100㎡', '>=100㎡'),
    ('&gt;100㎡', '>100㎡'),
    ('&lt;=100㎡', '<=100㎡'),
    ('&lt;100㎡', '<100㎡'),
])
def test_area_inequality_symbols_are_preserved_as_non_exact_evidence(
        source, source_url, area_markup, area_text):
    html = ('<html><body><main>小区：东湖花园 建筑面积：'
            f'{area_markup} 总价：365万</main></body></html>')
    result = parse_listing_html(source, source_url, html)

    assert result.fields['area_sqm'] is None
    assert 'non_exact_area_sqm' in result.warnings
    evidence = result.fields['field_evidence']['area_sqm']
    assert evidence['mentions'][0]['candidate_value'] == '100'
    assert evidence['mentions'][0]['quote'] == f'建筑面积：{area_text}'
    assert evidence['mentions'][0]['is_non_exact'] is True
    assert result.ready_for_review is False


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize(('area_text', 'candidate', 'range_warning'), [
    ('约建筑面积：100㎡', '100', False),
    ('估算建面：100㎡', '100', False),
    ('参考建筑面积：100㎡-120㎡', '100㎡-120㎡', True),
])
def test_area_qualifier_before_label_is_preserved_as_non_exact_evidence(
        source, source_url, area_text, candidate, range_warning):
    result = parse_listing_html(source, source_url,
        f'<html><body><main>小区：东湖花园 {area_text} 总价：365万'
        '</main></body></html>')

    assert result.fields['area_sqm'] is None
    assert 'non_exact_area_sqm' in result.warnings
    assert ('multiple_area_mentions' in result.warnings) is range_warning
    evidence = result.fields['field_evidence']['area_sqm']
    assert evidence['mentions'][0]['candidate_value'] == candidate
    assert evidence['mentions'][0]['quote'] == area_text
    assert evidence['mentions'][0]['is_non_exact'] is True
    assert result.ready_for_review is False


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize(('field', 'text', 'warning', 'candidate'), [
    ('area_sqm', '建筑面积约：100㎡', 'non_exact_area_sqm', '100'),
    ('area_sqm', '建筑面积估算：100㎡', 'non_exact_area_sqm', '100'),
    ('area_sqm', '建筑面积约：100㎡-120㎡', 'non_exact_area_sqm', '100㎡-120㎡'),
    ('area_sqm', '建筑面积估算：100㎡-120㎡', 'non_exact_area_sqm', '100㎡-120㎡'),
    ('asking_price_wan', '挂牌价约：200万', 'non_exact_asking_price', '200'),
    ('asking_price_wan', '总价估算：200万', 'non_exact_asking_price', '200'),
    ('asking_price_wan', '挂牌价约：300-320万', 'non_exact_asking_price', '300-320万'),
    ('asking_price_wan', '总价估算：300万-320万', 'non_exact_asking_price', '300万-320万'),
])
def test_qualifier_followed_by_colon_keeps_non_exact_evidence(
        source, source_url, field, text, warning, candidate):
    result = parse_listing_html(
        source, source_url,
        f'<html><body><main>小区：东湖花园 {text} 户型：3室</main></body></html>')

    assert result.fields[field] is None
    assert warning in result.warnings
    evidence = result.fields['field_evidence'][field]
    assert evidence['mentions'][0]['candidate_value'] == candidate
    assert evidence['mentions'][0]['quote'] == text
    assert evidence['mentions'][0]['is_non_exact'] is True
    assert result.ready_for_review is False


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
def test_exact_area_evidence_is_marked_not_non_exact(source, source_url):
    result = parse_listing_html(source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：100㎡ 总价：365万'
        '</main></body></html>')

    assert result.fields['area_sqm'] == 100
    assert result.fields['field_evidence']['area_sqm']['mentions'][0]['is_non_exact'] is False


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
def test_area_copula_preserves_exact_area_value(source, source_url):
    result = parse_listing_html(source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积为100㎡ 总价：365万'
        '</main></body></html>')

    assert result.fields['area_sqm'] == 100
    assert result.fields['field_evidence']['area_sqm']['mentions'][0]['quote'] == '建筑面积为100㎡'
    assert result.fields['field_evidence']['area_sqm']['mentions'][0]['is_non_exact'] is False


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
def test_exact_area_followed_by_living_room_text_is_not_a_lower_bound(source, source_url):
    result = parse_listing_html(source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：100㎡起居室宽敞 总价：365万'
        '</main></body></html>')

    assert result.fields['area_sqm'] == 100
    assert 'non_exact_area_sqm' not in result.warnings
    assert result.fields['field_evidence']['area_sqm']['mentions'][0]['is_non_exact'] is False


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize('after_qualifier', ['、采光好', '（含赠送面积）'])
def test_area_lower_bound_survives_following_punctuation(source, source_url, after_qualifier):
    result = parse_listing_html(source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：100㎡起'
        f'{after_qualifier} 总价：365万</main></body></html>')

    assert result.fields['area_sqm'] is None
    assert 'non_exact_area_sqm' in result.warnings
    assert result.fields['field_evidence']['area_sqm']['mentions'][0]['is_non_exact'] is True


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize('area_text', ['约100-120平方米', '100-120㎡以上'])
def test_non_exact_area_range_preserves_full_candidate_evidence(
        source, source_url, area_text):
    result = parse_listing_html(source, source_url,
        f'<html><body><main>小区：东湖花园 建筑面积：{area_text} 总价：365万'
        '</main></body></html>')

    assert result.fields['area_sqm'] is None
    assert {'multiple_area_mentions', 'non_exact_area_sqm'} <= set(result.warnings)
    evidence = result.fields['field_evidence']['area_sqm']
    assert evidence['mentions'][0]['candidate_value'] == area_text.replace('约', '').replace('以上', '')
    assert evidence['mentions'][0]['quote'] == f'建筑面积：{area_text}'
    assert evidence['mentions'][0]['is_non_exact'] is True


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
def test_square_area_abbreviation_is_preserved_in_field_evidence(source, source_url):
    result = parse_listing_html(source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：100平方 总价：365万'
        '</main></body></html>')

    evidence = result.fields['field_evidence']['area_sqm']
    assert evidence['mentions'][0]['candidate_value'] == '100'
    assert evidence['mentions'][0]['quote'] == '建筑面积：100平方'


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize('price_wan', ['0.1', '0.99'])
def test_parser_accepts_positive_prices_below_one_wan(source, source_url, price_wan):
    html = (f'<html><body><main>小区：东湖花园 建筑面积：120㎡ '
            f'总价：{price_wan}万</main></body></html>')

    result = parse_listing_html(source, source_url, html)

    assert result.fields['asking_price_wan'] == float(price_wan)
    assert 'missing_asking_price_wan' not in result.warnings
    assert result.ready_for_review


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize(('field_label', 'field_name'), [
    ('建筑面积：0㎡', 'area_sqm'),
    ('总价：0万', 'asking_price_wan'),
])
def test_parser_rejects_zero_area_and_price(source, source_url, field_label, field_name):
    supporting_field = '总价：365万' if field_name == 'area_sqm' else '建筑面积：120㎡'
    html = (f'<html><body><main>小区：东湖花园 {supporting_field} '
            f'{field_label}</main></body></html>')

    result = parse_listing_html(source, source_url, html)

    assert result.fields[field_name] is None


def test_parser_preserves_values_that_exceed_database_scale_but_blocks_review_ready():
    html = ('<html><body><main>小区：东湖花园 建筑面积：160.005㎡ 总价：365.005万'
            '</main></body></html>')

    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['area_sqm'] == 160.005
    assert result.fields['asking_price_wan'] == 365.005
    assert 'numeric_precision_requires_correction:area_sqm' in result.warnings
    assert 'numeric_precision_requires_correction:asking_price_wan' in result.warnings
    assert result.ready_for_review is False


def test_parser_checks_numeric_scale_before_float_conversion():
    html = ('<html><body><main>小区：东湖花园 建筑面积：160.00000000000000001㎡ '
            '总价：365.00000000000000001万</main></body></html>')

    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['area_sqm'] == 160.0
    assert result.fields['asking_price_wan'] == 365.0
    assert 'numeric_precision_requires_correction:area_sqm' in result.warnings
    assert 'numeric_precision_requires_correction:asking_price_wan' in result.warnings
    assert result.ready_for_review is False


def test_parser_accepts_long_decimal_scale_when_extra_digits_are_zero():
    html = ('<html><body><main>小区：东湖花园 建筑面积：160.0000000000000000000000000000000000000000000000㎡ '
            '总价：365.0000000000000000000000000000000000000000000000万</main></body></html>')

    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['area_sqm'] == 160.0
    assert result.fields['asking_price_wan'] == 365.0
    assert not any(warning.startswith('numeric_precision_requires_correction:')
                   for warning in result.warnings)
    assert result.ready_for_review is True


def test_numeric_range_check_precedes_float_rounding_at_upper_bound():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 '
        '建筑面积：20000.000000000000000001㎡ '
        '总价：200000.000000000000001万'
        '</main></body></html>')

    assert result.fields['area_sqm'] is None
    assert result.fields['asking_price_wan'] is None
    assert 'missing_area_sqm' in result.warnings
    assert 'missing_asking_price_wan' in result.warnings
    assert 'numeric_precision_requires_correction:area_sqm' in result.warnings
    assert 'numeric_precision_requires_correction:asking_price_wan' in result.warnings


def test_positive_numeric_values_below_the_old_lower_bounds_are_retained():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 '
        '建筑面积：9.999999999999999999㎡ '
        '总价：0.999999999999999999万'
        '</main></body></html>')

    assert result.fields['area_sqm'] == 10.0
    assert result.fields['asking_price_wan'] == 1.0
    assert 'missing_area_sqm' not in result.warnings
    assert 'missing_asking_price_wan' not in result.warnings
    assert 'numeric_precision_requires_correction:area_sqm' in result.warnings
    assert 'numeric_precision_requires_correction:asking_price_wan' in result.warnings
    assert not result.ready_for_review


def test_positive_values_that_underflow_float_are_not_emitted_as_zero():
    tiny = '0.' + '0' * 400 + '1'
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        f'<html><body><main>小区：东湖花园 建筑面积：{tiny}㎡ 总价：{tiny}万'
        '</main></body></html>')

    assert result.fields['area_sqm'] is None
    assert result.fields['asking_price_wan'] is None
    assert 'missing_area_sqm' in result.warnings
    assert 'missing_asking_price_wan' in result.warnings


@pytest.mark.parametrize(('area', 'price', 'expected_area', 'expected_price'), [
    ('10.00', '365.00', 10, 365),
    ('20000.00', '365.00', 20000, 365),
    ('160.00', '1.00', 160, 1),
    ('160.00', '200000.00', 160, 200000),
])
def test_numeric_range_boundaries_remain_inclusive(area, price, expected_area, expected_price):
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        f'<html><body><main>小区：东湖花园 建筑面积：{area}㎡ 总价：{price}万'
        '</main></body></html>')

    assert result.fields['area_sqm'] == expected_area
    assert result.fields['asking_price_wan'] == expected_price
    assert result.ready_for_review is True


def test_parsed_fields_include_visible_text_provenance_without_calibrated_confidence():
    html = ('<html><body><main>本页信息 小区：东湖花园 建筑面积：160㎡ 总价：365万'
            '</main></body></html>')

    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)
    evidence = result.fields['field_evidence']
    text = result.fields['evidence_excerpt']

    assert result.fields['confidence_status'] == 'not_calibrated'
    assert evidence['community_name']['value'] == '东湖花园'
    assert evidence['community_name']['mentions'][0]['source'] == 'visible_listing_text'
    assert evidence['community_name']['mentions'][0]['quote'] == '小区：东湖花园'
    assert evidence['area_sqm']['mentions'][0]['quote'] == '建筑面积：160㎡'
    assert evidence['asking_price_wan']['mentions'][0]['quote'] == '总价：365万'
    for field in evidence.values():
        for item in field['mentions']:
            if item['source'] == 'visible_listing_text':
                assert text[item['start_char']:item['end_char']] == item['quote']
            else:
                assert item['quote'][item['start_char']:item['end_char']] == item['candidate_value']


def test_visible_text_evidence_offsets_remain_relative_to_full_text_after_excerpt_limit():
    prefix = '无关页面说明' * 250
    html = ('<html><body><main>' + prefix
            + '<p>小区：东湖花园</p><p>建筑面积：160㎡</p><p>总价：365万</p>'
            + '</main></body></html>')

    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    normalized_text = re.sub(
        r'\s+', ' ', _text_with_inline_boundaries(BeautifulSoup(html, 'html.parser').main))
    mention = result.fields['field_evidence']['asking_price_wan']['mentions'][0]
    assert len(result.fields['evidence_excerpt']) == 1000
    assert result.fields['evidence_excerpt'] == normalized_text[:1000]
    assert mention['start_char'] >= 1000
    assert normalized_text[mention['start_char']:mention['end_char']] == mention['quote']


def test_community_label_after_compact_punctuation_is_recognized():
    html = ('<html><body><main>挂牌信息|小区：东湖花园；建筑面积：160㎡/总价：365万'
            '</main></body></html>')

    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['community_name'] == '东湖花园'
    assert result.fields['area_sqm'] == 160
    assert result.fields['asking_price_wan'] == 365


def test_community_value_stops_at_compact_field_separator():
    html = ('<html><body><main>小区：东湖花园|建筑面积：160㎡/总价：365万'
            '</main></body></html>')

    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['community_name'] == '东湖花园'
    assert result.fields['area_sqm'] == 160
    assert result.fields['asking_price_wan'] == 365


def test_floor_and_decoration_values_stop_at_compact_separators():
    html = ('<html><body><main>小区：东湖花园 建筑面积：160㎡ 楼层：高楼层|'
            '装修：精装/总价：365万</main></body></html>')

    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['floor_text'] == '高楼层'
    assert result.fields['decoration'] == '精装'
    assert result.fields['asking_price_wan'] == 365


def test_utf8_bom_does_not_hide_first_listing_field():
    html = ('\ufeff<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万'
            '</main></body></html>')

    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['community_name'] == '东湖花园'
    assert result.fields['area_sqm'] == 160
    assert result.fields['asking_price_wan'] == 365


def test_anjuke_sample_is_review_candidate():
    html=(ROOT/'fixtures/anjuke_demo.html').read_text('utf-8')
    result=parse_listing_html('anjuke','https://ningbo.anjuke.com/sale/1234567890',html)
    assert result.fields['community_name']=='锦港府'
    assert result.fields['area_sqm']==142.0
    assert result.fields['asking_price_wan']==398.0
    assert result.ready_for_review


def test_semantic_main_wins_over_earlier_generic_content_class():
    html = ('<html><body><div class="content">页面导航加载提示</div><main>'
            '小区：东湖花园 建筑面积：160㎡ 总价：365万'
            '</main></body></html>')

    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['community_name'] == '东湖花园'
    assert result.fields['area_sqm'] == 160
    assert result.fields['asking_price_wan'] == 365


def test_parser_keeps_inline_html_fragments_of_field_labels_and_values_together():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>'
        '<p><span>小</span><span>区：</span><span>东湖花园</span></p>'
        '<p><span>建</span><span>面：</span><span>160</span><span>㎡</span></p>'
        '<p><span>挂牌</span><span>价：</span><span>365</span><span>万</span></p>'
        '</main></body></html>')

    assert result.fields['community_name'] == '东湖花园'
    assert result.fields['area_sqm'] == 160
    assert result.fields['asking_price_wan'] == 365


def test_parser_does_not_join_label_across_block_level_center_element():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main><center><span>小</span></center>'
        '<span>区：东湖花园</span><p>建筑面积：160㎡</p><p>总价：365万</p>'
        '</main></body></html>')

    assert result.fields['community_name'] is None
    assert 'missing_community_name' in result.warnings
    assert 'community_name' not in result.fields['field_evidence']


@pytest.mark.parametrize(('first_part', 'expected_community'), [
    ('<span style="display:block">小</span>', None),
    ('<div style="display:inline">小</div>', '东湖花园'),
    ('<span style="display: BLOCK!important">小</span>', None),
    ('<span style="display:inline;display:block!important">小</span>', None),
    ('<span style="display:block!important;display:inline">小</span>', None),
    ('<span style="display:table-caption">小</span>', None),
    ('<div style="display:run-in">小</div>', None),
    ('<span style="display:run-in">小</span>', None),
    ('<div style="display:flow">小</div>', None),
    ('<div style="display:inline flow">小</div>', '东湖花园'),
    ('<div style="display:inline flow list-item">小</div>', '东湖花园'),
    ('<div style="display:inline   flow list-item">小</div>', '东湖花园'),
    ('<div style="display:inline\u00a0flow">小</div>', None),
])
def test_parser_uses_inline_display_for_text_boundaries(first_part, expected_community):
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>' + first_part
        + '<span>区：东湖花园</span><p>建筑面积：160㎡</p><p>总价：365万</p>'
        + '</main></body></html>')

    assert result.fields['community_name'] == expected_community


def test_parser_inlines_run_in_into_following_block_text():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main><span style="display:run-in">小</span>'
        '<p><span>区：东湖花园</span></p><p>建筑面积：160㎡</p>'
        '<p>总价：365万</p></main></body></html>')

    assert result.fields['community_name'] == '东湖花园'


def test_parser_inlines_run_in_sequence_into_following_block_text():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main><span style="display:run-in">小</span>'
        '<span style="display:run-in">区：</span>'
        '<p>东湖花园</p><p>建筑面积：160㎡</p><p>总价：365万</p>'
        '</main></body></html>')

    assert result.fields['community_name'] == '东湖花园'


def test_run_in_sibling_analysis_scales_with_node_count(monkeypatch):
    depth = 80
    html = ('<main>' + '<span style="display:run-in">x</span>' * depth
            + '<p>y</p></main>')
    main = BeautifulSoup(html, 'html.parser').main
    original = parser_module._inline_css_value
    display_queries = 0

    def count_display_queries(style, property_name):
        nonlocal display_queries
        if property_name == 'display':
            display_queries += 1
        return original(style, property_name)

    monkeypatch.setattr(parser_module, '_inline_css_value', count_display_queries)

    text = _text_with_inline_boundaries(main)

    assert 'x' * depth + 'y' in text
    assert display_queries <= depth * 4 + 30


def test_unresolved_inline_visibility_text_scan_scales_with_node_count(monkeypatch):
    depth = 80
    html = ('<main>' + '<div style="display:block">x' * (depth - 1)
            + '<span style="display:var(--display)">x</span>'
            + '</div>' * (depth - 1) + '</main>')
    main = BeautifulSoup(html, 'html.parser').main
    original = Tag._all_strings
    original_children = Tag.children.fget
    string_visits = 0
    child_visits = 0

    def count_string_visits(self, *args, **kwargs):
        nonlocal string_visits
        for value in original(self, *args, **kwargs):
            string_visits += 1
            yield value

    def count_child_visits(self):
        nonlocal child_visits
        for child in original_children(self):
            child_visits += 1
            yield child

    monkeypatch.setattr(Tag, '_all_strings', count_string_visits)
    monkeypatch.setattr(Tag, 'children', property(count_child_visits))

    assert parser_module._has_unresolved_inline_visibility(main)
    assert string_visits <= depth * 3
    assert child_visits <= depth * 5


def test_parser_keeps_preceding_inline_text_outside_inlinified_run_in():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>提示<span style="display:run-in">小</span>'
        '<p>区：东湖花园</p><p>建筑面积：160㎡</p>'
        '<p>总价：365万</p></main></body></html>')

    assert result.fields['community_name'] is None


def test_parser_does_not_inline_run_in_into_new_formatting_context():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main><span style="display:run-in">小</span>'
        '<p style="display:block flow-root">区：东湖花园</p>'
        '<p>建筑面积：160㎡</p><p>总价：365万</p></main></body></html>')

    assert result.fields['community_name'] is None


def test_parser_resolves_inherited_display_when_separating_text():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main><div style="display:block">'
        '<span>小</span><span style="display:inherit">区：</span>'
        '<span>东湖花园</span></div><p>建筑面积：160㎡</p><p>总价：365万</p>'
        '</main></body></html>')

    assert result.fields['community_name'] is None
    assert 'missing_community_name' in result.warnings


def test_inline_text_and_equal_score_sibling_root_conflicts_stay_pending():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>'
        '<p><span>小</span><span>区：东湖花园</span></p>'
        '<p><span>建</span><span>筑面积：</span><span>160</span><span>㎡</span></p>'
        '<p><span>总</span><span>价：365万</span></p>'
        '</main><article>小区：推荐房源 建筑面积：999㎡ 总价：999万</article>'
        '</body></html>')

    assert result.fields['community_name'] is None
    assert result.fields['area_sqm'] is None
    assert result.fields['asking_price_wan'] is None
    assert {'multiple_community_mentions', 'multiple_area_mentions',
            'multiple_price_mentions'} <= set(result.warnings)
    assert not result.ready_for_review


def test_parser_ignores_html_comments_when_joining_visible_text():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ '
        '<!-- 推荐房源总价：900万 -->挂牌价：365万</main></body></html>')

    assert result.fields['asking_price_wan'] == 365


def test_dom_walks_read_existing_contents_without_copying_children(monkeypatch):
    soup = BeautifulSoup(
        '<main><span>东湖</span><span hidden>隐藏广告一</span>'
        '<span style="display:none">隐藏广告二</span>'
        '<span style="visibility:hidden">广告<b>推荐</b>尾</span>'
        '<span>花园</span></main>',
        'html.parser')

    def copied_children_is_forbidden(_tag):
        raise AssertionError('text walk should read the existing contents list')

    monkeypatch.setattr(Tag, 'children', property(copied_children_is_forbidden))

    parser_module._remove_non_visible_tags(soup)
    parser_module._remove_inline_invisible_text(soup)
    assert not parser_module._has_unresolved_inline_visibility(soup)
    assert _text_with_inline_boundaries(soup.main).strip() == '东湖花园'


def test_nonempty_article_is_used_when_main_is_empty():
    html = ('<html><body><main></main><article>'
            '小区：东湖花园 建筑面积：160㎡ 总价：365万'
            '</article></body></html>')

    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['community_name'] == '东湖花园'
    assert result.fields['area_sqm'] == 160
    assert result.fields['asking_price_wan'] == 365


def test_listing_article_wins_over_non_listing_main_shell():
    html = ('<html><body><main>页面信息正在加载</main><article>'
            '小区：东湖花园 建筑面积：160㎡ 总价：365万'
            '</article></body></html>')

    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['community_name'] == '东湖花园'
    assert result.fields['area_sqm'] == 160
    assert result.fields['asking_price_wan'] == 365


@pytest.mark.parametrize('bad',[ 'http://nb.ke.com/ershoufang/109900001234.html',
    'https://evil.com/ershoufang/109900001234.html',
    'https://nb.ke.com.evil.com/ershoufang/109900001234.html',
    'https://sh.ke.com/ershoufang/109900001234.html',
    'https://www.ke.com/ershoufang/109900001234.html',
    'https://hangzhou.anjuke.com/sale/1234567890',
    'https://anjuke.com/sale/1234567890',
    'https://nb.ke.com../ershoufang/109900001234.html',
    'https://nb.ke.com.../ershoufang/109900001234.html',
    'https://user:pass@nb.ke.com/ershoufang/109900001234.html',
    'https://@nb.ke.com/ershoufang/109900001234.html',
    'https://:@nb.ke.com/ershoufang/109900001234.html',
    'https://nb.ke.com:9000/ershoufang/109900001234.html',
    'https://[::1/ershoufang/109900001234.html'])
def test_bad_source_url_rejected(bad):
    with pytest.raises(CollectionError):
        check_source_url('beike',bad)


@pytest.mark.parametrize('url', [
    'https://hangzhou.anjuke.com/sale/1234567890',
    'https://anjuke.com/sale/1234567890',
])
def test_anjuke_rejects_non_ningbo_source_hosts(url):
    with pytest.raises(CollectionError):
        check_source_url('anjuke', url)


@pytest.mark.parametrize('suffix', ['?token=private', '#tracking-fragment', '?', '#'])
def test_source_url_rejects_query_and_fragment(suffix):
    with pytest.raises(CollectionError, match='query and fragment'):
        check_source_url('beike', 'https://nb.ke.com/ershoufang/109900001234.html' + suffix)


@pytest.mark.parametrize('url', [
    ' https://nb.ke.com/ershoufang/109900001234.html',
    'https://nb.ke.com/ershoufang/109900001234.html ',
    'https://nb.ke.com/ershoufang/109900001234.html\n',
    'https://nb.ke.com/ershoufang/109900001234.html\t',
    'https://nb.ke.com/ershoufang/\x00109900001234.html',
    'https://nb.ke.com/ershoufang/109900001234.html\x7f',
])
def test_source_url_rejects_whitespace_and_control_characters(url):
    with pytest.raises(CollectionError, match='whitespace or control'):
        check_source_url('beike', url)


def test_source_url_obeys_api_character_limit():
    overlong = 'https://nb.ke.com/' + 'a' * 2000
    with pytest.raises(CollectionError, match='12 and 2000 characters'):
        check_source_url('beike', overlong)


def test_source_url_allows_single_dns_root_dot():
    url = 'https://nb.ke.com./ershoufang/109900001234.html'
    assert check_source_url('beike', url) == url


def test_missing_stable_detail_id_stays_pending():
    result=parse_listing_html('beike','https://nb.ke.com/ershoufang/',
        '<html><body><main>小区：东湖花园 面积：160㎡ 总价：365万</main></body></html>')
    assert result.fields['source_listing_id'] is None
    assert not result.ready_for_review


def test_canonical_url_conflicting_listing_id_stays_pending():
    result=parse_listing_html('beike','https://nb.ke.com/ershoufang/109900001234.html',
        '<html><head><link rel="canonical" '
        'href="/ershoufang/109900009999.html?tracking=do-not-copy"></head><body><main>'
        '小区：东湖花园 建筑面积：160㎡ 总价：365万'
        '</main></body></html>')

    assert result.fields['source_listing_id'] is None
    assert 'canonical_source_id_mismatch' in result.warnings
    assert result.parser_version == PARSER_VERSION
    evidence = result.fields['field_evidence']['source_listing_id']
    assert evidence['value'] is None
    assert [item['candidate_value'] for item in evidence['mentions']] == [
        '109900001234', '109900009999']
    assert [item['source'] for item in evidence['mentions']] == ['source_url','canonical_url']
    assert all('tracking' not in item['quote'] for item in evidence['mentions'])
    assert all(item['quote'][item['start_char']:item['end_char']] == item['candidate_value']
               for item in evidence['mentions'])
    assert not result.ready_for_review


def test_canonical_rel_keyword_is_ascii_case_insensitive():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><head><link rel="alternate CANONICAL" '
        'href="/ershoufang/109900009999.html"></head><body><main>'
        '小区：东湖花园 建筑面积：160㎡ 总价：365万'
        '</main></body></html>')

    assert result.fields['source_listing_id'] is None
    assert 'canonical_source_id_mismatch' in result.warnings


def test_og_url_conflicting_listing_id_stays_pending():
    result=parse_listing_html('anjuke','https://ningbo.anjuke.com/sale/1234567890',
        '<html><head><meta property="og:url" '
        'content="https://ningbo.anjuke.com/sale/9876543210"></head><body><main>'
        '小区：锦港府 建筑面积：142㎡ 总价：398万'
        '</main></body></html>')

    assert result.fields['source_listing_id'] is None
    assert 'canonical_source_id_mismatch' in result.warnings
    assert not result.ready_for_review


@pytest.mark.parametrize('source,source_url,canonical', [
    ('beike', 'https://nb.ke.com/ershoufang/',
     '<link rel="canonical" href="/ershoufang/109900001234.html">'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/',
     '<meta property="og:url" content="https://ningbo.anjuke.com/sale/1234567890">'),
])
def test_unique_canonical_detail_id_fills_missing_source_url_id(source, source_url, canonical):
    content = ('小区：东湖花园 建筑面积：160㎡ 总价：365万' if source == 'beike'
               else '小区：锦港府 建筑面积：142㎡ 总价：398万')
    result = parse_listing_html(source, source_url,
        f'<html><head>{canonical}</head><body><main>{content}</main></body></html>')

    assert result.fields['source_listing_id'] == (
        '109900001234' if source == 'beike' else '1234567890')
    assert 'missing_source_listing_id' not in result.warnings
    evidence = result.fields['field_evidence']['source_listing_id']
    assert evidence['value'] == result.fields['source_listing_id']
    assert evidence['mentions'][0]['source'] == 'canonical_url'
    assert evidence['mentions'][0]['quote'][evidence['mentions'][0]['start_char']:
                                             evidence['mentions'][0]['end_char']] == evidence['value']
    assert result.ready_for_review


def test_canonical_source_id_evidence_strips_query_and_fragment():
    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/',
        '<html><head><link rel="canonical" '
        'href="/secret-segment/ershoufang/109900001234.html?session=private#details"></head><body><main>'
        '小区：东湖花园 建筑面积：160㎡ 总价：365万'
        '</main></body></html>')

    mention = result.fields['field_evidence']['source_listing_id']['mentions'][0]
    assert mention['source'] == 'canonical_url'
    assert mention['quote'] == '/ershoufang/109900001234.html'
    assert mention['quote'][mention['start_char']:mention['end_char']] == '109900001234'


def test_head_identity_and_open_graph_title_share_one_dom_scan(monkeypatch):
    metadata = ''.join(f'<meta name="other-{index}" content="value">'
                       for index in range(100))
    html = ('<html><head>' + metadata
            + '<link rel="canonical" href="/ershoufang/109900001234.html">'
            + '<meta property="og:url" content="https://nb.ke.com/ershoufang/109900001234.html">'
            + '<meta property="og:title" content="东湖花园房源">'
            + '<title>备用标题</title></head><body><main>'
            + '小区：东湖花园 建筑面积：160㎡ 总价：365万'
            + '</main></body></html>')
    original_descendants = Tag.descendants.fget
    head_scans = 0

    def count_head_scans(node):
        nonlocal head_scans
        if node.name == 'head':
            head_scans += 1
        yield from original_descendants(node)

    monkeypatch.setattr(Tag, 'descendants', property(count_head_scans))

    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['title'] == '东湖花园房源'
    assert result.fields['source_listing_id'] == '109900001234'
    assert result.fields['field_evidence']['source_listing_id']['mention_count'] == 3
    assert head_scans == 1


def test_many_canonical_links_are_streamed_with_bounded_evidence(monkeypatch):
    count = 1002
    links = '<link rel="canonical" href="/ershoufang/109900001234.html">' * count
    metadata = ('<meta property="og:url" '
                'content="https://nb.ke.com/ershoufang/109900001234.html">' * count)
    html = ('<html><head>' + links + metadata + '</head><body><main>'
            '小区：东湖花园 建筑面积：160㎡ 总价：365万'
            '</main></body></html>')
    original_find_all = Tag.find_all

    def reject_materialized_canonical_queries(self, *args, **kwargs):
        if args and args[0] in ('link', 'meta'):
            raise AssertionError('canonical links must be processed without a result list')
        if kwargs.get('attrs') == {'property': 'og:url'}:
            raise AssertionError('og:url tags must be processed without a result list')
        return original_find_all(self, *args, **kwargs)

    monkeypatch.setattr(Tag, 'find_all', reject_materialized_canonical_queries)

    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    evidence = result.fields['field_evidence']['source_listing_id']
    assert result.fields['source_listing_id'] == '109900001234'
    assert evidence['mention_count'] == count * 2 + 1
    assert len(evidence['mentions']) == 20
    assert evidence['mentions_truncated'] is True


def test_late_canonical_conflict_is_detected_after_repeated_matching_ids():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><head>'
        '<link rel="canonical" href="/ershoufang/109900001234.html">'
        '<link rel="canonical" href="/ershoufang/109900001234.html">'
        '<link rel="canonical" href="/ershoufang/109900009999.html">'
        '</head><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万'
        '</main></body></html>')

    assert result.fields['source_listing_id'] is None
    assert 'canonical_source_id_mismatch' in result.warnings


def test_conflicting_canonical_ids_without_source_url_id_stay_pending():
    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/',
        '<html><head><link rel="canonical" href="/ershoufang/109900001234.html">'
        '<meta property="og:url" content="https://nb.ke.com/ershoufang/109900009999.html">'
        '</head><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万'
        '</main></body></html>')

    assert result.fields['source_listing_id'] is None
    assert 'canonical_source_id_mismatch' in result.warnings
    assert not result.ready_for_review


def test_malformed_canonical_url_does_not_abort_parsing():
    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><head><link rel="canonical" href="https://[::1/bad"></head><body><main>'
        '小区：东湖花园 建筑面积：160㎡ 总价：365万'
        '</main></body></html>')

    assert result.fields['source_listing_id'] == '109900001234'


@pytest.mark.parametrize('html', [
    '<html><body><main><div>小区：东湖花园<p>建筑面积：160㎡<span>总价：365万</main>',
    '<html><body><main>小区：东湖花园</section><p>建筑面积：160㎡</div>'
    '<p>总价：365万</body>',
    '<main><div><p>小区：东湖花园</div><span>建筑面积：160㎡</p>'
    '<em>总价：365万</main>',
])
def test_parser_tolerates_unclosed_and_mismatched_html_tags(html):
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['community_name'] == '东湖花园'
    assert result.fields['area_sqm'] == 160
    assert result.fields['asking_price_wan'] == 365
    assert result.fields['source_listing_id'] == '109900001234'
    assert 'human_review_required' in result.warnings


def test_canonical_id_mismatch_is_still_checked_when_canonical_has_query():
    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><head><link rel="canonical" '
        'href="/ershoufang/109900009999.html?tracking=private"></head><body><main>'
        '小区：东湖花园 建筑面积：160㎡ 总价：365万'
        '</main></body></html>')

    assert result.fields['source_listing_id'] is None
    assert 'canonical_source_id_mismatch' in result.warnings


def test_any_conflicting_canonical_declaration_stays_pending():
    result=parse_listing_html('beike','https://nb.ke.com/ershoufang/109900001234.html',
        '<html><head><link rel="canonical" '
        'href="/ershoufang/109900001234.html">'
        '<link rel="canonical" href="/ershoufang/109900009999.html">'
        '</head><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万'
        '</main></body></html>')

    assert result.fields['source_listing_id'] is None
    assert 'canonical_source_id_mismatch' in result.warnings
    assert not result.ready_for_review


def test_conflicting_prices_do_not_choose_one():
    result=parse_listing_html('beike','https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 总价：390万</main></body></html>')
    assert result.fields['asking_price_wan'] is None
    assert 'multiple_price_mentions' in result.warnings
    evidence = result.fields['field_evidence']['asking_price_wan']
    assert evidence['value'] is None
    assert [item['candidate_value'] for item in evidence['mentions']] == ['365', '390']
    assert evidence['mention_count'] == 2
    assert not result.ready_for_review


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/12345678'),
])
@pytest.mark.parametrize('price_text', ['2万', '2-3万', '2万元', '2-3万元'])
@pytest.mark.parametrize('price_suffix', [
    '/㎡', '/m²', '/平米', '/平方米', '/平', '每平方米', '／㎡', '／平米', '每平',
])
def test_unit_price_is_not_parsed_as_total_asking_price(
        source, source_url, price_text, price_suffix):
    result = parse_listing_html(
        source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：100㎡ '
        f'挂牌价：{price_text}{price_suffix}</main></body></html>')

    assert result.fields['asking_price_wan'] is None
    assert 'missing_asking_price_wan' in result.warnings
    assert 'multiple_price_mentions' not in result.warnings
    assert not result.ready_for_review


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/12345678'),
])
@pytest.mark.parametrize(('price_text', 'price_suffix'), [
    ('2万', '（元/㎡）'), ('2-3万', '（元/㎡）'),
    ('2万', '(元/㎡)'), ('2-3万', '(元/㎡)'),
    ('2万', '（每平方米）'), ('2-3万', '（每平方米）'),
    ('2万', '(/平米)'), ('2-3万', '(/平米)'),
    ('2万元', '（每平方米）'), ('2-3万元', '（每平方米）'),
])
def test_parenthesized_unit_price_is_not_total_price(
        source, source_url, price_text, price_suffix):
    result = parse_listing_html(
        source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：100㎡ '
        f'挂牌价：{price_text}{price_suffix}</main></body></html>')

    assert result.fields['asking_price_wan'] is None
    assert 'missing_asking_price_wan' in result.warnings
    assert 'multiple_price_mentions' not in result.warnings


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/12345678'),
])
def test_unit_price_does_not_hide_an_explicit_total_asking_price(source, source_url):
    result = parse_listing_html(
        source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：100㎡ '
        '总价：200万 挂牌价：2万/㎡</main></body></html>')

    assert result.fields['asking_price_wan'] == 200.0
    assert 'multiple_price_mentions' not in result.warnings


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/12345678'),
])
def test_yuan_suffix_without_area_unit_remains_a_total_asking_price(source, source_url):
    result = parse_listing_html(
        source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：100㎡ '
        '挂牌价：200万元</main></body></html>')

    assert result.fields['asking_price_wan'] == 200.0
    assert 'multiple_price_mentions' not in result.warnings


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/12345678'),
])
@pytest.mark.parametrize('qualifier', [
    '约', '大约', '大概', '左右', '上下', '出头', '以上', '以下', '以内',
    '附近', '不到', '不足', '不超过', '不高于', '不低于', '起', '起价', '起售',
    '起售房源', '起步', '起步价', '起始价', '封顶', '+', '＋',
])
def test_qualified_price_is_not_emitted_as_an_exact_listing_price(
        source, source_url, qualifier):
    result = parse_listing_html(
        source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：100㎡ '
        f'挂牌价：200万元{qualifier}</main></body></html>')

    assert result.fields['asking_price_wan'] is None
    assert 'non_exact_asking_price' in result.warnings
    assert result.fields['field_evidence']['asking_price_wan']['value'] is None
    assert result.fields['field_evidence']['asking_price_wan']['mentions'][0][
        'candidate_value'] == '200'
    assert result.fields['field_evidence']['asking_price_wan']['mentions'][0][
        'quote'] == f'挂牌价：200万元{qualifier}'
    assert not result.ready_for_review


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/12345678'),
])
@pytest.mark.parametrize('qualifier', [
    '约', '大约', '大概', '参考', '估算', '预估', '左右', '上下', '出头', '以上',
    '以下', '以内', '不到', '不足', '不超过', '不高于', '不低于', '至少', '至多', '在',
    '最低', '最高', '起步价', '起始价', '>=', '<=', '>', '≥', '≤',
])
def test_leading_price_qualifier_is_not_emitted_as_an_exact_listing_price(
        source, source_url, qualifier):
    result = parse_listing_html(
        source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：100㎡ '
        f'挂牌价：{qualifier}200万</main></body></html>')

    assert result.fields['asking_price_wan'] is None
    assert 'non_exact_asking_price' in result.warnings
    evidence = result.fields['field_evidence']['asking_price_wan']
    assert evidence['value'] is None
    assert evidence['mentions'][0]['candidate_value'] == '200'
    assert not result.ready_for_review


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/12345678'),
])
@pytest.mark.parametrize('price_text', [
    '挂牌价为约200万', '挂牌价约为200万', '挂牌价在200万左右', '总价为约200万',
])
def test_price_copula_and_location_qualifiers_stay_non_exact(source, source_url, price_text):
    result = parse_listing_html(
        source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：100㎡ '
        f'{price_text}</main></body></html>')

    assert result.fields['asking_price_wan'] is None
    assert 'non_exact_asking_price' in result.warnings
    evidence = result.fields['field_evidence']['asking_price_wan']
    assert evidence['value'] is None
    assert evidence['mentions'][0]['candidate_value'] == '200'
    assert evidence['mentions'][0]['is_non_exact'] is True


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/12345678'),
])
def test_exact_price_copula_remains_exact(source, source_url):
    result = parse_listing_html(
        source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：100㎡ 挂牌价为200万'
        '</main></body></html>')

    assert result.fields['asking_price_wan'] == 200
    assert result.fields['field_evidence']['asking_price_wan']['mentions'][0][
        'is_non_exact'] is False


def test_qualified_price_conflicts_with_exact_price_and_stays_pending():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：100㎡ '
        '挂牌价：200万左右 总价：210万</main></body></html>')

    assert result.fields['asking_price_wan'] is None
    assert 'multiple_price_mentions' in result.warnings
    assert 'non_exact_asking_price' in result.warnings


@pytest.mark.parametrize('qualified_price', ['挂牌价：200万左右', '挂牌价：约200万'])
def test_exact_price_root_outscores_earlier_approximate_price_root(qualified_price):
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><article><p>小区：东湖花园 建筑面积：100㎡ '
        f'{qualified_price}</p></article><article>'
        '<p>小区：东湖花园 建筑面积：100㎡ 总价：210万</p>'
        '</article></body></html>')

    assert result.fields['asking_price_wan'] == 210
    assert 'non_exact_asking_price' not in result.warnings


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize('qualified_price', [
    '折后总价', '优惠总价', '优惠后总价', '参考总价', '估算总价', '成交总价',
    '历史总价', '原始总价', '预估总价', '网签总价', '折扣后总价', '降价后总价',
    '折后 总价', '优惠后 总价', '口播总价', '口播 挂牌价', '口播：总价', '口播： 挂牌价',
    '口播:总价', '口播: 挂牌价', '成交:总价', '折后:挂牌价',
    '口播 挂牌总价', '成交 出售总价', '折后 挂牌总价', '交易总价', '合同总价', '签约总价',
    '评估总价', '银行评估总价', '评估 挂牌价', '租金总价', '月租总价', '年租总价', '原总价',
])
def test_qualified_total_is_not_treated_as_a_second_listing_price(
        source, source_url, qualified_price):
    result = parse_listing_html(
        source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ '
        f'挂牌价：365万 {qualified_price}：300万</main></body></html>')

    assert result.fields['asking_price_wan'] == 365
    assert 'multiple_price_mentions' not in result.warnings
    evidence = result.fields['field_evidence']['asking_price_wan']
    assert [item['candidate_value'] for item in evidence['mentions']] == ['365']


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize('price_label', [
    '总价', '挂牌总价', '挂牌价', '挂牌售价', '售价', '出售总价',
])
def test_supported_listing_price_labels_still_parse(source, source_url, price_label):
    result = parse_listing_html(
        source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ '
        f'{price_label}：365万</main></body></html>')

    assert result.fields['asking_price_wan'] == 365
    assert 'multiple_price_mentions' not in result.warnings
    evidence = result.fields['field_evidence']['asking_price_wan']
    assert [item['candidate_value'] for item in evidence['mentions']] == ['365']
    mention = evidence['mentions'][0]
    assert mention['quote'] == f'{price_label}：365万'
    excerpt = result.fields['evidence_excerpt']
    assert excerpt[mention['start_char']:mention['end_char']] == mention['quote']


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
def test_non_listing_price_prefixes_cannot_match_compound_price_labels(source, source_url):
    prefixes = ('折后', '优惠后', '优惠', '折扣后', '降价后', '参考', '估算', '成交', '交易',
                '合同', '签约', '历史', '原始', '预估', '网签', '口播', '口播：',
                '评估', '租金', '月租', '年租', '原')
    separators = ('', ' ', ':', '：', ': ', '： ')
    labels = ('总价', '挂牌总价', '挂牌价', '挂牌售价', '售价', '出售总价')

    for prefix in prefixes:
        for separator in separators:
            for label in labels:
                html = ('<html><body><main>小区：东湖花园 建筑面积：160㎡ 挂牌价：365万 '
                        f'{prefix}{separator}{label}：300万</main></body></html>')
                result = parse_listing_html(source, source_url, html)

                assert result.fields['asking_price_wan'] == 365, (prefix, separator, label)
                assert 'multiple_price_mentions' not in result.warnings, (
                    prefix, separator, label)


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize('qualified_label', [
    '折后总价', '交易总价', '合同总价', '签约总价', '成交售价', '合同售价',
    '评估总价', '银行评估总价', '租金总价', '月租总价', '年租总价', '原总价', '原挂牌价',
])
def test_qualified_total_alone_does_not_fill_listing_price(source, source_url, qualified_label):
    result = parse_listing_html(
        source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ '
        f'{qualified_label}：300万</main></body></html>')

    assert result.fields['asking_price_wan'] is None
    assert 'missing_asking_price_wan' in result.warnings


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
def test_oral_price_alone_does_not_fill_listing_price(source, source_url):
    result = parse_listing_html(
        source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ '
        '口播总价：300万</main></body></html>')

    assert result.fields['asking_price_wan'] is None
    assert 'missing_asking_price_wan' in result.warnings


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize('qualified_price', [
    '口播的总价', '口播 的 总价', '合同中的挂牌价', '合同 中 的 挂牌价',
    '交易中的总价', '交易 中 的 总价', '签约里的出售总价', '签约 里的 出售总价',
])
def test_linked_non_listing_price_qualifier_alone_does_not_fill_listing_price(
        source, source_url, qualified_price):
    result = parse_listing_html(
        source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ '
        f'{qualified_price}：300万</main></body></html>')

    assert result.fields['asking_price_wan'] is None
    assert 'missing_asking_price_wan' in result.warnings


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize('qualified_price', [
    '口播的总价', '口播 的 总价', '合同中的挂牌价', '合同 中 的 挂牌价',
    '交易中的总价', '交易 中 的 总价', '签约里的出售总价', '签约 里的 出售总价',
])
def test_linked_non_listing_price_qualifier_stays_out_of_multiple_listing_prices(
        source, source_url, qualified_price):
    result = parse_listing_html(
        source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ '
        f'挂牌价：365万 {qualified_price}：300万</main></body></html>')

    assert result.fields['asking_price_wan'] == 365
    assert 'multiple_price_mentions' not in result.warnings
    assert [item['candidate_value'] for item in
            result.fields['field_evidence']['asking_price_wan']['mentions']] == ['365']


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize('qualified_price', [
    '口播 的 总价', '合同 中 的 挂牌价', '交易 中 的 总价', '签约 里的 出售总价',
])
def test_linked_non_listing_price_range_is_not_listing_price_evidence(
        source, source_url, qualified_price):
    result = parse_listing_html(
        source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ '
        f'{qualified_price}：300万-320万</main></body></html>')

    assert result.fields['asking_price_wan'] is None
    assert 'multiple_price_mentions' not in result.warnings
    assert result.fields.get('field_evidence', {}).get('asking_price_wan', {}).get(
        'mentions', []) == []


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize('assessed_price', ['银行评估的总价', '银行评估 的 总价', '评估中的总价'])
def test_linked_assessed_price_qualifier_alone_does_not_fill_listing_price(
        source, source_url, assessed_price):
    result = parse_listing_html(
        source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ '
        f'{assessed_price}：300万</main></body></html>')

    assert result.fields['asking_price_wan'] is None
    assert 'missing_asking_price_wan' in result.warnings


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize('assessed_price', ['银行评估的总价', '银行评估 的 总价', '评估中的总价'])
def test_linked_assessed_price_qualifier_stays_out_of_multiple_listing_prices(
        source, source_url, assessed_price):
    result = parse_listing_html(
        source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ '
        f'挂牌价：365万 {assessed_price}：285万</main></body></html>')

    assert result.fields['asking_price_wan'] == 365
    assert 'multiple_price_mentions' not in result.warnings
    assert [item['candidate_value'] for item in
            result.fields['field_evidence']['asking_price_wan']['mentions']] == ['365']


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize('periodic_price', [
    '总价：3.6万/年', '总价：3.6万／年', '总价：3.6万元/月', '总价：3.6万每月',
    '租金总价：3.6万/年', '挂牌价：0.3万/天', '出售总价：0.9万/周',
])
def test_periodic_price_alone_does_not_fill_listing_price(
        source, source_url, periodic_price):
    result = parse_listing_html(
        source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ '
        f'{periodic_price}</main></body></html>')

    assert result.fields['asking_price_wan'] is None
    assert 'missing_asking_price_wan' in result.warnings
    assert result.fields.get('field_evidence', {}).get('asking_price_wan', {}).get(
        'mentions', []) == []


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize('periodic_price', [
    '总价：3万-3.6万/年', '总价：3万-3.6万/月',
])
def test_periodic_price_range_is_not_listing_price_evidence(
        source, source_url, periodic_price):
    result = parse_listing_html(
        source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ '
        f'{periodic_price}</main></body></html>')

    assert result.fields['asking_price_wan'] is None
    assert 'multiple_price_mentions' not in result.warnings
    assert result.fields.get('field_evidence', {}).get('asking_price_wan', {}).get(
        'mentions', []) == []


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize('year_in_parentheses', [
    '总价：300万（2024年）', '总价：300万（2024年交房）',
])
def test_year_annotation_after_price_keeps_exact_listing_price(
        source, source_url, year_in_parentheses):
    result = parse_listing_html(
        source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ '
        f'{year_in_parentheses}</main></body></html>')

    assert result.fields['asking_price_wan'] == 300
    assert 'multiple_price_mentions' not in result.warnings


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
def test_original_total_price_yields_current_total_price(source, source_url):
    result = parse_listing_html(
        source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ '
        '原总价：350万 现总价：300万</main></body></html>')

    assert result.fields['asking_price_wan'] == 300
    assert 'multiple_price_mentions' not in result.warnings
    assert [item['candidate_value'] for item in
            result.fields['field_evidence']['asking_price_wan']['mentions']] == ['300']


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize('exact_price_with_context', [
    '总价：300万 每月还贷1万元',
    '总价：300万（每年物业费2000元）',
    '总价：300万 每年物业费2000元',
])
def test_exact_price_survives_separate_period_context(
        source, source_url, exact_price_with_context):
    result = parse_listing_html(
        source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ '
        f'{exact_price_with_context}</main></body></html>')

    assert result.fields['asking_price_wan'] == 300
    assert 'missing_asking_price_wan' not in result.warnings


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize('periodic_price', [
    '总价：3.6万/年', '总价：3.6万／年', '总价：3.6万元/月', '总价：3.6万每月',
    '挂牌价：0.3万/天', '出售总价：0.9万/周',
])
def test_tight_periodic_price_stays_excluded(source, source_url, periodic_price):
    result = parse_listing_html(
        source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ '
        f'{periodic_price}</main></body></html>')

    assert result.fields['asking_price_wan'] is None
    assert 'missing_asking_price_wan' in result.warnings


@pytest.mark.parametrize('qualified_area', ['套内 面积', '使用 建筑面积'])
def test_qualified_area_with_collapsed_whitespace_is_not_a_second_listing_area(qualified_area):
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ '
        f'{qualified_area}：80㎡ 总价：365万</main></body></html>')

    assert result.fields['area_sqm'] == 160
    assert 'multiple_area_mentions' not in result.warnings
    assert [item['candidate_value'] for item in
            result.fields['field_evidence']['area_sqm']['mentions']] == ['160']


def test_field_evidence_caps_repeated_mentions_and_reports_total():
    mentions = ' '.join('总价：365万' for _ in range(30))
    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        f'<html><body><main>小区：东湖花园 建筑面积：160㎡ {mentions}</main></body></html>')

    evidence = result.fields['field_evidence']['asking_price_wan']
    assert result.fields['asking_price_wan'] == 365
    assert len(evidence['mentions']) == 20
    assert evidence['mention_count'] == 30
    assert evidence['mentions_truncated'] is True


def test_candidate_scoring_and_evidence_each_scan_repeated_prices_once(monkeypatch):
    original_finditer = re.finditer
    price_pattern_counts = {}
    repeated_prices = '挂牌总价：365万|' * 1002
    html = ('<html><body><main>小区：东湖花园 建筑面积：160㎡ '
            + repeated_prices + '</main></body></html>')

    def count_price_scans(pattern, text, flags=0):
        if r'([0-9,]+(?:\.[0-9]+)?)\s*万' in pattern and '东湖花园' in text:
            price_pattern_counts[pattern] = price_pattern_counts.get(pattern, 0) + 1
        yield from original_finditer(pattern, text, flags)

    monkeypatch.setattr(parser_module.re, 'finditer', count_price_scans)

    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    evidence = result.fields['field_evidence']['asking_price_wan']
    assert list(price_pattern_counts.values()) == [2]
    assert result.fields['asking_price_wan'] == 365
    assert evidence['mention_count'] == 1002
    assert len(evidence['mentions']) == 20
    assert evidence['mentions_truncated'] is True


def test_ambiguity_short_circuit_preserves_full_evidence_count():
    mentions = ' '.join(['总价：365万', '总价：390万'] + ['总价：365万'] * 1000)
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ ' + mentions
        + '</main></body></html>')

    evidence = result.fields['field_evidence']['asking_price_wan']
    assert result.fields['asking_price_wan'] is None
    assert 'multiple_price_mentions' in result.warnings
    assert len(evidence['mentions']) == 20
    assert evidence['mention_count'] == 1002
    assert evidence['mentions_truncated'] is True


@pytest.mark.parametrize(('field', 'repeated', 'conflict', 'warning'), [
    ('area_sqm', '建筑面积：160㎡', '建筑面积：165㎡', 'multiple_area_mentions'),
    ('asking_price_wan', '总价：365万', '总价：390万', 'multiple_price_mentions'),
])
def test_conflict_after_evidence_cap_still_blocks_review_ready(
        field, repeated, conflict, warning):
    mentions = ' '.join([repeated] * 19 + [conflict])
    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        f'<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 '
        f'{mentions}</main></body></html>')

    evidence = result.fields['field_evidence'][field]
    assert result.fields[field] is None
    assert warning in result.warnings
    assert evidence['mention_count'] == 21
    assert evidence['mentions_truncated'] is True
    assert not result.ready_for_review


def test_conflicting_field_evidence_offsets_survive_excerpt_truncation():
    prefix = '无关页面说明' * 250
    html = ('<html><body><main>' + prefix
            + ' 小区：东湖花园 小区：锦港府 建筑面积：160㎡ 总价：365万 总价：390万'
            + '</main></body></html>')

    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)
    normalized_text = re.sub(
        r'\s+', ' ',
        _text_with_inline_boundaries(BeautifulSoup(html, 'html.parser').main))

    assert result.fields['community_name'] is None
    assert result.fields['asking_price_wan'] is None
    assert 'multiple_community_mentions' in result.warnings
    assert 'multiple_price_mentions' in result.warnings
    for field in ('community_name', 'asking_price_wan'):
        evidence = result.fields['field_evidence'][field]
        assert evidence['value'] == result.fields[field] is None
        assert all(item['start_char'] >= len(result.fields['evidence_excerpt'])
                   for item in evidence['mentions'])
        for item in evidence['mentions']:
            assert normalized_text[item['start_char']:item['end_char']] == item['quote']
            assert item['candidate_value'] in item['quote']


def test_equivalent_numeric_mentions_do_not_count_as_conflicts():
    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：1,234㎡ 建面：1234.0㎡ '
        '总价：1,234万 挂牌价：1234.00万 户型：02室 户型：2室'
        '</main></body></html>')

    assert result.fields['area_sqm'] == 1234
    assert result.fields['asking_price_wan'] == 1234
    assert result.fields['bedrooms'] == 2
    assert not {'multiple_area_mentions', 'multiple_price_mentions',
                'multiple_bedrooms_mentions'} & set(result.warnings)


def test_building_area_is_not_conflicted_by_indoor_area_labels():
    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：120㎡ 套内面积：100㎡ '
        '使用面积：95㎡ 总价：365万</main></body></html>')

    assert result.fields['area_sqm'] == 120
    assert 'multiple_area_mentions' not in result.warnings
    assert result.ready_for_review


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize(('area_text', 'expected_area', 'has_multiple_areas'), [
    ('实用面积100㎡', None, False),
    ('实用面积100㎡ 建筑面积120㎡', 120, False),
])
def test_usable_area_label_is_not_mistaken_for_building_area(
        source, source_url, area_text, expected_area, has_multiple_areas):
    result = parse_listing_html(source, source_url,
        f'<html><body><main>小区：东湖花园 {area_text} 总价：365万'
        '</main></body></html>')

    assert result.fields['area_sqm'] == expected_area
    assert ('multiple_area_mentions' in result.warnings) is has_multiple_areas


def test_malformed_numeric_mention_does_not_crash_or_emit_value():
    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：,㎡ 总价：,万'
        '</main></body></html>')

    assert result.fields['area_sqm'] is None
    assert result.fields['asking_price_wan'] is None
    assert 'missing_area_sqm' in result.warnings
    assert 'missing_asking_price_wan' in result.warnings


def test_malformed_numeric_mention_does_not_hide_a_conflicting_value():
    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 总价：,万'
        '</main></body></html>')

    assert result.fields['asking_price_wan'] is None
    assert 'multiple_price_mentions' in result.warnings


def test_malformed_thousands_grouping_is_not_compacted_into_another_value():
    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：12,34㎡ 总价：12,34万'
        '</main></body></html>')

    assert result.fields['area_sqm'] is None
    assert result.fields['asking_price_wan'] is None


@pytest.mark.parametrize(('area', 'price', 'area_range', 'price_range'), [
    ('120-130㎡', '300-320万', '120-130㎡', '300-320万'),
    ('120㎡-130㎡', '300万-320万', '120㎡-130㎡', '300万-320万'),
    ('120平-130平', '300-320万', '120平-130平', '300-320万'),
    ('120-130平', '300万-320万', '120-130平', '300万-320万'),
    ('120平方-130平方', '300-320万', '120平方-130平方', '300-320万'),
])
def test_numeric_ranges_are_not_parsed_as_single_listing_values(
        area, price, area_range, price_range):
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        f'<html><body><main>小区：东湖花园 建筑面积：{area} 总价：{price}'
        '</main></body></html>')

    assert result.fields['area_sqm'] is None
    assert result.fields['asking_price_wan'] is None
    assert 'missing_area_sqm' in result.warnings
    assert 'missing_asking_price_wan' in result.warnings
    assert 'multiple_area_mentions' in result.warnings
    assert 'multiple_price_mentions' in result.warnings
    assert result.fields['field_evidence']['area_sqm']['mentions'][0]['candidate_value'] == area_range
    assert result.fields['field_evidence']['asking_price_wan']['mentions'][0]['candidate_value'] == price_range
    assert result.fields['field_evidence']['asking_price_wan']['mentions'][0]['is_non_exact'] is False
    assert not result.ready_for_review


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/12345678'),
])
@pytest.mark.parametrize(('qualifier', 'price_range'), [
    ('约', '300-320万'),
    ('不超过', '300万-320万'),
])
def test_leading_price_qualifier_preserves_range_evidence(
        source, source_url, qualifier, price_range):
    result = parse_listing_html(
        source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：100㎡ '
        f'挂牌价：{qualifier}{price_range}</main></body></html>')

    assert result.fields['asking_price_wan'] is None
    assert 'multiple_price_mentions' in result.warnings
    evidence = result.fields['field_evidence']['asking_price_wan']
    assert evidence['value'] is None
    assert evidence['mentions'][0]['candidate_value'] == price_range
    assert evidence['mentions'][0]['is_non_exact'] is True


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/12345678'),
])
@pytest.mark.parametrize('price_range', ['300-320万左右', '300万-320万以上'])
def test_trailing_price_range_qualifier_is_preserved_in_evidence(
        source, source_url, price_range):
    result = parse_listing_html(
        source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：100㎡ '
        f'挂牌价：{price_range}</main></body></html>')

    evidence = result.fields['field_evidence']['asking_price_wan']
    assert result.fields['asking_price_wan'] is None
    assert 'non_exact_asking_price' in result.warnings
    assert evidence['mentions'][0]['candidate_value'] == price_range.removesuffix('左右').removesuffix('以上')
    assert evidence['mentions'][0]['quote'] == f'挂牌价：{price_range}'
    assert evidence['mentions'][0]['is_non_exact'] is True
    assert not result.ready_for_review


@pytest.mark.parametrize('separator', ['-', '−', '－', '–', '—', '~', '～', '〜', '至', '到'])
def test_numeric_range_separators_do_not_promote_an_endpoint(separator):
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 '
        f'建筑面积：120㎡ {separator} 130㎡ 总价：300万 {separator} 320万'
        '</main></body></html>')

    assert result.fields['area_sqm'] is None
    assert result.fields['asking_price_wan'] is None
    assert 'missing_area_sqm' in result.warnings
    assert 'missing_asking_price_wan' in result.warnings
    assert 'multiple_area_mentions' in result.warnings
    assert 'multiple_price_mentions' in result.warnings


@pytest.mark.parametrize(('area', 'price'), [
    ('120㎡-一百三十㎡', '300万-320万'),
    ('120㎡-130㎡', '300万-三百二十万'),
])
def test_unsupported_chinese_range_endpoint_does_not_promote_arabic_endpoint(area, price):
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 '
        f'建筑面积：{area} 总价：{price}'
        '</main></body></html>')

    assert result.fields['area_sqm'] is None
    assert result.fields['asking_price_wan'] is None
    assert 'missing_area_sqm' in result.warnings
    assert 'missing_asking_price_wan' in result.warnings
    assert not result.ready_for_review


def test_range_guard_does_not_consume_single_values_before_field_labels():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：120㎡ - 楼层：高楼层 '
        '总价：300万 - 装修：精装</main></body></html>')

    assert result.fields['area_sqm'] == 120
    assert result.fields['asking_price_wan'] == 300
    assert result.fields['floor_text'] == '高楼层'
    assert result.fields['decoration'] == '精装'


@pytest.mark.parametrize(('field', 'detail', 'context', 'expected_mentions', 'warning'), [
    ('area_sqm', '建筑面积：120㎡-130㎡ 建筑面积：125㎡', '总价：365万',
     ['120㎡-130㎡', '125'], 'multiple_area_mentions'),
    ('asking_price_wan', '总价：300万-320万 挂牌价：310万', '建筑面积：160㎡',
     ['300万-320万', '310'], 'multiple_price_mentions'),
])
def test_range_and_single_value_are_reported_as_conflicting_evidence(
        field, detail, context, expected_mentions, warning):
    html = (f'<html><body><main>小区：东湖花园 {detail} {context}'
            '</main></body></html>')
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)
    normalized_text = re.sub(
        r'\s+', ' ',
        _text_with_inline_boundaries(BeautifulSoup(html, 'html.parser').main))

    assert result.fields[field] is None
    assert warning in result.warnings
    evidence = result.fields['field_evidence'][field]
    assert evidence['value'] is None
    assert [mention['candidate_value'] for mention in evidence['mentions']] == expected_mentions
    if field == 'asking_price_wan':
        assert all(mention['is_non_exact'] is False for mention in evidence['mentions'])
    for mention in evidence['mentions']:
        assert normalized_text[mention['start_char']:mention['end_char']] == mention['quote']
        assert mention['candidate_value'] in mention['quote']


def test_numeric_range_evidence_is_capped_and_counted():
    ranges = ' '.join('建筑面积：120㎡-130㎡' for _ in range(30))
    html = ('<html><body><main>小区：东湖花园 ' + ranges
            + ' 总价：365万</main></body></html>')

    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)
    evidence = result.fields['field_evidence']['area_sqm']

    assert result.fields['area_sqm'] is None
    assert evidence['value'] is None
    assert evidence['mention_count'] == 30
    assert len(evidence['mentions']) == 20
    assert evidence['mentions_truncated'] is True
    assert 'multiple_area_mentions' in result.warnings
    assert all('120㎡-130㎡' in mention['quote'] for mention in evidence['mentions'])


def test_valid_thousands_grouping_still_parses():
    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：1,234.5㎡ 总价：12,345.6万'
        '</main></body></html>')

    assert result.fields['area_sqm'] == 1234.5
    assert result.fields['asking_price_wan'] == 12345.6


def test_conflicting_optional_labels_are_reported_without_choosing_values():
    result=parse_listing_html('beike','https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 建面：155㎡ 总价：365万 '
        '户型：2室 户型：3室 区域：鄞州 区域：海曙 '
        '楼层：高楼层 楼层：低楼层 装修：精装 装修：简装'
        '</main></body></html>')

    assert result.fields['area_sqm'] is None
    assert result.fields['bedrooms'] is None
    assert result.fields['district'] is None
    assert result.fields['floor_text'] is None
    assert result.fields['decoration'] is None
    assert {'multiple_bedrooms_mentions', 'multiple_district_mentions',
            'multiple_floor_mentions', 'multiple_decoration_mentions',
            'multiple_area_mentions'} <= set(result.warnings)
    for field, candidates in {
        'area_sqm': ['160', '155'],
        'bedrooms': ['2', '3'],
        'district': ['鄞州', '海曙'],
        'floor_text': ['高楼层', '低楼层'],
        'decoration': ['精装', '简装'],
    }.items():
        evidence = result.fields['field_evidence'][field]
        assert evidence['value'] is None
        assert [item['candidate_value'] for item in evidence['mentions']] == candidates


def test_conflicting_community_mentions_are_reported_without_choosing_one():
    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 小区：锦港府 建筑面积：160㎡ 总价：365万'
        '</main></body></html>')

    assert result.fields['community_name'] is None
    assert 'multiple_community_mentions' in result.warnings
    assert not result.ready_for_review
    evidence = result.fields['field_evidence']['community_name']
    assert [item['candidate_value'] for item in evidence['mentions']] == ['东湖花园', '锦港府']


def test_out_of_range_bedroom_count_is_not_emitted():
    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 户型：21室'
        '</main></body></html>')

    assert result.fields['bedrooms'] is None
    assert 'invalid_bedrooms_mentions' in result.warnings
    assert result.fields['field_evidence']['bedrooms']['mentions'][0]['candidate_value'] == '21'


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/12345678'),
])
@pytest.mark.parametrize(('bedroom_text', 'expected'), [('0室', 0), ('20室', 20)])
def test_bedroom_count_inclusive_model_boundaries_are_preserved(
        source, source_url, bedroom_text, expected):
    result = parse_listing_html(
        source, source_url,
        '<html><body><main>小区：东湖花园 建筑面积：100㎡ 总价：200万 '
        f'户型：{bedroom_text}</main></body></html>')

    assert result.fields['bedrooms'] == expected
    assert 'invalid_bedrooms_mentions' not in result.warnings
    assert result.fields['field_evidence']['bedrooms']['mentions'][0][
        'candidate_value'] == str(expected)


@pytest.mark.parametrize('bedroom_text', ['102室', '123室'])
def test_bedroom_parser_does_not_match_a_suffix_of_three_digit_count(bedroom_text):
    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 '
        f'户型：{bedroom_text}</main></body></html>')

    assert result.fields['bedrooms'] is None
    assert 'bedrooms' not in result.fields['field_evidence']


def test_overlong_source_listing_id_is_not_emitted():
    listing_id = '1' * 221
    result = parse_listing_html('beike', f'https://nb.ke.com/ershoufang/{listing_id}.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万'
        '</main></body></html>')

    assert result.fields['source_listing_id'] is None
    assert 'missing_source_listing_id' in result.warnings
    assert not result.ready_for_review


def test_script_ads_and_ip_location_not_used():
    result=parse_listing_html('anjuke','https://ningbo.anjuke.com/sale/1234567890',
        '<html><body><script>小区：假的 总价：100万</script><main>'
        'IP属地：鄞州 小区：锦港府 建面：140㎡ 挂牌价：380万'
        '</main></body></html>')
    assert result.fields['community_name']=='锦港府'
    assert result.fields['district'] is None
    assert result.fields['asking_price_wan']==380


def test_sidebar_recommendation_price_is_not_used():
    result=parse_listing_html('beike','https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万</main>'
        '<aside><p>推荐房源 总价：900万</p></aside></body></html>')

    assert result.fields['asking_price_wan']==365
    assert 'multiple_price_mentions' not in result.warnings


def test_listing_form_fields_do_not_conflict_with_detail_values():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 '
        '<form><label>小区：锦港府</label><label>建筑面积：120㎡</label>'
        '<label>总价：888万</label><button>提交</button></form>'
        '</main></body></html>')

    assert result.fields['community_name'] == '东湖花园'
    assert result.fields['area_sqm'] == 160
    assert result.fields['asking_price_wan'] == 365
    assert result.ready_for_review


def test_hidden_ad_price_is_not_used():
    result=parse_listing_html('anjuke','https://ningbo.anjuke.com/sale/1234567890',
        '<html><body><main>小区：锦港府 建筑面积：142㎡ 总价：398万 '
        '<div aria-hidden="true" style="display:none">广告挂牌总价：888万</div>'
        '</main></body></html>')

    assert result.fields['asking_price_wan']==398
    assert 'multiple_price_mentions' not in result.warnings


@pytest.mark.parametrize('display', ['block', 'flex', 'contents'])
def test_hidden_attribute_with_inline_display_override_is_visible(display):
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 '
        f'<span hidden style="display:{display}">挂牌总价：900万</span>'
        '</main></body></html>')

    assert result.fields['asking_price_wan'] is None
    assert 'multiple_price_mentions' in result.warnings


def test_hidden_attribute_with_inline_display_none_stays_hidden():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 '
        '<span hidden style="display:block;display:none!important">'
        '挂牌总价：900万</span></main></body></html>')

    assert result.fields['asking_price_wan'] == 365
    assert 'multiple_price_mentions' not in result.warnings


def test_hidden_until_found_with_inline_display_block_stays_hidden():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 '
        '<span hidden="until-found" style="display:block">'
        '挂牌总价：900万</span></main></body></html>')

    assert result.fields['asking_price_wan'] == 365
    assert 'multiple_price_mentions' not in result.warnings


def test_aria_hidden_visible_price_is_still_considered():
    result=parse_listing_html('anjuke','https://ningbo.anjuke.com/sale/1234567890',
        '<html><body><main>小区：锦港府 建筑面积：142㎡ 总价：398万 '
        '<div aria-hidden="true">广告挂牌总价：888万</div></main></body></html>')

    assert result.fields['asking_price_wan'] is None
    assert 'multiple_price_mentions' in result.warnings


def test_template_content_is_not_used_as_visible_listing_text():
    result=parse_listing_html('beike','https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 '
        '<template><div>推荐房源 总价：900万</div></template></main></body></html>')

    assert result.fields['asking_price_wan']==365
    assert 'multiple_price_mentions' not in result.warnings


def test_metadata_inside_template_does_not_override_page_metadata():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><head><template>'
        '<link rel="canonical" href="/ershoufang/109900009999.html">'
        '<meta property="og:url" content="/ershoufang/109900009999.html">'
        '<meta property="og:title" content="模板标题">'
        '</template></head><body><h1>东湖花园 4室2厅</h1><main>'
        '小区：东湖花园 建筑面积：160㎡ 总价：365万'
        '</main></body></html>')

    assert result.fields['source_listing_id'] == '109900001234'
    assert result.fields['title'] == '东湖花园 4室2厅'
    assert 'canonical_source_id_mismatch' not in result.warnings


def test_body_metadata_does_not_override_head_metadata_or_page_identity():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><head><title>有效页面标题</title></head><body>'
        '<link rel="canonical" href="/ershoufang/109900009999.html">'
        '<meta property="og:url" content="/ershoufang/109900009999.html">'
        '<meta property="og:title" content="正文伪元数据">'
        '<h1>东湖花园 4室2厅</h1><main>'
        '小区：东湖花园 建筑面积：160㎡ 总价：365万'
        '</main></body></html>')

    assert result.fields['source_listing_id'] == '109900001234'
    assert result.fields['title'] == '东湖花园 4室2厅'
    assert 'canonical_source_id_mismatch' not in result.warnings


def test_document_title_is_fallback_when_og_title_and_h1_are_missing():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><head><title>东湖花园 4室2厅 | 贝壳找房</title></head>'
        '<body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万'
        '</main></body></html>')

    assert result.fields['title'] == '东湖花园 4室2厅 | 贝壳找房'


@pytest.mark.parametrize('tag', ['iframe', 'object', 'canvas'])
def test_embedded_fallback_text_is_not_used_as_visible_listing_text(tag):
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 '
        f'<{tag}>备用内容 总价：900万</{tag}></main></body></html>')

    assert result.fields['asking_price_wan'] == 365


def test_template_fallback_price_is_not_used():
    html = ('<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万'
            '<template><div>广告挂牌总价：900万</div></template>'
            '</main></body></html>')

    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['asking_price_wan'] == 365
    assert 'multiple_price_mentions' not in result.warnings


@pytest.mark.parametrize('hidden_nodes', [
    '<div style="display:none"><span style="display:none">广告总价：900万</span></div>',
    '<div hidden><span hidden>广告总价：900万</span></div>',
    '<dialog><dialog>广告总价：900万</dialog></dialog>',
    '<details><details>广告总价：900万</details></details>',
    '<nav><aside>广告总价：900万</aside></nav>',
])
def test_nested_hidden_nodes_do_not_crash_or_affect_parser(hidden_nodes):
    html = ('<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万'
            + hidden_nodes + '</main></body></html>')

    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['asking_price_wan'] == 365


def test_inline_visibility_hidden_ad_price_is_not_used():
    html = ('<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万'
            '<span style="visibility:hidden">挂牌总价：900万</span>'
            '</main></body></html>')

    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['asking_price_wan'] == 365
    assert 'multiple_price_mentions' not in result.warnings


def test_inline_visible_descendant_overrides_hidden_visibility_ancestor():
    html = ('<html><body><main><div style="visibility:hidden">'
            '<span style="visibility:visible">小区：东湖花园 建筑面积：160㎡ 总价：365万'
            '</span></div></main></body></html>')

    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['community_name'] == '东湖花园'
    assert result.fields['area_sqm'] == 160
    assert result.fields['asking_price_wan'] == 365
    assert 'multiple_price_mentions' not in result.warnings


@pytest.mark.parametrize(('style', 'is_hidden'), [
    ('visibility:hidden;visibility:visible', False),
    ('visibility:visible;visibility:hidden!important', True),
    ('visibility:hidden!important;visibility:visible', True),
])
def test_inline_visibility_uses_cascade_result(style, is_hidden):
    html = ('<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万'
            f'<span style="{style}">挂牌总价：900万</span>'
            '</main></body></html>')

    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert (result.fields['asking_price_wan'] == 365) is is_hidden
    assert ('multiple_price_mentions' in result.warnings) is not is_hidden


def test_inline_opacity_zero_ad_price_is_not_used():
    html = ('<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万'
            '<span style="opacity:0">挂牌总价：900万</span>'
            '</main></body></html>')

    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['asking_price_wan'] == 365
    assert 'multiple_price_mentions' not in result.warnings


def test_inline_opacity_zero_ancestor_cannot_be_overridden_by_child():
    html = ('<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万'
            '<div style="opacity:0"><span style="opacity:1">挂牌总价：900万</span></div>'
            '</main></body></html>')

    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['asking_price_wan'] == 365
    assert 'multiple_price_mentions' not in result.warnings


def test_content_visibility_hidden_ad_price_is_not_used():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 '
        '<span style="content-visibility:hidden">挂牌总价：900万</span>'
        '</main></body></html>')

    assert result.fields['asking_price_wan'] == 365
    assert 'multiple_price_mentions' not in result.warnings


def test_content_visibility_hidden_ancestor_hides_descendants():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main><div style="content-visibility:hidden">'
        '<span style="content-visibility:visible">挂牌总价：900万</span>'
        '</div>小区：东湖花园 建筑面积：160㎡ 总价：365万'
        '</main></body></html>')

    assert result.fields['asking_price_wan'] == 365
    assert 'multiple_price_mentions' not in result.warnings


def test_deeply_nested_html_does_not_overflow_visibility_walk():
    content = '小区：东湖花园 建筑面积：160㎡ 总价：365万'
    html = ('<html><body><main>' + '<div>' * 1200 + content
            + '</div>' * 1200 + '</main></body></html>')

    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['community_name'] == '东湖花园'
    assert result.fields['area_sqm'] == 160
    assert result.fields['asking_price_wan'] == 365


def test_inherited_display_text_walk_scales_with_node_count(monkeypatch):
    depth = 400
    html = ('<html><body><main>'
            + '<span style="display:inherit">' * depth
            + 'visible text'
            + '</span>' * depth
            + '</main></body></html>')
    main = BeautifulSoup(html, 'html.parser').main
    original = parser_module._inline_css_value
    display_queries = 0

    def count_display_queries(style, property_name):
        nonlocal display_queries
        if property_name == 'display':
            display_queries += 1
        return original(style, property_name)

    monkeypatch.setattr(parser_module, '_inline_css_value', count_display_queries)

    text = _text_with_inline_boundaries(main)

    assert 'visible text' in text
    assert display_queries <= depth * 3 + 20


@pytest.mark.parametrize(('style', 'is_hidden'), [
    ('opacity:0;opacity:1', False),
    ('opacity:1;opacity:0!important', True),
    ('opacity:0!important;opacity:1', True),
    ('opacity:0%', True),
    ('opacity:0.', True),
    ('opacity:0.%', True),
    ('opacity:calc(0)', True),
    ('opacity:calc(0.5)', False),
    ('opacity:calc(0%)', True),
    ('opacity:calc(1 - 1)', True),
    ('opacity:calc((1 - 1))', True),
    ('opacity:calc(0% + 0%)', True),
    ('opacity:calc(0 * 1)', True),
    ('opacity:calc(1 / 2)', False),
    ('opacity:calc(0 / 0)', False),
    ('opacity:calc(var(--opacity))', False),
    ('opacity:min(0, 1)', True),
    ('opacity:max(0, 0)', True),
    ('opacity:clamp(0, 0, 1)', True),
    ('opacity:min(0.1, 0.5)', False),
    ('opacity:clamp(0, 0.5, 1)', False),
    ('opacity:-0.5', True),
    ('opacity:-50%', True),
    ('opacity:-5e-1', True),
    ('opacity:-Infinity', False),
])
def test_inline_opacity_uses_cascade_result(style, is_hidden):
    html = ('<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万'
            f'<span style="{style}">挂牌总价：900万</span>'
            '</main></body></html>')

    result = parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert (result.fields['asking_price_wan'] == 365) is is_hidden
    assert ('multiple_price_mentions' in result.warnings) is not is_hidden


def test_opacity_calc_rejects_unsupported_or_oversized_expressions():
    assert parser_module._css_numeric_math('var(--opacity)') is None
    assert parser_module._css_numeric_math('0 + ' * 64 + '0') is None


def test_closed_dialog_content_is_not_used_as_visible_listing_text():
    result=parse_listing_html('beike','https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 '
        '<dialog><p>推荐房源 总价：900万</p></dialog></main></body></html>')

    assert result.fields['asking_price_wan']==365
    assert 'multiple_price_mentions' not in result.warnings


def test_open_dialog_content_remains_available_to_parser():
    result=parse_listing_html('beike','https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main><dialog open>小区：东湖花园 建筑面积：160㎡ 总价：365万'
        '</dialog></main></body></html>')

    assert result.fields['asking_price_wan']==365


def test_collapsed_details_content_is_not_used_as_visible_listing_text():
    result=parse_listing_html('beike','https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 '
        '<details><summary>房源概况</summary><p>推荐房源 总价：900万</p></details>'
        '</main></body></html>')

    assert result.fields['asking_price_wan']==365
    assert 'multiple_price_mentions' not in result.warnings


def test_collapsed_details_summary_preserves_inline_listing_labels_and_values():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main><details><summary>'
        '<span>小区</span><span>：</span><span>东湖</span><span>花园</span>'
        ' <span>建筑面积：</span><span>160</span><span>㎡</span>'
        ' <span>总</span><span>价：</span><span>365</span><span>万</span>'
        '</summary><p>推荐房源 总价：900万</p></details></main></body></html>')

    assert result.fields['community_name'] == '东湖花园'
    assert result.fields['area_sqm'] == 160
    assert result.fields['asking_price_wan'] == 365
    assert 'multiple_price_mentions' not in result.warnings


@pytest.mark.parametrize('hidden_summary_content', [
    '<span style="display:none">总价：900万</span>',
    '<span style="visibility:hidden">总价：900万</span>',
    '<span style="opacity:0">总价：900万</span>',
    '<span style="content-visibility:hidden">总价：900万</span>',
    '<span hidden>总价：900万</span>',
])
def test_hidden_content_inside_collapsed_details_summary_is_not_used(hidden_summary_content):
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 '
        '<details><summary>房源概况' + hidden_summary_content + '</summary>'
        '<p>推荐房源 总价：700万</p></details></main></body></html>')

    assert result.fields['asking_price_wan'] == 365
    assert 'multiple_price_mentions' not in result.warnings


def test_open_details_content_remains_available_to_parser():
    result=parse_listing_html('beike','https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main><details open><summary>房源概况</summary>'
        '小区：东湖花园 建筑面积：160㎡ 总价：365万'
        '</details></main></body></html>')

    assert result.fields['asking_price_wan']==365


def test_closed_details_inside_open_details_keeps_only_its_summary():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万'
        '<details open><summary>展开概况</summary><p>正文内容</p>'
        '<details><summary>挂牌总价：400万</summary><p>广告总价：900万</p>'
        '</details></details></main></body></html>')

    assert result.fields['asking_price_wan'] is None
    assert 'multiple_price_mentions' in result.warnings
    evidence = result.fields['field_evidence']['asking_price_wan']
    assert [item['candidate_value'] for item in evidence['mentions']] == ['365', '400']


@pytest.mark.parametrize('style', ['display:none', 'display: none !important'])
def test_inline_display_none_ad_price_is_not_used(style):
    result=parse_listing_html('anjuke','https://ningbo.anjuke.com/sale/1234567890',
        '<html><body><main>小区：锦港府 建筑面积：142㎡ 总价：398万 '
        f'<div style="{style}">推荐房源挂牌总价：888万</div></main></body></html>')

    assert result.fields['asking_price_wan']==398
    assert 'multiple_price_mentions' not in result.warnings


def test_inline_display_none_with_css_comment_hides_ad_price():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 '
        '<div style="display:none /* tracking; ad */">推荐挂牌总价：900万</div>'
        '</main></body></html>')

    assert result.fields['asking_price_wan'] == 365
    assert 'multiple_price_mentions' not in result.warnings


def test_parser_marks_text_truncation_and_blocks_ready_for_review():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 '
        + '说明' * 18000 + ' 总价：900万</main></body></html>')

    assert result.fields['asking_price_wan'] == 365
    assert 'visible_text_truncated' in result.warnings
    evidence = result.fields['field_evidence']['asking_price_wan']
    assert evidence['mention_count'] == 1
    assert evidence['mentions'][0]['candidate_value'] == '365'
    assert evidence['mentions'][0]['end_char'] <= parser_module.MAX_VISIBLE_TEXT_CHARS
    assert 'multiple_price_mentions' not in result.warnings
    assert not result.ready_for_review


def test_body_fallback_uses_bounded_text_and_reports_unscanned_tail():
    html = ('<html><body><div>小区：东湖花园 建筑面积：160㎡ 总价：365万</div>'
            + '说明' * 18000 + '总价：900万</body></html>')

    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['community_name'] == '东湖花园'
    assert result.fields['area_sqm'] == 160
    assert result.fields['asking_price_wan'] == 365
    assert 'visible_text_truncated' in result.warnings
    evidence = result.fields['field_evidence']['asking_price_wan']
    assert evidence['mention_count'] == 1
    assert evidence['mentions'][0]['end_char'] <= parser_module.MAX_VISIBLE_TEXT_CHARS
    assert 'multiple_price_mentions' not in result.warnings
    assert not result.ready_for_review


@pytest.mark.parametrize('style, is_hidden', [
    ('display:none;display:block', False),
    ('display:none!important;display:block', True),
    ('display:block;display:none!important', True),
    ('display:none;display:block!important', False),
    ('display:block;display:none /* note; ad */', True),
    ('display:none /* note; ad */;display:block', False),
])
def test_inline_display_uses_cascade_result(style, is_hidden):
    assert _inline_display_none(style) is is_hidden


@pytest.mark.parametrize('style, is_hidden', [
    ('display:none;display:bogus', True),
    ('display:block;display:bogus', False),
])
def test_inline_display_ignores_invalid_overrides(style, is_hidden):
    assert _inline_display_none(style) is is_hidden


def test_inline_opacity_ignores_invalid_override():
    assert _inline_opacity_zero('opacity:0;opacity:bogus')


def test_inline_opacity_ignores_whitespace_between_number_and_percent():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 '
        '<span style="opacity:0;opacity:1 %">推荐挂牌总价：900万</span>'
        '</main></body></html>')

    assert result.fields['asking_price_wan'] == 365
    assert 'multiple_price_mentions' not in result.warnings


@pytest.mark.parametrize('style', [
    'display:block;display:none!important bogus',
    'opacity:1;opacity:0!important bogus',
])
def test_inline_css_ignores_malformed_important_priority(style):
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ '
        f'<span style="{style}">总价：365万</span>'
        '</main></body></html>')

    assert result.fields['asking_price_wan'] == 365


@pytest.mark.parametrize('style', [
    'display:var(--hidden, none)',
    'display:var(--hidden, none!important)',
    'opacity:var(--fade, 0)',
    'opacity:calc(var(--fade, 0))',
    'visibility:var(--visibility, hidden)',
    'content-visibility:var(--content-state, hidden)',
])
def test_unresolved_inline_css_variables_block_review_ready(style):
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 '
        f'<span style="{style}">推荐挂牌总价：365万</span>'
        '</main></body></html>')

    assert result.fields['asking_price_wan'] == 365
    assert 'unresolved_inline_visibility' in result.warnings
    assert not result.ready_for_review


@pytest.mark.parametrize('style', [
    r'd\69 splay:none',
    r'display:n\6f ne',
    r'v\69 sibility:hidden',
    r'display:block;display:none !impor\74 ant',
])
def test_css_escaped_visibility_declarations_hide_ad_price(style):
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 '
        f'<span style="{style}">推荐挂牌总价：900万</span>'
        '</main></body></html>')

    assert result.fields['asking_price_wan'] == 365
    assert 'multiple_price_mentions' not in result.warnings


@pytest.mark.parametrize('style', [
    r'display:v\61 r(--hidden, none)',
    r'opacity:calc(v\61 r(--fade, 0))',
])
def test_css_escaped_var_function_blocks_review_ready(style):
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 '
        f'<span style="{style}">推荐挂牌总价：365万</span>'
        '</main></body></html>')

    assert result.fields['asking_price_wan'] == 365
    assert 'unresolved_inline_visibility' in result.warnings
    assert not result.ready_for_review


@pytest.mark.parametrize('style', [
    r'opacity:\30',
    r'opacity:calc(\30)',
])
def test_css_escaped_digits_are_not_opacity_numbers(style):
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 '
        f'<span style="{style}">推荐挂牌总价：900万</span>'
        '</main></body></html>')

    assert result.fields['asking_price_wan'] is None
    assert 'multiple_price_mentions' in result.warnings


def test_css_escaped_parentheses_do_not_form_opacity_function():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 '
        r'<span style="opacity:calc\(0\)">推荐挂牌总价：900万</span>'
        '</main></body></html>')

    assert result.fields['asking_price_wan'] is None
    assert 'multiple_price_mentions' in result.warnings
    assert 'unresolved_inline_visibility' in result.warnings


def test_content_visibility_auto_requires_review():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 '
        '<span style="content-visibility:auto">推荐挂牌总价：365万</span>'
        '</main></body></html>')

    assert result.fields['asking_price_wan'] == 365
    assert 'unresolved_inline_visibility' in result.warnings
    assert not result.ready_for_review


@pytest.mark.parametrize('stylesheet', [
    '<style>.recommendation{display:none}</style>',
    r'<style>.recommendation{d\69 splay:none}</style>',
    '<style>@import url("/listing.css");</style>',
    r'<style>@\69 mport url("/listing.css");</style>',
    '<style>.recommendation{clip-path:inset(100%)}</style>',
    '<style>.recommendation{mask-image:linear-gradient(transparent,transparent)}</style>',
    '<link rel="stylesheet" href="/listing.css">',
])
def test_stylesheet_visibility_requires_review(stylesheet):
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        f'<html><head>{stylesheet}</head><body><main>'
        '小区：东湖花园 建筑面积：160㎡ 总价：365万 '
        '<span class="recommendation">推荐挂牌总价：365万</span>'
        '</main></body></html>')

    assert result.fields['asking_price_wan'] == 365
    assert 'unresolved_stylesheet_visibility' in result.warnings
    assert not result.ready_for_review


def test_nested_stylesheet_scan_does_not_repeat_ancestor_walks(monkeypatch):
    depth = 80
    nested = ''.join(
        '<div><link rel="preload" href="/listing.css">'
        for _ in range(depth)
    ) + '</div>' * depth
    soup = BeautifulSoup(f'<html><head>{nested}</head></html>', 'html.parser')

    def fail_find_parent(*args, **kwargs):
        raise AssertionError('stylesheet scan must not walk ancestors per stylesheet')

    monkeypatch.setattr(Tag, 'find_parent', fail_find_parent)

    assert not parser_module._has_unresolved_stylesheet_visibility(soup)


@pytest.mark.parametrize('css_string', ['display:none', '@import'])
def test_css_string_content_does_not_trigger_stylesheet_visibility_review(css_string):
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        f'<html><head><style>.listing::before{{content:"{css_string}"}}</style></head>'
        '<body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万</main></body></html>')

    assert result.fields['asking_price_wan'] == 365
    assert 'unresolved_stylesheet_visibility' not in result.warnings
    assert result.ready_for_review


@pytest.mark.parametrize('custom_property', [
    '--display:none',
    '--label:display:none',
    '--label:{display:none;}',
])
def test_custom_property_tokens_do_not_trigger_stylesheet_visibility_review(custom_property):
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        f'<html><head><style>.listing{{{custom_property}}}</style></head>'
        '<body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万</main></body></html>')

    assert result.fields['asking_price_wan'] == 365
    assert 'unresolved_stylesheet_visibility' not in result.warnings
    assert result.ready_for_review


@pytest.mark.parametrize('css_rule', [
    '@media screen{.recommendation{display:none}}',
    '@supports (opacity:0){.recommendation{visibility:hidden}}',
    r'@media screen{.recommendation{d\69 splay:none}}',
    '.listing{--label:{display:none;};@media screen{.recommendation{clip-path:inset(100%)}}}',
])
def test_nested_stylesheet_visibility_rules_require_review(css_rule):
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        f'<html><head><style>{css_rule}</style></head><body><main>'
        '小区：东湖花园 建筑面积：160㎡ 总价：365万'
        '</main></body></html>')

    assert 'unresolved_stylesheet_visibility' in result.warnings
    assert not result.ready_for_review


def test_nested_custom_property_blocks_decode_prefix_once(monkeypatch):
    depth = 100
    css = '--payload:{' + '{' * depth + 'token' + '}' * depth + '}'
    original = parser_module._decode_css_escapes
    decode_calls = 0

    def count_decodes(value):
        nonlocal decode_calls
        decode_calls += 1
        return original(value)

    monkeypatch.setattr(parser_module, '_decode_css_escapes', count_decodes)

    list(parser_module._css_rule_segments(css))

    assert decode_calls == 1


def test_css_rule_segments_yield_lazily():
    class CountingCss(str):
        def __new__(cls, value):
            instance = super().__new__(cls, value)
            instance.slice_count = 0
            return instance

        def __getitem__(self, key):
            if isinstance(key, slice):
                self.slice_count += 1
            return super().__getitem__(key)

    css = CountingCss('aa;' * 1000)
    segments = iter(parser_module._css_rule_segments(css))

    assert next(segments) == 'aa'
    assert css.slice_count == 1


def test_css_comment_string_filter_does_not_build_per_character_list():
    css = 'a' * 300_000

    tracemalloc.start()
    try:
        visible = parser_module._css_without_comments_or_strings(css)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    assert visible == css
    assert peak < 1_000_000


@pytest.mark.parametrize('operation', ['inline_declarations', 'opacity_check'])
def test_css_declaration_scans_do_not_materialize_split_list(operation):
    style = 'x:a;' * 75_000

    tracemalloc.start()
    try:
        if operation == 'inline_declarations':
            parser_module._scan_inline_css_values(style, ('display',))
        else:
            parser_module._has_escaped_opacity_math_syntax(style)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    assert peak < 1_000_000


@pytest.mark.parametrize('style', [
    'clip-path:inset(100%)',
    'mask-image:linear-gradient(transparent,transparent)',
    '-webkit-mask:linear-gradient(transparent,transparent)',
])
def test_inline_clipping_or_masking_requires_review(style):
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 '
        f'<span style="{style}">推荐挂牌总价：365万</span>'
        '</main></body></html>')

    assert result.fields['asking_price_wan'] == 365
    assert 'unresolved_inline_visibility' in result.warnings
    assert not result.ready_for_review


@pytest.mark.parametrize('stylesheet', [
    '<style>.recommendation{display:none}</style>',
    '<link rel="stylesheet" href="/listing.css">',
])
def test_template_stylesheets_do_not_block_review_ready(stylesheet):
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        f'<html><head><template>{stylesheet}</template></head><body><main>'
        '小区：东湖花园 建筑面积：160㎡ 总价：365万'
        '</main></body></html>')

    assert result.fields['asking_price_wan'] == 365
    assert 'unresolved_stylesheet_visibility' not in result.warnings
    assert result.ready_for_review


@pytest.mark.parametrize('stylesheet', [
    '<style>.recommendation{display:none}</style>',
    '<link rel="stylesheet" href="/listing.css">',
])
def test_noscript_stylesheets_do_not_block_review_ready(stylesheet):
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        f'<html><head><noscript>{stylesheet}</noscript></head><body><main>'
        '小区：东湖花园 建筑面积：160㎡ 总价：365万'
        '</main></body></html>')

    assert result.fields['asking_price_wan'] == 365
    assert 'unresolved_stylesheet_visibility' not in result.warnings
    assert result.ready_for_review


@pytest.mark.parametrize('style', [
    'display:none;display:bogus',
    'opacity:0;opacity:bogus',
])
def test_invalid_css_override_does_not_expose_hidden_ad_price(style):
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 '
        f'<span style="{style}">推荐挂牌总价：900万</span>'
        '</main></body></html>')

    assert result.fields['asking_price_wan'] == 365
    assert 'multiple_price_mentions' not in result.warnings


def test_visible_inline_display_override_keeps_listing_fields():
    result=parse_listing_html('anjuke','https://ningbo.anjuke.com/sale/1234567890',
        '<html><body><main style="display:none;display:block">'
        '小区：锦港府 建筑面积：142㎡ 总价：398万'
        '</main></body></html>')

    assert result.fields['community_name']=='锦港府'
    assert result.fields['asking_price_wan']==398


def test_invalid_html_size():
    with pytest.raises(CollectionError):
        parse_listing_html('beike','https://nb.ke.com/ershoufang/109900001234.html','short')


def test_parser_rejects_html_over_utf8_byte_limit():
    with pytest.raises(CollectionError, match='UTF-8 bytes'):
        parse_listing_html('beike','https://nb.ke.com/ershoufang/109900001234.html','房' * 333334)


def test_parser_rejects_oversized_character_count_before_utf8_encoding():
    class OversizedHtml(str):
        def encode(self, *args, **kwargs):
            raise AssertionError('oversized input must be rejected before encoding')

    html = OversizedHtml('x' * 1_000_001)

    with pytest.raises(CollectionError, match='UTF-8 bytes'):
        parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)


def test_parser_rejects_nul_character_before_persistable_evidence_is_built():
    html = ('<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万'
            '\x00</main></body></html>')

    with pytest.raises(CollectionError, match='NUL character'):
        parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)


def test_blank_og_title_falls_back_to_nonblank_h1():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><head><meta property="og:title" content="   "></head>'
        '<body><h1>东湖花园 4室2厅</h1><main>'
        '小区：东湖花园 建筑面积：160㎡ 总价：365万'
        '</main></body></html>')

    assert result.fields['title'] == '东湖花园 4室2厅'


def test_blank_h1_falls_back_to_nonblank_document_title():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><head><title>东湖花园 4室2厅 | 贝壳找房</title></head>'
        '<body><h1>   </h1><main>'
        '小区：东湖花园 建筑面积：160㎡ 总价：365万'
        '</main></body></html>')

    assert result.fields['title'] == '东湖花园 4室2厅 | 贝壳找房'


def test_h1_title_preserves_contiguous_inline_text():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><head></head><body><h1>东湖<span>花</span><em>园</em> 3室</h1>'
        '<main>小区：东湖花园 建筑面积：120㎡ 总价：300万</main></body></html>')

    assert result.fields['title'] == '东湖花园 3室'
    assert result.fields['field_evidence']['title']['source'] == 'h1'


def test_conflicting_open_graph_titles_fall_back_to_unambiguous_h1():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><head>'
        '<meta property="og:title" content="推荐房源" />'
        '<meta property="og:title" content="附近热销房源" />'
        '<title>贝壳找房</title></head><body>'
        '<h1>东湖花园 4室2厅</h1><main>'
        '小区：东湖花园 建筑面积：160㎡ 总价：365万'
        '</main></body></html>')

    assert result.fields['title'] == '东湖花园 4室2厅'
    assert result.fields['field_evidence']['title']['source'] == 'h1'
    assert 'ambiguous_title_source:og:title' in result.warnings


def test_conflicting_h1_titles_fall_back_to_document_title():
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><head><title>东湖花园 4室2厅</title></head><body>'
        '<h1>推荐房源</h1><h1>附近热销</h1><main>'
        '小区：东湖花园 建筑面积：160㎡ 总价：365万'
        '</main></body></html>')

    assert result.fields['title'] == '东湖花园 4室2厅'
    assert result.fields['field_evidence']['title']['source'] == 'head:title'
    assert 'ambiguous_title_source:h1' in result.warnings


def test_nested_h1_title_candidates_stop_after_conflict_without_quadratic_walk(monkeypatch):
    depth = 80
    nested = ''.join(f'<h1>标题{i}' for i in range(depth))
    nested += '房源' + '</h1>' * depth
    html = ('<html><head><title>文档标题</title></head><body>' + nested
            + '<main>小区：东湖花园 建筑面积：120㎡ 总价：300万</main></body></html>')
    original_children = Tag.children.fget
    original_text = parser_module._text_with_inline_boundaries
    child_visits = 0
    h1_extractions = 0

    def counted_children(node):
        nonlocal child_visits
        for child in original_children(node):
            child_visits += 1
            yield child

    def count_h1_extractions(node, *args, **kwargs):
        nonlocal h1_extractions
        if isinstance(node, Tag) and node.name == 'h1':
            h1_extractions += 1
        return original_text(node, *args, **kwargs)

    monkeypatch.setattr(Tag, 'children', property(counted_children))
    monkeypatch.setattr(parser_module, '_text_with_inline_boundaries', count_h1_extractions)

    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['title'] == '文档标题'
    assert 'ambiguous_title_source:h1' in result.warnings
    assert h1_extractions == 2
    assert child_visits <= depth * 16


def test_nested_equal_h1_transparent_wrappers_only_extract_one_title_subtree(monkeypatch):
    depth = 80
    nested = '东湖花园房源'
    for _ in range(depth):
        nested = ('<h1><i class="icon"><span></span></i><span>'
                  + nested + '</span></h1>')
    html = ('<html><body>' + nested + '<main>'
            + '小区：东湖花园 建筑面积：120㎡ 总价：300万'
            + '</main></body></html>')
    original_text = parser_module._text_with_inline_boundaries
    h1_extractions = 0

    def count_h1_extractions(node, *args, **kwargs):
        nonlocal h1_extractions
        if isinstance(node, Tag) and node.name == 'h1':
            h1_extractions += 1
        return original_text(node, *args, **kwargs)

    monkeypatch.setattr(parser_module, '_text_with_inline_boundaries',
                        count_h1_extractions)

    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['title'] == '东湖花园房源'
    assert 'ambiguous_title_source:h1' not in result.warnings
    assert h1_extractions == 1


def test_parser_bounds_repeated_inline_style_property_scans(monkeypatch):
    style = ('color:#333;display:block;visibility:visible;opacity:1;'
             'content-visibility:visible;padding:2px')
    html = ('<html><body><main>小区：东湖花园 建筑面积：120㎡ 总价：300万 '
            f'<span style="{style}">房源说明</span></main></body></html>')
    original = parser_module._scan_inline_css_values
    scans = 0

    def count_style_scans(style_text, property_names):
        nonlocal scans
        if style_text == style:
            scans += 1
        return original(style_text, property_names)

    monkeypatch.setattr(parser_module, '_scan_inline_css_values', count_style_scans)

    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['asking_price_wan'] == 300
    assert scans == 1


def test_parser_caches_repeated_inline_styles_only_within_each_parse(monkeypatch):
    style = (';'.join(f'padding-{index}:1px' for index in range(12))
             + ';display:inline;visibility:visible;opacity:1;content-visibility:visible')
    repeated = ''.join(f'<span style="{style}">描述{index}</span>'
                       for index in range(50))
    html = ('<html><body><main>小区：东湖花园 建筑面积：120㎡ 总价：300万 '
            + repeated + '</main></body></html>')
    original = parser_module._scan_inline_css_values
    scanned_property_sets = []

    def count_unique_style_scans(style_text, property_names):
        if style_text == style:
            scanned_property_sets.append(frozenset(property_names))
        return original(style_text, property_names)

    monkeypatch.setattr(parser_module, '_scan_inline_css_values', count_unique_style_scans)

    for _ in range(2):
        before = len(scanned_property_sets)
        result = parse_listing_html(
            'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)
        parse_scans = scanned_property_sets[before:]

        assert result.fields['asking_price_wan'] == 300
        assert parse_scans == [parser_module._INLINE_CSS_CACHED_PROPERTIES]
        assert parser_module._INLINE_CSS_PARSE_CACHE.get() is None

    assert len(scanned_property_sets) == 2
    with pytest.raises(CollectionError):
        parse_listing_html('beike', 'https://nb.ke.com/ershoufang/109900001234.html', 'too short')
    assert parser_module._INLINE_CSS_PARSE_CACHE.get() is None


def test_inline_css_parse_cache_replaces_old_entries_at_its_limit(monkeypatch):
    monkeypatch.setattr(parser_module, 'INLINE_CSS_PARSE_CACHE_LIMIT', 4)
    styles = [f'color:#{index:06x};display:inline' for index in range(5)]
    token = parser_module._INLINE_CSS_PARSE_CACHE.set({})
    try:
        for style in styles[:4]:
            parser_module._inline_css_values(style, ('display',))
        parser_module._inline_css_values(styles[0], ('display',))
        parser_module._inline_css_values(styles[4], ('display',))
        parser_module._inline_css_values(styles[4], ('display',))
        cache = parser_module._INLINE_CSS_PARSE_CACHE.get()
        assert len(cache) == 4
        assert styles[0] not in cache
        assert styles[4] in cache
    finally:
        parser_module._INLINE_CSS_PARSE_CACHE.reset(token)


def test_inline_css_parse_cache_disabled_scans_only_requested_properties(monkeypatch):
    monkeypatch.setattr(parser_module, 'INLINE_CSS_PARSE_CACHE_LIMIT', 0)
    style = 'display:block;visibility:hidden;opacity:0'
    original = parser_module._scan_inline_css_values
    scanned_property_sets = []

    def count_scans(style_text, property_names):
        scanned_property_sets.append(frozenset(property_names))
        return original(style_text, property_names)

    monkeypatch.setattr(parser_module, '_scan_inline_css_values', count_scans)
    token = parser_module._INLINE_CSS_PARSE_CACHE.set({})
    try:
        values = parser_module._inline_css_values(style, ('display',))
        assert values == {'display': 'block'}
        assert scanned_property_sets == [frozenset(('display',))]
        assert parser_module._INLINE_CSS_PARSE_CACHE.get() == {}
    finally:
        parser_module._INLINE_CSS_PARSE_CACHE.reset(token)


def test_inline_css_parse_cache_reuses_hot_style_after_unique_styles_fill_it(monkeypatch):
    monkeypatch.setattr(parser_module, 'INLINE_CSS_PARSE_CACHE_LIMIT', 8)
    common = 'color:#ffffff;display:inline;visibility:visible;opacity:1;content-visibility:visible'
    unique_styles = [
        f'color:#{index:06x};display:inline;visibility:visible;opacity:1;content-visibility:visible'
        for index in range(20)
    ]
    body = ''.join(f'<span style="{style}">u{index}</span>'
                   for index, style in enumerate(unique_styles))
    body += ''.join(f'<span style="{common}">r{index}</span>' for index in range(100))
    html = ('<html><body><main>小区：东湖花园 建筑面积：120㎡ 总价：300万 '
            + body + '</main></body></html>')
    original = parser_module._scan_inline_css_values
    common_scan_property_sets = []
    largest_cache = 0

    def count_common_scans(style_text, property_names):
        nonlocal largest_cache
        if style_text == common:
            common_scan_property_sets.append(frozenset(property_names))
        cache = parser_module._INLINE_CSS_PARSE_CACHE.get()
        if cache is not None:
            largest_cache = max(largest_cache, len(cache))
        return original(style_text, property_names)

    monkeypatch.setattr(parser_module, '_scan_inline_css_values', count_common_scans)

    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['asking_price_wan'] == 300
    assert 1 <= len(common_scan_property_sets) <= 5
    assert set(common_scan_property_sets) == {parser_module._INLINE_CSS_CACHED_PROPERTIES}
    assert largest_cache == 8
    assert parser_module._INLINE_CSS_PARSE_CACHE.get() is None


def test_parser_stops_at_first_maximal_candidate_root(monkeypatch):
    nested = '<span>' * 80 + '小区：东湖花园 建筑面积：120㎡ 总价：300万' + '</span>' * 80
    html = ('<html><body><main><article><div class="content">' + nested
            + '</div></article></main></body></html>')
    original_text = parser_module._text_with_inline_boundaries
    original_find = BeautifulSoup.find
    original_select_one = BeautifulSoup.select_one
    candidate_calls = {}
    root_queries = []

    def count_find(node, name=None, *args, **kwargs):
        if name in ('main', 'article'):
            root_queries.append(name)
        return original_find(node, name, *args, **kwargs)

    def count_select_one(node, selector, *args, **kwargs):
        if selector == '.houseInfo, .house-info, .content':
            root_queries.append('content')
        return original_select_one(node, selector, *args, **kwargs)

    def count_candidate_text(node):
        if isinstance(node, Tag) and (
                node.name in ('main', 'article') or 'content' in (node.get('class') or [])):
            key = (node.name, tuple(node.get('class') or []))
            candidate_calls[key] = candidate_calls.get(key, 0) + 1
        return original_text(node)

    monkeypatch.setattr(parser_module, '_text_with_inline_boundaries', count_candidate_text)
    monkeypatch.setattr(BeautifulSoup, 'find', count_find)
    monkeypatch.setattr(BeautifulSoup, 'select_one', count_select_one)

    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['community_name'] == '东湖花园'
    assert result.fields['area_sqm'] == 120
    assert result.fields['asking_price_wan'] == 300
    assert candidate_calls == {('main', ()): 1}
    assert root_queries == ['main']


def test_parser_normalizes_selected_candidate_text_only_once(monkeypatch):
    html = ('<html><body><main>唯一候选标记 小区：东湖花园 建筑面积：120㎡ '
            '总价：300万</main><article>忽略根</article></body></html>')
    original_normalize = parser_module._normalize_text_prefix
    candidate_normalizations = 0

    def count_candidate_normalizations(text, limit):
        nonlocal candidate_normalizations
        if '唯一候选标记' in text:
            candidate_normalizations += 1
        return original_normalize(text, limit)

    monkeypatch.setattr(parser_module, '_normalize_text_prefix', count_candidate_normalizations)

    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['community_name'] == '东湖花园'
    assert result.fields['area_sqm'] == 120
    assert result.fields['asking_price_wan'] == 300
    assert candidate_normalizations == 1


def test_candidate_root_scoring_uses_the_same_text_window_as_field_extraction():
    listing = '小区：东湖花园 建筑面积：120㎡ 总价：300万'
    long_prefix = '导航内容' * (parser_module.MAX_VISIBLE_TEXT_CHARS // 4 + 1)
    html = ('<html><body><main>' + long_prefix
            + '<article>' + listing + '</article></main></body></html>')

    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['community_name'] == '东湖花园'
    assert result.fields['area_sqm'] == 120
    assert result.fields['asking_price_wan'] == 300
    assert result.ready_for_review


def test_candidate_root_scoring_prefers_in_range_values_over_invalid_sibling_root():
    html = ('<html><body><main>小区：旧信息 建筑面积：0㎡ 总价：0万</main>'
            '<article>小区：东湖花园 建筑面积：120㎡ 总价：300万</article>'
            '</body></html>')

    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['community_name'] == '东湖花园'
    assert result.fields['area_sqm'] == 120
    assert result.fields['asking_price_wan'] == 300
    assert result.ready_for_review


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize(('invalid_field', 'invalid_root'), [
    ('area_sqm', '小区：东湖花园 建筑面积：12,34㎡ 总价：300万'),
    ('asking_price_wan', '小区：东湖花园 建筑面积：120㎡ 总价：12,34万'),
])
def test_candidate_root_scoring_does_not_promote_malformed_thousands_grouping(
        source, source_url, invalid_field, invalid_root):
    valid_root = '建筑面积：120㎡ 总价：300万'
    html = (f'<html><body><div class="content">{valid_root}</div>'
            f'<div class="houseInfo">{invalid_root}</div></body></html>')

    result = parse_listing_html(source, source_url, html)

    assert result.fields['area_sqm'] == 120
    assert result.fields['asking_price_wan'] == 300
    assert result.fields['community_name'] is None


def test_candidate_root_scoring_does_not_count_contract_price_as_listing_evidence():
    html = ('<html><body><main>小区：东湖花园 建筑面积：120㎡ 合同总价：300万</main>'
            '<article>小区：东湖花园 建筑面积：120㎡ 挂牌价：320万</article>'
            '</body></html>')

    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['community_name'] == '东湖花园'
    assert result.fields['area_sqm'] == 120
    assert result.fields['asking_price_wan'] == 320
    assert result.ready_for_review


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
def test_candidate_root_scoring_excludes_linked_contract_listing_price(
        source, source_url):
    html = ('<html><body>'
            '<div class="houseInfo">小区：东湖花园 建筑面积：120㎡ 合同中的挂牌价：300万</div>'
            '<div class="content">小区：东湖花园 建筑面积：120㎡ 挂牌价：320万</div>'
            '</body></html>')

    result = parse_listing_html(source, source_url, html)

    assert result.fields['asking_price_wan'] == 320
    assert result.fields['area_sqm'] == 120
    assert result.ready_for_review


@pytest.mark.parametrize(('first_class', 'listing_class'), [
    ('houseInfo', 'content'),
    ('house-info', 'houseInfo'),
    ('content', 'house-info'),
])
def test_candidate_root_scoring_checks_later_class_root_with_listing_fields(
        first_class, listing_class):
    html = (f'<html><body><div class="{first_class}">推荐阅读</div>'
            f'<div class="{listing_class}">小区：东湖花园 建筑面积：120㎡ 挂牌价：320万</div>'
            '</body></html>')

    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['community_name'] == '东湖花园'
    assert result.fields['area_sqm'] == 120
    assert result.fields['asking_price_wan'] == 320
    assert result.ready_for_review


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
def test_candidate_root_scoring_checks_later_matching_class_root(source, source_url):
    html = ('<html><body><div class="content">推荐阅读</div>'
            '<div class="content">小区：东湖花园 建筑面积：120㎡ 挂牌价：320万</div>'
            '</body></html>')

    result = parse_listing_html(source, source_url, html)

    assert result.fields['community_name'] == '东湖花园'
    assert result.fields['area_sqm'] == 120
    assert result.fields['asking_price_wan'] == 320
    assert result.ready_for_review


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
def test_candidate_root_scoring_checks_later_article_with_listing_fields(source, source_url):
    html = ('<html><body><article>推荐阅读</article>'
            '<article>小区：东湖花园 建筑面积：120㎡ 挂牌价：320万</article>'
            '</body></html>')

    result = parse_listing_html(source, source_url, html)

    assert result.fields['community_name'] == '东湖花园'
    assert result.fields['area_sqm'] == 120
    assert result.fields['asking_price_wan'] == 320
    assert result.ready_for_review


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
def test_nested_content_price_conflict_within_article_stays_pending(source, source_url):
    html = ('<html><body><article>小区：东湖花园 建筑面积：120㎡ 挂牌价：300万 '
            '<div class="content">小区：东湖花园 建筑面积：120㎡ 挂牌价：320万</div>'
            '</article></body></html>')

    result = parse_listing_html(source, source_url, html)

    assert result.fields['asking_price_wan'] is None
    assert 'multiple_price_mentions' in result.warnings
    assert not result.ready_for_review
    evidence = result.fields['field_evidence']['asking_price_wan']
    assert [item['candidate_value'] for item in evidence['mentions']] == ['300', '320']
    excerpt = result.fields['evidence_excerpt']
    for item in evidence['mentions']:
        assert excerpt[item['start_char']:item['end_char']] == item['quote']


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
def test_nested_content_repeated_same_price_remains_reviewable(source, source_url):
    result = parse_listing_html(
        source, source_url,
        '<html><body><article>小区：东湖花园 建筑面积：120㎡ 挂牌价：320万 '
        '<div class="content">小区：东湖花园 建筑面积：120㎡ 挂牌价：320万</div>'
        '</article></body></html>')

    assert result.fields['asking_price_wan'] == 320
    assert 'multiple_price_mentions' not in result.warnings
    assert result.ready_for_review


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
def test_nested_class_root_does_not_hide_conflicting_price_evidence(
        source, source_url, monkeypatch):
    html = ('<html><body>' + '<div class="content">' * 40
            + '小区：东湖花园 建筑面积：120㎡ 挂牌价：300万'
            '<div class="content">小区：东湖花园 建筑面积：120㎡ 挂牌价：320万</div>'
            + '</div>' * 40 + '</body></html>')
    text_walks = 0
    original = parser_module._text_with_inline_boundaries

    def count_text_walks(*args, **kwargs):
        nonlocal text_walks
        text_walks += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(parser_module, '_text_with_inline_boundaries', count_text_walks)

    result = parse_listing_html(source, source_url, html)

    assert result.fields['asking_price_wan'] is None
    assert 'multiple_price_mentions' in result.warnings
    assert not result.ready_for_review
    assert text_walks == 1


def test_candidate_root_scoring_keeps_equivalent_class_root_ties_reviewable():
    html = ('<html><body><div class="content">小区：东湖花园 建筑面积：120㎡ 挂牌价：320万</div>'
            '<div class="houseInfo">小区：东湖花园 建筑面积：120.0㎡ 挂牌价：320.00万</div>'
            '</body></html>')

    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['community_name'] == '东湖花园'
    assert result.fields['area_sqm'] == 120
    assert result.fields['asking_price_wan'] == 320
    assert result.ready_for_review


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize(('field', 'left_value', 'right_value', 'warning'), [
    ('community_name', '东湖花园', '锦港府', 'multiple_community_mentions'),
    ('area_sqm', '120㎡', '130㎡', 'multiple_area_mentions'),
    ('asking_price_wan', '320万', '350万', 'multiple_price_mentions'),
])
def test_equal_score_independent_roots_clear_only_conflicting_fields(
        source, source_url, field, left_value, right_value, warning):
    values = {'community_name': '东湖花园', 'area_sqm': '120㎡',
              'asking_price_wan': '320万'}
    values[field] = left_value
    other_values = values.copy()
    other_values[field] = right_value
    left = (f'小区：{values["community_name"]} 建筑面积：{values["area_sqm"]} '
            f'挂牌价：{values["asking_price_wan"]}')
    right = (f'小区：{other_values["community_name"]} '
             f'建筑面积：{other_values["area_sqm"]} '
             f'挂牌价：{other_values["asking_price_wan"]}')
    html = (f'<html><body><div class="content">{left}</div>'
            f'<div class="houseInfo">{right}</div></body></html>')

    result = parse_listing_html(source, source_url, html)

    assert result.fields[field] is None
    assert warning in result.warnings
    expected_mentions = {
        'community_name': ['东湖花园', '锦港府'],
        'area_sqm': ['120', '130'],
        'asking_price_wan': ['320', '350'],
    }[field]
    evidence = result.fields['field_evidence'][field]
    assert evidence['value'] is None
    assert [mention['candidate_value'] for mention in evidence['mentions']] == expected_mentions
    excerpt = result.fields['evidence_excerpt']
    for mention in evidence['mentions']:
        assert excerpt[mention['start_char']:mention['end_char']] == mention['quote']
    for other_field, raw_value in values.items():
        if other_field == field:
            continue
        expected = {'community_name': raw_value,
                    'area_sqm': 120,
                    'asking_price_wan': 320}[other_field]
        assert result.fields[other_field] == expected
    assert not result.ready_for_review


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize(('field', 'left_detail', 'right_detail', 'warning'), [
    ('district', '所在区域：鄞州', '所在区域：海曙', 'multiple_district_mentions'),
    ('bedrooms', '户型：2室', '户型：3室', 'multiple_bedrooms_mentions'),
    ('floor_text', '楼层：高楼层', '楼层：低楼层', 'multiple_floor_mentions'),
    ('decoration', '装修：精装', '装修：毛坯', 'multiple_decoration_mentions'),
])
def test_equal_score_independent_roots_clear_conflicting_optional_fields(
        source, source_url, field, left_detail, right_detail, warning):
    common = '小区：东湖花园 建筑面积：120㎡ 挂牌价：320万 '
    html = (f'<html><body><div class="content">{common}{left_detail}</div>'
            f'<div class="houseInfo">{common}{right_detail}</div></body></html>')

    result = parse_listing_html(source, source_url, html)

    assert result.fields[field] is None
    assert warning in result.warnings
    assert result.fields['community_name'] == '东湖花园'
    assert result.fields['area_sqm'] == 120
    assert result.fields['asking_price_wan'] == 320
    assert result.ready_for_review


def test_candidate_root_conflicted_ranges_do_not_hide_clear_sibling_article():
    html = ('<html><body><main>导航推荐 小区：导航推荐 建筑面积：120-130㎡ '
            '建筑面积：125㎡ 总价：365万</main>'
            '<article>小区：东湖花园 建筑面积：120㎡ 总价：300万</article>'
            '</body></html>')

    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['community_name'] == '东湖花园'
    assert result.fields['area_sqm'] == 120
    assert result.fields['asking_price_wan'] == 300
    assert result.ready_for_review


def test_candidate_root_scoring_treats_equivalent_numeric_mentions_as_one_value():
    html = ('<html><body><main>小区：东湖花园 建筑面积：1,234㎡ 建面：1234.0㎡ '
            '总价：1,234万 挂牌价：1234.00万</main>'
            '<article>小区：锦港府 建筑面积：120㎡</article>'
            '</body></html>')

    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['community_name'] == '东湖花园'
    assert result.fields['area_sqm'] == 1234
    assert result.fields['asking_price_wan'] == 1234
    assert result.ready_for_review


def test_candidate_root_scoring_finds_conflict_after_equivalent_mentions():
    html = ('<html><body><main>小区：东湖花园 建筑面积：1,234㎡ 建面：1234.0㎡ '
            '建筑面积：1300㎡ 总价：1,234万 挂牌价：1234.00万 总价：1300万</main>'
            '<article>小区：锦港府 建筑面积：120㎡ 总价：300万</article>'
            '</body></html>')

    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['community_name'] == '锦港府'
    assert result.fields['area_sqm'] == 120
    assert result.fields['asking_price_wan'] == 300
    assert result.ready_for_review


def test_maximal_outer_root_does_not_hide_conflicting_recommendation_fields():
    html = ('<html><body><main>'
            '<section>推荐小区：推荐花园 建筑面积：90㎡ 总价：100万</section>'
            '<article>小区：东湖花园 建筑面积：120㎡ 总价：300万</article>'
            '</main></body></html>')

    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['community_name'] is None
    assert result.fields['area_sqm'] is None
    assert result.fields['asking_price_wan'] is None
    assert 'multiple_community_mentions' in result.warnings
    assert 'multiple_area_mentions' in result.warnings
    assert 'multiple_price_mentions' in result.warnings
    assert not result.ready_for_review


@pytest.mark.parametrize(('suffix', 'is_truncated'), [('', False), ('x', True)])
def test_candidate_text_limit_has_an_exact_inclusive_boundary(monkeypatch, suffix, is_truncated):
    listing = '小区：东湖花园 建筑面积：120㎡ 总价：300万'
    text = ('x' * (parser_module.MAX_VISIBLE_TEXT_CHARS - len(listing))
            + listing + suffix)
    original_text = parser_module._text_with_inline_boundaries

    def candidate_text(node, *args, **kwargs):
        if isinstance(node, Tag) and node.name == 'main':
            return text
        return original_text(node, *args, **kwargs)

    monkeypatch.setattr(parser_module, '_text_with_inline_boundaries', candidate_text)

    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>ignored</main></body></html>')

    assert result.fields['community_name'] == '东湖花园'
    assert result.fields['area_sqm'] == 120
    assert result.fields['asking_price_wan'] == 300
    assert ('visible_text_truncated' in result.warnings) is is_truncated
    assert result.ready_for_review is (not is_truncated)
    for field in ('community_name', 'area_sqm', 'asking_price_wan'):
        mentions = result.fields['field_evidence'][field]['mentions']
        assert all(
            item['end_char'] <= parser_module.MAX_VISIBLE_TEXT_CHARS
            and text[item['start_char']:item['end_char']] == item['quote']
            and item['candidate_value'] in item['quote']
            for item in mentions
        )


@pytest.mark.parametrize(('field', 'base', 'partial_range', 'hidden_tail', 'other_value'), [
    ('area_sqm', '小区：东湖花园 总价：300万 ', '建筑面积：120㎡-', '130㎡', 300),
    ('asking_price_wan', '小区：东湖花园 建筑面积：120㎡ ', '总价：300万-', '320万', 120),
])
@pytest.mark.parametrize('separator', ['-', '−', '－', '–', '—', '~', '～', '〜', '至', '到'])
def test_truncated_range_separator_does_not_promote_its_first_endpoint(
        monkeypatch, field, base, partial_range, hidden_tail, other_value, separator):
    limit = parser_module.MAX_VISIBLE_TEXT_CHARS
    partial_range = partial_range[:-1] + separator
    visible = base + 'x' * (limit - len(base) - len(partial_range)) + partial_range
    original_text = parser_module._text_with_inline_boundaries

    def range_cut_text(node, *args, **kwargs):
        if isinstance(node, Tag) and node.name == 'main':
            return visible + hidden_tail
        return original_text(node, *args, **kwargs)

    monkeypatch.setattr(parser_module, '_text_with_inline_boundaries', range_cut_text)
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        '<html><body><main>ignored</main></body></html>')

    assert result.fields[field] is None
    assert result.fields['asking_price_wan' if field == 'area_sqm' else 'area_sqm'] == other_value
    assert 'visible_text_truncated' in result.warnings
    assert not result.ready_for_review


def test_parser_keeps_searching_when_later_candidate_has_stronger_evidence(monkeypatch):
    html = ('<html><body><main><article><div class="content">正文</div>'
            '</article></main></body></html>')
    original_text = parser_module._text_with_inline_boundaries
    candidate_calls = []

    def candidate_text(node):
        if isinstance(node, Tag) and node.name in ('main', 'article', 'div'):
            candidate_calls.append(node.name)
            if node.name == 'main':
                return '小区：东湖花园 建筑面积：120㎡'
            return '小区：东湖花园 建筑面积：120㎡ 总价：300万'
        return original_text(node)

    monkeypatch.setattr(parser_module, '_text_with_inline_boundaries', candidate_text)

    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['asking_price_wan'] == 300
    assert candidate_calls == ['main', 'article']


def test_parser_preprocessing_bounds_full_document_walks(monkeypatch):
    html = ('<html><head><style>.ad{display:none}</style></head><body><main>'
            '小区：东湖花园 建筑面积：160㎡ 总价：365万'
            '<div hidden>推荐房源 总价：900万</div>'
            '<div style="display:none">广告 总价：800万</div>'
            '<dialog>对话框 总价：700万</dialog>'
            '<details><summary>房源简介</summary><p>推荐房源 总价：600万</p></details>'
            '</main></body></html>')
    original_descendants = Tag.descendants.fget
    document_walks = 0

    def count_document_walks(node):
        nonlocal document_walks
        if node.name == '[document]':
            document_walks += 1
        yield from original_descendants(node)

    monkeypatch.setattr(Tag, 'descendants', property(count_document_walks))

    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['asking_price_wan'] == 365
    assert 'multiple_price_mentions' not in result.warnings
    assert 'unresolved_stylesheet_visibility' in result.warnings
    assert document_walks <= 6


def test_nested_collapsed_details_summaries_are_textified_once(monkeypatch):
    depth = 80
    nested = '末尾'
    for index in reversed(range(depth)):
        nested = (f'<details><summary>层{index}' + nested
                  + '</summary><p>折叠内容</p></details>')
    html = ('<html><body><main>小区：东湖花园 建筑面积：120㎡ 总价：300万'
            '<details><summary>起始' + nested
            + '</summary><p>外层折叠内容</p></details></main></body></html>')
    original_text = parser_module._text_with_inline_boundaries
    summary_walks = 0

    def count_summary_walks(node, *args, **kwargs):
        nonlocal summary_walks
        if isinstance(node, Tag) and node.name == 'summary':
            summary_walks += 1
        return original_text(node, *args, **kwargs)

    monkeypatch.setattr(parser_module, '_text_with_inline_boundaries', count_summary_walks)

    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html', html)

    assert result.fields['asking_price_wan'] == 300
    assert 'multiple_price_mentions' not in result.warnings
    assert summary_walks == 1


def test_summary_whitespace_trimming_batches_leading_part_removal():
    class CountingParts(list):
        def __init__(self, values):
            super().__init__(values)
            self.front_pops = 0
            self.slice_deletions = 0

        def pop(self, index=-1):
            self.front_pops += index == 0
            return super().pop(index)

        def __delitem__(self, key):
            self.slice_deletions += isinstance(key, slice)
            return super().__delitem__(key)

    parts = CountingParts(['前缀'] + [' '] * 4000 + [' 摘要\n'])

    parser_module._strip_text_parts(parts, 1)

    assert parts == ['前缀', '摘要']
    assert parts.front_pops == 0
    assert parts.slice_deletions == 1


@pytest.mark.parametrize(('head', 'body', 'expected_source', 'expected_quote'), [
    ('<meta property="og:title" content="东湖花园 4室2厅">',
     '<h1>备用标题</h1>', 'og:title', '东湖花园 4室2厅'),
    ('', '<h1>东湖花园 4室2厅</h1>', 'h1', '东湖花园 4室2厅'),
    ('<title>东湖花园 4室2厅 | 贝壳找房</title>', '',
     'head:title', '东湖花园 4室2厅 | 贝壳找房'),
])
def test_title_evidence_records_selected_source_and_quote(head, body, expected_source, expected_quote):
    result = parse_listing_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001234.html',
        f'<html><head>{head}</head><body>{body}<main>'
        '小区：东湖花园 建筑面积：160㎡ 总价：365万'
        '</main></body></html>')

    assert result.fields['field_evidence']['title'] == {
        'value': result.fields['title'],
        'source': expected_source,
        'quote': expected_quote,
    }
