# Current State

Snapshot: 2026-11-20. This is the short handoff for coding agents; read the assigned GitHub Issue before editing.
Repository: [jingshenga/ningbo-re-ai-v0.2](https://github.com/jingshenga/ningbo-re-ai-v0.2)
Main baseline after PR #35: `1454c98` (2026-11-20).

## Confirmed product and code

- Single-operator FastAPI/PostgreSQL 17 backend prototype, **not** a public multi-user product. Existing approved listing pipeline, source-scoped price history, saved-search matching, price-drop candidates, and notification outbox should be reused.
- PR #6: PR and main GitHub Actions CI, isolated PostgreSQL 17 integration, and agent collaboration instructions merged.
- PR #8 / Issue #1: parser `generic-labelled-v0.2.168` merged. Assessed values, rent and historic asking-price contexts do not become exact platform asking prices; periodic units must be attached to the number, preserving a valid asking price followed by unrelated monthly/annual expenses. This is **synthetic fixture verification**, not real page accuracy validation.
- PR #7: DTK worker status semantics and offline regression tests merged. The DTK 403/429 path currently records ordinary `failed` (redacted), **not a dedicated blocked status or backoff**; the documentation records that implementation gap.
- Combined PR #7 on latest parser main (2026-11-13): GitHub Actions **1963 quick tests passed**, **31 isolated PostgreSQL 17 integration tests passed**, no failing checks. These are CI results, not NAS production deployment checks.
- PR #35: human-triggered single-post social clue intake merged. The endpoint is idempotent by normalized platform/URL/content SHA-256, leaves duplicates unchanged, and stores clues separately from official listings and price history. GitHub Actions passed: quick **2123 passed / 4 skipped**, PostgreSQL 17 **35 passed**; Admin Browser UAT workflow passed. No NAS migration or live platform capture was performed.

## Data-source and deployment gates

- Beike and Anjuke: public-page parsing and manual/approved HTML sample ingestion are the current technical plan; licensed APIs are optional future adapters. Online automatic collection remains **OFF** pending written permission and site/robots review. P0-02 requires 20 legitimately obtained and manually labeled samples per source; still blocked.
- Douyin: DTK v5 adapter has offline contract coverage only. Actual DTK instance, three permitted accounts and 24-hour observation are not verified. Issue #3 remains open. WeChat Channels stays manual-import only.
- The social Tampermonkey collector is an explicit single-item operator tool; it is not background or bulk collection. Stored social posts remain unverified clues and are not promoted to listings or prices.
- NAS DXP4800: last documented read-only production audit found services healthy on local 8788, but schema migrations 006–014 and latest code were not deployed. Issue #4 is **isolated PG17 migration preflight only**; no production DB/schema/volume writes without fresh verified backup and explicit operator approval.
- No validated external notifications, automatic production video ASR/OCR, finished consumer interface, or reliable actual-sale-level valuation.

## Current tasks and ownership

| GitHub Issue | Owner | Next gate |
|---|---|---|
| #1 | ZCode | Closed; parser PR #8 merged. |
| #2 | Codex | Closed; CI PR #6 merged. |
| #3 | ZCode | Offline DTK PR #7 merged; live 3-account / 24-hour acceptance outstanding, and rate-limit blocked-status hardening is a separate unimplemented task. |
| #4 | Codex | PR #10 merged after isolated PG17 preflight; no production writes. Migration 012 sweep-ID preservation is tracked separately in Issue #13. |
| #5 | Codex | Internal management UI MVP in active development, using existing APIs and evidence-backed empty states. |
| #9 | Codex with ZCode local support | Mimosa Node scanner timeout / incomplete coverage and precise SQL/test-fixture false-positive triage; scanning must not be disabled. |

## Collaboration

- GitHub `main` is the only stable code source. Work on `codex/*` or `zcode/*` branches, CI + review before merge.
- Agents document work in their PRs. Codex integration lead consolidates short state and historical records *after* merge; avoid concurrent edits to global logs.
- Do not claim that passing synthetic tests means real-world listings, continuous collection, or NAS deployment are verified.
