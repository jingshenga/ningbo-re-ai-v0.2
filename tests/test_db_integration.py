"""PostgreSQL-backed API checks. Set TEST_DATABASE_URL to an isolated rehouse_test DB."""
import os
import json
import gzip
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from psycopg import sql
from psycopg.rows import dict_row
from app import collection_service
from app.collectors.parser import PARSER_VERSION
from scripts.storage_report import evidence_reference_summary


DATABASE_URL = os.getenv('TEST_DATABASE_URL')
if DATABASE_URL and conninfo_to_dict(DATABASE_URL).get('dbname') != 'rehouse_test':
    pytest.fail('TEST_DATABASE_URL must point to the dedicated rehouse_test database')


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / 'fixtures' / 'beike_demo.html').read_text()
BASE_URL = 'https://nb.ke.com/ershoufang/109900001234.html'
API_KEY = 'integration-test-key'


def connect_test_db(conninfo, **kwargs):
    try:
        kwargs.setdefault('row_factory', dict_row)
        return psycopg.connect(conninfo, **kwargs)
    except psycopg.Error as exc:
        state = f' (SQLSTATE {exc.sqlstate})' if exc.sqlstate else ''
        raise RuntimeError(f'Cannot connect to isolated PostgreSQL test database{state}; details redacted') from None


def test_connection_errors_do_not_disclose_conninfo(monkeypatch):
    secret = 'test-password-must-not-appear'

    def fail_connect(*args, **kwargs):
        raise psycopg.OperationalError(f'connection failed for password={secret}')

    monkeypatch.setattr(psycopg, 'connect', fail_connect)
    with pytest.raises(RuntimeError) as err:
        connect_test_db(f'postgresql://test:{secret}@127.0.0.1:1/rehouse_test')
    assert secret not in str(err.value)
    assert 'details redacted' in str(err.value)


def test_source_policy_share_lock_blocks_concurrent_revocation(api):
    _, scoped_url = api
    with connect_test_db(scoped_url) as reader, connect_test_db(scoped_url) as writer:
        reader.execute('SELECT source FROM source_registry WHERE source=%s FOR SHARE',
                       ('beike',)).fetchone()
        with pytest.raises(psycopg.errors.LockNotAvailable):
            with writer.transaction():
                writer.execute("SET LOCAL lock_timeout = '100ms'")
                writer.execute('''UPDATE source_registry SET online_policy_status='revoked',
                  online_enabled=FALSE WHERE source=%s''', ('beike',))

        reader.rollback()
        writer.execute('''UPDATE source_registry SET online_policy_status='revoked',
          online_enabled=FALSE WHERE source=%s''', ('beike',))
        state = writer.execute('''SELECT online_policy_status,online_enabled
          FROM source_registry WHERE source=%s''', ('beike',)).fetchone()
        assert state == {'online_policy_status': 'revoked', 'online_enabled': False}


@pytest.fixture
def api(tmp_path, monkeypatch):
    if not DATABASE_URL:
        pytest.skip('Set TEST_DATABASE_URL to run PostgreSQL integration tests')
    schema = 'it_' + uuid4().hex
    created = False
    try:
        with connect_test_db(DATABASE_URL, autocommit=True) as conn:
            conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
        created = True
        scoped_url = make_conninfo(DATABASE_URL, options=f'-csearch_path={schema}')
        monkeypatch.setattr('app.db.DATABASE_URL', scoped_url)
        monkeypatch.setattr('app.collection_service.RAW_HTML_DIR', str(tmp_path / 'raw-pages'))
        monkeypatch.setattr('app.main.APP_API_KEY', API_KEY)
        with connect_test_db(scoped_url, autocommit=True) as conn:
            conn.execute((ROOT / 'sql' / '001_init.sql').read_text())
            conn.execute((ROOT / 'sql' / '002_collection_pipeline.sql').read_text())
            health_indexes = (ROOT / 'sql' / '003_collection_health_indexes.sql').read_text()
            conn.execute(health_indexes)
            conn.execute(health_indexes)
            health_metrics = (ROOT / 'sql' / '004_collection_health_metrics.sql').read_text()
            conn.execute(health_metrics)
            conn.execute(health_metrics)
            saved_search_filters = (ROOT / 'sql' / '005_saved_search_filters.sql').read_text()
            conn.execute(saved_search_filters)
            conn.execute(saved_search_filters)
            discovery_state = (ROOT / 'sql' / '006_collection_discovery_state.sql').read_text()
            conn.execute(discovery_state)
            conn.execute(discovery_state)
            listing_observations = (ROOT / 'sql' / '007_collection_listing_observations.sql').read_text()
            conn.execute(listing_observations)
            conn.execute(listing_observations)
            discovery_sweeps = (ROOT / 'sql' / '008_collection_discovery_sweeps.sql').read_text()
            conn.execute(discovery_sweeps)
            conn.execute(discovery_sweeps)
            listing_reviews = (ROOT / 'sql' / '009_collection_listing_reviews.sql').read_text()
            conn.execute(listing_reviews)
            conn.execute(listing_reviews)
            parse_metrics = (ROOT / 'sql' / '010_collection_parse_metrics.sql').read_text()
            conn.execute(parse_metrics)
            conn.execute(parse_metrics)
            parse_attempt_guards = (ROOT / 'sql' / '011_parse_attempts_append_only.sql').read_text()
            conn.execute(parse_attempt_guards)
            conn.execute(parse_attempt_guards)
            staged_ids = (ROOT / 'sql' / '012_collection_discovery_staged_ids.sql').read_text()
            conn.execute(staged_ids)
            conn.execute(staged_ids)
            history_cursor = (ROOT / 'sql' / '013_account_history_backfill_cursor.sql').read_text()
            conn.execute(history_cursor)
            conn.execute(history_cursor)
            detail_queue = (ROOT / 'sql' / '014_collection_detail_queue.sql').read_text()
            conn.execute(detail_queue)
            conn.execute(detail_queue)
        from app.main import app
        with TestClient(app, raise_server_exceptions=False) as client:
            yield client, scoped_url
    finally:
        if created:
            with connect_test_db(DATABASE_URL, autocommit=True) as conn:
                conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))


def test_v01_schema_migration_preserves_existing_data():
    if not DATABASE_URL:
        pytest.skip('Set TEST_DATABASE_URL to run PostgreSQL integration tests')
    schema = 'upgrade_' + uuid4().hex
    created = False
    try:
        with connect_test_db(DATABASE_URL, autocommit=True) as conn:
            conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
        created = True
        scoped_url = make_conninfo(DATABASE_URL, options=f'-csearch_path={schema}')
        with connect_test_db(scoped_url, autocommit=True) as conn:
            conn.execute((ROOT / 'sql' / '001_init.sql').read_text())
            account_id = conn.execute('''INSERT INTO monitored_accounts
              (platform,account_ref,nickname,collector_mode,history_mode,poll_interval_minutes,
               enabled,initial_synced,last_status)
              VALUES('douyin','legacy-account-001','Legacy creator','manual','30d',240,
               FALSE,TRUE,'success')
              RETURNING id''').fetchone()['id']
            conn.execute('''INSERT INTO account_sync_runs
              (account_id,status,pages,observed_count,new_count,error_text)
              VALUES(%s,'partial',3,17,4,'legacy warning')''', (account_id,))
            conn.execute('''INSERT INTO account_seen_posts
              (platform,source_post_id,account_id,baseline_only)
              VALUES('douyin','legacy-post-001',%s,TRUE)''', (account_id,))
            video_id = conn.execute('''INSERT INTO videos
              (account_id,platform,source_post_id,source_url,author_name,title,description,
               transcript,ocr_text,extracted_fields,processing_status,raw_location,permission_note)
              VALUES(%s,'douyin','legacy-post-001','https://www.douyin.com/video/legacy-post-001',
               'Legacy creator','Legacy title','Legacy description','Legacy transcript','Legacy OCR',
               '{"district":"鄞州"}'::jsonb,'enriched','鄞州','user-provided') RETURNING id''',
              (account_id,)).fetchone()['id']
            community_id = conn.execute('''INSERT INTO communities
              (city,name,district,address,latitude,longitude,verified)
              VALUES('宁波','V0.1 migration fixture','鄞州','Legacy address',29.82,121.55,TRUE)
              RETURNING id''').fetchone()['id']
            conn.execute('''INSERT INTO community_aliases(alias,community_id)
              VALUES('V0.1 migration alias',%s)''', (community_id,))
            property_id = conn.execute('''INSERT INTO properties
              (community_id,area_sqm,bedrooms,floor_text,layout_note,decoration,building_info,identity_status)
              VALUES(%s,100,2,'中层','南北通透','精装','2幢','verified') RETURNING id''',
              (community_id,)).fetchone()['id']
            listing_id = conn.execute('''INSERT INTO source_listings
              (source,source_listing_id,property_id,title,listing_url,asking_price_wan,
               first_observed_at,last_observed_at,status,permission_note)
              VALUES('beike','legacy-listing-001',%s,'Legacy listing',
               'https://nb.ke.com/ershoufang/legacy-listing-001.html',320,now(),now(),
               'available','legacy permission note') RETURNING id''',
              (property_id,)).fetchone()['id']
            conn.execute('''INSERT INTO price_history
              (listing_id,price_wan,observed_at,quote_type,evidence_url)
              VALUES(%s,330,now()-interval '1 day','agent_claim','https://evidence.example/legacy')''',
              (listing_id,))
            conn.execute('''INSERT INTO property_matches
              (video_id,listing_id,match_score,evidence,status)
              VALUES(%s,%s,75,'{"source":"legacy"}'::jsonb,'confirmed')''',
              (video_id,listing_id))
            search_id = conn.execute('''INSERT INTO saved_searches
              (name,district,community_name,max_price_wan,min_area_sqm,min_bedrooms,
               min_drop_pct,notifications_enabled)
              VALUES('Legacy search','鄞州','V0.1 migration fixture',350,80,2,7,FALSE)
              RETURNING id''').fetchone()['id']
            conn.execute('''INSERT INTO notification_logs(search_id,listing_id,event_key,event_type)
              VALUES(%s,%s,'legacy-event','new_listing')''', (search_id,listing_id))
            conn.execute('''UPDATE notification_logs SET payload='{"legacy":true}'::jsonb,
              delivery_status='read' WHERE event_key='legacy-event' ''')

            migration = (ROOT / 'sql' / '002_collection_pipeline.sql').read_text()
            conn.execute(migration)
            conn.execute(migration)
            for name in (
                '003_collection_health_indexes.sql',
                '004_collection_health_metrics.sql',
                '005_saved_search_filters.sql',
                '006_collection_discovery_state.sql',
                '007_collection_listing_observations.sql',
                '008_collection_discovery_sweeps.sql',
                '009_collection_listing_reviews.sql',
                '010_collection_parse_metrics.sql',
                '011_parse_attempts_append_only.sql',
                '012_collection_discovery_staged_ids.sql',
                '013_account_history_backfill_cursor.sql',
                '014_collection_detail_queue.sql',
            ):
                migration = (ROOT / 'sql' / name).read_text()
                conn.execute(migration)
                conn.execute(migration)

            listing = conn.execute('''SELECT source_listing_id,title,listing_url,asking_price_wan,
                status,permission_note,acquisition_method,latest_candidate_id,last_evidence_sha256
                FROM source_listings WHERE id=%s''',
                (listing_id,)).fetchone()
            assert listing == {
                'source_listing_id': 'legacy-listing-001',
                'title': 'Legacy listing',
                'listing_url': 'https://nb.ke.com/ershoufang/legacy-listing-001.html',
                'asking_price_wan': 320,
                'status': 'available',
                'permission_note': 'legacy permission note',
                'acquisition_method': 'manual_import',
                'latest_candidate_id': None,
                'last_evidence_sha256': None,
            }
            preserved_v01_tables = (
                'monitored_accounts', 'account_sync_runs', 'account_seen_posts', 'videos',
                'communities', 'community_aliases', 'properties', 'price_history',
                'property_matches', 'saved_searches', 'notification_logs',
            )
            for table in preserved_v01_tables:
                count = conn.execute(sql.SQL('SELECT count(*) AS count FROM {}').format(
                    sql.Identifier(table))).fetchone()['count']
                assert count == 1, table
            preserved_values = {
                'account': conn.execute('''SELECT account_ref,nickname,history_mode,
                  poll_interval_minutes,enabled,initial_synced,last_status
                  FROM monitored_accounts WHERE id=%s''', (account_id,)).fetchone(),
                'sync_run': conn.execute('''SELECT status,pages,observed_count,new_count,error_text
                  FROM account_sync_runs WHERE account_id=%s''', (account_id,)).fetchone(),
                'seen_post': conn.execute('''SELECT baseline_only FROM account_seen_posts
                  WHERE source_post_id='legacy-post-001' ''').fetchone(),
                'video': conn.execute('''SELECT source_url,author_name,title,description,transcript,
                  ocr_text,extracted_fields,processing_status,raw_location,permission_note
                  FROM videos WHERE id=%s''', (video_id,)).fetchone(),
                'community': conn.execute('''SELECT city,district,address,latitude::text AS latitude,
                  longitude::text AS longitude,verified
                  FROM communities WHERE id=%s''', (community_id,)).fetchone(),
                'alias': conn.execute('''SELECT city,alias FROM community_aliases
                  WHERE community_id=%s''', (community_id,)).fetchone(),
                'property': conn.execute('''SELECT area_sqm,bedrooms,floor_text,layout_note,
                  decoration,building_info,identity_status FROM properties WHERE id=%s''',
                  (property_id,)).fetchone(),
                'price_history': conn.execute('''SELECT price_wan,quote_type,evidence_url
                  FROM price_history WHERE listing_id=%s''', (listing_id,)).fetchone(),
                'property_match': conn.execute('''SELECT match_score,evidence,status
                  FROM property_matches WHERE video_id=%s AND listing_id=%s''',
                  (video_id, listing_id)).fetchone(),
                'saved_search': conn.execute('''SELECT name,district,community_name,max_price_wan,
                  min_area_sqm,min_bedrooms,min_drop_pct,notifications_enabled,districts,
                  preferred_communities,excluded_communities,max_listing_age_days
                  FROM saved_searches WHERE id=%s''', (search_id,)).fetchone(),
                'notification': conn.execute('''SELECT event_key,event_type,payload,delivery_status
                  FROM notification_logs WHERE search_id=%s''', (search_id,)).fetchone(),
            }
            assert preserved_values == {
                'account': {'account_ref':'legacy-account-001','nickname':'Legacy creator',
                  'history_mode':'30d','poll_interval_minutes':240,'enabled':False,
                  'initial_synced':True,'last_status':'success'},
                'sync_run': {'status':'partial','pages':3,'observed_count':17,'new_count':4,
                  'error_text':'legacy warning'},
                'seen_post': {'baseline_only':True},
                'video': {'source_url':'https://www.douyin.com/video/legacy-post-001',
                  'author_name':'Legacy creator','title':'Legacy title',
                  'description':'Legacy description','transcript':'Legacy transcript',
                  'ocr_text':'Legacy OCR','extracted_fields':{'district':'鄞州'},
                  'processing_status':'enriched','raw_location':'鄞州',
                  'permission_note':'user-provided'},
                'community': {'city':'宁波','district':'鄞州','address':'Legacy address',
                  'latitude':'29.8200000','longitude':'121.5500000','verified':True},
                'alias': {'city':'宁波','alias':'V0.1 migration alias'},
                'property': {'area_sqm':100,'bedrooms':2,'floor_text':'中层',
                  'layout_note':'南北通透','decoration':'精装','building_info':'2幢',
                  'identity_status':'verified'},
                'price_history': {'price_wan':330,'quote_type':'agent_claim',
                  'evidence_url':'https://evidence.example/legacy'},
                'property_match': {'match_score':75,'evidence':{'source':'legacy'},
                  'status':'confirmed'},
                'saved_search': {'name':'Legacy search','district':'鄞州',
                  'community_name':'V0.1 migration fixture','max_price_wan':350,
                  'min_area_sqm':80,'min_bedrooms':2,'min_drop_pct':7,
                  'notifications_enabled':False,'districts':[],
                  'preferred_communities':[],'excluded_communities':[],
                  'max_listing_age_days':None},
                'notification': {'event_key':'legacy-event','event_type':'new_listing',
                  'payload':{'legacy':True},'delivery_status':'read'},
            }
            assert conn.execute('''SELECT bool_and(NOT online_enabled) AS all_disabled
              FROM source_registry''').fetchone()['all_disabled'] is True
            health = conn.execute('''SELECT source,success_count,failure_count,blocked_count,
              pending_count,approved_count,rejected_count,listing_count
              FROM collection_health_metrics ORDER BY source''').fetchall()
            assert health == [
                {'source':'anjuke','success_count':0,'failure_count':0,'blocked_count':0,
                 'pending_count':0,'approved_count':0,'rejected_count':0,'listing_count':0},
                {'source':'beike','success_count':0,'failure_count':0,'blocked_count':0,
                 'pending_count':0,'approved_count':0,'rejected_count':0,'listing_count':1},
            ]
    finally:
        if created:
            with connect_test_db(DATABASE_URL, autocommit=True) as conn:
                conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))


