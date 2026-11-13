import gzip
import hashlib
import re
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

from fastapi.testclient import TestClient

from app import admin_ui
from app.main import app


def client_with_key(monkeypatch, **client_kwargs):
    monkeypatch.setattr(admin_ui, "APP_API_KEY", "test-admin-key")
    monkeypatch.setattr(admin_ui, "_recently_created_listings", lambda: [])
    monkeypatch.setattr(admin_ui, "_summary", lambda: {
        "listing_count": 0, "pending_count": 0, "new_count": 0, "recent_price_drop_count": 0,
    })
    monkeypatch.setattr(admin_ui.collection_service, "health_metrics", lambda: [])
    monkeypatch.setattr(admin_ui.services, "all_accounts", lambda: [])
    monkeypatch.setattr(admin_ui.services, "listings", lambda **kwargs: [])
    monkeypatch.setattr(admin_ui.services, "opportunities", lambda **kwargs: [])
    monkeypatch.setattr(admin_ui.services, "list_videos", lambda **kwargs: [])
    client_kwargs.setdefault("client", ("127.0.0.1", 12345))
    return TestClient(app, **client_kwargs)


def test_admin_dashboard_requires_signed_session_and_hides_api_key(monkeypatch):
    client = client_with_key(monkeypatch)

    assert client.get("/admin/").status_code == 401
    login = client.get("/admin/login")
    assert login.status_code == 200
    assert "test-admin-key" not in login.text
    assert "<script" not in login.text

    response = client.post("/admin/login", data={"password": "test-admin-key"}, follow_redirects=False)
    assert response.status_code == 303
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie
    assert "SameSite=strict" in cookie
    assert "test-admin-key" not in cookie

    dashboard = client.get("/admin/")
    assert dashboard.status_code == 200
    assert "尚无入库房源" in dashboard.text
    assert "尚未配置 DTK 服务" in dashboard.text
    assert "test-admin-key" not in dashboard.text
    assert "script-src &#x27;none&#x27;" in dashboard.headers["content-security-policy"] or "script-src 'none'" in dashboard.headers["content-security-policy"]
    assert dashboard.headers["cache-control"] == "no-store"


def test_admin_logout_requires_csrf_token(monkeypatch):
    client = client_with_key(monkeypatch)
    client.post("/admin/login", data={"password": "test-admin-key"}, follow_redirects=False)

    denied = client.post("/admin/logout", data={})
    assert denied.status_code == 403

    page = client.get("/admin/")
    csrf = re.search(r'name="csrf" value="([a-f0-9]+)"', page.text).group(1)
    logged_out = client.post("/admin/logout", data={"csrf": csrf}, follow_redirects=False)
    assert logged_out.status_code == 303
    assert client.get("/admin/").status_code == 401


def test_admin_login_rejects_public_client_address(monkeypatch):
    client = client_with_key(monkeypatch, client=("8.8.8.8", 12345))
    assert client.get("/admin/login").status_code == 403

def test_admin_login_rejects_forwarded_client_identity(monkeypatch):
    client = client_with_key(monkeypatch)
    response = client.get("/admin/login", headers={"x-forwarded-for": "127.0.0.1"})
    assert response.status_code == 403

def test_dashboard_labels_global_gate_and_bounded_opportunity_count(monkeypatch):
    monkeypatch.setattr(admin_ui, "ENABLE_ONLINE_COLLECTION", True)
    client = client_with_key(monkeypatch)
    monkeypatch.setattr(admin_ui.services, "opportunities", lambda **kwargs: [{}] * 1200)
    client.post("/admin/login", data={"password": "test-admin-key"}, follow_redirects=False)

    dashboard = client.get("/admin/")
    assert dashboard.status_code == 200
    assert "全局在线采集开关已开启" in dashboard.text
    assert "近 30 天挂牌降价" in dashboard.text
    assert "完整机会线索在机会页按需扫描" in dashboard.text

