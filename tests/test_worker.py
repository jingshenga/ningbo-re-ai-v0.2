from app import worker
from app.dtk import Page


def test_missing_cursor_with_more_pages_is_reported_as_partial(monkeypatch):
    finished = []

    class Client:
        def __init__(self, base_url, api_key):
            pass

        def author_posts(self, account_ref, cursor):
            return Page(items=[], next_cursor=None, has_more=True)

        def close(self):
            pass

    monkeypatch.setattr(worker, 'DTK_BASE_URL', 'http://dtk.test')
    monkeypatch.setattr(worker, 'DTK_API_KEY', 'test-key')
    monkeypatch.setattr(worker, 'start_run', lambda account_id: 'run-1')
    monkeypatch.setattr(worker, 'finish_run', lambda *args, **kwargs: finished.append((args, kwargs)))
    monkeypatch.setattr(worker, 'store_page', lambda *args: (0, 0, 0, 0, 0))
    monkeypatch.setattr(worker, 'DtkClient', Client)

    worker.run_account({
        'id': 'account-1',
        'account_ref': 'author-1',
        'initial_synced': True,
        'history_mode': 'none',
    })

    args, kwargs = finished[0]
    assert args[2] == 'partial'
    assert 'more posts without a pagination cursor' in args[-1]


def test_history_backfill_resumes_after_page_limit_with_fixed_cutoff(monkeypatch):
    account = {
        'id': 'account-1',
        'account_ref': 'author-1',
        'initial_synced': False,
        'history_mode': '30d',
        'history_backfill_cursor': None,
        'history_backfill_cutoff': None,
    }
    finished = []
    saved = []
    cursors = []
    cutoff_value = worker.now_utc() - worker.timedelta(days=30)

    class Client:
        def __init__(self, base_url, api_key):
            pass

        def author_posts(self, account_ref, cursor):
            cursors.append(cursor)
            index = int(cursor[1:]) if cursor else 0
            return Page(items=[], next_cursor=f'c{index + 1}', has_more=True)

        def close(self):
            pass

    def save_progress(account_id, cursor, cutoff):
        saved.append((cursor, cutoff))
        account['history_backfill_cursor'] = cursor
        account['history_backfill_cutoff'] = cutoff

    monkeypatch.setattr(worker, 'DTK_BASE_URL', 'http://dtk.test')
    monkeypatch.setattr(worker, 'DTK_API_KEY', 'test-key')
    monkeypatch.setattr(worker, 'start_run', lambda account_id: 'run-1')
    monkeypatch.setattr(worker, 'finish_run',
                        lambda *args, **kwargs: finished.append((args, kwargs)))
    monkeypatch.setattr(worker, 'store_page', lambda *args: (0, 0, 0, 0, 0))
    monkeypatch.setattr(worker, 'persist_history_backfill', save_progress)
    monkeypatch.setattr(worker, 'DtkClient', Client)
    monkeypatch.setattr(worker, 'now_utc', lambda: cutoff_value + worker.timedelta(days=30))
    monkeypatch.setattr(worker.time, 'sleep', lambda seconds: None)

    worker.run_account(account)

    assert cursors == [None, 'c1', 'c2', 'c3', 'c4']
    assert account['history_backfill_cursor'] == 'c5'
    assert account['history_backfill_cutoff'] == cutoff_value
    assert finished[-1][0][2] == 'partial'
    assert finished[-1][1]['initial_sync_complete'] is False

    cursors.clear()
    class FinalPageClient(Client):
        def author_posts(self, account_ref, cursor):
            cursors.append(cursor)
            return Page(items=[], next_cursor=None, has_more=False)
    monkeypatch.setattr(worker, 'DtkClient', FinalPageClient)

    worker.run_account(account)

    assert cursors == ['c5']
    assert account['history_backfill_cursor'] is None
    assert account['history_backfill_cutoff'] is None
    assert finished[-1][0][2] == 'success'
    assert finished[-1][1]['initial_sync_complete'] is True
    assert saved[0] == (None, cutoff_value)
    assert saved[1] == ('c1', cutoff_value)
    assert saved[-1] == (None, None)