def test_v02_baseline_migration_preserves_collection_data_and_parse_metrics():
    if not DATABASE_URL:
        pytest.skip('Set TEST_DATABASE_URL to run PostgreSQL integration tests')
    schema = 'baseline_' + uuid4().hex
    created = False
    try:
        with connect_test_db(DATABASE_URL, autocommit=True) as conn:
            conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
        created = True
        scoped_url = make_conninfo(DATABASE_URL, options=f'-csearch_path={schema}')
        with connect_test_db(scoped_url, autocommit=True) as conn:
            for name in (
                '001_init.sql',
                '002_collection_pipeline.sql',
                '003_collection_health_indexes.sql',
                '004_collection_health_metrics.sql',
                '005_saved_search_filters.sql',
            ):
                conn.execute((ROOT / 'sql' / name).read_text())

            community_id = conn.execute('''INSERT INTO communities(city,name,district)
              VALUES('宁波','V0.2 baseline fixture','鄞州') RETURNING id''').fetchone()['id']
            property_id = conn.execute('''INSERT INTO properties(community_id,area_sqm,bedrooms)
              VALUES(%s,100,3) RETURNING id''', (community_id,)).fetchone()['id']
            listing_id = conn.execute('''INSERT INTO source_listings
              (source,source_listing_id,property_id,title,listing_url,asking_price_wan,
               first_observed_at,last_observed_at,status)
              VALUES('beike','12345678901',%s,'V0.2 baseline listing',
               'https://nb.ke.com/ershoufang/12345678901.html',320,now(),now(),'available')
              RETURNING id''', (property_id,)).fetchone()['id']
            target_id = conn.execute('''INSERT INTO collection_targets(source,url,enabled)
              VALUES('beike','https://nb.ke.com/ershoufang/',FALSE) RETURNING id''').fetchone()['id']
            run_id = conn.execute('''INSERT INTO collection_runs
              (target_id,source,source_url,status,note)
              VALUES(%s,'beike','https://nb.ke.com/ershoufang/','success','baseline run')
              RETURNING id''', (target_id,)).fetchone()['id']
            candidate_id = conn.execute('''INSERT INTO collection_candidates
              (source,source_url,capture_method,source_listing_id,raw_sha256,raw_storage_path,
               parser_version,extracted_fields)
              VALUES('beike','https://nb.ke.com/ershoufang/12345678901.html',
               'manual_html_snapshot','12345678901',%s,'raw-pages/baseline.html.gz',
               'baseline-parser','{"community_name":"V0.2 baseline fixture"}'::jsonb)
              RETURNING id''', ('a' * 64,)).fetchone()['id']
            search_id = conn.execute('''INSERT INTO saved_searches(name,district,max_price_wan)
              VALUES('V0.2 baseline search','鄞州',350) RETURNING id''').fetchone()['id']

            baseline_metrics = conn.execute('''SELECT success_count,pending_count,listing_count
              FROM collection_health_metrics WHERE source='beike' ''').fetchone()
            assert baseline_metrics == {
                'success_count': 1, 'pending_count': 1, 'listing_count': 1,
            }

            migrations = (
                '006_collection_discovery_state.sql',
                '007_collection_listing_observations.sql',
                '008_collection_discovery_sweeps.sql',
                '009_collection_listing_reviews.sql',
                '010_collection_parse_metrics.sql',
                '011_parse_attempts_append_only.sql',
                '012_collection_discovery_staged_ids.sql',
                '013_account_history_backfill_cursor.sql',
                '014_collection_detail_queue.sql',
            )
            for name in migrations:
                conn.execute((ROOT / 'sql' / name).read_text())

            conn.execute('''INSERT INTO collection_discovery_states
              (target_id,seen_listing_ids,last_page_url,next_page_url,visited_page_urls,
               sweep_number,sweep_active,sweep_seen_listing_ids,completed_sweeps)
              VALUES(%s,'["12345678901"]'::jsonb,'https://nb.ke.com/ershoufang/',
               'https://nb.ke.com/ershoufang/pg2/','["https://nb.ke.com/ershoufang/"]'::jsonb,
               4,TRUE,'["12345678901"]'::jsonb,3)''', (target_id,))
            conn.execute('''INSERT INTO collection_listing_observations
              (target_id,source,source_listing_id,listing_url,first_page_url,last_page_url,
               first_page_sha256,last_page_sha256,first_page_storage_path,last_page_storage_path,
               last_seen_sweep,last_evaluated_sweep,missed_complete_scans,review_status)
              VALUES(%s,'beike','12345678901',
               'https://nb.ke.com/ershoufang/12345678901.html',
               'https://nb.ke.com/ershoufang/','https://nb.ke.com/ershoufang/',%s,%s,
               'raw-pages/list.html.gz','raw-pages/list.html.gz',4,4,2,'pending_review')''',
              (target_id, 'b' * 64, 'b' * 64))
            conn.execute('''INSERT INTO collection_listing_reviews
              (target_id,source,source_listing_id,conclusion,note)
              VALUES(%s,'beike','12345678901','inconclusive','baseline review')''',
              (target_id,))
            conn.execute('''INSERT INTO collection_parse_attempts
              (source,capture_method,parser_version,parse_status,required_fields_complete)
              VALUES('beike','manual_html_snapshot','baseline-parser','success',TRUE),
                    ('beike','public_page_collection','baseline-parser','failed',FALSE)''')
            for name in migrations:
                conn.execute((ROOT / 'sql' / name).read_text())

            preserved = {
                'listing': conn.execute('''SELECT source_listing_id,title,asking_price_wan,status,
                  acquisition_method FROM source_listings WHERE id=%s''', (listing_id,)).fetchone(),
                'target': conn.execute('''SELECT source,url,enabled FROM collection_targets
                  WHERE id=%s''', (target_id,)).fetchone(),
                'run': conn.execute('''SELECT id,source,status,note FROM collection_runs
                  WHERE id=%s''', (run_id,)).fetchone(),
                'candidate': conn.execute('''SELECT source_listing_id,review_status,raw_sha256
                  FROM collection_candidates WHERE id=%s''', (candidate_id,)).fetchone(),
                'search': conn.execute('''SELECT name,district,max_price_wan,districts,
                  preferred_communities FROM saved_searches WHERE id=%s''', (search_id,)).fetchone(),
                'state': conn.execute('''SELECT seen_listing_ids,sweep_number,sweep_active,
                  completed_sweeps FROM collection_discovery_states WHERE target_id=%s''',
                  (target_id,)).fetchone(),
                'staged_ids': conn.execute('''SELECT source_listing_id
                  FROM collection_discovery_staged_ids WHERE target_id=%s''',
                  (target_id,)).fetchall(),
                'observation': conn.execute('''SELECT missed_complete_scans,review_status
                  FROM collection_listing_observations WHERE target_id=%s
                  AND source='beike' AND source_listing_id='12345678901' ''',
                  (target_id,)).fetchone(),
                'review': conn.execute('''SELECT conclusion,note FROM collection_listing_reviews
                  WHERE target_id=%s AND source='beike' AND source_listing_id='12345678901' ''',
                  (target_id,)).fetchone(),
                'metrics': conn.execute('''SELECT success_count,pending_count,listing_count,
                  parse_attempt_count,parse_success_count,complete_field_count
                  FROM collection_health_metrics WHERE source='beike' ''').fetchone(),
            }
            assert preserved == {
                'listing': {'source_listing_id':'12345678901','title':'V0.2 baseline listing',
                  'asking_price_wan':320,'status':'available','acquisition_method':'manual_import'},
                'target': {'source':'beike','url':'https://nb.ke.com/ershoufang/',
                  'enabled':False},
                'run': {'id':run_id,'source':'beike','status':'success','note':'baseline run'},
                'candidate': {'source_listing_id':'12345678901','review_status':'pending',
                  'raw_sha256':'a' * 64},
                'search': {'name':'V0.2 baseline search','district':'鄞州','max_price_wan':350,
                  'districts':[],'preferred_communities':[]},
                'state': {'seen_listing_ids':[],'sweep_number':4,
                  'sweep_active':True,'completed_sweeps':3},
                'staged_ids': [{'source_listing_id':'12345678901'}],
                'observation': {'missed_complete_scans':2,'review_status':'pending_review'},
                'review': {'conclusion':'inconclusive','note':'baseline review'},
                'metrics': {'success_count':1,'pending_count':1,'listing_count':1,
                  'parse_attempt_count':2,'parse_success_count':1,'complete_field_count':1},
            }
    finally:
        if created:
            with connect_test_db(DATABASE_URL, autocommit=True) as conn:
                conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))


