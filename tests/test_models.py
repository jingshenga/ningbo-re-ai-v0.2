import pytest
from pydantic import ValidationError
from app.models import (AccountIn, AccountPatch, CommunityIn, ListingIn, SavedSearchIn,
                        VideoBatch, VideoEnrichment, VideoIn)


def test_account_douyin_profile():
    x=AccountIn(platform='douyin',account_ref='https://www.douyin.com/user/ABC')
    assert x.poll_interval_minutes==120


@pytest.mark.parametrize('account_ref', [' ', ' a '])
def test_account_ref_is_validated_after_trimming(account_ref):
    with pytest.raises(ValidationError):
        AccountIn(platform='wechat_channels', account_ref=account_ref)


def test_account_ref_trims_outer_whitespace_before_length_validation():
    account = AccountIn(platform='wechat_channels', account_ref=' profile-id ')
    assert account.account_ref == 'profile-id'


@pytest.mark.parametrize('source_post_id', [' ', ' \t\n '])
def test_video_source_post_id_rejects_blank_after_trimming(source_post_id):
    with pytest.raises(ValidationError):
        VideoIn(platform='douyin', source_post_id=source_post_id)


def test_video_source_post_id_trims_outer_whitespace():
    video = VideoIn(platform='douyin', source_post_id=' post-id ')
    assert video.source_post_id == 'post-id'


@pytest.mark.parametrize('name', [' ', ' \t\n '])
def test_saved_search_name_rejects_blank_after_trimming(name):
    with pytest.raises(ValidationError):
        SavedSearchIn(name=name)


def test_saved_search_name_trims_outer_whitespace_before_length_validation():
    search = SavedSearchIn(name=' 可执行条件单 ')
    assert search.name == '可执行条件单'


def test_saved_search_optional_text_filters_normalize_blank_and_trim():
    search = SavedSearchIn(name=' 条件单 ', district=' 鄞州 ', community_name='   ')
    assert search.name == '条件单'
    assert search.district == '鄞州'
    assert search.community_name is None


def test_account_douyin_profile_accepts_case_insensitive_https_scheme():
    x=AccountIn(platform='douyin',account_ref='HTTPS://www.douyin.com/user/ABC')
    assert x.account_ref=='HTTPS://www.douyin.com/user/ABC'


@pytest.mark.parametrize('suffix', [
    '?share_token=secret#profile', '?', '#', '?share_token=secret', '#profile',
])
def test_douyin_profile_url_drops_query_and_fragment(suffix):
    x=AccountIn(platform='douyin',
                account_ref='https://www.douyin.com/user/ABC' + suffix)
    assert x.account_ref == 'https://www.douyin.com/user/ABC'


def test_non_douyin_url_rejected():
    with pytest.raises(ValidationError):
        AccountIn(platform='douyin',account_ref='https://other.example/user/ABC')


@pytest.mark.parametrize('account_ref', [
    'HTTPS://other.example/user/ABC',
    'https://user@www.douyin.com/user/ABC',
    'https://www.douyin.com:444/user/ABC',
])
def test_douyin_profile_url_rejects_untrusted_authority(account_ref):
    with pytest.raises(ValidationError):
        AccountIn(platform='douyin', account_ref=account_ref)


def test_price_unit_and_area_validation():
    with pytest.raises(ValidationError):
        ListingIn(source='agent',source_listing_id='z1',community_name='东湖花园',
                  asking_price_wan=-5,area_sqm=160)
    x=SavedSearchIn(name='示例',max_price_wan=400,min_area_sqm=140,min_bedrooms=4)
    assert str(x.max_price_wan)=='400.00'


@pytest.mark.parametrize(('model', 'field', 'values'), [
    (ListingIn, 'bedrooms', {
        'source': 'other', 'source_listing_id': 'manual-1', 'community_name': '东湖花园',
        'area_sqm': 100, 'asking_price_wan': 100,
    }),
    (SavedSearchIn, 'min_bedrooms', {'name': '条件单'}),
    (SavedSearchIn, 'max_listing_age_days', {'name': '条件单'}),
])
def test_bedroom_counts_reject_boolean_values(model, field, values):
    with pytest.raises(ValidationError, match='not a boolean'):
        model(**values, **{field: True})


@pytest.mark.parametrize(('model', 'values'), [
    (AccountPatch, {'enabled': 0}),
    (CommunityIn, {'name': '东湖花园', 'verified': 0}),
    (SavedSearchIn, {'name': '条件单', 'notifications_enabled': 0}),
])
@pytest.mark.parametrize('value', [0, 1])
def test_model_boolean_flags_reject_numeric_values(model, values, value):
    values = {key: value if isinstance(item, int) else item for key, item in values.items()}
    with pytest.raises(ValidationError):
        model(**values)


@pytest.mark.parametrize(('model', 'values'), [
    (AccountPatch, {'nickname': 'name\x00suffix'}),
    (VideoIn, {'platform': 'douyin', 'source_post_id': 'post-1', 'title': 'title\x00suffix'}),
    (VideoEnrichment, {'transcript': 'caption\x00suffix'}),
    (CommunityIn, {'name': '东湖花园', 'address': 'address\x00suffix'}),
    (ListingIn, {
        'source': 'other', 'source_listing_id': 'manual-1', 'community_name': '东湖花园',
        'area_sqm': 100, 'asking_price_wan': 100, 'title': 'title\x00suffix',
    }),
    (SavedSearchIn, {'name': 'search\x00suffix'}),
    (VideoBatch, {'items': [{
        'platform': 'douyin', 'source_post_id': 'post-1', 'description': 'text\x00suffix',
    }]}),
])
def test_persisted_model_text_rejects_nul_recursively(model, values):
    with pytest.raises(ValidationError, match='NUL character'):
        model(**values)


