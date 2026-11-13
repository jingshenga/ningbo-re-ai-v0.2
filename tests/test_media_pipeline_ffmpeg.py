"""FFmpeg wrapper tests: fake subprocess results, limit rejections, error kinds."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from app.media_pipeline import ffmpeg_tools, limits
from app.media_pipeline.errors import MediaPipelineError


class FakeProc:
    def __init__(self, returncode=0, stdout='', stderr=''):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


@pytest.fixture()
def tools_on_path(monkeypatch):
    monkeypatch.setattr(ffmpeg_tools.shutil, 'which', lambda name: '/usr/bin/' + name)


def _probe_json(duration=30.0, format_name='mov,mp4,m4a,3gp,3g2,mj2', has_audio=True):
    streams = [{'codec_type': 'video', 'width': 1920, 'height': 1080}]
    if has_audio:
        streams.append({'codec_type': 'audio'})
    return json.dumps({'format': {'duration': str(duration), 'format_name': format_name},
                       'streams': streams})


def _run_fake(monkeypatch, proc):
    monkeypatch.setattr(ffmpeg_tools.subprocess, 'run',
                        lambda *a, **kw: proc)


def test_probe_media_reads_duration_streams_and_flags(tools_on_path, monkeypatch, tmp_path):
    _run_fake(monkeypatch, FakeProc(stdout=_probe_json(duration=65.0, has_audio=False)))
    info = ffmpeg_tools.probe_media(tmp_path, size_bytes=12345)
    assert info['duration_seconds'] == 65.0
    assert info['has_audio'] is False
    assert info['width'] == 1920 and info['height'] == 1080
    assert info['size_bytes'] == 12345


def test_probe_media_rejects_overlong_media(tools_on_path, monkeypatch, tmp_path):
    _run_fake(monkeypatch, FakeProc(stdout=_probe_json(duration=limits.MAX_DURATION_SECONDS + 1)))
    with pytest.raises(MediaPipelineError) as err:
        ffmpeg_tools.probe_media(tmp_path, size_bytes=10)
    assert err.value.kind == 'too_long'


def test_probe_media_rejects_empty_media(tools_on_path, monkeypatch, tmp_path):
    _run_fake(monkeypatch, FakeProc(stdout=_probe_json(duration=0.1)))
    with pytest.raises(MediaPipelineError) as err:
        ffmpeg_tools.probe_media(tmp_path, size_bytes=10)
    assert err.value.kind == 'invalid_input'


def test_probe_media_maps_ffprobe_failure(tools_on_path, monkeypatch, tmp_path):
    _run_fake(monkeypatch, FakeProc(returncode=1, stderr='Invalid data found'))
    with pytest.raises(MediaPipelineError) as err:
        ffmpeg_tools.probe_media(tmp_path, size_bytes=10)
    assert err.value.kind == 'invalid_input'
    assert 'Invalid data found' in err.value.detail


def test_probe_media_maps_timeout(tools_on_path, monkeypatch, tmp_path):
    def blow_up(*a, **kw):
        raise subprocess.TimeoutExpired(cmd='ffprobe', timeout=1)
    monkeypatch.setattr(ffmpeg_tools.subprocess, 'run', blow_up)
    with pytest.raises(MediaPipelineError) as err:
        ffmpeg_tools.probe_media(tmp_path, size_bytes=10)
    assert err.value.kind == 'ffmpeg_timeout'


def test_validate_input_rejects_unsupported_extension(tmp_path):
    bad = tmp_path / 'listing.txt'
    bad.write_text('x', encoding='utf-8')
    with pytest.raises(MediaPipelineError) as err:
        ffmpeg_tools.validate_input(bad)
    assert err.value.kind == 'unsupported_format'


def test_validate_input_rejects_missing_file(tmp_path):
    with pytest.raises(MediaPipelineError) as err:
        ffmpeg_tools.validate_input(tmp_path / 'missing.mp4')
    assert err.value.kind == 'invalid_input'


def test_validate_input_rejects_oversized_file(tmp_path, monkeypatch):
    big = tmp_path / 'big.mp4'
    big.write_bytes(b'00')  # 2 bytes vs 1-byte limit
    monkeypatch.setattr(limits, 'MAX_INPUT_BYTES', 1)
    with pytest.raises(MediaPipelineError) as err:
        ffmpeg_tools.validate_input(big)
    assert err.value.kind == 'too_large'


def test_prepare_input_copies_and_hashes(tmp_path):
    source = tmp_path / 'src.mp4'
    payload = b'video-bytes' * 100
    source.write_bytes(payload)
    sha, size = ffmpeg_tools.prepare_input(source, tmp_path)
    assert size == len(payload)
    assert len(sha) == 64
    assert (tmp_path / 'input.media').read_bytes() == payload


def test_extract_audio_returns_none_for_empty_output(tools_on_path, monkeypatch, tmp_path):
    _run_fake(monkeypatch, FakeProc(stdout=''))
    assert ffmpeg_tools.extract_audio(tmp_path) is None


def test_extract_audio_returns_path_on_success(tools_on_path, monkeypatch, tmp_path):
    _run_fake(monkeypatch, FakeProc(stdout=''))
    (tmp_path / 'audio.wav').write_bytes(b'RIFF0000')
    assert ffmpeg_tools.extract_audio(tmp_path) == tmp_path / 'audio.wav'


def test_extract_audio_maps_ffmpeg_failure(tools_on_path, monkeypatch, tmp_path):
    _run_fake(monkeypatch, FakeProc(returncode=1, stderr='Output file #0 does not contain any stream'))
    with pytest.raises(MediaPipelineError) as err:
        ffmpeg_tools.extract_audio(tmp_path)
    assert err.value.kind == 'ffmpeg_failed'


def test_extract_keyframes_maps_index_and_timestamps(tools_on_path, monkeypatch, tmp_path):
    _run_fake(monkeypatch, FakeProc(stdout=''))
    for name in ('frame_0001.jpg', 'frame_0002.jpg', 'frame_0003.jpg'):
        (tmp_path / name).write_bytes(b'jpg')
    frames = ffmpeg_tools.extract_keyframes(tmp_path)
    assert [f.index for f in frames] == [0, 1, 2]
    assert [f.timestamp_seconds for f in frames] == [
        round(i * limits.KEYFRAME_INTERVAL_SECONDS, 3) for i in (0, 1, 2)]
    assert all(f.source == 'interval' for f in frames)


def test_extract_keyframes_maps_ffmpeg_failure(tools_on_path, monkeypatch, tmp_path):
    _run_fake(monkeypatch, FakeProc(returncode=1, stderr='Error opening input'))
    with pytest.raises(MediaPipelineError) as err:
        ffmpeg_tools.extract_keyframes(tmp_path)
    assert err.value.kind == 'ffmpeg_failed'


def test_require_ffmpeg_tools_fails_closed(monkeypatch):
    monkeypatch.setattr(ffmpeg_tools.shutil, 'which', lambda name: None)
    with pytest.raises(MediaPipelineError) as err:
        ffmpeg_tools.probe_media(Path('/tmp'), size_bytes=1)
    assert err.value.kind == 'ffmpeg_missing'