def post_page(client, *, url=BASE_URL, html=HTML):
    return client.post('/api/collection/pages', headers={'X-API-Key': API_KEY}, json={
        'source': 'beike', 'source_url': url, 'html': html,
    })


def test_collection_discovery_state_persists_cursor_and_rejects_stale_update(api):
    client, scoped_url = api
    headers = {'X-API-Key': API_KEY}
    created = client.post('/api/collection/targets', headers=headers, json={
        'source': 'beike', 'url': 'https://nb.ke.com/ershoufang/', 'enabled': False,
    })
    assert created.status_code == 200
    target_id = created.json()['id']
    endpoint = f'/api/collection/targets/{target_id}/discovery-state'

    empty = client.get(endpoint, headers=headers)
    assert empty.status_code == 200
    assert empty.json() == {
        'version': 1, 'revision': 0, 'source': 'beike', 'seen_ids': [],
        'seen_ids_count': 0, 'seen_ids_truncated': False,
        'last_page_url': None, 'next_page_url': None, 'visited_page_urls': [],
        'last_attempted_page_url': None, 'last_error_type': None, 'failed_attempts': 0,
        'sweep_number': 0, 'sweep_active': False, 'sweep_seen_ids': [],
        'sweep_seen_ids_count': 0, 'sweep_seen_ids_truncated': False,
        'pending_detail_urls': [], 'pending_detail_urls_count': 0,
        'pending_detail_urls_truncated': False,
        'completed_sweeps': 0,
    }

    listing_url = 'https://nb.ke.com/ershoufang/109900009876.html'
    with connect_test_db(scoped_url, autocommit=True) as conn:
        conn.execute('''INSERT INTO collection_listing_observations
          (target_id,source,source_listing_id,listing_url,first_page_url,last_page_url,
           first_page_sha256,last_page_sha256,first_page_storage_path,last_page_storage_path)
          VALUES(%s,'beike','109900009876',%s,'https://nb.ke.com/ershoufang/',
           'https://nb.ke.com/ershoufang/',%s,%s,'raw-pages/list.gz','raw-pages/list.gz')''',
          (target_id,listing_url,'a' * 64,'a' * 64))
        conn.execute('''INSERT INTO collection_discovery_detail_queue
          (target_id,source,source_listing_id,listing_url,discovered_page_url)
          VALUES(%s,'beike','109900009876',%s,'https://nb.ke.com/ershoufang/')''',
          (target_id,listing_url))
    queued = client.get(endpoint, headers=headers).json()
    assert queued['pending_detail_urls_count'] == 1
    assert queued['pending_detail_urls_truncated'] is False
    assert queued['pending_detail_urls'][0]['source_listing_id'] == '109900009876'
    assert queued['pending_detail_urls'][0]['listing_url'] == listing_url

    state = {
        **queued,
        'seen_ids': ['109900001234', '109900001234'],
        'last_page_url': 'https://nb.ke.com/ershoufang/',
        'next_page_url': 'https://nb.ke.com/ershoufang/page2',
        'visited_page_urls': ['https://nb.ke.com/ershoufang/'],
        'last_attempted_page_url': 'https://nb.ke.com/ershoufang/',
    }
    saved = client.put(endpoint, headers=headers, json=state)
    assert saved.status_code == 200
    assert saved.json()['revision'] == 1
    assert saved.json()['seen_ids'] == ['109900001234']

    alias_loop = {
        **saved.json(),
        'next_page_url': 'https://NB.KE.COM:443/ershoufang/page2',
        'visited_page_urls': [
            *saved.json()['visited_page_urls'],
            'https://NB.KE.COM:443/ershoufang/page2',
        ],
    }
    rejected_loop = client.put(endpoint, headers=headers, json=alias_loop)
    assert rejected_loop.status_code == 422
    assert client.get(endpoint, headers=headers).json()['revision'] == 1

    stale = client.put(endpoint, headers=headers, json=state)
    assert stale.status_code == 409

    unsafe = {**saved.json(), 'next_page_url':
              'https://nb.ke.com/ershoufang/page3?token=secret'}
    rejected = client.put(endpoint, headers=headers, json=unsafe)
    assert rejected.status_code == 422
    assert client.get(endpoint, headers=headers).json()['revision'] == 1

    retry = {
        **saved.json(),
        'last_attempted_page_url': 'https://nb.ke.com/ershoufang/page2',
        'next_page_url': 'https://nb.ke.com/ershoufang/page2',
        'last_error_type': 'TimeoutError',
        'failed_attempts': 1,
    }
    retry_saved = client.put(endpoint, headers=headers, json=retry)
    assert retry_saved.status_code == 200
    assert retry_saved.json()['revision'] == 2
    assert retry_saved.json()['last_error_type'] == 'TimeoutError'
    assert retry_saved.json()['failed_attempts'] == 1

    with connect_test_db(scoped_url) as conn:
        row = conn.execute('''SELECT next_page_url,seen_listing_ids,visited_page_urls,
          last_error_type,failed_attempts,revision FROM collection_discovery_states
          WHERE target_id=%s''', (target_id,)).fetchone()
    assert row == {
        'next_page_url': 'https://nb.ke.com/ershoufang/page2',
        'seen_listing_ids': [],
        'visited_page_urls': ['https://nb.ke.com/ershoufang/'],
        'last_error_type': 'TimeoutError', 'failed_attempts': 1, 'revision': 2,
    }
    with connect_test_db(scoped_url) as conn:
        assert conn.execute('''SELECT source_listing_id FROM collection_discovery_staged_ids
          WHERE target_id=%s''', (target_id,)).fetchall() == [
            {'source_listing_id': '109900001234'}]


def test_discovery_detail_queue_cascades_with_listing_observation(api):
    client, scoped_url = api
    created = client.post('/api/collection/targets', headers={'X-API-Key': API_KEY}, json={
        'source': 'beike', 'url': 'https://nb.ke.com/ershoufang/', 'enabled': False,
    })
    assert created.status_code == 200
    target_id = created.json()['id']
    listing_url = 'https://nb.ke.com/ershoufang/109900009876.html'
    with connect_test_db(scoped_url, autocommit=True) as conn:
        conn.execute('''INSERT INTO collection_listing_observations
          (target_id,source,source_listing_id,listing_url,first_page_url,last_page_url,
           first_page_sha256,last_page_sha256,first_page_storage_path,last_page_storage_path)
          VALUES(%s,'beike','109900009876',%s,'https://nb.ke.com/ershoufang/',
           'https://nb.ke.com/ershoufang/',%s,%s,'raw-pages/list.gz','raw-pages/list.gz')''',
          (target_id,listing_url,'a' * 64,'a' * 64))
        conn.execute('''INSERT INTO collection_discovery_detail_queue
          (target_id,source,source_listing_id,listing_url,discovered_page_url,
           attempt_count,last_attempt_at,last_error_type)
          VALUES(%s,'beike','109900009876',%s,'https://nb.ke.com/ershoufang/',
           2,now(),'TimeoutError')''', (target_id,listing_url))
        queued = conn.execute('''SELECT attempt_count,last_error_type
          FROM collection_discovery_detail_queue WHERE target_id=%s''',
          (target_id,)).fetchone()
        assert queued == {'attempt_count': 2, 'last_error_type': 'TimeoutError'}
        conn.execute('''DELETE FROM collection_listing_observations
          WHERE target_id=%s AND source='beike' AND source_listing_id='109900009876' ''',
          (target_id,))
        rows = conn.execute('''SELECT source_listing_id FROM collection_discovery_detail_queue
          WHERE target_id=%s''', (target_id,)).fetchall()

    assert rows == []


def test_worker_paginates_list_targets_and_persists_detail_candidates(api, monkeypatch):
    client, scoped_url = api
    monkeypatch.setattr(collection_service, 'ENABLE_ONLINE_COLLECTION', True)
    monkeypatch.setattr(collection_service, 'MAX_DISCOVERY_PAGES_PER_RUN', 1)
    page_one = 'https://nb.ke.com/ershoufang/'
    page_two = 'https://nb.ke.com/ershoufang/page2'
    detail_one = 'https://nb.ke.com/ershoufang/109900001234.html'
    detail_two = 'https://nb.ke.com/ershoufang/109900005678.html'
    created = client.post('/api/collection/targets', headers={'X-API-Key': API_KEY}, json={
        'source': 'beike', 'url': page_one, 'enabled': True,
    })
    assert created.status_code == 200
    target = created.json()
    with connect_test_db(scoped_url) as conn:
        conn.execute('''UPDATE source_registry SET online_enabled=TRUE,
          online_policy_status='approved',policy_reference='isolated-integration-test'
          WHERE source='beike' ''')

    detail_html = ('<html><body><main><div>小区：东湖花园</div>'
                   '<div>建筑面积：120㎡</div><div>总价：350万</div></main></body></html>')
    pages = {
        page_one: (f'<html><head><link rel="next" href="{page_two}"></head><body><main>'
                   f'<a href="{detail_one}">detail</a></main></body></html>'),
        page_two: f'<html><body><main><a href="{detail_two}">detail</a></main></body></html>',
        detail_one: detail_html,
        detail_two: detail_html,
    }
    fetch_calls = []

    def fetch(source, url, **kwargs):
        fetch_calls.append(url)
        return pages[url]

    monkeypatch.setattr(collection_service, 'fetch_public_html', fetch)

    assert collection_service.run_collection_target(target) == 'success'
    first_state = client.get(
        f"/api/collection/targets/{target['id']}/discovery-state",
        headers={'X-API-Key': API_KEY}).json()
    assert first_state['next_page_url'] == page_two
    assert first_state['last_page_url'] == page_one
    assert first_state['seen_ids'] == ['109900001234']
    assert first_state['visited_page_urls'] == [page_one]
    assert first_state['sweep_number'] == 1
    assert first_state['sweep_active'] is True
    assert first_state['completed_sweeps'] == 0

    assert collection_service.run_collection_target(target) == 'success'
    second_state = client.get(
        f"/api/collection/targets/{target['id']}/discovery-state",
        headers={'X-API-Key': API_KEY}).json()
    assert second_state['next_page_url'] is None
    assert second_state['last_page_url'] == page_two
    assert second_state['seen_ids'] == ['109900001234', '109900005678']
    assert second_state['visited_page_urls'] == [page_one, page_two]
    assert second_state['sweep_active'] is False
    assert second_state['completed_sweeps'] == 1
    assert fetch_calls == [page_one, detail_one, page_two, detail_two]

    with connect_test_db(scoped_url) as conn:
        candidates = conn.execute('''SELECT source_url,source_listing_id,review_status
          FROM collection_candidates ORDER BY source_listing_id''').fetchall()
        run_statuses = conn.execute('''SELECT status FROM collection_runs
          WHERE target_id=%s ORDER BY id''', (target['id'],)).fetchall()
    assert candidates == [
        {'source_url': detail_one, 'source_listing_id': '109900001234',
         'review_status': 'pending'},
        {'source_url': detail_two, 'source_listing_id': '109900005678',
         'review_status': 'pending'},
    ]
    assert run_statuses == [{'status': 'success'}, {'status': 'success'}]

    observations = client.get('/api/collection/discovery-observations?source=beike',
                              headers={'X-API-Key': API_KEY})
    assert observations.status_code == 200
    assert {row['source_listing_id'] for row in observations.json()} == {
        '109900001234', '109900005678'
    }
    first_observed = next(row for row in observations.json()
                          if row['source_listing_id'] == '109900001234')
    assert first_observed['observation_count'] == 1
    assert first_observed['target_id'] == target['id']
    assert first_observed['last_page_url'] == page_one
    assert first_observed['review_status'] == 'active'
    assert first_observed['missed_complete_scans'] == 0
    assert first_observed['first_page_sha256'] == sha256(pages[page_one].encode()).hexdigest()
    with gzip.open(first_observed['last_page_storage_path'], 'rb') as evidence:
        assert evidence.read() == pages[page_one].encode()

    # A later scan still refreshes last-seen time even though this target already
    # queued the ID and therefore must not fetch its detail page again.
    assert collection_service.run_collection_target(target) == 'success'
    refreshed = client.get('/api/collection/discovery-observations?source=beike',
                           headers={'X-API-Key': API_KEY})
    refreshed_first = next(row for row in refreshed.json()
                           if row['source_listing_id'] == '109900001234')
    assert refreshed_first['observation_count'] == 2
    assert refreshed_first['first_seen_at'] == first_observed['first_seen_at']
    assert refreshed_first['last_seen_at'] >= first_observed['last_seen_at']
    assert fetch_calls == [page_one, detail_one, page_two, detail_two, page_one]


