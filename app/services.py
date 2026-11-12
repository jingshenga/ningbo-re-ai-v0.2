import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from statistics import median
from typing import Any
from uuid import UUID
from fastapi import HTTPException
from psycopg.types.json import Jsonb
from app.db import session
from app.extractor import extract_hints
from app.models import CommunityIn, ListingIn, SavedSearchIn, VideoIn


def now_utc():
    return datetime.now(timezone.utc)


def date_utc(value: datetime | None):
    if value is None:
        return now_utc()
    if value.tzinfo is None:
        raise HTTPException(422, 'Timestamps must include a timezone, e.g. +08:00 or Z')
    return value


def require_row(row: dict | None, kind='record'):
    if row is None:
        raise HTTPException(404, f'{kind} not found')
    return row


def account_by_id(conn, account_id):
    return require_row(conn.execute('SELECT * FROM monitored_accounts WHERE id=%s', (account_id,)).fetchone(), 'account')


def create_account(data):
    mode = 'dtk' if data.platform == 'douyin' else 'manual'
    with session() as conn:
        row = conn.execute('''INSERT INTO monitored_accounts
            (platform,account_ref,nickname,collector_mode,history_mode,poll_interval_minutes,next_poll_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT(platform,account_ref) DO UPDATE SET
                nickname=COALESCE(EXCLUDED.nickname,monitored_accounts.nickname),
                updated_at=now()
            RETURNING *''',
            (data.platform,data.account_ref,data.nickname,mode,data.history_mode,
             data.poll_interval_minutes,now_utc() if mode == 'dtk' else None)).fetchone()
        return row


def all_accounts():
    with session() as conn:
        return conn.execute('SELECT * FROM monitored_accounts ORDER BY created_at DESC').fetchall()


def update_account(account_id, patch):
    fields = patch.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(400, 'No changes specified')
    allowed = {'nickname','enabled','history_mode','poll_interval_minutes'}
    setters, values = [], []
    for name, value in fields.items():
        if name in allowed:
            setters.append(f'{name}=%s')
            values.append(value)
    if not setters:
        raise HTTPException(400, 'No editable fields')
    with session() as conn:
        acct = account_by_id(conn,account_id)
        if 'history_mode' in fields and fields['history_mode'] != acct['history_mode']:
            setters.extend(('initial_synced=FALSE','history_backfill_cursor=NULL',
                            'history_backfill_cutoff=NULL'))
        if fields.get('enabled') is True and acct['collector_mode'] == 'dtk':
            setters.append('next_poll_at=now()')
        setters.append('updated_at=now()')
        values.append(account_id)
        return conn.execute(f"UPDATE monitored_accounts SET {','.join(setters)} WHERE id=%s RETURNING *",values).fetchone()


def queue_account_poll(account_id, history_mode=None):
    with session() as conn:
        acct = account_by_id(conn,account_id)
        if acct['collector_mode'] != 'dtk':
            raise HTTPException(409, 'This account is manual-import only; import videos instead')
        if not acct['enabled']:
            raise HTTPException(409, 'Account monitoring is disabled')
        if history_mode:
            return conn.execute('''UPDATE monitored_accounts SET next_poll_at=now(),
                initial_synced=FALSE,history_mode=%s,history_backfill_cursor=NULL,
                history_backfill_cutoff=NULL,updated_at=now() WHERE id=%s RETURNING *''',
                (history_mode,account_id)).fetchone()
        return conn.execute('UPDATE monitored_accounts SET next_poll_at=now() WHERE id=%s RETURNING *', (account_id,)).fetchone()


def recent_runs(account_id, limit=30):
    with session() as conn:
        account_by_id(conn,account_id)
        return conn.execute('SELECT * FROM account_sync_runs WHERE account_id=%s ORDER BY started_at DESC LIMIT %s',
                            (account_id,limit)).fetchall()


def community_by_name(conn, name):
    return conn.execute('''SELECT c.* FROM communities c WHERE c.city='宁波' AND c.name=%s
        UNION SELECT c.* FROM communities c JOIN community_aliases a ON a.community_id=c.id
        WHERE a.city='宁波' AND a.alias=%s LIMIT 1''', (name,name)).fetchone()


