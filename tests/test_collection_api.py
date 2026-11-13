from contextlib import contextmanager
import gzip
import os

import pytest
from fastapi.testclient import TestClient

from app import collection_service
from app.collectors import parse_listing_html
from app.main import app

# Local fixture key for monkeypatched auth; overridable via env, never a real secret.
TEST_API_KEY = os.environ.get('NBRE_TEST_API_KEY', 'local-test-placeholder-key')


class FakeResult:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self, row):
        self.row = row
        self.params = None

    def execute(self, query, params=None):
        self.params = params
        return FakeResult(self.row)


def test_candidate_price_correction_api_returns_manual_evidence(monkeypatch):
    candidate_id = '00000000-0000-0000-0000-000000000001'
    row = {
        'id': candidate_id, 'source': 'beike', 'review_status': 'pending',
        'source_listing_id': '109900001234',
        'extracted_fields': {
            'source_listing_id': '109900001234', 'community_name': '东湖花园',
            'area_sqm': 120, 'asking_price_wan': None,
            'field_evidence': {
                'asking_price_wan': {
                    'value': None, 'mentions': [{
                        'candidate_value': '200', 'source': 'visible_listing_text',
                        'quote': '挂牌价约200万', 'start_char': 0, 'end_char': 10,
                        'is_non_exact': True,
                    }], 'mention_count': 1, 'mentions_truncated': False,
                },
            },
            'manually_corrected': False,
        },
        'warnings': ['non_exact_asking_price'],
    }

    class CandidateCorrectionConnection:
        def execute(self, query, params=None):
            if query.startswith('SELECT * FROM collection_candidates'):
                return FakeResult(row)
            assert query.startswith('UPDATE collection_candidates SET extracted_fields=')
            return FakeResult({
                **row, 'extracted_fields': params[0].obj, 'warnings': params[1].obj,
            })

    connection = CandidateCorrectionConnection()

    @contextmanager
    def fake_session():
        yield connection

    monkeypatch.setattr(collection_service, 'session', fake_session)
    monkeypatch.setattr('app.main.APP_API_KEY', TEST_API_KEY)

    with TestClient(app) as client:
        response = client.patch(
            f'/api/collection/candidates/{candidate_id}',
            headers={'X-API-Key': TEST_API_KEY},
            json={'asking_price_wan': 200, 'review_note': '对照保存页面确认挂牌价'},
        )

    body = response.json()
    fields = body['extracted_fields']
    evidence = fields['field_evidence']['asking_price_wan']
    assert response.status_code == 200
    assert fields['asking_price_wan'] == 200
    assert evidence == {
        'value': 200, 'source': 'manual_review', 'mentions': [],
        'mention_count': 0, 'mentions_truncated': False,
    }
    assert fields['manually_corrected'] is True
    assert 'non_exact_asking_price' in body['warnings']


def test_saved_html_api_reports_truncated_candidate_as_not_ready(tmp_path, monkeypatch):
    url = 'https://nb.ke.com/ershoufang/109900001234.html'
    html = ('<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万 '
            + '说明' * 18000 + ' 总价：900万</main></body></html>')
    parsed = parse_listing_html('beike', url, html)
    row = {
        'id': 'candidate-1', 'source': 'beike', 'source_url': url,
        'review_status': 'pending', 'source_listing_id': parsed.fields['source_listing_id'],
        'raw_sha256': parsed.sha256, 'raw_storage_path': 'raw-pages/synthetic.html.gz',
        'parser_version': parsed.parser_version, 'extracted_fields': parsed.fields,
        'warnings': parsed.warnings,
    }
    connection = FakeConnection(row)

    @contextmanager
    def fake_session():
        yield connection

    monkeypatch.setattr(collection_service, 'session', fake_session)
    monkeypatch.setattr(collection_service, 'RAW_HTML_DIR', str(tmp_path / 'raw-pages'))
    monkeypatch.setattr('app.main.APP_API_KEY', TEST_API_KEY)

    with TestClient(app) as client:
        response = client.post('/api/collection/pages', headers={'X-API-Key': TEST_API_KEY},
                               json={'source': 'beike', 'source_url': url, 'html': html})

    body = response.json()
    assert response.status_code == 200
    assert body['candidate']['review_status'] == 'pending'
    assert 'visible_text_truncated' in body['candidate']['warnings']
    assert body['ready_for_review'] is False
    assert 'visible_text_truncated' in connection.params[8].obj


