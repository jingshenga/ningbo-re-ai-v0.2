# Current State

Snapshot: 2026-11-13. This is the short operational handoff; see linked project records for detail.
GitHub: [jingshenga/ningbo-re-ai-v0.2](https://github.com/jingshenga/ningbo-re-ai-v0.2)
Main baseline after Issue #2: `86fbbd462fa8897e151f437b0fcd17fed55a9562` (2026-11-13). PR #6 was squash-merged; Issue #2 is closed.

## Product and verification

- V0.2 is a single-operator backend prototype for Ningbo listings, video context, price history, saved searches, opportunities, and reviewable notifications.
- Candidate review, approved source listings, source-scoped price history, saved-search matching, price-drop detection, and notification events already exist. Do not rebuild them as part of infrastructure work.
- Latest recorded isolated PostgreSQL 17.11 run: `tests/test_db_integration.py` **31 passed** (2026-11-12, NAS temporary internal network, 512 MiB tmpfs, no production volume/port; temporary resources cleaned). This is prior verification, not the new GitHub Actions result.
- GitHub Actions run #43355428469 passed on main: fast suite 1849 passed, 0 skipped, 27 subtests; isolated PostgreSQL 17 suite 31 passed, 0 skipped. Both jobs reported one existing warning.
- Local PostgreSQL integration tests skip unless `TEST_DATABASE_URL` names the dedicated `rehouse_test` database.
- Production migrations 006–014 are not confirmed present. Issue #4 has an isolated synthetic PG17 rehearsal; no production schema was read or changed. Migration 012's handling of sweep-only IDs remains a separate pre-production data-preservation gate. Do not run migrations or deploy without a fresh backup and explicit authorization.
- No production-grade frontend, multi-user authentication, automatic video ASR/OCR, or external notification delivery is verified.

## Current P0 status

| Goal | Status | Remaining gate |
|---|---|---|
| P0-01 V0.1 migration | blocked | A real V0.1 database backup is unavailable. |
| P0-02 licensed listing samples | blocked | Written source permission and 20 labeled HTML pages per source are missing; online collection stays off. |
| P0-03 parser field accuracy | in progress | Requires P0-02 samples; synthetic fixtures do not prove live accuracy. |
| P0-04 source policy review | in progress | Current policy evidence and project permission are incomplete. |
| P0-05 PostgreSQL integration | verified | PR #6 CI passed on PR head and main: 1849 fast tests and 31 PG17 integration tests. |
| P0-07 production schema/health | in progress | Issue #4 synthetic PG17 preflight passed; live schema, real backup restore, and migration 012 sweep-ID risk remain open. |
| P0-09 listing discovery | in progress | Authorized live-source end-to-end validation is outstanding. |

## Active work and next

- Active: GitHub Issue #4, migration inspection and isolated preflight (Codex). ZCode Issue #1/#3 branches are awaiting the declared Bundle file; no ZCode code is imported or merged.
- Next order: resolve Issue #4's migration 012 review gate; then Issue #5 visual management backend MVP.
- Never run destructive tests against production. Use an isolated `rehouse_test` database and PostgreSQL 17.
- Data ingestion still requires reviewable evidence and human approval; video oral prices are not platform asking prices.

For owners and branch/PR rules, see [AGENT_COLLABORATION.md](AGENT_COLLABORATION.md). For detailed history, see [PROJECT_STATUS.md](PROJECT_STATUS.md), [ROADMAP.md](ROADMAP.md), and [GOAL_STATE.json](GOAL_STATE.json).
