from app.extractor import extract_hints


def test_extract_price_area_community():
    r=extract_hints('【示例】东湖花园', '四室 160㎡ 原价398万，现在365万',
                    known_community_names=['东湖花园','锦港府'])
    assert r['community_mentions']==['东湖花园']
    assert r['price_mentions_wan']==[398.0,365.0]
    assert r['area_mentions_sqm']==[160.0]
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
