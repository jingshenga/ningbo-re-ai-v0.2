# NAS migration preflight (006–014)

## Scope and safety

This report covers static review and an isolated PostgreSQL 17 rehearsal of the current `main` migrations. It does not inspect the live production database or claim that any migration is deployed. There was no current production schema snapshot or V0.1 backup available to this task.

No production database, production container, production volume, Compose file, or business row was used or changed. The rehearsal used a temporary `rehouse_test` database with synthetic records only.

## Rehearsal evidence

- Source: GitHub `main` at `054786c8527778855c35dd373d4272b6ba8c2efd`.
- Runtime: PostgreSQL 17 (`postgres:17-alpine`).
- Isolation: dedicated Docker internal network; database directory on 512 MiB tmpfs; no published port and no mounts or persistent volumes.
- Synthetic starting point: migrations 001–014 applied in order, with a legacy listing, property, platform price history, saved search and notification row inserted after 001.
- Result: all 14 migrations completed; 006–014 were then applied a second time. Assertions confirmed legacy price, status, permission note, price history, search and notification values remained intact.
- Rollback: a deliberate SQL error after transactional DDL rolled the test transaction back; the created table was absent afterward.
- Cleanup: the exact temporary PostgreSQL container and internal network were removed and verified absent.
- No production backup was restored. This rehearsal does not replace a real V0.1 backup restore or a production schema comparison.

The existing `tests/test_db_integration.py::test_v01_schema_migration_preserves_existing_data` also applies the 001–014 path twice against synthetic V0.1 records. A focused static test now checks that every migration from 006 through 014 has one explicit `BEGIN` and `COMMIT`.

## Migration review

| Migration | Change | Review note |
|---|---|---|
| 006 | Creates persistent discovery cursor state | Additive table with target cascade. |
| 007 | Adds listing observation ledger and index | New table and index; source IDs are constrained. |
| 008 | Adds sweep progress fields | Additive columns with nonnegative checks and JSON-array checks. |
| 009 | Adds review conclusion history and permits `reviewed` | Replaces the review-status check constraint; existing out-of-domain values would make this fail. |
| 010 | Adds parse counters, attempt ledger, trigger and backfill | Backfills from existing source rows while installing trigger-based maintenance. |
| 011 | Blocks update/delete/truncate of parse attempts | Trigger changes write behavior for the append-only ledger. |
| 012 | Moves `seen_listing_ids` into a relation and clears the JSON arrays | Review gate: it copies `seen_listing_ids`, then clears both `seen_listing_ids` and `sweep_seen_listing_ids`. The current code derives sweep IDs from listing observations, but an old sweep-only ID without a matching observation would not be copied by this migration. No live snapshot was available to establish whether such rows exist. Treat this as an unresolved data-preservation risk and verify/fix it in a separate SQL PR before any production migration. |
| 013 | Adds account-history backfill cursor and cutoff | Additive nullable columns. |
| 014 | Adds durable detail queue | New queue table and index; queue rows cascade with their observation row. |

All nine files declare an explicit transaction. The rehearsal verifies PostgreSQL accepts the statements and that repeat execution succeeds; it does not prove that production data satisfies every check constraint or trigger assumption.

## Read-only schema checker

`scripts/check_schema.py` compares the migration 006–014 signature tables, columns, parse-metric functions, enabled append-only/metrics triggers, and the expected migration check constraints in the current schema. It starts a read-only transaction and only queries PostgreSQL catalogs plus a read-only count; it never executes migrations or data-changing SQL. Before migration 012, when migrations 006–008 are present, it also counts IDs in `sweep_seen_listing_ids` without a matching `collection_listing_observations.last_seen_sweep`. A nonzero count is a stop condition because 012 clears that JSON array without copying it. By default the script refuses a database name other than `rehouse_test`. Use the explicit non-test option only after obtaining approval for read access to that environment.

Example:

```sh
TEST_DATABASE_URL=postgresql://rehouse:…@127.0.0.1:5432/rehouse_test \
  python scripts/check_schema.py
```

A missing object is reported with exit status 1. Connection failures redact connection details.

## Production readiness and recovery sequence

Production migration is not authorized by this issue. Before a separately approved change:

1. Obtain a fresh full backup of the actual database and record its checksum, time, size and source commit/schema.
2. Restore that backup into an isolated PostgreSQL 17 instance and verify `pg_restore --list`, row counts and selected business-field checks.
3. Compare the restored schema with migration signatures and resolve the migration 012 sweep-ID risk before applying any migration.
4. Apply each migration in order with stop-on-error behavior. Each file has its own transaction; on failure stop immediately and restore the verified backup into a fresh isolated instance for recovery testing. Do not improvise destructive reverse SQL.
5. Recheck schema objects, critical constraints, counts and selected business fields before a separately authorized production rollout.

Until a real backup and schema snapshot are available, production migration status remains unverified.


## Main synchronization and review follow-up

The preflight branch was synchronized with main commit `054786c8527778855c35dd373d4272b6ba8c2efd`. The read-only checker also verifies the migration 011 function, enabled triggers, and behavior-defining constraints. The review thread for that gap is resolved; synchronized GitHub Actions passed 1962 quick tests and 31 PostgreSQL 17 integration tests. Migration 012 sweep-only ID preservation is isolated in Issue #13 and remains a production-upgrade gate.
