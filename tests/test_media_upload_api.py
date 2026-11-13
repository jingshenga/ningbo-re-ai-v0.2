"""Filesystem-backed upload API checks; the pipeline is mocked in fast CI."""
from __future__ import annotations

import io
import time
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main
from app.media_pipeline.errors import MediaPipelineError
from app.media_pipeline.models import (MediaEvidence, MediaInfo, OcrItem,
                                       OcrResult, TranscriptResult)
from app.video_upload_service import UploadManager, get_upload_manager

API_KEY = 'synthetic-upload-api-key'
VALID_MP4 = b'\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isom'


def fake_pipeline(path, *, asr_engine, ocr_engine, work_dir, keep_work,
                  known_community_names=None):
    work_dir.mkdir(mode=0o700)
    frame = work_dir / 'frame_0000.jpg'
    frame.write_bytes(b'jpeg-evidence')
    return MediaEvidence(
        media=MediaInfo(sha256='f' * 64, size_bytes=24, duration_seconds=1.0,
                        format_name='mov,mp4,m4a,3gp,3g2,mj2', has_audio=False,
                        width=640, height=360),
        transcript=TranscriptResult(status='no_audio', error='media has no audio stream'),
        ocr=OcrResult(status='ok', engine='rapidocr', model_name='test-model',
                       items=(OcrItem(text='东湖花园 160平方米 365万', frame_index=0,
                                      frame_path=str(frame), timestamp_seconds=0.0,
                                      confidence=0.98),)),
        hints={'price_mentions_wan': [365.0], 'confidence_status': 'not_calibrated',
               'warning': '视频价格仅为线索，不得自动当作正式挂牌价。',
               'evidence': [{'field': 'price_mentions_wan', 'quote': '365万'}]},
        warnings=(), work_dir=str(work_dir), elapsed_seconds=0.2,
    )


@contextmanager
def upload_client(tmp_path, monkeypatch, runner=fake_pipeline, *, maximum=1024,
                  quota=4096):
    manager = UploadManager(tmp_path / 'uploads', max_file_bytes=maximum,
                            quota_bytes=quota, pipeline_runner=runner)
    monkeypatch.setattr(main, 'APP_API_KEY', API_KEY)
    monkeypatch.setattr(main, 'start_upload_worker', manager.start)
    monkeypatch.setattr(main, 'stop_upload_worker', manager.stop)
    main.app.dependency_overrides[get_upload_manager] = lambda: manager
    try:
        with TestClient(main.app) as client:
            yield client, manager
    finally:
        main.app.dependency_overrides.pop(get_upload_manager, None)
        manager.stop()


def submit(client, data=VALID_MP4, name='synthetic.mp4', **fields):
    form = {'source_type': 'operator_local',
            'permission_note': '由项目负责人制作的合成测试视频'}
    form.update(fields)
    return client.post('/api/media/uploads', headers={'X-API-Key': API_KEY},
                       data=form, files={'file': (name, io.BytesIO(data), 'video/mp4')})


def wait_for_status(manager, upload_id, expected, timeout=5):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        job = manager.get_job(upload_id)
        if job['status'] in expected:
            return job
        time.sleep(0.02)
    raise AssertionError('upload did not reach a terminal status')


def test_upload_runs_queue_and_keeps_ocr_frame_evidence_without_database(monkeypatch, tmp_path):
    monkeypatch.setattr(main, 'session', lambda: pytest.fail('upload API must not use PostgreSQL'))
    with upload_client(tmp_path, monkeypatch) as (client, manager):
        response = submit(client, name='../client-name.mp4', title='合成测试')
        assert response.status_code == 202
        queued = response.json()
        assert queued['status'] == 'queued'
        assert queued['storage_name'].startswith('media_')
        assert '..' not in queued['storage_name']
        job = wait_for_status(manager, queued['upload_id'], {'completed'})
        assert job['attempts'] == 1
        assert job['result']['ocr']['engine'] == 'rapidocr'
        assert job['result']['ocr']['items'][0]['text'] == '东湖花园 160平方米 365万'
        assert job['result']['hints']['confidence_status'] == 'not_calibrated'
        assert job['result']['ocr']['items'][0]['frame_path'].endswith('/frames/0')
        assert manager._file_path(job).stat().st_mode & 0o777 == 0o600
        assert manager.root.stat().st_mode & 0o777 == 0o700
        frame = client.get(job['result']['ocr']['items'][0]['frame_path'],
                           headers={'X-API-Key': API_KEY})
        assert frame.status_code == 200
        assert frame.content == b'jpeg-evidence'
        assert client.post('/api/media/uploads/' + queued['upload_id'] + '/retry',
                           headers={'X-API-Key': API_KEY}).json()['error']['code'] == 'not_retryable'