def create_community(data: CommunityIn):
    with session() as conn:
        row = conn.execute('''INSERT INTO communities(name,district,address,verified)
          VALUES(%s,%s,%s,%s) ON CONFLICT(city,name) DO UPDATE SET
          district=COALESCE(communities.district,EXCLUDED.district),
          address=COALESCE(communities.address,EXCLUDED.address),
          verified=communities.verified OR EXCLUDED.verified RETURNING *''',
          (data.name,data.district,data.address,data.verified)).fetchone()
        for alias in set(x.strip() for x in data.aliases if x.strip() and x.strip()!=data.name):
            # Do not silently reassign aliases already owned by another community.
            conn.execute('''INSERT INTO community_aliases(city,alias,community_id)
              VALUES('宁波',%s,%s) ON CONFLICT(city,alias) DO NOTHING''',(alias,row['id']))
        return row


def ensure_community(conn, name, district):
    row = community_by_name(conn,name)
    if row:
        if district and not row['district'] and not row['verified']:
            conn.execute('UPDATE communities SET district=%s WHERE id=%s',(district,row['id']))
        return row['id']
    row = conn.execute('''INSERT INTO communities(name,district,verified)
          VALUES(%s,%s,FALSE) ON CONFLICT(city,name) DO UPDATE SET name=EXCLUDED.name
          RETURNING id''',(name,district)).fetchone()
    return row['id']


def list_communities(query=None):
    with session() as conn:
        if query:
            return conn.execute('''SELECT * FROM communities WHERE name ILIKE %s OR district ILIKE %s
                 ORDER BY name LIMIT 100''',(f'%{query}%',f'%{query}%')).fetchall()
        return conn.execute('SELECT * FROM communities ORDER BY name LIMIT 200').fetchall()


def video_upsert_conn(conn, data: VideoIn | dict):
    d = data.model_dump() if hasattr(data,'model_dump') else data
    if d.get('account_id'):
        acct = account_by_id(conn, d['account_id'])
        if acct['platform'] != d['platform']:
            raise HTTPException(422,'Video platform does not match account')
    row = conn.execute('''INSERT INTO videos
        (account_id,platform,source_post_id,source_url,author_name,title,description,published_at,
        raw_location,permission_note,transcript,ocr_text)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT(platform,source_post_id) DO UPDATE SET
        source_url=COALESCE(EXCLUDED.source_url,videos.source_url),
        title=COALESCE(EXCLUDED.title,videos.title),
        description=COALESCE(EXCLUDED.description,videos.description),
        account_id=COALESCE(videos.account_id,EXCLUDED.account_id),
        author_name=COALESCE(EXCLUDED.author_name,videos.author_name),
        published_at=COALESCE(EXCLUDED.published_at,videos.published_at),
        transcript=COALESCE(EXCLUDED.transcript,videos.transcript),
        ocr_text=COALESCE(EXCLUDED.ocr_text,videos.ocr_text),
        raw_location=COALESCE(EXCLUDED.raw_location,videos.raw_location),
        permission_note=COALESCE(EXCLUDED.permission_note,videos.permission_note),
        updated_at=now() RETURNING *''',
        (d.get('account_id'),d['platform'],d['source_post_id'],d.get('source_url'),
         d.get('author_name'),d.get('title'),d.get('description'),
         date_utc(d['published_at']) if d.get('published_at') else None,
         d.get('raw_location'),d.get('permission_note'),d.get('transcript'),d.get('ocr_text'))).fetchone()
    return row


def video_upsert(data: VideoIn):
    with session() as conn:
        return video_upsert_conn(conn,data)


def batch_videos(items: list[VideoIn]):
    with session() as conn:
        return [video_upsert_conn(conn,x) for x in items]


def list_videos(platform=None, account_id=None, limit=50):
    where, params=[],[]
    if platform:
        where.append('platform=%s'); params.append(platform)
    if account_id:
        where.append('account_id=%s'); params.append(account_id)
    sql='SELECT * FROM videos'
    if where:
        sql+=' WHERE '+' AND '.join(where)
    sql+=' ORDER BY created_at DESC LIMIT %s'
    params.append(limit)
    with session() as conn:
        return conn.execute(sql,params).fetchall()


