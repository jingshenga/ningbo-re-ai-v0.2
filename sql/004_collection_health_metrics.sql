-- Maintain the collection health snapshot in the same transaction as source rows.
BEGIN;

LOCK TABLE source_registry, collection_runs, collection_candidates, source_listings
  IN SHARE ROW EXCLUSIVE MODE;

CREATE TABLE IF NOT EXISTS collection_health_metrics (
  source TEXT PRIMARY KEY REFERENCES source_registry(source) ON DELETE CASCADE,
  success_count BIGINT NOT NULL DEFAULT 0 CHECK (success_count >= 0),
  failure_count BIGINT NOT NULL DEFAULT 0 CHECK (failure_count >= 0),
  blocked_count BIGINT NOT NULL DEFAULT 0 CHECK (blocked_count >= 0),
  pending_count BIGINT NOT NULL DEFAULT 0 CHECK (pending_count >= 0),
  approved_count BIGINT NOT NULL DEFAULT 0 CHECK (approved_count >= 0),
  rejected_count BIGINT NOT NULL DEFAULT 0 CHECK (rejected_count >= 0),
  listing_count BIGINT NOT NULL DEFAULT 0 CHECK (listing_count >= 0),
  last_attempt_at TIMESTAMPTZ,
  last_success_at TIMESTAMPTZ,
  last_observed_at TIMESTAMPTZ,
  latest_status TEXT,
  latest_note TEXT,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION refresh_collection_run_times(p_source TEXT)
RETURNS VOID LANGUAGE plpgsql AS $$
DECLARE
  v_last_attempt TIMESTAMPTZ;
  v_last_success TIMESTAMPTZ;
  v_latest_status TEXT;
  v_latest_note TEXT;
BEGIN
  SELECT max(started_at), max(finished_at) FILTER (WHERE status='success')
    INTO v_last_attempt, v_last_success
    FROM collection_runs WHERE source=p_source;
  SELECT status,note INTO v_latest_status,v_latest_note
    FROM collection_runs WHERE source=p_source
    ORDER BY started_at DESC,id DESC LIMIT 1;
  UPDATE collection_health_metrics SET last_attempt_at=v_last_attempt,
    last_success_at=v_last_success,latest_status=v_latest_status,
    latest_note=v_latest_note,updated_at=now() WHERE source=p_source;
END $$;

CREATE OR REPLACE FUNCTION apply_collection_run_delta(
  p_source TEXT,p_status TEXT,p_delta BIGINT,p_started TIMESTAMPTZ,
  p_finished TIMESTAMPTZ,p_note TEXT
) RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
  IF p_delta < 0 THEN
    UPDATE collection_health_metrics SET
      success_count=success_count+CASE WHEN p_status='success' THEN p_delta ELSE 0 END,
      failure_count=failure_count+CASE WHEN p_status='failed' THEN p_delta ELSE 0 END,
      blocked_count=blocked_count+CASE WHEN p_status LIKE 'blocked%' THEN p_delta ELSE 0 END,
      updated_at=now()
    WHERE source=p_source;
    RETURN;
  END IF;

  INSERT INTO collection_health_metrics(source,success_count,failure_count,blocked_count,
      last_attempt_at,last_success_at,latest_status,latest_note)
    VALUES (p_source,
      CASE WHEN p_status='success' THEN p_delta ELSE 0 END,
      CASE WHEN p_status='failed' THEN p_delta ELSE 0 END,
      CASE WHEN p_status LIKE 'blocked%' THEN p_delta ELSE 0 END,
      CASE WHEN p_delta > 0 THEN p_started END,
      CASE WHEN p_delta > 0 AND p_status='success' THEN p_finished END,
      CASE WHEN p_delta > 0 THEN p_status END,
      CASE WHEN p_delta > 0 THEN p_note END)
  ON CONFLICT(source) DO UPDATE SET
    success_count=collection_health_metrics.success_count+EXCLUDED.success_count,
    failure_count=collection_health_metrics.failure_count+EXCLUDED.failure_count,
    blocked_count=collection_health_metrics.blocked_count+EXCLUDED.blocked_count,
    last_attempt_at=CASE WHEN p_delta > 0 THEN
      GREATEST(collection_health_metrics.last_attempt_at,EXCLUDED.last_attempt_at)
      ELSE collection_health_metrics.last_attempt_at END,
    last_success_at=CASE WHEN p_delta > 0 THEN
      GREATEST(collection_health_metrics.last_success_at,EXCLUDED.last_success_at)
      ELSE collection_health_metrics.last_success_at END,
    latest_status=CASE WHEN p_delta > 0 AND
      (collection_health_metrics.last_attempt_at IS NULL OR
       p_started >= collection_health_metrics.last_attempt_at)
      THEN p_status ELSE collection_health_metrics.latest_status END,
    latest_note=CASE WHEN p_delta > 0 AND
      (collection_health_metrics.last_attempt_at IS NULL OR
       p_started >= collection_health_metrics.last_attempt_at)
      THEN p_note ELSE collection_health_metrics.latest_note END,
    updated_at=now();
END $$;

CREATE OR REPLACE FUNCTION maintain_collection_run_metrics()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP='INSERT' THEN
    PERFORM apply_collection_run_delta(NEW.source,NEW.status,1,NEW.started_at,NEW.finished_at,NEW.note);
    RETURN NEW;
  ELSIF TG_OP='DELETE' THEN
    PERFORM apply_collection_run_delta(OLD.source,OLD.status,-1,OLD.started_at,OLD.finished_at,OLD.note);
    PERFORM refresh_collection_run_times(OLD.source);
    RETURN OLD;
  END IF;

  PERFORM apply_collection_run_delta(OLD.source,OLD.status,-1,OLD.started_at,OLD.finished_at,OLD.note);
  PERFORM apply_collection_run_delta(NEW.source,NEW.status,1,NEW.started_at,NEW.finished_at,NEW.note);
  PERFORM refresh_collection_run_times(OLD.source);
  IF NEW.source IS DISTINCT FROM OLD.source THEN
    PERFORM refresh_collection_run_times(NEW.source);
  END IF;
  RETURN NEW;
END $$;

CREATE OR REPLACE FUNCTION apply_collection_candidate_delta(
  p_source TEXT,p_status TEXT,p_delta BIGINT
) RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
  IF p_delta < 0 THEN
    UPDATE collection_health_metrics SET
      pending_count=pending_count+CASE WHEN p_status='pending' THEN p_delta ELSE 0 END,
      approved_count=approved_count+CASE WHEN p_status='approved' THEN p_delta ELSE 0 END,
      rejected_count=rejected_count+CASE WHEN p_status='rejected' THEN p_delta ELSE 0 END,
      updated_at=now()
    WHERE source=p_source;
    RETURN;
  END IF;

  INSERT INTO collection_health_metrics(source,pending_count,approved_count,rejected_count)
    VALUES (p_source,
      CASE WHEN p_status='pending' THEN p_delta ELSE 0 END,
      CASE WHEN p_status='approved' THEN p_delta ELSE 0 END,
      CASE WHEN p_status='rejected' THEN p_delta ELSE 0 END)
  ON CONFLICT(source) DO UPDATE SET
    pending_count=collection_health_metrics.pending_count+EXCLUDED.pending_count,
    approved_count=collection_health_metrics.approved_count+EXCLUDED.approved_count,
    rejected_count=collection_health_metrics.rejected_count+EXCLUDED.rejected_count,
    updated_at=now();
END $$;

CREATE OR REPLACE FUNCTION maintain_collection_candidate_metrics()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP='INSERT' THEN
    PERFORM apply_collection_candidate_delta(NEW.source,NEW.review_status,1);
    RETURN NEW;
  ELSIF TG_OP='DELETE' THEN
    PERFORM apply_collection_candidate_delta(OLD.source,OLD.review_status,-1);
    RETURN OLD;
  END IF;

  IF NEW.source IS NOT DISTINCT FROM OLD.source THEN
    IF NEW.review_status IS DISTINCT FROM OLD.review_status THEN
      UPDATE collection_health_metrics SET
        pending_count=pending_count
          +CASE WHEN NEW.review_status='pending' THEN 1 ELSE 0 END
          -CASE WHEN OLD.review_status='pending' THEN 1 ELSE 0 END,
        approved_count=approved_count
          +CASE WHEN NEW.review_status='approved' THEN 1 ELSE 0 END
          -CASE WHEN OLD.review_status='approved' THEN 1 ELSE 0 END,
        rejected_count=rejected_count
          +CASE WHEN NEW.review_status='rejected' THEN 1 ELSE 0 END
          -CASE WHEN OLD.review_status='rejected' THEN 1 ELSE 0 END,
        updated_at=now()
      WHERE source=NEW.source;
    END IF;
    RETURN NEW;
  END IF;

  PERFORM apply_collection_candidate_delta(OLD.source,OLD.review_status,-1);
  PERFORM apply_collection_candidate_delta(NEW.source,NEW.review_status,1);
  RETURN NEW;
END $$;

CREATE OR REPLACE FUNCTION refresh_collection_listing_time(p_source TEXT)
RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
  UPDATE collection_health_metrics SET
    last_observed_at=(SELECT max(last_observed_at) FROM source_listings WHERE source=p_source),
    updated_at=now()
  WHERE source=p_source;
END $$;

CREATE OR REPLACE FUNCTION maintain_collection_listing_metrics()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
  v_metric_last_observed TIMESTAMPTZ;
BEGIN
  IF TG_OP='INSERT' THEN
    UPDATE collection_health_metrics SET listing_count=listing_count+1,
      last_observed_at=GREATEST(last_observed_at,NEW.last_observed_at),updated_at=now()
      WHERE source=NEW.source;
    RETURN NEW;
  ELSIF TG_OP='DELETE' THEN
    UPDATE collection_health_metrics SET listing_count=listing_count-1,updated_at=now()
      WHERE source=OLD.source;
    PERFORM refresh_collection_listing_time(OLD.source);
    RETURN OLD;
  END IF;

  IF NEW.source IS DISTINCT FROM OLD.source THEN
    UPDATE collection_health_metrics SET listing_count=listing_count-1,updated_at=now()
      WHERE source=OLD.source;
    UPDATE collection_health_metrics SET listing_count=listing_count+1,updated_at=now()
      WHERE source=NEW.source;
    PERFORM refresh_collection_listing_time(OLD.source);
    PERFORM refresh_collection_listing_time(NEW.source);
  ELSIF NEW.last_observed_at IS DISTINCT FROM OLD.last_observed_at THEN
    -- Advancing the maximum is constant-time; rescan only if the previous maximum moved back.
    UPDATE collection_health_metrics SET
      last_observed_at=GREATEST(last_observed_at,NEW.last_observed_at),updated_at=now()
      WHERE source=NEW.source RETURNING last_observed_at INTO v_metric_last_observed;
    IF OLD.last_observed_at >= v_metric_last_observed
        AND NEW.last_observed_at < OLD.last_observed_at THEN
      PERFORM refresh_collection_listing_time(NEW.source);
    END IF;
  END IF;
  RETURN NEW;
END $$;

CREATE OR REPLACE FUNCTION seed_collection_health_metrics()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  INSERT INTO collection_health_metrics(source) VALUES (NEW.source)
    ON CONFLICT(source) DO NOTHING;
  RETURN NEW;
END $$;

-- Backfill existing rows before installing triggers while the source tables are locked.
WITH run_metrics AS (
  SELECT source,
    count(*) FILTER (WHERE status='success') AS success_count,
    count(*) FILTER (WHERE status='failed') AS failure_count,
    count(*) FILTER (WHERE status LIKE 'blocked%') AS blocked_count,
    max(started_at) AS last_attempt_at,
    max(finished_at) FILTER (WHERE status='success') AS last_success_at
  FROM collection_runs GROUP BY source
), candidate_metrics AS (
  SELECT source,
    count(*) FILTER (WHERE review_status='pending') AS pending_count,
    count(*) FILTER (WHERE review_status='approved') AS approved_count,
    count(*) FILTER (WHERE review_status='rejected') AS rejected_count
  FROM collection_candidates GROUP BY source
), listing_metrics AS (
  SELECT source,count(*) AS listing_count,max(last_observed_at) AS last_observed_at
  FROM source_listings GROUP BY source
), latest_runs AS (
  SELECT DISTINCT ON (source) source,status,note
  FROM collection_runs ORDER BY source,started_at DESC,id DESC
)
INSERT INTO collection_health_metrics(source,success_count,failure_count,blocked_count,
    pending_count,approved_count,rejected_count,listing_count,last_attempt_at,last_success_at,
    last_observed_at,latest_status,latest_note)
SELECT s.source,coalesce(r.success_count,0),coalesce(r.failure_count,0),coalesce(r.blocked_count,0),
  coalesce(c.pending_count,0),coalesce(c.approved_count,0),coalesce(c.rejected_count,0),
  coalesce(l.listing_count,0),r.last_attempt_at,r.last_success_at,l.last_observed_at,
  lr.status,lr.note
FROM source_registry s
LEFT JOIN run_metrics r USING(source)
LEFT JOIN candidate_metrics c USING(source)
LEFT JOIN listing_metrics l USING(source)
LEFT JOIN latest_runs lr USING(source)
ON CONFLICT(source) DO UPDATE SET
  success_count=EXCLUDED.success_count,failure_count=EXCLUDED.failure_count,
  blocked_count=EXCLUDED.blocked_count,pending_count=EXCLUDED.pending_count,
  approved_count=EXCLUDED.approved_count,rejected_count=EXCLUDED.rejected_count,
  listing_count=EXCLUDED.listing_count,last_attempt_at=EXCLUDED.last_attempt_at,
  last_success_at=EXCLUDED.last_success_at,last_observed_at=EXCLUDED.last_observed_at,
  latest_status=EXCLUDED.latest_status,latest_note=EXCLUDED.latest_note,updated_at=now();

DROP TRIGGER IF EXISTS collection_runs_health_metrics ON collection_runs;
CREATE TRIGGER collection_runs_health_metrics AFTER INSERT OR UPDATE OR DELETE ON collection_runs
  FOR EACH ROW EXECUTE FUNCTION maintain_collection_run_metrics();
DROP TRIGGER IF EXISTS collection_candidates_health_metrics ON collection_candidates;
CREATE TRIGGER collection_candidates_health_metrics AFTER INSERT OR UPDATE OR DELETE ON collection_candidates
  FOR EACH ROW EXECUTE FUNCTION maintain_collection_candidate_metrics();
DROP TRIGGER IF EXISTS source_listings_health_metrics ON source_listings;
CREATE TRIGGER source_listings_health_metrics AFTER INSERT OR UPDATE OR DELETE ON source_listings
  FOR EACH ROW EXECUTE FUNCTION maintain_collection_listing_metrics();
DROP TRIGGER IF EXISTS source_registry_health_metrics ON source_registry;
CREATE TRIGGER source_registry_health_metrics AFTER INSERT ON source_registry
  FOR EACH ROW EXECUTE FUNCTION seed_collection_health_metrics();

COMMIT;
