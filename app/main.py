"""Single-operator backend. X-API-Key required for all business endpoints."""
from contextlib import asynccontextmanager
import secrets
from decimal import Decimal
from typing import Literal
from uuid import UUID
from fastapi import FastAPI, Depends, HTTPException, Path, Query
from fastapi.security import APIKeyHeader
from app.db import session
from app import services
from app import comparables
from app.models import (AccountIn,AccountPatch,CommunityIn,ListingIn,SavedSearchIn,
                        VideoIn,VideoEnrichment,VideoBatch)
from app.settings import APP_API_KEY
from app import collection_service
from app.body_limits import CollectionPageBodyLimitMiddleware
from app.collectors.parser import CollectionError
from app.collection_models import (HTMLPageIn,CollectionTargetIn,CollectionTargetPatch,
                                   PolicyReviewIn,CandidateCorrection,DiscoveryStateIn,
                                   DiscoveryReviewIn)
from app.admin_ui import router as admin_ui_router
from app.media_upload_api import (AdminSourceAllowlistMiddleware,
                                  UploadBodyLimitMiddleware,
                                  router as media_upload_router)
from app.video_upload_service import start_upload_worker, stop_upload_worker

@asynccontextmanager
async def lifespan(_app):
    try:
        start_upload_worker()
    except Exception as exc:  # noqa: BLE001 - upload storage must not prevent the rest of the API from starting
        from app.log_safety import safe_error_summary
        import logging
        logging.getLogger('media_uploads').error(
            'video upload worker is unavailable: %s',
            safe_error_summary(exc, 'media upload startup'))
    try:
        yield
    finally:
        stop_upload_worker()


app=FastAPI(title='宁波房产 AI 数据平台 - V0.2',version='0.2.0',
    lifespan=lifespan,
    description='指定账号监控 / 贝壳安居客采集候选审核 / 历史挂牌价 / 条件单 / 提醒事件（未接外部发送）')
app.add_middleware(CollectionPageBodyLimitMiddleware)
app.add_middleware(UploadBodyLimitMiddleware)
app.add_middleware(AdminSourceAllowlistMiddleware)
app.include_router(admin_ui_router)


api_key_header=APIKeyHeader(name='X-API-Key',auto_error=False)

def auth(x_api_key: str | None = Depends(api_key_header)):
    if not APP_API_KEY:
        raise HTTPException(status_code=503,detail='APP_API_KEY is not configured')
    if not x_api_key or not secrets.compare_digest(x_api_key,APP_API_KEY):
        raise HTTPException(status_code=401,detail='Invalid X-API-Key')


app.include_router(media_upload_router, dependencies=[Depends(auth)])


@app.get('/healthz',tags=['system'])
def healthz():
    with session() as conn:
        row=conn.execute("SELECT to_regclass('public.collection_candidates') AS candidates").fetchone()
    if not row['candidates']:
        raise HTTPException(status_code=503,detail='V0.2 schema missing: apply sql/002_collection_pipeline.sql')
    return {'ok':True,'service':'ningbo-re-ai-v0.2','schema':'v0.2'}


@app.post('/api/accounts',dependencies=[Depends(auth)],tags=['accounts'])
def add_account(payload: AccountIn):
    return services.create_account(payload)


@app.get('/api/accounts',dependencies=[Depends(auth)],tags=['accounts'])
def accounts():
    return services.all_accounts()


@app.patch('/api/accounts/{account_id}',dependencies=[Depends(auth)],tags=['accounts'])
def edit_account(account_id:UUID,payload: AccountPatch):
    return services.update_account(account_id,payload)


@app.post('/api/accounts/{account_id}/poll',dependencies=[Depends(auth)],tags=['accounts'])
def trigger_poll(account_id:UUID):
    return {'scheduled':True,'account':services.queue_account_poll(account_id)}


@app.post('/api/accounts/{account_id}/backfill',dependencies=[Depends(auth)],tags=['accounts'])
def request_backfill(account_id:UUID,history_mode:Literal['30d','90d']=Query(...)):
    return {'scheduled':True,'account':services.queue_account_poll(account_id,history_mode)}


@app.get('/api/accounts/{account_id}/runs',dependencies=[Depends(auth)],tags=['accounts'])
def runs(account_id:UUID,limit:int=Query(20,ge=1,le=100)):
    return services.recent_runs(account_id,limit)


@app.post('/api/ingest/videos',dependencies=[Depends(auth)],tags=['videos'])
def ingest_video(payload: VideoIn):
    return services.video_upsert(payload)


@app.post('/api/ingest/videos/batch',dependencies=[Depends(auth)],tags=['videos'])
def ingest_videos(payload: VideoBatch):
    rows=services.batch_videos(payload.items)
    return {'count':len(rows),'video_ids':[x['id'] for x in rows]}