def enrich_video(video_id, patch):
    d=patch.model_dump(exclude_none=True)
    with session() as conn:
        row=require_row(conn.execute('SELECT * FROM videos WHERE id=%s FOR UPDATE',(video_id,)).fetchone(),'video')
        parts=[d.get('ocr_text',row['ocr_text']),d.get('transcript',row['transcript']),row['title'],row['description']]
        names=conn.execute('''SELECT name AS label FROM communities UNION SELECT alias AS label FROM community_aliases''').fetchall()
        hints=extract_hints(*parts,known_community_names=[n['label'] for n in names],
                            source_labels=['ocr_text','transcript','title','description'])
        return conn.execute('''UPDATE videos SET transcript=COALESCE(%s,transcript),
         ocr_text=COALESCE(%s,ocr_text),raw_location=COALESCE(%s,raw_location),
         extracted_fields=%s,processing_status='enriched',updated_at=now()
         WHERE id=%s RETURNING *''',
         (d.get('transcript'),d.get('ocr_text'),d.get('raw_location'),Jsonb(hints),video_id)).fetchone()


def listing_matches_search(search, listing):
    if search['district'] and search['district'] != listing['district']:
        return False
    districts = search.get('districts') or []
    if districts and listing['district'] not in districts:
        return False
    if search['community_name'] and search['community_name'] != listing['community_name']:
        return False
    if listing['community_name'] in (search.get('excluded_communities') or []):
        return False
    if search['max_price_wan'] and Decimal(str(listing['asking_price_wan'])) > search['max_price_wan']:
        return False
    if search['min_area_sqm'] and Decimal(str(listing['area_sqm'])) < search['min_area_sqm']:
        return False
    if search['min_bedrooms'] is not None and (listing['bedrooms'] is None or listing['bedrooms'] < search['min_bedrooms']):
        return False
    max_age_days = search.get('max_listing_age_days')
    if max_age_days is not None and listing['last_observed_at'] < now_utc() - timedelta(days=max_age_days):
        return False
    return True


def saved_search_match_reasons(search, listing):
    def number(value):
        return format(Decimal(str(value)).normalize(), 'f')

    reasons = []
    if search['district'] or search.get('districts'):
        reasons.append(f"区域匹配：{listing['district']}")
    if search['community_name']:
        reasons.append(f"小区匹配：{listing['community_name']}")
    if search['max_price_wan'] is not None:
        reasons.append(f"总价{number(listing['asking_price_wan'])}万元，不超过上限{number(search['max_price_wan'])}万元")
    if search['min_area_sqm'] is not None:
        reasons.append(f"面积{number(listing['area_sqm'])}㎡，达到下限{number(search['min_area_sqm'])}㎡")
    if search['min_bedrooms'] is not None:
        reasons.append(f"户型{listing['bedrooms']}室，达到至少{search['min_bedrooms']}室")
    if search.get('max_listing_age_days') is not None:
        reasons.append(f"最近{search['max_listing_age_days']}天内有更新")
    if listing['community_name'] in (search.get('preferred_communities') or []):
        reasons.append(f"命中偏好小区：{listing['community_name']}")
    return reasons or ['符合当前条件单筛选项']


def queue_notifications(conn, listing_id, event_type, observed_at, old_price=None):
    listing=conn.execute('''SELECT l.*,p.area_sqm,p.bedrooms,c.name AS community_name,c.district
      FROM source_listings l JOIN properties p ON p.id=l.property_id
      JOIN communities c ON c.id=p.community_id WHERE l.id=%s''',(listing_id,)).fetchone()
    if not listing:
        return
    searches=conn.execute('SELECT * FROM saved_searches WHERE notifications_enabled').fetchall()
    for search in searches:
        if not listing_matches_search(search,listing):
            continue
        drop_pct=None
        if event_type=='price_drop':
            if old_price is None or old_price<=0:
                continue
            drop_pct=round((old_price-listing['asking_price_wan'])/old_price*100,2)
            if drop_pct < search['min_drop_pct']:
                continue
        event_key=f"{listing_id}:{event_type}:{observed_at.isoformat()}" if event_type=='price_drop' else f'{listing_id}:new'
        payload={'community':listing['community_name'],'price_wan':float(listing['asking_price_wan']),
                 'area_sqm':float(listing['area_sqm']),'source':listing['source'],
                 'preferred_community': listing['community_name'] in (search.get('preferred_communities') or []),
                 'old_price_wan':float(old_price) if old_price is not None else None,
                 'drop_pct':float(drop_pct) if drop_pct is not None else None,
                 'note':'Event recorded only, not externally sent; listing status and data rights must be verified.'}
        conn.execute('''INSERT INTO notification_logs(search_id,listing_id,event_key,event_type,payload)
            VALUES(%s,%s,%s,%s,%s) ON CONFLICT(search_id,event_key) DO NOTHING''',
            (search['id'],listing_id,event_key,event_type,Jsonb(payload)))