def test_discovery_state_lists_staged_ids_in_stable_order(api):
    client, scoped_url = api
    created = client.post('/api/collection/targets', headers={'X-API-Key': API_KEY}, json={
        'source': 'beike', 'url': 'https://nb.ke.com/ershoufang/', 'enabled': False,
    })
    target = created.json()
    with connect_test_db(scoped_url) as conn:
        conn.execute('''INSERT INTO collection_discovery_staged_ids
          (target_id,source_listing_id,staged_at)
          VALUES(%s,'109900005678',now()-interval '1 day'),
                (%s,'109900001234',now())''', (target['id'],target['id']))

    state = client.get(
        f"/api/collection/targets/{target['id']}/discovery-state",
        headers={'X-API-Key': API_KEY}).json()
    assert state['seen_ids'] == ['109900001234', '109900005678']


def test_staged_ids_migration_keeps_active_sweep_observations(api):
    client, scoped_url = api
    created = client.post('/api/collection/targets', headers={'X-API-Key': API_KEY}, json={
        'source': 'beike', 'url': 'https://nb.ke.com/ershoufang/', 'enabled': False,
    })
    target_id = created.json()['id']
    listing_id = '109900005678'
    with connect_test_db(scoped_url) as conn:
        conn.execute('''INSERT INTO collection_discovery_states
          (target_id,sweep_number,sweep_active,sweep_seen_listing_ids)
          VALUES(%s,2,TRUE,%s::jsonb)''', (target_id, json.dumps([listing_id])))
        conn.execute('''INSERT INTO collection_listing_observations
          (target_id,source,source_listing_id,listing_url,first_page_url,last_page_url,
           first_page_sha256,last_page_sha256,first_page_storage_path,last_page_storage_path,
           last_seen_sweep)
          VALUES(%s,'beike',%s,%s,%s,%s,%s,%s,'raw-pages/list.html.gz',
           'raw-pages/list.html.gz',2)''',
          (target_id,listing_id,
           f'https://nb.ke.com/ershoufang/{listing_id}.html',
           'https://nb.ke.com/ershoufang/','https://nb.ke.com/ershoufang/',
           'a' * 64,'a' * 64))
        conn.execute((ROOT / 'sql' / '012_collection_discovery_staged_ids.sql').read_text())

    state = client.get(
        f'/api/collection/targets/{target_id}/discovery-state',
        headers={'X-API-Key': API_KEY}).json()
    assert state['sweep_active'] is True
    assert state['sweep_number'] == 2
    assert state['sweep_seen_ids'] == [listing_id]
    assert state['sweep_seen_ids_count'] == 1


def test_worker_continues_after_staged_id_history_exceeds_json_limit(api, monkeypatch):
    client, scoped_url = api
    monkeypatch.setattr(collection_service, 'ENABLE_ONLINE_COLLECTION', True)
    page_url = 'https://nb.ke.com/ershoufang/'
    detail_url = 'https://nb.ke.com/ershoufang/109900001234.html'
    created = client.post('/api/collection/targets', headers={'X-API-Key': API_KEY}, json={
        'source': 'beike', 'url': page_url, 'enabled': True,
    })
    target = created.json()
    with connect_test_db(scoped_url) as conn:
        conn.execute('''UPDATE source_registry SET online_enabled=TRUE,
          online_policy_status='approved',policy_reference='isolated-integration-test'
          WHERE source='beike' ''')
        conn.execute('''INSERT INTO collection_discovery_staged_ids
          (target_id,source_listing_id)
          SELECT %s,(10000000000 + value)::text FROM generate_series(1,100001) AS seq(value)''',
          (target['id'],))

    page_html = f'<html><body><main><a href="{detail_url}">listing</a></main></body></html>'
    detail_html = ('<html><body><main><div>小区：东湖花园</div>'
                   '<div>建筑面积：120㎡</div><div>总价：350万</div></main></body></html>')
    monkeypatch.setattr(collection_service, 'fetch_public_html',
                        lambda _source, url, **_kwargs:
                        page_html if url == page_url else detail_html)

    assert collection_service.run_collection_target(target) == 'success'
    state = client.get(f"/api/collection/targets/{target['id']}/discovery-state",
                       headers={'X-API-Key': API_KEY}).json()
    assert state['seen_ids_count'] == 100002
    assert state['seen_ids_truncated'] is True
    assert len(state['seen_ids']) == 100000
    assert state['sweep_seen_ids'] == ['109900001234']
    with connect_test_db(scoped_url) as conn:
        assert conn.execute('''SELECT count(*) AS total
          FROM collection_candidates WHERE source_listing_id='109900001234' ''').fetchone()['total'] == 1
        assert conn.execute('''SELECT seen_listing_ids FROM collection_discovery_states
          WHERE target_id=%s''', (target['id'],)).fetchone()['seen_listing_ids'] == []


def test_worker_marks_listing_for_review_after_two_complete_missing_sweeps(
        api, monkeypatch, tmp_path):
    client, scoped_url = api
    monkeypatch.setattr(collection_service, 'ENABLE_ONLINE_COLLECTION', True)
    page_one = 'https://nb.ke.com/ershoufang/'
    page_two = 'https://nb.ke.com/ershoufang/page2'
    detail = 'https://nb.ke.com/ershoufang/109900001234.html'
    created = client.post('/api/collection/targets', headers={'X-API-Key': API_KEY}, json={
        'source': 'beike', 'url': page_one, 'enabled': True,
    })
    assert created.status_code == 200
    target = created.json()
    with connect_test_db(scoped_url) as conn:
        conn.execute('''UPDATE source_registry SET online_enabled=TRUE,
          online_policy_status='approved',policy_reference='isolated-integration-test'
          WHERE source='beike' ''')
        community_id = conn.execute('''INSERT INTO communities(name)
          VALUES('东湖花园') RETURNING id''').fetchone()['id']
        property_id = conn.execute('''INSERT INTO properties(community_id,area_sqm,bedrooms)
          VALUES(%s,120,3) RETURNING id''',(community_id,)).fetchone()['id']
        conn.execute('''INSERT INTO source_listings(source,source_listing_id,property_id,
          asking_price_wan,first_observed_at,last_observed_at,status)
          VALUES('beike','109900005678',%s,350,now(),now(),'available')''',(property_id,))

    page_one_html = (f'<html><head><link rel="next" href="{page_two}"></head>'
                     f'<body><main><a href="{detail}">listing</a></main></body></html>')
    detail_html = ('<html><body><main><div>小区：东湖花园</div>'
                   '<div>建筑面积：120㎡</div><div>总价：350万</div></main></body></html>')
    page_two_with_listing = f'<html><body><main><a href="{detail.replace("1234", "5678")}">old</a></main></body></html>'
    page_two_empty = '<html><body><main>no matching listings</main></body></html>'
    detail_two = detail.replace('1234', '5678')
    pages = {page_one: page_one_html, detail: detail_html, detail_two: detail_html}
    fetch_calls = []
    rediscover_listing = {'enabled': False}

    def fetch(source, url, **kwargs):
        fetch_calls.append(url)
        if url == page_two:
            if rediscover_listing['enabled']:
                return page_two_with_listing
            return page_two_with_listing if len([x for x in fetch_calls if x == page_two]) == 1 else page_two_empty
        return pages[url]

    monkeypatch.setattr(collection_service, 'fetch_public_html', fetch)
    assert collection_service.run_collection_target(target) == 'success'
    assert client.get(f"/api/collection/targets/{target['id']}/discovery-state",
                      headers={'X-API-Key': API_KEY}).json()['completed_sweeps'] == 1

    assert collection_service.run_collection_target(target) == 'success'
    after_first_miss = client.get(
        '/api/collection/discovery-observations?review_status=active',
        headers={'X-API-Key': API_KEY}).json()
    missing = next(row for row in after_first_miss
                   if row['source_listing_id'] == '109900005678')
    assert missing['missed_complete_scans'] == 1
    assert missing['review_status'] == 'active'

    assert collection_service.run_collection_target(target) == 'success'
    pending = client.get(
        '/api/collection/discovery-observations?review_status=pending_review',
        headers={'X-API-Key': API_KEY}).json()
    missing = next(row for row in pending if row['source_listing_id'] == '109900005678')
    assert missing['missed_complete_scans'] == 2
    assert missing['review_status'] == 'pending_review'
    with connect_test_db(scoped_url) as conn:
        listing_statuses = conn.execute('''SELECT status FROM source_listings
          WHERE source='beike' AND source_listing_id='109900005678' ''').fetchall()
    assert listing_statuses == [{'status': 'available'}]

    review_path = (f"/api/collection/targets/{target['id']}/"
                   'discovery-observations/109900005678/reviews')
    assert client.post(review_path, json={'conclusion': 'still_listed'}).status_code == 401
    invalid_id_path = (f"/api/collection/targets/{target['id']}/"
                       'discovery-observations/not-a-listing-id/reviews')
    assert client.post(invalid_id_path, headers={'X-API-Key': API_KEY},
                       json={'conclusion': 'still_listed'}).status_code == 422
    invalid_review = client.post(review_path, headers={'X-API-Key': API_KEY}, json={
        'conclusion': 'withdrawn',
    })
    assert invalid_review.status_code == 422
    recorded = client.post(review_path, headers={'X-API-Key': API_KEY}, json={
        'conclusion': 'confirmed_withdrawn', 'note': '  人工确认已撤牌  ',
    })
    assert recorded.status_code == 200
    assert recorded.json()['review_status'] == 'reviewed'
    assert recorded.json()['conclusion'] == 'confirmed_withdrawn'
    assert recorded.json()['note'] == '人工确认已撤牌'
    assert client.post(review_path, headers={'X-API-Key': API_KEY}, json={
        'conclusion': 'still_listed',
    }).status_code == 409

    review_history = client.get(review_path, headers={'X-API-Key': API_KEY})
    assert review_history.status_code == 200
    assert [row['conclusion'] for row in review_history.json()] == ['confirmed_withdrawn']
    reviewed_observations = client.get(
        '/api/collection/discovery-observations?review_status=reviewed',
        headers={'X-API-Key': API_KEY}).json()
    reviewed = next(row for row in reviewed_observations
                    if row['source_listing_id'] == '109900005678')
    assert reviewed['latest_review_conclusion'] == 'confirmed_withdrawn'
    assert reviewed['latest_review_note'] == '人工确认已撤牌'
    assert reviewed['latest_reviewed_at'] is not None
    assert client.get(
        f"/api/collection/targets/{target['id']}/discovery-observations/109900005677/reviews",
        headers={'X-API-Key': API_KEY}).status_code == 404
    with connect_test_db(scoped_url) as conn:
        listing_statuses = conn.execute('''SELECT status FROM source_listings
          WHERE source='beike' AND source_listing_id='109900005678' ''').fetchall()
    assert listing_statuses == [{'status': 'available'}]
    assert fetch_calls.count(page_two) == 3

    rediscover_listing['enabled'] = True
    assert collection_service.run_collection_target(target) == 'success'
    reappeared = client.get(
        '/api/collection/discovery-observations?review_status=active',
        headers={'X-API-Key': API_KEY}).json()
    missing = next(row for row in reappeared
                   if row['source_listing_id'] == '109900005678')
    assert missing['missed_complete_scans'] == 0
    assert missing['review_status'] == 'active'
    assert missing['latest_review_conclusion'] == 'confirmed_withdrawn'
    with connect_test_db(scoped_url) as conn:
        listing_statuses = conn.execute('''SELECT status FROM source_listings
          WHERE source='beike' AND source_listing_id='109900005678' ''').fetchall()
    assert listing_statuses == [{'status': 'available'}]

    rediscover_listing['enabled'] = False
    assert collection_service.run_collection_target(target) == 'success'
    assert collection_service.run_collection_target(target) == 'success'
    pending_again = client.get(
        '/api/collection/discovery-observations?review_status=pending_review',
        headers={'X-API-Key': API_KEY}).json()
    missing = next(row for row in pending_again
                   if row['source_listing_id'] == '109900005678')
    assert missing['missed_complete_scans'] == 2
    recorded_again = client.post(review_path, headers={'X-API-Key': API_KEY}, json={
        'conclusion': 'inconclusive', 'note': '再次核验仍无法确认',
    })
    assert recorded_again.status_code == 200
    review_history = client.get(review_path, headers={'X-API-Key': API_KEY})
    assert [row['conclusion'] for row in review_history.json()] == [
        'inconclusive', 'confirmed_withdrawn']
    with connect_test_db(scoped_url) as conn:
        listing_statuses = conn.execute('''SELECT status FROM source_listings
          WHERE source='beike' AND source_listing_id='109900005678' ''').fetchall()
    assert listing_statuses == [{'status': 'available'}]
    with connect_test_db(scoped_url) as conn:
        review_count = conn.execute('''SELECT count(*) AS count
          FROM collection_listing_reviews
          WHERE target_id=%s AND source='beike' AND source_listing_id='109900005678' ''',
          (target['id'],)).fetchone()['count']
        references = conn.execute('''SELECT raw_storage_path AS storage_path
          FROM collection_candidates
          UNION SELECT first_page_storage_path FROM collection_listing_observations
          UNION SELECT last_page_storage_path FROM collection_listing_observations''').fetchall()
    assert review_count == 2
    unreferenced, missing = evidence_reference_summary(
        tmp_path / 'raw-pages', {row['storage_path'] for row in references})
    assert unreferenced == []
    assert missing == []
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        with connect_test_db(scoped_url) as conn:
            conn.execute('''DELETE FROM collection_listing_observations
              WHERE target_id=%s AND source='beike' AND source_listing_id='109900005678' ''',
              (target['id'],))