def test_admin_login_rejects_non_ascii_password_without_server_error(monkeypatch):
    client = client_with_key(monkeypatch)
    response = client.post("/admin/login", data={"password": "错误的密码"})
    assert response.status_code == 401

def test_admin_routes_are_hidden_from_openapi(monkeypatch):
    client = client_with_key(monkeypatch)
    schema = client.get("/openapi.json").json()
    assert "/admin/login" not in schema["paths"]
    assert "/admin/logout" not in schema["paths"]
    assert "/admin/" not in schema["paths"]


def test_logout_rejects_non_ascii_csrf_without_server_error(monkeypatch):
    client = client_with_key(monkeypatch)
    client.post("/admin/login", data={"password": "test-admin-key"}, follow_redirects=False)
    response = client.post("/admin/logout", data={"csrf": "錯誤"})
    assert response.status_code == 403

def test_dashboard_does_not_run_full_opportunity_scan(monkeypatch):
    client = client_with_key(monkeypatch)
    monkeypatch.setattr(admin_ui.services, "opportunities",
                        lambda **kwargs: (_ for _ in ()).throw(AssertionError("expensive scan")))
    client.post("/admin/login", data={"password": "test-admin-key"}, follow_redirects=False)

    dashboard = client.get("/admin/")
    assert dashboard.status_code == 200
    assert "近 30 天挂牌降价" in dashboard.text

def test_admin_listing_and_candidate_pages_render_after_login(monkeypatch):
    client = client_with_key(monkeypatch)
    monkeypatch.setattr(admin_ui, "_search_listings", lambda *args, **kwargs: [])
    monkeypatch.setattr(admin_ui.collection_service, "candidates", lambda **kwargs: [])
    client.post("/admin/login", data={"password": "test-admin-key"}, follow_redirects=False)

    listings = client.get("/admin/listings")
    candidates = client.get("/admin/candidates")
    assert listings.status_code == 200
    assert "面积下限" in listings.text
    assert "价格上限" in listings.text
    assert candidates.status_code == 200
    assert "采集候选审核" in candidates.text


def test_candidate_correction_uses_csrf_and_existing_review_service(monkeypatch):
    client = client_with_key(monkeypatch)
    candidate_id = uuid4()
    monkeypatch.setattr(admin_ui, "_candidate_detail", lambda candidate_id: {
        "id": candidate_id, "source": "beike", "source_listing_id": "12345678",
        "review_status": "pending", "captured_at": None, "source_url": "https://example.test/listing/12345678",
        "capture_method": "manual_html_snapshot", "parser_version": "test-parser",
        "raw_sha256": "a" * 64, "extracted_fields": {"title": "合成候选", "area_sqm": 90},
        "warnings": [],
    })
    received = []
    monkeypatch.setattr(admin_ui.collection_service, "correct_candidate",
                        lambda candidate_id, payload: received.append((candidate_id, payload.model_dump(exclude_unset=True))))
    client.post("/admin/login", data={"password": "test-admin-key"}, follow_redirects=False)
    page = client.get(f"/admin/candidates/{candidate_id}")
    csrf = re.search(r'name="csrf" value="([a-f0-9]+)"', page.text).group(1)

    response = client.post(f"/admin/candidates/{candidate_id}", data={
        "csrf": csrf, "action": "correct", "title": "人工核验标题", "correct_title": "1",
        "district": "", "correct_district": "1", "review_note": "已对照原始页面",
    }, follow_redirects=False)
    assert response.status_code == 303
    assert received == [(candidate_id, {"title": "人工核验标题", "district": None, "review_note": "已对照原始页面"})]


