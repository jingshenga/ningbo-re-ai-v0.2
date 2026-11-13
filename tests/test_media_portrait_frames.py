"""Regression checks for bounded portrait OCR frames.

Real geometry tests use only synthetic local lavfi inputs and never fetch
third-party media. The production scale literal is asserted independently.
"""
import shutil
import subprocess

import pytest

from app.media_pipeline import limits


SCALE = 'scale=1280:720:force_original_aspect_ratio=decrease:force_divisible_by=2'


def test_all_cadences_and_long_video_filters_are_bounded():
    assert limits.FRAME_SCALE_FILTER == SCALE
    for interval in limits.ALLOWED_KEYFRAME_INTERVALS:
        key = format(interval, 'g')
        assert limits.INTERVAL_FILTERS[key].endswith(',' + SCALE)
        assert 'scale=1280:-2' not in limits.INTERVAL_FILTERS[key]
    assert limits.sampling_filter(8.0).endswith(',' + SCALE)
    assert limits.sampling_filter(1200.0).endswith(',' + SCALE)
    assert 'scale=1280:-2' not in limits.sampling_filter(1200.0)


@pytest.mark.skipif(
    not shutil.which('ffmpeg') or not shutil.which('ffprobe'),
    reason='requires real ffmpeg and ffprobe',
)
def test_real_ffmpeg_portrait_is_not_upscaled(tmp_path):
    # All argv elements are fixed literals; only cwd is a test temp directory.
    subprocess.run(
        ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'lavfi',
         '-i', 'color=c=black:s=720x1280:r=1',
         '-vf', 'scale=1280:720:force_original_aspect_ratio=decrease:force_divisible_by=2',
         '-frames:v', '1', '-y', 'scaled.jpg'],
        shell=False, cwd=str(tmp_path), capture_output=True, text=True,
        check=True, timeout=30,
    )
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
         '-show_entries', 'stream=width,height', '-of', 'csv=p=0', 'scaled.jpg'],
        shell=False, cwd=str(tmp_path), capture_output=True, text=True,
        check=True, timeout=10,
    )
    assert result.stdout.strip() == '406,720'


@pytest.mark.skipif(
    not shutil.which('ffmpeg') or not shutil.which('ffprobe'),
    reason='requires real ffmpeg and ffprobe',
)
def test_real_ffmpeg_landscape_is_bounded(tmp_path):
    subprocess.run(
        ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'lavfi',
         '-i', 'color=c=black:s=1920x1080:r=1',
         '-vf', 'scale=1280:720:force_original_aspect_ratio=decrease:force_divisible_by=2',
         '-frames:v', '1', '-y', 'scaled.jpg'],
        shell=False, cwd=str(tmp_path), capture_output=True, text=True,
        check=True, timeout=30,
    )
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
         '-show_entries', 'stream=width,height', '-of', 'csv=p=0', 'scaled.jpg'],
        shell=False, cwd=str(tmp_path), capture_output=True, text=True,
        check=True, timeout=10,
    )
    assert result.stdout.strip() == '1280,720'
