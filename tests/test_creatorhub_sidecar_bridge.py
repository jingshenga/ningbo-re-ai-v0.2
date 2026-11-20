"""CreatorHub sidecar bridge offline tests: temp-file SQLite loaded from
committed .sql fixtures (no SQL statements written in this module),
httpx.MockTransport for 200/422/503/network-timeout, cursor state machine."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import httpx
import pytest

from tools.bridges import creatorhub_bridge as bridge

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
SEED_SQL = (FIXTURES / "creatorhub_seed.sql").read_text(encoding="utf-8")
POISON_SQL = (FIXTURES / "creatorhub_poison.sql").read_text(encoding="utf-8")


def build_hub_db(tmp_path: Path, with_poison: bool = False) -> Path:
    path = tmp_path / ("hub_" + ("poison" if with_poison else "seed") + ".db")
    conn = sqlite3.connect(path)
    conn.executescript(SEED_SQL)
    if with_poison:
        conn.executescript(POISON_SQL)
    conn.commit()
    conn.close()
    return path


@pytest.fixture()
def hub_db(tmp_path):
    return build_hub_db(tmp_path)


def make_transport(handler):
    return httpx.MockTransport(handler)


def stored_response(sha_prefix="b"):
    return httpx.Response(200, json={"status": "stored", "sha256": sha_prefix * 64})


def ningbo_reject_response():
    return httpx.Response(422, json={"error": {"code": "not_ningbo_related",
                                               "message": "no ningbo keywords"}})


def storage_pending_response():
    return httpx.Response(503, json={"error": {"code": "storage_pending",
                                               "message": "store missing"}})


def row_count(conn) -> int:
    """Count via the bridge's own read-only SELECT; no SQL written here."""
    return len(bridge.fetch_rows(conn, 0, 1000))


# ---------- 映射 ----------
def test_map_platform_aliases_chinese_and_english():
    assert bridge.map_platform("小红书") == "xiaohongshu"
    assert bridge.map_platform("XHS") == "xiaohongshu"
    assert bridge.map_platform("抖音") == "douyin"
    assert bridge.map_platform("视频号") == "channels"
    assert bridge.map_platform("bilibili") == "other"
    assert bridge.map_platform(None) == "other"


def test_parse_list_field_accepts_json_and_comma_forms():
    assert bridge.parse_list_field('["a","b"]') == ["a", "b"]
    assert bridge.parse_list_field("a.jpg,b.jpg") == ["a.jpg", "b.jpg"]
    assert bridge.parse_list_field("") == []
    assert bridge.parse_list_field(None) == []


def test_row_to_payload_maps_fields_and_caps():
    payload = bridge.row_to_payload({
        "platform": "小红书", "post_id": "p1", "source_url": "https://x.test/1",
        "title": "t" * 400, "content": "宁波 " + "c" * 60000,
        "author_name": "a" * 200, "publish_time": "2026-11-19",
        "media_urls": json.dumps([f"https://i/{n}" for n in range(30)]),
        "tags": "宁波, 买房",
        "raw_html_snippet": "<div>" * 30000,
    })
    assert payload["platform"] == "xiaohongshu"
    assert len(payload["title"]) == 300
    assert len(payload["content"]) == 50000
    assert len(payload["author_name"]) == 120
    assert len(payload["media_urls"]) == 20
    assert payload["tags"] == ["宁波", "买房"]
    assert len(payload["raw_html_snippet"]) == 20000


def test_row_to_payload_returns_none_for_unsalvageable_rows():
    assert bridge.row_to_payload({"content": "", "source_url": "https://x/1"}) is None
    assert bridge.row_to_payload({"content": "宁波", "source_url": "http://x/1"}) is None
    assert bridge.row_to_payload({"content": "宁波"}) is None


# ---------- 连接与状态文件 ----------
def test_connect_readonly_never_mutates_the_database_file(tmp_path):
    """mode=ro guarantee, verified at the file level: any bridge session on the
    CreatorHub database leaves its bytes untouched."""
    db = build_hub_db(tmp_path, with_poison=True)
    before = (db.stat().st_mtime_ns, db.stat().st_size)
    conn = bridge.connect_readonly(str(db))
    assert row_count(conn) == 5  # 4 seed rows + 1 poison row
    conn.close()
    after = (db.stat().st_mtime_ns, db.stat().st_size)
    assert before == after


def test_connect_readonly_requires_existing_file(tmp_path):
    with pytest.raises(bridge.BridgeConfigError):
        bridge.connect_readonly(str(tmp_path / "missing.db"))


def test_state_roundtrip_and_corrupt_fallback(tmp_path):
    state_file = tmp_path / "state.json"
    assert bridge.load_state(str(state_file)) == {"last_id": 0, "version": 1}
    bridge.save_state(str(state_file), {"last_id": 7, "version": 1})
    assert bridge.load_state(str(state_file))["last_id"] == 7
    state_file.write_text("{not json", encoding="utf-8")
    assert bridge.load_state(str(state_file))["last_id"] == 0


