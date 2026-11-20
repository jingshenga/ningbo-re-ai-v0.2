"""CreatorHub sidecar bridge: read-only SQLite → main-app HTTP ingest.

Pulls new posts from CreatorHub's SQLite database in read-only mode (URI
`mode=ro`, never takes a write lock) and pushes each one to the main app's
`POST /api/v1/ingest/social`. No PostgreSQL access and no SQL writes here:
this process only SELECTs from SQLite and speaks HTTP.

Cursor discipline (state file, atomic tmp+rename writes):
- 200/201 stored            -> cursor advances
- 422 not_ningbo_related    -> cursor advances (permanent, safe skip)
- 503 storage_pending / 5xx / network errors / timeouts -> cursor HOLDS,
  the batch stops, and the same row is retried on the next run
- rows that can never be valid (missing content, non-https source_url) are
  skipped locally with a warning and DO advance the cursor, since retrying
  them can never succeed; each skip is counted in the summary.

All configuration comes from environment variables (see --help and
docs/deployment/creatorhub_sidecar.md).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit

import httpx

DEFAULT_INGEST_URL = "http://api:8000/api/v1/ingest/social"
DEFAULT_DB_PATH = "/data/creatorhub/creatorhub.db"
DEFAULT_STATE_PATH = "/data/bridge_state.json"
DEFAULT_POLL_SECONDS = 60
DEFAULT_BATCH_SIZE = 25
REQUEST_TIMEOUT_SECONDS = 20.0
MAX_LIST_FIELDS = 20

PLATFORM_ALIASES = {
    "xiaohongshu": "xiaohongshu", "xhs": "xiaohongshu", "小红书": "xiaohongshu",
    "douyin": "douyin", "抖音": "douyin",
    "channels": "channels", "视频号": "channels", "wechat": "channels",
    "微信": "channels", "公众号": "channels", "gzh": "channels",
}


class BridgeConfigError(RuntimeError):
    """Operator-facing configuration problem; the bridge refuses to start."""


# ---------- 配置（调用时读取环境变量，便于测试注入） ----------
def env_value(name: str, default: str) -> str:
    value = os.environ.get(name, "").strip()
    return value or default


def ingest_base() -> str:
    return validate_ingest_base(env_value("MAIN_APP_INGEST_URL", DEFAULT_INGEST_URL))


def api_key() -> str:
    return os.environ.get("MAIN_APP_API_KEY", "").strip()


def db_path() -> str:
    return env_value("CREATORHUB_DB_PATH", DEFAULT_DB_PATH)


def state_path() -> str:
    return env_value("SYNC_STATE_PATH", DEFAULT_STATE_PATH)


def poll_seconds() -> int:
    raw = os.environ.get("POLL_INTERVAL_SECONDS", "").strip()
    try:
        value = int(raw) if raw else DEFAULT_POLL_SECONDS
    except ValueError:
        value = DEFAULT_POLL_SECONDS
    return max(1, value)


def batch_size() -> int:
    raw = os.environ.get("SYNC_BATCH_SIZE", "").strip()
    try:
        value = int(raw) if raw else DEFAULT_BATCH_SIZE
    except ValueError:
        value = DEFAULT_BATCH_SIZE
    return max(1, min(value, 200))


# ---------- 目标地址校验：仅 http/https、无凭据、无 query/fragment ----------
def validate_ingest_base(url: str) -> str:
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise BridgeConfigError("MAIN_APP_INGEST_URL must use http or https")
    if not parts.hostname:
        raise BridgeConfigError("MAIN_APP_INGEST_URL has no host")
    if parts.username is not None or parts.password is not None:
        raise BridgeConfigError("MAIN_APP_INGEST_URL must not contain credentials")
    if parts.query or parts.fragment:
        raise BridgeConfigError("MAIN_APP_INGEST_URL must not contain query or fragment")
    return url.rstrip("/")


# ---------- SQLite 只读访问 ----------
def connect_readonly(path: str) -> sqlite3.Connection:
    """Open CreatorHub's SQLite in read-only URI mode (never takes a write lock)."""
    resolved = Path(path)
    if not resolved.is_file():
        raise BridgeConfigError(f"CreatorHub database not found: {path}")
    uri = "file:" + str(resolved).replace("?", "%3f").replace("#", "%23") + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_rows(conn: sqlite3.Connection, last_id: int, limit: int) -> list[dict]:
    tables = {row[0] for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'")}
    if "posts" in tables:
        rows = conn.execute(
            "SELECT id, platform, post_id, source_url, title, content, "
            "author_name, publish_time, media_urls, tags, raw_html_snippet "
            "FROM posts WHERE id > ? ORDER BY id LIMIT ?",
            (last_id, limit),
        ).fetchall()
    elif {"contentrecord", "monitortarget"} <= tables:
        rows = conn.execute(
            'SELECT c.id, c.platform, c.aweme_id AS post_id, '
            'c."desc" AS title, c."desc" AS content, '
            'm.nickname AS author_name, '
            "CASE WHEN c.create_time > 0 "
            "THEN datetime(c.create_time, 'unixepoch') END AS publish_time, "
            "'[]' AS media_urls, m.tags AS tags, "
            "NULL AS raw_html_snippet, NULL AS source_url "
            "FROM contentrecord AS c LEFT JOIN monitortarget AS m "
            "ON m.id = c.target_id WHERE c.id > ? ORDER BY c.id LIMIT ?",
            (last_id, limit),
        ).fetchall()
    else:
        raise BridgeConfigError(
            "CreatorHub database has neither the supported posts table nor "
            "the ContentRecord/MonitorTarget schema")
    return [dict(row) for row in rows]


# ---------- 字段映射到 SocialPostIngestPayload ----------
def map_platform(raw: str | None) -> str:
    text = (raw or "").strip().lower()
    return PLATFORM_ALIASES.get(text, "other")


def parse_list_field(raw) -> list[str]:
    """CreatorHub may store JSON arrays or comma-separated strings; accept both."""
    if raw is None:
        return []
    if isinstance(raw, list):
        items = raw
    else:
        text = str(raw).strip()
        if not text:
            return []
        try:
            loaded = json.loads(text)
        except ValueError:
            items = text.split(",")
        else:
            items = loaded if isinstance(loaded, list) else [loaded]
    cleaned = []
    for item in items[:MAX_LIST_FIELDS]:
        text = str(item).strip()
        if text:
            cleaned.append(text[:2000])
    return cleaned


def canonical_source_url(platform: str | None, post_id: str | None) -> str:
    """Build a canonical public URL only for platforms with stable URL forms."""
    post_id = str(post_id or "").strip()
    platform = (platform or "").strip().lower()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,220}", post_id):
        return ""
    if platform in {"douyin", "抖音"}:
        return f"https://www.douyin.com/video/{post_id}"
    if platform in {"xhs", "xiaohongshu", "小红书"}:
        return f"https://www.xiaohongshu.com/explore/{post_id}"
    return ""


