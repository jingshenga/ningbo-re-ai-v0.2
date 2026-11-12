from datetime import datetime, timedelta, timezone
import gzip
import hashlib
import os

import pytest

from scripts.storage_report import (evidence_reference_summary, expired_backup_paths,
                                    expired_backup_summary, format_time,
                                    invalid_evidence_files, summarize)


def test_summarize_reports_files_and_ignores_directories(tmp_path):
    (tmp_path / 'nested').mkdir()
    (tmp_path / 'a.gz').write_bytes(b'abc')
    (tmp_path / 'nested' / 'b.gz').write_bytes(b'defg')

    count, size, oldest, newest = summarize(tmp_path)

    assert count == 2
    assert size == 7
    assert oldest is not None
    assert newest is not None
    assert oldest <= newest


def test_summarize_handles_deep_directory_trees_without_python_recursion(tmp_path):
    import sys

    root = tmp_path / 'deep'
    root.mkdir()
    current = root
    for _ in range(120):
        current = current / 'd'
        current.mkdir()
    (current / 'evidence.gz').write_bytes(b'evidence')

    previous_limit = sys.getrecursionlimit()
    try:
        sys.setrecursionlimit(150)
        assert summarize(root)[:2] == (1, 8)
    finally:
        sys.setrecursionlimit(previous_limit)


def test_summarize_missing_directory_is_empty(tmp_path):
    assert summarize(tmp_path / 'missing') == (0, 0, None, None)


def test_summarize_rejects_unreadable_directory(tmp_path, monkeypatch):
    denied = tmp_path / 'restricted'
    denied.mkdir()
    scandir = os.scandir

    def restricted_scandir(path):
        if os.fspath(path) == os.fspath(denied):
            raise PermissionError('permission denied')
        return scandir(path)

    monkeypatch.setattr(os, 'scandir', restricted_scandir)

    with pytest.raises(PermissionError, match='permission denied'):
        summarize(denied)


def test_storage_reports_ignore_symlinked_files_and_directories(tmp_path):
    root = tmp_path / 'backups'
    outside = tmp_path / 'outside'
    root.mkdir()
    outside.mkdir()
    (root / 'real.dump').write_bytes(b'backup')
    (outside / 'linked.dump').write_bytes(b'outside')
    (root / 'linked-file.dump').symlink_to(outside / 'linked.dump')
    (root / 'linked-dir').symlink_to(outside, target_is_directory=True)

    count, size, _, _ = summarize(root)

    assert (count, size) == (1, 6)


def test_storage_reports_do_not_follow_symlinked_root(tmp_path):
    target = tmp_path / 'actual-backups'
    target.mkdir()
    (target / 'backup.dump').write_bytes(b'backup')
    linked_root = tmp_path / 'backups-link'
    linked_root.symlink_to(target, target_is_directory=True)

    assert summarize(linked_root) == (0, 0, None, None)
    assert expired_backup_summary(linked_root, 90) == (0, 0)


@pytest.mark.parametrize('option', ['--raw-pages', '--backups'])
def test_storage_report_refuses_symlinked_inventory_root(tmp_path, monkeypatch, capsys, option):
    import sys

    from scripts import storage_report

    outside = tmp_path / 'outside'
    outside.mkdir()
    (outside / 'evidence.html.gz').write_bytes(b'fixture')
    linked_root = tmp_path / 'inventory-link'
    linked_root.symlink_to(outside, target_is_directory=True)
    args = ['storage_report', option, str(linked_root)]
    monkeypatch.setattr(sys, 'argv', args)

    with pytest.raises(SystemExit) as raised:
        storage_report.main()

    assert raised.value.code == 2
    assert 'must not be a symlink' in capsys.readouterr().err


@pytest.mark.parametrize('option', ['--raw-pages', '--backups'])
def test_storage_report_rejects_file_as_inventory_root(tmp_path, monkeypatch, capsys, option):
    import sys

    from scripts import storage_report

    root = tmp_path / 'inventory-file'
    root.write_text('not a directory')
    monkeypatch.setattr(sys, 'argv', ['storage_report', option, str(root)])

    with pytest.raises(SystemExit) as raised:
        storage_report.main()

    captured = capsys.readouterr()
    assert raised.value.code == 2
    assert 'must be a directory' in captured.err
    assert 'Traceback' not in captured.err