# ---------- 同步状态机：200 / 422 / 503 / 网络超时 ----------
def test_sync_stores_rows_and_advances_cursor(hub_db, tmp_path):
    state = tmp_path / "state.json"
    seen_urls = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_urls.append(str(request.url))
        return stored_response()

    conn = bridge.connect_readonly(str(hub_db))
    summary = bridge.sync_batch(conn, str(state), base="http://api:8000/api/v1/ingest/social",
                                key="bridge-key", batch_size=10,
                                transport=make_transport(handler))
    conn.close()

    assert summary["stored"] == 4
    assert summary["failed"] == 0
    assert summary["last_id"] == 4
    assert bridge.load_state(str(state))["last_id"] == 4
    assert all(url.startswith("http://api:8000/api/v1/ingest/social")
               for url in seen_urls)
    assert len(seen_urls) == 4


def test_sync_holds_cursor_on_storage_pending(hub_db, tmp_path):
    state = tmp_path / "state.json"
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return storage_pending_response()

    conn = bridge.connect_readonly(str(hub_db))
    summary = bridge.sync_batch(conn, str(state), base="http://api:8000/api/v1/ingest/social",
                                key="", batch_size=10,
                                transport=make_transport(handler))
    conn.close()

    assert summary["failed"] == 1
    assert summary["hold_reason"] == "storage_pending"
    assert summary["last_id"] == 0
    assert bridge.load_state(str(state))["last_id"] == 0
    assert len(calls) == 1  # batch stopped at the first failure


def test_sync_skips_not_ningbo_rows_and_advances(hub_db, tmp_path):
    state = tmp_path / "state.json"

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        if "宁波" in payload["content"] or "镇海" in payload["content"] or \
                "奉化" in payload["content"]:
            return stored_response("c")
        return ningbo_reject_response()

    conn = bridge.connect_readonly(str(hub_db))
    summary = bridge.sync_batch(conn, str(state), base="http://api:8000/api/v1/ingest/social",
                                key="", batch_size=10,
                                transport=make_transport(handler))
    conn.close()

    assert summary["stored"] == 3
    assert summary["skipped_not_ningbo"] == 1
    assert summary["last_id"] == 4
    assert bridge.load_state(str(state))["last_id"] == 4


def test_sync_holds_on_network_timeout(hub_db, tmp_path):
    state = tmp_path / "state.json"

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timed out")

    conn = bridge.connect_readonly(str(hub_db))
    summary = bridge.sync_batch(conn, str(state), base="http://api:8000/api/v1/ingest/social",
                                key="", batch_size=10,
                                transport=make_transport(handler))
    conn.close()

    assert summary["failed"] == 1
    assert summary["hold_reason"] == "network: ConnectTimeout"
    assert summary["last_id"] == 0
    assert bridge.load_state(str(state))["last_id"] == 0


def test_sync_batch_size_limits_and_resumes(hub_db, tmp_path):
    state = tmp_path / "state.json"

    def handler(request: httpx.Request) -> httpx.Response:
        return stored_response("d")

    conn = bridge.connect_readonly(str(hub_db))
    first = bridge.sync_batch(conn, str(state), base="http://api:8000/api/v1/ingest/social",
                              key="", batch_size=2,
                              transport=make_transport(handler))
    assert first["stored"] == 2 and first["last_id"] == 2
    second = bridge.sync_batch(conn, str(state), base="http://api:8000/api/v1/ingest/social",
                               key="", batch_size=2,
                               transport=make_transport(handler))
    conn.close()

    assert second["scanned"] == 2  # rows 3 and 4 only
    assert second["last_id"] == 4
    assert bridge.load_state(str(state))["last_id"] == 4


def test_sync_skips_unsalvageable_row_locally(tmp_path):
    state = tmp_path / "state.json"
    db = build_hub_db(tmp_path, with_poison=True)

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["source_url"].startswith("https://")
        return stored_response("e")

    conn = bridge.connect_readonly(str(db))
    summary = bridge.sync_batch(conn, str(state), base="http://api:8000/api/v1/ingest/social",
                                key="", batch_size=10,
                                transport=make_transport(handler))
    conn.close()

    assert summary["skipped_invalid"] == 1
    assert summary["stored"] == 4
    assert summary["last_id"] == 5


# ---------- 目标地址校验 ----------
def test_validate_ingest_base_accepts_container_and_lan_targets():
    assert bridge.validate_ingest_base("http://api:8000/api/v1/ingest/social") == \
        "http://api:8000/api/v1/ingest/social"
    assert bridge.validate_ingest_base("http://127.0.0.1:18788/") == "http://127.0.0.1:18788"


def test_validate_ingest_base_rejects_bad_targets():
    for bad in ("ftp://app:8000", "http://user:pass@app:8000",
                "http://app:8000/?x=1", "not-a-url"):
        with pytest.raises(bridge.BridgeConfigError):
            bridge.validate_ingest_base(bad)


# ---------- CLI ----------
def test_main_once_runs_single_batch(hub_db, tmp_path, monkeypatch):
    monkeypatch.setenv("CREATORHUB_DB_PATH", str(hub_db))
    monkeypatch.setenv("SYNC_STATE_PATH", str(tmp_path / "state.json"))
    monkeypatch.setenv("MAIN_APP_INGEST_URL", "http://api:8000/api/v1/ingest/social")

    def handler(request: httpx.Request) -> httpx.Response:
        return stored_response("f")

    real_client = httpx.Client

    def client_factory(*args, **kwargs):
        kwargs["transport"] = make_transport(handler)
        return real_client(*args, **kwargs)

    monkeypatch.setattr(bridge.httpx, "Client", client_factory)
    exit_code = bridge.main(["--once"])
    assert exit_code == 0
    assert bridge.load_state(str(tmp_path / "state.json"))["last_id"] == 4