def test_html_sample_import_creates_candidate_only(monkeypatch):
    client = client_with_key(monkeypatch)
    candidate_id = uuid4()
    received = []
    monkeypatch.setattr(admin_ui.collection_service, "stage_manual_page",
                        lambda payload: (received.append(payload), {"candidate": {"id": candidate_id}})[1])
    client.post("/admin/login", data={"password": "test-admin-key"}, follow_redirects=False)
    page = client.get("/admin/import")
    csrf = re.search(r'name="csrf" value="([a-f0-9]+)"', page.text).group(1)

    response = client.post("/admin/import", data={
        "csrf": csrf, "source": "beike",
        "source_url": "https://example.test/listing/12345678",
        "html": "<html><body>synthetic sample</body></html>",
        "note": "合成测试样本",
    }, follow_redirects=False)
    assert response.status_code == 303
    assert str(candidate_id) in response.headers["location"]
    assert received[0].source == "beike"


def test_candidate_review_posts_existing_approval_service(monkeypatch):
    client = client_with_key(monkeypatch)
    candidate_id = uuid4()
    received = []
    monkeypatch.setattr(admin_ui.collection_service, "review_candidate",
                        lambda candidate_id, decision, note: received.append((candidate_id, decision, note)))
    client.post("/admin/login", data={"password": "test-admin-key"}, follow_redirects=False)
    page = client.get("/admin/")
    csrf = re.search(r'name="csrf" value="([a-f0-9]+)"', page.text).group(1)

    response = client.post(f"/admin/candidates/{candidate_id}/review", data={
        "csrf": csrf, "decision": "approve", "review_note": "审核字段和来源证据完整",
    }, follow_redirects=False)
    assert response.status_code == 303
    assert received == [(candidate_id, "approve", "审核字段和来源证据完整")]

def test_original_html_evidence_is_rendered_as_escaped_text(monkeypatch):
    client = client_with_key(monkeypatch)
    candidate_id = uuid4()
    row = {"id": candidate_id, "raw_sha256": "a" * 64}
    monkeypatch.setattr(admin_ui, "_candidate_detail", lambda candidate_id: row)
    monkeypatch.setattr(admin_ui, "_candidate_html_evidence",
                        lambda row: "<script>alert(1)</script>")
    client.post("/admin/login", data={"password": "test-admin-key"}, follow_redirects=False)

    response = client.get(f"/admin/candidates/{candidate_id}/evidence")
    assert response.status_code == 200
    assert "<script>alert" not in response.text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in response.text

def test_dashboard_links_to_all_admin_workflows(monkeypatch):
    client = client_with_key(monkeypatch)
    client.post("/admin/login", data={"password": "test-admin-key"}, follow_redirects=False)

    page = client.get("/admin/")
    assert "/admin/listings" in page.text
    assert "/admin/candidates" in page.text
    assert "/admin/import" in page.text


def test_listing_filter_accepts_blank_optional_numbers(monkeypatch):
    client = client_with_key(monkeypatch)
    monkeypatch.setattr(admin_ui, "_search_listings", lambda *args, **kwargs: [])
    client.post("/admin/login", data={"password": "test-admin-key"}, follow_redirects=False)

    response = client.get("/admin/listings?min_area_sqm=&max_area_sqm=&min_price_wan=&max_price_wan=&min_bedrooms=")
    assert response.status_code == 200


def test_blank_candidate_source_means_all_sources(monkeypatch):
    client = client_with_key(monkeypatch)
    calls = []
    monkeypatch.setattr(admin_ui.collection_service, "candidates",
                        lambda **kwargs: (calls.append(kwargs), [])[1])
    client.post("/admin/login", data={"password": "test-admin-key"}, follow_redirects=False)

    response = client.get("/admin/candidates?status=pending&source=")
    assert response.status_code == 200
    assert calls[-1]["source"] is None