def test_worker_does_not_count_incomplete_listing_sweeps(api, monkeypatch):
    from app.collectors.http_client import CollectionBlocked

    client, scoped_url = api
    monkeypatch.setattr(collection_service, 'ENABLE_ONLINE_COLLECTION', True)
    page_one = 'https://nb.ke.com/ershoufang/'
    page_two = 'https://nb.ke.com/ershoufang/page2'
    detail = 'https://nb.ke.com/ershoufang/109900005678.html'
    created = client.post('/api/collection/targets', headers={'X-API-Key': API_KEY}, json={
        'source': 'beike', 'url': page_one, 'enabled': True,
    })
    assert created.status_code == 200
    target = created.json()
    with connect_test_db(scoped_url) as conn:
        conn.execute('''UPDATE source_registry SET online_enabled=TRUE,
          online_policy_status='approved',policy_reference='isolated-integration-test'
          WHERE source='beike' ''')

    detail_html = ('<html><body><main><div>小区：东湖花园</div>'
                   '<div>建筑面积：120㎡</div><div>总价：350万</div></main></body></html>')
    listing_page = (f'<html><head><link rel="next" href="{page_two}"></head><body><main>'
                    f'<a href="{detail}">listing</a></main></body></html>')
    empty_page = '<html><body><main>no matching listings</main></body></html>'
    fetch_mode = {'incomplete': False, 'failed_page': False, 'blocked_page': False}

    def fetch(source, url, **kwargs):
        if url == page_one:
            return listing_page if not fetch_mode['incomplete'] else (
                f'<html><head><link rel="next" href="{page_two}"></head>'
                '<body><main>no matching listings</main></body></html>')
        if url == page_two and fetch_mode['failed_page']:
            raise TimeoutError('synthetic page timeout')
        if url == page_two and fetch_mode['blocked_page']:
            raise CollectionBlocked('synthetic policy revocation', 'blocked_policy')
        return detail_html if url == detail else empty_page

    monkeypatch.setattr(collection_service, 'fetch_public_html', fetch)
    assert collection_service.run_collection_target(target) == 'success'
    baseline = client.get(
        '/api/collection/discovery-observations?source=beike',
        headers={'X-API-Key': API_KEY}).json()
    observed = next(row for row in baseline if row['source_listing_id'] == '109900005678')
    assert observed['missed_complete_scans'] == 0
    assert client.get(f"/api/collection/targets/{target['id']}/discovery-state",
                      headers={'X-API-Key': API_KEY}).json()['completed_sweeps'] == 1

    # A page cap leaves the current sweep active and must not count as a miss.
    fetch_mode['incomplete'] = True
    monkeypatch.setattr(collection_service, 'MAX_DISCOVERY_PAGES_PER_RUN', 1)
    assert collection_service.run_collection_target(target) == 'success'
    partial_state = client.get(
        f"/api/collection/targets/{target['id']}/discovery-state",
        headers={'X-API-Key': API_KEY}).json()
    assert partial_state['sweep_active'] is True
    assert partial_state['completed_sweeps'] == 1
    after_limit = client.get(
        '/api/collection/discovery-observations?source=beike',
        headers={'X-API-Key': API_KEY}).json()
    assert next(row for row in after_limit
                if row['source_listing_id'] == '109900005678')['missed_complete_scans'] == 0

    # A subsequent page failure also preserves the incomplete sweep.
    fetch_mode['failed_page'] = True
    assert collection_service.run_collection_target(target) == 'failed'
    failed_state = client.get(
        f"/api/collection/targets/{target['id']}/discovery-state",
        headers={'X-API-Key': API_KEY}).json()
    assert failed_state['sweep_active'] is True
    assert failed_state['completed_sweeps'] == 1
    after_failure = client.get(
        '/api/collection/discovery-observations?source=beike',
        headers={'X-API-Key': API_KEY}).json()
    assert next(row for row in after_failure
                if row['source_listing_id'] == '109900005678')['missed_complete_scans'] == 0

    # Policy revocation must also leave the sweep incomplete without a miss.
    fetch_mode['failed_page'] = False
    fetch_mode['blocked_page'] = True
    assert collection_service.run_collection_target(target) == 'blocked_policy'
    blocked_state = client.get(
        f"/api/collection/targets/{target['id']}/discovery-state",
        headers={'X-API-Key': API_KEY}).json()
    assert blocked_state['sweep_active'] is True
    assert blocked_state['completed_sweeps'] == 1
    after_block = client.get(
        '/api/collection/discovery-observations?source=beike',
        headers={'X-API-Key': API_KEY}).json()
    assert next(row for row in after_block
                if row['source_listing_id'] == '109900005678')['missed_complete_scans'] == 0

    # Recovery completes that same sweep; only now is one missing scan recorded.
    fetch_mode['blocked_page'] = False
    assert collection_service.run_collection_target(target) == 'success'
    final_state = client.get(
        f"/api/collection/targets/{target['id']}/discovery-state",
        headers={'X-API-Key': API_KEY}).json()
    assert final_state['sweep_active'] is False
    assert final_state['completed_sweeps'] == 2
    final_rows = client.get(
        '/api/collection/discovery-observations?source=beike',
        headers={'X-API-Key': API_KEY}).json()
    assert next(row for row in final_rows
                if row['source_listing_id'] == '109900005678')['missed_complete_scans'] == 1


def test_worker_policy_revocation_persists_partial_page_progress(api, monkeypatch):
    client, scoped_url = api
    monkeypatch.setattr(collection_service, 'ENABLE_ONLINE_COLLECTION', True)
    page_url = 'https://nb.ke.com/ershoufang/'
    detail_one = 'https://nb.ke.com/ershoufang/109900001234.html'
    detail_two = 'https://nb.ke.com/ershoufang/109900001235.html'
    created = client.post('/api/collection/targets', headers={'X-API-Key': API_KEY}, json={
        'source': 'beike', 'url': page_url, 'enabled': True,
    })
    assert created.status_code == 200
    target = created.json()
    with connect_test_db(scoped_url) as conn:
        conn.execute('''UPDATE source_registry SET online_enabled=TRUE,
          online_policy_status='approved',policy_reference='isolated-integration-test'
          WHERE source='beike' ''')

    pages = {
        page_url: f'<html><body><main><a href="{detail_one}">first</a>'
                  f'<a href="{detail_two}">second</a></main></body></html>',
        detail_one: '<html><body><main><div>小区：东湖花园</div>'
                    '<div>建筑面积：120㎡</div><div>总价：350万</div></main></body></html>',
        detail_two: '<html><body><main><div>小区：东湖花园</div>'
                    '<div>建筑面积：121㎡</div><div>总价：351万</div></main></body></html>',
    }
    fetch_calls = []

    def fetch(source, url, **kwargs):
        fetch_calls.append(url)
        if url == detail_one:
            with connect_test_db(scoped_url) as conn:
                conn.execute('''UPDATE source_registry SET online_enabled=FALSE,
                  online_policy_status='revoked' WHERE source='beike' ''')
        return pages[url]

    monkeypatch.setattr(collection_service, 'fetch_public_html', fetch)
    assert collection_service.run_collection_target(target) == 'blocked_policy'
    partial = client.get(
        f"/api/collection/targets/{target['id']}/discovery-state",
        headers={'X-API-Key': API_KEY}).json()
    assert partial['seen_ids'] == ['109900001234']
    assert partial['next_page_url'] == page_url
    assert partial['last_attempted_page_url'] == page_url
    assert partial['failed_attempts'] == 0
    with connect_test_db(scoped_url) as conn:
        candidates = conn.execute('''SELECT source_listing_id,review_status
          FROM collection_candidates ORDER BY source_listing_id''').fetchall()
    assert candidates == [{'source_listing_id': '109900001234', 'review_status': 'pending'}]

    with connect_test_db(scoped_url) as conn:
        conn.execute('''UPDATE source_registry SET online_enabled=TRUE,
          online_policy_status='approved',policy_reference='isolated-integration-test'
          WHERE source='beike' ''')
    assert collection_service.run_collection_target(target) == 'success'
    assert fetch_calls == [page_url, detail_one, detail_two, page_url]
    final = client.get(
        f"/api/collection/targets/{target['id']}/discovery-state",
        headers={'X-API-Key': API_KEY}).json()
    assert final['seen_ids'] == ['109900001234', '109900001235']
    assert final['next_page_url'] is None
    assert final['failed_attempts'] == 0
    with connect_test_db(scoped_url) as conn:
        candidates = conn.execute('''SELECT source_listing_id,review_status
          FROM collection_candidates ORDER BY source_listing_id''').fetchall()
        run_statuses = conn.execute('''SELECT status FROM collection_runs
          WHERE target_id=%s ORDER BY id''', (target['id'],)).fetchall()
    assert candidates == [
        {'source_listing_id': '109900001234', 'review_status': 'pending'},
        {'source_listing_id': '109900001235', 'review_status': 'pending'},
    ]
    assert run_statuses == [{'status': 'blocked_policy'}, {'status': 'success'}]