def row_to_payload(row: dict) -> dict | None:
    """Map one CreatorHub row to the ingest payload; None when unsalvageable.

    Unsalvageable rows (no content, or a non-https source_url that the main
    endpoint can never accept) are skipped locally and the cursor advances;
    retrying them could never succeed.
    """
    content = str(row.get("content") or "").strip()
    source_url = str(row.get("source_url") or "").strip()
    if not source_url:
        source_url = canonical_source_url(row.get("platform"), row.get("post_id"))
    if not content or not source_url.lower().startswith("https://"):
        return None
    title = str(row.get("title") or content).strip()
    return {
        "platform": map_platform(row.get("platform")),
        "source_url": source_url,
        "post_id": (str(row["post_id"]).strip() if row.get("post_id") else None),
        "title": title[:300] if title else None,
        "content": content[:50000],
        "author_name": (str(row["author_name"]).strip()[:120]
                        if row.get("author_name") else None),
        "publish_time": (str(row["publish_time"]).strip()[:64]
                         if row.get("publish_time") else None),
        "media_urls": parse_list_field(row.get("media_urls")),
        "tags": parse_list_field(row.get("tags")),
        "raw_html_snippet": (str(row["raw_html_snippet"])[:20000]
                             if row.get("raw_html_snippet") else None),
    }


# ---------- 游标状态文件（原子 tmp+rename） ----------
def load_state(path: str) -> dict:
    state_file = Path(path)
    if not state_file.is_file():
        return {"last_id": 0, "version": 1}
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"last_id": 0, "version": 1}
    if not isinstance(state, dict) or not isinstance(state.get("last_id"), int):
        return {"last_id": 0, "version": 1}
    state.setdefault("version", 1)
    return state


