-- Persist bounded listing-page cursors for operator-approved discovery targets.
BEGIN;

CREATE TABLE IF NOT EXISTS collection_discovery_states (
  target_id UUID PRIMARY KEY REFERENCES collection_targets(id) ON DELETE CASCADE,
  revision BIGINT NOT NULL DEFAULT 1 CHECK (revision >= 1),
  version INTEGER NOT NULL DEFAULT 1 CHECK (version = 1),
  seen_listing_ids JSONB NOT NULL DEFAULT '[]'::jsonb
    CHECK (jsonb_typeof(seen_listing_ids) = 'array'),
  last_page_url TEXT,
  next_page_url TEXT,
  visited_page_urls JSONB NOT NULL DEFAULT '[]'::jsonb
    CHECK (jsonb_typeof(visited_page_urls) = 'array'),
  last_attempted_page_url TEXT,
  last_error_type TEXT CHECK (last_error_type IS NULL OR
    (length(last_error_type) <= 80 AND last_error_type ~ '^[A-Za-z_][A-Za-z0-9_]*$')),
  failed_attempts INTEGER NOT NULL DEFAULT 0 CHECK (failed_attempts >= 0),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMIT;
