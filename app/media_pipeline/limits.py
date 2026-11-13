"""Processing limits for the DXP4800 (Intel N100, 16 GB RAM): one media job at a time.

Bounds are Python-side checks. FFmpeg filter values are generated only from
validated media duration and these fixed limits, never operator text.
"""
from __future__ import annotations

import os

SUPPORTED_EXTENSIONS = frozenset((
    '.mp4', '.mov', '.mkv', '.m4v', '.webm', '.avi', '.flv', '.ts',
    '.mpg', '.mpeg', '.3gp',
))

DEFAULT_MAX_INPUT_BYTES = 1024 * 1024 * 1024        # 1 GiB per input file
DEFAULT_MAX_DURATION_SECONDS = 1800.0               # 30 minutes
DEFAULT_MIN_DURATION_SECONDS = 0.5                  # reject empty/stub media
DEFAULT_KEYFRAME_INTERVAL_SECONDS = 2.0             # one sampled frame every N seconds
ALLOWED_KEYFRAME_INTERVALS = (1, 2, 3, 5, 10)       # argv filter must come from this set
MAX_KEYFRAMES = 12                                  # fixed cap; bounds OCR work per video
AUDIO_SAMPLE_RATE = 16000                           # mono PCM for ASR
FFMPEG_TIMEOUT_SECONDS = 120.0                      # per ffmpeg invocation (Python-side)

# Interval filters are literal argv elements; timestamp math uses the
# matching numeric value, so both stay in lockstep.
INTERVAL_FILTERS = {
    '1': 'fps=1,scale=1280:-2',
    '2': 'fps=1/2,scale=1280:-2',
    '3': 'fps=1/3,scale=1280:-2',
    '5': 'fps=1/5,scale=1280:-2',
    '10': 'fps=1/10,scale=1280:-2',
}


def _read_env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == '':
        return default
    try:
        value = float(raw.strip())
    except ValueError:
        return default
    return value if value > 0 else default


def _read_env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == '':
        return default
    try:
        value = int(raw.strip())
    except ValueError:
        return default
    return value if value > 0 else default


MAX_INPUT_BYTES = _read_env_int('NBRE_MEDIA_MAX_BYTES', DEFAULT_MAX_INPUT_BYTES)
MAX_DURATION_SECONDS = _read_env_float('NBRE_MEDIA_MAX_DURATION_SECONDS',
                                       DEFAULT_MAX_DURATION_SECONDS)
MIN_DURATION_SECONDS = DEFAULT_MIN_DURATION_SECONDS
_keyframe_raw = _read_env_float('NBRE_MEDIA_KEYFRAME_INTERVAL_SECONDS',
                                DEFAULT_KEYFRAME_INTERVAL_SECONDS)
KEYFRAME_INTERVAL_SECONDS = (_keyframe_raw if _keyframe_raw in ALLOWED_KEYFRAME_INTERVALS
                             else DEFAULT_KEYFRAME_INTERVAL_SECONDS)


def interval_filter() -> str:
    return INTERVAL_FILTERS[format(KEYFRAME_INTERVAL_SECONDS, 'g')]


def sampling_filter(duration_seconds: float) -> str:
    """Keep short-video cadence and spread the capped samples across long videos."""
    interval = sampling_interval(duration_seconds)
    if interval == KEYFRAME_INTERVAL_SECONDS:
        return interval_filter()
    return 'fps=1/' + format(interval, '.6g') + ',scale=1280:-2'


def sampling_interval(duration_seconds: float) -> float:
    if duration_seconds <= MAX_KEYFRAMES * KEYFRAME_INTERVAL_SECONDS:
        return KEYFRAME_INTERVAL_SECONDS
    return (duration_seconds - KEYFRAME_INTERVAL_SECONDS) / (MAX_KEYFRAMES - 1)
