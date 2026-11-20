"""Persistence for operator-collected social clues (insert-only layer).
Single responsibility: write one social_posts row using the shared app.db
psycopg connection factory. Every value is a bound parameter; conflicts on the
unique raw_sha256 key do not update the original clue.
"""
from __future__ import annotations
from app.db import session

_INSERT_SQL = (
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
    " ON CONFLICT (raw_sha256) DO NOTHING"
    " RETURNING *"
)


def insert_social_post_row(conn, values) -> tuple[dict | None, bool]:
    """Insert one social_posts row; conflicts leave the stored row untouched."""
    row = conn.execute(_INSERT_SQL, (
        values["platform"], values["post_id"], values["source_url"],
        values["title"], values["content"], values["author_name"],
        values["publish_time"], values["media_urls"], values["tags"],
        values["raw_html_snippet"], values["raw_sha256"],
        values["is_ningbo_related"], values["matched_keywords"],
        values["extracted_hints"], values["status"],
    )).fetchone()
    return row, row is not None


def insert_social_post(record: dict) -> dict:
    """Operator-facing convenience wrapper: open one short transaction."""
    normalized = dict(record)
    from psycopg.types.json import Jsonb
    for jsonb_key in ("media_urls", "tags", "matched_keywords", "extracted_hints"):
        value = normalized.get(jsonb_key)
        if value is not None and not isinstance(value, Jsonb):
            normalized[jsonb_key] = Jsonb(value)
    with session() as conn:
        row, inserted = insert_social_post_row(conn, normalized)
    if row is None:
        with session() as conn:
            row = conn.execute(
                "SELECT * FROM social_posts WHERE raw_sha256=%s",
                (normalized["raw_sha256"],),
            ).fetchone()
    if row is None:
        return {"inserted": False}
    row = dict(row)
    row["inserted"] = inserted
    return row
