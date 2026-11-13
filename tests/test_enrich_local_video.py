"""CLI tests: dry-run output, submit path, host policy, exit codes, key hygiene."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from app.media_pipeline.errors import MediaPipelineError
from app.media_pipeline.models import MediaEvidence, MediaInfo, OcrResult, TranscriptResult

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / 'scripts'


def _load_cli():
    spec = importlib.util.spec_from_file_location(
        'enrich_local_video', SCRIPTS_DIR / 'enrich_local_video.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _evidence() -> MediaEvidence:
    return MediaEvidence(
        media=MediaInfo(sha256='abc123', size_bytes=10, duration_seconds=6.0,
                        format_name='mov', has_audio=True),
        transcript=TranscriptResult(status='ok', text='报价365万', engine='mock'),
        ocr=OcrResult(status='ok', items=(), engine='mock'),
        hints={'method': 'rule_based_hints_not_verified', 'price_mentions_wan': [365.0]},
        warnings=('ASR used the mock/manual engine; this is not a real transcription',),
    )


@pytest.fixture()
def cli():
    return _load_cli()


def _run_cli(cli, monkeypatch, argv, evidence=None):
    """Monkeypatch the script's own imported names, then run main()."""
    monkeypatch.setattr(cli, 'run_pipeline', lambda *a, **kw: evidence or _evidence())
    captured = {}

    def fake_submit(**kwargs):
        captured.update(kwargs)
        return {'video_id': kwargs['video_id'], 'processing_status': 'enriched'}

    monkeypatch.setattr(cli, 'submit_enrichment', fake_submit)
    return captured


def test_dry_run_prints_evidence_json(cli, monkeypatch, capsys):
    _run_cli(cli, monkeypatch, ['/tmp/x.mp4'])
    code = cli.main(['/tmp/x.mp4'])
    out = capsys.readouterr().out
    assert code == cli.EXIT_OK
    payload = json.loads(out)
    assert payload['ok'] is True
    assert payload['submitted'] is False
    assert payload['media_sha256'] == 'abc123'
    assert payload['transcript']['engine'] == 'mock'


def test_dry_run_requires_no_api_key(cli, monkeypatch, capsys, tmp_path):
    _run_cli(cli, monkeypatch, [str(tmp_path / 'x.mp4')])
    code = cli.main([str(tmp_path / 'x.mp4')])
    assert code == cli.EXIT_OK
    assert capsys.readouterr().out.strip()


def test_submit_requires_video_id(cli, monkeypatch, capsys):
    code = cli.main(['/tmp/x.mp4', '--submit'])
    assert code == cli.EXIT_INVALID
    assert '--submit requires --video-id' in capsys.readouterr().err


def test_submit_requires_api_key(cli, monkeypatch, capsys):
    _run_cli(cli, monkeypatch, ['/tmp/x.mp4', '--submit', '--video-id', 'v-1'])
    code = cli.main(['/tmp/x.mp4', '--submit', '--video-id', 'v-1'])
    assert code == cli.EXIT_SUBMIT
    assert 'APP_API_KEY' in capsys.readouterr().err


def test_submit_sends_transcript_and_ocr_text(cli, monkeypatch, capsys):
    captured = _run_cli(cli, monkeypatch, ['/tmp/x.mp4'])
    monkeypatch.setenv('APP_API_KEY', 'secret-key')
    code = cli.main(['/tmp/x.mp4', '--submit', '--video-id', 'v-1'])
    out = capsys.readouterr().out
    assert code == cli.EXIT_OK
    assert captured['video_id'] == 'v-1'
    assert captured['transcript'] == '报价365万'
    payload = json.loads(out)
    assert payload['submitted'] is True
    # the key must never leak into stdout/stderr/JSON
    assert 'secret-key' not in out


def test_submit_private_network_requires_opt_in(cli, monkeypatch, capsys):
    _run_cli(cli, monkeypatch, ['/tmp/x.mp4'])
    monkeypatch.setenv('APP_API_KEY', 'secret-key')

    def deny(**kwargs):
        raise MediaPipelineError(
            'invalid_api_url',
            'API target is a private/LAN or unresolvable-host address; '
            'pass --allow-private-network to accept this operator-controlled target')

    monkeypatch.setattr(cli, 'submit_enrichment', deny)
    code = cli.main(['/tmp/x.mp4', '--submit', '--video-id', 'v-1',
                     '--api-url', 'http://192.168.1.10:8788'])
    assert code == cli.EXIT_SUBMIT
    assert 'private' in capsys.readouterr().err


def test_invalid_media_error_exit_code(cli, monkeypatch, capsys):
    def boom(*a, **kw):
        raise MediaPipelineError('unsupported_format', 'unsupported extension .txt')
    monkeypatch.setattr(cli, 'run_pipeline', boom)
    code = cli.main(['/tmp/x.txt'])
    assert code == cli.EXIT_INVALID
    assert json.loads(capsys.readouterr().err)['error']['kind'] == 'unsupported_format'


def test_processing_failure_exit_code(cli, monkeypatch, capsys):
    def boom(*a, **kw):
        raise MediaPipelineError('ffmpeg_failed', 'frame extraction failed')
    monkeypatch.setattr(cli, 'run_pipeline', boom)
    code = cli.main(['/tmp/x.mp4'])
    assert code == cli.EXIT_PROCESSING
    assert json.loads(capsys.readouterr().err)['error']['kind'] == 'ffmpeg_failed'


def test_mock_asr_script_option_flows_to_engine(cli, monkeypatch, capsys, tmp_path):
    script = tmp_path / 't.txt'
    script.write_text('东湖花园 建筑面积160平方米 报价365万', encoding='utf-8')
    seen = {}

    def fake_run(path, asr_engine=None, ocr_engine=None, **kw):
        seen['asr'] = asr_engine
        return _evidence()

    monkeypatch.setattr(cli, 'run_pipeline', fake_run)
    code = cli.main(['/tmp/x.mp4', '--asr', 'mock', '--asr-script', str(script)])
    assert code == cli.EXIT_OK
    assert seen['asr'].engine == 'mock'
