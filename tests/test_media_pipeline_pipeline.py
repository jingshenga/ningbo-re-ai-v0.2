"""Pipeline orchestration tests: full chain with mocked ffmpeg tools and engines.

Covers: happy path, no audio, empty OCR, ffmpeg failure, ASR unavailable,
OCR unavailable, multiple price mentions, work-dir cleanup and deterministic
re-runs. extract_hints runs for real, so price/area/bedroom candidates are
checked against its actual conservative behavior.
"""
from __future__ import annotations

import builtins
import json
import tempfile
from pathlib import Path

import pytest

from app.media_pipeline import ffmpeg_tools, run_pipeline
from app.media_pipeline.asr import MockAsrEngine, UnavailableAsrEngine
from app.media_pipeline.errors import MediaPipelineError
from app.media_pipeline.models import KeyFrame
from app.media_pipeline.ocr import MockOcrEngine, RapidOcrEngine


PROBE = {
    'size_bytes': 1024,
    'duration_seconds': 60.0,
    'format_name': 'mov,mp4,m4a,3gp,3g2,mj2',
    'has_audio': True,
    'width': 1280,
    'height': 720,
}


def _frame(index: int) -> KeyFrame:
    return KeyFrame(path='/tmp/f%s.jpg' % index, index=index,
                    timestamp_seconds=index * 2.0, source='interval')


def _patch_ffmpeg(monkeypatch, *, probe=None, frames=None, audio_path='/tmp/audio.wav',
                  audio_error=None, frame_error=None, source='/tmp/in.mp4'):
    monkeypatch.setattr(ffmpeg_tools, 'validate_input', lambda path: source)
    monkeypatch.setattr(ffmpeg_tools, 'prepare_input',
                        lambda src, work: ('sha256x', 1024))
    monkeypatch.setattr(ffmpeg_tools, 'probe_media',
                        lambda work, size: dict(probe or PROBE))

    def fake_audio(work):
        if audio_error:
            raise MediaPipelineError(audio_error, audio_error)
        return audio_path

    def fake_frames(work, duration_seconds=None):
        if frame_error:
            raise MediaPipelineError(frame_error, frame_error)
        return frames if frames is not None else [_frame(0), _frame(1), _frame(2)]

    monkeypatch.setattr(ffmpeg_tools, 'extract_audio', fake_audio)
    monkeypatch.setattr(ffmpeg_tools, 'extract_keyframes', fake_frames)


def test_happy_path_builds_transcript_ocr_and_hints(monkeypatch):
    _patch_ffmpeg(monkeypatch)
    evidence = run_pipeline(
        '/tmp/in.mp4',
        asr_engine=MockAsrEngine(script='东湖花园 建筑面积160平方米 四室两厅 报价365万'),
        ocr_engine=MockOcrEngine(text_map={0: '小区：东湖花园 总价：365万 精装修'}),
        known_community_names=['东湖花园'],
    )
    assert evidence.transcript.status == 'ok'
    assert evidence.ocr.status == 'ok' and len(evidence.ocr.items) == 1
    assert evidence.hints['price_mentions_wan'] == [365.0]  # deduped across sources
    assert evidence.hints['area_mentions_sqm'] == [160.0]
    assert evidence.hints['community_mentions'] == ['东湖花园']
    assert evidence.hints['confidence_status'] == 'not_calibrated'
    assert evidence.work_dir is None  # temp dir removed


def test_no_audio_marks_transcript_no_audio_but_still_ocr(monkeypatch):
    _patch_ffmpeg(monkeypatch, probe={**PROBE, 'has_audio': False},
                  audio_path=None)
    evidence = run_pipeline(
        '/tmp/in.mp4',
        asr_engine=MockAsrEngine(script='不该出现'),
        ocr_engine=MockOcrEngine(text_map={0: '总价：320万'}),
    )
    assert evidence.transcript.status == 'no_audio'
    assert evidence.transcript.text is None
    assert evidence.ocr.status == 'ok'
    assert evidence.hints['price_mentions_wan'] == [320.0]
    assert any('no audio' in w for w in evidence.warnings)


def test_empty_ocr_yields_empty_hints_without_crashing(monkeypatch):
    _patch_ffmpeg(monkeypatch)
    evidence = run_pipeline(
        '/tmp/in.mp4',
        asr_engine=MockAsrEngine(script='这是口播内容但无价格'),
        ocr_engine=MockOcrEngine(),
    )
    assert evidence.ocr.status == 'ok'
    assert evidence.ocr.items == ()
    assert evidence.hints['price_mentions_wan'] == []
    assert evidence.hints['area_mentions_sqm'] == []


def test_ffmpeg_frame_failure_degrades_ocr_with_warning(monkeypatch):
    _patch_ffmpeg(monkeypatch, frame_error='ffmpeg_failed')
    evidence = run_pipeline(
        '/tmp/in.mp4',
        asr_engine=MockAsrEngine(script='报价365万'),
        ocr_engine=MockOcrEngine(text_map={0: 'x'}),
    )
    assert evidence.ocr.status == 'failed'
    assert any('frame extraction failed' in w for w in evidence.warnings)


def test_ffmpeg_audio_failure_degrades_transcript(monkeypatch):
    _patch_ffmpeg(monkeypatch, audio_error='ffmpeg_failed', audio_path=None)
    evidence = run_pipeline(
        '/tmp/in.mp4',
        asr_engine=MockAsrEngine(script='x'),
        ocr_engine=MockOcrEngine(),
    )
    assert evidence.transcript.status == 'failed'


