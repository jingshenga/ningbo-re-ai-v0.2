# Current State

Snapshot: 2026-11-13. This is the short operational handoff; see linked project records for detail.
GitHub: [jingshenga/ningbo-re-ai-v0.2](https://github.com/jingshenga/ningbo-re-ai-v0.2)
Main baseline for Issue #2: `d372a94aed2d3649dfe508ee266b851066031262` (2026-11-12). Refresh this line after the PR merges.

## Product and verification

- V0.2 is a single-operator backend prototype for Ningbo listings, video context, price history, saved searches, opportunities, and reviewable notifications.
- Candidate review, approved source listings, source-scoped price history, saved-search matching, price-drop detection, and notification events already exist. Do not rebuild them as part of infrastructure work.
- Latest recorded isolated PostgreSQL 17.11 run: `tests/test_db_integration.py` **31 passed** (2026-11-12, NAS temporary internal network, 512 MiB tmpfs, no production volume/port; temporary resources cleaned). This is prior verification, not the new GitHub Actions result.
- Local PostgreSQL integration tests skip unless `TEST_DATABASE_URL` names the dedicated `rehouse_test` database. Issue #2 adds PR automation for fast tests and PostgreSQL 17 integration.
- Production migrations 006–014 are not confirmed present; do not run migrations or deploy without a fresh backup and explicit task authorization.
- No production-grade frontend, multi-user authentication, automatic video ASR/OCR, or external notification delivery is verified.

## Current P0 status

| Goal | Status | Remaining gate |
|---|---|---|
| P0-01 V0.1 migration | blocked | A real V0.1 database backup is unavailable. |
| P0-02 licensed listing samples | blocked | Written source permission and 20 labeled HTML pages per source are missing; online collection stays off. |
| P0-03 parser field accuracy | in progress | Requires P0-02 samples; synthetic fixtures do not prove live accuracy. |
| P0-04 source policy review | in progress | Current policy evidence and project permission are incomplete. |
| P0-05 PostgreSQL integration | verified on NAS | 31 integration tests passed on isolated PG17; add repeatable CI. |
| P0-07 production schema/health | in progress | Production schema gap and current code mismatch remain unverified for deployment. |
| P0-09 listing discovery | in progress | Authorized live-source end-to-end validation is outstanding. |

## Active work and next

- Active: GitHub Issue #2, PR automation and this concise handoff (Codex).
- Next order: Issue #4 migration inspection and isolated preflight; then Issue #5 visual management backend MVP.
- Never run destructive tests against production. Use an isolated `rehouse_test` database and PostgreSQL 17.
- Data ingestion still requires reviewable evidence and human approval; video oral prices are not platform asking prices.

For owners and branch/PR rules, see [AGENT_COLLABORATION.md](AGENT_COLLABORATION.md). For detailed history, see [PROJECT_STATUS.md](PROJECT_STATUS.md), [ROADMAP.md](ROADMAP.md), and [GOAL_STATE.json](GOAL_STATE.json).
