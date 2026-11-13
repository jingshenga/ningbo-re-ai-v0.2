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
    def __init__(self, rows, unbacked_sweep_ids=0):
        self.rows = rows
        self.unbacked_sweep_ids = unbacked_sweep_ids
        self.statements = []

    @contextmanager
    def transaction(self):
        yield

    def execute(self, statement):
        self.statements.append(statement)
        if statement == "SELECT current_schema()":
            return FakeResult([("public",)])
        if "information_schema.columns" in statement:
            return FakeResult(self.rows)
        if "jsonb_array_elements_text" in statement:
            return FakeResult([(self.unbacked_sweep_ids,)])
        return FakeResult([])


def test_schema_inspection_is_read_only_and_reports_missing_objects():
    connection = FakeConnection([("collection_listing_reviews", "conclusion")])

    schema, missing_tables, missing_columns, unbacked_sweep_ids = check_schema.inspect_schema(connection)

    assert connection.statements[0] == "SET TRANSACTION READ ONLY"
    assert schema == "public"
    assert "collection_discovery_states" in missing_tables
    assert "collection_listing_reviews.conclusion" not in missing_columns
    assert "collection_listing_reviews.reviewed_at" in missing_columns
    assert unbacked_sweep_ids is None


def test_schema_inspection_accepts_complete_signature():
    rows = [
        (table, column)
        for table, columns in check_schema.EXPECTED_COLUMNS.items()
        for column in columns
    ]
    schema, missing_tables, missing_columns, unbacked_sweep_ids = check_schema.inspect_schema(
        FakeConnection(rows, unbacked_sweep_ids=2)
    )

    assert schema == "public"
    assert missing_tables == []
    assert missing_columns == []
    assert unbacked_sweep_ids == 2


def test_migrations_006_to_014_have_explicit_transaction_boundaries():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    for number in range(6, 15):
        path = next((root / "sql").glob(f"{number:03d}_*.sql"))
        migration = path.read_text(encoding="utf-8")
        assert migration.count("BEGIN;") == 1, path.name
        assert migration.count("COMMIT;") == 1, path.name
        assert migration.index("BEGIN;") < migration.index("COMMIT;"), path.name
