-- Track listing observations per discovery target and retain source-page evidence.
BEGIN;

CREATE TABLE IF NOT EXISTS collection_listing_observations (
  target_id UUID NOT NULL,
  source TEXT NOT NULL CHECK (source IN ('beike', 'anjuke')),
  source_listing_id TEXT NOT NULL CHECK (
    source_listing_id ~ '^[0-9]+$' AND
    ((source = 'beike' AND length(source_listing_id) BETWEEN 8 AND 220) OR
     (source = 'anjuke' AND length(source_listing_id) BETWEEN 7 AND 220))
  ),
  listing_url TEXT NOT NULL,
  first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  observation_count BIGINT NOT NULL DEFAULT 1 CHECK (observation_count >= 1),
  first_page_url TEXT NOT NULL,
  last_page_url TEXT NOT NULL,
  first_page_sha256 CHAR(64) NOT NULL CHECK (first_page_sha256 ~ '^[0-9a-f]{64}$'),
  last_page_sha256 CHAR(64) NOT NULL CHECK (last_page_sha256 ~ '^[0-9a-f]{64}$'),
  first_page_storage_path TEXT NOT NULL,
  last_page_storage_path TEXT NOT NULL,
  last_seen_sweep BIGINT NOT NULL DEFAULT 0 CHECK (last_seen_sweep >= 0),
  last_evaluated_sweep BIGINT NOT NULL DEFAULT 0 CHECK (last_evaluated_sweep >= 0),
  missed_complete_scans SMALLINT NOT NULL DEFAULT 0
    CHECK (missed_complete_scans BETWEEN 0 AND 2),
  review_status TEXT NOT NULL DEFAULT 'active'
    CHECK (review_status IN ('active', 'pending_review')),
  PRIMARY KEY (target_id, source, source_listing_id)
);

CREATE INDEX IF NOT EXISTS idx_collection_listing_observations_review
  ON collection_listing_observations(target_id, review_status, last_seen_at DESC);

COMMIT;