def test_saved_html_api_returns_range_conflict_evidence(tmp_path, monkeypatch):
    url = 'https://nb.ke.com/ershoufang/109900001234.html'
    html = ('<html><body><main>小区：东湖花园 建筑面积：120㎡-130㎡ '
            '建筑面积：125㎡ 总价：365万</main></body></html>')
    parsed = parse_listing_html('beike', url, html)
    row = {
        'id': 'candidate-1', 'source': 'beike', 'source_url': url,
        'review_status': 'pending', 'source_listing_id': parsed.fields['source_listing_id'],
        'raw_sha256': parsed.sha256, 'raw_storage_path': 'raw-pages/synthetic.html.gz',
        'parser_version': parsed.parser_version, 'extracted_fields': parsed.fields,
        'warnings': parsed.warnings,
    }
    connection = FakeConnection(row)

    @contextmanager
    def fake_session():
        yield connection

    monkeypatch.setattr(collection_service, 'session', fake_session)
    monkeypatch.setattr(collection_service, 'RAW_HTML_DIR', str(tmp_path / 'raw-pages'))
    monkeypatch.setattr('app.main.APP_API_KEY', TEST_API_KEY)

    with TestClient(app) as client:
        response = client.post('/api/collection/pages', headers={'X-API-Key': TEST_API_KEY},
                               json={'source': 'beike', 'source_url': url, 'html': html})

    body = response.json()
    fields = body['candidate']['extracted_fields']
    evidence = fields['field_evidence']['area_sqm']
    assert response.status_code == 200
    assert body['ready_for_review'] is False
    assert fields['area_sqm'] is None
    assert evidence['value'] is None
    assert [item['candidate_value'] for item in evidence['mentions']] == [
        '120㎡-130㎡', '125']
    assert 'multiple_area_mentions' in body['candidate']['warnings']
    assert evidence['mentions_truncated'] is False


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize('transaction_label', [
    '合同总价', '签约总价', '评估总价', '银行评估总价', '租金总价', '原总价',
])
def test_saved_html_api_keeps_transaction_price_as_evidence_only(
        tmp_path, monkeypatch, source, source_url, transaction_label):
    html = ('<html><body><main>小区：东湖花园 建筑面积：160㎡ '
            f'{transaction_label}：300万</main></body></html>')
    parsed = parse_listing_html(source, source_url, html)
    raw_dir = tmp_path / 'raw-pages'
    raw_path = raw_dir / f'{parsed.sha256}.html.gz'
    row = {
        'id': 'candidate-1', 'source': source, 'source_url': source_url,
        'review_status': 'pending', 'source_listing_id': parsed.fields['source_listing_id'],
        'raw_sha256': parsed.sha256, 'raw_storage_path': str(raw_path),
        'parser_version': parsed.parser_version, 'extracted_fields': parsed.fields,
        'warnings': parsed.warnings,
    }
    connection = FakeConnection(row)

    @contextmanager
    def fake_session():
        yield connection

    monkeypatch.setattr(collection_service, 'session', fake_session)
    monkeypatch.setattr(collection_service, 'RAW_HTML_DIR', str(raw_dir))
    monkeypatch.setattr('app.main.APP_API_KEY', TEST_API_KEY)

    with TestClient(app) as client:
        response = client.post('/api/collection/pages', headers={'X-API-Key': TEST_API_KEY},
                               json={'source': source, 'source_url': source_url, 'html': html})

    body = response.json()
    fields = body['candidate']['extracted_fields']
    assert response.status_code == 200
    assert body['candidate']['review_status'] == 'pending'
    assert body['ready_for_review'] is False
    assert fields['asking_price_wan'] is None
    assert 'missing_asking_price_wan' in body['candidate']['warnings']
    assert f'{transaction_label}：300万' in fields['evidence_excerpt']
    assert body['note'].endswith('NOT modified.')
    with gzip.open(raw_path, 'rb') as saved:
        assert saved.read() == html.encode('utf-8')