def upsert_listing(data: ListingIn):
    with session() as conn:
        return upsert_listing_conn(conn,data)


def upsert_listing_conn(conn, data: ListingIn):
    """Ingest a source-specific listing in caller's transaction.

    This allows candidate approval and price snapshots to be committed atomically.
    """
    ts=date_utc(data.observed_at)
    community_id=ensure_community(conn,data.community_name,data.district)
    quote_type='agent_claim' if data.source=='agent' else 'platform_listed'
    existing=conn.execute('''SELECT * FROM source_listings WHERE source=%s AND source_listing_id=%s FOR UPDATE''',
                          (data.source,data.source_listing_id)).fetchone()
    if existing is None:
        prop=conn.execute('''INSERT INTO properties(community_id,area_sqm,bedrooms,floor_text,decoration)
            VALUES(%s,%s,%s,%s,%s) RETURNING id''',
            (community_id,data.area_sqm,data.bedrooms,data.floor_text,data.decoration)).fetchone()
        row=conn.execute('''INSERT INTO source_listings(source,source_listing_id,property_id,
           title,listing_url,asking_price_wan,first_observed_at,last_observed_at,permission_note)
           VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *''',
           (data.source,data.source_listing_id,prop['id'],data.title,data.listing_url,
            data.asking_price_wan,ts,ts,data.permission_note)).fetchone()
        conn.execute('''INSERT INTO price_history(listing_id,price_wan,observed_at,quote_type,evidence_url)
           VALUES(%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING''',
           (row['id'],data.asking_price_wan,ts,quote_type,data.listing_url))
        queue_notifications(conn,row['id'],'new_listing',ts)
        return {'listing':row,'created':True,'price_changed':False,'historical_only':False}

    # Do not fabricate a price-drop story if a source reuses listing IDs.
    old_prop=conn.execute('SELECT community_id,area_sqm,bedrooms FROM properties WHERE id=%s',
                          (existing['property_id'],)).fetchone()
    if old_prop['community_id']!=community_id or abs(float(old_prop['area_sqm']/data.area_sqm)-1)>0.03:
        raise HTTPException(409,'Source listing identity changed (community/area); manual review required')
    # Never replace the latest snapshot with an older one. Preserve backfill as evidence.
    if ts < existing['last_observed_at']:
        conn.execute('''INSERT INTO price_history(listing_id,price_wan,observed_at,quote_type,evidence_url)
            VALUES(%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING''',
            (existing['id'],data.asking_price_wan,ts,quote_type,data.listing_url))
        return {'listing':existing,'created':False,'price_changed':False,'historical_only':True}
    changed=Decimal(data.asking_price_wan)!=existing['asking_price_wan']
    if changed and ts==existing['last_observed_at']:
        raise HTTPException(409,'A changed price needs a newer observed_at timestamp')
    row=conn.execute('''UPDATE source_listings SET title=COALESCE(%s,title),
       listing_url=COALESCE(%s,listing_url),asking_price_wan=%s,
       last_observed_at=GREATEST(last_observed_at,%s),
       permission_note=COALESCE(%s,permission_note),updated_at=now()
       WHERE id=%s RETURNING *''',
       (data.title,data.listing_url,data.asking_price_wan,ts,data.permission_note,existing['id'])).fetchone()
    # If listing identity attributes changed, flag via manual review rather than rematching it.
    if changed:
        conn.execute('''INSERT INTO price_history(listing_id,price_wan,observed_at,quote_type,evidence_url)
           VALUES(%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING''',
           (row['id'],data.asking_price_wan,ts,quote_type,data.listing_url))
        if data.asking_price_wan<existing['asking_price_wan']:
            queue_notifications(conn,row['id'],'price_drop',ts,existing['asking_price_wan'])
    return {'listing':row,'created':False,'price_changed':changed,'historical_only':False}

