"""Pluggable OCR adapters: deterministic mock and optional RapidOCR.

Every OCR item keeps its source frame (index, path, timestamp), so screen
text stays traceable to the exact frame it came from. `MockOcrEngine` is the
offline contract path; `RapidOcrEngine` lazy-loads the real runtime and
reports `unavailable` instead of fabricating results.
"""
from __future__ import annotations

import os

from app.media_pipeline.models import KeyFrame, OcrItem, OcrResult


class MockOcrEngine:
    """Deterministic engine for tests; text_map keys are frame indices."""

    engine = 'mock'

    def __init__(self, text_map: dict[int, str] | None = None,
                 default_text: str | None = None):
        self.text_map = dict(text_map or {})
        self.default_text = default_text or ''

    def recognize(self, frames: list[KeyFrame]) -> OcrResult:
        items = []
        for frame in frames:
            text = self.text_map.get(frame.index, self.default_text)
            if text:
                items.append(OcrItem(
                    text=text, frame_index=frame.index, frame_path=frame.path,
                    timestamp_seconds=frame.timestamp_seconds, confidence=1.0,
                ))
        return OcrResult(
            status='ok', items=tuple(items), engine=self.engine,
            model_name='mock_ocr', model_version='mock-fixed',
        )


class UnavailableOcrEngine:
    """No real OCR dependency and no supplied manual text; never claim success."""

    engine = 'none'

    def recognize(self, frames: list[KeyFrame]) -> OcrResult:
        return OcrResult(status='unavailable', engine=self.engine,
                         error='no OCR engine available; install RapidOCR or provide --ocr-text')


class RapidOcrEngine:
    """RapidOCR (onnxruntime) wrapper; optional dependency, lazy loaded."""

    engine = 'rapidocr'

    def __init__(self):
        self._engine = None

    def _ensure_loaded(self) -> 'object':  # noqa: F821 - runtime optional dependency
        if self._engine is not None:
            return self._engine
        try:
            from rapidocr_onnxruntime import RapidOCR  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError('rapidocr-onnxruntime is not installed: ' + type(exc).__name__) from exc
        self._engine = RapidOCR()
        return self._engine

    def recognize(self, frames: list[KeyFrame]) -> OcrResult:
        try:
            engine = self._ensure_loaded()
        except (ImportError, RuntimeError, OSError) as exc:
            return OcrResult(
                status='unavailable', engine=self.engine,
                error='ocr engine unavailable: ' + type(exc).__name__,
            )
        items = []
        try:
            for frame in frames:
                result = engine(frame.path)
                # rapidocr_onnxruntime returns (rows, elapse); older builds may
                # return rows directly. Unpack defensively — never stringify a
                # whole row or leak elapse timings as text.
                if isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], list):
                    result = result[0]
                for line in result or []:
                    if not isinstance(line, (list, tuple)) or len(line) < 2:
                        continue
                    text = line[1]
                    if not isinstance(text, str):
                        continue
                    text = text.strip()
                    if not text:
                        continue
                    confidence = None
                    if len(line) > 2:
                        try:
                            confidence = float(line[2])
                        except (TypeError, ValueError):
                            confidence = None
                    items.append(OcrItem(
                        text=text, frame_index=frame.index, frame_path=frame.path,
                        timestamp_seconds=frame.timestamp_seconds, confidence=confidence,
                    ))
        except Exception as exc:  # noqa: BLE001 - model errors must never kill the job
            return OcrResult(
                status='failed', items=tuple(items), engine=self.engine,
                model_name='rapidocr-onnxruntime',
                model_version=os.environ.get('RAPIDOCR_MODEL_VERSION'),
                error='ocr failed: ' + type(exc).__name__,
            )
        return OcrResult(
            status='ok', items=tuple(items), engine=self.engine,
            model_name='rapidocr-onnxruntime',
            model_version=os.environ.get('RAPIDOCR_MODEL_VERSION'),
        )


def build_ocr_engine(engine: str | None, text_map: dict[int, str] | None = None,
                     default_text: str | None = None) -> object:
    """Resolve `auto`/`mock`/`rapidocr` to an engine instance for the CLI."""
    if engine == 'mock':
        return MockOcrEngine(text_map=text_map, default_text=default_text)
    if engine == 'rapidocr':
        return RapidOcrEngine()
    if engine in (None, 'auto'):
        if _rapidocr_available():
            return RapidOcrEngine()
        if text_map or default_text:
            return MockOcrEngine(text_map=text_map, default_text=default_text)
        return UnavailableOcrEngine()
    raise ValueError('unknown ocr engine: ' + str(engine))


def _rapidocr_available() -> bool:
    try:
        import importlib.util
        return importlib.util.find_spec('rapidocr_onnxruntime') is not None
    except (ImportError, ValueError):
        return False