@pytest.mark.parametrize('non_total_price', [
    '挂牌价：2万／㎡',
    '总价：3.6万/年', '租金总价：3.6万/月', '挂牌价：0.3万/天',
])
@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
def test_saved_html_api_keeps_non_total_price_out_of_total_price_candidate(
        tmp_path, monkeypatch, source, source_url, non_total_price):
    html = ('<html><body><main>小区：东湖花园 建筑面积：100㎡ '
            f'{non_total_price}</main></body></html>')
    parsed = parse_listing_html(source, source_url, html)
    raw_dir = tmp_path / 'raw-pages'
    raw_path = raw_dir / f'{parsed.sha256}.html.gz'
    row = {
        'id': 'candidate-1', 'source': source, 'source_url': source_url,
        'review_status': 'pending', 'source_listing_id': parsed.fields['source_listing_id'],
        'raw_sha256': parsed.sha256, 'raw_storage_path': str(raw_path),
        'parser_version': parsed.parser_version, 'extracted_fields': parsed.fields,
        'warnings': parsed.warnings,
    }
    connection = FakeConnection(row)

    @contextmanager
    def fake_session():
        yield connection

    monkeypatch.setattr(collection_service, 'session', fake_session)
    monkeypatch.setattr(collection_service, 'RAW_HTML_DIR', str(raw_dir))
    monkeypatch.setattr('app.main.APP_API_KEY', TEST_API_KEY)

    with TestClient(app) as client:
        response = client.post('/api/collection/pages', headers={'X-API-Key': TEST_API_KEY},
                               json={'source': source, 'source_url': source_url, 'html': html})

    body = response.json()
    fields = body['candidate']['extracted_fields']
    assert response.status_code == 200
    assert body['candidate']['review_status'] == 'pending'
    assert body['ready_for_review'] is False
    assert fields['asking_price_wan'] is None
    assert 'asking_price_wan' not in fields['field_evidence']
    assert 'missing_asking_price_wan' in body['candidate']['warnings']
    assert body['note'].endswith('NOT modified.')
    with gzip.open(raw_path, 'rb') as saved:
        assert saved.read() == html.encode('utf-8')


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
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
    ('约：', True), ('估算：', True),
    ('≥', True), ('≤', True),
])
def test_saved_html_api_stages_approximate_price_for_manual_correction(
        tmp_path, monkeypatch, source, source_url, qualifier, before_amount):
    price = f'{qualifier}200万' if before_amount else f'200万{qualifier}'
    html = ('<html><body><main>小区：东湖花园 建筑面积：100㎡ '
            f'挂牌价：{price}</main></body></html>')
    parsed = parse_listing_html(source, source_url, html)
    raw_dir = tmp_path / 'raw-pages'
    raw_path = raw_dir / f'{parsed.sha256}.html.gz'
    row = {
        'id': 'candidate-1', 'source': source, 'source_url': source_url,
        'review_status': 'pending', 'source_listing_id': parsed.fields['source_listing_id'],
        'raw_sha256': parsed.sha256, 'raw_storage_path': str(raw_path),
        'parser_version': parsed.parser_version, 'extracted_fields': parsed.fields,
        'warnings': parsed.warnings,
    }
    connection = FakeConnection(row)

    @contextmanager
    def fake_session():
        yield connection

    monkeypatch.setattr(collection_service, 'session', fake_session)
    monkeypatch.setattr(collection_service, 'RAW_HTML_DIR', str(raw_dir))
    monkeypatch.setattr('app.main.APP_API_KEY', TEST_API_KEY)

    with TestClient(app) as client:
        response = client.post('/api/collection/pages', headers={'X-API-Key': TEST_API_KEY},
                               json={'source': source, 'source_url': source_url, 'html': html})

    body = response.json()
    fields = body['candidate']['extracted_fields']
    assert response.status_code == 200
    assert body['candidate']['review_status'] == 'pending'
    assert body['ready_for_review'] is False
    assert fields['asking_price_wan'] is None
    assert 'non_exact_asking_price' in body['candidate']['warnings']
    evidence = fields['field_evidence']['asking_price_wan']
    assert evidence['value'] is None
    assert evidence['mentions'][0]['candidate_value'] == '200'
    assert evidence['mentions'][0]['quote'] == f'挂牌价：{price}'
    assert all(mention['is_non_exact'] is True for mention in evidence['mentions'])
    stored_evidence = connection.params[7].obj['field_evidence']['asking_price_wan']
    assert all(mention['is_non_exact'] is True for mention in stored_evidence['mentions'])
    assert body['note'].endswith('NOT modified.')
    with gzip.open(raw_path, 'rb') as saved:
        assert saved.read() == html.encode('utf-8')


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize(('price_text', 'candidate'), [
    ('挂牌价：300-320万左右', '300-320万'),
    ('挂牌价：300万-320万以上', '300万-320万'),
    ('挂牌价约：300-320万', '300-320万'),
])
def test_saved_html_api_preserves_qualified_price_range_evidence(
        tmp_path, monkeypatch, source, source_url, price_text, candidate):
    html = ('<html><body><main>小区：东湖花园 建筑面积：100㎡ '
            f'{price_text}</main></body></html>')
    parsed = parse_listing_html(source, source_url, html)
    raw_dir = tmp_path / 'raw-pages'
    raw_path = raw_dir / f'{parsed.sha256}.html.gz'
    row = {
        'id': 'candidate-1', 'source': source, 'source_url': source_url,
        'review_status': 'pending', 'source_listing_id': parsed.fields['source_listing_id'],
        'raw_sha256': parsed.sha256, 'raw_storage_path': str(raw_path),
        'parser_version': parsed.parser_version, 'extracted_fields': parsed.fields,
        'warnings': parsed.warnings,
    }
    connection = FakeConnection(row)

    @contextmanager
    def fake_session():
        yield connection

    monkeypatch.setattr(collection_service, 'session', fake_session)
    monkeypatch.setattr(collection_service, 'RAW_HTML_DIR', str(raw_dir))
    monkeypatch.setattr('app.main.APP_API_KEY', TEST_API_KEY)

    with TestClient(app) as client:
        response = client.post('/api/collection/pages', headers={'X-API-Key': TEST_API_KEY},
                               json={'source': source, 'source_url': source_url, 'html': html})

    body = response.json()
    fields = body['candidate']['extracted_fields']
    evidence = fields['field_evidence']['asking_price_wan']
    assert response.status_code == 200
    assert body['candidate']['review_status'] == 'pending'
    assert fields['asking_price_wan'] is None
    assert {'multiple_price_mentions', 'non_exact_asking_price'} <= set(
        body['candidate']['warnings'])
    assert evidence['mentions'][0]['candidate_value'] == candidate
    assert evidence['mentions'][0]['quote'] == price_text
    assert evidence['mentions'][0]['is_non_exact'] is True
    stored_evidence = connection.params[7].obj['field_evidence']['asking_price_wan']
    assert stored_evidence == evidence
    with gzip.open(raw_path, 'rb') as saved:
        assert saved.read() == html.encode('utf-8')


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize('area_text', [
    '约100㎡', '100㎡左右', '100㎡以上', '100㎡起', '100㎡+', '≥100㎡', '大于100㎡',
    '100㎡封顶', '100㎡起步', '在100㎡左右', '参考100㎡', '估算100㎡', '估计100㎡', '预估100㎡',
    '100㎡参考', '100㎡估算', '100㎡估计', '100㎡预估', '约：100㎡', '估算：100㎡',
    '约建筑面积：100㎡', '估算建面：100㎡', '参考建筑面积：100㎡-120㎡',
])
def test_saved_html_api_stages_non_exact_area_for_manual_review(
        tmp_path, monkeypatch, source, source_url, area_text):
    area_quote = (area_text if area_text.startswith(
        ('约建筑面积：', '估算建面：', '参考建筑面积：'))
        else f'建筑面积：{area_text}')
    html = (f'<html><body><main>小区：东湖花园 {area_quote} '
            '总价：365万</main></body></html>')
    parsed = parse_listing_html(source, source_url, html)
    raw_dir = tmp_path / 'raw-pages'
    raw_path = raw_dir / f'{parsed.sha256}.html.gz'
    row = {
        'id': 'candidate-1', 'source': source, 'source_url': source_url,
        'review_status': 'pending', 'source_listing_id': parsed.fields['source_listing_id'],
        'raw_sha256': parsed.sha256, 'raw_storage_path': str(raw_path),
        'parser_version': parsed.parser_version, 'extracted_fields': parsed.fields,
        'warnings': parsed.warnings,
    }
    connection = FakeConnection(row)

    @contextmanager
    def fake_session():
        yield connection

    monkeypatch.setattr(collection_service, 'session', fake_session)
    monkeypatch.setattr(collection_service, 'RAW_HTML_DIR', str(raw_dir))
    monkeypatch.setattr('app.main.APP_API_KEY', TEST_API_KEY)

    with TestClient(app) as client:
        response = client.post('/api/collection/pages', headers={'X-API-Key': TEST_API_KEY},
                               json={'source': source, 'source_url': source_url, 'html': html})

    body = response.json()
    fields = body['candidate']['extracted_fields']
    evidence = fields['field_evidence']['area_sqm']
    assert response.status_code == 200
    assert body['candidate']['review_status'] == 'pending'
    assert body['ready_for_review'] is False
    assert fields['area_sqm'] is None
    assert 'non_exact_area_sqm' in body['candidate']['warnings']
    assert evidence['value'] is None
    assert evidence['mentions'][0]['quote'] == area_quote
    assert evidence['mentions'][0]['is_non_exact'] is True
    stored_evidence = connection.params[7].obj['field_evidence']['area_sqm']
    assert stored_evidence == evidence
    with gzip.open(raw_path, 'rb') as saved:
        assert saved.read() == html.encode('utf-8')


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
@pytest.mark.parametrize(('area_text', 'candidate'), [
    ('建筑面积：100㎡-120㎡左右', '100㎡-120㎡'),
    ('建筑面积约：100㎡-120㎡', '100㎡-120㎡'),
    ('建筑面积估算：100㎡-120㎡', '100㎡-120㎡'),
])
def test_saved_html_api_preserves_qualified_area_range_evidence(
        tmp_path, monkeypatch, source, source_url, area_text, candidate):
    html = f'<html><body><main>小区：东湖花园 {area_text} 总价：365万</main></body></html>'
    parsed = parse_listing_html(source, source_url, html)
    raw_dir = tmp_path / 'raw-pages'
    raw_path = raw_dir / f'{parsed.sha256}.html.gz'
    row = {
        'id': 'candidate-1', 'source': source, 'source_url': source_url,
        'review_status': 'pending', 'source_listing_id': parsed.fields['source_listing_id'],
        'raw_sha256': parsed.sha256, 'raw_storage_path': str(raw_path),
        'parser_version': parsed.parser_version, 'extracted_fields': parsed.fields,
        'warnings': parsed.warnings,
    }
    connection = FakeConnection(row)

    @contextmanager
    def fake_session():
        yield connection

    monkeypatch.setattr(collection_service, 'session', fake_session)
    monkeypatch.setattr(collection_service, 'RAW_HTML_DIR', str(raw_dir))
    monkeypatch.setattr('app.main.APP_API_KEY', TEST_API_KEY)

    with TestClient(app) as client:
        response = client.post('/api/collection/pages', headers={'X-API-Key': TEST_API_KEY},
                               json={'source': source, 'source_url': source_url, 'html': html})

    body = response.json()
    fields = body['candidate']['extracted_fields']
    evidence = fields['field_evidence']['area_sqm']
    assert response.status_code == 200
    assert body['candidate']['review_status'] == 'pending'
    assert body['ready_for_review'] is False
    assert fields['area_sqm'] is None
    assert {'multiple_area_mentions', 'non_exact_area_sqm'} <= set(
        body['candidate']['warnings'])
    assert evidence['value'] is None
    assert evidence['mentions'][0]['candidate_value'] == candidate
    assert evidence['mentions'][0]['quote'] == area_text
    assert evidence['mentions'][0]['is_non_exact'] is True
    stored_evidence = connection.params[7].obj['field_evidence']['area_sqm']
    assert stored_evidence == evidence
    with gzip.open(raw_path, 'rb') as saved:
        assert saved.read() == html.encode('utf-8')


