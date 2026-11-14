"""Server-side client for the video upload/processing backend (Issue #30 contract).

Used ONLY by app.admin_ui routes: the APP_API_KEY stays in the server process
and never reaches the browser. Targets are restricted to the operator's own
loopback/private network (protocol, credential and resolved-IP checks), and
all backend traffic goes through one httpx entry point so the key never
appears in logs or browser payloads.
"""
from __future__ import annotations

import ipaddress
import os
from urllib.parse import urlsplit

import httpx

from app.settings import APP_API_KEY

DEFAULT_TIMEOUT_SECONDS = 6.0
_SOURCE_TYPES = ("operator_local", "authorized_author", "licensed_platform")


class MediaBackendUnavailable(RuntimeError):
    """Backend missing, unreachable, or answering outside the contract."""


class MediaBackendError(RuntimeError):
    """Backend answered with a structured error the UI can show directly."""

    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail


def _validate_base(base: str) -> str:
    """Restrict backend targets to the operator's own loopback/private network.

    The upload backend runs next to the admin UI (same process or same
    private LAN/compose network); a public address can only be a
    misconfiguration, so it is rejected along with URL credentials.
    Only IP literals are accepted, preventing DNS rebinding and public targets.
    """
    parts = urlsplit(base)
    if parts.scheme not in ("http", "https"):
        raise MediaBackendUnavailable("backend base must use http or https")
    if parts.username is not None or parts.password is not None:
        raise MediaBackendUnavailable("backend base must not contain credentials")
    host = parts.hostname
    if not host:
        raise MediaBackendUnavailable("backend base has no host")
    # Restrict to IP literals: resolved hostnames can change between
    # validation and httpx connection (DNS rebinding).
    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise MediaBackendUnavailable("backend base must use an IP literal") from exc
    if not (address.is_loopback or address.is_private):
        raise MediaBackendUnavailable(
            "backend base must be a loopback or private-network address")
    if parts.path not in ("", "/") or parts.query or parts.fragment:
        raise MediaBackendUnavailable("backend base must contain only a trusted origin")
    return base.rstrip("/")


def backend_base(request_base: str | None = None) -> str:
    """Resolve the upload backend base URL.

    MEDIA_UPLOAD_API_BASE wins when configured. By default the backend lives
    in the same FastAPI process as the admin UI (Issue #30 mounts
    app.media_upload_api into app.main); default to its internal loopback port,
    never to the untrusted browser Host header.
    """
    configured = os.environ.get("MEDIA_UPLOAD_API_BASE", "").strip()
    if configured:
        return _validate_base(configured)
    # This UI and upload API run in the same Uvicorn process. The NAS-facing
    # Host header may be inaccessible from inside its own Docker container.
    # Never derive the credential-bearing backend target from client headers.
    if request_base:
        return _validate_base(request_base)
    return "http://127.0.0.1:8000"


def _key() -> str:
    if not APP_API_KEY:
        raise MediaBackendUnavailable("APP_API_KEY is not configured")
    return APP_API_KEY


def _exchange(method: str, url: str, *, json_body: dict | None = None,
              files=None, data=None, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> httpx.Response:
    """Single httpx entry point; every backend call validates its target first."""
    try:
        return httpx.request(
            method, url, json=json_body, files=files, data=data,
            headers={"X-API-Key": _key()}, timeout=timeout,
            follow_redirects=False, trust_env=False)
    except httpx.HTTPError as exc:
        raise MediaBackendUnavailable("backend unreachable: " + type(exc).__name__) from exc


def _request(method: str, path: str, *, base: str | None = None,
             json_body: dict | None = None, files=None, data=None,
             timeout: float = DEFAULT_TIMEOUT_SECONDS) -> dict:
    url = _validate_base(backend_base(base)) + path
    response = _exchange(method, url, json_body=json_body, files=files,
                         data=data, timeout=timeout)
    if response.status_code == 401:
        raise MediaBackendUnavailable("backend rejected the admin credential")
    if response.status_code >= 400:
        try:
            payload = response.json()
        except ValueError:
            payload = None
        error = payload.get("error") if isinstance(payload, dict) else None
        if not isinstance(error, dict) or not error.get("code"):
            if response.status_code == 404:
                raise MediaBackendUnavailable(
                    "backend endpoint not found (is the Issue #30 service deployed?)")
            raise MediaBackendError("backend_error", "HTTP " + str(response.status_code))
        raise MediaBackendError(str(error["code"]),
                                str(error.get("detail") or response.status_code))
    try:
        return response.json()
    except ValueError as exc:
        raise MediaBackendUnavailable("backend returned non-JSON payload") from exc


def list_uploads(limit: int = 50, base: str | None = None) -> list[dict]:
    payload = _request("GET", f"/api/media/uploads?limit={int(limit)}", base=base)
    items = payload.get("items") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        raise MediaBackendUnavailable("unexpected list payload shape")
    return items


def get_upload(upload_id: str, base: str | None = None) -> dict:
    payload = _request("GET", "/api/media/uploads/" + upload_id, base=base)
    if not isinstance(payload, dict):
        raise MediaBackendUnavailable("unexpected detail payload shape")
    return payload


def create_upload(file_field: tuple, fields: dict, base: str | None = None) -> dict:
    """Forward one multipart upload. `file_field` is (filename, fileobj, content_type)."""
    if fields.get("source_type") not in _SOURCE_TYPES:
        raise MediaBackendError("invalid_source_type", "来源类型不被后端接受")
    return _request("POST", "/api/media/uploads", base=base, files={"file": file_field},
                    data=fields, timeout=90.0)


def retry_upload(upload_id: str, base: str | None = None) -> dict:
    return _request("POST", "/api/media/uploads/" + upload_id + "/retry",
                    base=base, json_body={})


def fetch_frame(upload_id: str, frame_index: int,
                base: str | None = None) -> tuple[bytes, str]:
    """Fetch one keyframe image from the backend frames endpoint.

    Returns (payload, media_type); the admin route proxies it to the browser
    so the X-API-Key stays server-side.
    """
    url = _validate_base(backend_base(base)) + \
        f"/api/media/uploads/{upload_id}/frames/{int(frame_index)}"
    response = _exchange("GET", url)
    if response.status_code >= 400:
        try:
            error = response.json().get("error") or {}
            raise MediaBackendError(error.get("code", "frame_error"),
                                    str(error.get("detail") or response.status_code))
        except ValueError:
            raise MediaBackendError("frame_error", "HTTP " + str(response.status_code)) from None
    media_type = response.headers.get("content-type", "image/jpeg").split(";")[0]
    if not media_type.startswith("image/"):
        raise MediaBackendError("frame_error", "backend returned a non-image payload")
    return response.content, media_type


def is_available(base: str | None = None) -> bool:
    try:
        list_uploads(limit=1, base=base)
        return True
    except (MediaBackendUnavailable, MediaBackendError):
        return False
