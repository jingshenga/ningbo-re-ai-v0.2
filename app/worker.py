"""Single low-concurrency account poller; does NOT crawl WeChat Channels."""
import logging
import time
from datetime import timedelta
from app.db import session
from app.dtk import DtkClient, DtkError, normalize_post
from app.services import now_utc, video_upsert_conn
from app.settings import DTK_BASE_URL, DTK_API_KEY, COLLECTION_MIN_DELAY_SECONDS
from app.collection_service import claim_due_target,run_collection_target
from app.log_safety import safe_error_summary

logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
log=logging.getLogger('account-worker')


def claim_due_account():
    """Advance schedule atomically before networking; prevents duplicate worker claims."""
    with session() as conn:
        row=conn.execute('''SELECT * FROM monitored_accounts
           WHERE enabled AND collector_mode='dtk' AND next_poll_at<=now()
           ORDER BY next_poll_at LIMIT 1 FOR UPDATE SKIP LOCKED''').fetchone()
        if not row:
            return None
        conn.execute('''UPDATE monitored_accounts SET
          next_poll_at=now()+(poll_interval_minutes * interval '1 minute'),
          updated_at=now() WHERE id=%s''',(row['id'],))
        return row


def start_run(account_id):
    with session() as conn:
        row=conn.execute('''INSERT INTO account_sync_runs(account_id,status)
          VALUES(%s,'running') RETURNING id''',(account_id,)).fetchone()
        return row['id']


def finish_run(account_id,run_id,status,pages=0,observed=0,new_count=0,error=None,
               initial_sync_complete=False):
    with session() as conn:
        conn.execute('''UPDATE account_sync_runs SET finished_at=now(),status=%s,pages=%s,
          observed_count=%s,new_count=%s,error_text=%s WHERE id=%s''',
          (status,pages,observed,new_count,error,run_id))
        conn.execute('''UPDATE monitored_accounts SET last_status=%s,last_error=%s,
          last_success_at=CASE WHEN %s IN ('success','partial') THEN now() ELSE last_success_at END,
          initial_synced=initial_synced OR %s, updated_at=now() WHERE id=%s''',
          (status,error,status,initial_sync_complete,account_id))


def persist_history_backfill(account_id, cursor, cutoff):
    with session() as conn:
        conn.execute('''UPDATE monitored_accounts SET history_backfill_cursor=%s,
          history_backfill_cutoff=%s,
          initial_synced=initial_synced OR (%s IS NULL AND %s IS NULL),
          updated_at=now() WHERE id=%s''',
          (cursor,cutoff,cursor,cutoff,account_id))


def store_page(account,items,first_run,cutoff):
    """Returns (observed, new, already_seen, invalid, unknown_date)."""
    observed=new_count=already_seen=invalid=unknown_date=0
    with session() as conn:
        for item in items:
            record=normalize_post(item)
            if not record:
                invalid+=1
                field_count=len(item) if isinstance(item,dict) else 0
                log.warning('DTK normalized item without stable post ID; skipped, object_type=%s field_count=%s',
                            type(item).__name__,field_count)
                continue
            observed+=1
            if first_run and cutoff and not record.get('published_at'):
                unknown_date+=1
            post_id=record['source_post_id']
            old=conn.execute('''SELECT baseline_only FROM account_seen_posts
              WHERE platform='douyin' AND source_post_id=%s''',(post_id,)).fetchone()
            if old:
                already_seen+=1
            # First scan / history_mode=none sets a baseline but does NOT ingest old content.
            baseline=first_run and account['history_mode']=='none'
            if first_run and cutoff:
                # Unknown publish time is NOT enough evidence for a 30/90-day historical import.
                if not record.get('published_at') or record['published_at']<cutoff:
                    baseline=True
            conn.execute('''INSERT INTO account_seen_posts(platform,source_post_id,account_id,baseline_only)
              VALUES('douyin',%s,%s,%s)
              ON CONFLICT(platform,source_post_id) DO UPDATE SET
                baseline_only=account_seen_posts.baseline_only AND EXCLUDED.baseline_only''',
                (post_id,account['id'],baseline))
            # An older baseline can be imported later via an explicit backfill request.
            import_video=(not baseline) and (not old or old['baseline_only'])
            if import_video:
                record['account_id']=account['id']
                video_upsert_conn(conn,record)
                new_count+=1
    return observed,new_count,already_seen,invalid,unknown_date