@pytest.mark.parametrize(('source', 'source_url'), [
    ('beike', 'https://nb.ke.com/ershoufang/109900001234.html'),
    ('anjuke', 'https://ningbo.anjuke.com/sale/1234567890'),
])
def test_saved_html_api_keeps_exact_price_before_folded_start_summary(
        tmp_path, monkeypatch, source, source_url):
    html = ('<html><body><main>小区：东湖花园 建筑面积：100㎡ 总价：300万'
            '<details><summary>起始摘要</summary><p>折叠内容</p></details>'
            '</main></body></html>')
    parsed = parse_listing_html(source, source_url, html)
    raw_dir = tmp_path / 'raw-pages'
    raw_path = raw_dir / f'{parsed.sha256}.html.gz'
    row = {
        'id': 'candidate-1', 'source': source, 'source_url': source_url,
        'review_status': 'pending', 'source_listing_id': parsed.fields['source_listing_id'],
        'raw_sha256': parsed.sha256, 'raw_storage_path': str(raw_path),
        'parser_version': parsed.parser_version, 'extracted_fields': parsed.fields,
        'warnings': parsed.warnings,
    }
    connection = FakeConnection(row)

    @contextmanager
    def fake_session():
        yield connection

    monkeypatch.setattr(collection_service, 'session', fake_session)
    monkeypatch.setattr(collection_service, 'RAW_HTML_DIR', str(raw_dir))
    monkeypatch.setattr('app.main.APP_API_KEY', TEST_API_KEY)

    with TestClient(app) as client:
        response = client.post('/api/collection/pages', headers={'X-API-Key': TEST_API_KEY},
                               json={'source': source, 'source_url': source_url, 'html': html})

    body = response.json()
    fields = body['candidate']['extracted_fields']
    assert response.status_code == 200
    assert body['candidate']['review_status'] == 'pending'
    assert fields['asking_price_wan'] == 300
    assert 'non_exact_asking_price' not in body['candidate']['warnings']
    assert 'multiple_price_mentions' not in body['candidate']['warnings']
    assert fields['field_evidence']['asking_price_wan']['mentions'][0][
        'candidate_value'] == '300'
    with gzip.open(raw_path, 'rb') as saved:
        assert saved.read() == html.encode('utf-8')


