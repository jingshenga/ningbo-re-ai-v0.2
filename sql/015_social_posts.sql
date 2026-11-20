-- Store operator-collected social media clues (one human-initiated capture per row;
-- never auto-collected, never promoted to official listings or price history).
BEGIN;

CREATE TABLE IF NOT EXISTS social_posts (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  platform TEXT NOT NULL CHECK (platform IN ('xiaohongshu', 'douyin', 'channels', 'other')),
  post_id TEXT,
  source_url TEXT NOT NULL,
  title TEXT,
  content TEXT NOT NULL,
  author_name TEXT,
  publish_time TEXT,
  media_urls JSONB NOT NULL DEFAULT '[]'::jsonb,
  tags JSONB NOT NULL DEFAULT '[]'::jsonb,
  raw_html_snippet TEXT,
  raw_sha256 TEXT NOT NULL UNIQUE,
  is_ningbo_related BOOLEAN NOT NULL DEFAULT false,
  matched_keywords JSONB NOT NULL DEFAULT '[]'::jsonb,
  extracted_hints JSONB,
  status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'archived')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS social_posts_created_at_idx
  ON social_posts (created_at DESC);

CREATE INDEX IF NOT EXISTS social_posts_platform_idx
  ON social_posts (platform, created_at DESC);

COMMIT;
