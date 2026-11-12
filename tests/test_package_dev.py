from pathlib import Path
import zipfile

import pytest

from scripts.package_dev import build_package


def test_package_excludes_secrets_runtime_data_and_archives(tmp_path):
    root = tmp_path / 'project'
    (root / 'app').mkdir(parents=True)
    (root / 'data' / 'raw-pages').mkdir(parents=True)
    (root / 'backups').mkdir()
    (root / '.pytest_cache').mkdir()
    (root / 'app' / 'main.py').write_text('source', encoding='utf-8')
    (root / '.env').write_text('secret', encoding='utf-8')
    (root / '.env.example').write_text('placeholder', encoding='utf-8')
    (root / 'data' / 'raw-pages' / '.gitkeep').write_text('', encoding='utf-8')
    (root / 'data' / 'raw-pages' / 'private.html').write_text('private', encoding='utf-8')
    (root / 'backups' / 'db.dump').write_text('backup', encoding='utf-8')
    (root / '.pytest_cache' / 'cache').write_text('cache', encoding='utf-8')
    (root / 'old.zip').write_bytes(b'old archive')
    output = tmp_path / 'delivery.zip'

    count, _ = build_package(root, output)

    assert count == 3
    with zipfile.ZipFile(output) as archive:
        names = set(archive.namelist())
        assert names == {
            'project/app/main.py',
            'project/.env.example',
            'project/data/raw-pages/.gitkeep',
            'project/MANIFEST.sha256',
        }
        assert archive.testzip() is None


def test_package_rejects_output_inside_project(tmp_path):
    root = tmp_path / 'project'
    root.mkdir()

    with pytest.raises(ValueError, match='outside the project'):
        build_package(root, root / 'delivery.zip')


def test_package_excludes_symlinked_secrets_and_credential_files(tmp_path):
    root = tmp_path / 'project'
    (root / 'app').mkdir(parents=True)
    (root / '.aws').mkdir()
    (root / 'app' / 'main.py').write_text('source', encoding='utf-8')
    (root / 'app' / 'private-key.pem').write_text('private key', encoding='utf-8')
    (root / '.aws' / 'credentials').write_text('cloud secret', encoding='utf-8')
    (root / 'credentials').write_text('root secret', encoding='utf-8')
    (root / '.netrc').write_text('machine secret', encoding='utf-8')
    outside_secret = tmp_path / 'outside-secret.txt'
    outside_secret.write_text('linked secret', encoding='utf-8')
    (root / 'app' / 'linked-secret.py').symlink_to(outside_secret)
    output = tmp_path / 'delivery.zip'

    count, _ = build_package(root, output)

    assert count == 1
    with zipfile.ZipFile(output) as archive:
        assert set(archive.namelist()) == {'project/app/main.py', 'project/MANIFEST.sha256'}