def test_upload_auth_permission_format_signature_duplicate_and_quota(monkeypatch, tmp_path):
    with upload_client(tmp_path, monkeypatch, maximum=64, quota=2048) as (client, _manager):
        unauthenticated = client.post('/api/media/uploads', files={
            'file': ('x.mp4', io.BytesIO(VALID_MP4), 'video/mp4')})
        assert unauthenticated.status_code == 401

        missing_note = client.post('/api/media/uploads', headers={'X-API-Key': API_KEY},
                                   data={'source_type': 'operator_local'},
                                   files={'file': ('x.mp4', io.BytesIO(VALID_MP4), 'video/mp4')})
        assert missing_note.status_code == 400
        assert missing_note.json()['error']['code'] == 'permission_note_required'

        bad_source = submit(client, source_type='unapproved')
        assert bad_source.status_code == 400
        assert bad_source.json()['error']['code'] == 'invalid_source_type'

        bad_extension = submit(client, name='synthetic.exe')
        assert bad_extension.status_code == 400
        assert bad_extension.json()['error']['code'] == 'unsupported_format'

        bad_signature = submit(client, data=b'not a movie', name='synthetic.mp4')
        assert bad_signature.status_code == 400
        assert bad_signature.json()['error']['code'] == 'invalid_media'

        oversized = submit(client, data=VALID_MP4 + b'x' * 64)
        assert oversized.status_code == 413
        assert oversized.json()['error']['code'] == 'too_large'

        first = submit(client)
        assert first.status_code == 202
        duplicate = submit(client)
        assert duplicate.status_code == 409
        assert duplicate.json()['error']['code'] == 'duplicate_sha256'


def test_storage_quota_is_checked_before_persisting_upload(monkeypatch, tmp_path):
    with upload_client(tmp_path, monkeypatch, maximum=1024, quota=32) as (client, manager):
        response = submit(client)
        assert response.status_code == 413
        assert response.json()['error']['code'] == 'storage_quota_exceeded'
        assert manager.list_jobs(10) == []


def test_http_body_limit_rejects_large_request_before_multipart_parsing(monkeypatch, tmp_path):
    monkeypatch.setenv('NBRE_MEDIA_UPLOAD_MAX_BYTES', '64')
    with upload_client(tmp_path, monkeypatch, maximum=64) as (client, _manager):
        response = client.post(
            '/api/media/uploads',
            headers={'X-API-Key': API_KEY, 'Content-Length': str(64 + 128 * 1024 + 1)},
            content=b'',
        )
        assert response.status_code == 413
        assert response.json()['error']['code'] == 'too_large'


def test_failed_upload_can_be_retried_without_reuploading_file(monkeypatch, tmp_path):
    calls = []

    def flaky_pipeline(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise MediaPipelineError('ffmpeg_timeout', 'processing timed out')
        return fake_pipeline(*args, **kwargs)

    with upload_client(tmp_path, monkeypatch, runner=flaky_pipeline) as (client, manager):
        first = submit(client)
        upload_id = first.json()['upload_id']
        failed = wait_for_status(manager, upload_id, {'failed'})
        assert failed['error']['code'] == 'ffmpeg_timeout'
        stored = manager._file_path(failed)
        size_before = stored.stat().st_size

        retried = client.post('/api/media/uploads/' + upload_id + '/retry',
                              headers={'X-API-Key': API_KEY})
        assert retried.status_code == 202
        completed = wait_for_status(manager, upload_id, {'completed'})
        assert completed['attempts'] == 2
        assert stored.exists() and stored.stat().st_size == size_before


def test_missing_ocr_is_explicit_and_retryable(monkeypatch, tmp_path):
    calls = []

    def unavailable_then_ready(*args, **kwargs):
        calls.append(1)
        evidence = fake_pipeline(*args, **kwargs)
        if len(calls) == 1:
            return replace(evidence, ocr=OcrResult(
                status='unavailable', engine='rapidocr', error='runtime unavailable'))
        return evidence

    with upload_client(tmp_path, monkeypatch, runner=unavailable_then_ready) as (client, manager):
        first = submit(client)
        upload_id = first.json()['upload_id']
        missing = wait_for_status(manager, upload_id, {'failed_unavailable_ocr'})
        assert missing['error']['code'] == 'ocr_unavailable'
        response = client.post('/api/media/uploads/' + upload_id + '/retry',
                               headers={'X-API-Key': API_KEY})
        assert response.status_code == 202
        ready = wait_for_status(manager, upload_id, {'completed'})
        assert ready['attempts'] == 2
        assert ready['result']['ocr']['status'] == 'ok'
