-- Ningbo Real Estate AI / V0.1. Initial install only; use migrations for future changes.
BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS monitored_accounts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  platform TEXT NOT NULL CHECK (platform IN ('douyin', 'wechat_channels')),
  account_ref TEXT NOT NULL,
  nickname TEXT,
  collector_mode TEXT NOT NULL CHECK (collector_mode IN ('dtk','manual')),
  history_mode TEXT NOT NULL DEFAULT 'none' CHECK (history_mode IN ('none','30d','90d')),
  poll_interval_minutes INTEGER NOT NULL DEFAULT 120 CHECK (poll_interval_minutes BETWEEN 60 AND 10080),
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  initial_synced BOOLEAN NOT NULL DEFAULT FALSE,
  next_poll_at TIMESTAMPTZ,
  last_success_at TIMESTAMPTZ,
  last_error TEXT,
  last_status TEXT NOT NULL DEFAULT 'not_started',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(platform, account_ref)
);
CREATE INDEX IF NOT EXISTS idx_accounts_due ON monitored_accounts(next_poll_at) WHERE enabled AND collector_mode='dtk';

CREATE TABLE IF NOT EXISTS account_sync_runs (
  id BIGSERIAL PRIMARY KEY,
  account_id UUID NOT NULL REFERENCES monitored_accounts(id) ON DELETE CASCADE,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at TIMESTAMPTZ,
  status TEXT NOT NULL CHECK (status IN ('running','success','partial','failed','blocked_config')),
  pages INTEGER NOT NULL DEFAULT 0,
  observed_count INTEGER NOT NULL DEFAULT 0,
  new_count INTEGER NOT NULL DEFAULT 0,
  error_text TEXT
);
CREATE INDEX IF NOT EXISTS idx_runs_account ON account_sync_runs(account_id,started_at DESC);

CREATE TABLE IF NOT EXISTS account_seen_posts (
  platform TEXT NOT NULL CHECK (platform IN ('douyin','wechat_channels')),
  source_post_id TEXT NOT NULL,
  account_id UUID NOT NULL REFERENCES monitored_accounts(id) ON DELETE CASCADE,
  baseline_only BOOLEAN NOT NULL DEFAULT FALSE,
  first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY(platform, source_post_id)
);

CREATE TABLE IF NOT EXISTS videos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID REFERENCES monitored_accounts(id) ON DELETE SET NULL,
  platform TEXT NOT NULL CHECK (platform IN ('douyin','wechat_channels')),
  source_post_id TEXT NOT NULL,
  source_url TEXT,
  author_name TEXT,
  title TEXT,
  description TEXT,
  published_at TIMESTAMPTZ,
  transcript TEXT,
  ocr_text TEXT,
  extracted_fields JSONB NOT NULL DEFAULT '{}'::jsonb,
  processing_status TEXT NOT NULL DEFAULT 'metadata' CHECK (processing_status IN ('metadata','enriched','reviewed')),
  raw_location TEXT,
  permission_note TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(platform, source_post_id)
);
CREATE INDEX IF NOT EXISTS idx_videos_recent ON videos(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_videos_account ON videos(account_id,created_at DESC);

CREATE TABLE IF NOT EXISTS communities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  city TEXT NOT NULL DEFAULT '宁波',
  name TEXT NOT NULL,
  district TEXT,
  address TEXT,
  latitude NUMERIC(10,7),
  longitude NUMERIC(10,7),
  verified BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(city,name)
);
CREATE TABLE IF NOT EXISTS community_aliases (
  id BIGSERIAL PRIMARY KEY,
  city TEXT NOT NULL DEFAULT '宁波',
  alias TEXT NOT NULL,
  community_id UUID NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
  UNIQUE(city,alias)
);

