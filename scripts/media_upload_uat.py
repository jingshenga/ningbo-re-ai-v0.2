"""Real FFmpeg/RapidOCR API acceptance for the isolated NAS UAT container."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

import httpx
import psycopg

API_BASE = os.getenv('MEDIA_UPLOAD_API_BASE', 'http://127.0.0.1:8000').rstrip('/')
API_KEY = os.getenv('APP_API_KEY', '')
DATABASE_URL = os.getenv('DATABASE_URL', '')
FONT = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')


def fail(message: str) -> None:
    raise SystemExit(message)


def protected_table_counts() -> dict[str, int]:
    if not DATABASE_URL:
        fail('DATABASE_URL is not configured for read-only isolation assertions')
    counts = {}
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        conn.execute('SET default_transaction_read_only = on')
        for table in ('videos', 'source_listings', 'price_history'):
            counts[table] = conn.execute('SELECT count(*) FROM ' + table).fetchone()[0]
    return counts


def main() -> None:
    if not API_KEY:
        fail('APP_API_KEY is not configured')
    if not FONT.is_file():
        fail('Noto CJK font is unavailable in the UAT image')
    before = protected_table_counts()
    upload_id = None
    with tempfile.TemporaryDirectory(prefix='media-upload-uat-') as temp:
        work = Path(temp)
        label_file = work / 'label.txt'
        video_file = work / 'synthetic.mp4'
        label_file.write_text('东湖花园 160平方米 3室2厅 365万', encoding='utf-8')
        marker = uuid.uuid4().hex
        vf = ('drawtext=fontfile=%s:textfile=%s:fontcolor=black:fontsize=56:'
              'x=(w-text_w)/2:y=(h-text_h)/2' % (FONT, label_file))
        subprocess.run([
            'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
            '-f', 'lavfi', '-i', 'color=c=white:s=1280x720:r=25:d=4',
            '-vf', vf, '-an', '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
            '-movflags', '+faststart', '-metadata', 'comment=uat-' + marker,
            str(video_file),
        ], check=True, timeout=60, capture_output=True)

        headers = {'X-API-Key': API_KEY}
        form = {
            'source_type': 'operator_local',
            'permission_note': 'NAS隔离验收中由本机生成的合成视频，不含真实房源素材。',
            'title': 'NAS隔离OCR合成验收 ' + marker[:8],
        }
        with httpx.Client(timeout=httpx.Timeout(30, read=15)) as client:
            with video_file.open('rb') as stream:
                uploaded = client.post(
                    API_BASE + '/api/media/uploads', headers=headers, data=form,
                    files={'file': ('synthetic.mp4', stream, 'video/mp4')},
                )
            if uploaded.status_code != 202:
                fail('upload rejected: HTTP %s %s' % (uploaded.status_code, uploaded.text[:300]))
            upload_id = uploaded.json()['upload_id']
            deadline = time.monotonic() + 600
            while time.monotonic() < deadline:
                response = client.get(API_BASE + '/api/media/uploads/' + upload_id,
                                      headers=headers)
                response.raise_for_status()
                job = response.json()
                if job['status'] in ('completed', 'failed', 'failed_unavailable_ocr'):
                    break
                time.sleep(1)
            else:
                fail('upload processing did not reach a terminal status within 600 seconds')

            if job['status'] != 'completed':
                fail('media processing ended with %s: %s' % (job['status'], job.get('error')))
            result = job['result']
            if result['ocr']['status'] != 'ok' or result['ocr']['engine'] != 'rapidocr':
                fail('real RapidOCR was not used successfully')
            ocr_text = '\n'.join(item['text'] for item in result['ocr']['items'])
            hints = result['hints']
            if '365' not in ocr_text or 365.0 not in hints['price_mentions_wan']:
                fail('synthetic asking-price evidence was not detected by OCR and hint extraction')
            if 160.0 not in hints['area_mentions_sqm']:
                fail('synthetic area evidence was not detected')
            if '东湖花园' not in hints['community_mentions']:
                fail('configured synthetic community name was not recognized')
            if hints['confidence_status'] != 'not_calibrated':
                fail('price hints must remain explicitly uncalibrated')
            frame = client.get(result['ocr']['items'][0]['frame_url'], headers=headers)
            if frame.status_code != 200 or not frame.content.startswith(b'\xff\xd8'):
                fail('authenticated OCR frame evidence was not readable')

    after = protected_table_counts()
    if before != after:
        fail('video upload changed videos/listings/price_history tables: ' +
             json.dumps({'before': before, 'after': after}, ensure_ascii=False))
    print(json.dumps({
        'status': job['status'], 'upload_id': upload_id,
        'media_sha256': result['media_sha256'], 'size_bytes': job['size_bytes'],
        'ocr_engine': result['ocr']['engine'], 'ocr_items': len(result['ocr']['items']),
        'ocr_text': ocr_text, 'hints': hints,
        'protected_table_counts_unchanged': after,
        'price_handling': 'not_calibrated; no formal listing or transaction row created',
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
