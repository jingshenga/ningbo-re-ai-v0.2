"""Authenticated HTTP API for uploading and reviewing video-processing jobs."""
from __future__ import annotations

import json
import ipaddress
import os
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Path, Query, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from app.video_upload_service import UploadManager, UploadServiceError, get_upload_manager

router = APIRouter(prefix='/api/media/uploads', tags=['media-uploads'])


class UploadBodyLimitMiddleware:
    """Bound multipart bodies before Starlette spools them to disk."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if (scope['type'] != 'http' or scope['method'] != 'POST' or
                scope['path'] != '/api/media/uploads'):
            await self.app(scope, receive, send)
            return

        maximum = int(os.getenv('NBRE_MEDIA_UPLOAD_MAX_BYTES', str(1024**3)))
        request_limit = maximum + 128 * 1024
        headers = {key.lower(): value for key, value in scope['headers']}
        content_length = headers.get(b'content-length')
        if content_length:
            try:
                if int(content_length) > request_limit:
                    await self._reject(send)
                    return
            except ValueError:
                await self._reject(send, 400, 'invalid_content_length')
                return

        received = 0

        async def limited_receive():
            nonlocal received
            message = await receive()
            if message['type'] == 'http.request':
                received += len(message.get('body', b''))
                if received > request_limit:
                    raise _UploadRequestTooLarge
            return message

        response_started = False

        async def tracked_send(message):
            nonlocal response_started
            if message['type'] == 'http.response.start':
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracked_send)
        except _UploadRequestTooLarge:
            if not response_started:
                await self._reject(send)

    @staticmethod
    async def _reject(send, status=413, code='too_large'):
        body = json.dumps({'error': {'code': code,
                                     'detail': 'uploaded request exceeds the configured limit'}}).encode()
        await send({'type': 'http.response.start', 'status': status,
                    'headers': [(b'content-type', b'application/json'),
                                (b'content-length', str(len(body)).encode())]})
        await send({'type': 'http.response.body', 'body': body})


class _UploadRequestTooLarge(Exception):
    pass


class AdminSourceAllowlistMiddleware:
    """Optional socket-peer allowlist for a private-LAN UAT listener."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        enabled = os.getenv('NBRE_ADMIN_ALLOWLIST_ENABLED', '').lower() in {'1', 'true', 'yes'}
        if scope['type'] != 'http' or not enabled:
            await self.app(scope, receive, send)
            return

        client = scope.get('client')
        try:
            address = ipaddress.ip_address(client[0]) if client else None
            networks = [ipaddress.ip_network(value.strip(), strict=False)
                        for value in os.getenv('NBRE_ADMIN_ALLOWED_CLIENTS', '').split(',')
                        if value.strip()]
            allowed = bool(address and (address.is_loopback or
                                        any(address in network for network in networks)))
        except ValueError:
            allowed = False
        if not allowed:
            body = b'{"detail":"client source is not allowed"}'
            await send({'type': 'http.response.start', 'status': 403,
                        'headers': [(b'content-type', b'application/json'),
                                    (b'content-length', str(len(body)).encode())]})
            await send({'type': 'http.response.body', 'body': body})
            return
        await self.app(scope, receive, send)


def _error(exc: UploadServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={'error': {'code': exc.code, 'detail': exc.detail, **exc.extra}},
    )


@router.post('', status_code=202)
def upload_video(
        request: Request,
        file: UploadFile | None = File(default=None),
        source_type: str | None = Form(default=None),
        permission_note: str | None = Form(default=None),
        title: str | None = Form(default=None),
        description: str | None = Form(default=None),
        manager: UploadManager = Depends(get_upload_manager)):
    if file is None:
        return _error(UploadServiceError(400, 'file_required', 'file is required'))
    content_length = request.headers.get('content-length')
    if content_length:
        try:
            request_bytes = int(content_length)
        except ValueError:
            return _error(UploadServiceError(400, 'invalid_content_length', 'content length is invalid'))
        if request_bytes > manager.max_file_bytes + 128 * 1024:
            return _error(UploadServiceError(413, 'too_large', 'uploaded request exceeds the configured limit'))
    try:
        job = manager.upload(file.file, file.filename, source_type, permission_note,
                             title=title, description=description)
        job['poll_url'] = '/api/media/uploads/' + job['upload_id']
        return JSONResponse(status_code=202, content=job)
    except UploadServiceError as exc:
        return _error(exc)
    finally:
        file.file.close()


@router.get('')
def list_uploads(
        limit: int = Query(default=50, ge=1, le=100),
        manager: UploadManager = Depends(get_upload_manager)):
    try:
        items = manager.list_jobs(limit)
        return {'items': items, 'count': len(items)}
    except UploadServiceError as exc:
        return _error(exc)


@router.get('/{upload_id}/frames/{frame_index}')
def get_upload_frame(
        upload_id: UUID,
        frame_index: int = Path(ge=0),
        manager: UploadManager = Depends(get_upload_manager)):
    try:
        path = manager.frame_path(str(upload_id), frame_index)
        return FileResponse(path, media_type='image/jpeg')
    except UploadServiceError as exc:
        return _error(exc)


@router.post('/{upload_id}/retry', status_code=202)
def retry_upload(
        upload_id: UUID,
        manager: UploadManager = Depends(get_upload_manager)):
    try:
        return JSONResponse(status_code=202, content=manager.retry(str(upload_id)))
    except UploadServiceError as exc:
        return _error(exc)


@router.get('/{upload_id}')
def get_upload(
        upload_id: UUID,
        manager: UploadManager = Depends(get_upload_manager)):
    try:
        return manager.get_job(str(upload_id))
    except UploadServiceError as exc:
        return _error(exc)
