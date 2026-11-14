"""Video workbench UI tests: honest backend states, session/CSRF, no key leaks.

The fixture key comes from NBRE_TEST_API_KEY (env override) with a fixed
non-secret placeholder default, matching the repo's established test pattern.
"""
import io
import os

import pytest
from fastapi.testclient import TestClient

from app import admin_media_client, admin_ui
from app.main import app

TEST_API_KEY = os.environ.get("NBRE_TEST_API_KEY", "local-test-placeholder-key")


def client_with_key(monkeypatch, **client_kwargs):
    monkeypatch.setattr(admin_ui, "APP_API_KEY", TEST_API_KEY)
    monkeypatch.setattr(admin_ui.collection_service, "health_metrics", lambda: [])
    monkeypatch.setattr(admin_ui.services, "all_accounts", lambda: [])
    monkeypatch.setattr(admin_ui.services, "list_videos", lambda **kwargs: [])
    monkeypatch.setattr(admin_ui, "_summary", lambda: {
        "listing_count": 0, "pending_count": 0, "new_count": 0, "recent_price_drop_count": 0,
    })
    monkeypatch.setattr(admin_ui, "_recently_created_listings", lambda: [])
    client_kwargs.setdefault("client", ("127.0.0.1", 12345))
    return TestClient(app, **client_kwargs)


def login(client):
    response = client.post("/admin/login", data={"password": TEST_API_KEY},
                           follow_redirects=False)
    assert response.status_code == 303
    return response


def _csrf_of(client) -> str:
    page = client.get("/admin/videos/upload")
    marker = 'name="csrf" value="'
    start = page.text.index(marker) + len(marker)
    return page.text[start:page.text.index('"', start)]


def test_video_pages_require_session(monkeypatch):
    client = client_with_key(monkeypatch)
    assert client.get("/admin/videos").status_code == 401
    assert client.get("/admin/videos/upload").status_code == 401
    assert client.get("/admin/videos/not-a-real-id").status_code == 401


def test_video_list_shows_honest_unavailable_state_without_backend(monkeypatch):
    client = client_with_key(monkeypatch)
    login(client)

    def raise_unavailable(limit=50, base=None):
        raise admin_media_client.MediaBackendUnavailable("backend unreachable: ConnectError")

    monkeypatch.setattr(admin_ui, "list_uploads", raise_unavailable)
    page = client.get("/admin/videos")
    assert page.status_code == 200
    assert "视频上传后端未接入" in page.text
    assert "不会展示任何虚构识别结果" in page.text
    # CSP stays strict: no scripts on this degraded page
    assert "script-src 'none'" in page.headers["content-security-policy"]
    assert "<script" not in page.text


def test_video_upload_page_disabled_without_backend(monkeypatch):
    client = client_with_key(monkeypatch)
    login(client)

    def raise_unavailable(limit=1, base=None):
        raise admin_media_client.MediaBackendUnavailable("backend unreachable")

    monkeypatch.setattr(admin_ui, "list_uploads", raise_unavailable)
    page = client.get("/admin/videos/upload")
    assert page.status_code == 200
    assert "仅为最终形态预览，已停用" in page.text
    assert "<fieldset disabled" in page.text


def test_video_list_and_upload_page_render_when_backend_available(monkeypatch):
    client = client_with_key(monkeypatch)
    login(client)
    jobs = [{
        "upload_id": "11111111-1111-4111-8111-111111111111",
        "title": "东湖花园实拍",
        "storage_name": "media_abcd.mp4",
        "sha256": "a" * 64,
        "size_bytes": 123456,
        "status": "completed",
        "source_type": "operator_local",
        "updated_at": "2026-11-13T12:00:00Z",
    }]
    monkeypatch.setattr(admin_ui, "list_uploads", lambda limit=50, base=None: jobs)
    page = client.get("/admin/videos")
    assert page.status_code == 200
    assert "东湖花园实拍" in page.text
    assert "completed" in page.text
    assert "上传新视频" in page.text
    # script-src relaxes to 'self' only on video pages that load the UI script
    csp = page.headers["content-security-policy"]
    assert "script-src 'self'" in csp
    assert "<script src=\"/admin/static/videos.js\" defer></script>" in page.text

    upload_page = client.get("/admin/videos/upload")
    assert upload_page.status_code == 200
    assert "<fieldset disabled" not in upload_page.text
    assert "来源与授权说明" in upload_page.text
    # the key must never appear in any admin page
    assert TEST_API_KEY not in page.text and TEST_API_KEY not in upload_page.text


