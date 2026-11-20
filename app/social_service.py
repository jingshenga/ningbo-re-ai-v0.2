"""Ningbo keyword detection, proof hashing and storage seam for social clues.

Operator-collected posts only: each row comes from a human clicking "collect"
on a page they are viewing. Content is stored as an unverified clue and is
never promoted to source_listings, price_history, or any official record.

The INSERT itself lives in app.social_store (persistence layer, owned by the
backend integration lead). This module owns detection, hashing, validation of
the clue and the duplicate-check transaction.
"""
from __future__ import annotations

import hashlib
import re

from psycopg.types.json import Jsonb

from app.db import session
from app.extractor import extract_hints
from app.schemas.social_ingest import SocialPostIngestPayload

try:  # persistence layer may land separately (backend integration lead)
    from app.social_store import insert_social_post_row
except ImportError:  # pragma: no cover - honest fallback until the store lands
    insert_social_post_row = None

# Ordered Ningbo location vocabulary: city name first, then districts, then
# new-town zones. County-level cities (余姚/慈溪/宁海/象山) match the existing
# extractor.DISTRICTS list so both modules stay consistent.
NINGBO_KEYWORDS = (
    "宁波",
    "海曙", "鄞州", "江北", "镇海", "北仑", "奉化",
    "高新区", "东部新城", "前湾新区",
    "余姚", "慈溪", "宁海", "象山",
)

_COLUMNS = (
    "platform", "post_id", "source_url", "title", "content", "author_name",
    "publish_time", "media_urls", "tags", "raw_html_snippet", "raw_sha256",
    "is_ningbo_related", "matched_keywords", "extracted_hints", "status",
)

_WHITESPACE_RUN = re.compile(r"\s+")


def normalize_text(value: str | None) -> str:
    """Collapse whitespace so copy/paste and DOM differences hash identically."""
    if not value:
        return ""
    return _WHITESPACE_RUN.sub(" ", value.replace("\r\n", "\n").replace("\r", "\n")).strip()


def normalized_source_url(value: str) -> str:
    """Strip fragments and trailing slashes; fragments never change the post."""
    base = value.split("#", 1)[0]
    return base.rstrip("/")


def compute_raw_sha256(platform: str, source_url: str, content: str) -> str:
    """Idempotency proof over the normalized platform + URL + content triple."""
    normalized = "\n".join((
        platform.strip().lower(),
        normalized_source_url(source_url),
        normalize_text(content),
    ))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def match_ningbo_keywords(*parts: str | None) -> list[str]:
    """Return every known Ningbo keyword present in the joined text, in vocabulary order."""
    text = normalize_text(" ".join(part for part in parts if part))
    return [keyword for keyword in NINGBO_KEYWORDS if keyword in text]


def _row_values(payload: SocialPostIngestPayload, sha256: str,
                matched_keywords: list[str], hints: dict) -> dict:
    return {
        "platform": payload.platform.value,
        "post_id": payload.post_id,
        "source_url": str(payload.source_url),
        "title": payload.title,
        "content": payload.content,
        "author_name": payload.author_name,
        "publish_time": payload.publish_time,
        "media_urls": Jsonb(list(payload.media_urls)),
        "tags": Jsonb(list(payload.tags)),
        "raw_html_snippet": payload.raw_html_snippet,
        "raw_sha256": sha256,
        "is_ningbo_related": bool(matched_keywords),
        "matched_keywords": Jsonb(matched_keywords),
        "extracted_hints": Jsonb(hints),
        "status": "new",
    }


def persist_social_post(payload: SocialPostIngestPayload,
                        insert_row=None) -> tuple[dict, bool]:
    """Duplicate-check then insert the clue; idempotent on raw_sha256.

    Returns (row, created). `insert_row(conn, values)` may be injected for
    tests; by default it resolves to app.social_store.insert_social_post_row.
    """
    if insert_row is None:
        if insert_social_post_row is None:
            raise RuntimeError(
                "social_posts persistence is pending: app/social_store.py "
                "(backend integration lead) has not been deployed yet")
        insert_row = insert_social_post_row
    sha256 = compute_raw_sha256(payload.platform.value, str(payload.source_url),
                                payload.content)
    matched = match_ningbo_keywords(payload.title, payload.content, *(payload.tags or []))
    hints = extract_hints(payload.content, payload.title,
                          source_labels=["content", "title"],
                          known_community_names=[k for k in matched if k not in ("宁波",)])
    values = _row_values(payload, sha256, matched, hints)
    with session() as conn:
        existing = conn.execute(
            'SELECT * FROM social_posts WHERE raw_sha256=%s', (sha256,)).fetchone()
        if existing:
            return existing, False
        row = insert_row(conn, values)
        if row is None:
            # Concurrent duplicate won the race; return the stored row honestly.
            existing = conn.execute(
                'SELECT * FROM social_posts WHERE raw_sha256=%s', (sha256,)).fetchone()
            return existing, False
        return row, True


def row_to_response_fields(row: dict, created: bool) -> dict:
    """Map a stored row onto the SocialIngestResponse field set."""
    hints = row.get("extracted_hints") or {}
    return {
        "status": "stored" if created else "duplicate",
        "id": str(row.get("id")),
        "sha256": row.get("raw_sha256"),
        "is_ningbo_related": bool(row.get("is_ningbo_related")),
        "matched_keywords": list(row.get("matched_keywords") or []),
        "hints": hints if isinstance(hints, dict) else {},
    }
