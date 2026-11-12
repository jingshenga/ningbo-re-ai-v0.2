-- V0.2 safe collection staging and source policy. Idempotent migration.
-- Public-page collection is a technical plan, NOT a representation of permission.
BEGIN;

CREATE TABLE IF NOT EXISTS source_registry (
  source TEXT PRIMARY KEY CHECK (source IN ('beike','anjuke')),
  current_mode TEXT NOT NULL DEFAULT 'public_page_collection'
    CHECK (current_mode IN ('public_page_collection','licensed_api')),
  online_policy_status TEXT NOT NULL DEFAULT 'not_reviewed'
    CHECK (online_policy_status IN ('not_reviewed','not_authorized','approved','revoked')),
  online_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  policy_reference TEXT,
  policy_reviewed_at TIMESTAMPTZ,
  note TEXT,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (NOT online_enabled OR (online_policy_status='approved' AND policy_reference IS NOT NULL))
);
INSERT INTO source_registry(source,current_mode,online_policy_status,online_enabled,note)
  VALUES
  ('beike','public_page_collection','not_authorized',FALSE,'Website service agreement restricts unauthorized automated collection; keep OFF until written permission/policy review.'),
  ('anjuke','public_page_collection','not_reviewed',FALSE,'Review current service terms and robots before any online access.')
ON CONFLICT (source) DO NOTHING;

CREATE TABLE IF NOT EXISTS collection_targets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source TEXT NOT NULL REFERENCES source_registry(source),
  url TEXT NOT NULL,
  enabled BOOLEAN NOT NULL DEFAULT FALSE,
  poll_interval_minutes INTEGER NOT NULL DEFAULT 1440 CHECK(poll_interval_minutes BETWEEN 360 AND 10080),
  next_check_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_attempt_at TIMESTAMPTZ,
  last_status TEXT NOT NULL DEFAULT 'not_started',
  last_error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(source,url)
);
CREATE INDEX IF NOT EXISTS idx_collection_targets_due
  ON collection_targets(next_check_at) WHERE enabled;

CREATE TABLE IF NOT EXISTS collection_candidates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source TEXT NOT NULL REFERENCES source_registry(source),
  source_url TEXT NOT NULL,
  capture_method TEXT NOT NULL CHECK(capture_method IN ('manual_html_snapshot','public_page_collection')),
  source_listing_id TEXT,
  raw_sha256 CHAR(64) NOT NULL,
  raw_storage_path TEXT NOT NULL,
  parser_version TEXT NOT NULL,
  extracted_fields JSONB NOT NULL DEFAULT '{}'::jsonb,
  warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
  review_status TEXT NOT NULL DEFAULT 'pending' CHECK(review_status IN ('pending','approved','rejected')),
  review_note TEXT,
  approved_listing_id UUID REFERENCES source_listings(id),
  captured_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  reviewed_at TIMESTAMPTZ,
  UNIQUE(source,source_url,raw_sha256)
);
CREATE INDEX IF NOT EXISTS idx_candidates_pending ON collection_candidates(captured_at DESC)
  WHERE review_status='pending';

CREATE TABLE IF NOT EXISTS collection_runs (
  id BIGSERIAL PRIMARY KEY,
  target_id UUID REFERENCES collection_targets(id) ON DELETE SET NULL,
  source TEXT NOT NULL REFERENCES source_registry(source),
  source_url TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('success','blocked_policy','blocked_robots','blocked_upstream','failed')),
  http_status INTEGER,
  candidate_id UUID REFERENCES collection_candidates(id),
  note TEXT,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_collection_runs_target ON collection_runs(target_id,started_at DESC);

ALTER TABLE source_listings
  ADD COLUMN IF NOT EXISTS acquisition_method TEXT NOT NULL DEFAULT 'manual_import';
ALTER TABLE source_listings
  ADD COLUMN IF NOT EXISTS latest_candidate_id UUID REFERENCES collection_candidates(id);
ALTER TABLE source_listings
  ADD COLUMN IF NOT EXISTS last_evidence_sha256 CHAR(64);

-- V0.1 records retain their historical method as manual_import; never backfill a false origin.

COMMIT;
