import re

from fastapi.testclient import TestClient

from app import admin_ui
from app.main import app


def client_with_key(monkeypatch, **client_kwargs):
    monkeypatch.setattr(admin_ui, "APP_API_KEY", "test-admin-key")
    monkeypatch.setattr(admin_ui, "_recently_created_listings", lambda: [])
    monkeypatch.setattr(admin_ui, "_summary", lambda: {
        "listing_count": 0, "pending_count": 0, "new_count": 0,
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
    assert "近 30 天机会线索" in dashboard.text
    assert "1200+" in dashboard.text

def test_admin_login_rejects_non_ascii_password_without_server_error(monkeypatch):
    client = client_with_key(monkeypatch)
    response = client.post("/admin/login", data={"password": "错误的密码"})
    assert response.status_code == 401
