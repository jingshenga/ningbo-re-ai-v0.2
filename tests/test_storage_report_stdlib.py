import gzip
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.storage_report import invalid_evidence_files


class EvidenceIntegrityTests(unittest.TestCase):
    def write_evidence(self, root: Path, content: bytes, name_digest: str | None = None) -> Path:
        digest = name_digest or hashlib.sha256(content).hexdigest()
        path = root / f'{digest}.html.gz'
        with gzip.open(path, 'wb') as compressed:
            compressed.write(content)
        return path

    def test_integrity_check_accepts_content_addressed_gzip(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_evidence(root, b'<html>synthetic evidence</html>')

            self.assertEqual(invalid_evidence_files(root), [])

    def test_integrity_check_reports_hash_mismatch_and_invalid_gzip(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mismatch = self.write_evidence(root, b'changed evidence', 'a' * 64)
            broken = root / f"{'b' * 64}.html.gz"
            broken.write_bytes(b'not a gzip stream')

            self.assertEqual(invalid_evidence_files(root), [mismatch, broken])

    def test_integrity_check_ignores_symlinks_and_unrelated_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root.parent / f'{root.name}-external-evidence.tmp'
            outside.write_bytes(b'not evidence')
            try:
                (root / f"{'c' * 64}.html.gz").symlink_to(outside)
                (root / 'notes.txt').write_text('not evidence', encoding='utf-8')

                self.assertEqual(invalid_evidence_files(root), [])
            finally:
                outside.unlink(missing_ok=True)

    def test_integrity_check_propagates_read_permission_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_evidence(root, b'<html>synthetic evidence</html>')

            with patch.object(Path, 'open', side_effect=PermissionError('permission denied')):
                with self.assertRaisesRegex(PermissionError, 'permission denied'):
                    invalid_evidence_files(root)


if __name__ == '__main__':
    unittest.main()
