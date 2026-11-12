-- Cover per-source health counts and the latest run lookup without changing data.
BEGIN;

CREATE INDEX IF NOT EXISTS idx_collection_runs_source_metrics
  ON collection_runs(source, started_at DESC)
  INCLUDE(status, finished_at, note);

CREATE INDEX IF NOT EXISTS idx_collection_candidates_source_review
  ON collection_candidates(source, review_status);

COMMIT;