def test_review_accepts_maximum_length_chinese_note(monkeypatch):
    client = client_with_key(monkeypatch)
    received = []
    monkeypatch.setattr(admin_ui.collection_service, "review_candidate",
                        lambda candidate_id, decision, note: received.append(note))
    client.post("/admin/login", data={"password": "test-admin-key"}, follow_redirects=False)
    page = client.get("/admin/")
    csrf = re.search(r'name="csrf" value="([a-f0-9]+)"', page.text).group(1)
    note = "审" * 1000

    response = client.post(f"/admin/candidates/{uuid4()}/review", data={
        "csrf": csrf, "decision": "approve", "review_note": note,
    }, follow_redirects=False)
    assert response.status_code == 303
    assert received == [note]

def test_review_error_dictionary_is_url_encoded(monkeypatch):
    from fastapi import HTTPException

    client = client_with_key(monkeypatch)
    candidate_id = uuid4()
    monkeypatch.setattr(admin_ui.collection_service, "review_candidate",
                        lambda *args: (_ for _ in ()).throw(HTTPException(
                            status_code=422, detail={"missing": "area_sqm", "说明": "需要补充"})))
    client.post("/admin/login", data={"password": "test-admin-key"}, follow_redirects=False)
    page = client.get("/admin/")
    csrf = re.search(r'name="csrf" value="([a-f0-9]+)"', page.text).group(1)

    response = client.post(f"/admin/candidates/{candidate_id}/review", data={
        "csrf": csrf, "decision": "approve", "review_note": "审核字段和来源证据完整",
    }, follow_redirects=False)
    query = parse_qs(urlsplit(response.headers["location"]).query)
    assert response.status_code == 303
    assert "area_sqm" in query["message"][0]
    assert "需要补充" in query["message"][0]

def test_listing_numeric_filters_reject_nonfinite_and_out_of_range(monkeypatch):
    client = client_with_key(monkeypatch)
    monkeypatch.setattr(admin_ui, "_search_listings", lambda *args, **kwargs: [])
    client.post("/admin/login", data={"password": "test-admin-key"}, follow_redirects=False)

    for value in ("NaN", "Infinity", "1e99999999999", "20001"):
        response = client.get(f"/admin/listings?min_area_sqm={value}")
        assert response.status_code == 422


def test_candidate_evidence_rejects_content_hash_mismatch(tmp_path, monkeypatch):
    expected = b"approved candidate evidence"
    sha = hashlib.sha256(expected).hexdigest()
    evidence_file = tmp_path / f"{sha}.html.gz"
    with gzip.open(evidence_file, "wb") as stream:
        stream.write(b"different evidence")
    monkeypatch.setattr(admin_ui, "RAW_HTML_DIR", str(tmp_path))

    assert admin_ui._candidate_html_evidence({"raw_sha256": sha}) is None

def test_candidate_filters_keep_selected_status_and_source(monkeypatch):
    client = client_with_key(monkeypatch)
    monkeypatch.setattr(admin_ui.collection_service, "candidates", lambda **kwargs: [])
    client.post("/admin/login", data={"password": "test-admin-key"}, follow_redirects=False)

    page = client.get("/admin/candidates?status=approved&source=anjuke")
    assert page.status_code == 200
    assert '<option value="approved" selected>已通过</option>' in page.text
    assert '<option value="anjuke" selected>安居客</option>' in page.text

def test_saved_search_creation_uses_existing_model_and_service(monkeypatch):
    client = client_with_key(monkeypatch)
    created = []
    search_id = uuid4()
    monkeypatch.setattr(admin_ui.services, "create_saved_search",
                        lambda payload: (created.append(payload), {"id": search_id})[1])
    monkeypatch.setattr(admin_ui.services, "all_saved_searches", lambda: [])
    client.post("/admin/login", data={"password": "test-admin-key"}, follow_redirects=False)
    page = client.get("/admin/searches")
    csrf = re.search(r'name="csrf" value="([a-f0-9]+)"', page.text).group(1)

    response = client.post("/admin/searches", data={
        "csrf": csrf, "name": "海曙改善房", "district": "海曙区",
        "max_price_wan": "350", "min_area_sqm": "90", "min_bedrooms": "3",
        "notifications_enabled": "on",
    }, follow_redirects=False)
    assert response.status_code == 303
    assert str(search_id) in response.headers["location"]
    assert created[0].district == "海曙区"
    assert str(created[0].max_price_wan) == "350"
    assert created[0].notifications_enabled is True


