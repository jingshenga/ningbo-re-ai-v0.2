# Agent Collaboration

## Ownership

| Area | Primary owner | Scope |
|---|---|---|
| Collection parsing and source acquisition | ZCode | `app/collectors/**`, parser and collection tests, source HTML samples, collection-layer policy changes, and video extraction/DTK adapter. |
| Main product integration | Codex | GitHub Actions, PostgreSQL and migrations, FastAPI business APIs, listing review and price history, saved searches, opportunity calculations, notifications, NAS deployment, and management UI. |
| Shared contracts | Both, coordinated by Codex | API/schema changes crossing ownership boundaries require a dedicated PR, a compatibility note, and review by both owners before merge. |

## Branch and PR rules

- Work from the latest `main` in a branch named `codex/<issue>-<short-topic>` or `zcode/<issue>-<short-topic>`; never commit directly to `main`.
- Use one focused PR per Issue. Include the Issue, goal, changed paths, test results, compatibility notes, and unverified items.
- Do not edit files owned by the other agent unless the Issue requires a shared contract change and that change is called out in the PR.
- Do not overwrite in-progress work. Rebase or refresh against `main` and resolve only the files owned by the current task.
- Every PR description must include a `本轮开发记录` with goal/status, changed files and decisions, test command with passed/failed/skipped counts and unverified items, migration/configuration risks, and the next 1–3 priorities with acceptance criteria.
- Contributors do not edit the global state files `docs/CURRENT_STATE.md`, `docs/PROJECT_STATUS.md`, `docs/ROADMAP.md`, `docs/GOAL_STATE.json`, or `CHANGELOG.md` during parallel feature work, unless the assigned Issue explicitly includes one of them.
- After merge, Codex as integration lead reconciles those global state files once, using the merged PR development record; this rule applies equally to ZCode and Codex.
- Do not merge changes with unresolved data-loss, security, permission, or migration-safety risks. Production database changes require an explicit user-authorized Issue and a fresh verified backup.

## Current sequence

1. Issue #2: PR CI, isolated PostgreSQL 17 tests, concise state and collaboration rules.
2. Issue #4: inspect migrations 006–014 and rehearse only in an isolated database; no production database mutation.
3. Issue #5: implement the visual management backend MVP after the migration preflight.