CREATE TABLE IF NOT EXISTS properties (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  community_id UUID NOT NULL REFERENCES communities(id),
  area_sqm NUMERIC(9,2) NOT NULL CHECK (area_sqm>0),
  bedrooms INTEGER CHECK (bedrooms BETWEEN 0 AND 20),
  floor_text TEXT,
  layout_note TEXT,
  decoration TEXT,
  building_info TEXT,
  identity_status TEXT NOT NULL DEFAULT 'unverified' CHECK (identity_status IN ('unverified','verified')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS source_listings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source TEXT NOT NULL CHECK (source IN ('beike','anjuke','agent','other')),
  source_listing_id TEXT NOT NULL,
  property_id UUID NOT NULL REFERENCES properties(id),
  title TEXT,
  listing_url TEXT,
  asking_price_wan NUMERIC(12,2) NOT NULL CHECK (asking_price_wan>0),
  first_observed_at TIMESTAMPTZ NOT NULL,
  last_observed_at TIMESTAMPTZ NOT NULL,
  status TEXT NOT NULL DEFAULT 'unknown' CHECK (status IN ('unknown','available','withdrawn','sold')),
  permission_note TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(source,source_listing_id)
);
CREATE INDEX IF NOT EXISTS idx_listings_property ON source_listings(property_id);
CREATE INDEX IF NOT EXISTS idx_listings_price ON source_listings(asking_price_wan);

-- Historical quote snapshots: only same-source listing price changes are comparable as drops.
CREATE TABLE IF NOT EXISTS price_history (
  id BIGSERIAL PRIMARY KEY,
  listing_id UUID NOT NULL REFERENCES source_listings(id) ON DELETE CASCADE,
  price_wan NUMERIC(12,2) NOT NULL CHECK (price_wan>0),
  observed_at TIMESTAMPTZ NOT NULL,
  quote_type TEXT NOT NULL DEFAULT 'platform_listed' CHECK (quote_type IN ('platform_listed','agent_claim')),
  evidence_url TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(listing_id,observed_at,quote_type)
);
CREATE INDEX IF NOT EXISTS idx_prices_listing_time ON price_history(listing_id,observed_at DESC);

-- Candidate relationships are NOT verified identities by default.
CREATE TABLE IF NOT EXISTS property_matches (
  id BIGSERIAL PRIMARY KEY,
  video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
  listing_id UUID REFERENCES source_listings(id) ON DELETE CASCADE,
  match_score NUMERIC(5,2) CHECK(match_score BETWEEN 0 AND 100),
  evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
  status TEXT NOT NULL DEFAULT 'candidate' CHECK(status IN ('candidate','confirmed','rejected')),
  reviewed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK(video_id IS NOT NULL AND listing_id IS NOT NULL),
  UNIQUE(video_id,listing_id)
);

CREATE TABLE IF NOT EXISTS saved_searches (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  district TEXT,
  community_name TEXT,
  max_price_wan NUMERIC(12,2) CHECK(max_price_wan>0),
  min_area_sqm NUMERIC(9,2) CHECK(min_area_sqm>0),
  min_bedrooms INTEGER CHECK(min_bedrooms BETWEEN 0 AND 20),
  min_drop_pct NUMERIC(5,2) NOT NULL DEFAULT 5 CHECK(min_drop_pct BETWEEN 0 AND 100),
  notifications_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- V0.1 outbox only: records a notification event, does NOT send messages externally.
CREATE TABLE IF NOT EXISTS notification_logs (
  id BIGSERIAL PRIMARY KEY,
  search_id UUID NOT NULL REFERENCES saved_searches(id) ON DELETE CASCADE,
  listing_id UUID NOT NULL REFERENCES source_listings(id) ON DELETE CASCADE,
  event_key TEXT NOT NULL,
  event_type TEXT NOT NULL CHECK(event_type IN ('new_listing','price_drop')),
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  delivery_status TEXT NOT NULL DEFAULT 'pending' CHECK(delivery_status IN ('pending','read')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(search_id,event_key)
);
CREATE INDEX IF NOT EXISTS idx_notifications_status ON notification_logs(delivery_status,created_at DESC);

COMMIT;
