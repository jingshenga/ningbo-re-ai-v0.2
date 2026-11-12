from pathlib import Path
import os
import subprocess
import sys


def test_submit_script_rejects_oversized_html_before_api_request(tmp_path):
    root = Path(__file__).resolve().parents[1]
    sample = tmp_path / 'oversized.html'
    sample.write_bytes(b'x' * 1_000_001)
    env = {**os.environ, 'APP_API_KEY': 'test-key'}

    result = subprocess.run(
        [sys.executable, str(root / 'scripts/submit_html_snapshot.py'), str(sample),
         '--source', 'beike', '--source-url',
         'https://nb.ke.com/ershoufang/109900001234.html'],
        cwd=root, env=env, capture_output=True, text=True, check=False,
    )

    assert result.returncode == 2
    assert 'HTML sample exceeds 1000000 byte limit' in result.stderr
