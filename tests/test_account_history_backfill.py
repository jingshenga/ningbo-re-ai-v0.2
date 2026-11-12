from contextlib import contextmanager

from app import services
from app.models import AccountPatch


class Result:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


class Connection:
    def __init__(self, account):
        self.account = account
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))
        if query.startswith('SELECT * FROM monitored_accounts'):
            return Result(self.account)
        return Result(self.account)


def session_for(connection):
    @contextmanager
    def context():
        yield connection
    return context


def test_changing_history_mode_resets_backfill_progress(monkeypatch):
    account = {
        'id': 'account-1',
        'collector_mode': 'dtk',
        'history_mode': '30d',
        'enabled': True,
        'initial_synced': False,
    }
    conn = Connection(account)
    monkeypatch.setattr(services, 'session', session_for(conn))

    services.update_account('account-1', AccountPatch(history_mode='90d'))

    sql = conn.calls[-1][0]
    assert 'initial_synced=FALSE' in sql
    assert 'history_backfill_cursor=NULL' in sql
    assert 'history_backfill_cutoff=NULL' in sql


def test_explicit_backfill_request_resets_old_progress(monkeypatch):
    account = {
        'id': 'account-1',
        'collector_mode': 'dtk',
        'history_mode': '30d',
        'enabled': True,
        'initial_synced': True,
    }
    conn = Connection(account)
    monkeypatch.setattr(services, 'session', session_for(conn))

    services.queue_account_poll('account-1', '90d')

    sql = conn.calls[-1][0]
    assert 'initial_synced=FALSE' in sql
    assert 'history_backfill_cursor=NULL' in sql
    assert 'history_backfill_cutoff=NULL' in sql