def test_saved_search_matches_show_existing_match_reasons(monkeypatch):
    client = client_with_key(monkeypatch)
    search_id = uuid4()
    monkeypatch.setattr(admin_ui.services, "saved_search_matches", lambda *args, **kwargs: {
        "search_id": search_id, "total": 1, "matches": [{
            "community_name": "合成小区", "district": "海曙区", "source": "beike",
            "area_sqm": 100, "bedrooms": 3, "asking_price_wan": 300,
            "match_reasons": ["区域符合", "预算符合", "面积符合"],
            "listing_url": "https://example.test/listing/1", "last_observed_at": "now",
        }],
    })
    client.post("/admin/login", data={"password": "test-admin-key"}, follow_redirects=False)

    page = client.get(f"/admin/searches/{search_id}/matches")
    assert page.status_code == 200
    assert "合成小区" in page.text
    assert "预算符合" in page.text


def test_opportunity_page_selects_window_and_shows_price_evidence(monkeypatch):
    client = client_with_key(monkeypatch)
    calls = []
    monkeypatch.setattr(admin_ui.services, "opportunities", lambda **kwargs: (
        calls.append(kwargs), [
            {"signals": ["same_listing_price_drop"], "community": "降价小区",
             "district": "海曙区", "source": "beike", "drop_from_price_wan": 330,
             "drop_to_price_wan": 300, "drop_amount_wan": 30, "drop_pct_in_window": 9.09,
             "drop_from_observed_at": "2026-01-01", "drop_to_observed_at": "2026-01-10",
             "drop_evidence_url": "https://example.test/evidence",
             "listing_url": "https://example.test/listing/1"},
            {"signals": ["cross_platform_price_gap"], "community": "比较小区",
             "source": "anjuke", "signal_reasons": ["同小区跨平台价差，待核实"]},
        ],
    )[1])
    client.post("/admin/login", data={"password": "test-admin-key"}, follow_redirects=False)

    page = client.get("/admin/opportunities?days=7")
    assert page.status_code == 200
    assert calls[-1]["days"] == 7
    assert "330 → 300 万" in page.text
    assert "降 30 万（9.09%）" in page.text
    assert "同小区跨平台价差，待核实" in page.text


def test_monitoring_page_labels_unconfigured_dtk_and_manual_accounts(monkeypatch):
    client = client_with_key(monkeypatch)
    monkeypatch.setattr(admin_ui, "DTK_BASE_URL", "")
    monkeypatch.setattr(admin_ui, "DTK_API_KEY", "")
    monkeypatch.setattr(admin_ui.services, "all_accounts", lambda: [
        {"id": uuid4(), "platform": "douyin", "collector_mode": "dtk",
         "account_ref": "douyin-user", "nickname": "抖音账号"},
        {"id": uuid4(), "platform": "wechat_channels", "collector_mode": "manual",
         "account_ref": "channels-user", "nickname": "视频号"},
    ])
    monkeypatch.setattr(admin_ui.services, "recent_runs", lambda *args, **kwargs: [])
    monkeypatch.setattr(admin_ui.services, "list_videos", lambda **kwargs: [{
        "title": "已导入视频", "platform": "wechat_channels", "processing_status": "completed",
        "published_at": "2026-01-01", "source_url": "https://example.test/video",
        "extracted_fields": {"community_mentions": ["合成小区"]},
    }])
    client.post("/admin/login", data={"password": "test-admin-key"}, follow_redirects=False)

    page = client.get("/admin/monitoring")
    assert page.status_code == 200
    assert "尚未配置DTK服务" in page.text
    assert "手工导入；无实时同步" in page.text
    assert "已导入视频" in page.text
    assert "合成小区" in page.text
