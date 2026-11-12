-- Persist complete-pagination sweep progress for safe stale-listing review.
BEGIN;

ALTER TABLE collection_discovery_states
  ADD COLUMN IF NOT EXISTS sweep_number BIGINT NOT NULL DEFAULT 0
    CHECK (sweep_number >= 0),
  ADD COLUMN IF NOT EXISTS sweep_active BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS sweep_seen_listing_ids JSONB NOT NULL DEFAULT '[]'::jsonb
    CHECK (jsonb_typeof(sweep_seen_listing_ids) = 'array'),
  ADD COLUMN IF NOT EXISTS completed_sweeps BIGINT NOT NULL DEFAULT 0
    CHECK (completed_sweeps >= 0);

COMMIT;
