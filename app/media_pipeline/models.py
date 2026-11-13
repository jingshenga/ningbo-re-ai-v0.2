"""Structured evidence dataclasses for the local media pipeline.

Status values are explicit so that missing models or empty media can never be
read as complete content: ASR/OCR always carry a `status` field and, when the
engine could not run, an `error` reason with the mock/real provenance.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MediaInfo:
    sha256: str
    size_bytes: int
    duration_seconds: float
    format_name: str
    has_audio: bool
    width: int | None = None
    height: int | None = None


@dataclass(frozen=True)
class KeyFrame:
    path: str
    index: int
    timestamp_seconds: float
    source: str  # 'interval'


@dataclass(frozen=True)
class TranscriptResult:
    status: str  # 'ok' | 'no_audio' | 'unavailable' | 'failed'
    text: str | None = None
    engine: str = 'none'
    model_name: str | None = None
    model_version: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class OcrItem:
    text: str
    frame_index: int
    frame_path: str
    timestamp_seconds: float
    confidence: float | None = None


@dataclass(frozen=True)
class OcrResult:
    status: str  # 'ok' | 'no_frames' | 'unavailable' | 'failed'
    items: tuple[OcrItem, ...] = ()
    engine: str = 'none'
    model_name: str | None = None
    model_version: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class MediaEvidence:
    media: MediaInfo
    transcript: TranscriptResult
    ocr: OcrResult
    hints: dict
    warnings: tuple[str, ...] = ()
    work_dir: str | None = None
    elapsed_seconds: float = 0.0

    def as_dict(self) -> dict:
        """JSON-serializable summary; frame provenance preserved per OCR item."""
        return {
            'media_sha256': self.media.sha256,
            'media': {
                'size_bytes': self.media.size_bytes,
                'duration_seconds': self.media.duration_seconds,
                'format_name': self.media.format_name,
                'has_audio': self.media.has_audio,
                'width': self.media.width,
                'height': self.media.height,
            },
            'transcript': {
                'status': self.transcript.status,
                'text': self.transcript.text,
                'engine': self.transcript.engine,
                'model_name': self.transcript.model_name,
                'model_version': self.transcript.model_version,
                'error': self.transcript.error,
            },
            'ocr': {
                'status': self.ocr.status,
                'engine': self.ocr.engine,
                'model_name': self.ocr.model_name,
                'model_version': self.ocr.model_version,
                'error': self.ocr.error,
                'items': [
                    {
                        'text': item.text,
                        'frame_index': item.frame_index,
                        'timestamp_seconds': item.timestamp_seconds,
                        'confidence': item.confidence,
                        'frame_path': item.frame_path,
                    } for item in self.ocr.items
                ],
            },
            'hints': self.hints,
            'warnings': list(self.warnings),
            'elapsed_seconds': self.elapsed_seconds,
            'evidence_note': ('口播/OCR文字仅为线索，不得自动当作平台挂牌价或成交价；'
                              '见 hints.warning 与 confidence_status。'),
        }


@dataclass
class PipelineRun:
    """Mutable working state passed between pipeline steps (not serialized directly)."""
    work_dir: str
    media: MediaInfo
    audio_path: str | None = None
    frames: list[KeyFrame] = field(default_factory=list)
    transcript: TranscriptResult = field(
        default_factory=lambda: TranscriptResult(status='unavailable', error='not started'))
    ocr: OcrResult = field(default_factory=lambda: OcrResult(status='unavailable', error='not started'))
    warnings: list[str] = field(default_factory=list)
