import pytest
from pydantic import ValidationError
from app.collection_models import (CandidateCorrection, CollectionTargetIn,
                                   CollectionTargetPatch, DiscoveryStateIn,
                                   HTMLPageIn, PolicyReviewIn)


def test_policy_review_requires_explicit_evidence():
    with pytest.raises(ValidationError):
        PolicyReviewIn(online_policy_status='approved',online_enabled=True)
    with pytest.raises(ValidationError):
        PolicyReviewIn(online_policy_status='not_reviewed',online_enabled=True,policy_reference='x')
    with pytest.raises(ValidationError):
        PolicyReviewIn(online_policy_status='approved',online_enabled=True,policy_reference='   ')
    p=PolicyReviewIn(online_policy_status='approved',online_enabled=True,
                     policy_reference='actual-written-permission-reference')
    assert p.online_enabled


def test_old_html_capture_needs_timezone():
    with pytest.raises(ValidationError):
        HTMLPageIn(source='beike',source_url='https://nb.ke.com/ershoufang/109900001234.html',
                   html='<html>'+'sample'*20+'</html>',captured_at='2026-11-09 08:00:00')


def test_html_page_enforces_utf8_byte_limit():
    with pytest.raises(ValidationError, match='1000000 UTF-8 bytes'):
        HTMLPageIn(source='beike',source_url='https://nb.ke.com/ershoufang/109900001234.html',
                   html='房' * 333334)


def test_collection_target_has_min_interval_and_default_disabled():
    with pytest.raises(ValidationError):
        CollectionTargetIn(source='beike',url='https://nb.ke.com/ershoufang/109900001234.html',
                           poll_interval_minutes=10)
    t=CollectionTargetIn(source='anjuke',url='https://ningbo.anjuke.com/sale/1234567890')
    assert not t.enabled


def test_discovery_state_rejects_unicode_iri_page_loop_alias():
    with pytest.raises(ValidationError, match='must not repeat last_page_url'):
        DiscoveryStateIn(
            revision=0, source='beike',
            last_page_url='https://nb.ke.com/ershoufang/小区',
            next_page_url='https://nb.ke.com/ershoufang/%E5%B0%8F%E5%8C%BA',
        )


@pytest.mark.parametrize(('model', 'values'), [
    (CollectionTargetIn, {
        'source': 'beike', 'url': 'https://nb.ke.com/ershoufang/109900001234.html',
        'enabled': 0,
    }),
    (CollectionTargetPatch, {'enabled': 0}),
    (PolicyReviewIn, {
        'online_policy_status': 'approved', 'policy_reference': 'permission-reference',
        'online_enabled': 0,
    }),
])
@pytest.mark.parametrize('value', [0, 1])
def test_collection_gate_booleans_reject_numeric_values(model, values, value):
    values = {key: value if isinstance(item, int) else item for key, item in values.items()}
    with pytest.raises(ValidationError):
        model(**values)


@pytest.mark.parametrize(('model', 'values'), [
    (CandidateCorrection, {'review_note': 'review\x00note'}),
    (PolicyReviewIn, {
        'online_policy_status': 'not_reviewed', 'note': 'review\x00note',
    }),
])
def test_collection_models_reject_nul_in_text(model, values):
    with pytest.raises(ValidationError, match='NUL character'):
        model(**values)


def test_candidate_correction_rejects_numbers_database_would_round():
    with pytest.raises(ValidationError, match='two decimal places'):
        CandidateCorrection(area_sqm='120.001', review_note='按页面核对修正')
    with pytest.raises(ValidationError, match='two decimal places'):
        CandidateCorrection(asking_price_wan='365.001', review_note='按页面核对修正')


def test_candidate_correction_normalizes_equivalent_numeric_scale():
    correction = CandidateCorrection(
        area_sqm='120.2300', asking_price_wan='365.1200',
        review_note='依据原始页面人工纠正')

    assert str(correction.area_sqm) == '120.23'
    assert str(correction.asking_price_wan) == '365.12'


def test_candidate_correction_rejects_boolean_bedroom_count():
    with pytest.raises(ValidationError, match='not a boolean'):
        CandidateCorrection(bedrooms=True, review_note='依据保存页面人工核对')


def test_candidate_title_correction_rejects_blank_and_trims_outer_whitespace():
    with pytest.raises(ValidationError, match='title must not be blank'):
        CandidateCorrection(title=' \t ', review_note='按原始页面纠正')

    correction = CandidateCorrection(title='  东湖花园 4室2厅  ', review_note='按原始页面纠正')

    assert correction.title == '东湖花园 4室2厅'


@pytest.mark.parametrize('field', [
    'title', 'community_name', 'district', 'floor_text', 'decoration',
    'source_listing_id', 'review_note',
])
def test_candidate_correction_rejects_whitespace_only_text(field):
    values = {'review_note': '根据保存页面人工核对'}
    values[field] = '   '

    with pytest.raises(ValidationError):
        CandidateCorrection(**values)


def test_candidate_correction_trims_text_before_length_validation():
    with pytest.raises(ValidationError):
        CandidateCorrection(community_name=' 小 ', review_note='根据页面核对更正')

    correction = CandidateCorrection(
        community_name=' 东湖花园 ', floor_text=' 高楼层 ',
        review_note=' 根据页面核对更正 ')

    assert correction.community_name == '东湖花园'
    assert correction.floor_text == '高楼层'
    assert correction.review_note == '根据页面核对更正'


def test_candidate_correction_source_listing_id_must_be_numeric():
    with pytest.raises(ValidationError):
        CandidateCorrection(source_listing_id='beike-1234567', review_note='依据页面人工核对')
