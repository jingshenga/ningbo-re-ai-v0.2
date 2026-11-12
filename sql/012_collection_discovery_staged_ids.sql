-- Keep the per-target detail dedupe ledger out of the bounded cursor JSON.
BEGIN;

CREATE TABLE IF NOT EXISTS collection_discovery_staged_ids (
  target_id UUID NOT NULL REFERENCES collection_targets(id) ON DELETE CASCADE,
  source_listing_id TEXT NOT NULL,
  staged_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (target_id, source_listing_id)
);

INSERT INTO collection_discovery_staged_ids (target_id, source_listing_id)
SELECT state.target_id, item.source_listing_id
FROM collection_discovery_states state
CROSS JOIN LATERAL jsonb_array_elements_text(state.seen_listing_ids) AS item(source_listing_id)
ON CONFLICT (target_id, source_listing_id) DO NOTHING;

UPDATE collection_discovery_states
SET seen_listing_ids = '[]'::jsonb,
    sweep_seen_listing_ids = '[]'::jsonb
WHERE seen_listing_ids <> '[]'::jsonb OR sweep_seen_listing_ids <> '[]'::jsonb;

COMMIT;
