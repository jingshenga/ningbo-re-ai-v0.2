-- Append operator verification conclusions without changing canonical listing state.
BEGIN;

ALTER TABLE collection_listing_observations
  DROP CONSTRAINT IF EXISTS collection_listing_observations_review_status_check;
ALTER TABLE collection_listing_observations
  ADD CONSTRAINT collection_listing_observations_review_status_check
  CHECK (review_status IN ('active', 'pending_review', 'reviewed'));

CREATE TABLE IF NOT EXISTS collection_listing_reviews (
  id BIGSERIAL PRIMARY KEY,
  target_id UUID NOT NULL,
  source TEXT NOT NULL CHECK (source IN ('beike', 'anjuke')),
  source_listing_id TEXT NOT NULL CHECK (
    source_listing_id ~ '^[0-9]+$' AND
    ((source = 'beike' AND length(source_listing_id) BETWEEN 8 AND 220) OR
     (source = 'anjuke' AND length(source_listing_id) BETWEEN 7 AND 220))
  ),
  conclusion TEXT NOT NULL CHECK (
    conclusion IN ('still_listed', 'confirmed_withdrawn', 'inconclusive')
  ),
  note TEXT CHECK (note IS NULL OR char_length(note) <= 1000),
  reviewed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  FOREIGN KEY (target_id, source, source_listing_id)
    REFERENCES collection_listing_observations(target_id, source, source_listing_id)
    ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_collection_listing_reviews_history
  ON collection_listing_reviews(target_id, source, source_listing_id,
                                 reviewed_at DESC, id DESC);

COMMIT;
