"""Filesystem-backed upload queue for operator-provided, authorized videos."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import queue
import re
import shutil
import stat
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.media_pipeline import (MediaPipelineError, build_asr_engine,
                                build_ocr_engine, run_pipeline)

log = logging.getLogger('media_uploads')
CHUNK_BYTES = 1024 * 1024
SUPPORTED_EXTENSIONS = {'.mp4', '.mov', '.m4v', '.mkv', '.webm'}
SOURCE_TYPES = {'operator_local', 'authorized_author', 'licensed_platform'}
UPLOAD_NAME_RE = re.compile(r'^media_[0-9a-f]{32}\.(mp4|mov|m4v|mkv|webm)$')


class UploadServiceError(Exception):
    def __init__(self, status_code: int, code: str, detail: str, **extra):
        super().__init__(detail)
        self.status_code = status_code
        self.code = code
        self.detail = detail
        self.extra = extra


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_text(value: str | None, maximum: int) -> str | None:
    if value is None:
        return None
    text = ''.join(ch for ch in value.strip() if ch >= ' ' and ch != '\x7f')
    return text[:maximum] or None


class UploadManager:
    """One process-local worker; job state and evidence survive API restarts."""

    def __init__(self, root: str | Path | None = None, *, max_file_bytes: int | None = None,
                 quota_bytes: int | None = None, processing_headroom_bytes: int | None = None,
                 pipeline_runner=None):
        default_root = Path(os.getenv('RAW_HTML_DIR', '/data/raw-pages')).parent / 'media-uploads-uat'
        self.root = Path(root or os.getenv('NBRE_MEDIA_UPLOAD_DIR') or default_root)
        self.max_file_bytes = max_file_bytes or int(os.getenv('NBRE_MEDIA_UPLOAD_MAX_BYTES', str(1024**3)))
        self.quota_bytes = quota_bytes or int(os.getenv('NBRE_MEDIA_UPLOAD_QUOTA_BYTES', str(20 * 1024**3)))
        self.processing_headroom_bytes = (processing_headroom_bytes if processing_headroom_bytes is not None
                                          else int(os.getenv('NBRE_MEDIA_PROCESSING_HEADROOM_BYTES',
                                                             str(self.max_file_bytes * 2))))
        if self.processing_headroom_bytes < 0:
            raise ValueError('processing headroom must be non-negative')
        self.pipeline_runner = pipeline_runner or run_pipeline
        self._jobs: dict[str, dict] = {}
        self._sha_index: dict[str, str] = {}
        self._queue: queue.Queue[str | None] = queue.Queue()
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._loaded = False

    @property
    def files_dir(self) -> Path:
        return self.root / 'files'

    @property
    def jobs_dir(self) -> Path:
        return self.root / 'jobs'

    @property
    def frames_dir(self) -> Path:
        return self.root / 'frames'

    @property
    def work_dir(self) -> Path:
        return self.root / 'work'

    def _ensure_directory(self, path: Path) -> None:
        if path.is_symlink():
            raise UploadServiceError(503, 'storage_unavailable', 'upload storage path is unsafe')
        try:
            path.mkdir(mode=0o700, parents=True, exist_ok=True)
            if path.is_symlink() or not path.is_dir():
                raise OSError('not a directory')
            os.chmod(path, 0o700)
        except OSError:
            raise UploadServiceError(503, 'storage_unavailable', 'upload storage is unavailable') from None

    def _ensure_storage(self) -> None:
        self._ensure_directory(self.root)
        for child in (self.files_dir, self.jobs_dir, self.frames_dir, self.work_dir):
            self._ensure_directory(child)

    def _manifest_path(self, upload_id: str) -> Path:
        try:
            normalized = uuid.UUID(upload_id).hex
        except (ValueError, AttributeError):
            raise UploadServiceError(404, 'upload_not_found', 'upload was not found') from None
        return self.jobs_dir / (normalized + '.json')

    def _write_manifest(self, job: dict) -> None:
        target = self._manifest_path(job['upload_id'])
        tmp = self.jobs_dir / ('.' + uuid.uuid4().hex + '.tmp')
        try:
            fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                json.dump(job, stream, ensure_ascii=False, separators=(',', ':'))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(tmp, target)
        except OSError:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
            raise UploadServiceError(503, 'storage_unavailable', 'upload metadata could not be saved') from None

    def _storage_usage(self) -> int:
        total = 0
        try:
            for directory, dirs, files in os.walk(self.root, followlinks=False):
                base = Path(directory)
                for name in dirs:
                    if (base / name).is_symlink():
                        raise OSError('symlink directory')
                for name in files:
                    item = base / name
                    info = item.lstat()
                    if not stat.S_ISREG(info.st_mode):
                        raise OSError('non-regular file')
                    total += info.st_size
        except OSError:
            raise UploadServiceError(503, 'storage_unavailable', 'upload storage could not be inspected') from None
        return total

    def _load_jobs(self) -> None:
        if self._loaded:
            return
        self._ensure_storage()
        for path in self.jobs_dir.glob('*.json'):
            if path.is_symlink():
                raise UploadServiceError(503, 'storage_unavailable', 'upload metadata path is unsafe')
            try:
                job = json.loads(path.read_text(encoding='utf-8'))
                upload_id = uuid.UUID(job['upload_id']).hex
                if path.name != upload_id + '.json' or not UPLOAD_NAME_RE.fullmatch(job['storage_name']):
                    continue
                self._jobs[upload_id] = job
                self._sha_index[job['sha256']] = upload_id
            except (OSError, ValueError, KeyError, TypeError):
                log.warning('ignoring invalid upload manifest')
        for job in self._jobs.values():
            if job['status'] in ('queued', 'processing'):
                job['status'] = 'queued'
                job['error'] = None
                self._write_manifest(job)
                self._queue.put(job['upload_id'])
        self._loaded = True

    def start(self) -> None:
        with self._lock:
            self._load_jobs()
            if self._thread and self._thread.is_alive():
                return
            self._stop.clear()
            self._thread = threading.Thread(target=self._worker, name='media-upload-worker', daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._queue.put(None)
        thread = self._thread
        if thread and thread.is_alive():
            thread.join(timeout=5)

    def _file_path(self, job: dict) -> Path:
        name = job.get('storage_name', '')
        if not UPLOAD_NAME_RE.fullmatch(name):
            raise UploadServiceError(503, 'storage_unavailable', 'stored upload path is invalid')
        path = self.files_dir / name
        if path.is_symlink():
            raise UploadServiceError(503, 'storage_unavailable', 'stored upload path is unsafe')
        return path

    def upload(self, stream, filename: str | None, source_type: str | None,
               permission_note: str | None, title: str | None = None,
               description: str | None = None) -> dict:
        with self._lock:
            self._load_jobs()
            note = _clean_text(permission_note, 500)
            source = _clean_text(source_type, 40)
            if source not in SOURCE_TYPES:
                raise UploadServiceError(400, 'invalid_source_type', 'source_type is invalid')
            if not note or len(note) < 10:
                raise UploadServiceError(400, 'permission_note_required',
                                         'permission_note must contain 10 to 500 characters')
            if permission_note and len(permission_note.strip()) > 500:
                raise UploadServiceError(400, 'permission_note_too_long', 'permission_note is too long')
            safe_title = _clean_text(title, 200)
            safe_description = _clean_text(description, 2000)
            if title and safe_title is None:
                raise UploadServiceError(400, 'invalid_title', 'title is invalid')
            suffix = Path((filename or '').replace('\\', '/').split('/')[-1]).suffix.lower()
            if suffix not in SUPPORTED_EXTENSIONS:
                raise UploadServiceError(400, 'unsupported_format', 'file extension is not supported')
            usage = self._storage_usage()
            if usage >= self.quota_bytes:
                raise UploadServiceError(413, 'storage_quota_exceeded', 'upload storage quota is full')

            upload_id = uuid.uuid4().hex
            storage_name = 'media_' + upload_id + suffix
            tmp_path = self.files_dir / ('.' + upload_id + '.part')
            final_path = self.files_dir / storage_name
            digest = hashlib.sha256()
            prefix = bytearray()
            size = 0
            try:
                fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
                with os.fdopen(fd, 'wb') as target:
                    while True:
                        chunk = stream.read(CHUNK_BYTES)
                        if not chunk:
                            break
                        size += len(chunk)
                        if size > self.max_file_bytes:
                            raise UploadServiceError(413, 'too_large', 'uploaded file exceeds the configured limit')
                        if usage + size + self.processing_headroom_bytes > self.quota_bytes:
                            raise UploadServiceError(413, 'storage_quota_exceeded', 'upload storage quota would be exceeded')
                        if len(prefix) < 64:
                            prefix.extend(chunk[:64 - len(prefix)])
                        digest.update(chunk)
                        target.write(chunk)
                    target.flush()
                    os.fsync(target.fileno())
                if not self._signature_matches(suffix, bytes(prefix)):
                    raise UploadServiceError(400, 'invalid_media', 'file signature does not match its extension')
                sha = digest.hexdigest()
                existing = self._sha_index.get(sha)
                if existing:
                    raise UploadServiceError(409, 'duplicate_sha256', 'identical video already exists',
                                             existing_upload_id=existing)
                if size == 0:
                    raise UploadServiceError(400, 'invalid_media', 'uploaded file is empty')
                job = {
                    'upload_id': upload_id, 'status': 'queued', 'source_type': source,
                    'permission_note': note, 'title': safe_title, 'description': safe_description,
                    'storage_name': storage_name, 'sha256': sha, 'size_bytes': size,
                    'created_at': _utc_now(), 'updated_at': _utc_now(), 'attempts': 1,
                    'result': None, 'error': None,
                }
                manifest_bytes = len(json.dumps(job, ensure_ascii=False,
                                                separators=(',', ':')).encode('utf-8'))
                if usage + size + manifest_bytes + self.processing_headroom_bytes > self.quota_bytes:
                    raise UploadServiceError(413, 'storage_quota_exceeded',
                                             'upload storage quota would be exceeded')
                os.replace(tmp_path, final_path)
                try:
                    self._write_manifest(job)
                except UploadServiceError:
                    final_path.unlink(missing_ok=True)
                    raise
                self._jobs[upload_id] = job
                self._sha_index[sha] = upload_id
                self._queue.put(upload_id)
                return self._public_job(job)
            except UploadServiceError:
                tmp_path.unlink(missing_ok=True)
                raise
            except OSError:
                tmp_path.unlink(missing_ok=True)
                raise UploadServiceError(503, 'storage_unavailable', 'upload could not be stored') from None

    @staticmethod
    def _signature_matches(suffix: str, header: bytes) -> bool:
        if suffix in {'.mp4', '.mov', '.m4v'}:
            return len(header) >= 12 and header[4:8] == b'ftyp'
        return len(header) >= 4 and header[:4] == b'\x1a\x45\xdf\xa3'

    @staticmethod
    def _public_job(job: dict) -> dict:
        return json.loads(json.dumps(job, ensure_ascii=False))

    def list_jobs(self, limit: int) -> list[dict]:
        with self._lock:
            self._load_jobs()
            rows = sorted(self._jobs.values(), key=lambda row: row['created_at'], reverse=True)
            return [self._public_job(row) for row in rows[:limit]]

    def get_job(self, upload_id: str) -> dict:
        with self._lock:
            self._load_jobs()
            job = self._jobs.get(uuid.UUID(upload_id).hex)
            if not job:
                raise UploadServiceError(404, 'upload_not_found', 'upload was not found')
            return self._public_job(job)

    def retry(self, upload_id: str) -> dict:
        with self._lock:
            self._load_jobs()
            normalized = uuid.UUID(upload_id).hex
            job = self._jobs.get(normalized)
            if not job:
                raise UploadServiceError(404, 'upload_not_found', 'upload was not found')
            if job['status'] not in ('failed', 'failed_unavailable_ocr'):
                raise UploadServiceError(409, 'not_retryable', 'only failed uploads can be retried')
            path = self._file_path(job)
            if not path.is_file() or path.stat().st_size != job['size_bytes']:
                raise UploadServiceError(409, 'storage_unavailable', 'stored video is missing or changed')
            digest = hashlib.sha256()
            with path.open('rb') as stream:
                for chunk in iter(lambda: stream.read(CHUNK_BYTES), b''):
                    digest.update(chunk)
            if digest.hexdigest() != job['sha256']:
                raise UploadServiceError(409, 'storage_unavailable', 'stored video is missing or changed')
            job['status'] = 'queued'
            job['error'] = None
            job['attempts'] += 1
            job['updated_at'] = _utc_now()
            self._write_manifest(job)
            self._queue.put(normalized)
            return self._public_job(job)

    def frame_path(self, upload_id: str, frame_index: int) -> Path:
        job = self.get_job(upload_id)
        if job['status'] not in ('completed', 'failed', 'failed_unavailable_ocr'):
            raise UploadServiceError(404, 'frame_not_found', 'frame evidence is not available')
        path = self.frames_dir / uuid.UUID(upload_id).hex / ('frame_%04d.jpg' % frame_index)
        if path.is_symlink() or not path.is_file():
            raise UploadServiceError(404, 'frame_not_found', 'frame evidence was not found')
        return path

    def _worker(self) -> None:
        while not self._stop.is_set():
            try:
                upload_id = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue
            if upload_id is None:
                self._queue.task_done()
                continue
            try:
                self._process(upload_id)
            except Exception:  # noqa: BLE001 - a bad media job must not stop the worker
                log.error('media upload worker recovered from an unexpected job failure')
                self._fail(upload_id, 'internal_error', 'media processing failed unexpectedly')
            finally:
                self._queue.task_done()

    def _process(self, upload_id: str) -> None:
        with self._lock:
            job = self._jobs.get(upload_id)
            if not job or job['status'] != 'queued':
                return
            job['status'] = 'processing'
            job['updated_at'] = _utc_now()
            self._write_manifest(job)
            media_path = self._file_path(job)
        work = self.work_dir / (upload_id + '-' + uuid.uuid4().hex)
        try:
            evidence = self.pipeline_runner(
                media_path,
                asr_engine=build_asr_engine(os.getenv('NBRE_MEDIA_ASR_ENGINE', 'auto')),
                ocr_engine=build_ocr_engine(os.getenv('NBRE_MEDIA_OCR_ENGINE', 'rapidocr')),
                work_dir=work,
                keep_work=True,
                known_community_names=[name.strip() for name in
                                       os.getenv('NBRE_MEDIA_KNOWN_COMMUNITIES', '').split(',')
                                       if name.strip()],
            )
            result = evidence.as_dict()
            self._retain_frame_evidence(upload_id, result, work)
            if evidence.ocr.status == 'unavailable':
                self._finish(upload_id, 'failed_unavailable_ocr', result,
                             'ocr_unavailable', 'RapidOCR is unavailable in this runtime')
            elif evidence.ocr.status != 'ok':
                code = 'ocr_unavailable' if evidence.ocr.status == 'failed' else 'ffmpeg_failed'
                self._finish(upload_id, 'failed', result, code,
                             'video frames could not be recognized')
            else:
                self._finish(upload_id, 'completed', result, None, None)
        except UploadServiceError as exc:
            self._fail(upload_id, exc.code, exc.detail)
        except MediaPipelineError as exc:
            code, detail = {
                'invalid_input': ('invalid_media', 'video could not be validated'),
                'unsupported_format': ('unsupported_format', 'video format is not supported'),
                'too_large': ('too_large', 'video exceeds the configured size limit'),
                'too_long': ('too_long', 'video exceeds the configured duration limit'),
                'ffmpeg_missing': ('ffmpeg_missing', 'FFmpeg/ffprobe is unavailable'),
                'ffmpeg_timeout': ('ffmpeg_timeout', 'FFmpeg exceeded the processing time limit'),
                'ffmpeg_failed': ('ffmpeg_failed', 'FFmpeg processing failed'),
                'media_busy': ('internal_error', 'another media-processing job is running'),
                'media_lock_failed': ('internal_error', 'media-processing lock is unavailable'),
            }.get(exc.kind, ('internal_error', 'media processing failed'))
            self._fail(upload_id, code, detail)
        except Exception as exc:  # noqa: BLE001 - retain safe status, not exception contents
            log.warning('media upload processing failed: %s', type(exc).__name__)
            self._fail(upload_id, 'internal_error', 'media processing failed')
        finally:
            shutil.rmtree(work, ignore_errors=True)

    def _retain_frame_evidence(self, upload_id: str, result: dict, work: Path) -> None:
        items = result.get('ocr', {}).get('items', [])
        if not items:
            return
        destination = self.frames_dir / upload_id
        with self._lock:
            self._ensure_directory(destination)
            for item in items:
                source = Path(item['frame_path'])
                try:
                    source.resolve().relative_to(work.resolve())
                except (OSError, ValueError):
                    raise UploadServiceError(503, 'storage_unavailable', 'OCR frame path is unsafe') from None
                target = destination / ('frame_%04d.jpg' % int(item['frame_index']))
                if target.is_symlink() or (target.exists() and not target.is_file()):
                    raise UploadServiceError(503, 'storage_unavailable', 'OCR frame evidence is unsafe') from None
                if not target.exists():
                    if source.is_symlink() or not source.is_file():
                        raise UploadServiceError(503, 'storage_unavailable', 'OCR frame evidence is unavailable') from None
                    os.replace(source, target)
                    os.chmod(target, 0o600)
                url = '/api/media/uploads/%s/frames/%s' % (upload_id, item['frame_index'])
                item['frame_path'] = url
                item['frame_url'] = url

    def _finish(self, upload_id: str, status: str, result: dict,
                error_code: str | None, detail: str | None) -> None:
        with self._lock:
            job = self._jobs[upload_id]
            job['status'] = status
            job['result'] = result
            job['error'] = ({'code': error_code, 'detail': detail} if error_code else None)
            job['updated_at'] = _utc_now()
            self._write_manifest(job)

    def _fail(self, upload_id: str, code: str, detail: str) -> None:
        with self._lock:
            job = self._jobs.get(upload_id)
            if not job:
                return
            job['status'] = 'failed'
            job['error'] = {'code': code, 'detail': detail}
            job['updated_at'] = _utc_now()
            try:
                self._write_manifest(job)
            except UploadServiceError:
                log.error('failed to persist media upload failure state')


upload_manager = UploadManager()


def start_upload_worker() -> None:
    upload_manager.start()


def stop_upload_worker() -> None:
    upload_manager.stop()


def get_upload_manager() -> UploadManager:
    return upload_manager
