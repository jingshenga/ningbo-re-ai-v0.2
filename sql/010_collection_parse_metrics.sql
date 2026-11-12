-- Count parser stages per source while keeping an append-only attempt record.
BEGIN;

ALTER TABLE collection_health_metrics
  ADD COLUMN IF NOT EXISTS parse_attempt_count BIGINT NOT NULL DEFAULT 0
    CHECK (parse_attempt_count >= 0),
  ADD COLUMN IF NOT EXISTS parse_success_count BIGINT NOT NULL DEFAULT 0
    CHECK (parse_success_count >= 0),
  ADD COLUMN IF NOT EXISTS complete_field_count BIGINT NOT NULL DEFAULT 0
    CHECK (complete_field_count >= 0);

CREATE TABLE IF NOT EXISTS collection_parse_attempts (
  id BIGSERIAL PRIMARY KEY,
  source TEXT NOT NULL REFERENCES source_registry(source) ON DELETE CASCADE,
  capture_method TEXT NOT NULL CHECK (
    capture_method IN ('manual_html_snapshot', 'public_page_collection')
  ),
  parser_version TEXT NOT NULL,
  parse_status TEXT NOT NULL CHECK (parse_status IN ('success', 'failed')),
  required_fields_complete BOOLEAN NOT NULL DEFAULT FALSE,
  attempted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (parse_status = 'success' OR NOT required_fields_complete)
);

CREATE INDEX IF NOT EXISTS idx_collection_parse_attempts_source_time
  ON collection_parse_attempts(source, attempted_at DESC);

CREATE OR REPLACE FUNCTION maintain_collection_parse_metrics()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  INSERT INTO collection_health_metrics(source,parse_attempt_count,
      parse_success_count,complete_field_count)
    VALUES (NEW.source,1,
      CASE WHEN NEW.parse_status='success' THEN 1 ELSE 0 END,
      CASE WHEN NEW.required_fields_complete THEN 1 ELSE 0 END)
  ON CONFLICT(source) DO UPDATE SET
    parse_attempt_count=collection_health_metrics.parse_attempt_count+1,
    parse_success_count=collection_health_metrics.parse_success_count
      +CASE WHEN NEW.parse_status='success' THEN 1 ELSE 0 END,
    complete_field_count=collection_health_metrics.complete_field_count
      +CASE WHEN NEW.required_fields_complete THEN 1 ELSE 0 END,
    updated_at=now();
  RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS collection_parse_attempt_metrics_trigger
  ON collection_parse_attempts;
CREATE TRIGGER collection_parse_attempt_metrics_trigger
  AFTER INSERT ON collection_parse_attempts
  FOR EACH ROW EXECUTE FUNCTION maintain_collection_parse_metrics();

COMMIT;