def listings(district=None,max_price_wan=None,min_area_sqm=None,min_bedrooms=None,community_name=None,limit=100):
    sql='''SELECT l.*,p.area_sqm,p.bedrooms,p.floor_text,p.decoration,c.name AS community_name,
          c.district,c.verified AS community_verified
          FROM source_listings l JOIN properties p ON p.id=l.property_id
          JOIN communities c ON c.id=p.community_id WHERE 1=1'''
    values=[]
    if district:
        sql+=' AND c.district=%s'; values.append(district)
    if community_name:
        sql+=' AND c.name=%s'; values.append(community_name)
    if max_price_wan is not None:
        sql+=' AND l.asking_price_wan<=%s'; values.append(max_price_wan)
    if min_area_sqm is not None:
        sql+=' AND p.area_sqm>=%s'; values.append(min_area_sqm)
    if min_bedrooms is not None:
        sql+=' AND p.bedrooms>=%s'; values.append(min_bedrooms)
    sql+=' ORDER BY l.last_observed_at DESC LIMIT %s'
    values.append(limit)
    with session() as conn:
        return conn.execute(sql,values).fetchall()


def listing_prices(listing_id):
    with session() as conn:
        require_row(conn.execute('SELECT id FROM source_listings WHERE id=%s',(listing_id,)).fetchone(),'listing')
        return conn.execute('''SELECT price_wan,observed_at,quote_type,evidence_url
         FROM price_history WHERE listing_id=%s ORDER BY observed_at''',(listing_id,)).fetchall()


def create_saved_search(data: SavedSearchIn):
    with session() as conn:
        return conn.execute('''INSERT INTO saved_searches(name,district,community_name,max_price_wan,
          min_area_sqm,min_bedrooms,min_drop_pct,notifications_enabled,districts,
          preferred_communities,excluded_communities,max_listing_age_days)
          VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *''',
          (data.name,data.district,data.community_name,data.max_price_wan,
           data.min_area_sqm,data.min_bedrooms,data.min_drop_pct,data.notifications_enabled,
           data.districts,data.preferred_communities,data.excluded_communities,
           data.max_listing_age_days)).fetchone()


def all_saved_searches():
    with session() as conn:
        return conn.execute('SELECT * FROM saved_searches ORDER BY created_at DESC').fetchall()


def saved_search_matches(search_id, limit=100):
    with session() as conn:
        search = require_row(conn.execute(
            'SELECT * FROM saved_searches WHERE id=%s', (search_id,)).fetchone(), 'saved search')
        conditions = ["l.status NOT IN ('withdrawn','sold')"]
        values = []
        if search['district']:
            conditions.append('c.district=%s'); values.append(search['district'])
        if search['districts']:
            conditions.append('c.district=ANY(%s)'); values.append(search['districts'])
        if search['community_name']:
            conditions.append('c.name=%s'); values.append(search['community_name'])
        if search['excluded_communities']:
            conditions.append('NOT (c.name=ANY(%s))'); values.append(search['excluded_communities'])
        if search['max_price_wan'] is not None:
            conditions.append('l.asking_price_wan<=%s'); values.append(search['max_price_wan'])
        if search['min_area_sqm'] is not None:
            conditions.append('p.area_sqm>=%s'); values.append(search['min_area_sqm'])
        if search['min_bedrooms'] is not None:
            conditions.append('p.bedrooms>=%s'); values.append(search['min_bedrooms'])
        if search['max_listing_age_days'] is not None:
            conditions.append("l.last_observed_at>=now()-(%s * interval '1 day')")
            values.append(search['max_listing_age_days'])
        preferred = search['preferred_communities'] or []
        rows = conn.execute('''SELECT count(*) OVER() AS total_count,l.id,l.source,
          l.source_listing_id,l.title,l.listing_url,l.asking_price_wan,l.last_observed_at,
          p.area_sqm,p.bedrooms,p.floor_text,p.decoration,c.name AS community_name,c.district
          FROM source_listings l JOIN properties p ON p.id=l.property_id
          JOIN communities c ON c.id=p.community_id WHERE ''' + ' AND '.join(conditions) + '''
          ORDER BY CASE WHEN c.name=ANY(%s) THEN 0 ELSE 1 END,l.last_observed_at DESC LIMIT %s''',
          (*values, preferred, limit)).fetchall()
    total = rows[0]['total_count'] if rows else 0
    matches = []
    for row in rows:
        item = dict(row)
        item.pop('total_count')
        item['preferred_community'] = item['community_name'] in preferred
        item['match_reasons'] = saved_search_match_reasons(search, item)
        matches.append(item)
    return {'search_id': search_id, 'total': total, 'matches': matches}


