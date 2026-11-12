"""Submit an operator-saved HTML sample to the local API; never fetches source sites."""
import argparse
from pathlib import Path
import json
import os
import httpx

MAX_HTML_BYTES = 1_000_000


def main():
    p=argparse.ArgumentParser(description='Send a local HTML page snapshot to the staging API')
    p.add_argument('path',type=Path)
    p.add_argument('--source',choices=['beike','anjuke'],required=True)
    p.add_argument('--source-url',required=True)
    p.add_argument('--api-url',default='http://127.0.0.1:8787')
    p.add_argument('--key',default=None,help='Optional; prefer APP_API_KEY environment variable')
    p.add_argument('--note',default='Operator-saved HTML page sample for review')
    args=p.parse_args()
    key=args.key or os.getenv('APP_API_KEY')
    if not key:
        p.error('Set APP_API_KEY environment variable or pass --key')
    try:
        with args.path.open('rb') as sample:
            raw_html = sample.read(MAX_HTML_BYTES + 1)
    except OSError as exc:
        p.error(f'Cannot read HTML sample: {exc}')
    if len(raw_html) > MAX_HTML_BYTES:
        p.error('HTML sample exceeds 1000000 byte limit')
    try:
        html = raw_html.decode('utf-8')
    except UnicodeDecodeError:
        p.error('HTML sample must be UTF-8')
    payload={'source':args.source,'source_url':args.source_url,'html':html,'note':args.note}
    with httpx.Client(timeout=25) as client:
        resp=client.post(args.api_url.rstrip('/')+'/api/collection/pages',json=payload,
                         headers={'X-API-Key':key})
    resp.raise_for_status()
    data=resp.json()
    candidate=data['candidate']
    print(json.dumps({'candidate_id':candidate['id'],'review_status':candidate['review_status'],
                      'ready_for_review':data['ready_for_review'],'warnings':candidate['warnings']},
                     ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
