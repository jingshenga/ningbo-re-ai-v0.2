"""Orchestrates one local media file into transcript/OCR evidence and field hints.

Single-job by design: one input at a time, isolated temp directory, cleanup
on exit (keep_work opt-in for operator inspection). ASR/OCR engine failures
degrade to explicit statuses — an unavailable model never produces content
and mock output is always labeled as such.
"""
from __future__ import annotations

import shutil
import tempfile
import time
from pathlib import Path

from app.extractor import extract_hints
from app.media_pipeline import ffmpeg_tools
from app.media_pipeline.errors import MediaPipelineError
from app.media_pipeline.models import (KeyFrame, MediaEvidence, MediaInfo,
                                       OcrResult, PipelineRun, TranscriptResult)


def _empty_transcript(status: str, error: str) -> TranscriptResult:
    return TranscriptResult(status=status, engine='none', error=error)


def run_pipeline(path: str | Path, *,
                 asr_engine=None,
                 ocr_engine=None,
                 work_dir: str | Path | None = None,
                 keep_work: bool = False,
                 known_community_names: list[str] | None = None) -> MediaEvidence:
    """Run the full local chain: validate → probe → audio → frames → ASR/OCR → hints.

    `work_dir`, when given, must be an existing empty directory the operator
    controls; otherwise an isolated temp directory is created and removed.
    """
    started = time.monotonic()
    source = ffmpeg_tools.validate_input(Path(path))
    own_work_dir = work_dir is None
    work = Path(work_dir) if work_dir is not None else Path(
        tempfile.mkdtemp(prefix='nbre-media-'))
    if own_work_dir:
        work.mkdir(parents=True, exist_ok=True)
    if not work.is_dir() or work.is_symlink():
        raise MediaPipelineError('invalid_input', 'work directory must be a real directory')
    # FFmpeg uses fixed output names; an existing file/symlink must never be
    # overwritten by an operator-provided --keep-work path.
    if any(work.iterdir()):
        raise MediaPipelineError('invalid_input', 'work directory must be empty')
    try:
        sha256, size_bytes = ffmpeg_tools.prepare_input(source, work)
        probe = ffmpeg_tools.probe_media(work, size_bytes)
        media = MediaInfo(sha256=sha256, **probe)

        warnings: list[str] = []
        if not media.has_audio:
            warnings.append('media has no audio stream; transcript marked no_audio')

        # Audio → ASR
        transcript: TranscriptResult | None = None
        audio_path: Path | None = None
        if media.has_audio:
            try:
                audio_path = ffmpeg_tools.extract_audio(work)
            except MediaPipelineError as exc:
                transcript = _empty_transcript('failed', 'audio extraction failed: ' + exc.kind)
                warnings.append(transcript.error)
            if transcript is None and audio_path is not None:
                if asr_engine is None:
                    transcript = _empty_transcript('unavailable', 'no ASR engine configured')
                    warnings.append(transcript.error)
                else:
                    transcript = asr_engine.transcribe(audio_path)
                    if transcript.status == 'no_audio' or (transcript.status == 'ok' and not transcript.text):
                        transcript = TranscriptResult(
                            status='no_audio', engine=transcript.engine,
                            model_name=transcript.model_name, model_version=transcript.model_version,
                            error='no recognizable speech in audio')
                    if transcript.status in ('unavailable', 'failed'):
                        warnings.append(transcript.error or transcript.status)
                    if transcript.engine == 'mock':
                        warnings.append('ASR used the mock/manual engine; this is not a real transcription')
        if transcript is None:
            transcript = _empty_transcript(
                'no_audio', 'media has no audio stream' if not media.has_audio else 'audio extraction produced no audio')

        # Keyframes → OCR
        frames: list[KeyFrame] = []
        ocr: OcrResult | None = None
        try:
            frames = ffmpeg_tools.extract_keyframes(work)
        except MediaPipelineError as exc:
            ocr = OcrResult(status='failed', error='frame extraction failed: ' + exc.kind)
            warnings.append(ocr.error)
        if ocr is None:
            if not frames:
                ocr = OcrResult(status='no_frames', error='no frames extracted')
                warnings.append(ocr.error)
            elif ocr_engine is None:
                ocr = OcrResult(status='unavailable', error='no OCR engine configured')
                warnings.append(ocr.error)
            else:
                ocr = ocr_engine.recognize(frames)
                if ocr.status in ('unavailable', 'failed'):
                    warnings.append(ocr.error or ocr.status)
                if ocr.engine == 'mock':
                    warnings.append('OCR used the mock engine; this is not real screen recognition')
        elif ocr.status in ('failed', 'no_frames'):
            warnings.append(ocr.error or ocr.status)

        ocr_text = '\n'.join(item.text for item in ocr.items)
        transcript_text = transcript.text or ''
        hints = extract_hints(
            ocr_text or None, transcript_text or None,
            source_labels=['ocr_text', 'transcript'],
            known_community_names=known_community_names,
        )
        return MediaEvidence(
            media=media, transcript=transcript, ocr=ocr, hints=hints,
            warnings=tuple(dict.fromkeys(warnings)),
            work_dir=str(work) if keep_work else None,
            elapsed_seconds=round(time.monotonic() - started, 3),
        )
    finally:
        if own_work_dir and not keep_work:
            shutil.rmtree(work, ignore_errors=True)
