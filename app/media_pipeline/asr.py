"""Pluggable ASR adapters: deterministic mock/manual transcript and optional FunASR.

`MockAsrEngine` is the offline contract path and also the operator-supplied
manual-transcript path; it is always labeled `engine='mock'` so mock output
can never be mistaken for a real transcription. `FunasrEngine` lazy-loads the
real model: any import or runtime failure is reported as `unavailable`, never
as a successful transcript.
"""
from __future__ import annotations

import os
from pathlib import Path

from app.media_pipeline.models import TranscriptResult

DEFAULT_FUNASR_MODEL = 'paraformer-zh'


def _read_text_file(path: str) -> str:
    try:
        return Path(path).read_text(encoding='utf-8').strip()
    except OSError as exc:
        raise ValueError('cannot read transcript file: ' + type(exc).__name__) from exc


class MockAsrEngine:
    """Deterministic engine for tests and operator-supplied manual transcripts."""

    engine = 'mock'

    def __init__(self, script: str | None = None, script_file: str | None = None,
                 model_name: str = 'manual_transcript'):
        if script is not None and script_file is not None:
            raise ValueError('provide either script or script_file, not both')
        if script_file is not None:
            script = _read_text_file(script_file)
        self.script = script if script is not None else ''
        self.model_name = model_name

    def transcribe(self, audio_path: Path) -> TranscriptResult:
        return TranscriptResult(
            status='ok', text=self.script, engine=self.engine,
            model_name=self.model_name, model_version='mock-fixed',
        )


class UnavailableAsrEngine:
    """Explicitly-unavailable engine: honest failure instead of empty content."""

    engine = 'none'

    def transcribe(self, audio_path: Path) -> TranscriptResult:
        return TranscriptResult(
            status='unavailable', engine=self.engine,
            error='no ASR engine available; install funasr or provide --asr-script',
        )


class FunasrEngine:
    """FunASR wrapper; import and model load happen on first use.

    FunASR is the preferred real ASR engine, but it is optional: without the
    package or the model files the adapter reports `unavailable` with the
    reason instead of failing the whole pipeline.
    """

    engine = 'funasr'

    def __init__(self, model: str | None = None):
        self.model = model or os.environ.get('FUNASR_MODEL') or DEFAULT_FUNASR_MODEL
        self._loaded = None

    def _ensure_loaded(self) -> 'object':  # noqa: F821 - runtime optional dependency
        if self._loaded is not None:
            return self._loaded
        model_path = Path(self.model).expanduser()
        if not model_path.is_dir():
            raise RuntimeError('FunASR model must be preinstalled as a local directory')
        try:
            from funasr import AutoModel  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError('funasr is not installed: ' + type(exc).__name__) from exc
        self._loaded = AutoModel(model=str(model_path.resolve()))
        return self._loaded

    def transcribe(self, audio_path: Path) -> TranscriptResult:
        try:
            model = self._ensure_loaded()
            output = model.generate(input=str(audio_path))
            text = ' '.join(
                str(item.get('text', ''))
                for item in (output or [])
                if isinstance(item, dict) and item.get('text')
            ).strip()
            return TranscriptResult(
                status='ok', text=text or None, engine=self.engine,
                model_name=self.model,
                model_version=os.environ.get('FUNASR_MODEL_VERSION'),
            )
        except (ImportError, RuntimeError, OSError, ValueError) as exc:
            return TranscriptResult(
                status='unavailable', engine=self.engine, model_name=self.model,
                error='asr engine unavailable: ' + type(exc).__name__,
            )
        except Exception as exc:  # noqa: BLE001 - model errors must never kill the job
            return TranscriptResult(
                status='failed', engine=self.engine, model_name=self.model,
                error='asr failed: ' + type(exc).__name__,
            )


def build_asr_engine(engine: str | None, script: str | None = None,
                     script_file: str | None = None) -> object:
    """Resolve `auto`/`mock`/`funasr` to an engine instance for the CLI."""
    if engine == 'mock':
        return MockAsrEngine(script=script, script_file=script_file)
    if engine == 'funasr':
        return FunasrEngine()
    if engine in (None, 'auto'):
        if _funasr_available():
            return FunasrEngine()
        if script is not None or script_file is not None:
            return MockAsrEngine(script=script, script_file=script_file)
        return UnavailableAsrEngine()
    raise ValueError('unknown asr engine: ' + str(engine))


def _funasr_available() -> bool:
    try:
        import importlib.util
        return importlib.util.find_spec('funasr') is not None
    except (ImportError, ValueError):
        return False