def run_account(account):
    """Sync one account against DTK v5; status semantics recorded in account_sync_runs:

    success  - every requested page was read and no degradation signal appeared;
               baseline mode (history_mode='none') intentionally reads one page,
               so an upstream has_more there is expected, not partial.
    partial  - data returned but confidence is reduced (guest_fallback feed, skipped
               items without stable IDs, unknown publish dates during backfill,
               missing pagination cursor, or page cap while more posts remain).
               new_count==0 with status partial must be read as "unknown, possibly
               missed", never as "no updates".
    failed   - an exception aborted the run; pages/observed/new keep what was
               collected before the error; the account stays enabled and is
               retried at its next regular poll because the claim advanced
               next_poll_at before any network call.
    blocked_config - DTK_BASE_URL/DTK_API_KEY unset; no network attempt is made.
    """
    run_id=start_run(account['id'])
    pages=seen=new=0
    if not DTK_BASE_URL or not DTK_API_KEY:
        reason='DTK connector not configured; update DTK_BASE_URL and DTK_API_KEY'
        finish_run(account['id'],run_id,'blocked_config',error=reason)
        log.warning('Account %s blocked: %s',account['id'],reason)
        return
    first_run=not account['initial_synced']
    cutoff=None
    cursor=None
    if first_run and account['history_mode']!='none':
        cutoff=account.get('history_backfill_cutoff')
        if cutoff is None:
            cutoff=now_utc()-timedelta(days=30 if account['history_mode']=='30d' else 90)
        cursor=account.get('history_backfill_cursor')
    max_pages=1 if first_run and account['history_mode']=='none' else 5
    partial=False
    warnings=[]
    initial_sync_complete=(first_run and account['history_mode']=='none')
    try:
        if first_run and cutoff:
            persist_history_backfill(account['id'],cursor,cutoff)
        client=DtkClient(DTK_BASE_URL,DTK_API_KEY)
        try:
            for i in range(max_pages):
                page=client.author_posts(account['account_ref'],cursor)
                pages+=1
                partial=partial or page.guest_fallback
                if page.guest_fallback and 'DTK guest_fallback: feed may omit newest posts' not in warnings:
                    warnings.append('DTK guest_fallback: feed may omit newest posts')
                obs,added,already,invalid,unknown_date=store_page(account,page.items,first_run,cutoff)
                seen+=obs; new+=added
                if invalid:
                    partial=True
                    warnings.append(f"{invalid} upstream items lacked stable post IDs and were skipped")
                if unknown_date:
                    partial=True
                    warnings.append(f"{unknown_date} items lacked publish times during history backfill")
                if not page.has_more:
                    if first_run and cutoff:
                        persist_history_backfill(account['id'],None,None)
                        initial_sync_complete=True
                    break
                if not page.next_cursor:
                    partial=True
                    warnings.append('DTK indicated more posts without a pagination cursor')
                    break
                # On a regular incremental sync, stop after encountering the previous baseline.
                if not first_run and already>0:
                    break
                if page.next_cursor==cursor:
                    raise DtkError('Upstream pagination cursor did not advance')
                if first_run and cutoff:
                    persist_history_backfill(account['id'],page.next_cursor,cutoff)
                if i == max_pages-1 and not (first_run and account['history_mode']=='none'):
                    partial=True
                    warnings.append('Page limit reached while upstream still has more posts')
                    break
                cursor=page.next_cursor
                time.sleep(1.0)  # avoid dense backfill bursts
        finally:
            client.close()
        status='partial' if partial else 'success'
        if partial and not warnings:
            warnings.append('DTK guest_fallback: author feed may omit newest posts; login coverage needed')
        warning='; '.join(warnings) if warnings else None
        finish_run(account['id'],run_id,status,pages,seen,new,warning,
                   initial_sync_complete=initial_sync_complete)
        log.info('poll %s %s, pages=%s observed=%s new=%s',account['id'],status,pages,seen,new)
    except Exception as exc:
        # No attempt to evade rate limits / access controls: error is surfaced for operator action.
        error=safe_error_summary(exc,'account sync')
        finish_run(account['id'],run_id,'failed',pages,seen,new,error)
        log.error('poll %s failed: %s',account['id'],error)


def main():
    log.info('worker started, single-threaded polling, base configured=%s',bool(DTK_BASE_URL and DTK_API_KEY))
    while True:
        try:
            account=claim_due_account()
            if account:
                run_account(account)
            else:
                target=claim_due_target()
                if target:
                    status=run_collection_target(target)
                    log.info('collection %s result=%s',target['id'],status)
                    if status != 'blocked_policy':
                        time.sleep(COLLECTION_MIN_DELAY_SECONDS)
                else:
                    time.sleep(15)
        except Exception as exc:
            log.error('worker loop failed: %s',safe_error_summary(exc,'worker loop'))
            time.sleep(30)


if __name__=='__main__':
    main()
