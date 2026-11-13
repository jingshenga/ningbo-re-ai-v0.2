"""Engine adapter tests: deterministic mocks, honest unavailable states, provenance labels."""
from __future__ import annotations

import builtins
from pathlib import Path

import pytest

from app.media_pipeline.asr import (FunasrEngine, MockAsrEngine,
                                    UnavailableAsrEngine, build_asr_engine)
from app.media_pipeline.models import KeyFrame
from app.media_pipeline.ocr import MockOcrEngine, RapidOcrEngine, build_ocr_engine


def test_mock_asr_returns_fixed_script_and_mock_label():
    engine = MockAsrEngine(script='东湖花园 160㎡ 四室两厅 报价365万')
    result = engine.transcribe(Path('/tmp/audio.wav'))
    assert result.status == 'ok'
    assert '东湖花园' in (result.text or '')
    assert result.engine == 'mock'


def test_mock_asr_reads_script_file(tmp_path):
    script = tmp_path / 'transcript.txt'
    script.write_text('手动逐字稿：建筑面积160平方米\n', encoding='utf-8')
    result = MockAsrEngine(script_file=str(script)).transcribe(Path('/tmp/audio.wav'))
    assert '160' in (result.text or '')


def test_mock_asr_rejects_script_and_file_together():
    import pytest
    with pytest.raises(ValueError):
        MockAsrEngine(script='x', script_file='y')


def test_unavailable_asr_is_explicitly_unavailable():
    result = UnavailableAsrEngine().transcribe(Path('/tmp/audio.wav'))
    assert result.status == 'unavailable'
    assert result.text is None
    assert 'no ASR engine available' in (result.error or '')


def test_funasr_engine_reports_unavailable_without_package(tmp_path, monkeypatch):
    model = tmp_path / 'local-model'
    model.mkdir()
    original_import = builtins.__import__

    def import_without_funasr(name, *args, **kwargs):
        if name == 'funasr':
            raise ModuleNotFoundError("No module named 'funasr'")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', import_without_funasr)
    engine = FunasrEngine(model=str(model))
    result = engine.transcribe(tmp_path / 'audio.wav')
    assert result.status == 'unavailable'
    assert result.engine == 'funasr'
    assert result.model_name == str(model)


def test_funasr_refuses_to_download_missing_model(monkeypatch, tmp_path):
    imported = []
    original_import = builtins.__import__

    def track_import(name, *args, **kwargs):
        imported.append(name)
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', track_import)
    result = FunasrEngine(model=str(tmp_path / 'not-installed')).transcribe(
        tmp_path / 'audio.wav')
    assert result.status == 'unavailable'
    assert not any(name == 'funasr' for name in imported)


def test_build_asr_engine_auto_falls_back_to_mock_with_script(monkeypatch):
    monkeypatch.setattr('app.media_pipeline.asr._funasr_available', lambda: False)
    engine = build_asr_engine('auto', script='口播稿')
    assert engine.engine == 'mock'
    assert engine.transcribe(Path('/tmp/a.wav')).status == 'ok'


def test_build_asr_engine_auto_without_script_is_unavailable(monkeypatch):
    monkeypatch.setattr('app.media_pipeline.asr._funasr_available', lambda: False)
    engine = build_asr_engine('auto')
    assert engine.transcribe(Path('/tmp/a.wav')).status == 'unavailable'


def test_mock_ocr_keeps_frame_provenance():
    frames = [
        KeyFrame(path='/tmp/f0.jpg', index=0, timestamp_seconds=0.0, source='interval'),
        KeyFrame(path='/tmp/f1.jpg', index=1, timestamp_seconds=2.0, source='interval'),
    ]
    engine = MockOcrEngine(text_map={0: '小区：东湖花园 总价：365万'})
    result = engine.recognize(frames)
    assert result.status == 'ok'
    assert len(result.items) == 1
    item = result.items[0]
    assert item.frame_index == 0 and item.frame_path == '/tmp/f0.jpg'
    assert item.timestamp_seconds == 0.0


def test_mock_ocr_empty_when_no_text():
    result = MockOcrEngine().recognize([])
    assert result.status == 'ok'
    assert result.items == ()


def test_rapidocr_engine_reports_unavailable_without_package(monkeypatch):
    original_import = builtins.__import__

    def import_without_rapidocr(name, *args, **kwargs):
        if name == 'rapidocr_onnxruntime':
            raise ModuleNotFoundError("No module named 'rapidocr_onnxruntime'")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', import_without_rapidocr)
    engine = RapidOcrEngine()
    result = engine.recognize([])
    assert result.status == 'unavailable'
    assert 'rapidocr' in result.engine


def test_rapidocr_engine_parses_tuple_result_and_frame_provenance(monkeypatch):
    """Real-run contract: rapidocr_onnxruntime returns (rows, elapse) and each
    row is [box, text, confidence]; text must not be stringified as a whole row."""
    from app.media_pipeline.models import KeyFrame

    class FakeRapidOcr:
        def __call__(self, image_path):
            return (
                [
                    [[[104, 269], [458, 272], [457, 338], [103, 334]], '小区：东湖花园', 0.99947],
                    [[[104, 419], [458, 422], [457, 488], [103, 484]], '总价：365万', 0.99961],
                ],
                [0.0016, 0.0001, 0.0411],  # elapse list, must never become items
            )

    engine = RapidOcrEngine()
    monkeypatch.setattr(engine, '_ensure_loaded', lambda: FakeRapidOcr())
    frames = [KeyFrame(path='/tmp/f0.jpg', index=0, timestamp_seconds=0.0, source='interval')]
    result = engine.recognize(frames)

    assert result.status == 'ok'
    assert result.engine == 'rapidocr'
    texts = [item.text for item in result.items]
    assert texts == ['小区：东湖花园', '总价：365万']
    assert not any('[[[' in text for text in texts), 'row repr leaked into OCR text'
    assert not any(item.text.startswith('0.0') for item in result.items), 'elapse leaked into OCR items'
    assert result.items[0].confidence == pytest.approx(0.99947, abs=1e-5)
    assert result.items[0].frame_index == 0
    assert result.items[0].timestamp_seconds == 0.0


def test_build_ocr_engine_auto_falls_back_to_mock(monkeypatch):
    monkeypatch.setattr('app.media_pipeline.ocr._rapidocr_available', lambda: False)
    engine = build_ocr_engine('auto')
    assert engine.engine == 'mock'
