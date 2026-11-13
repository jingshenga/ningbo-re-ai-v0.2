"""FFmpeg/ffprobe subprocess wrappers for the local media pipeline.

Design constraint: every ffmpeg argv is a *literal* argument vector (never a
shell, shell=False) and file paths never enter argv — the operator's media is
copied into the isolated work directory under the fixed name `input.media`
and ffmpeg runs with `cwd=work_dir` against fixed output names. This keeps
command injection structurally impossible while bounding disk, time and
output volume for the DXP4800 single-job policy.
"""
from __future__ import annotations

import hashlib
import os
import json
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path

from app.media_pipeline import limits
from app.media_pipeline.errors import MediaPipelineError

_FFPROBE = 'ffprobe'
_FFMPEG = 'ffmpeg'
_READ_CHUNK = 1024 * 1024
_INPUT_NAME = 'input.media'
_AUDIO_NAME = 'audio.wav'
_FRAME_PATTERN = 'frame_%04d.jpg'


def _sanitize(stderr: str) -> str:
    first_line = next((line for line in stderr.splitlines() if line.strip()), '')
    return first_line.strip()[:160] or 'no stderr output'


@contextmanager
def _tool_errors():
    """Map subprocess-level failures to stable MediaPipelineError kinds."""
    try:
        yield
    except subprocess.TimeoutExpired as exc:
        raise MediaPipelineError(
            'ffmpeg_timeout',
            'ffmpeg exceeded the ' + format(limits.FFMPEG_TIMEOUT_SECONDS, 'g') + 's time limit',
        ) from exc
    except OSError as exc:
        raise MediaPipelineError(
            'ffmpeg_missing',
            'ffmpeg/ffprobe is not installed or not executable: ' + str(exc.strerror),
        ) from exc


def _require_ffmpeg_tools() -> None:
    if shutil.which(_FFMPEG) is None or shutil.which(_FFPROBE) is None:
        raise MediaPipelineError('ffmpeg_missing', 'ffmpeg and ffprobe are required on PATH')


def validate_input(path: Path) -> Path:
    """Pure checks before any copy or process spawn; no subprocess involved."""
    candidate = Path(path).resolve(strict=False)
    if not candidate.is_file():
        raise MediaPipelineError('invalid_input', 'input is not a regular file')
    if candidate.suffix.lower() not in limits.SUPPORTED_EXTENSIONS:
        raise MediaPipelineError(
            'unsupported_format',
            'unsupported extension ' + (candidate.suffix.lower() or '(none)'),
        )
    size = candidate.stat().st_size
    if size > limits.MAX_INPUT_BYTES:
        raise MediaPipelineError(
            'too_large',
            'file size ' + str(size) + ' exceeds the ' + str(limits.MAX_INPUT_BYTES) + ' byte limit',
        )
    return candidate


