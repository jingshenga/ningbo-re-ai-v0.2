"""Bounded API client for the existing PATCH /api/videos/{id}/enrichment endpoint.

The CLI talks to the operator's own NAS-local API. URL handling is defensive:
http/https only, no userinfo, and loopback is the only implicitly allowed
non-public target — LAN/private or hostname targets require the operator's
explicit `--allow-private-network` opt-in. The API key is a call parameter
(always sourced from the environment by the caller) and never appears in
logs, exceptions or returned data.
"""
from __future__ import annotations

import ipaddress
from urllib.parse import urlsplit

import httpx

from app.media_pipeline.errors import MediaPipelineError


def _classify_host(host: str) -> str:
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return 'hostname'
    if address.is_loopback:
        return 'loopback'
    if (address.is_private or address.is_link_local or address.is_reserved
            or address.is_multicast or address.is_unspecified):
        return 'private'
    return 'public'


def submit_enrichment(*, api_base: str, api_key: str, video_id: str,
                      transcript: str | None, ocr_text: str | None,
                      raw_location: str | None = None,
                      allow_private_network: bool = False,
                      timeout: float = 60.0) -> dict:
    """PATCH the enrichment endpoint and return the server's JSON response."""
    try:
        parts = urlsplit(api_base)
    except ValueError as exc:
        raise MediaPipelineError('invalid_api_url', 'API base URL is malformed') from exc
    if parts.scheme not in ('http', 'https'):
        raise MediaPipelineError('invalid_api_url', 'API base URL must use http or https')
    if parts.username is not None or parts.password is not None:
        raise MediaPipelineError('invalid_api_url', 'API base URL must not contain credentials')
    host = parts.hostname
    if not host:
        raise MediaPipelineError('invalid_api_url', 'API base URL has no host')
    host_kind = _classify_host(host)
    if host_kind in ('private', 'hostname') and not allow_private_network:
        raise MediaPipelineError(
            'invalid_api_url',
            'API target is a private/LAN or unresolvable-host address; '
            'pass --allow-private-network to accept this operator-controlled target',
        )
    if parts.port is not None and not (0 < parts.port < 65536):
        raise MediaPipelineError('invalid_api_url', 'API base URL has an invalid port')
    base = api_base.rstrip('/')
    url = base + '/api/videos/' + video_id + '/enrichment'
    payload = {'transcript': transcript, 'ocr_text': ocr_text, 'raw_location': raw_location}
    payload = {key: value for key, value in payload.items() if value is not None}
    try:
        response = httpx.patch(url, json=payload, headers={'X-API-Key': api_key},
                               timeout=timeout)
    except httpx.HTTPError as exc:
        raise MediaPipelineError(
            'submit_failed',
            'enrichment request failed: ' + type(exc).__name__,
        ) from exc
    if response.status_code >= 400:
        raise MediaPipelineError(
            'submit_failed',
            'enrichment endpoint returned HTTP ' + str(response.status_code),
        )
    try:
        return response.json()
    except ValueError as exc:
        raise MediaPipelineError(
            'submit_failed',
            'enrichment endpoint returned non-JSON response',
        ) from exc
