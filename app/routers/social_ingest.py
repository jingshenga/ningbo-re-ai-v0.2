"""HTTP entry point for operator-collected social clues (browser userscript).

Single-operator tool: accepts one post per call from the operator's own
browser capture. Auth is deliberately stricter than the spec's minimum:
- when APP_API_KEY is configured, a matching X-API-Key header is required;
- only when no key is configured do loopback clients pass (local dev mode).

Ningbo relevance is the server's decision: posts without a recognized Ningbo
keyword are rejected with 422 not_ningbo_related so the userscript can show
an honest "nothing Ningbo-related on this page" state instead of guessing.
"""
from __future__ import annotations

import ipaddress
import secrets

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.schemas.social_ingest import SocialIngestResponse, SocialPostIngestPayload
from app.settings import APP_API_KEY
from app import social_service

router = APIRouter(prefix="/api/v1/ingest", tags=["social-ingest"])


def _authorize(request: Request) -> None:
    if APP_API_KEY:
        supplied = request.headers.get("X-API-Key", "")
        if not supplied or not secrets.compare_digest(supplied, APP_API_KEY):
            raise HTTPException(status_code=401, detail="Invalid X-API-Key")
        return
    client_host = request.client.host if request.client else ""
    try:
        address = ipaddress.ip_address(client_host)
    except ValueError:
        address = None
    if address is None or not address.is_loopback:
        raise HTTPException(
            status_code=403,
            detail="Set APP_API_KEY or call this endpoint from the NAS itself (loopback)")


@router.post("/social", response_model=SocialIngestResponse)
def ingest_social_post(payload: SocialPostIngestPayload, request: Request):
    _authorize(request)
    matched = social_service.match_ningbo_keywords(
        payload.title, payload.content, *(payload.tags or []))
    if not matched:
        return JSONResponse(status_code=422, content={
            "error": {
                "code": "not_ningbo_related",
                "message": "页面内容未识别到宁波地域关键词；本工具只采集宁波相关线索",
            },
        })
    try:
        row, created = social_service.persist_social_post(payload)
    except RuntimeError as exc:
        # Honest degraded state: persistence layer not deployed yet.
        return JSONResponse(status_code=503, content={
            "error": {"code": "storage_pending", "message": str(exc)},
        })
    fields = social_service.row_to_response_fields(row, created)
    return SocialIngestResponse(**fields)
