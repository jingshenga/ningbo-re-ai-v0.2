#!/usr/bin/env python3
"""Read-only check for schema objects introduced by migrations 006-014."""
import argparse
import os
import sys

import psycopg
from psycopg.conninfo import conninfo_to_dict


EXPECTED_COLUMNS = {
    "collection_discovery_states": {
        "target_id", "revision", "version", "seen_listing_ids", "last_page_url",
        "next_page_url", "visited_page_urls", "last_attempted_page_url",
        "last_error_type", "failed_attempts", "sweep_number", "sweep_active",
        "sweep_seen_listing_ids", "completed_sweeps",
    },
    "collection_listing_observations": {
        "target_id", "source", "source_listing_id", "first_seen_at", "last_seen_at",
        "first_page_sha256", "last_page_sha256", "last_seen_sweep",
        "missed_complete_scans", "review_status",
    },
    "collection_listing_reviews": {
        "id", "target_id", "source", "source_listing_id", "conclusion",
        "note", "reviewed_at",
    },
    "collection_health_metrics": {
        "source", "parse_attempt_count", "parse_success_count", "complete_field_count",
    },
    "collection_parse_attempts": {
        "id", "source", "capture_method", "parser_version", "parse_status",
        "required_fields_complete", "attempted_at",
    },
    "collection_discovery_staged_ids": {"target_id", "source_listing_id", "staged_at"},
    "monitored_accounts": {"history_backfill_cursor", "history_backfill_cutoff"},
    "collection_discovery_detail_queue": {
        "target_id", "source", "source_listing_id", "listing_url",
        "discovered_page_url", "attempt_count", "last_error_type",
    },
}


def inspect_schema(conn):
    """Return missing migration objects using a read-only transaction."""
    with conn.transaction():
        conn.execute("SET TRANSACTION READ ONLY")
        schema = conn.execute("SELECT current_schema()").fetchone()[0]
        rows = conn.execute(
            """SELECT table_name, column_name
               FROM information_schema.columns
               WHERE table_schema = current_schema()"""
        ).fetchall()
        actual = {}
        for table_name, column_name in rows:
            actual.setdefault(table_name, set()).add(column_name)
        prerequisites = {
            "collection_discovery_states": {"target_id", "sweep_number", "sweep_seen_listing_ids"},
            "collection_targets": {"id", "source"},
            "collection_listing_observations": {
                "target_id", "source", "source_listing_id", "last_seen_sweep",
            },
        }
        if all(columns <= actual.get(table, set()) for table, columns in prerequisites.items()):
            unbacked_sweep_ids = conn.execute(
                """SELECT count(*)
                   FROM collection_discovery_states AS state
                   JOIN collection_targets AS target ON target.id = state.target_id
                   CROSS JOIN LATERAL jsonb_array_elements_text(
                       state.sweep_seen_listing_ids
                   ) AS item(source_listing_id)
                   LEFT JOIN collection_listing_observations AS observation
                     ON observation.target_id = state.target_id
                    AND observation.source = target.source
                    AND observation.source_listing_id = item.source_listing_id
                    AND observation.last_seen_sweep = state.sweep_number
                   WHERE observation.target_id IS NULL"""
            ).fetchone()[0]
        else:
            unbacked_sweep_ids = None

    missing_tables = sorted(set(EXPECTED_COLUMNS) - set(actual))
    missing_columns = sorted(
        f"{table}.{column}"
        for table, columns in EXPECTED_COLUMNS.items()
        for column in columns - actual.get(table, set())
    )
    return schema, missing_tables, missing_columns, unbacked_sweep_ids


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allow-non-test-database",
        action="store_true",
        help="allow a database other than rehouse_test (use only with explicit read access approval)",
    )
    args = parser.parse_args()
    dsn = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not dsn:
        parser.error("set TEST_DATABASE_URL or DATABASE_URL")
    database = conninfo_to_dict(dsn).get("dbname")
    if database != "rehouse_test" and not args.allow_non_test_database:
        parser.error("refusing non-rehouse_test database; pass --allow-non-test-database only when authorized")

    try:
        with psycopg.connect(dsn) as conn:
            schema, missing_tables, missing_columns, unbacked_sweep_ids = inspect_schema(conn)
    except psycopg.Error:
        print("schema check failed; connection details redacted", file=sys.stderr)
        return 2

    print(f"Read-only schema check: database={database}, schema={schema}")
    if unbacked_sweep_ids is not None:
        print(f"Unbacked active-sweep IDs (review before migration 012): {unbacked_sweep_ids}")
    if missing_tables or missing_columns or unbacked_sweep_ids:
        if missing_tables:
            print("Missing tables: " + ", ".join(missing_tables))
        if missing_columns:
            print("Missing columns: " + ", ".join(missing_columns))
        return 1
    print("Migration 006-014 signature objects are present.")
    if unbacked_sweep_ids is None:
        print("Sweep-ID consistency check unavailable until migrations 006-008 are present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