@app.get('/api/videos',dependencies=[Depends(auth)],tags=['videos'])
def get_videos(platform:Literal['douyin','wechat_channels'] | None=None,
               account_id:UUID | None=None,limit:int=Query(50,ge=1,le=200)):
    return services.list_videos(platform,account_id,limit)


@app.patch('/api/videos/{video_id}/enrichment',dependencies=[Depends(auth)],tags=['videos'])
def enrich_video(video_id:UUID,payload:VideoEnrichment):
    return services.enrich_video(video_id,payload)


@app.post('/api/communities',dependencies=[Depends(auth)],tags=['real-estate'])
def create_community(payload:CommunityIn):
    return services.create_community(payload)


@app.get('/api/communities',dependencies=[Depends(auth)],tags=['real-estate'])
def get_communities(query:str | None=None):
    return services.list_communities(query)


@app.post('/api/listings',dependencies=[Depends(auth)],tags=['real-estate'])
def ingest_listing(payload:ListingIn):
    return services.upsert_listing(payload)


@app.get('/api/listings',dependencies=[Depends(auth)],tags=['real-estate'])
def get_listings(district:str | None=None,community_name:str | None=None,
                 max_price_wan:Decimal | None=Query(default=None,gt=0),
                 min_area_sqm:Decimal | None=Query(default=None,gt=0),
                 min_bedrooms:int | None=Query(default=None,ge=0,le=20),
                 limit:int=Query(default=100,ge=1,le=300)):
    return services.listings(district,max_price_wan,min_area_sqm,min_bedrooms,community_name,limit)


@app.get('/api/listings/{listing_id}/prices',dependencies=[Depends(auth)],tags=['real-estate'])
def get_listing_prices(listing_id:UUID):
    return services.listing_prices(listing_id)


@app.post('/api/saved-searches',dependencies=[Depends(auth)],tags=['saved-searches'])
def save_search(payload:SavedSearchIn):
    return services.create_saved_search(payload)


@app.get('/api/saved-searches',dependencies=[Depends(auth)],tags=['saved-searches'])
def searches():
    return services.all_saved_searches()


@app.get('/api/saved-searches/{search_id}/matches',dependencies=[Depends(auth)],tags=['saved-searches'])
def get_saved_search_matches(search_id:UUID,limit:int=Query(100,ge=1,le=300)):
    return services.saved_search_matches(search_id,limit)


@app.get('/api/opportunities',dependencies=[Depends(auth)],tags=['saved-searches'])
def get_opportunities(days:Literal[7,30,90]=Query(30),
                     min_drop_pct:float=Query(5,ge=0,le=100),
                     min_discount_pct:float=Query(8,ge=0,le=100),
                     limit:int=Query(100,ge=1,le=300)):
    return services.opportunities(days,min_drop_pct,min_discount_pct,limit)


@app.get('/api/notifications',dependencies=[Depends(auth)],tags=['saved-searches'])
def get_notifications(status:Literal['pending','read']='pending',limit:int=Query(100,ge=1,le=300)):
    return services.notifications(status,limit)


@app.post('/api/notifications/{event_id}/read',dependencies=[Depends(auth)],tags=['saved-searches'])
def read_notification(event_id:int):
    return services.mark_notification_read(event_id)


@app.post('/api/videos/{video_id}/match-candidates',dependencies=[Depends(auth)],tags=['real-estate'])
def match_video(video_id:UUID,limit:int=Query(20,ge=1,le=100)):
    return services.match_video_candidates(video_id,limit)


@app.post('/api/property-matches/{match_id}/review',dependencies=[Depends(auth)],tags=['real-estate'])
def review_match(match_id:int,status:Literal['confirmed','rejected']=Query(...)):
    return services.review_match(match_id,status)


# === Collection source policy / staged listing evidence ===
# Public website collection is NOT automatically authorized. Online is OFF by default.

@app.get('/api/collection/sources',dependencies=[Depends(auth)],tags=['collection'])
def get_collection_sources():
    return collection_service.sources()


@app.get('/api/collection/health',dependencies=[Depends(auth)],tags=['collection'])
def get_collection_health():
    return collection_service.health_metrics()


@app.get('/api/collection/discovery-observations',dependencies=[Depends(auth)],tags=['collection'])
def get_collection_discovery_observations(
        source:Literal['beike','anjuke'] | None=None,
        target_id:UUID | None=None,
        review_status:Literal['active','pending_review','reviewed'] | None=None,
        limit:int=Query(100,ge=1,le=200),offset:int=Query(0,ge=0,le=1000000)):
    return collection_service.discovery_observations(source,target_id,review_status,
                                                     limit,offset)


