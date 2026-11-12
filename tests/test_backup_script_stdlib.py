from io import BytesIO
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys
import stat
import tarfile
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'backup.sh'


class BackupScriptTests(unittest.TestCase):
    def fake_commands(self, root):
        bin_dir = root / 'bin'
        bin_dir.mkdir()
        docker = bin_dir / 'docker'
        docker.write_text(f'''#!{sys.executable}
import os
from pathlib import Path
import subprocess
import sys

args = sys.argv[1:]
if any('pg_dump' in arg for arg in args):
    sys.stdout.buffer.write(b'fake-postgresql-custom-dump')
elif 'pg_restore' in args:
    sys.stdin.buffer.read()
elif '-c' in args:
    command = args[args.index('-c') + 1]
    raw_pages = Path(os.environ['FAKE_RAW_PAGES'])
    command = command.replace('/data/raw-pages', str(raw_pages))
    command = command.replace('-C /data raw-pages', f'-C {{raw_pages.parent}} raw-pages')
    result = subprocess.run(['sh', '-c', command], capture_output=True, check=False)
    sys.stdout.buffer.write(result.stdout)
    sys.stderr.buffer.write(result.stderr)
    raise SystemExit(result.returncode)
else:
    raise SystemExit('unexpected fake docker command')
''', encoding='utf-8')
        docker.chmod(0o700)
        sha256sum = bin_dir / 'sha256sum'
        sha256sum.write_text(f'''#!{sys.executable}
import hashlib
from pathlib import Path
import sys

for name in sys.argv[1:]:
    digest = hashlib.sha256(Path(name).read_bytes()).hexdigest()
    print(f"{{digest}}  {{name}}")
''', encoding='utf-8')
        sha256sum.chmod(0o700)
        return bin_dir

    def test_backup_script_refuses_filesystem_or_project_root_before_any_command(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bin_dir = root / 'bin'
            bin_dir.mkdir()
            log = root / 'commands.log'
            for name in ('mkdir', 'chmod', 'docker'):
                command = bin_dir / name
                command.write_text(f'''#!{sys.executable}
from pathlib import Path
import os
Path(os.environ['FAKE_COMMAND_LOG']).open('a').write(Path(__file__).name + "\\n")
raise SystemExit(17)
''', encoding='utf-8')
                command.chmod(0o700)

            outside = root / 'outside'
            (outside / 'backups').mkdir(parents=True)
            symlinked_parent = root / 'redirect'
            symlinked_parent.symlink_to(outside, target_is_directory=True)

            for backup_root in ('/', '/tmp/..', '.', './', '..',
                                str(SCRIPT.parents[1]), str(SCRIPT.parents[1].parent),
                                f'{SCRIPT.parents[1]}/..',
                                str(symlinked_parent / 'backups'),
                                str(symlinked_parent / 'new' / 'backups')):
                env = os.environ.copy()
                env.update({
                    'BACKUP_ROOT': backup_root,
                    'FAKE_COMMAND_LOG': str(log),
                    'PATH': f'{bin_dir}:{os.defpath}',
                })
                result = subprocess.run(
                    ['bash', str(SCRIPT)], cwd=SCRIPT.parents[1], env=env,
                    capture_output=True, text=True, check=False,
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertIn('Backup root', result.stderr)
                self.assertFalse(log.exists(), f'command ran for BACKUP_ROOT={backup_root}')
            self.assertFalse((outside / 'new').exists())

    def test_backup_script_rejects_project_root_alias_with_missing_component(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory).resolve() / 'project'
            project.mkdir(mode=0o755)
            backup_root = project / 'not-created' / '..'
            before_mode = stat.S_IMODE(project.stat().st_mode)
            bin_dir = self.fake_commands(Path(directory))
            env = os.environ.copy()
            env.update({
                'BACKUP_ROOT': str(backup_root),
                'FAKE_RAW_PAGES': str(project),
                'PATH': f'{bin_dir}:{os.defpath}',
            })

            result = subprocess.run(
                ['bash', str(SCRIPT)], cwd=project, env=env,
                capture_output=True, text=True, check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn('parent-directory components', result.stderr)
            self.assertEqual(stat.S_IMODE(project.stat().st_mode), before_mode)
            self.assertFalse((project / 'not-created').exists())

    def run_backup(self, root, raw_pages):
        bin_dir = self.fake_commands(root)
        backup_root = (root / 'backups').resolve()
        env = os.environ.copy()
        env.update({
            'BACKUP_ROOT': str(backup_root),
            'FAKE_RAW_PAGES': str(raw_pages),
            'PATH': f'{bin_dir}:{os.defpath}',
        })
        result = subprocess.run(
            ['bash', str(SCRIPT)], cwd=SCRIPT.parents[1], env=env,
            capture_output=True, text=True, check=False,
        )
        return result, backup_root

    def archive_command(self, raw_pages):
        source = SCRIPT.read_text(encoding='utf-8')
        match = re.search(
            r"docker compose exec -u 0 -T api sh -c \\\n\s*'([^']+)'",
            source,
        )
        self.assertIsNotNone(match, 'container-side raw-pages archive command missing')
        command = match.group(1)
        self.assertLess(command.index('test ! -L /data/raw-pages'),
                        command.index('exec tar -czf -'))
        command = command.replace('/data/raw-pages', str(raw_pages))
        command = command.replace('-C /data raw-pages', f'-C {raw_pages.parent} raw-pages')
        return command

    def test_backup_archives_real_raw_pages_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw_pages = root / 'raw-pages'
            raw_pages.mkdir()
            (raw_pages / 'evidence.html.gz').write_bytes(b'fixture')

            result = subprocess.run(
                ['sh', '-c', self.archive_command(raw_pages)],
                capture_output=True, check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
            with tarfile.open(fileobj=BytesIO(result.stdout), mode='r:gz') as archive:
                self.assertIn('raw-pages/evidence.html.gz', archive.getnames())

    def test_backup_refuses_raw_pages_symlink_before_tar(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / 'outside'
            outside.mkdir()
            (outside / 'evidence.html.gz').write_bytes(b'fixture')
            raw_pages = root / 'raw-pages'
            raw_pages.symlink_to(outside, target_is_directory=True)

            result = subprocess.run(
                ['sh', '-c', self.archive_command(raw_pages)],
                capture_output=True, check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, b'')

    def test_backup_script_publishes_verified_private_backup_set(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw_pages = root / 'raw-pages'
            raw_pages.mkdir()
            (raw_pages / 'evidence.html.gz').write_bytes(b'fixture evidence')

            result, backup_root = self.run_backup(root, raw_pages)

            self.assertEqual(result.returncode, 0, result.stderr)
            destination = Path(result.stdout.strip())
            self.assertEqual(destination.parent, backup_root)
            self.assertEqual(stat.S_IMODE(destination.stat().st_mode), 0o700)
            self.assertEqual({item.name for item in destination.iterdir()},
                             {'database.dump', 'raw-pages.tar.gz', 'SHA256SUMS'})
            for name in ('database.dump', 'raw-pages.tar.gz', 'SHA256SUMS'):
                self.assertEqual(stat.S_IMODE((destination / name).stat().st_mode), 0o600)
            self.assertEqual((destination / 'database.dump').read_bytes(),
                             b'fake-postgresql-custom-dump')
            hashes = {}
            for line in (destination / 'SHA256SUMS').read_text().splitlines():
                digest, name = line.split('  ', 1)
                hashes[name] = digest
            for name in ('database.dump', 'raw-pages.tar.gz'):
                actual = hashlib.sha256((destination / name).read_bytes()).hexdigest()
                self.assertEqual(hashes[name], actual)
            with tarfile.open(destination / 'raw-pages.tar.gz', 'r:gz') as archive:
                self.assertIn('raw-pages/evidence.html.gz', archive.getnames())
            self.assertFalse(any(item.name.startswith('.backup.') for item in backup_root.iterdir()))

    def test_backup_script_refuses_symlinked_backup_root_without_chmod_or_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / 'outside'
            outside.mkdir(mode=0o755)
            backup_root = root / 'backups'
            backup_root.symlink_to(outside, target_is_directory=True)
            raw_pages = root / 'raw-pages'
            raw_pages.mkdir()
            (raw_pages / 'evidence.html.gz').write_bytes(b'fixture evidence')
            before_mode = stat.S_IMODE(outside.stat().st_mode)

            bin_dir = self.fake_commands(root)
            env = os.environ.copy()
            env.update({
                'BACKUP_ROOT': str(backup_root),
                'FAKE_RAW_PAGES': str(raw_pages),
                'PATH': f'{bin_dir}:{os.defpath}',
            })
            result = subprocess.run(
                ['bash', str(SCRIPT)], cwd=SCRIPT.parents[1], env=env,
                capture_output=True, text=True, check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(stat.S_IMODE(outside.stat().st_mode), before_mode)
            self.assertEqual(list(outside.iterdir()), [])

    def test_backup_script_cleans_staging_and_publishes_nothing_for_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / 'outside'
            outside.mkdir()
            (outside / 'evidence.html.gz').write_bytes(b'fixture evidence')
            raw_pages = root / 'raw-pages'
            raw_pages.symlink_to(outside, target_is_directory=True)

            result, backup_root = self.run_backup(root, raw_pages)

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(backup_root.iterdir()), [])

    def test_backup_script_rejects_nested_raw_pages_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw_pages = root / 'raw-pages'
            nested = raw_pages / 'nested'
            nested.mkdir(parents=True)
            outside = root / 'outside.html.gz'
            outside.write_bytes(b'fixture evidence')
            (nested / 'evidence.html.gz').symlink_to(outside)

            result, backup_root = self.run_backup(root, raw_pages)

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(backup_root.iterdir()), [])

    def test_backup_script_rejects_fifo_in_raw_pages(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw_pages = root / 'raw-pages'
            raw_pages.mkdir()
            os.mkfifo(raw_pages / 'unexpected.pipe')

            result, backup_root = self.run_backup(root, raw_pages)

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(backup_root.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