def notifications(status='pending',limit=100):
    with session() as conn:
        return conn.execute('''SELECT n.*,s.name AS search_name FROM notification_logs n
          JOIN saved_searches s ON s.id=n.search_id WHERE n.delivery_status=%s
          ORDER BY n.created_at DESC LIMIT %s''',(status,limit)).fetchall()


def mark_notification_read(event_id):
    with session() as conn:
        return require_row(conn.execute('''UPDATE notification_logs SET delivery_status='read'
         WHERE id=%s RETURNING *''',(event_id,)).fetchone(),'notification')


def same_listing_price_drop(history, cutoff, through):
    """Return the first-to-last platform-listed drop for one listing in a closed time window."""
    rows = sorted((row for row in history
                   if row['quote_type'] == 'platform_listed' and cutoff <= row['observed_at'] <= through),
                  key=lambda row: row['observed_at'])
    if len(rows) < 2 or rows[0]['price_wan'] <= rows[-1]['price_wan']:
        return None
    amount = rows[0]['price_wan'] - rows[-1]['price_wan']
    return {
        'amount_wan': amount,
        'pct': round(float(amount / rows[0]['price_wan'] * 100), 2),
        'from_price_wan': rows[0]['price_wan'],
        'to_price_wan': rows[-1]['price_wan'],
        'from_observed_at': rows[0]['observed_at'],
        'to_observed_at': rows[-1]['observed_at'],
        'evidence_url': rows[-1].get('evidence_url'),
    }


CROSS_PLATFORM_PRICE_GAP_MIN_PCT = Decimal('10')


