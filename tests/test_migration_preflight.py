from contextlib import contextmanager

from scripts import check_schema


class FakeResult:
    def __init__(self, rows):
        self.rows = rows

    def fetchone(self):
        return self.rows[0]

    def fetchall(self):
        return self.rows


class FakeConnection:
    def __init__(self, columns, functions=(), triggers=(), constraints=(), unbacked_sweep_ids=0):
        self.columns = columns
        self.functions = functions
        self.triggers = triggers
        self.constraints = constraints
        self.unbacked_sweep_ids = unbacked_sweep_ids
        self.statements = []

    @contextmanager
    def transaction(self):
        yield

    def execute(self, statement, params=None):
        self.statements.append(statement)
        if statement == "SELECT current_schema()":
            return FakeResult([("public",)])
        if "information_schema.columns" in statement:
            return FakeResult(self.columns)
        if "FROM pg_proc" in statement:
            return FakeResult([(name,) for name in self.functions])
        if "FROM pg_trigger" in statement:
            return FakeResult(self.triggers)
        if "FROM pg_constraint" in statement:
            return FakeResult(self.constraints)
        if "jsonb_array_elements_text" in statement:
            return FakeResult([(self.unbacked_sweep_ids,)])
        return FakeResult([])


def complete_columns():
    rows = [
        (table, column)
        for table, columns in check_schema.EXPECTED_COLUMNS.items()
        for column in columns
    ]
    rows.extend([
        ("collection_discovery_states", "target_id"),
        ("collection_discovery_states", "sweep_number"),
        ("collection_discovery_states", "sweep_seen_listing_ids"),
        ("collection_targets", "id"),
        ("collection_targets", "source"),
        ("collection_listing_observations", "target_id"),
        ("collection_listing_observations", "source"),
        ("collection_listing_observations", "source_listing_id"),
        ("collection_listing_observations", "last_seen_sweep"),
    ])
    return rows


def complete_functions():
    return check_schema.EXPECTED_FUNCTIONS


def complete_constraints(missing=()):
    rows = [
        (name, "collection_listing_reviews", "CHECK (review_status IS NOT NULL)")
        for name in check_schema.EXPECTED_CONSTRAINTS - set(missing)
    ]
    rows.extend([
        ("source_listing_id_check", table, "CHECK (source_listing_id ~ '[0-9]+' AND source IN ('beike', 'anjuke') AND length(source_listing_id) BETWEEN 8 AND 220 OR length(source_listing_id) BETWEEN 7 AND 220)")
        for table in check_schema.EXPECTED_CHECK_DEFINITIONS
    ])
    return rows


def complete_triggers():
    return [
        (name, table, function)
        for name, (table, function) in check_schema.EXPECTED_TRIGGERS.items()
    ]


def test_schema_inspection_is_read_only_and_reports_missing_objects():
    connection = FakeConnection([("collection_listing_reviews", "conclusion")])

    result = check_schema.inspect_schema(connection)

    assert connection.statements[0] == "SET TRANSACTION READ ONLY"
    schema, missing_tables, missing_columns, missing_functions, missing_triggers, missing_constraints, unbacked = result
    assert schema == "public"
    assert "collection_discovery_states" in missing_tables
    assert "collection_listing_reviews.conclusion" not in missing_columns
    assert "collection_listing_reviews.reviewed_at" in missing_columns
    assert missing_functions == sorted(check_schema.EXPECTED_FUNCTIONS)
    assert len(missing_triggers) == 3
    expected_missing = sorted(
        check_schema.EXPECTED_CONSTRAINTS
        | {definition[0] for definition in check_schema.EXPECTED_CHECK_DEFINITIONS.values()}
    )
    assert missing_constraints == expected_missing
    assert unbacked is None


def test_schema_inspection_checks_append_only_triggers_and_constraints():
    connection = FakeConnection(
        complete_columns(),
        functions={"maintain_collection_parse_metrics"},
        triggers=[("collection_parse_attempt_metrics_trigger", "collection_parse_attempts", "maintain_collection_parse_metrics")],
        constraints=complete_constraints({"collection_listing_observations_review_status_check"}),
        unbacked_sweep_ids=2,
    )

    result = check_schema.inspect_schema(connection)

    _, missing_tables, missing_columns, missing_functions, missing_triggers, missing_constraints, unbacked = result
    assert missing_tables == []
    assert missing_columns == []
    assert missing_functions == ["reject_collection_parse_attempt_mutation"]
    assert missing_triggers == [
        "collection_parse_attempts_no_truncate on collection_parse_attempts",
        "collection_parse_attempts_no_update_delete on collection_parse_attempts",
    ]
    assert missing_constraints == ["collection_listing_observations_review_status_check"]
    assert unbacked == 2


def test_schema_inspection_accepts_complete_critical_signature():
    connection = FakeConnection(
        complete_columns(),
        functions=complete_functions(),
        triggers=complete_triggers(),
        constraints=complete_constraints(),
        unbacked_sweep_ids=0,
    )

    result = check_schema.inspect_schema(connection)

    _, missing_tables, missing_columns, missing_functions, missing_triggers, missing_constraints, unbacked = result
    assert missing_tables == []
    assert missing_columns == []
    assert missing_functions == []
    assert missing_triggers == []
    assert missing_constraints == []
    assert unbacked == 0


def test_migrations_006_to_014_have_explicit_transaction_boundaries():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    for number in range(6, 15):
        path = next((root / "sql").glob(f"{number:03d}_*.sql"))
        migration = path.read_text(encoding="utf-8")
        assert migration.count("BEGIN;") == 1, path.name
        assert migration.count("COMMIT;") == 1, path.name
        assert migration.index("BEGIN;") < migration.index("COMMIT;"), path.name