def test_worker_policy_revocation_before_first_detail_persists_sweep_state(api, monkeypatch):
    client, scoped_url = api
    monkeypatch.setattr(collection_service, 'ENABLE_ONLINE_COLLECTION', True)
    page_url = 'https://nb.ke.com/ershoufang/'
    detail_url = 'https://nb.ke.com/ershoufang/109900001236.html'
    target = client.post('/api/collection/targets', headers={'X-API-Key': API_KEY}, json={
        'source': 'beike', 'url': page_url, 'enabled': True,
    }).json()
    with connect_test_db(scoped_url) as conn:
        conn.execute('''UPDATE source_registry SET online_enabled=TRUE,
          online_policy_status='approved',policy_reference='isolated-integration-test'
          WHERE source='beike' ''')

    page = f'<html><body><main><a href="{detail_url}">listing</a></main></body></html>'
    fetch_calls = []

    def fetch(source, url, **kwargs):
        kwargs['before_page_request']()
        fetch_calls.append(url)
        if url == page_url:
            with connect_test_db(scoped_url) as conn:
                conn.execute('''UPDATE source_registry SET online_enabled=FALSE,
                  online_policy_status='revoked' WHERE source='beike' ''')
            return page
        raise AssertionError('revoked detail request must be blocked before HTTP')

    monkeypatch.setattr(collection_service, 'fetch_public_html', fetch)
    assert collection_service.run_collection_target(target) == 'blocked_policy'
    assert fetch_calls == [page_url]
    state = client.get(f"/api/collection/targets/{target['id']}/discovery-state",
                       headers={'X-API-Key': API_KEY}).json()
    assert state['sweep_number'] == 1
    assert state['sweep_active'] is True
    assert state['next_page_url'] == page_url
    assert state['seen_ids'] == []
    assert state['sweep_seen_ids'] == ['109900001236']
    observations = client.get('/api/collection/discovery-observations?source=beike',
                              headers={'X-API-Key': API_KEY}).json()
    assert next(row for row in observations
                if row['source_listing_id'] == '109900001236')['missed_complete_scans'] == 0
    with connect_test_db(scoped_url) as conn:
        assert conn.execute('''SELECT status FROM collection_runs
          WHERE target_id=%s ORDER BY id DESC LIMIT 1''', (target['id'],)).fetchone()['status'] == 'blocked_policy'


def test_health_aggregate_indexes_are_created_and_idempotent(api):
    _, scoped_url = api
    with connect_test_db(scoped_url) as conn:
        names = {row['indexname'] for row in conn.execute('''
          SELECT indexname FROM pg_indexes WHERE schemaname=current_schema()
        ''').fetchall()}
    assert 'idx_collection_runs_source_metrics' in names
    assert 'idx_collection_candidates_source_review' in names


def test_health_rates_use_confirmed_stage_denominators(api, monkeypatch):
    client, scoped_url = api
    first = collection_service.stage_html(
        'beike', BASE_URL, HTML, 'manual_html_snapshot')['candidate']
    second = collection_service.stage_html(
        'beike', 'https://nb.ke.com/ershoufang/109900001235.html',
        '<html><body><main><p>建筑面积：120㎡</p></main></body></html>',
        'public_page_collection')['candidate']

    def fail_parse(*args, **kwargs):
        raise ValueError('synthetic parser failure')

    monkeypatch.setattr(collection_service, 'parse_listing_html', fail_parse)
    with pytest.raises(ValueError, match='synthetic parser failure'):
        collection_service.stage_html(
            'beike', 'https://nb.ke.com/ershoufang/109900001236.html',
            '<html><body>invalid</body></html>', 'public_page_collection')

    with connect_test_db(scoped_url) as conn:
        conn.execute('''UPDATE collection_candidates SET review_status='approved',reviewed_at=now()
          WHERE id=%s''', (first['id'],))
        conn.execute('''UPDATE collection_candidates SET review_status='rejected',reviewed_at=now()
          WHERE id=%s''', (second['id'],))
        for status in ('success', 'success', 'failed', 'blocked_policy', 'blocked_upstream'):
            conn.execute('''INSERT INTO collection_runs(source,source_url,status)
              VALUES('beike','https://synthetic.invalid/health-rate',%s)''', (status,))

    rows = client.get('/api/collection/health', headers={'X-API-Key': API_KEY}).json()
    beike = next(row for row in rows if row['source'] == 'beike')
    assert beike['success_count'] == 2
    assert beike['failure_count'] == 1
    assert beike['blocked_count'] == 2
    assert beike['collection_success_rate_pct'] == 66.67
    assert beike['parse_attempt_count'] == 3
    assert beike['parse_success_count'] == 2
    assert beike['complete_field_count'] == 1
    assert beike['parse_success_rate_pct'] == 66.67
    assert beike['field_complete_rate_pct'] == 50.0
    assert beike['approved_count'] == 1
    assert beike['rejected_count'] == 1
    assert beike['approval_rate_pct'] == 50.0
    with connect_test_db(scoped_url) as conn:
        methods = conn.execute('''SELECT capture_method,parse_status,
            required_fields_complete FROM collection_parse_attempts
          WHERE source='beike' ORDER BY id''').fetchall()
    assert [row['capture_method'] for row in methods] == [
        'manual_html_snapshot', 'public_page_collection', 'public_page_collection']
    assert [row['parse_status'] for row in methods] == ['success', 'success', 'failed']


def test_parse_attempt_ledger_rejects_mutation_and_preserves_health_counts(api):
    _, scoped_url = api
    with connect_test_db(scoped_url) as conn:
        attempt_id = conn.execute('''INSERT INTO collection_parse_attempts
          (source,capture_method,parser_version,parse_status,required_fields_complete)
          VALUES('beike','manual_html_snapshot','test-parser','success',TRUE)
          RETURNING id''').fetchone()['id']

        mutations = (
            ('UPDATE collection_parse_attempts SET parse_status=\'failed\' WHERE id=%s',
             (attempt_id,)),
            ('DELETE FROM collection_parse_attempts WHERE id=%s', (attempt_id,)),
            ('TRUNCATE collection_parse_attempts', ()),
        )
        for statement, parameters in mutations:
            with pytest.raises(psycopg.errors.RaiseException,
                               match='collection_parse_attempts is append-only'):
                with conn.transaction():
                    conn.execute(statement, parameters)

        assert conn.execute('''SELECT parse_status,required_fields_complete
          FROM collection_parse_attempts WHERE id=%s''', (attempt_id,)).fetchone() == {
              'parse_status': 'success', 'required_fields_complete': True,
          }
        assert conn.execute('''SELECT parse_attempt_count,parse_success_count,
          complete_field_count FROM collection_health_metrics WHERE source='beike'
        ''').fetchone() == {
            'parse_attempt_count': 1, 'parse_success_count': 1,
            'complete_field_count': 1,
        }


def test_health_metrics_projection_tracks_changes_and_rebuilds(api):
    client, scoped_url = api
    headers = {'X-API-Key': API_KEY}
    latest = datetime.now(timezone.utc)
    earlier = latest - timedelta(minutes=1)
    with connect_test_db(scoped_url) as conn:
        first_run = conn.execute('''INSERT INTO collection_runs
          (source,source_url,status,started_at,finished_at,note)
          VALUES('beike','https://synthetic.invalid/run/1','success',%s,%s,'ok') RETURNING id''',
          (earlier, earlier)).fetchone()['id']
        latest_run = conn.execute('''INSERT INTO collection_runs
          (source,source_url,status,started_at,finished_at,note)
          VALUES('beike','https://synthetic.invalid/run/2','blocked_policy',%s,%s,'blocked') RETURNING id''',
          (latest, latest)).fetchone()['id']
        candidate_id = conn.execute('''INSERT INTO collection_candidates
          (source,source_url,capture_method,raw_sha256,raw_storage_path,parser_version)
          VALUES('beike','https://synthetic.invalid/candidate/1','manual_html_snapshot',%s,
          '/synthetic/1.gz','test') RETURNING id''',
          (sha256(b'health metric test').hexdigest(),)).fetchone()['id']
        community_id = conn.execute('''INSERT INTO communities(name,district)
          VALUES('Health Metric Test','鄞州') RETURNING id''').fetchone()['id']
        property_id = conn.execute('''INSERT INTO properties(community_id,area_sqm)
          VALUES(%s,100) RETURNING id''',(community_id,)).fetchone()['id']
        listing_id = conn.execute('''INSERT INTO source_listings
          (source,source_listing_id,property_id,asking_price_wan,first_observed_at,last_observed_at)
          VALUES('beike','health-metric-test',%s,200,%s,%s) RETURNING id''',
          (property_id,latest,latest)).fetchone()['id']

    # Re-running the migration rebuilds the projection from existing rows without doubling counts.
    with connect_test_db(scoped_url, autocommit=True) as conn:
        conn.execute((ROOT / 'sql' / '004_collection_health_metrics.sql').read_text())
    row = next(x for x in client.get('/api/collection/health', headers=headers).json()
               if x['source'] == 'beike')
    assert (row['success_count'], row['blocked_count'], row['pending_count'],
            row['listing_count'], row['latest_status'], row['latest_note']) == (1, 1, 1, 1,
                                                                                'blocked_policy', 'blocked')

    with connect_test_db(scoped_url) as conn:
        metrics_time = datetime(2000, 1, 1, tzinfo=timezone.utc)
        conn.execute("UPDATE collection_health_metrics SET updated_at=%s WHERE source='beike'",
                     (metrics_time,))
        conn.execute("UPDATE collection_candidates SET review_note='operator correction' WHERE id=%s",
                     (candidate_id,))
        assert conn.execute('''SELECT updated_at FROM collection_health_metrics
          WHERE source='beike' ''').fetchone()['updated_at'] == metrics_time

        conn.execute("UPDATE collection_candidates SET source='anjuke' WHERE id=%s", (candidate_id,))
        metrics = {row['source']: row for row in conn.execute('''SELECT source,pending_count
          FROM collection_health_metrics WHERE source IN ('beike','anjuke')''').fetchall()}
        assert (metrics['beike']['pending_count'], metrics['anjuke']['pending_count']) == (0, 1)
        conn.execute("UPDATE collection_candidates SET source='beike' WHERE id=%s", (candidate_id,))

    with connect_test_db(scoped_url) as conn:
        conn.execute('UPDATE source_listings SET last_observed_at=%s WHERE id=%s',
                     (earlier, listing_id))
        beike = conn.execute('''SELECT listing_count,last_observed_at
          FROM collection_health_metrics WHERE source='beike' ''').fetchone()
        assert (beike['listing_count'], beike['last_observed_at']) == (1, earlier)

        newest = latest + timedelta(minutes=1)
        conn.execute('UPDATE source_listings SET last_observed_at=%s WHERE id=%s',
                     (newest, listing_id))
        beike = conn.execute('''SELECT listing_count,last_observed_at
          FROM collection_health_metrics WHERE source='beike' ''').fetchone()
        assert (beike['listing_count'], beike['last_observed_at']) == (1, newest)

        conn.execute("UPDATE source_listings SET source='anjuke' WHERE id=%s", (listing_id,))
        metrics = {row['source']: row for row in conn.execute('''SELECT source,listing_count,last_observed_at
          FROM collection_health_metrics WHERE source IN ('beike','anjuke')''').fetchall()}
        assert (metrics['beike']['listing_count'], metrics['beike']['last_observed_at']) == (0, None)
        assert (metrics['anjuke']['listing_count'], metrics['anjuke']['last_observed_at']) == (1, newest)

        conn.execute('''UPDATE source_listings SET source='beike',last_observed_at=%s WHERE id=%s''',
                     (latest, listing_id))
        metrics = {row['source']: row for row in conn.execute('''SELECT source,listing_count,last_observed_at
          FROM collection_health_metrics WHERE source IN ('beike','anjuke')''').fetchall()}
        assert (metrics['beike']['listing_count'], metrics['beike']['last_observed_at']) == (1, latest)
        assert (metrics['anjuke']['listing_count'], metrics['anjuke']['last_observed_at']) == (0, None)

    with connect_test_db(scoped_url) as conn:
        conn.execute("UPDATE collection_candidates SET review_status='approved' WHERE id=%s",
                     (candidate_id,))
        conn.execute("UPDATE collection_runs SET status='failed',note='failed' WHERE id=%s",
                     (latest_run,))
    row = next(x for x in client.get('/api/collection/health', headers=headers).json()
               if x['source'] == 'beike')
    assert (row['success_count'], row['failure_count'], row['blocked_count'],
            row['approved_count'], row['pending_count'], row['latest_status']) == (1, 1, 0, 1, 0, 'failed')

    with connect_test_db(scoped_url) as conn:
        conn.execute('DELETE FROM collection_runs WHERE id=%s',(latest_run,))
        conn.execute('DELETE FROM collection_candidates WHERE id=%s',(candidate_id,))
        conn.execute('DELETE FROM source_listings WHERE id=%s',(listing_id,))
    row = next(x for x in client.get('/api/collection/health', headers=headers).json()
               if x['source'] == 'beike')
    assert (row['success_count'], row['failure_count'], row['blocked_count'],
            row['approved_count'], row['listing_count'], row['latest_status']) == (1, 0, 0, 0, 0, 'success')
    assert row['last_attempt_at'] is not None
    assert row['last_observed_at'] is None


