"""Create a verified source-only development ZIP and refresh MANIFEST.sha256."""
import argparse
import hashlib
from pathlib import Path
import zipfile


EXCLUDED_DIRS = {
    '.git', '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache',
    '.venv', 'venv', 'backups', '.aws', '.ssh', '.secrets', 'secrets',
    '.credentials', 'credentials', 'private', 'certs', 'certificates', 'logs',
}
EXCLUDED_SUFFIXES = {
    '.zip', '.pyc', '.pyo', '.log', '.dump', '.backup', '.db',
    '.pem', '.key', '.p12', '.pfx', '.jks', '.keystore',
}
EXCLUDED_FILENAMES = {
    '.env', '.envrc', '.npmrc', '.netrc', '.pypirc', 'credentials',
    'credentials.json', 'secret', 'secret.json', 'secrets.json', 'token', 'token.json',
    'service-account.json',
    'authorized_keys', 'id_rsa', 'id_ed25519', 'id_ecdsa', 'id_dsa',
}


def source_files(root: Path) -> list[Path]:
    files = []
    for path in root.rglob('*'):
        if path.is_symlink():
            continue
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in EXCLUDED_DIRS for part in relative.parts):
            continue
        if path.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        if relative.name in EXCLUDED_FILENAMES or (relative.name.startswith('.env.') and relative.name != '.env.example'):
            continue
        if relative.parts[0] == 'data' and relative.name != '.gitkeep':
            continue
        if relative.as_posix() == 'MANIFEST.sha256':
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(root).as_posix())


def write_manifest(root: Path, files: list[Path]) -> str:
    content = ''.join(
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(root).as_posix()}\n"
        for path in files
    )
    (root / 'MANIFEST.sha256').write_text(content, encoding='utf-8')
    return content


def build_package(root: Path, output: Path) -> tuple[int, str]:
    root = root.resolve()
    output = output.resolve()
    if output.is_relative_to(root):
        raise ValueError('output ZIP must be outside the project directory')
    files = source_files(root)
    manifest = write_manifest(root, files)
    files.append(root / 'MANIFEST.sha256')
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            archive.write(path, Path(root.name) / path.relative_to(root))

    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise ValueError('ZIP integrity check failed')
        members = {name[len(root.name) + 1:]: name
                   for name in archive.namelist() if name.startswith(root.name + '/')}
        for line in manifest.splitlines():
            digest, relative = line.split('  ', 1)
            if relative not in members or hashlib.sha256(archive.read(members[relative])).hexdigest() != digest:
                raise ValueError(f'ZIP hash mismatch: {relative}')
        if len(members) != len(files) or any(name.endswith('/.env') for name in members):
            raise ValueError('ZIP contains missing or forbidden project files')

    return len(files) - 1, hashlib.sha256(output.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path, help='ZIP destination outside project directory')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    count, digest = build_package(root, args.output)
    print(f'files={count} zip={args.output.resolve()} sha256={digest}')


if __name__ == '__main__':
    main()
