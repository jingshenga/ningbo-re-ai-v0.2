from contextlib import nullcontext

from app.log_safety import safe_error_summary
from app import worker


def test_upstream_exception_summary_omits_sensitive_message():
    secret = 'token=private-value&phone=13800000000'
    summary = safe_error_summary(RuntimeError(secret), 'account sync')
    assert 'RuntimeError' in summary
    assert 'account sync failed' in summary
    assert secret not in summary


def test_malformed_upstream_item_logs_metadata_without_external_keys(monkeypatch, caplog):
    payload = {'api_key=private-value': 'unused', 'phone=13800000000': 'unused'}
    monkeypatch.setattr(worker, 'normalize_post', lambda _item: None)
    monkeypatch.setattr(worker, 'session', nullcontext)

    worker.store_page({}, [payload], first_run=False, cutoff=None)

    assert 'object_type=dict field_count=2' in caplog.text
    assert 'api_key=private-value' not in caplog.text
    assert 'phone=13800000000' not in caplog.text
