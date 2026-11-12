-- Persist the historical pagination position and a stable cutoff across worker runs.
BEGIN;

ALTER TABLE monitored_accounts
  ADD COLUMN IF NOT EXISTS history_backfill_cursor TEXT,
  ADD COLUMN IF NOT EXISTS history_backfill_cutoff TIMESTAMPTZ;

COMMIT;
