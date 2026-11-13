"""PG17 regression for loss of legacy discovery sweep IDs during migration 012."""
import json
import os
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql
import pytest
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from psycopg.rows import dict_row


DATABASE_URL = os.getenv("TEST_DATABASE_URL")
ROOT = Path(__file__).resolve().parents[1]
SEEN_IDS = {"12345678", "87654321"}
SWEEP_IDS = {"12345678", "55555555"}


def connect_test_db(conninfo, **kwargs):
    kwargs.setdefault("row_factory", dict_row)
    try:
        return psycopg.connect(conninfo, **kwargs)
    except psycopg.Error as exc:
        state = f" (SQLSTATE {exc.sqlstate})" if exc.sqlstate else ""
        raise RuntimeError(
            f"Cannot connect to isolated PostgreSQL test database{state}; details redacted"
        ) from None


def apply_pre_012_migrations(conn):
    for migration in sorted((ROOT / "sql").glob("*.sql")):
        if migration.name.startswith("012_"):
            continue
        conn.execute(migration.read_text(encoding="utf-8"))


def test_012_preserves_legacy_sweep_ids_without_matching_current_observation(monkeypatch):
    if not DATABASE_URL:
        pytest.skip("Set TEST_DATABASE_URL to run PostgreSQL integration tests")
    if conninfo_to_dict(DATABASE_URL).get("dbname") != "rehouse_test":
        pytest.fail("TEST_DATABASE_URL must point to the dedicated rehouse_test database")

    schema = "migration012_" + uuid4().hex
    created = False
    try:
        with connect_test_db(DATABASE_URL, autocommit=True) as conn:
            conn.execute(sql.SQL("CREATE SCHEMA {}").format(
                sql.Identifier(schema)
            ))
        created = True
        scoped_url = make_conninfo(DATABASE_URL, options=f"-csearch_path={schema}")

        with connect_test_db(scoped_url, autocommit=True) as conn:
            apply_pre_012_migrations(conn)

            target_id = conn.execute(
                """INSERT INTO collection_targets(source,url)
                   VALUES ('beike','https://nb.ke.com/ershoufang/109900001234.html')
                   RETURNING id"""
            ).fetchone()["id"]
            conn.execute(
                """INSERT INTO collection_discovery_states
                   (target_id,revision,seen_listing_ids,sweep_number,sweep_active,
                    sweep_seen_listing_ids,completed_sweeps)
                   VALUES (%s,4,%s::jsonb,7,TRUE,%s::jsonb,6)""",
                (target_id, json.dumps(["12345678", "87654321", "12345678"]),
                 json.dumps(["12345678", "55555555", "55555555"])),
            )
            # A legacy sweep ID can have an observation, but that observation may
            # refer to a different sweep. The other ID has no observation at all.
            conn.execute(
                """INSERT INTO collection_listing_observations
                   (target_id,source,source_listing_id,listing_url,
                    first_page_url,last_page_url,first_page_sha256,last_page_sha256,
                    first_page_storage_path,last_page_storage_path,last_seen_sweep)
                   VALUES (%s,'beike','12345678',
                    'https://nb.ke.com/ershoufang/12345678.html',
                    'https://nb.ke.com/ershoufang/','https://nb.ke.com/ershoufang/',
                    %s,%s,'/synthetic/first.gz','/synthetic/last.gz',2)""",
                (target_id, "a" * 64, "a" * 64),
            )

            conn.execute((ROOT / "sql" / "012_collection_discovery_staged_ids.sql")
                         .read_text(encoding="utf-8"))
            # Idempotent re-application must not erase the preserved set.
            migration_012 = (ROOT / "sql" / "012_collection_discovery_staged_ids.sql")
            conn.execute(migration_012.read_text(encoding="utf-8"))

        monkeypatch.setattr("app.db.DATABASE_URL", scoped_url)
        from app import collection_service

        state = collection_service.get_discovery_state(target_id)
        assert state["seen_ids_count"] == len(SEEN_IDS | SWEEP_IDS)
        assert set(state["seen_ids"]) == SEEN_IDS | SWEEP_IDS
        assert state["sweep_seen_ids_count"] == len(SWEEP_IDS)
        assert set(state["sweep_seen_ids"]) == SWEEP_IDS
        assert state["sweep_number"] == 7
        assert state["sweep_active"] is True
        # Bounded response must retain the exact counts and truncation flags.
        # A small test-only limit exercises the SQL LIMIT without creating
        # 100,000 synthetic rows in the isolated PostgreSQL database.
        monkeypatch.setattr(collection_service, "MAX_DISCOVERY_STATE_IDS", 1)
        limited = collection_service.get_discovery_state(target_id)
        assert limited["seen_ids_count"] == len(SEEN_IDS | SWEEP_IDS)
        assert len(limited["seen_ids"]) == 1
        assert limited["seen_ids_truncated"] is True
        assert limited["sweep_seen_ids_count"] == len(SWEEP_IDS)
        assert len(limited["sweep_seen_ids"]) == 1
        assert limited["sweep_seen_ids_truncated"] is True

        # The independent UTF-8 size guard must still be enforced after
        # SQL-level row limiting.
        monkeypatch.setattr(collection_service, "MAX_DISCOVERY_STATE_ID_BYTES", 2)
        byte_limited = collection_service.get_discovery_state(target_id)
        assert byte_limited["sweep_seen_ids_count"] == len(SWEEP_IDS)
        assert byte_limited["sweep_seen_ids"] == []
        assert byte_limited["sweep_seen_ids_truncated"] is True
        with connect_test_db(scoped_url) as conn:
            rows = conn.execute(
                """SELECT source_listing_id,last_seen_sweep
                   FROM collection_discovery_staged_ids
                   WHERE target_id=%s""",
                (target_id,),
            ).fetchall()
        assert {row["source_listing_id"] for row in rows} == SEEN_IDS | SWEEP_IDS
        assert {row["source_listing_id"] for row in rows
                if row["last_seen_sweep"] == 7} == SWEEP_IDS
        with connect_test_db(scoped_url) as conn:
            with pytest.raises(psycopg.errors.ForeignKeyViolation):
                with conn.transaction():
                    conn.execute(
                        """INSERT INTO collection_discovery_staged_ids
                           (target_id,source_listing_id) VALUES (%s,'77777777')""",
                        (uuid4(),),
                    )
            with pytest.raises(psycopg.errors.CheckViolation):
                with conn.transaction():
                    conn.execute(
                        """UPDATE collection_discovery_staged_ids
                           SET last_seen_sweep=-1
                           WHERE target_id=%s AND source_listing_id='55555555'""",
                        (target_id,),
                    )
    finally:
        if created:
            with connect_test_db(DATABASE_URL, autocommit=True) as conn:
                conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(
                    sql.Identifier(schema)
                ))