@app.post('/api/collection/targets/{target_id}/discovery-observations/{source_listing_id}/reviews',
          dependencies=[Depends(auth)],tags=['collection'])
def review_discovery_observation(
        target_id:UUID,
        payload:DiscoveryReviewIn,
        source_listing_id:str=Path(min_length=7,max_length=220,pattern=r'^[0-9]+$')):
    return collection_service.record_discovery_review(
        target_id,source_listing_id,payload)


@app.get('/api/collection/targets/{target_id}/discovery-observations/{source_listing_id}/reviews',
         dependencies=[Depends(auth)],tags=['collection'])
def get_discovery_reviews(
        target_id:UUID,
        source_listing_id:str=Path(min_length=7,max_length=220,pattern=r'^[0-9]+$'),
        limit:int=Query(50,ge=1,le=200),
        offset:int=Query(0,ge=0,le=1000000)):
    return collection_service.discovery_reviews(target_id,source_listing_id,limit,offset)


@app.post('/api/collection/sources/{source}/policy-review',dependencies=[Depends(auth)],tags=['collection'])
def policy_review(source:Literal['beike','anjuke'], payload:PolicyReviewIn):
    return collection_service.update_source_policy(source,payload)


@app.post('/api/collection/pages',dependencies=[Depends(auth)],tags=['collection'])
def collect_saved_html(payload:HTMLPageIn):
    try:
        return collection_service.stage_manual_page(payload)
    except CollectionError as exc:
        raise HTTPException(422,str(exc)) from exc


@app.get('/api/collection/candidates',dependencies=[Depends(auth)],tags=['collection'])
def collection_candidates(status:Literal['pending','approved','rejected']='pending',
                          source:Literal['beike','anjuke'] | None=None,
                          limit:int=Query(50,ge=1,le=200)):
    return collection_service.candidates(status,source,limit)


@app.patch('/api/collection/candidates/{candidate_id}',dependencies=[Depends(auth)],tags=['collection'])
def correct_collection_candidate(candidate_id:UUID,payload:CandidateCorrection):
    return collection_service.correct_candidate(candidate_id,payload)


@app.post('/api/collection/candidates/{candidate_id}/review',dependencies=[Depends(auth)],tags=['collection'])
def review_collection_candidate(candidate_id:UUID,decision:Literal['approve','reject']=Query(...),
                                note:str=Query(...,min_length=5,max_length=1000)):
    return collection_service.review_candidate(candidate_id,decision,note)


@app.post('/api/collection/targets',dependencies=[Depends(auth)],tags=['collection'])
def create_collection_target(payload:CollectionTargetIn):
    return collection_service.create_target(payload)


@app.get('/api/collection/targets',dependencies=[Depends(auth)],tags=['collection'])
def list_collection_targets():
    return collection_service.get_targets()


@app.patch('/api/collection/targets/{target_id}',dependencies=[Depends(auth)],tags=['collection'])
def update_collection_target(target_id:UUID,payload:CollectionTargetPatch):
    return collection_service.update_target(target_id,payload)


@app.get('/api/collection/targets/{target_id}/discovery-state',
         dependencies=[Depends(auth)],tags=['collection'])
def get_collection_discovery_state(target_id:UUID):
    return collection_service.get_discovery_state(target_id)


@app.put('/api/collection/targets/{target_id}/discovery-state',
         dependencies=[Depends(auth)],tags=['collection'])
def save_collection_discovery_state(target_id:UUID,payload:DiscoveryStateIn):
    return collection_service.save_discovery_state(target_id,payload)


@app.post('/api/collection/targets/{target_id}/check',dependencies=[Depends(auth)],tags=['collection'])
def check_collection_target(target_id:UUID):
    return collection_service.request_target_check(target_id)


@app.get('/api/collection/runs',dependencies=[Depends(auth)],tags=['collection'])
def get_collection_runs(target_id:UUID | None=None,limit:int=Query(30,ge=1,le=100)):
    return collection_service.recent_collection_runs(target_id,limit)


@app.get('/api/value/comparables',dependencies=[Depends(auth)],tags=['valuation'])
def get_comparable_listing_prices(
        community_name:str=Query(min_length=2,max_length=180),
        area_sqm:Decimal=Query(gt=0,le=20000),
        bedrooms:int | None=Query(default=None,ge=0,le=20),
        area_tolerance_pct:Decimal=Query(default=Decimal('10'),gt=0,le=30),
        asking_price_wan:Decimal | None=Query(default=None,gt=0),
        limit:int=Query(default=30,ge=1,le=100)):
    return comparables.analyze_listings(
        community_name,area_sqm,bedrooms,area_tolerance_pct,asking_price_wan,limit)
