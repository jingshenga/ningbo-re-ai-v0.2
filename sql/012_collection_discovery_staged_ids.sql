-- Keep the per-target detail dedupe ledger out of the bounded cursor JSON.
BEGIN;

CREATE TABLE IF NOT EXISTS collection_discovery_staged_ids (
  target_id UUID NOT NULL REFERENCES collection_targets(id) ON DELETE CASCADE,
  source_listing_id TEXT NOT NULL,
  staged_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (target_id, source_listing_id)
);

ALTER TABLE collection_discovery_staged_ids
  ADD COLUMN IF NOT EXISTS last_seen_sweep BIGINT
    CHECK (last_seen_sweep IS NULL OR last_seen_sweep >= 0);

INSERT INTO collection_discovery_staged_ids (target_id, source_listing_id)
SELECT DISTINCT state.target_id, item.source_listing_id
FROM collection_discovery_states state
CROSS JOIN LATERAL jsonb_array_elements_text(state.seen_listing_ids) AS item(source_listing_id)
ON CONFLICT (target_id, source_listing_id) DO NOTHING;

INSERT INTO collection_discovery_staged_ids
  (target_id, source_listing_id, last_seen_sweep)
SELECT DISTINCT state.target_id, item.source_listing_id, state.sweep_number
FROM collection_discovery_states state
CROSS JOIN LATERAL jsonb_array_elements_text(state.sweep_seen_listing_ids)
  AS item(source_listing_id)
ON CONFLICT (target_id, source_listing_id) DO UPDATE SET
  last_seen_sweep = GREATEST(
    COALESCE(collection_discovery_staged_ids.last_seen_sweep, EXCLUDED.last_seen_sweep),
    EXCLUDED.last_seen_sweep
  );

UPDATE collection_discovery_states
SET seen_listing_ids = '[]'::jsonb,
    sweep_seen_listing_ids = '[]'::jsonb
WHERE seen_listing_ids <> '[]'::jsonb OR sweep_seen_listing_ids <> '[]'::jsonb;

COMMIT;
