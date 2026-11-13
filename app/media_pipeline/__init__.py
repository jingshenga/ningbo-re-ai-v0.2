"""Local media pipeline: FFmpeg → ASR/OCR → field hints → video enrichment.

Public surface:
- run_pipeline(...) → MediaEvidence (offline closed loop, engine-agnostic)
- build_asr_engine / build_ocr_engine (mock | funasr | rapidocr | auto)
- submit_enrichment(...) (bounded PATCH to the existing enrichment endpoint)
- MediaPipelineError with stable `kind` codes for CLI exit mapping
"""
from app.media_pipeline.asr import (FunasrEngine, MockAsrEngine,
                                    UnavailableAsrEngine, build_asr_engine)
from app.media_pipeline.enrich_api import submit_enrichment
from app.media_pipeline.errors import MediaPipelineError
from app.media_pipeline.models import (KeyFrame, MediaEvidence, MediaInfo,
                                       OcrItem, OcrResult, TranscriptResult)
from app.media_pipeline.ocr import (MockOcrEngine, RapidOcrEngine,
                                    build_ocr_engine)
from app.media_pipeline.pipeline import run_pipeline

__all__ = [
    'FunasrEngine', 'MockAsrEngine', 'UnavailableAsrEngine', 'build_asr_engine',
    'MockOcrEngine', 'RapidOcrEngine', 'build_ocr_engine',
    'submit_enrichment', 'run_pipeline', 'MediaPipelineError',
    'KeyFrame', 'MediaEvidence', 'MediaInfo', 'OcrItem', 'OcrResult',
    'TranscriptResult',
]