def test_incremental_sync_does_not_write_history_backfill_cursor(monkeypatch):
    finished = []
    saved = []

    class Client:
        def __init__(self, base_url, api_key):
            pass

        def author_posts(self, account_ref, cursor):
            index = int(cursor[1:]) if cursor else 0
            return Page(items=[], next_cursor=f'c{index + 1}', has_more=True)

        def close(self):
            pass

    monkeypatch.setattr(worker, 'DTK_BASE_URL', 'http://dtk.test')
    monkeypatch.setattr(worker, 'DTK_API_KEY', 'test-key')
    monkeypatch.setattr(worker, 'start_run', lambda account_id: 'run-1')
    monkeypatch.setattr(worker, 'finish_run',
                        lambda *args, **kwargs: finished.append((args, kwargs)))
    monkeypatch.setattr(worker, 'store_page', lambda *args: (0, 0, 0, 0, 0))
    monkeypatch.setattr(worker, 'persist_history_backfill',
                        lambda *args: saved.append(args))
    monkeypatch.setattr(worker, 'DtkClient', Client)
    monkeypatch.setattr(worker.time, 'sleep', lambda seconds: None)

    worker.run_account({
        'id': 'account-1',
        'account_ref': 'author-1',
        'initial_synced': True,
        'history_mode': '30d',
        'history_backfill_cursor': None,
        'history_backfill_cutoff': None,
    })

    assert saved == []
    assert finished[-1][0][2] == 'partial'
    assert 'Page limit reached' in finished[-1][0][-1]


def test_history_backfill_resumes_after_request_failure(monkeypatch):
    account = {
        'id': 'account-1',
        'account_ref': 'author-1',
        'initial_synced': False,
        'history_mode': '90d',
        'history_backfill_cursor': None,
        'history_backfill_cutoff': None,
    }
    cutoff_value = worker.now_utc() - worker.timedelta(days=90)
    cursors = []
    finished = []
    fail_second_page = True

    class Client:
        def __init__(self, base_url, api_key):
            pass

        def author_posts(self, account_ref, cursor):
            nonlocal fail_second_page
            cursors.append(cursor)
            if cursor == 'c1' and fail_second_page:
                fail_second_page = False
                raise worker.DtkError('temporary failure')
            if cursor is None:
                return Page(items=[], next_cursor='c1', has_more=True)
            return Page(items=[], next_cursor=None, has_more=False)

        def close(self):
            pass

    def save_progress(account_id, cursor, cutoff):
        account['history_backfill_cursor'] = cursor
        account['history_backfill_cutoff'] = cutoff

    monkeypatch.setattr(worker, 'DTK_BASE_URL', 'http://dtk.test')
    monkeypatch.setattr(worker, 'DTK_API_KEY', 'test-key')
    monkeypatch.setattr(worker, 'start_run', lambda account_id: 'run-1')
    monkeypatch.setattr(worker, 'finish_run',
                        lambda *args, **kwargs: finished.append((args, kwargs)))
    monkeypatch.setattr(worker, 'store_page', lambda *args: (0, 0, 0, 0, 0))
    monkeypatch.setattr(worker, 'persist_history_backfill', save_progress)
    monkeypatch.setattr(worker, 'DtkClient', Client)
    monkeypatch.setattr(worker.time, 'sleep', lambda seconds: None)
    monkeypatch.setattr(worker, 'now_utc', lambda: cutoff_value + worker.timedelta(days=90))

    worker.run_account(account)
    assert cursors == [None, 'c1']
    assert account['history_backfill_cursor'] == 'c1'
    assert account['history_backfill_cutoff'] == cutoff_value
    assert finished[-1][0][2] == 'failed'
    assert finished[-1][1].get('initial_sync_complete', False) is False

    cursors.clear()
    worker.run_account(account)
    assert cursors == ['c1']
    assert account['history_backfill_cursor'] is None
    assert account['history_backfill_cutoff'] is None
    assert finished[-1][0][2] == 'success'
    assert finished[-1][1]['initial_sync_complete'] is True
