-- Keep discovered detail URLs durable so one failing detail does not block pagination.
BEGIN;

CREATE TABLE IF NOT EXISTS collection_discovery_detail_queue (
  target_id UUID NOT NULL,
  source TEXT NOT NULL CHECK (source IN ('beike', 'anjuke')),
  source_listing_id TEXT NOT NULL CHECK (
    source_listing_id ~ '^[0-9]+$' AND
    ((source = 'beike' AND length(source_listing_id) BETWEEN 8 AND 220) OR
     (source = 'anjuke' AND length(source_listing_id) BETWEEN 7 AND 220))
  ),
  listing_url TEXT NOT NULL,
  discovered_page_url TEXT NOT NULL,
  queued_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
  last_attempt_at TIMESTAMPTZ,
  last_error_type TEXT CHECK (last_error_type IS NULL OR
    (length(last_error_type) <= 80 AND last_error_type ~ '^[A-Za-z_][A-Za-z0-9_]*$')),
  PRIMARY KEY (target_id, source_listing_id),
  FOREIGN KEY (target_id, source, source_listing_id)
    REFERENCES collection_listing_observations(target_id, source, source_listing_id)
    ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_collection_detail_queue_due
  ON collection_discovery_detail_queue(
    target_id, last_attempt_at ASC NULLS FIRST, queued_at, source_listing_id
  );

COMMIT;