def opportunities(days=30,min_drop_pct=5,min_discount_pct=8,limit=100):
    """Candidate signals, not valuations or cross-platform identity assertions."""
    if days not in (7, 30, 90):
        raise HTTPException(422, 'days must be 7, 30, or 90')
    through=now_utc()
    cutoff=through-timedelta(days=days)
    with session() as conn:
        ls=conn.execute('''SELECT l.id,l.property_id,l.source,l.source_listing_id,l.title,l.asking_price_wan,
          l.last_observed_at,l.listing_url,p.area_sqm,p.bedrooms,p.community_id,c.name AS community_name,c.district
          FROM source_listings l JOIN properties p ON p.id=l.property_id
          JOIN communities c ON c.id=p.community_id WHERE l.source<>'agent'
          AND l.status NOT IN ('withdrawn','sold')
          AND l.last_observed_at >= now() - interval '90 days' AND l.last_observed_at <= now()
          ORDER BY l.last_observed_at DESC LIMIT 1200''').fetchall()
        if not ls:
            return []
        histories=conn.execute('''SELECT listing_id,price_wan,observed_at,quote_type,evidence_url FROM price_history
          WHERE observed_at >= %s AND observed_at <= %s AND quote_type='platform_listed'
          ORDER BY observed_at ASC''',(cutoff,through)).fetchall()
    listings_by_community_and_bedrooms={}
    for candidate in ls:
        if candidate['bedrooms'] is None:
            continue
        key=(candidate['community_id'],candidate['bedrooms'])
        listings_by_community_and_bedrooms.setdefault(key,[]).append(candidate)
    grouped={}
    for h in histories:
        grouped.setdefault(h['listing_id'],[]).append(h)
    results=[]
    for listing in ls:
        history=grouped.get(listing['id'],[])
        drop=same_listing_price_drop(history,cutoff,through)
        drop_pct=drop['pct'] if drop else 0.0
        similar_by_property={}
        matching_listings = (listings_by_community_and_bedrooms.get(
            (listing['community_id'],listing['bedrooms']), ())
            if listing['bedrooms'] is not None else ())
        for candidate in matching_listings:
            if candidate['property_id']==listing['property_id']:
                continue
            candidate_area=Decimal(str(candidate['area_sqm']))
            listing_area=Decimal(str(listing['area_sqm']))
            if abs(candidate_area-listing_area)/listing_area>Decimal('0.10'):
                continue
            similar_by_property.setdefault(candidate['property_id'],[]).append(
                float(candidate['asking_price_wan']/candidate['area_sqm']))
        similar=[median(prices) for prices in similar_by_property.values()]
        compare_n=len(similar)
        discount_pct=None
        compare_med=None
        unit_price=float(listing['asking_price_wan']/listing['area_sqm'])
        if compare_n>=5:
            compare_med=median(similar)
            discount_pct=round(max(0.0,(compare_med-unit_price)/compare_med*100),2) if compare_med else None
        cross_platform_gaps=[]
        if listing['source'] in ('beike','anjuke') and listing['bedrooms'] is not None:
            for candidate in matching_listings:
                if candidate['source'] not in ('beike','anjuke') or candidate['source']==listing['source']:
                    continue
                if candidate['community_id']!=listing['community_id']:
                    continue
                if candidate['bedrooms'] is None or candidate['bedrooms']!=listing['bedrooms']:
                    continue
                area=Decimal(str(listing['area_sqm']))
                candidate_area=Decimal(str(candidate['area_sqm']))
                area_gap_pct=abs(area-candidate_area)/min(area,candidate_area)*100
                if area_gap_pct>Decimal('5'):
                    continue
                candidate_unit=Decimal(str(candidate['asking_price_wan']))/candidate_area
                target_unit=Decimal(str(listing['asking_price_wan']))/area
                target_cross=Decimal(str(listing['asking_price_wan']))*candidate_area
                candidate_cross=Decimal(str(candidate['asking_price_wan']))*area
                low_cross,high_cross=sorted((target_cross,candidate_cross))
                price_gap_numerator=high_cross-low_cross
                if price_gap_numerator*100 < low_cross*CROSS_PLATFORM_PRICE_GAP_MIN_PCT:
                    continue
                price_gap_pct=price_gap_numerator/low_cross*100
                cross_platform_gaps.append({
                    'listing_id':candidate['id'],
                    'source':candidate['source'],
                    'source_listing_id':candidate['source_listing_id'],
                    'listing_url':candidate['listing_url'],
                    'asking_price_wan':candidate['asking_price_wan'],
                    'area_sqm':candidate['area_sqm'],
                    'unit_price_wan_per_sqm':round(float(candidate_unit),2),
                    'last_observed_at':candidate['last_observed_at'],
                    'unit_price_gap_pct':round(float(price_gap_pct),2),
                    'area_difference_pct':round(float(area_gap_pct),2),
                    'verification_status':'candidate',
                })
        cross_platform_gaps.sort(key=lambda gap:gap['unit_price_gap_pct'],reverse=True)
        signals=[]
        if drop_pct>=min_drop_pct and drop_pct>0:
            signals.append('same_listing_price_drop')
        if discount_pct is not None and discount_pct>=min_discount_pct and discount_pct>0:
            signals.append('below_raw_listing_median')
        if cross_platform_gaps:
            signals.append('cross_platform_price_gap')
        if signals:
            reasons=[]
            if 'same_listing_price_drop' in signals:
                reasons.append(f"{days}日内同挂牌平台报价下降{drop['amount_wan']}万元（{drop_pct:.2f}%）")
            if 'below_raw_listing_median' in signals:
                reasons.append(f"挂牌单价{unit_price:.2f}万元/㎡，低于{compare_n}套可比房屋单价中位数{compare_med:.2f}万元/㎡")
            for gap in cross_platform_gaps:
                source_name='贝壳' if gap['source']=='beike' else '安居客'
                reasons.append(f"跨平台候选：与{source_name}单价相差{gap['unit_price_gap_pct']:.2f}%（以低价为分母，面积差{gap['area_difference_pct']:.2f}%），疑似同套，待核实")
            results.append({
                'listing_id':listing['id'],'community':listing['community_name'],
                'district':listing['district'],'source':listing['source'],
                'source_listing_id':listing['source_listing_id'],
                'listing_url':listing['listing_url'],
                'area_sqm':listing['area_sqm'],'bedrooms':listing['bedrooms'],
                'asking_price_wan':listing['asking_price_wan'],
                'unit_price_wan_per_sqm':round(unit_price,2),
                'drop_pct_in_window':round(drop_pct,2),
                'drop_amount_wan':drop['amount_wan'] if drop else None,
                'drop_from_price_wan':drop['from_price_wan'] if drop else None,
                'drop_to_price_wan':drop['to_price_wan'] if drop else None,
                'drop_from_observed_at':drop['from_observed_at'] if drop else None,
                'drop_to_observed_at':drop['to_observed_at'] if drop else None,
                'drop_evidence_url':drop['evidence_url'] if drop else None,
                'discount_vs_raw_listing_median_pct':discount_pct,
                'comparable_median_wan_per_sqm':round(compare_med,2) if compare_med is not None else None,
                'comparable_sample_count':compare_n,
                'cross_platform_price_gap_pct':cross_platform_gaps[0]['unit_price_gap_pct'] if cross_platform_gaps else None,
                'cross_platform_price_gaps':cross_platform_gaps,
                'last_observed_at':listing['last_observed_at'],
                'signals':signals,
                'signal_reasons':reasons,
                'notice':'仅为挂牌数据线索，不是成交价或估值；跨平台相似挂牌只是待核实候选，不代表已确认同套。'
            })
    return sorted(results,key=lambda x:(x['drop_pct_in_window'],x['discount_vs_raw_listing_median_pct'] or 0,
                                        x['cross_platform_price_gap_pct'] or 0),reverse=True)[:limit]