def prepare_input(source: Path, work_dir: Path) -> tuple[str, int]:
    """Copy the validated media into the isolated work dir; returns (sha256, size).

    The SHA-256 is computed over the operator's original bytes while copying,
    so evidence always refers to the input the operator handed over.
    """
    digest = hashlib.sha256()
    size = 0
    destination = Path(work_dir) / _INPUT_NAME
    # Exclusive creation prevents races with pre-existing files/symlinks.
    # This is a local tool, but supplied work folders must still be safe.
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with source.open('rb') as reader, os.fdopen(fd, 'wb') as writer:
        while True:
            chunk = reader.read(_READ_CHUNK)
            if not chunk:
                break
            digest.update(chunk)
            writer.write(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def probe_media(work_dir: Path, size_bytes: int) -> dict:
    """Read metadata from the prepared input; returns MediaInfo fields minus sha256."""
    _require_ffmpeg_tools()
    try:
        with _tool_errors():
            proc = subprocess.run(
                ['ffprobe', '-v', 'error', '-print_format', 'json',
                 '-show_format', '-show_streams', 'input.media'],
                shell=False, capture_output=True, text=True, check=False,
                timeout=limits.FFMPEG_TIMEOUT_SECONDS, cwd=str(Path(work_dir)),
            )
        if proc.returncode != 0:
            raise MediaPipelineError(
                'invalid_input',
                'ffprobe rejected the file (exit ' + str(proc.returncode) + '): ' + _sanitize(proc.stderr),
            )
        data = json.loads(proc.stdout or '{}')
        duration = float(data.get('format', {}).get('duration') or 0.0)
        if duration < limits.MIN_DURATION_SECONDS:
            raise MediaPipelineError('invalid_input', 'media is empty or shorter than the minimum duration')
        if duration > limits.MAX_DURATION_SECONDS:
            raise MediaPipelineError(
                'too_long',
                'duration ' + format(duration, 'g') + 's exceeds the '
                + format(limits.MAX_DURATION_SECONDS, 'g') + 's limit',
            )
        streams = data.get('streams') or []
        has_audio = any(stream.get('codec_type') == 'audio' for stream in streams)
        video = next((s for s in streams if s.get('codec_type') == 'video'), {})
        width, height = video.get('width'), video.get('height')
        return {
            'size_bytes': size_bytes,
            'duration_seconds': duration,
            'format_name': str(data.get('format', {}).get('format_name') or 'unknown'),
            'has_audio': has_audio,
            'width': int(width) if isinstance(width, int) else None,
            'height': int(height) if isinstance(height, int) else None,
        }
    except MediaPipelineError:
        raise
    except (json.JSONDecodeError, ValueError, OSError) as exc:
        raise MediaPipelineError(
            'invalid_input',
            'could not read media metadata: ' + type(exc).__name__,
        ) from exc


def extract_audio(work_dir: Path) -> Path | None:
    """Extract 16 kHz mono PCM (WAV) for ASR. Returns None when the input has no audio."""
    _require_ffmpeg_tools()
    with _tool_errors():
        proc = subprocess.run(
            ['ffmpeg', '-v', 'error', '-y', '-i', 'input.media',
             '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', 'audio.wav'],
            shell=False, capture_output=True, text=True, check=False,
            timeout=limits.FFMPEG_TIMEOUT_SECONDS, cwd=str(Path(work_dir)),
        )
    if proc.returncode != 0:
        raise MediaPipelineError(
            'ffmpeg_failed',
            'audio extraction failed (exit ' + str(proc.returncode) + '): ' + _sanitize(proc.stderr),
        )
    out_path = Path(work_dir) / _AUDIO_NAME
    if not out_path.exists() or out_path.stat().st_size == 0:
        return None
    return out_path


def extract_keyframes(work_dir: Path) -> list:
    """Sample one frame every KEYFRAME_INTERVAL_SECONDS, capped at MAX_KEYFRAMES.

    The filter and frame cap are literal argv entries; the numeric interval
    (from limits) drives timestamp attribution only.
    """
    from app.media_pipeline.models import KeyFrame
    _require_ffmpeg_tools()
    with _tool_errors():
        proc = subprocess.run(
            ['ffmpeg', '-v', 'error', '-y', '-i', 'input.media',
             '-vf', limits.interval_filter(),
             '-frames:v', str(limits.MAX_KEYFRAMES), '-q:v', '3',
             'frame_%04d.jpg'],
            shell=False, capture_output=True, text=True, check=False,
            timeout=limits.FFMPEG_TIMEOUT_SECONDS, cwd=str(Path(work_dir)),
        )
    if proc.returncode != 0:
        raise MediaPipelineError(
            'ffmpeg_failed',
            'frame extraction failed (exit ' + str(proc.returncode) + '): ' + _sanitize(proc.stderr),
        )
    frames = []
    for frame_path in sorted(Path(work_dir).glob('frame_*.jpg')):
        index = int(frame_path.stem.split('_')[-1]) - 1  # %04d is 1-based
        frames.append(KeyFrame(
            path=str(frame_path), index=index,
            timestamp_seconds=round(index * limits.KEYFRAME_INTERVAL_SECONDS, 3),
            source='interval'))
    return frames
