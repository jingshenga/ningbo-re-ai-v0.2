from app.extractor import extract_hints


def test_extract_price_area_community():
    r=extract_hints('【示例】东湖花园', '四室 160㎡ 原价398万，现在365万',
                    known_community_names=['东湖花园','锦港府'])
    assert r['community_mentions']==['东湖花园']
    assert r['price_mentions_wan']==[398.0,365.0]
    assert r['area_mentions_sqm']==[160.0]
    assert r['bedroom_mentions']==[4]
    assert r['method']=='rule_based_hints_not_verified'


def test_no_guess_if_empty():
    r=extract_hints('你好，今天看房')
    assert not r['price_mentions_wan']
    assert not r['area_mentions_sqm']
    assert not r['community_mentions']


def test_evidence_points_to_exact_source_span_without_calibrated_confidence():
    r=extract_hints('原价398万，现在365万', '鄞州东湖花园4室160㎡',
                    known_community_names=['东湖花园'],
                    source_labels=['ocr_text','transcript'])

    assert r['confidence_status']=='not_calibrated'
    assert r['evidence']==[
        {'field':'price_mentions_wan','value':398.0,'source':'ocr_text','quote':'398万','start_char':2,'end_char':6},
        {'field':'price_mentions_wan','value':365.0,'source':'ocr_text','quote':'365万','start_char':9,'end_char':13},
        {'field':'area_mentions_sqm','value':160.0,'source':'transcript','quote':'160㎡','start_char':8,'end_char':12},
        {'field':'bedroom_mentions','value':4,'source':'transcript','quote':'4室','start_char':6,'end_char':8},
        {'field':'district_mentions','value':'鄞州','source':'transcript','quote':'鄞州','start_char':0,'end_char':2},
        {'field':'community_mentions','value':'东湖花园','source':'transcript','quote':'东湖花园','start_char':2,'end_char':6},
    ]


def test_evidence_does_not_cross_source_boundaries():
    r=extract_hints('东湖', '花园', known_community_names=['东湖花园'],
                    source_labels=['title','description'])

    assert r['community_mentions']==[]
    assert not r['evidence']

def test_chinese_bedroom_numerals_extract_correct_values_and_evidence():
    result = extract_hints(
        '东湖花园 四室两厅',
        '两房一厅',
        source_labels=['ocr_text', 'transcript'],
    )

    assert result['bedroom_mentions'] == [4, 2]
    bedroom_evidence = [
        row for row in result['evidence'] if row['field'] == 'bedroom_mentions'
    ]
    assert bedroom_evidence == [
        {'field': 'bedroom_mentions', 'value': 4, 'source': 'ocr_text',
         'quote': '四室', 'start_char': 5, 'end_char': 7},
        {'field': 'bedroom_mentions', 'value': 2, 'source': 'transcript',
         'quote': '两房', 'start_char': 0, 'end_char': 2},
    ]
    assert result['confidence_status'] == 'not_calibrated'


def test_chinese_and_arabic_bedroom_counts_deduplicate_by_numeric_value():
    result = extract_hints('四室、4房、二室、两室、三房、3室')
    assert result['bedroom_mentions'] == [4, 2, 3]


def test_chinese_bedroom_numerals_preserve_optional_spaces():
    result = extract_hints('户型：三 室 两 厅')
    assert result['bedroom_mentions'] == [3]
    assert any(item['field'] == 'bedroom_mentions'
               and item['quote'] == '三 室' for item in result['evidence'])


def test_chinese_bedroom_match_does_not_take_suffix_of_larger_numbers():
    result = extract_hints('十一室，十室，一百室，11室，10房，0室')
    assert result['bedroom_mentions'] == []
    assert not any(item['field'] == 'bedroom_mentions' for item in result['evidence'])


def test_chinese_bedroom_ranges_are_not_claimed_as_exact_calibrated_hints():
    result = extract_hints('四室两厅 总价365万', source_labels=['ocr_text'])
    assert result['bedroom_mentions'] == [4]
    assert result['price_mentions_wan'] == [365.0]
    assert result['confidence_status'] == 'not_calibrated'
    assert '不得自动当作正式挂牌价' in result['warning']