def test_video_upload_post_forwards_permission_note_and_redirects(monkeypatch):
    client = client_with_key(monkeypatch)
    login(client)
    received = {}

    def fake_create_upload(file_field, fields, base=None):
        received["file_field"] = file_field[0]
        received["fields"] = fields
        return {"upload_id": "22222222-2222-4222-8222-222222222222"}

    monkeypatch.setattr(admin_ui, "create_upload", fake_create_upload)
    response = client.post(
        "/admin/videos/upload",
        data={"csrf": _csrf_of(client), "source_type": "operator_local",
              "permission_note": "自摄房源实拍，作者本人授权内部处理",
              "title": "东湖花园"},
        files={"file": ("clip.mp4", io.BytesIO(b"fake-bytes"), "video/mp4")},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/videos/22222222-2222-4222-8222-222222222222"
    assert received["file_field"] == "clip.mp4"
    assert received["fields"]["permission_note"] == "自摄房源实拍，作者本人授权内部处理"
    assert received["fields"]["source_type"] == "operator_local"


def test_video_upload_post_rejects_short_permission_note(monkeypatch):
    client = client_with_key(monkeypatch)
    login(client)
    monkeypatch.setattr(admin_ui, "create_upload", pytest.fail)
    response = client.post(
        "/admin/videos/upload",
        data={"csrf": _csrf_of(client), "source_type": "operator_local",
              "permission_note": "太短"},
        files={"file": ("clip.mp4", io.BytesIO(b"x"), "video/mp4")},
    )
    assert response.status_code == 422
    assert "至少 10 个字符" in response.text


def test_video_upload_post_requires_csrf(monkeypatch):
    client = client_with_key(monkeypatch)
    login(client)
    response = client.post(
        "/admin/videos/upload",
        data={"source_type": "operator_local", "permission_note": "授权说明足够长"},
        files={"file": ("clip.mp4", io.BytesIO(b"x"), "video/mp4")},
    )
    assert response.status_code == 403


def test_video_detail_renders_ocr_evidence_and_price_warning(monkeypatch):
    client = client_with_key(monkeypatch)
    login(client)
    job = {
        "upload_id": "33333333-3333-4333-8333-333333333333",
        "status": "completed",
        "source_type": "operator_local",
        "permission_note": "自摄房源实拍，作者本人授权内部处理",
        "sha256": "b" * 64,
        "size_bytes": 1000,
        "created_at": "2026-11-13T12:00:00Z",
        "updated_at": "2026-11-13T12:01:00Z",
        "attempts": 1,
        "result": {
            "media": {"duration_seconds": 8.0, "has_audio": True, "width": 1280, "height": 720},
            "transcript": {"status": "no_audio", "engine": "mock"},
            "ocr": {"status": "ok", "engine": "rapidocr", "model_name": "rapidocr-onnxruntime",
                    "items": [{"text": "总价：365万", "frame_index": 0,
                               "timestamp_seconds": 0.0, "confidence": 0.9996}]},
            "hints": {"price_mentions_wan": [365.0], "area_mentions_sqm": [],
                      "bedroom_mentions": [], "community_mentions": [],
                      "confidence_status": "not_calibrated",
                      "warning": "口播/字幕可能混有原价、现价、他套房及广告信息；不得自动当作正式挂牌价。",
                      "evidence": [{"field": "price_mentions_wan", "quote": "365万"}]},
        },
    }
    monkeypatch.setattr(admin_ui, "get_upload", lambda upload_id, base=None: job)
    page = client.get("/admin/videos/33333333-3333-4333-8333-333333333333")
    assert page.status_code == 200
    assert "completed" in page.text
    assert "总价：365万" in page.text
    assert "rapidocr" in page.text
    assert "not_calibrated" in page.text
    assert "不得自动当作正式挂牌价" in page.text
    assert "口播转写：no_audio" in page.text
    # keyframe thumbnails proxy through the session-authenticated admin route
    assert ('src="/admin/videos/33333333-3333-4333-8333-333333333333/frames/0"' in page.text)
    assert TEST_API_KEY not in page.text


def test_video_frame_proxy_serves_image_with_session(monkeypatch):
    client = client_with_key(monkeypatch)
    assert client.get("/admin/videos/66666666-6666-4666-8666-666666666666/frames/0").status_code == 401
    login(client)
    calls = {}

    def fake_fetch(upload_id, frame_index, base=None):
        if frame_index >= 2:  # emulate the backend's per-frame 404
            raise admin_media_client.MediaBackendError("frame_not_found", "Frame not found")
        calls["args"] = (upload_id, frame_index, base)
        return b"png-bytes", "image/png"

    monkeypatch.setattr(admin_ui, "fetch_frame", fake_fetch)
    response = client.get("/admin/videos/66666666-6666-4666-8666-666666666666/frames/0")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/png")
    assert response.content == b"png-bytes"
    assert calls["args"][1] == 0
    assert calls["args"][2].startswith("http://")  # same-origin base from the request

    bad_id = client.get("/admin/videos/zz/frames/0")
    assert bad_id.status_code == 404
    bad_index = client.get("/admin/videos/66666666-6666-4666-8666-666666666666/frames/99999")
    assert bad_index.status_code == 404
    backend_error = client.get("/admin/videos/66666666-6666-4666-8666-666666666666/frames/3")
    assert backend_error.status_code in (404, 503)


def test_client_backend_base_rejects_public_targets(monkeypatch, tmp_path):
    from app import admin_media_client
    monkeypatch.setattr(admin_media_client, "APP_API_KEY", TEST_API_KEY)
    with pytest.raises(admin_media_client.MediaBackendUnavailable):
        admin_media_client._validate_base("http://93.184.216.34:8000")
    assert admin_media_client._validate_base("http://127.0.0.1:18788") == "http://127.0.0.1:18788"
    assert admin_media_client._validate_base("http://192.168.1.10:8788") == "http://192.168.1.10:8788"


def test_video_detail_shows_unavailable_ocr_with_retry(monkeypatch):
    client = client_with_key(monkeypatch)
    login(client)
    job = {
        "upload_id": "44444444-4444-4444-8444-444444444444",
        "status": "failed_unavailable_ocr",
        "source_type": "authorized_author",
        "permission_note": "作者授权视频，用于系统内部识别测试",
        "sha256": "c" * 64, "size_bytes": 10,
        "error": {"code": "ocr_unavailable", "detail": "rapidocr is not installed"},
        "attempts": 1,
    }
    monkeypatch.setattr(admin_ui, "get_upload", lambda upload_id, base=None: job)
    page = client.get("/admin/videos/44444444-4444-4444-8444-444444444444")
    assert page.status_code == 200
    assert "failed_unavailable_ocr" in page.text
    assert "ocr_unavailable" in page.text
    assert "安装依赖后重试" in page.text
    assert "/admin/videos/44444444-4444-4444-8444-444444444444/retry" in page.text


def test_video_retry_forwards_and_requires_csrf(monkeypatch):
    client = client_with_key(monkeypatch)
    login(client)
    retried = []
    monkeypatch.setattr(admin_ui, "retry_upload",
                        lambda upload_id, base=None: retried.append(upload_id) or {})
    csrf = _csrf_of(client)
    response = client.post("/admin/videos/55555555-5555-4555-8555-555555555555/retry",
                           data={"csrf": csrf}, follow_redirects=False)
    assert response.status_code == 303
    assert retried == ["55555555-5555-4555-8555-555555555555"]
    denied = client.post("/admin/videos/55555555-5555-4555-8555-555555555555/retry",
                         data={"csrf": "wrong"})
    assert denied.status_code == 403


def test_static_assets_served_with_cache_and_type(monkeypatch):
    client = client_with_key(monkeypatch)
    css = client.get("/admin/static/admin.css")
    assert css.status_code == 200
    assert css.headers["content-type"].startswith("text/css")
    assert "max-age" in css.headers["cache-control"]
    js = client.get("/admin/static/videos.js")
    assert js.status_code == 200
    assert js.headers["content-type"].startswith("text/javascript")
    traversal = client.get("/admin/static/..%2Fsettings.py")
    assert traversal.status_code in (403, 404)
