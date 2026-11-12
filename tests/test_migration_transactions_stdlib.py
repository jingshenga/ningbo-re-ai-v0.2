import re
from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class MigrationTransactionTests(unittest.TestCase):
    def test_initialization_and_migrations_manage_their_own_transaction(self):
        for name in (
            '001_init.sql',
            '002_collection_pipeline.sql',
            '003_collection_health_indexes.sql',
            '004_collection_health_metrics.sql',
            '005_saved_search_filters.sql',
            '006_collection_discovery_state.sql',
            '007_collection_listing_observations.sql',
            '008_collection_discovery_sweeps.sql',
            '009_collection_listing_reviews.sql',
            '010_collection_parse_metrics.sql',
            '011_parse_attempts_append_only.sql',
            '012_collection_discovery_staged_ids.sql',
            '013_account_history_backfill_cursor.sql',
            '014_collection_detail_queue.sql',
        ):
            sql = (PROJECT_ROOT / 'sql' / name).read_text(encoding='utf-8')
            statements = re.sub(r'--[^\n]*', '', sql).strip()

            with self.subTest(migration=name):
                self.assertRegex(statements, r'^BEGIN\s*;')
                self.assertRegex(statements, r'COMMIT\s*;\s*$')
                self.assertEqual(
                    len(re.findall(r'^BEGIN\s*;$', statements,
                                   re.IGNORECASE | re.MULTILINE)), 1)
                self.assertEqual(
                    len(re.findall(r'^COMMIT\s*;$', statements,
                                   re.IGNORECASE | re.MULTILINE)), 1)

    def test_deployment_commands_do_not_wrap_file_transactions(self):
        instructions = (PROJECT_ROOT / 'docs' / 'NAS_DEPLOYMENT.md').read_text(
            encoding='utf-8')
        commands = [line for line in instructions.splitlines()
                    if line.startswith('docker compose exec')]

        self.assertFalse(any('psql --single-transaction' in line for line in commands))
        self.assertIn('不要再添加`psql --single-transaction`', instructions)

    def test_compose_initializes_all_sql_files_in_migration_order(self):
        compose = (PROJECT_ROOT / 'docker-compose.yml').read_text(encoding='utf-8')
        expected = (
            '001_init.sql',
            '002_collection_pipeline.sql',
            '003_collection_health_indexes.sql',
            '004_collection_health_metrics.sql',
            '005_saved_search_filters.sql',
            '006_collection_discovery_state.sql',
            '007_collection_listing_observations.sql',
            '008_collection_discovery_sweeps.sql',
            '009_collection_listing_reviews.sql',
            '010_collection_parse_metrics.sql',
            '011_parse_attempts_append_only.sql',
            '012_collection_discovery_staged_ids.sql',
            '013_account_history_backfill_cursor.sql',
            '014_collection_detail_queue.sql',
        )
        positions = [compose.index(f'./sql/{name}:/docker-entrypoint-initdb.d/{name}')
                     for name in expected]
        self.assertEqual(positions, sorted(positions))


if __name__ == '__main__':
    unittest.main()
