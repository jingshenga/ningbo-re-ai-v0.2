-- Extend condition orders without changing or removing existing filters.
BEGIN;

ALTER TABLE saved_searches
  ADD COLUMN IF NOT EXISTS districts TEXT[] NOT NULL DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS preferred_communities TEXT[] NOT NULL DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS excluded_communities TEXT[] NOT NULL DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS max_listing_age_days INTEGER;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'saved_searches'::regclass
      AND conname = 'saved_searches_max_listing_age_days_check'
  ) THEN
    ALTER TABLE saved_searches
      ADD CONSTRAINT saved_searches_max_listing_age_days_check
      CHECK (max_listing_age_days IS NULL OR max_listing_age_days BETWEEN 1 AND 3650);
  END IF;
END $$;

COMMIT;