def test_saved_html_api_rejects_nul_before_storage_or_database_access(tmp_path, monkeypatch):
    url = 'https://nb.ke.com/ershoufang/109900001234.html'
    html = ('<html><body><main>小区：东湖花园 建筑面积：160㎡ 总价：365万'
            '\x00</main></body></html>')

    def unexpected_session():
        raise AssertionError('database must not be accessed for invalid HTML')

    monkeypatch.setattr(collection_service, 'session', unexpected_session)
    raw_dir = tmp_path / 'raw-pages'
    monkeypatch.setattr(collection_service, 'RAW_HTML_DIR', str(raw_dir))
    monkeypatch.setattr('app.main.APP_API_KEY', TEST_API_KEY)

    with TestClient(app) as client:
        response = client.post('/api/collection/pages', headers={'X-API-Key': TEST_API_KEY},
                               json={'source': 'beike', 'source_url': url, 'html': html})

    assert response.status_code == 422
    assert 'NUL character' in str(response.json()['detail'])
    assert not raw_dir.exists()


def test_candidate_approval_api_requires_numeric_precision_correction(monkeypatch):
    candidate_id = '00000000-0000-0000-0000-000000000001'
    connection = FakeConnection({
        'id': candidate_id, 'source': 'beike',
        'source_url': 'https://nb.ke.com/ershoufang/109900001234.html',
        'review_status': 'pending', 'captured_at': None,
        'extracted_fields': {
            'source_listing_id': '109900001234', 'community_name': '东湖花园',
            'area_sqm': 160.005, 'asking_price_wan': 365.005,
        },
        'warnings': ['numeric_precision_requires_correction:area_sqm',
                     'numeric_precision_requires_correction:asking_price_wan'],
    })

    @contextmanager
    def fake_session():
        yield connection

    monkeypatch.setattr(collection_service, 'session', fake_session)
    monkeypatch.setattr('app.main.APP_API_KEY', TEST_API_KEY)

    with TestClient(app) as client:
        response = client.post(
            f'/api/collection/candidates/{candidate_id}/review',
            headers={'X-API-Key': TEST_API_KEY},
            params={'decision': 'approve', 'note': '已核对原始页面'},
        )

    assert response.status_code == 409
    assert response.json()['detail']['fields'] == ['area_sqm', 'asking_price_wan']