def save_state(path: str, state: dict) -> None:
    state_file = Path(path)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    tmp = state_file.with_suffix(state_file.suffix + ".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(state_file)


# ---------- 同步一批（游标状态机） ----------
def sync_batch(conn: sqlite3.Connection, state_path: str, *, base: str,
               key: str, batch_size: int,
               transport: httpx.Transport | None = None) -> dict:
    """Process up to batch_size rows; stops and HOLDS the cursor on any failure
    that might succeed later (5xx, storage_pending, network, timeout)."""
    state = load_state(state_path)
    last_id = state["last_id"]
    rows = fetch_rows(conn, last_id, batch_size)
    summary = {
        "scanned": len(rows), "stored": 0, "skipped_not_ningbo": 0,
        "skipped_invalid": 0, "failed": 0, "last_id": last_id,
        "hold_reason": None,
    }
    if not rows:
        return summary

    headers = {"X-API-Key": key} if key else {}
    with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS, transport=transport) as client:
        for row in rows:
            row_id = row.get("id")
            payload = row_to_payload(row)
            if payload is None:
                summary["skipped_invalid"] += 1
                last_id = row_id
                state["last_id"] = last_id
                save_state(state_path, state)
                print(f"[bridge] row {row_id} skipped locally: "
                      "missing content or non-https source_url", file=sys.stderr)
                continue
            try:
                response = client.post(base, json=payload, headers=headers)
            except httpx.HTTPError as exc:
                summary["failed"] += 1
                summary["hold_reason"] = f"network: {type(exc).__name__}"
                print(f"[bridge] row {row_id} network failure, cursor held: "
                      f"{type(exc).__name__}", file=sys.stderr)
                break
            if response.status_code in (200, 201):
                summary["stored"] += 1
                last_id = row_id
                state["last_id"] = last_id
                save_state(state_path, state)
                continue
            error = {}
            try:
                error = response.json().get("error") or {}
            except ValueError:
                pass
            if (response.status_code == 422
                    and error.get("code") == "not_ningbo_related"):
                summary["skipped_not_ningbo"] += 1
                last_id = row_id
                state["last_id"] = last_id
                save_state(state_path, state)
                continue
            if response.status_code == 503 and error.get("code") == "storage_pending":
                summary["failed"] += 1
                summary["hold_reason"] = "storage_pending"
                print(f"[bridge] row {row_id} held: main app storage not ready",
                      file=sys.stderr)
                break
            # Any other 4xx/5xx: hold the cursor so nothing is silently lost.
            summary["failed"] += 1
            summary["hold_reason"] = (f"HTTP {response.status_code} "
                                      f"{error.get('code') or ''}".strip())
            print(f"[bridge] row {row_id} unexpected response "
                  f"HTTP {response.status_code}, cursor held", file=sys.stderr)
            break
    summary["last_id"] = last_id
    return summary


# ---------- CLI ----------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="CreatorHub sidecar bridge: read-only SQLite to main-app ingest")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true", help="run one batch and exit")
    mode.add_argument("--loop", action="store_true",
                      help="poll continuously (default)")
    parser.add_argument("--batch-size", type=int, default=None,
                        help="override SYNC_BATCH_SIZE")
    args = parser.parse_args(argv)

    try:
        base = ingest_base()
    except BridgeConfigError as exc:
        print(f"[bridge] config error: {exc}", file=sys.stderr)
        return 2
    key = api_key()
    state_file = state_path()
    size = args.batch_size or batch_size()

    while True:
        conn = None
        try:
            conn = connect_readonly(db_path())
        except (BridgeConfigError, sqlite3.Error) as exc:
            print(f"[bridge] database unavailable: {exc}", file=sys.stderr)
        try:
            if conn is not None:
                summary = sync_batch(conn, state_file, base=base, key=key,
                                     batch_size=size)
                print("[bridge] " + json.dumps(summary, ensure_ascii=False), flush=True)
        finally:
            if conn is not None:
                conn.close()
        if args.once:
            return 0
        time.sleep(poll_seconds())


if __name__ == "__main__":
    sys.exit(main())