def match_video_candidates(video_id,limit=20):
    """Candidate-only, intentionally never merges or asserts identical units."""
    with session() as conn:
        video=require_row(conn.execute('SELECT * FROM videos WHERE id=%s',(video_id,)).fetchone(),'video')
        hints=video['extracted_fields'] or {}
        if not hints.get('community_mentions'):
            raise HTTPException(409,'Enrich the video first; no community hints are available')
        resolved=[]
        for label in hints['community_mentions']:
            row=community_by_name(conn,label)
            if row and row['id'] not in resolved:
                resolved.append(row['id'])
        if not resolved:
            return []
        rows=conn.execute('''SELECT l.id,l.asking_price_wan,l.source,l.source_listing_id,
             p.area_sqm,p.bedrooms,p.community_id,c.name AS community_name
             FROM source_listings l JOIN properties p ON p.id=l.property_id
             JOIN communities c ON c.id=p.community_id
             WHERE p.community_id = ANY(%s) AND l.status NOT IN ('sold','withdrawn')
             ORDER BY l.last_observed_at DESC LIMIT 200''', (resolved,)).fetchall()
        output=[]
        for row in rows:
            score=40
            evidence={'community_match':row['community_name']}
            areas=hints.get('area_mentions_sqm') or []
            if areas:
                area_error=min(abs(float(row['area_sqm'])/float(a)-1) for a in areas if float(a)>0)
                evidence['area_relative_error']=round(area_error,4)
                if area_error<=0.02: score+=25
                elif area_error<=0.05:score+=15
                elif area_error<=0.10:score+=5
            rooms=hints.get('bedroom_mentions') or []
            if row['bedrooms'] is not None and rooms:
                evidence['bedrooms_match']=row['bedrooms'] in rooms
                if row['bedrooms'] in rooms:score+=10
            prices=hints.get('price_mentions_wan') or []
            if prices:
                price_error=min(abs(float(row['asking_price_wan'])/float(p)-1) for p in prices if float(p)>0)
                evidence['price_relative_error']=round(price_error,4)
                if price_error<=0.03: score+=15
                elif price_error<=0.08:score+=8
            output.append({'listing_id':row['id'],'score':score,'evidence':evidence,
              'source':row['source'],'source_listing_id':row['source_listing_id'],
              'status':'candidate_only_not_confirmed'})
        output.sort(key=lambda x:x['score'],reverse=True)
        result=[]
        for row in output[:limit]:
            matched=conn.execute('''INSERT INTO property_matches(video_id,listing_id,match_score,evidence)
              VALUES(%s,%s,%s,%s) ON CONFLICT(video_id,listing_id) DO UPDATE SET
              match_score=CASE WHEN property_matches.status='candidate' THEN EXCLUDED.match_score
                   ELSE property_matches.match_score END,
              evidence=CASE WHEN property_matches.status='candidate' THEN EXCLUDED.evidence
                   ELSE property_matches.evidence END
              RETURNING id,status''',(video_id,row['listing_id'],row['score'],Jsonb(row['evidence']))).fetchone()
            row['match_id']=matched['id'];row['review_status']=matched['status']
            result.append(row)
        return result


def review_match(match_id,review_status):
    with session() as conn:
        return require_row(conn.execute('''UPDATE property_matches SET status=%s,reviewed_at=now()
           WHERE id=%s RETURNING *''',(review_status,match_id)).fetchone(),'match')
