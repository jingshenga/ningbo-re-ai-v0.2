"""Review-gated Beike/Anjuke page data staging.

V0.2 never promotes extracted values to canonical listings without an explicit
operator approval. Online mode defaults OFF and depends on site permission.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import logging
import os
import tempfile
import zlib
from decimal import Decimal
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException
from pydantic import ValidationError
from psycopg.types.json import Jsonb

from app.collectors.http_client import CollectionBlocked, fetch_public_html
from app.collectors import check_source_url, extract_source_id, parse_listing_html
from app.collectors.discovery import discover_listing_links
from app.collectors.url_policy import source_page_key
from app.collectors.parser import CollectionError, PARSER_VERSION, ParseResult
from app.collectors.policy import may_fetch_online
from app.collection_models import (CandidateCorrection, CollectionTargetIn,
                                   CollectionTargetPatch, DiscoveryStateIn,
                                   DiscoveryReviewIn, HTMLPageIn, PolicyReviewIn)
from app.db import session
from app.models import ListingIn
from app.settings import ENABLE_ONLINE_COLLECTION, RAW_HTML_DIR, COLLECTION_MIN_DELAY_SECONDS
from app import services
from app.log_safety import safe_error_summary

log = logging.getLogger('collection')
MAX_DISCOVERY_DETAILS_PER_RUN = 20
MAX_DISCOVERY_PAGES_PER_RUN = 5
MAX_DISCOVERY_STATE_IDS = 100_000
MAX_DISCOVERY_STATE_ID_BYTES = 1_500_000
REQUIRED_LISTING_FIELDS = ('source_listing_id', 'community_name',
                           'asking_price_wan', 'area_sqm')


def now():
    return datetime.now(timezone.utc)


def _save_html(sha: str, html: str) -> str:
    """Save evidence as a compressed, content-addressed file via atomic replace."""
    folder = Path(RAW_HTML_DIR)
    if folder.is_symlink():
        raise CollectionError('Raw HTML storage directory must not be a symlink')
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    if folder.is_symlink():
        raise CollectionError('Raw HTML storage directory must not be a symlink')
    file = folder / f'{sha}.html.gz'
    html_bytes = html.encode('utf-8')
    if file.exists() and not file.is_symlink():
        try:
            with gzip.open(file, 'rb') as saved:
                if saved.read(len(html_bytes) + 1) == html_bytes:
                    return str(file)
        except (OSError, EOFError, zlib.error):
            pass
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=folder, prefix='.tmp-', suffix='.html.gz',
                                         delete=False) as tmp:
            tmp_path = Path(tmp.name)
            with gzip.GzipFile(fileobj=tmp, mode='wb', compresslevel=6) as out:
                out.write(html_bytes)
        # Identical SHA implies identical content; concurrent updates are harmless.
        os.replace(tmp_path, file)
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink()
    return str(file)


def stage_html(source: str, url: str, html: str, capture_method: str,
               captured_at: datetime | None = None, note: str | None = None):
    if capture_method not in ('manual_html_snapshot', 'public_page_collection'):
        raise CollectionError('Invalid capture method')
    try:
        parsed = parse_listing_html(source, url, html)
    except Exception:
        _record_parse_attempt(source, capture_method, PARSER_VERSION, 'failed', False)
        raise
    field_complete = _required_fields_complete(parsed.fields)
    _record_parse_attempt(source, capture_method, parsed.parser_version,
                          'success', field_complete)
    path = _save_html(parsed.sha256, html)
    warnings = parsed.warnings[:]
    if note:
        warnings.append('operator_note: ' + note[:400])
    with session() as conn:
        row = conn.execute('''INSERT INTO collection_candidates
          (source,source_url,capture_method,source_listing_id,raw_sha256,raw_storage_path,
           parser_version,extracted_fields,warnings,captured_at)
          VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
          ON CONFLICT(source,source_url,raw_sha256) DO UPDATE SET
            source_listing_id=EXCLUDED.source_listing_id,
            parser_version=EXCLUDED.parser_version,
            extracted_fields=EXCLUDED.extracted_fields,
            warnings=EXCLUDED.warnings || COALESCE((
              SELECT jsonb_agg(old_warning)
              FROM jsonb_array_elements(collection_candidates.warnings) AS old(old_warning)
              WHERE old_warning #>> '{}' LIKE 'operator_note:%%'
            ), '[]'::jsonb)
          WHERE collection_candidates.review_status='pending'
            AND collection_candidates.parser_version IS DISTINCT FROM EXCLUDED.parser_version
            AND NOT (collection_candidates.extracted_fields ? 'manually_corrected')
          RETURNING *''',
          (source,url,capture_method,parsed.fields.get('source_listing_id'),
           parsed.sha256,path,parsed.parser_version,Jsonb(parsed.fields),Jsonb(warnings),captured_at or now())).fetchone()
        if row is None:
            row = conn.execute('''SELECT * FROM collection_candidates
              WHERE source=%s AND source_url=%s AND raw_sha256=%s''',
              (source,url,parsed.sha256)).fetchone()
        if row is None:
            raise CollectionError('Collection candidate disappeared during duplicate submission')
        persisted_parse = ParseResult(
            fields=row['extracted_fields'], warnings=row['warnings'],
            sha256=row['raw_sha256'], parser_version=row['parser_version'])
    return {'candidate': row, 'ready_for_review': persisted_parse.ready_for_review,
            'note': 'Only a review candidate; listing and price history were NOT modified.'}


def _record_parse_attempt(source, capture_method, parser_version,
                          parse_status, field_complete):
    with session() as conn:
        conn.execute('''INSERT INTO collection_parse_attempts
          (source,capture_method,parser_version,parse_status,required_fields_complete)
          VALUES(%s,%s,%s,%s,%s)''',
          (source,capture_method,parser_version,parse_status,field_complete))


def _required_fields_complete(fields):
    return all(field in fields and fields[field] is not None and
               (not isinstance(fields[field], str) or fields[field].strip())
               for field in REQUIRED_LISTING_FIELDS)


def stage_manual_page(data: HTMLPageIn):
    return stage_html(data.source,data.source_url,data.html,'manual_html_snapshot',
                      data.captured_at,data.note)


def sources():
    with session() as conn:
        rows = conn.execute('SELECT * FROM source_registry ORDER BY source').fetchall()
    return [{**dict(x), 'global_online_enabled': ENABLE_ONLINE_COLLECTION} for x in rows]


def health_metrics():
    with session() as conn:
        rows = conn.execute('''SELECT s.source,s.online_policy_status,s.online_enabled,
            m.success_count,m.failure_count,m.blocked_count,m.last_attempt_at,m.last_success_at,
            m.parse_attempt_count,m.parse_success_count,m.complete_field_count,
            m.pending_count,m.approved_count,m.rejected_count,m.listing_count,m.last_observed_at,
            m.latest_status,m.latest_note
          FROM source_registry s
          JOIN collection_health_metrics m USING (source)
          ORDER BY s.source''').fetchall()
    result = []
    for row in rows:
        item = dict(row)
        success_and_failure = item['success_count'] + item['failure_count']
        parse_attempts = item['parse_attempt_count']
        parse_successes = item['parse_success_count']
        reviewed_candidates = item['approved_count'] + item['rejected_count']
        item.update(
            collection_success_rate_pct=_rate(item['success_count'], success_and_failure),
            parse_success_rate_pct=_rate(parse_successes, parse_attempts),
            field_complete_rate_pct=_rate(item['complete_field_count'], parse_successes),
            approval_rate_pct=_rate(item['approved_count'], reviewed_candidates),
            global_online_enabled=ENABLE_ONLINE_COLLECTION)
        result.append(item)
    return result


def _rate(numerator, denominator):
    return round(numerator * 100 / denominator, 2) if denominator else None


def update_source_policy(source: str, data: PolicyReviewIn):
    if source not in ('beike', 'anjuke'):
        raise HTTPException(404, 'Unknown source')
    with session() as conn:
        row = conn.execute('''UPDATE source_registry SET online_policy_status=%s,
          online_enabled=%s,policy_reference=%s,note=%s,policy_reviewed_at=now(),
          updated_at=now() WHERE source=%s RETURNING *''',
          (data.online_policy_status,data.online_enabled,data.policy_reference,data.note,source)).fetchone()
    return row


def candidates(status: str = 'pending', source: str | None = None, limit: int = 100):
    with session() as conn:
        return conn.execute('''SELECT * FROM collection_candidates WHERE review_status=%s
          AND (%s::text IS NULL OR source=%s) ORDER BY captured_at DESC LIMIT %s''',
          (status,source,source,limit)).fetchall()


def correct_candidate(candidate_id, data: CandidateCorrection):
    updates = data.model_dump(exclude_unset=True, exclude={'review_note'})
    if not updates:
        raise HTTPException(400, 'Specify at least one field to correct')
    with session() as conn:
        row = services.require_row(conn.execute('''SELECT * FROM collection_candidates
          WHERE id=%s FOR UPDATE''',(candidate_id,)).fetchone(), 'collection candidate')
        if row['review_status'] != 'pending':
            raise HTTPException(409,'Only pending candidates can be corrected')
        corrected_id = updates.get('source_listing_id')
        if corrected_id is not None:
            minimum_id_length = 8 if row['source'] == 'beike' else 7
            if len(corrected_id) < minimum_id_length:
                raise HTTPException(422, 'source_listing_id does not match source ID format')
        fields = dict(row['extracted_fields'])
        for key,value in updates.items():
            value = float(value) if isinstance(value, Decimal) else value
            fields[key] = value
            field_evidence = fields.get('field_evidence')
            if not isinstance(field_evidence, dict):
                field_evidence = {}
            field_evidence[key] = {'value': value, 'source': 'manual_review', 'mentions': [],
                                   'mention_count': 0, 'mentions_truncated': False}
            fields['field_evidence'] = field_evidence
        fields['manually_corrected'] = True
        resolved_precision_warnings = {
            f'numeric_precision_requires_correction:{key}' for key in updates
        }
        warnings = [warning for warning in row['warnings']
                    if warning not in resolved_precision_warnings]
        warnings.append('fields_corrected_by_operator')
        return conn.execute('''UPDATE collection_candidates SET extracted_fields=%s,
          warnings=%s,review_note=%s,source_listing_id=%s
          WHERE id=%s RETURNING *''',
          (Jsonb(fields),Jsonb(list(dict.fromkeys(warnings))),data.review_note,
           fields.get('source_listing_id'),candidate_id)).fetchone()


def review_candidate(candidate_id, decision: str, note: str):
    if decision not in ('approve','reject'):
        raise HTTPException(422, 'Decision must be approve or reject')
    if not note or len(note.strip()) < 5:
        raise HTTPException(422, 'Provide a review note (at least 5 characters)')
    # One DB transaction: candidate state, canonical listing and price history move together.
    with session() as conn:
        row = services.require_row(conn.execute('''SELECT * FROM collection_candidates
          WHERE id=%s FOR UPDATE''',(candidate_id,)).fetchone(),'collection candidate')
        if row['review_status'] == 'approved':
            if decision == 'approve':
                return {'candidate_id': candidate_id, 'status': 'approved',
                        'listing_id': row['approved_listing_id'], 'idempotent': True}
            raise HTTPException(409,'Cannot reject an already approved candidate')
        if row['review_status'] == 'rejected':
            raise HTTPException(409,'Rejected candidate cannot be re-reviewed')
        if decision == 'reject':
            updated = conn.execute('''UPDATE collection_candidates SET review_status='rejected',
                review_note=%s,reviewed_at=now() WHERE id=%s RETURNING id,review_status''',
                (note,candidate_id)).fetchone()
            return updated
        fields = row['extracted_fields']
        required = ('source_listing_id','community_name','area_sqm','asking_price_wan')
        missing = [k for k in required if fields.get(k) is None]
        if missing:
            raise HTTPException(409,{'reason':'Incomplete page extraction; correct candidate first',
                                     'missing':missing})
        precision_fields = [warning.rsplit(':', 1)[-1] for warning in row['warnings']
                            if warning.startswith('numeric_precision_requires_correction:')]
        if precision_fields:
            raise HTTPException(409,{
                'reason':'Numeric fields exceed database precision; correct candidate first',
                'fields':precision_fields,
            })
        try:
            payload = ListingIn(
                source=row['source'], source_listing_id=str(fields['source_listing_id']),
                community_name=fields['community_name'], district=fields.get('district'),
                title=fields.get('title'), listing_url=row['source_url'],
                area_sqm=fields['area_sqm'], bedrooms=fields.get('bedrooms'),
                floor_text=fields.get('floor_text'),decoration=fields.get('decoration'),
                asking_price_wan=fields['asking_price_wan'], observed_at=row['captured_at'],
                permission_note=f'collection_candidate:{candidate_id}; review={note[:200]}')
        except ValidationError as exc:
            invalid_fields = sorted({str(error['loc'][0]) for error in exc.errors() if error['loc']})
            raise HTTPException(409,{
                'reason':'Candidate fields are invalid; correct candidate first',
                'fields':invalid_fields,
            }) from exc
        result = services.upsert_listing_conn(conn,payload)
        listing_id = result['listing']['id']
        conn.execute('''UPDATE collection_candidates SET review_status='approved',
          approved_listing_id=%s,review_note=%s,reviewed_at=now()
          WHERE id=%s''',(listing_id,note,candidate_id))
        conn.execute('''UPDATE source_listings SET acquisition_method=%s,
          latest_candidate_id=%s,last_evidence_sha256=%s WHERE id=%s
          AND last_observed_at<=%s''',
          (row['capture_method'],candidate_id,row['raw_sha256'],listing_id,row['captured_at']))
        return {'candidate_id':candidate_id,'status':'approved','listing_id':listing_id,
                'listing_created':result['created'],'price_changed':result['price_changed']}


def create_target(data: CollectionTargetIn):
    try:
        check_source_url(data.source, data.url)
    except CollectionError as exc:
        raise HTTPException(422,str(exc)) from exc
    with session() as conn:
        return conn.execute('''INSERT INTO collection_targets(source,url,enabled,poll_interval_minutes)
          VALUES(%s,%s,%s,%s) ON CONFLICT(source,url) DO UPDATE SET
          enabled=EXCLUDED.enabled,poll_interval_minutes=EXCLUDED.poll_interval_minutes,
          updated_at=now() RETURNING *''',
          (data.source,data.url,data.enabled,data.poll_interval_minutes)).fetchone()


def get_targets():
    with session() as conn:
        return conn.execute('SELECT * FROM collection_targets ORDER BY created_at DESC').fetchall()


def _discovery_state(source, row=None):
    if row is None:
        return {'version': 1, 'revision': 0, 'source': source, 'seen_ids': [],
                'last_page_url': None, 'next_page_url': None, 'visited_page_urls': [],
                'last_attempted_page_url': None, 'last_error_type': None,
                'failed_attempts': 0, 'sweep_number': 0, 'sweep_active': False,
                'sweep_seen_ids': [], 'completed_sweeps': 0}
    return {'version': row['version'], 'revision': row['revision'], 'source': source,
            'seen_ids': row['seen_listing_ids'], 'last_page_url': row['last_page_url'],
            'next_page_url': row['next_page_url'],
            'visited_page_urls': row['visited_page_urls'],
            'last_attempted_page_url': row['last_attempted_page_url'],
            'last_error_type': row['last_error_type'],
            'failed_attempts': row['failed_attempts'],
            'sweep_number': row['sweep_number'], 'sweep_active': row['sweep_active'],
            'sweep_seen_ids': row['sweep_seen_listing_ids'],
            'completed_sweeps': row['completed_sweeps']}


def get_discovery_state(target_id, include_seen_ids=True):
    with session() as conn:
        target = conn.execute('SELECT source FROM collection_targets WHERE id=%s',
                              (target_id,)).fetchone()
        if target is None:
            raise HTTPException(404, 'Collection target not found')
        row = conn.execute('''SELECT * FROM collection_discovery_states WHERE target_id=%s''',
                           (target_id,)).fetchone()
        state = _discovery_state(target['source'], row)
        if not include_seen_ids:
            return state
        count = conn.execute('''SELECT count(*) AS total
          FROM collection_discovery_staged_ids WHERE target_id=%s''',
          (target_id,)).fetchone()['total']
        rows = conn.execute('''SELECT source_listing_id
          FROM collection_discovery_staged_ids WHERE target_id=%s
          ORDER BY source_listing_id LIMIT %s''',
          (target_id,MAX_DISCOVERY_STATE_IDS)).fetchall()
        sweep_seen_count = conn.execute('''SELECT count(*) AS total
          FROM collection_listing_observations
          WHERE target_id=%s AND last_seen_sweep=%s''',
          (target_id,state['sweep_number'])).fetchone()['total']
        sweep_rows = conn.execute('''SELECT source_listing_id
          FROM collection_listing_observations
          WHERE target_id=%s AND last_seen_sweep=%s
          ORDER BY last_seen_at,source_listing_id LIMIT %s''',
          (target_id,state['sweep_number'],MAX_DISCOVERY_STATE_IDS)).fetchall()
        pending_count = conn.execute('''SELECT count(*) AS total
          FROM collection_discovery_detail_queue WHERE target_id=%s''',
          (target_id,)).fetchone()['total']
        pending_rows = conn.execute('''SELECT source_listing_id,listing_url,
              attempt_count,last_attempt_at,last_error_type
          FROM collection_discovery_detail_queue WHERE target_id=%s
          ORDER BY last_attempt_at NULLS FIRST,queued_at,source_listing_id LIMIT 100''',
          (target_id,)).fetchall()
    ids = _bounded_state_ids(rows)
    sweep_ids = _bounded_state_ids(sweep_rows)
    state['seen_ids'] = ids
    state['seen_ids_count'] = count
    state['seen_ids_truncated'] = len(ids) < count
    state['sweep_seen_ids'] = sweep_ids
    state['sweep_seen_ids_count'] = sweep_seen_count
    state['sweep_seen_ids_truncated'] = len(sweep_ids) < sweep_seen_count
    state['pending_detail_urls'] = pending_rows
    state['pending_detail_urls_count'] = pending_count
    state['pending_detail_urls_truncated'] = len(pending_rows) < pending_count
    return state


def _bounded_state_ids(rows):
    ids = []
    size = 2
    for item in rows:
        encoded_size = len(json.dumps(item['source_listing_id'], ensure_ascii=False).encode('utf-8'))
        next_size = size + encoded_size + (1 if ids else 0)
        if next_size > MAX_DISCOVERY_STATE_ID_BYTES:
            break
        ids.append(item['source_listing_id'])
        size = next_size
    return ids


def save_discovery_state(target_id, data: DiscoveryStateIn):
    _validate_discovery_state_urls(data)

    with session() as conn:
        return _save_discovery_state_conn(conn,target_id,data)


def _validate_discovery_state_urls(data):
    state = data.model_dump()
    state_json = json.dumps(state, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    if len(state_json) > 2_000_000:
        raise HTTPException(413, 'Discovery state exceeds 2000000 byte limit')
    for page_url in (data.last_page_url, data.next_page_url,
                     data.last_attempted_page_url, *data.visited_page_urls):
        if page_url is not None:
            try:
                check_source_url(data.source, page_url)
            except CollectionError as exc:
                raise HTTPException(422, str(exc)) from exc
    if data.next_page_url:
        next_page_key = source_page_key(data.source, data.next_page_url)
        if any(source_page_key(data.source, page_url) == next_page_key
               for page_url in data.visited_page_urls):
            raise HTTPException(422, 'next_page_url must not point to a visited page')

def _save_discovery_state_conn(conn, target_id, data):
    state = data.model_dump()
    target = conn.execute('''SELECT source FROM collection_targets WHERE id=%s FOR UPDATE''',
                          (target_id,)).fetchone()
    if target is None:
        raise HTTPException(404, 'Collection target not found')
    if target['source'] != data.source:
        raise HTTPException(422, 'Discovery state source does not match target source')
    current = conn.execute('''SELECT revision FROM collection_discovery_states
      WHERE target_id=%s FOR UPDATE''', (target_id,)).fetchone()
    current_revision = current['revision'] if current else 0
    if data.revision != current_revision:
        raise HTTPException(409, 'Discovery state revision is stale')
    revision = current_revision + 1
    conn.execute('''INSERT INTO collection_discovery_staged_ids (target_id,source_listing_id)
      SELECT %s, source_listing_id FROM unnest(%s::text[]) AS input(source_listing_id)
      ON CONFLICT (target_id,source_listing_id) DO NOTHING''',
      (target_id,data.seen_ids))
    conn.execute('''INSERT INTO collection_discovery_states
      (target_id,revision,version,seen_listing_ids,last_page_url,next_page_url,
       visited_page_urls,last_attempted_page_url,last_error_type,failed_attempts,
       sweep_number,sweep_active,sweep_seen_listing_ids,completed_sweeps,updated_at)
      VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now())
      ON CONFLICT(target_id) DO UPDATE SET revision=EXCLUDED.revision,
        version=EXCLUDED.version,seen_listing_ids=EXCLUDED.seen_listing_ids,
        last_page_url=EXCLUDED.last_page_url,next_page_url=EXCLUDED.next_page_url,
        visited_page_urls=EXCLUDED.visited_page_urls,
        last_attempted_page_url=EXCLUDED.last_attempted_page_url,
        last_error_type=EXCLUDED.last_error_type,
        failed_attempts=EXCLUDED.failed_attempts,sweep_number=EXCLUDED.sweep_number,
        sweep_active=EXCLUDED.sweep_active,
        sweep_seen_listing_ids=EXCLUDED.sweep_seen_listing_ids,
        completed_sweeps=EXCLUDED.completed_sweeps,updated_at=now()''',
      (target_id,revision,data.version,Jsonb([]),data.last_page_url,
       data.next_page_url,Jsonb(data.visited_page_urls),data.last_attempted_page_url,
       data.last_error_type,data.failed_attempts,data.sweep_number,data.sweep_active,
       Jsonb([]),data.completed_sweeps))
    return {**state, 'revision': revision}


def update_target(target_id, data: CollectionTargetPatch):
    edits=data.model_dump(exclude_unset=True)
    if not edits:
        raise HTTPException(400,'No changes specified')
    setters=[]; params=[]
    for key in ('enabled','poll_interval_minutes'):
        if key in edits:
            setters.append(f'{key}=%s');params.append(edits[key])
    if edits.get('enabled') is True:
        setters.append('next_check_at=now()')
    setters.append('updated_at=now()');params.append(target_id)
    with session() as conn:
        row=conn.execute('UPDATE collection_targets SET '+','.join(setters)+
                         ' WHERE id=%s RETURNING *',params).fetchone()
        return services.require_row(row,'collection target')


def request_target_check(target_id):
    with session() as conn:
        return services.require_row(conn.execute('''UPDATE collection_targets
          SET next_check_at=now() WHERE id=%s RETURNING *''',(target_id,)).fetchone(),
          'collection target')


def recent_collection_runs(target_id=None, limit=30):
    with session() as conn:
        return conn.execute('''SELECT * FROM collection_runs
          WHERE (%s::uuid IS NULL OR target_id=%s)
          ORDER BY started_at DESC LIMIT %s''',(target_id,target_id,limit)).fetchall()


def discovery_observations(source=None, target_id=None, review_status=None,
                           limit=100, offset=0):
    with session() as conn:
        return conn.execute('''SELECT target_id,source,source_listing_id,listing_url,
          first_seen_at,last_seen_at,observation_count,first_page_url,last_page_url,
          first_page_sha256,last_page_sha256,first_page_storage_path,last_page_storage_path,
          missed_complete_scans,review_status,
          latest_review.conclusion AS latest_review_conclusion,
          latest_review.note AS latest_review_note,
          latest_review.reviewed_at AS latest_reviewed_at
          FROM collection_listing_observations o
          LEFT JOIN LATERAL (
            SELECT conclusion,note,reviewed_at FROM collection_listing_reviews r
            WHERE r.target_id=o.target_id AND r.source=o.source
              AND r.source_listing_id=o.source_listing_id
            ORDER BY reviewed_at DESC,id DESC LIMIT 1
          ) latest_review ON TRUE
          WHERE (%s::text IS NULL OR source=%s)
            AND (%s::uuid IS NULL OR target_id=%s)
            AND (%s::text IS NULL OR review_status=%s)
          ORDER BY CASE WHEN review_status='pending_review' THEN 0
                        WHEN review_status='reviewed' THEN 1 ELSE 2 END,
            last_seen_at DESC,source,source_listing_id
          LIMIT %s OFFSET %s''',
          (source,source,target_id,target_id,review_status,review_status,limit,offset)).fetchall()


def record_discovery_review(target_id, source_listing_id, data: DiscoveryReviewIn):
    with session() as conn:
        observation = conn.execute('''SELECT source,review_status
          FROM collection_listing_observations
          WHERE target_id=%s AND source_listing_id=%s FOR UPDATE''',
          (target_id,source_listing_id)).fetchone()
        if observation is None:
            raise HTTPException(404, 'Discovery observation not found')
        if observation['review_status'] != 'pending_review':
            raise HTTPException(409, 'Discovery observation is not pending review')
        row = conn.execute('''INSERT INTO collection_listing_reviews
          (target_id,source,source_listing_id,conclusion,note)
          VALUES(%s,%s,%s,%s,%s)
          RETURNING id,target_id,source,source_listing_id,conclusion,note,reviewed_at''',
          (target_id,observation['source'],source_listing_id,
           data.conclusion,data.note)).fetchone()
        conn.execute('''UPDATE collection_listing_observations
          SET review_status='reviewed'
          WHERE target_id=%s AND source=%s AND source_listing_id=%s''',
          (target_id,observation['source'],source_listing_id))
    return {**row, 'review_status': 'reviewed'}


def discovery_reviews(target_id, source_listing_id, limit=50, offset=0):
    with session() as conn:
        observation = conn.execute('''SELECT 1 FROM collection_listing_observations
          WHERE target_id=%s AND source_listing_id=%s''',
          (target_id,source_listing_id)).fetchone()
        if observation is None:
            raise HTTPException(404, 'Discovery observation not found')
        return conn.execute('''SELECT id,target_id,source,source_listing_id,
          conclusion,note,reviewed_at FROM collection_listing_reviews
          WHERE target_id=%s AND source_listing_id=%s
          ORDER BY reviewed_at DESC,id DESC LIMIT %s OFFSET %s''',
          (target_id,source_listing_id,limit,offset)).fetchall()


def claim_due_target():
    with session() as conn:
        row=conn.execute('''SELECT t.* FROM collection_targets t
          JOIN source_registry s ON s.source=t.source
          WHERE t.enabled AND t.next_check_at<=now()
          ORDER BY t.next_check_at LIMIT 1 FOR UPDATE OF t SKIP LOCKED''').fetchone()
        if row:
            conn.execute('''UPDATE collection_targets SET
              next_check_at=now()+poll_interval_minutes * interval '1 minute',
              last_attempt_at=now(),updated_at=now() WHERE id=%s''',(row['id'],))
        return row


def _save_target_discovery_state(target_id, state):
    payload = DiscoveryStateIn(**state)
    saved = save_discovery_state(target_id, payload)
    state['revision'] = saved['revision']
    return state


def _finish_discovery_sweep(target_id, state):
    state['completed_sweeps'] += 1
    state['sweep_active'] = False
    payload = DiscoveryStateIn(**state)
    _validate_discovery_state_urls(payload)
    with session() as conn:
        saved = _save_discovery_state_conn(conn,target_id,payload)
        conn.execute('''UPDATE collection_listing_observations SET
          missed_complete_scans=LEAST(missed_complete_scans+1,2),
          last_evaluated_sweep=%s,
          review_status=CASE WHEN missed_complete_scans+1>=2
            THEN 'pending_review' ELSE review_status END
          WHERE target_id=%s AND source=%s AND last_seen_sweep<%s
            AND last_evaluated_sweep<%s''',
          (state['sweep_number'],target_id,state['source'],
           state['sweep_number'],state['sweep_number']))
    state['revision'] = saved['revision']
    return state


def _require_online_policy(source):
    if not ENABLE_ONLINE_COLLECTION:
        raise CollectionBlocked('Online collection disabled or source permission is not approved',
                                'blocked_policy')
    with session() as conn:
        policy = conn.execute('''SELECT online_enabled,online_policy_status,policy_reference
          FROM source_registry WHERE source=%s''', (source,)).fetchone()
    if not policy or not may_fetch_online(
            global_enabled=ENABLE_ONLINE_COLLECTION,
            source_enabled=policy['online_enabled'],
            policy_status=policy['online_policy_status'],
            policy_reference=policy['policy_reference']):
        raise CollectionBlocked('Online collection disabled or source permission is not approved',
                                'blocked_policy')


def _fetch_approved_html(source, url):
    _require_online_policy(source)
    return fetch_public_html(source, url,
                             min_delay_seconds=COLLECTION_MIN_DELAY_SECONDS,
                             before_page_request=lambda: _require_online_policy(source))


def _record_target_discovery_failure(target_id, state, page_url, error):
    page_key = source_page_key(state['source'], page_url)
    visited = state['visited_page_urls']
    visited_index = next((index for index, value in enumerate(visited)
                          if source_page_key(state['source'], value) == page_key), None)
    if visited_index is not None:
        # Rewind from this page so its failed detail is retried before later pages.
        state['visited_page_urls'] = visited[:visited_index]
        state['last_page_url'] = (state['visited_page_urls'][-1]
                                  if state['visited_page_urls'] else None)
    state['next_page_url'] = page_url
    state['last_attempted_page_url'] = page_url
    state['last_error_type'] = type(error).__name__
    state['failed_attempts'] += 1
    _save_target_discovery_state(target_id, state)


def _staged_listing_ids(target_id, listing_ids):
    if not listing_ids:
        return set()
    with session() as conn:
        rows = conn.execute('''SELECT source_listing_id FROM collection_discovery_staged_ids
          WHERE target_id=%s AND source_listing_id=ANY(%s::text[])''',
          (target_id,list(listing_ids))).fetchall()
    return {row['source_listing_id'] for row in rows}


def _mark_discovery_listing_staged(target_id, source_listing_id):
    with session() as conn:
        row = conn.execute('''INSERT INTO collection_discovery_staged_ids
          (target_id,source_listing_id) VALUES(%s,%s)
          ON CONFLICT (target_id,source_listing_id) DO NOTHING
          RETURNING source_listing_id''', (target_id,source_listing_id)).fetchone()
    return row is not None


def _enqueue_discovery_listings(target, page_url, listings):
    if not listings:
        return
    with session() as conn:
        for listing in listings:
            conn.execute('''INSERT INTO collection_discovery_detail_queue
              (target_id,source,source_listing_id,listing_url,discovered_page_url)
              VALUES(%s,%s,%s,%s,%s)
              ON CONFLICT(target_id,source_listing_id) DO UPDATE SET
                listing_url=EXCLUDED.listing_url,
                discovered_page_url=EXCLUDED.discovered_page_url,last_seen_at=now()''',
              (target['id'],target['source'],listing.source_listing_id,
               listing.url,page_url))


def _next_discovery_queue_item(target_id, attempted_ids):
    with session() as conn:
        return conn.execute('''SELECT source_listing_id,listing_url
          FROM collection_discovery_detail_queue WHERE target_id=%s
            AND NOT (source_listing_id=ANY(%s::text[]))
          ORDER BY last_attempt_at NULLS FIRST,queued_at,source_listing_id LIMIT 1''',
          (target_id,sorted(attempted_ids))).fetchone()


def _delete_discovery_queue_item(target_id, source_listing_id):
    with session() as conn:
        conn.execute('''DELETE FROM collection_discovery_detail_queue
          WHERE target_id=%s AND source_listing_id=%s''',
          (target_id,source_listing_id))


def _record_discovery_queue_failure(target_id, source_listing_id, error):
    with session() as conn:
        conn.execute('''UPDATE collection_discovery_detail_queue SET
          attempt_count=attempt_count+1,last_attempt_at=now(),last_error_type=%s
          WHERE target_id=%s AND source_listing_id=%s''',
          (type(error).__name__,target_id,source_listing_id))


def _drain_discovery_detail_queue(target, state, page_url, attempted_ids, limit):
    attempted_count=staged_count=failed_count=0
    while attempted_count < limit:
        item = _next_discovery_queue_item(target['id'],attempted_ids)
        if item is None:
            break
        listing_id = item['source_listing_id']
        staged_ids = _staged_listing_ids(target['id'],{listing_id})
        if staged_ids is None:
            staged_ids = set(state['seen_ids'])
        if listing_id in staged_ids:
            _delete_discovery_queue_item(target['id'],listing_id)
            attempted_ids.add(listing_id)
            continue
        try:
            detail_html = _fetch_approved_html(target['source'],item['listing_url'])
            stage_html(target['source'],item['listing_url'],detail_html,
                       'public_page_collection')
            recorded = _mark_discovery_listing_staged(target['id'],listing_id)
            if recorded is False:
                state['seen_ids'] = sorted(set(state['seen_ids']) | {listing_id})
            _delete_discovery_queue_item(target['id'],listing_id)
            staged_count+=1
        except CollectionBlocked as exc:
            if exc.category != 'blocked_policy':
                _record_discovery_queue_failure(target['id'],listing_id,exc)
                _record_target_discovery_failure(target['id'],state,page_url,exc)
            else:
                state['next_page_url']=page_url
                state['last_attempted_page_url']=page_url
                state['last_error_type']=None
                _save_target_discovery_state(target['id'],state)
            return attempted_count,staged_count,failed_count,exc
        except Exception as exc:
            _record_discovery_queue_failure(target['id'],listing_id,exc)
            failed_count+=1
        attempted_count+=1
        attempted_ids.add(listing_id)
    return attempted_count,staged_count,failed_count,None


def _record_listing_observations(target, state, page_url, html, listings):
    page_sha256 = hashlib.sha256(html.encode('utf-8')).hexdigest()
    page_storage_path = _save_html(page_sha256, html)
    with session() as conn:
        for listing in listings:
            conn.execute('''INSERT INTO collection_listing_observations
              (target_id,source,source_listing_id,listing_url,first_page_url,last_page_url,
               first_page_sha256,last_page_sha256,first_page_storage_path,last_page_storage_path,
               last_seen_sweep)
              VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
              ON CONFLICT(target_id,source,source_listing_id) DO UPDATE SET
                listing_url=EXCLUDED.listing_url,last_seen_at=now(),
                observation_count=collection_listing_observations.observation_count+1,
                last_page_url=EXCLUDED.last_page_url,
                last_page_sha256=EXCLUDED.last_page_sha256,
                last_page_storage_path=EXCLUDED.last_page_storage_path,
                last_seen_sweep=EXCLUDED.last_seen_sweep,missed_complete_scans=0,
                review_status=CASE
                  WHEN collection_listing_observations.review_status='pending_review'
                    THEN 'pending_review' ELSE 'active' END''',
              (target['id'],target['source'],listing.source_listing_id,listing.url,
               page_url,page_url,page_sha256,page_sha256,page_storage_path,page_storage_path,
               state['sweep_number']))


def _run_discovery_target(target):
    state = get_discovery_state(target['id'], include_seen_ids=False)
    state.setdefault('sweep_number', 0)
    state.setdefault('sweep_active', False)
    state.setdefault('sweep_seen_ids', [])
    state.setdefault('completed_sweeps', 0)
    if not state['sweep_active']:
        state['sweep_number'] += 1
        state['sweep_active'] = True
        state['sweep_seen_ids'] = []
        state['visited_page_urls'] = []
        state['last_page_url'] = None
        state['next_page_url'] = None
    page_url = state['next_page_url'] or target['url']
    first_page_url = page_url
    staged_count = 0
    detail_attempts = 0
    detail_failures = 0
    page_count = 0
    discovered_count = 0
    warnings = []
    attempted_ids = set()
    detail_attempts, staged_count, detail_failures, blocked = (
        _drain_discovery_detail_queue(
            target,state,page_url,attempted_ids,MAX_DISCOVERY_DETAILS_PER_RUN))
    if blocked:
        status = blocked.category
        note = safe_error_summary(blocked,'collection detail')
        note += f'; details_staged={staged_count}; detail_failures={detail_failures}'
        return status,blocked.http_status,note,None,first_page_url

    while (page_url and page_count < MAX_DISCOVERY_PAGES_PER_RUN
           and detail_attempts < MAX_DISCOVERY_DETAILS_PER_RUN):
        try:
            html = _fetch_approved_html(target['source'], page_url)
            discovery = discover_listing_links(
                target['source'], page_url, html, set())
        except Exception as exc:
            if not (isinstance(exc, CollectionBlocked) and exc.category == 'blocked_policy'):
                _record_target_discovery_failure(target['id'], state, page_url, exc)
            status = exc.category if isinstance(exc, CollectionBlocked) else 'failed'
            http_status = exc.http_status if isinstance(exc, CollectionBlocked) else None
            return (status, http_status,
                    safe_error_summary(exc, 'collection discovery'), None, first_page_url)

        if discovery.observed_listings:
            _record_listing_observations(target,state,page_url,html,
                                         discovery.observed_listings)

        listing_ids = {item.source_listing_id for item in discovery.listings}
        staged_ids = _staged_listing_ids(target['id'], listing_ids)
        if staged_ids is None:
            staged_ids = set(state['seen_ids'])
        new_listings = [item for item in discovery.listings
                        if item.source_listing_id not in staged_ids]
        discovered_count += len(new_listings)
        _enqueue_discovery_listings(target,page_url,new_listings)
        remaining = MAX_DISCOVERY_DETAILS_PER_RUN - detail_attempts
        attempts, added, failures, blocked = _drain_discovery_detail_queue(
            target,state,page_url,attempted_ids,remaining)
        detail_attempts += attempts
        staged_count += added
        detail_failures += failures
        if blocked:
            status = blocked.category
            note = safe_error_summary(blocked,'collection detail')
            note += f'; details_staged={staged_count}; detail_failures={detail_failures}'
            return status,blocked.http_status,note,None,first_page_url

        state['last_attempted_page_url'] = page_url
        state['last_error_type'] = None
        page_key = source_page_key(target['source'], page_url)
        if all(source_page_key(target['source'], old_url) != page_key
               for old_url in state['visited_page_urls']):
            state['visited_page_urls'].append(page_url)
        state['last_page_url'] = page_url
        next_page_url = discovery.next_page_url
        if next_page_url and any(
                source_page_key(target['source'], old_url)
                == source_page_key(target['source'], next_page_url)
                for old_url in state['visited_page_urls']):
            next_page_url = None
            warnings.append('pagination_loop')
        state['next_page_url'] = next_page_url
        state = _save_target_discovery_state(target['id'], state)
        page_count += 1
        warnings.extend(discovery.warnings)
        page_url = next_page_url
        if detail_attempts >= MAX_DISCOVERY_DETAILS_PER_RUN:
            break

    note = f'pages={page_count}; details_staged={staged_count}; listings_discovered={discovered_count}'
    if page_url and page_count >= MAX_DISCOVERY_PAGES_PER_RUN:
        note += '; page_limit_reached'
    if page_url and detail_attempts >= MAX_DISCOVERY_DETAILS_PER_RUN:
        note += '; detail_limit_reached'
    if state['next_page_url'] == first_page_url and page_count == 0:
        note += '; list_page_retained'
    if warnings:
        note += '; warnings=' + ','.join(warnings)
    if page_url is None:
        if warnings:
            state['sweep_active'] = False
            _save_target_discovery_state(target['id'], state)
            note += '; sweep_incomplete'
        else:
            state = _finish_discovery_sweep(target['id'], state)
            note += '; sweep_complete'
    if detail_failures:
        note += f'; detail_failures={detail_failures}'
        return 'failed',None,note,None,first_page_url
    return 'success', 200, note, None, first_page_url


def run_collection_target(target):
    status='failed'; http_status=None; error=None; candidate_id=None
    run_url=target['url']
    if not ENABLE_ONLINE_COLLECTION:
        status='blocked_policy'
        error='Online collection disabled or source permission is not approved'
    else:
        try:
            if extract_source_id(target['source'], target['url']):
                html=_fetch_approved_html(target['source'], target['url'])
                staged=stage_html(target['source'],target['url'],html,
                                  'public_page_collection')
                candidate_id=staged['candidate']['id'];status='success';http_status=200
            else:
                status,http_status,error,candidate_id,run_url=_run_discovery_target(target)
        except CollectionBlocked as exc:
            status=exc.category;http_status=exc.http_status;error=str(exc)
        except Exception as exc:
            status='failed';error=safe_error_summary(exc,'collection')
            log.error('collection target failed, id=%s, %s',target['id'],error)
    with session() as conn:
        conn.execute('''INSERT INTO collection_runs(target_id,source,source_url,status,
          http_status,candidate_id,note) VALUES(%s,%s,%s,%s,%s,%s,%s)''',
          (target['id'],target['source'],run_url,status,http_status,candidate_id,error))
        conn.execute('''UPDATE collection_targets SET last_status=%s,last_error=%s,
          enabled=CASE WHEN %s IN ('blocked_robots','blocked_upstream') THEN FALSE ELSE enabled END,
          updated_at=now() WHERE id=%s''',(status,error,status,target['id']))
    return status