@pytest.mark.parametrize(('field', 'value'), [
    ('area_sqm', '120.001'),
    ('asking_price_wan', '365.001'),
])
def test_listing_rejects_values_that_database_would_round(field, value):
    values = {
        'source': 'beike', 'source_listing_id': '109900001234',
        'community_name': '东湖花园', 'area_sqm': '120', 'asking_price_wan': '365',
    }
    values[field] = value

    with pytest.raises(ValidationError, match='two decimal places'):
        ListingIn(**values)


def test_listing_accepts_values_equivalent_to_two_decimal_places():
    listing = ListingIn(source='beike', source_listing_id='109900001234',
        community_name='东湖花园', area_sqm='120.2300', asking_price_wan='365.120')

    assert str(listing.area_sqm) == '120.23'
    assert str(listing.asking_price_wan) == '365.12'


def test_listing_accepts_long_fractional_zero_tails_without_rounding():
    tail = '0' * 50
    listing = ListingIn(
        source='beike', source_listing_id='109900001234', community_name='东湖花园',
        area_sqm='120.' + tail, asking_price_wan='365.' + tail)

    assert str(listing.area_sqm) == '120.00'
    assert str(listing.asking_price_wan) == '365.00'


@pytest.mark.parametrize(('field', 'value'), [
    ('max_price_wan', '365.001'),
    ('min_area_sqm', '80.001'),
    ('min_drop_pct', '5.001'),
])
def test_saved_search_rejects_values_that_database_would_round(field, value):
    with pytest.raises(ValidationError, match='two decimal places'):
        SavedSearchIn(name='精度测试', **{field: value})


def test_saved_search_filters_are_normalized_and_bounded():
    x=SavedSearchIn(name='示例', districts=[' 鄞州 ', '海曙', '鄞州'],
                    preferred_communities=[' 东湖花园 ', '东湖花园'],
                    excluded_communities=['锦港府'], max_listing_age_days=30)
    assert x.districts == ['鄞州', '海曙']
    assert x.preferred_communities == ['东湖花园']
    assert x.excluded_communities == ['锦港府']
    with pytest.raises(ValidationError):
        SavedSearchIn(name='太久', max_listing_age_days=3651)


@pytest.mark.parametrize(('source', 'source_listing_id'), [
    ('beike', '1234567'),
    ('beike', 'listing-123'),
    ('anjuke', '123456'),
    ('anjuke', 'listing-123'),
])
def test_listing_rejects_source_ids_outside_platform_format(source, source_listing_id):
    with pytest.raises(ValidationError):
        ListingIn(
            source=source, source_listing_id=source_listing_id,
            community_name='东湖花园', area_sqm='120', asking_price_wan='365')


@pytest.mark.parametrize(('source', 'source_listing_id'), [
    ('beike', '12345678'),
    ('anjuke', '1234567'),
    ('agent', 'agent-id-1'),
    ('other', 'legacy/source-1'),
])
def test_listing_accepts_each_source_id_boundary(source, source_listing_id):
    listing = ListingIn(
        source=source, source_listing_id=source_listing_id,
        community_name='东湖花园', area_sqm='120', asking_price_wan='365')

    assert listing.source_listing_id == source_listing_id


@pytest.mark.parametrize('source', ['beike', 'anjuke', 'agent', 'other'])
@pytest.mark.parametrize('source_listing_id', [' ', '  \t\n '])
def test_listing_rejects_blank_source_listing_id(source, source_listing_id):
    with pytest.raises(ValidationError):
        ListingIn(
            source=source, source_listing_id=source_listing_id,
            community_name='东湖花园', area_sqm='120', asking_price_wan='365')


def test_listing_trims_outer_whitespace_from_custom_source_id():
    listing = ListingIn(
        source='agent', source_listing_id=' agent-id-1 ',
        community_name='东湖花园', area_sqm='120', asking_price_wan='365')

    assert listing.source_listing_id == 'agent-id-1'


def test_listing_optional_text_trims_and_normalizes_blank_to_none():
    listing = ListingIn(
        source='agent', source_listing_id='agent-1', community_name='东湖花园',
        area_sqm='120', asking_price_wan='365', title='  ',
        listing_url=' \t ', district=' 鄞州 ', floor_text=' ',
        decoration=' 精装 ', permission_note='\n')

    assert listing.title is None
    assert listing.listing_url is None
    assert listing.district == '鄞州'
    assert listing.floor_text is None
    assert listing.decoration == '精装'
    assert listing.permission_note is None


@pytest.mark.parametrize('name', ['  ', ' \t\n '])
def test_community_models_reject_blank_required_names(name):
    with pytest.raises(ValidationError):
        CommunityIn(name=name)
    with pytest.raises(ValidationError):
        ListingIn(
            source='agent', source_listing_id='agent-1', community_name=name,
            area_sqm='120', asking_price_wan='365')


def test_community_models_trim_required_names():
    assert CommunityIn(name=' 东湖花园 ').name == '东湖花园'
    listing = ListingIn(
        source='agent', source_listing_id='agent-1', community_name=' 东湖花园 ',
        area_sqm='120', asking_price_wan='365')
    assert listing.community_name == '东湖花园'