def test_health_metrics_projection_bulk_writes_match_source_tables(api):
    _, scoped_url = api

    def assert_projection_matches(conn):
        actual = {row['source']: row for row in conn.execute('''
          SELECT source,success_count,failure_count,blocked_count,pending_count,
            approved_count,rejected_count,listing_count,last_attempt_at,last_success_at,
            last_observed_at,latest_status,latest_note
          FROM collection_health_metrics ORDER BY source
        ''').fetchall()}
        expected = conn.execute('''
          SELECT s.source,
            (SELECT count(*) FROM collection_runs r WHERE r.source=s.source AND r.status='success') success_count,
            (SELECT count(*) FROM collection_runs r WHERE r.source=s.source AND r.status='failed') failure_count,
            (SELECT count(*) FROM collection_runs r WHERE r.source=s.source AND r.status LIKE 'blocked%') blocked_count,
            (SELECT count(*) FROM collection_candidates c WHERE c.source=s.source AND c.review_status='pending') pending_count,
            (SELECT count(*) FROM collection_candidates c WHERE c.source=s.source AND c.review_status='approved') approved_count,
            (SELECT count(*) FROM collection_candidates c WHERE c.source=s.source AND c.review_status='rejected') rejected_count,
            (SELECT count(*) FROM source_listings l WHERE l.source=s.source) listing_count,
            (SELECT max(started_at) FROM collection_runs r WHERE r.source=s.source) last_attempt_at,
            (SELECT max(finished_at) FROM collection_runs r WHERE r.source=s.source AND r.status='success') last_success_at,
            (SELECT max(last_observed_at) FROM source_listings l WHERE l.source=s.source) last_observed_at,
            (SELECT status FROM collection_runs r WHERE r.source=s.source ORDER BY started_at DESC,id DESC LIMIT 1) latest_status,
            (SELECT note FROM collection_runs r WHERE r.source=s.source ORDER BY started_at DESC,id DESC LIMIT 1) latest_note
          FROM source_registry s ORDER BY s.source
        ''').fetchall()
        fields = ('success_count','failure_count','blocked_count','pending_count',
                  'approved_count','rejected_count','listing_count','last_attempt_at',
                  'last_success_at','last_observed_at','latest_status','latest_note')
        assert set(actual) == {row['source'] for row in expected}
        for row in expected:
            assert tuple(actual[row['source']][field] for field in fields) == tuple(row[field] for field in fields)

    started = perf_counter()
    write_seconds = {}
    projection_check_seconds = 0
    with connect_test_db(scoped_url) as conn:
        write_started = perf_counter()
        conn.execute('''INSERT INTO collection_runs(source,source_url,status,started_at,finished_at,note)
          SELECT CASE WHEN i%2=0 THEN 'beike' ELSE 'anjuke' END,
            'https://synthetic.invalid/bulk-run/' || i,
            CASE WHEN i%3=0 THEN 'success' WHEN i%3=1 THEN 'failed' ELSE 'blocked_robots' END,
            now()-i*interval '1 second',now()-i*interval '1 second','bulk test'
          FROM generate_series(1,10000) i''')
        write_seconds['insert_runs'] = perf_counter()-write_started
        write_started = perf_counter()
        conn.execute('''INSERT INTO collection_candidates
          (source,source_url,capture_method,raw_sha256,raw_storage_path,parser_version)
          SELECT CASE WHEN i%2=0 THEN 'beike' ELSE 'anjuke' END,
            'https://synthetic.invalid/bulk-candidate/' || i,'manual_html_snapshot',
            lpad(md5('bulk-' || i::text),64,'0'),'/synthetic/bulk/' || i || '.gz','bulk-test'
          FROM generate_series(1,10000) i''')
        write_seconds['insert_candidates'] = perf_counter()-write_started
        check_started = perf_counter()
        assert_projection_matches(conn)
        projection_check_seconds += perf_counter()-check_started

        write_started = perf_counter()
        conn.execute('''UPDATE collection_candidates SET review_status='approved',reviewed_at=now()
          WHERE source='beike' AND source_url LIKE 'https://synthetic.invalid/bulk-candidate/%'
            AND review_status='pending' ''')
        write_seconds['approve_candidates'] = perf_counter()-write_started
        check_started = perf_counter()
        assert_projection_matches(conn)
        projection_check_seconds += perf_counter()-check_started

        write_started = perf_counter()
        conn.execute('''DELETE FROM collection_runs
          WHERE source_url LIKE 'https://synthetic.invalid/bulk-run/%'
            AND substring(source_url FROM '[0-9]+$')::integer%10=0''')
        write_seconds['delete_runs'] = perf_counter()-write_started
        write_started = perf_counter()
        conn.execute('''DELETE FROM collection_candidates
          WHERE source_url LIKE 'https://synthetic.invalid/bulk-candidate/%'
            AND substring(source_url FROM '[0-9]+$')::integer%10=0''')
        write_seconds['delete_candidates'] = perf_counter()-write_started
        check_started = perf_counter()
        assert_projection_matches(conn)
        projection_check_seconds += perf_counter()-check_started
    print(f'bulk_projection_operation_seconds={write_seconds}')
    print(f'bulk_projection_check_seconds={projection_check_seconds:.3f}; total_elapsed_seconds={perf_counter()-started:.3f}')


def test_candidate_is_hidden_until_approval_and_approval_is_idempotent(api):
    client, scoped_url = api
    first = post_page(client)
    assert first.status_code == 200
    candidate_id = first.json()['candidate']['id']
    extracted = first.json()['candidate']['extracted_fields']
    assert extracted['confidence_status'] == 'not_calibrated'
    assert extracted['field_evidence']['community_name']['mentions'][0]['source'] == 'visible_listing_text'
    assert extracted['field_evidence']['source_listing_id']['mentions'][0]['source'] == 'source_url'
    duplicate = post_page(client)
    assert duplicate.status_code == 200
    assert duplicate.json()['candidate']['id'] == candidate_id
    assert client.get('/api/listings', headers={'X-API-Key': API_KEY}).json() == []

    review_url = f'/api/collection/candidates/{candidate_id}/review?decision=approve&note=人工核对样本'
    approved = client.post(review_url, headers={'X-API-Key': API_KEY})
    repeated = client.post(review_url, headers={'X-API-Key': API_KEY})
    assert approved.status_code == repeated.status_code == 200
    assert repeated.json()['idempotent'] is True
    listings = client.get('/api/listings', headers={'X-API-Key': API_KEY}).json()
    assert len(listings) == 1
    assert listings[0]['source_listing_id'] == '109900001234'
    prices = client.get(f"/api/listings/{listings[0]['id']}/prices",
                        headers={'X-API-Key': API_KEY}).json()
    assert len(prices) == 1
    with connect_test_db(scoped_url) as conn:
        conn.execute("UPDATE collection_candidates SET parser_version='reviewed-parser' WHERE id=%s",
                     (candidate_id,))
    reviewed_duplicate = post_page(client)
    assert reviewed_duplicate.status_code == 200
    assert reviewed_duplicate.json()['candidate']['parser_version'] == 'reviewed-parser'
    assert reviewed_duplicate.json()['candidate']['review_status'] == 'approved'


def test_corrected_non_exact_price_can_be_approved_with_audit_warning(api):
    client, scoped_url = api
    html = ('<html><body><main>小区：东湖花园 建筑面积：120㎡ '
            '挂牌价约200万</main></body></html>')
    staged = post_page(client, html=html)
    assert staged.status_code == 200
    candidate_id = staged.json()['candidate']['id']
    original_fields = staged.json()['candidate']['extracted_fields']
    assert original_fields['asking_price_wan'] is None
    assert 'non_exact_asking_price' in staged.json()['candidate']['warnings']

    corrected = client.patch(
        f'/api/collection/candidates/{candidate_id}',
        headers={'X-API-Key': API_KEY},
        json={'asking_price_wan': 200, 'review_note': '对照保存页面确认挂牌价'},
    )
    assert corrected.status_code == 200
    corrected_fields = corrected.json()['extracted_fields']
    assert corrected_fields['asking_price_wan'] == 200
    assert corrected_fields['field_evidence']['asking_price_wan'] == {
        'value': 200, 'source': 'manual_review', 'mentions': [],
        'mention_count': 0, 'mentions_truncated': False,
    }
    assert 'non_exact_asking_price' in corrected.json()['warnings']

    with connect_test_db(scoped_url) as conn:
        stored = conn.execute('''SELECT extracted_fields,warnings FROM collection_candidates
          WHERE id=%s''', (candidate_id,)).fetchone()
    assert stored['extracted_fields']['asking_price_wan'] == 200
    assert stored['extracted_fields']['field_evidence']['asking_price_wan']['source'] == 'manual_review'
    assert stored['extracted_fields']['field_evidence']['asking_price_wan']['mentions'] == []
    assert 'non_exact_asking_price' in stored['warnings']

    replayed = post_page(client, html=html)
    assert replayed.status_code == 200
    replayed_candidate = replayed.json()['candidate']
    assert replayed_candidate['id'] == candidate_id
    assert replayed_candidate['extracted_fields']['asking_price_wan'] == 200
    assert replayed_candidate['extracted_fields']['field_evidence']['asking_price_wan']['source'] == 'manual_review'
    assert replayed_candidate['extracted_fields']['field_evidence']['asking_price_wan']['mentions'] == []
    assert 'non_exact_asking_price' in replayed_candidate['warnings']

    approved = client.post(
        f'/api/collection/candidates/{candidate_id}/review?decision=approve&note=人工核对挂牌价',
        headers={'X-API-Key': API_KEY},
    )
    assert approved.status_code == 200
    listings = client.get('/api/listings', headers={'X-API-Key': API_KEY}).json()
    assert len(listings) == 1
    assert listings[0]['asking_price_wan'] == 200
    prices = client.get(
        f"/api/listings/{listings[0]['id']}/prices", headers={'X-API-Key': API_KEY},
    ).json()
    assert len(prices) == 1
    assert prices[0]['price_wan'] == 200


@pytest.mark.parametrize('price_text', ['挂牌价：>=200万', '总价：≤200万'])
def test_inequality_price_candidate_evidence_is_persisted(api, price_text):
    client, scoped_url = api
    html = ('<html><body><main>小区：东湖花园 建筑面积：120㎡ '
            f'{price_text}</main></body></html>')

    response = post_page(client, html=html)

    assert response.status_code == 200
    candidate = response.json()['candidate']
    assert candidate['review_status'] == 'pending'
    assert response.json()['ready_for_review'] is False
    fields = candidate['extracted_fields']
    assert fields['asking_price_wan'] is None
    assert 'non_exact_asking_price' in candidate['warnings']
    mention = fields['field_evidence']['asking_price_wan']['mentions'][0]
    assert mention['candidate_value'] == '200'
    assert mention['quote'] == price_text
    assert mention['is_non_exact'] is True

    with connect_test_db(scoped_url) as conn:
        stored = conn.execute('''SELECT extracted_fields,warnings,raw_sha256,raw_storage_path
          FROM collection_candidates WHERE id=%s''', (candidate['id'],)).fetchone()
    assert stored['extracted_fields'] == fields
    assert 'non_exact_asking_price' in stored['warnings']
    assert stored['raw_sha256'] == sha256(html.encode('utf-8')).hexdigest()
    with gzip.open(stored['raw_storage_path'], 'rb') as saved:
        assert saved.read() == html.encode('utf-8')


def test_duplicate_pending_candidate_reparses_when_parser_version_changes(api):
    client, scoped_url = api
    html = ('<html><body><main>小区：东湖花园 建筑面积：160㎡ '
            '合同总价：300万</main></body></html>')
    first = post_page(client, html=html)
    assert first.status_code == 200
    candidate_id = first.json()['candidate']['id']
    with connect_test_db(scoped_url) as conn:
        conn.execute('''UPDATE collection_candidates SET parser_version='generic-labelled-v0.2.0',
          extracted_fields=jsonb_set(jsonb_set(extracted_fields,'{community_name}',
            '"stale value"'::jsonb),'{asking_price_wan}','300'::jsonb),
          warnings='[]'::jsonb
          WHERE id=%s''', (candidate_id,))

    duplicate = post_page(client, html=html)
    assert duplicate.status_code == 200
    candidate = duplicate.json()['candidate']

    assert candidate['id'] == candidate_id
    assert candidate['review_status'] == 'pending'
    assert candidate['parser_version'] == PARSER_VERSION
    assert candidate['extracted_fields']['community_name'] == '东湖花园'
    assert candidate['extracted_fields']['asking_price_wan'] is None
    assert 'missing_asking_price_wan' in candidate['warnings']


