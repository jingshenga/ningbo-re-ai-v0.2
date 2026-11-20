"""Social ingest tests: Ningbo detection, proof-hash dedupe, validation, auth,
and an end-to-end simulated push through the real API layer (DB faked).

Fixture key follows the repo pattern: NBRE_TEST_API_KEY env override with a
fixed non-secret placeholder default; wrong-key negatives derive from it.
"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from app import social_service
from app.main import app
from app.routers import social_ingest
from app.schemas.social_ingest import SocialPlatformEnum, SocialPostIngestPayload
from app.social_store import insert_social_post_row

TEST_API_KEY = os.environ.get("NBRE_TEST_API_KEY", "local-test-placeholder-key")

NINGBO_POST = (
    "宁波东部新城这套房真笋！海曙学区房挂了三个月终于降价，"
    "业主急售，建筑面积89平，挂牌价189万，比同小区上个月低了两成。"
)
SHANGHAI_POST = "上海浦东内环新房开盘，均价10万每平，当天售罄。"


def client_loopback():
    return TestClient(app, client=("127.0.0.1", 12345))


def client_public():
    return TestClient(app, client=("93.184.216.34", 12345))


def payload(**overrides):
    base = {
        "platform": "xiaohongshu",
        "source_url": "https://www.xiaohongshu.com/explore/abcdef1234567890abcdef",
        "title": "宁波东部新城笋盘",
        "content": NINGBO_POST,
        "author_name": "宁波看房日记",
        "media_urls": ["https://sns-img.xhscdn.com/abc.jpg"],
        "tags": ["宁波买房"],
    }
    base.update(overrides)
    return base


class FakeResult:
    def __init__(self, row):
        self._row = row

    def fetchone(self):
        return self._row


class FakeConn:
    """SELECT returns None (no existing row); the INSERT is never reached here."""

    def __init__(self):
        self.selects = 0

    def execute(self, query, params):
        assert query.startswith("SELECT"), "test fake must not see an INSERT"
        self.selects += 1
        assert "%s" in query  # parameterized, never interpolated
        return FakeResult(None)


def fake_session_factory(conn):
    from contextlib import contextmanager

    @contextmanager
    def session():
        yield conn
    return session


STORED_ROW = {
    "id": "0f7d5c1e-1111-4111-8111-000000000001",
    "raw_sha256": "a" * 64,
    "is_ningbo_related": True,
    "matched_keywords": ["宁波", "东部新城", "海曙"],
    "extracted_hints": {"price_mentions_wan": [189.0], "area_mentions_sqm": [89.0],
                        "confidence_status": "not_calibrated"},
}


# ---------- 纯函数：宁波关键词与存证哈希 ----------
def test_ningbo_keyword_detection_matches_districts_and_zones():
    matched = social_service.match_ningbo_keywords(
        "镇海区骆驼街道老盘", "前湾新区新盘首付两成", None)
    assert matched == ["镇海", "前湾新区"]


def test_ningbo_keyword_detection_ignores_non_ningbo_city_content():
    assert social_service.match_ningbo_keywords(SHANGHAI_POST) == []


def test_sha256_is_whitespace_and_fragment_insensitive():
    base = social_service.compute_raw_sha256(
        "xiaohongshu", "https://www.xiaohongshu.com/explore/abc123", NINGBO_POST)
    messy = social_service.compute_raw_sha256(
        " xiaohongshu ",
        "https://www.xiaohongshu.com/explore/abc123/#utm_track",
        NINGBO_POST.replace("\n", "  \r\n  ") + "  ")
    assert base == messy


def test_sha256_changes_when_content_changes():
    first = social_service.compute_raw_sha256("douyin", "https://www.douyin.com/video/v1", "A")
    second = social_service.compute_raw_sha256("douyin", "https://www.douyin.com/video/v1", "B")
    assert first != second


# ---------- 服务层：去重事务与参数绑定（注入 INSERT seam） ----------
def test_persist_selects_duplicate_first_and_binds_all_values():
    conn = FakeConn()
    monkey_session = fake_session_factory(conn)
    original_session = social_service.session
    social_service.session = monkey_session
    try:
        insert_calls = []

        def fake_insert(conn_, values):
            insert_calls.append((conn_, values))
            return dict(STORED_ROW), True

        row, created = social_service.persist_social_post(
            SocialPostIngestPayload(**payload()), insert_row=fake_insert)
    finally:
        social_service.session = original_session

    assert created is True
    assert conn.selects == 1
    assert len(insert_calls) == 1
    _, values = insert_calls[0]
    assert values["content"] == NINGBO_POST
    assert values["platform"] == "xiaohongshu"
    assert values["raw_sha256"] == social_service.compute_raw_sha256(
        "xiaohongshu", payload()["source_url"], NINGBO_POST)
    assert values["matched_keywords"] is not None  # Jsonb-wrapped keyword list


def test_persist_returns_existing_row_without_insert():
    existing_row = dict(STORED_ROW)
    conn = FakeConn()
    insert_calls = []

    def fake_insert(conn_, values):
        insert_calls.append(values)
        return existing_row, True

    def select_returns_existing(query, params):
        assert query.startswith("SELECT")
        return FakeResult(existing_row)

    class ExistingConn:
        def execute(self, query, params):
            return select_returns_existing(query, params)

    original_session = social_service.session
    social_service.session = fake_session_factory(ExistingConn())
    try:
        row, created = social_service.persist_social_post(
            SocialPostIngestPayload(**payload()), insert_row=fake_insert)
    finally:
        social_service.session = original_session

    assert created is False
    assert row["raw_sha256"] == STORED_ROW["raw_sha256"]
    assert insert_calls == []  # duplicate path never inserts


def test_persist_returns_existing_row_when_concurrent_insert_wins():
    class RaceConn:
        def __init__(self):
            self.selects = 0

        def execute(self, query, params):
            assert query.startswith("SELECT")
            self.selects += 1
            return FakeResult(None if self.selects == 1 else dict(STORED_ROW))

    conn = RaceConn()
    original_session = social_service.session
    social_service.session = fake_session_factory(conn)
    try:
        row, created = social_service.persist_social_post(
            SocialPostIngestPayload(**payload()),
            insert_row=lambda _conn, _values: (None, False))
    finally:
        social_service.session = original_session

    assert created is False
    assert row["raw_sha256"] == STORED_ROW["raw_sha256"]
    assert conn.selects == 2


def test_store_returns_inserted_flag_and_never_updates_duplicate():
    class InsertConn:
        def execute(self, query, params):
            assert query.startswith("INSERT INTO social_posts")
            assert "ON CONFLICT (raw_sha256) DO NOTHING" in query
            assert "DO UPDATE" not in query
            assert query.count("%s") == len(params) == 15
            return FakeResult(dict(STORED_ROW))

    values = {
        "platform": "xiaohongshu", "post_id": None,
        "source_url": payload()["source_url"], "title": "标题",
        "content": NINGBO_POST, "author_name": None, "publish_time": None,
        "media_urls": [], "tags": [], "raw_html_snippet": None,
        "raw_sha256": "a" * 64, "is_ningbo_related": True,
        "matched_keywords": ["宁波"], "extracted_hints": {}, "status": "new",
    }

    row, inserted = insert_social_post_row(InsertConn(), values)

    assert row["id"] == STORED_ROW["id"]
    assert inserted is True


# ---------- 端到端模拟：真实 API 层（持久化 mock） ----------
def test_api_stores_post_returns_calibrated_warning(monkeypatch):
    client = client_loopback()
    monkeypatch.setattr(social_ingest, "APP_API_KEY", "")
    monkeypatch.setattr(social_service, "persist_social_post",
                        lambda payload_, insert_row=None: (dict(STORED_ROW), True))
    response = client.post("/api/v1/ingest/social", json=payload())
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "stored"
    assert body["is_ningbo_related"] is True
    assert "宁波" in body["matched_keywords"]
    assert body["hints"]["confidence_status"] == "not_calibrated"


def test_api_rejects_content_without_ningbo_keywords(monkeypatch):
    client = client_loopback()
    monkeypatch.setattr(social_ingest, "APP_API_KEY", "")
    response = client.post(
        "/api/v1/ingest/social",
        json=payload(content=SHANGHAI_POST, title="上海新房", tags=["上海"]))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "not_ningbo_related"


def test_api_rejects_unrecognized_payload_fields(monkeypatch):
    monkeypatch.setattr(social_ingest, "APP_API_KEY", "")
    response = client_loopback().post(
        "/api/v1/ingest/social", json=payload(unexpected="ignored data"))
    assert response.status_code == 422


def test_api_duplicate_returns_existing_without_insert(monkeypatch):
    client = client_loopback()
    monkeypatch.setattr(social_ingest, "APP_API_KEY", "")
    monkeypatch.setattr(social_service, "persist_social_post",
                        lambda payload_, insert_row=None: (dict(STORED_ROW), False))
    response = client.post("/api/v1/ingest/social", json=payload())
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "duplicate"
    assert body["sha256"] == STORED_ROW["raw_sha256"]


def test_api_reports_storage_pending_honestly(monkeypatch):
    client = client_loopback()
    monkeypatch.setattr(social_ingest, "APP_API_KEY", "")

    def raise_pending(payload_, insert_row=None):
        raise RuntimeError("social_posts persistence is pending")

    monkeypatch.setattr(social_service, "persist_social_post", raise_pending)
    response = client.post("/api/v1/ingest/social", json=payload())
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "storage_pending"


def test_default_seam_matches_documented_contract():
    """Without app/social_store.py the default seam must fail loudly (503
    storage_pending path); once the store lands it must resolve to a callable
    so the endpoint flips to real persistence with zero code changes."""
    if social_service.insert_social_post_row is None:
        with pytest.raises(RuntimeError, match="persistence is pending"):
            social_service.persist_social_post(
                SocialPostIngestPayload(**payload()), insert_row=None)
    else:
        assert callable(social_service.insert_social_post_row)


# ---------- 校验：非法字段 ----------
def test_api_rejects_http_source_url(monkeypatch):
    client = client_loopback()
    monkeypatch.setattr(social_ingest, "APP_API_KEY", "")
    response = client.post(
        "/api/v1/ingest/social",
        json=payload(source_url="http://www.xiaohongshu.com/explore/abc123"))
    assert response.status_code == 422


def test_api_rejects_host_platform_mismatch(monkeypatch):
    client = client_loopback()
    monkeypatch.setattr(social_ingest, "APP_API_KEY", "")
    response = client.post(
        "/api/v1/ingest/social",
        json=payload(platform="xiaohongshu",
                     source_url="https://www.douyin.com/video/999"))
    assert response.status_code == 422


def test_api_rejects_blank_content_and_bad_media_urls(monkeypatch):
    client = client_loopback()
    monkeypatch.setattr(social_ingest, "APP_API_KEY", "")
    assert client.post("/api/v1/ingest/social",
                       json=payload(content="   ")).status_code == 422
    assert client.post(
        "/api/v1/ingest/social",
        json=payload(media_urls=["javascript:alert(1)"])).status_code == 422


# ---------- 鉴权：key 模式与回环豁免 ----------
def test_ingest_requires_api_key_when_configured(monkeypatch):
    client = client_loopback()
    monkeypatch.setattr(social_ingest, "APP_API_KEY", TEST_API_KEY)
    denied = client.post("/api/v1/ingest/social", json=payload())
    assert denied.status_code == 401
    derived_wrong = TEST_API_KEY + "-x"
    wrong = client.post("/api/v1/ingest/social", json=payload(),
                        headers={"X-API-Key": derived_wrong})
    assert wrong.status_code == 401
    monkeypatch.setattr(social_service, "persist_social_post",
                        lambda payload_, insert_row=None: (dict(STORED_ROW), True))
    accepted = client.post("/api/v1/ingest/social", json=payload(),
                           headers={"X-API-Key": TEST_API_KEY})
    assert accepted.status_code == 200


def test_ingest_rejects_public_client_when_no_key_configured(monkeypatch):
    monkeypatch.setattr(social_ingest, "APP_API_KEY", "")
    client = client_public()
    response = client.post("/api/v1/ingest/social", json=payload())
    assert response.status_code == 403


def test_other_platform_allows_any_https_host(monkeypatch):
    client = client_loopback()
    monkeypatch.setattr(social_ingest, "APP_API_KEY", "")
    monkeypatch.setattr(social_service, "persist_social_post",
                        lambda payload_, insert_row=None: (dict(STORED_ROW), True))
    response = client.post(
        "/api/v1/ingest/social",
        json=payload(platform="other",
                     source_url="https://forum.example.com/thread/123",
                     content="宁波江北这套老破小值得关注"))
    assert response.status_code == 200


def test_platform_enum_covers_supported_sources():
    assert {member.value for member in SocialPlatformEnum} == {
        "xiaohongshu", "douyin", "channels", "other"}
