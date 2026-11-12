#!/usr/bin/env python3
"""Read-only inventory of raw-page evidence and backup storage."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import os
import re
import shutil
import zlib
from datetime import datetime, timedelta, timezone
from pathlib import Path


EVIDENCE_FILENAME = re.compile(r'^[0-9a-f]{64}\.html\.gz$')
BACKUP_SET_NAME = re.compile(r'^ningbo-re-ai-[0-9]{8}T[0-9]{6}Z-[0-9]+$')
MAX_EVIDENCE_HTML_BYTES = 1_000_000
MAX_EVIDENCE_GZIP_BYTES = 2_000_000


def _regular_files(path: Path):
    if path.is_symlink():
        return
    pending = [path]
    while pending:
        current = pending.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    if entry.is_symlink():
                        continue
                    item = Path(entry.path)
                    if entry.is_dir(follow_symlinks=False):
                        pending.append(item)
                    elif entry.is_file(follow_symlinks=False):
                        yield item
        except FileNotFoundError:
            continue


def summarize(path: Path) -> tuple[int, int, float | None, float | None]:
    files = list(_regular_files(path))
    mtimes = [item.stat().st_mtime for item in files]
    return len(files), sum(item.stat().st_size for item in files), \
        min(mtimes, default=None), max(mtimes, default=None)


def format_time(timestamp: float | None) -> str:
    if timestamp is None:
        return 'none'
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat(timespec='seconds')


def expired_backup_paths(path: Path, retention_days: int,
                         now: datetime | None = None) -> list[Path]:
    if retention_days < 1:
        raise ValueError('retention_days must be at least 1')
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=retention_days)
    files = list(_regular_files(path))
    backup_sets = {
        child for child in path.iterdir()
        if child.is_dir() and BACKUP_SET_NAME.fullmatch(child.name)
    } if path.is_dir() and not path.is_symlink() else set()
    candidates = []
    set_files = {backup_set: [item for item in files if backup_set in item.parents]
                 for backup_set in backup_sets}
    for backup_set, members in set_files.items():
        if (members and all(datetime.fromtimestamp(item.stat().st_mtime, timezone.utc) < cutoff
                            for item in members)
                and datetime.fromtimestamp(backup_set.stat().st_mtime, timezone.utc) < cutoff):
            candidates.append(backup_set)
    candidates.extend(
        item for item in files
        if not any(backup_set in item.parents for backup_set in backup_sets)
        and datetime.fromtimestamp(item.stat().st_mtime, timezone.utc) < cutoff
    )
    return sorted(candidates, key=lambda item: item.as_posix())


def expired_backup_summary(path: Path, retention_days: int,
                           now: datetime | None = None) -> tuple[int, int]:
    candidates = expired_backup_paths(path, retention_days, now)
    total_size = sum(item.stat().st_size if item.is_file() else
                     sum(member.stat().st_size for member in _regular_files(item))
                     for item in candidates)
    return len(candidates), total_size


def evidence_reference_summary(path: Path, referenced_paths: set[str]) -> tuple[list[Path], list[str]]:
    """Return unreferenced evidence files and DB references missing on disk."""
    files = {item.name: item for item in _regular_files(path)
             if EVIDENCE_FILENAME.fullmatch(item.name)}
    referenced_names = {Path(item).name for item in referenced_paths}
    unreferenced = [files[name] for name in sorted(files.keys() - referenced_names)]
    missing = sorted(name for name in referenced_names - files.keys()
                     if EVIDENCE_FILENAME.fullmatch(name))
    return unreferenced, missing


def invalid_evidence_files(path: Path) -> list[Path]:
    """Return content-addressed evidence whose gzip bytes do not match its name."""
    invalid = []
    for item in _regular_files(path):
        match = EVIDENCE_FILENAME.fullmatch(item.name)
        if not match:
            continue
        if item.stat().st_size > MAX_EVIDENCE_GZIP_BYTES:
            invalid.append(item)
            continue
        digest = hashlib.sha256()
        too_large = False
        size = 0
        try:
            with item.open('rb') as compressed:
                with gzip.GzipFile(fileobj=compressed, mode='rb') as evidence:
                    while True:
                        chunk = evidence.read(min(64 * 1024,
                                                  MAX_EVIDENCE_HTML_BYTES + 1 - size))
                        if not chunk:
                            break
                        size += len(chunk)
                        if size > MAX_EVIDENCE_HTML_BYTES:
                            too_large = True
                            break
                        digest.update(chunk)
        except (gzip.BadGzipFile, EOFError, zlib.error):
            invalid.append(item)
            continue
        if too_large or digest.hexdigest() != item.name[:-len('.html.gz')]:
            invalid.append(item)
    return sorted(invalid, key=lambda item: item.as_posix())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-pages', type=Path, default=Path('data/raw-pages'))
    parser.add_argument('--backups', type=Path, default=Path('backups'))
    parser.add_argument('--backup-retention-days', type=int, default=90)
    parser.add_argument('--check-evidence-references', action='store_true',
                        help='compare content-addressed evidence files with candidate and discovery records')
    parser.add_argument('--check-evidence-integrity', action='store_true',
                        help='verify gzip evidence size bounds and content hashes')
    args = parser.parse_args()
    if args.backup_retention_days < 1:
        parser.error('--backup-retention-days must be at least 1')

    for label, path in (('raw-pages', args.raw_pages), ('backups', args.backups)):
        if path.is_symlink():
            parser.error(f'{label} path must not be a symlink')
        if path.exists() and not path.is_dir():
            parser.error(f'{label} path must be a directory')
        try:
            count, size, oldest, newest = summarize(path)
        except OSError as exc:
            parser.error(f'{label} inventory could not be read: {exc.strerror or exc.__class__.__name__}')
        state = 'missing' if not path.is_dir() else f'{count} files, {size} bytes'
        print(f'{label}: {path} — {state}; oldest={format_time(oldest)}; newest={format_time(newest)}')

    if args.check_evidence_integrity:
        try:
            invalid = invalid_evidence_files(args.raw_pages)
        except OSError as exc:
            parser.error(f'raw-pages integrity check could not be completed: {exc.strerror or exc.__class__.__name__}')
        print(f'evidence_integrity: invalid={len(invalid)} files; no files changed')
        for item in invalid:
            print(f'evidence_integrity_failure: {item.relative_to(args.raw_pages)}')

    try:
        expired_files = expired_backup_paths(args.backups, args.backup_retention_days)
    except OSError as exc:
        parser.error(f'backup inventory could not be read: {exc.strerror or exc.__class__.__name__}')
    expired_count = len(expired_files)
    expired_size = sum(item.stat().st_size if item.is_file() else
                       sum(member.stat().st_size for member in _regular_files(item))
                       for item in expired_files)
    print(f'backup_retention: {args.backup_retention_days} days; '
          f'manual_review_candidates={expired_count} paths, {expired_size} bytes; no files deleted')
    for item in expired_files:
        print(f'backup_retention_candidate: {item.relative_to(args.backups)}')

    if args.check_evidence_references:
        from app.db import session

        with session() as conn:
            rows = conn.execute('''SELECT raw_storage_path AS storage_path
              FROM collection_candidates
              UNION SELECT first_page_storage_path FROM collection_listing_observations
              UNION SELECT last_page_storage_path FROM collection_listing_observations''').fetchall()
        try:
            unreferenced, missing = evidence_reference_summary(
                args.raw_pages, {row['storage_path'] for row in rows})
        except OSError as exc:
            parser.error(f'raw-pages inventory could not be read: {exc.strerror or exc.__class__.__name__}')
        unreferenced_size = sum(item.stat().st_size for item in unreferenced)
        print(f'evidence_references: unreferenced={len(unreferenced)} files, '
              f'{unreferenced_size} bytes; missing={len(missing)} files; no files deleted')
        for item in unreferenced:
            print(f'evidence_unreferenced_candidate: {item.name}')
        for name in missing:
            print(f'evidence_missing_reference: {name}')

    usage = shutil.disk_usage(Path.cwd())
    print(f'filesystem: total={usage.total} bytes; used={usage.used} bytes; free={usage.free} bytes')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
