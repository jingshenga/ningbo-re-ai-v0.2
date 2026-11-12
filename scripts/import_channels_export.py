#!/usr/bin/env python3
"""Map a local JSON export to this project's batch endpoint. Manual / authorized import only.

Does not log in to WeChat or attempt to fetch private data.
Usage:
  python scripts/import_channels_export.py data.json --account-id UUID --url http://127.0.0.1:8787 --key YOUR_KEY
The exporter field names vary across versions. Inspect the --dry-run output first.
"""
import argparse
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen


def first(row,*keys):
    for k in keys:
        if row.get(k) is not None and row.get(k)!='':
            return row[k]
    return None


def map_rows(data,account_id=None):
    if isinstance(data,dict):
        for k in ('items','records','videos','data'):
            if isinstance(data.get(k),list):
                data=data[k]
                break
    if not isinstance(data,list):
        raise ValueError('Expected array or object with items/records/videos/data array')
    items=[]; missing=[]
    for index,row in enumerate(data):
        if not isinstance(row,dict):
            missing.append(index);continue
        post_id=first(row,'source_post_id','video_id','videoId','id','object_id')
        if not post_id:
            missing.append(index);continue
        item={
          'platform':'wechat_channels',
          'source_post_id':str(post_id),
          'author_name':first(row,'author_name','author','nickname','finderNickname'),
          'title':first(row,'title','desc','description'),
          'description':first(row,'description','desc'),
          'source_url':first(row,'share_url','url','video_url'),
          'raw_location':first(row,'location','poi_name','ip_location'),
          'permission_note':'Imported by operator from locally exported video metadata; verify use rights.'
        }
        if account_id:
            item['account_id']=account_id
        # Export timestamps may be milliseconds, Unix seconds, or locale-specific; leave
        # unset instead of silently misdating a video. Add published_at after review.
        date=first(row,'published_at','publishedAt','create_time_iso')
        if isinstance(date,str) and ('T' in date) and ('+' in date or date.endswith('Z')):
            item['published_at']=date
        items.append(item)
    return {'items':items},missing


def main():
    p=argparse.ArgumentParser()
    p.add_argument('json_file')
    p.add_argument('--account-id')
    p.add_argument('--url',default='http://127.0.0.1:8787')
    p.add_argument('--key')
    p.add_argument('--dry-run',action='store_true')
    args=p.parse_args()
    payload,missing=map_rows(json.loads(Path(args.json_file).read_text(encoding='utf-8')),args.account_id)
    if missing:
        print('Rows missing stable ID, skipped:',missing,file=sys.stderr)
    print('Mapped items:',len(payload['items']))
    if not payload['items']:
        raise SystemExit('No valid records; inspect export format')
    if args.dry_run:
        print(json.dumps(payload['items'][:3],ensure_ascii=False,indent=2))
        return
    if not args.key:
        raise SystemExit('--key required unless --dry-run')
    for start in range(0,len(payload['items']),200):
        batch={'items':payload['items'][start:start+200]}
        req=Request(args.url.rstrip('/')+'/api/ingest/videos/batch',
            data=json.dumps(batch,ensure_ascii=False).encode('utf-8'),
            headers={'Content-Type':'application/json','X-API-Key':args.key},method='POST')
        with urlopen(req,timeout=60) as r:
            print(r.read().decode('utf-8'))


if __name__=='__main__':
    main()