def test_asr_unavailable_is_explicit_and_flagged(monkeypatch):
    _patch_ffmpeg(monkeypatch)
    evidence = run_pipeline('/tmp/in.mp4', asr_engine=UnavailableAsrEngine(),
                            ocr_engine=MockOcrEngine())
    assert evidence.transcript.status == 'unavailable'
    assert any('no ASR engine available' in w for w in evidence.warnings)


def test_ocr_unavailable_is_explicit_and_flagged(monkeypatch):
    original_import = builtins.__import__

    def import_without_rapidocr(name, *args, **kwargs):
        if name == 'rapidocr_onnxruntime':
            raise ModuleNotFoundError("No module named 'rapidocr_onnxruntime'")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', import_without_rapidocr)
    _patch_ffmpeg(monkeypatch)
    evidence = run_pipeline('/tmp/in.mp4', asr_engine=MockAsrEngine(script=''),
                            ocr_engine=RapidOcrEngine())
    assert evidence.ocr.status == 'unavailable'


def test_multiple_prices_kept_as_mentions_not_a_listing(monkeypatch):
    _patch_ffmpeg(monkeypatch)
    evidence = run_pipeline(
        '/tmp/in.mp4',
        asr_engine=MockAsrEngine(script='原价400万 现报价365万 成交价355万'),
        ocr_engine=MockOcrEngine(text_map={0: '画面标注：368万'}),
    )
    assert sorted(evidence.hints['price_mentions_wan']) == [355.0, 365.0, 368.0, 400.0]
    # hints are线索 only: the extractor contract itself warns against treating
    # 口播/画面价格 as platform asking prices.
    assert '不得自动当作正式挂牌价' in evidence.hints['warning']
    assert evidence.hints['method'] == 'rule_based_hints_not_verified'


def test_rerun_is_deterministic_with_same_input(monkeypatch):
    _patch_ffmpeg(monkeypatch)
    asr = MockAsrEngine(script='东湖花园 160㎡ 365万')
    ocr = MockOcrEngine(text_map={0: '总价：365万'})
    first = run_pipeline('/tmp/in.mp4', asr_engine=asr, ocr_engine=ocr)
    second = run_pipeline('/tmp/in.mp4', asr_engine=asr, ocr_engine=ocr)
    assert first.as_dict()['media_sha256'] == second.as_dict()['media_sha256']
    assert first.as_dict()['hints'] == second.as_dict()['hints']
    assert first.as_dict()['transcript'] == second.as_dict()['transcript']


def test_pipeline_cleans_private_work_dir_after_processing_failure(monkeypatch, tmp_path):
    _patch_ffmpeg(monkeypatch)
    created = []
    real_mkdtemp = tempfile.mkdtemp

    def make_temp(**kwargs):
        path = real_mkdtemp(dir=tmp_path, **kwargs)
        created.append(path)
        return path

    monkeypatch.setattr(tempfile, 'mkdtemp', make_temp)
    monkeypatch.setattr(ffmpeg_tools, 'probe_media',
                        lambda *a, **kw: (_ for _ in ()).throw(MediaPipelineError('ffmpeg_timeout', 'timeout')))
    with pytest.raises(MediaPipelineError):
        run_pipeline('/tmp/in.mp4', asr_engine=MockAsrEngine(script='x'), ocr_engine=MockOcrEngine())
    assert len(created) == 1
    assert not Path(created[0]).exists()


def test_keep_work_retains_work_dir(monkeypatch, tmp_path):
    _patch_ffmpeg(monkeypatch)
    work = tmp_path / 'keep'
    evidence = run_pipeline('/tmp/in.mp4', asr_engine=MockAsrEngine(script='x'),
                            ocr_engine=MockOcrEngine(), work_dir=work, keep_work=True)
    assert evidence.work_dir == str(work)
    assert work.is_dir()
    assert work.stat().st_mode & 0o777 == 0o700


def test_work_dir_must_be_new_and_empty(monkeypatch, tmp_path):
    work = tmp_path / 'existing'
    work.mkdir()
    with pytest.raises(MediaPipelineError) as err:
        run_pipeline('/tmp/in.mp4', work_dir=work,
                     asr_engine=MockAsrEngine(script='x'), ocr_engine=MockOcrEngine())
    assert err.value.kind == 'invalid_input'


def test_pipeline_lock_rejects_concurrent_media_job(monkeypatch, tmp_path):
    from app.media_pipeline import pipeline

    monkeypatch.setattr(pipeline, 'PIPELINE_LOCK_PATH', tmp_path / 'media.lock')
    with pipeline._exclusive_pipeline_lock():
        with pytest.raises(MediaPipelineError) as err:
            run_pipeline('/tmp/in.mp4', asr_engine=MockAsrEngine(script='x'),
                         ocr_engine=MockOcrEngine())
    assert err.value.kind == 'media_busy'


def test_invalid_input_raises_before_processing(monkeypatch):
    monkeypatch.setattr(ffmpeg_tools, 'validate_input',
                        lambda path: (_ for _ in ()).throw(
                            MediaPipelineError('unsupported_format', 'unsupported extension .txt')))
    with pytest.raises(MediaPipelineError) as err:
        run_pipeline('/tmp/in.txt', asr_engine=MockAsrEngine(script='x'),
                     ocr_engine=MockOcrEngine())
    assert err.value.kind == 'unsupported_format'


def test_evidence_as_dict_is_json_serializable(monkeypatch):
    _patch_ffmpeg(monkeypatch)
    evidence = run_pipeline('/tmp/in.mp4', asr_engine=MockAsrEngine(script='160㎡'),
                            ocr_engine=MockOcrEngine(text_map={0: '365万'}))
    payload = evidence.as_dict()
    json.dumps(payload, ensure_ascii=False)
    assert payload['media_sha256'] == 'sha256x'
    assert payload['ocr']['items'][0]['text'] == '365万'
