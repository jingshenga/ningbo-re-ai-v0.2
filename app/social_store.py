"""Persistence for operator-collected social clues (INSERT/upsert layer).
Single responsibility: write one social_posts row using the shared app.db
psycopg connection factory. Every value is a bound parameter; the proof hash
(raw_sha256) carries a unique index and the upsert keeps concurrent pushes of
the same post from double-inserting.
"""
from __future__ import annotations
from app.db import session

_UPSERT_SQL = (
    "INSERT INTO social_posts"
    " (platform, post_id, source_url, title, content, author_name,"
    " publish_time, media_urls, tags, raw_html_snippet, raw_sha256,"
    " is_ningbo_related, matched_keywords, extracted_hints, status)"
    " VALUES"
    " (%s, %s,"
    "  %s, %s, %s,"
    "  %s, %s,"
    "  %s, %s, %s,"
    "  %s, %s,"
    "  %s, %s, %s)"
    " ON CONFLICT (raw_sha256) DO UPDATE SET"
    " post_id = EXCLUDED.post_id,"
    " title = EXCLUDED.title,"
    " author_name = EXCLUDED.author_name,"
    " publish_time = EXCLUDED.publish_time,"
    " media_urls = EXCLUDED.media_urls,"
    " tags = EXCLUDED.tags,"
    " raw_html_snippet = EXCLUDED.raw_html_snippet"
    " RETURNING *, (xmax = 0) AS inserted"
)


def insert_social_post_row(conn, values) -> tuple[dict, bool]:
    """Upsert one social_posts row inside the caller's transaction."""
    row = conn.execute(_UPSERT_SQL, (
        values["platform"], values["post_id"], values["source_url"],
        values["title"], values["content"], values["author_name"],
        values["publish_time"], values["media_urls"], values["tags"],
        values["raw_html_snippet"], values["raw_sha256"],
        values["is_ningbo_related"], values["matched_keywords"],
        values["extracted_hints"], values["status"],
    )).fetchone()
    if row is None:
        return {}, False
    return row, bool(row.get("inserted"))


def insert_social_post(record: dict) -> dict:
    """Operator-facing convenience wrapper: open one short transaction."""
    normalized = dict(record)
    from psycopg.types.json import Jsonb
    for jsonb_key in ("media_urls", "tags", "matched_keywords", "extracted_hints"):
        value = normalized.get(jsonb_key)
        if value is not None and not hasattr(value, "adapted"):
            normalized[jsonb_key] = Jsonb(value)
    with session() as conn:
        row, inserted = insert_social_post_row(conn, normalized)
    row = dict(row)
    row["inserted"] = inserted
    return row