def test_storage_report_reports_inventory_read_error_without_traceback(
        tmp_path, monkeypatch, capsys):
    import sys

    from scripts import storage_report

    restricted = tmp_path / 'restricted'
    restricted.mkdir()
    scandir = os.scandir

    def denied(path):
        if os.fspath(path) == os.fspath(restricted):
            raise PermissionError('permission denied')
        return scandir(path)

    monkeypatch.setattr(os, 'scandir', denied)
    monkeypatch.setattr(sys, 'argv', ['storage_report', '--raw-pages', str(restricted)])

    with pytest.raises(SystemExit) as raised:
        storage_report.main()

    captured = capsys.readouterr()
    assert raised.value.code == 2
    assert 'raw-pages inventory could not be read' in captured.err
    assert 'Traceback' not in captured.err


def test_format_time_uses_utc_and_none_marker():
    assert format_time(0) == '1970-01-01T00:00:00+00:00'
    assert format_time(None) == 'none'


def test_expired_backup_summary_reports_only_files_older_than_retention(tmp_path):
    now = datetime(2026, 11, 10, tzinfo=timezone.utc)
    old = tmp_path / 'source-snapshots' / 'old.tar.gz'
    boundary = tmp_path / 'database' / 'boundary.dump'
    recent = tmp_path / 'database' / 'recent.dump'
    old.parent.mkdir()
    recent.parent.mkdir()
    boundary.parent.mkdir(exist_ok=True)
    old.write_bytes(b'old')
    boundary.write_bytes(b'edge')
    recent.write_bytes(b'recent')
    old_time = (now - timedelta(days=91)).timestamp()
    boundary_time = (now - timedelta(days=90)).timestamp()
    recent_time = (now - timedelta(days=89)).timestamp()
    os.utime(old, (old_time, old_time))
    os.utime(boundary, (boundary_time, boundary_time))
    os.utime(recent, (recent_time, recent_time))

    assert expired_backup_summary(tmp_path, 90, now) == (1, 3)
    assert expired_backup_paths(tmp_path, 90, now) == [old]


def test_storage_report_lists_expired_backup_paths_without_deleting(tmp_path, monkeypatch, capsys):
    import sys

    from scripts import storage_report

    old_file = tmp_path / 'backup-set' / 'database.dump'
    old_file.parent.mkdir()
    old_file.write_bytes(b'old')
    expired = (datetime.now(timezone.utc) - timedelta(days=91)).timestamp()
    os.utime(old_file, (expired, expired))
    monkeypatch.setattr(sys, 'argv', ['storage_report', '--backups', str(tmp_path)])

    assert storage_report.main() == 0
    assert f'backup_retention_candidate: {old_file.relative_to(tmp_path)}' in capsys.readouterr().out
    assert old_file.read_bytes() == b'old'


def test_expired_backup_report_keeps_backup_set_together(tmp_path, monkeypatch, capsys):
    now = datetime(2026, 11, 10, tzinfo=timezone.utc)
    complete = tmp_path / 'ningbo-re-ai-20260801T000000Z-1234'
    partial = tmp_path / 'ningbo-re-ai-20260801T000000Z-5678'
    complete.mkdir()
    partial.mkdir()
    complete_dump = complete / 'database.dump'
    complete_evidence = complete / 'raw-pages.tar.gz'
    partial_dump = partial / 'database.dump'
    partial_evidence = partial / 'raw-pages.tar.gz'
    for item in (complete_dump, complete_evidence, partial_dump, partial_evidence):
        item.write_bytes(b'backup')
    old_time = (now - timedelta(days=91)).timestamp()
    recent_time = (now - timedelta(days=10)).timestamp()
    for item in (complete_dump, complete_evidence, partial_dump, partial_evidence):
        os.utime(item, (old_time, old_time))
    os.utime(complete, (old_time, old_time))
    os.utime(partial, (old_time, old_time))
    os.utime(partial_evidence, (recent_time, recent_time))

    assert expired_backup_paths(tmp_path, 90, now) == [complete]
    assert expired_backup_summary(tmp_path, 90, now) == (1, len(b'backup') * 2)

    import sys

    from scripts import storage_report

    monkeypatch.setattr(sys, 'argv', ['storage_report', '--backups', str(tmp_path)])
    assert storage_report.main() == 0
    output = capsys.readouterr().out
    assert 'manual_review_candidates=1 paths, 12 bytes' in output
    assert f'backup_retention_candidate: {complete.name}' in output
    assert complete_dump.exists() and complete_evidence.exists()


