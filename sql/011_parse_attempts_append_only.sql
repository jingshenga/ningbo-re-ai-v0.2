-- Preserve the parse-attempt ledger and its insert-maintained health counters.
BEGIN;

CREATE OR REPLACE FUNCTION reject_collection_parse_attempt_mutation()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'collection_parse_attempts is append-only';
  RETURN NULL;
END $$;

DROP TRIGGER IF EXISTS collection_parse_attempts_no_update_delete
  ON collection_parse_attempts;
CREATE TRIGGER collection_parse_attempts_no_update_delete
  BEFORE UPDATE OR DELETE ON collection_parse_attempts
  FOR EACH ROW EXECUTE FUNCTION reject_collection_parse_attempt_mutation();

DROP TRIGGER IF EXISTS collection_parse_attempts_no_truncate
  ON collection_parse_attempts;
CREATE TRIGGER collection_parse_attempts_no_truncate
  BEFORE TRUNCATE ON collection_parse_attempts
  FOR EACH STATEMENT EXECUTE FUNCTION reject_collection_parse_attempt_mutation();

COMMIT;