def test_duplicate_candidate_does_not_overwrite_manual_correction(api):
    client, scoped_url = api
    first = post_page(client)
    candidate_id = first.json()['candidate']['id']
    corrected = client.patch(f'/api/collection/candidates/{candidate_id}',
        headers={'X-API-Key': API_KEY}, json={
            'community_name': '人工复核小区', 'review_note': '按页面证据人工更正小区名称'})
    assert corrected.status_code == 200
    assert corrected.json()['extracted_fields']['field_evidence']['community_name'] == {
        'value': '人工复核小区', 'source': 'manual_review', 'mentions': [],
        'mention_count': 0, 'mentions_truncated': False}
    with connect_test_db(scoped_url) as conn:
        conn.execute("UPDATE collection_candidates SET parser_version='generic-labelled-v0.2.0' WHERE id=%s",
                     (candidate_id,))

    duplicate = post_page(client)
    assert duplicate.status_code == 200
    candidate = duplicate.json()['candidate']

    assert candidate['id'] == candidate_id
    assert candidate['parser_version'] == 'generic-labelled-v0.2.0'
    assert candidate['extracted_fields']['community_name'] == '人工复核小区'
    assert candidate['extracted_fields']['manually_corrected'] is True


def test_opportunities_returns_cross_platform_price_gap_candidates(api):
    from datetime import datetime, timezone

    client, scoped_url = api
    headers = {'X-API-Key': API_KEY}
    community = 'Cross-platform integration ' + uuid4().hex
    observed_at = datetime.now(timezone.utc).isoformat()
    common = {
        'community_name': community,
        'district': '鄞州',
        'bedrooms': 3,
        'observed_at': observed_at,
    }
    beike = client.post('/api/listings', headers=headers, json={
        **common, 'source': 'beike', 'source_listing_id': str(uuid4().int),
        'area_sqm': 100, 'asking_price_wan': 100,
        'listing_url': 'https://example.invalid/beike',
    })
    anjuke = client.post('/api/listings', headers=headers, json={
        **common, 'source': 'anjuke', 'source_listing_id': str(uuid4().int),
        'area_sqm': 105, 'asking_price_wan': 115.5,
        'listing_url': 'https://example.invalid/anjuke',
    })
    assert beike.status_code == anjuke.status_code == 200
    assert beike.json()['listing']['property_id'] != anjuke.json()['listing']['property_id']

    response = client.get('/api/opportunities', headers=headers)

    assert response.status_code == 200
    results = response.json()
    assert len(results) == 2
    for result in results:
        assert 'cross_platform_price_gap' in result['signals']
        peer, = result['cross_platform_price_gaps']
        assert peer['unit_price_gap_pct'] == 10.0
        assert peer['area_difference_pct'] == 5.0
        assert peer['verification_status'] == 'candidate'
        assert peer['listing_url'].startswith('https://example.invalid/')

    with connect_test_db(scoped_url) as conn:
        assert conn.execute('''SELECT count(DISTINCT property_id) AS count
          FROM source_listings WHERE source_listing_id IN (%s,%s)''',
          (beike.json()['listing']['source_listing_id'],
           anjuke.json()['listing']['source_listing_id'])).fetchone()['count'] == 2


def test_opportunities_ignores_future_dated_listing_candidates(api):
    from datetime import datetime, timedelta, timezone

    client, _ = api
    headers = {'X-API-Key': API_KEY}
    community = 'Future listing integration ' + uuid4().hex
    common = {'community_name': community, 'district': '鄞州', 'bedrooms': 3}
    current = datetime.now(timezone.utc)
    listings = [
        {
            **common, 'source': 'beike', 'source_listing_id': str(uuid4().int),
            'area_sqm': 100, 'asking_price_wan': 100,
            'observed_at': current.isoformat(),
        },
        {
            **common, 'source': 'anjuke', 'source_listing_id': str(uuid4().int),
            'area_sqm': 100, 'asking_price_wan': 120,
            'observed_at': (current + timedelta(days=1)).isoformat(),
        },
    ]
    for payload in listings:
        response = client.post('/api/listings', headers=headers, json=payload)
        assert response.status_code == 200

    response = client.get('/api/opportunities', headers=headers)

    assert response.status_code == 200
    assert response.json() == []


def test_failed_candidate_approval_rolls_back_listing_and_price(api):
    client, scoped_url = api
    candidate_id = post_page(client).json()['candidate']['id']
    with connect_test_db(scoped_url) as conn:
        conn.execute('''CREATE FUNCTION reject_approval() RETURNS trigger LANGUAGE plpgsql AS $$
          BEGIN RAISE EXCEPTION 'injected approval failure'; END $$''')
        conn.execute('''CREATE TRIGGER reject_approval BEFORE UPDATE OF review_status
          ON collection_candidates FOR EACH ROW
          WHEN (NEW.review_status='approved') EXECUTE FUNCTION reject_approval()''')

    response = client.post(
        f'/api/collection/candidates/{candidate_id}/review?decision=approve&note=人工核对样本',
        headers={'X-API-Key': API_KEY})
    assert response.status_code == 500
    assert client.get('/api/listings', headers={'X-API-Key': API_KEY}).json() == []
    with connect_test_db(scoped_url) as conn:
        state = conn.execute('''SELECT review_status,approved_listing_id
          FROM collection_candidates WHERE id=%s''', (candidate_id,)).fetchone()
        assert state['review_status'] == 'pending'
        assert state['approved_listing_id'] is None
        assert conn.execute('SELECT count(*) FROM price_history').fetchone()['count'] == 0


def test_backfill_keeps_latest_price_and_price_drop_notification_is_deduplicated(api):
    from datetime import datetime, timezone
    from app import services

    client, scoped_url = api
    headers = {'X-API-Key': API_KEY}
    search = client.post('/api/saved-searches', headers=headers, json={
        'name': 'integration test', 'district': '鄞州', 'community_name': '东湖花园',
        'max_price_wan': 400, 'min_drop_pct': 1, 'notifications_enabled': True,
    })
    assert search.status_code == 200
    base = {
        'source': 'agent', 'source_listing_id': 'integration-' + uuid4().hex,
        'community_name': '东湖花园', 'district': '鄞州', 'area_sqm': 158.6,
        'bedrooms': 4, 'asking_price_wan': 365, 'listing_url': 'https://example.invalid/demo',
    }
    first_time = '2025-01-02T10:00:00Z'
    created = client.post('/api/listings', headers=headers,
                          json={**base, 'observed_at': first_time})
    assert created.status_code == 200
    listing_id = created.json()['listing']['id']

    dropped = client.post('/api/listings', headers=headers, json={
        **base, 'observed_at': '2025-01-03T10:00:00Z', 'asking_price_wan': 350,
    })
    assert dropped.status_code == 200 and dropped.json()['price_changed'] is True
    duplicate_time = datetime(2025, 1, 3, 10, tzinfo=timezone.utc)
    with connect_test_db(scoped_url) as conn:
        services.queue_notifications(conn, listing_id, 'price_drop', duplicate_time, 365)

    backfill = client.post('/api/listings', headers=headers, json={
        **base, 'observed_at': '2024-12-31T10:00:00Z', 'asking_price_wan': 370,
    })
    assert backfill.status_code == 200 and backfill.json()['historical_only'] is True
    listings = client.get('/api/listings', headers=headers).json()
    assert len(listings) == 1 and listings[0]['asking_price_wan'] == 350
    prices = client.get(f'/api/listings/{listing_id}/prices', headers=headers).json()
    assert [x['price_wan'] for x in prices] == [370, 365, 350]
    notifications = client.get('/api/notifications', headers=headers).json()
    assert len(notifications) == 2
    assert {x['event_type'] for x in notifications} == {'new_listing', 'price_drop'}


def test_saved_search_new_filters_persist_and_preference_is_reported(api):
    client, scoped_url = api
    headers = {'X-API-Key': API_KEY}
    response = client.post('/api/saved-searches', headers=headers, json={
        'name': '区域筛选', 'districts': ['鄞州', '海曙'],
        'preferred_communities': ['东湖花园'],
        'excluded_communities': ['锦港府'], 'max_listing_age_days': 30,
    })
    assert response.status_code == 200
    saved = response.json()
    assert saved['districts'] == ['鄞州', '海曙']
    assert saved['preferred_communities'] == ['东湖花园']
    assert saved['excluded_communities'] == ['锦港府']
    assert saved['max_listing_age_days'] == 30

    listing_response = client.post('/api/listings', headers=headers, json={
        'source': 'agent', 'source_listing_id': 'preferred-' + uuid4().hex,
        'community_name': '东湖花园', 'district': '鄞州', 'area_sqm': 100,
        'bedrooms': 3, 'asking_price_wan': 300,
    })
    assert listing_response.status_code == 200
    notification = client.get('/api/notifications', headers=headers).json()[0]
    assert notification['payload']['preferred_community'] is True

    with connect_test_db(scoped_url) as conn:
        row = conn.execute('''SELECT districts,preferred_communities,excluded_communities,
          max_listing_age_days FROM saved_searches WHERE id=%s''', (saved['id'],)).fetchone()
    assert row == {'districts': ['鄞州', '海曙'], 'preferred_communities': ['东湖花园'],
                   'excluded_communities': ['锦港府'], 'max_listing_age_days': 30}


def test_saved_search_matches_return_hard_matches_with_preference_order(api):
    client, _ = api
    headers = {'X-API-Key': API_KEY}
    search = client.post('/api/saved-searches', headers=headers, json={
        'name': '可执行条件单', 'districts': ['鄞州', '海曙'],
        'preferred_communities': ['锦港府'], 'excluded_communities': ['万科里'],
        'max_price_wan': 400, 'min_area_sqm': 80, 'min_bedrooms': 2,
        'max_listing_age_days': 30, 'notifications_enabled': False,
    })
    assert search.status_code == 200
    search_id = search.json()['id']
    now = datetime.now(timezone.utc)
    listings = [
        ('锦港府', '海曙', 300, 100, 3, now),
        ('东湖花园', '鄞州', 380, 90, 2, now),
        ('万科里', '鄞州', 300, 100, 3, now),
        ('江湾城', '海曙', 300, 100, 3, now - timedelta(days=31)),
    ]
    for community, district, price, area, bedrooms, observed_at in listings:
        response = client.post('/api/listings', headers=headers, json={
            'source': 'agent', 'source_listing_id': 'search-' + uuid4().hex,
            'community_name': community, 'district': district,
            'asking_price_wan': price, 'area_sqm': area, 'bedrooms': bedrooms,
            'observed_at': observed_at.isoformat(),
        })
        assert response.status_code == 200

    limited = client.get(f'/api/saved-searches/{search_id}/matches?limit=1', headers=headers)
    assert limited.status_code == 200
    assert limited.json()['total'] == 2
    assert len(limited.json()['matches']) == 1
    assert limited.json()['matches'][0]['community_name'] == '锦港府'
    assert limited.json()['matches'][0]['preferred_community'] is True
    assert limited.json()['matches'][0]['match_reasons'] == [
        '区域匹配：海曙', '总价300万元，不超过上限400万元',
        '面积100㎡，达到下限80㎡', '户型3室，达到至少2室',
        '最近30天内有更新', '命中偏好小区：锦港府',
    ]

    complete = client.get(f'/api/saved-searches/{search_id}/matches', headers=headers).json()
    assert complete['total'] == 2
    assert {row['community_name'] for row in complete['matches']} == {'锦港府', '东湖花园'}
    assert {row['community_name']: row['preferred_community'] for row in complete['matches']} == {
        '锦港府': True, '东湖花园': False,
    }
    assert '命中偏好小区：锦港府' in complete['matches'][0]['match_reasons']
    assert all('命中偏好小区：' not in ' '.join(row['match_reasons'])
               for row in complete['matches'] if not row['preferred_community'])
    missing = client.get(f'/api/saved-searches/{uuid4()}/matches', headers=headers)
    assert missing.status_code == 404


def test_readonly_schema_checker_matches_pg17_migration_schema(api):
    from scripts.check_schema import inspect_schema

    _, scoped_url = api
    with connect_test_db(scoped_url) as conn:
        (
            schema, missing_tables, missing_columns, missing_functions,
            missing_triggers, missing_constraints, unbacked_sweep_ids,
        ) = inspect_schema(conn)

    assert schema.startswith('it_')
    assert missing_tables == []
    assert missing_columns == []
    assert missing_functions == []
    assert missing_triggers == []
    assert missing_constraints == []
    assert unbacked_sweep_ids == 0
