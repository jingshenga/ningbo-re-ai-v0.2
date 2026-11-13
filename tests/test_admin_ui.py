import re
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
                        lambda candidate_id, payload: received.append((candidate_id, payload.title)))
    client.post("/admin/login", data={"password": "test-admin-key"}, follow_redirects=False)
    page = client.get(f"/admin/candidates/{candidate_id}")
    csrf = re.search(r'name="csrf" value="([a-f0-9]+)"', page.text).group(1)

    response = client.post(f"/admin/candidates/{candidate_id}", data={
        "csrf": csrf, "action": "correct", "title": "人工核验标题",
        "review_note": "已对照原始页面",
    }, follow_redirects=False)
    assert response.status_code == 303
    assert received == [(candidate_id, "人工核验标题")]


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