def test_012_failure_rolls_back_all_backfill_and_json_clearing():
    if not DATABASE_URL:
        pytest.skip("Set TEST_DATABASE_URL to run PostgreSQL integration tests")
    if conninfo_to_dict(DATABASE_URL).get("dbname") != "rehouse_test":
        pytest.fail("TEST_DATABASE_URL must point to the dedicated rehouse_test database")

    schema = "migration012_rollback_" + uuid4().hex
    created = False
    try:
        with connect_test_db(DATABASE_URL, autocommit=True) as conn:
            conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        created = True
        scoped_url = make_conninfo(DATABASE_URL, options=f"-csearch_path={schema}")
        with connect_test_db(scoped_url, autocommit=True) as conn:
            apply_pre_012_migrations(conn)
            target_id = conn.execute(
                """INSERT INTO collection_targets(source,url)
                   VALUES ('beike','https://nb.ke.com/ershoufang/109900001234.html')
                   RETURNING id"""
            ).fetchone()["id"]
            conn.execute(
                """INSERT INTO collection_discovery_states
                   (target_id,revision,seen_listing_ids,sweep_number,sweep_active,
                    sweep_seen_listing_ids,completed_sweeps)
                   VALUES (%s,4,%s::jsonb,7,TRUE,%s::jsonb,6)""",
                (target_id, json.dumps(sorted(SEEN_IDS)),
                 json.dumps(sorted(SWEEP_IDS))),
            )
            conn.execute(
                """CREATE TABLE collection_discovery_staged_ids (
                     target_id UUID NOT NULL REFERENCES collection_targets(id) ON DELETE CASCADE,
                     source_listing_id TEXT NOT NULL CHECK (source_listing_id <> '55555555'),
                     staged_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                     PRIMARY KEY (target_id,source_listing_id)
                   )"""
            )
            migration_012 = (ROOT / "sql" / "012_collection_discovery_staged_ids.sql")
            with pytest.raises(psycopg.errors.CheckViolation):
                conn.execute(migration_012.read_text(encoding="utf-8"))
            conn.execute("ROLLBACK")

            state = conn.execute(
                """SELECT seen_listing_ids,sweep_seen_listing_ids
                   FROM collection_discovery_states WHERE target_id=%s""",
                (target_id,),
            ).fetchone()
            assert set(state["seen_listing_ids"]) == SEEN_IDS
            assert set(state["sweep_seen_listing_ids"]) == SWEEP_IDS
            columns = conn.execute(
                """SELECT column_name FROM information_schema.columns
                   WHERE table_schema=%s AND table_name='collection_discovery_staged_ids'""",
                (schema,),
            ).fetchall()
            assert "last_seen_sweep" not in {row["column_name"] for row in columns}
            assert conn.execute(
                "SELECT count(*) AS total FROM collection_discovery_staged_ids"
            ).fetchone()["total"] == 0
    finally:
        if created:
            with connect_test_db(DATABASE_URL, autocommit=True) as conn:
                conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(
                    sql.Identifier(schema)
                ))