def test_expired_backup_summary_rejects_invalid_retention(tmp_path):
    with pytest.raises(ValueError, match='at least 1'):
        expired_backup_summary(tmp_path, 0)


def test_evidence_reference_summary_reports_orphans_and_missing_files(tmp_path):
    referenced = 'a' * 64
    orphan = 'b' * 64
    missing_hash = 'c' * 64
    (tmp_path / f'{referenced}.html.gz').write_bytes(b'kept')
    (tmp_path / f'{orphan}.html.gz').write_bytes(b'orphan')
    (tmp_path / 'not-content-addressed.html.gz').write_bytes(b'ignore')

    unreferenced, missing = evidence_reference_summary(
        tmp_path, {f'/data/raw-pages/{referenced}.html.gz',
                   f'/data/raw-pages/{missing_hash}.html.gz'})

    assert [item.name for item in unreferenced] == [f'{orphan}.html.gz']
    assert missing == [f'{missing_hash}.html.gz']
    assert (tmp_path / f'{orphan}.html.gz').exists()


def test_evidence_reference_summary_ignores_symlinks_and_non_evidence_files(tmp_path):
    outside = tmp_path / 'outside'
    outside.write_bytes(b'not evidence')
    (tmp_path / f"{'d' * 64}.html.gz").symlink_to(outside)
    (tmp_path / 'notes.txt').write_text('not evidence')

    unreferenced, missing = evidence_reference_summary(tmp_path, set())

    assert unreferenced == []
    assert missing == []


def test_evidence_integrity_rejects_gzip_larger_than_html_limit(tmp_path):
    content = b'x' * 1_000_001
    digest = hashlib.sha256(content).hexdigest()
    path = tmp_path / f'{digest}.html.gz'
    path.write_bytes(gzip.compress(content))

    assert invalid_evidence_files(tmp_path) == [path]


def test_evidence_integrity_accepts_html_at_limit(tmp_path):
    content = b'x' * 1_000_000
    digest = hashlib.sha256(content).hexdigest()
    path = tmp_path / f'{digest}.html.gz'
    path.write_bytes(gzip.compress(content))

    assert invalid_evidence_files(tmp_path) == []


def test_evidence_integrity_rejects_compressed_file_over_limit_without_decompressing(
        tmp_path, monkeypatch):
    content = b'x' * 2_000_001
    digest = hashlib.sha256(content).hexdigest()
    path = tmp_path / f'{digest}.html.gz'
    path.write_bytes(content)

    def unexpected_decompression(*args, **kwargs):
        raise AssertionError('oversized compressed evidence must be rejected before gzip open')

    monkeypatch.setattr(gzip, 'GzipFile', unexpected_decompression)

    assert invalid_evidence_files(tmp_path) == [path]


def test_reference_audit_does_not_report_zero_when_database_is_unavailable(tmp_path, monkeypatch):
    import sys

    from app import db
    from scripts import storage_report

    def unavailable_session():
        raise ConnectionError('database unavailable')

    monkeypatch.setattr(db, 'session', unavailable_session)
    monkeypatch.setattr(sys, 'argv', [
        'storage_report', '--raw-pages', str(tmp_path / 'raw-pages'),
        '--backups', str(tmp_path / 'backups'), '--check-evidence-references',
    ])

    with pytest.raises(ConnectionError, match='database unavailable'):
        storage_report.main()
