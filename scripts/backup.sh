#!/usr/bin/env bash
set -euo pipefail
umask 077

backup_root=${BACKUP_ROOT:-./backups}
while [[ $backup_root != / && $backup_root == */ ]]; do
  backup_root=${backup_root%/}
done
case "/$backup_root/" in
  */../*)
    printf 'Backup root must not contain parent-directory components\n' >&2
    exit 1
    ;;
esac
[[ ! -L $backup_root ]] || { printf 'Backup root must not be a symlink\n' >&2; exit 1; }
path_probe=$backup_root
while [[ ! -d $path_probe ]]; do
  if [[ $path_probe == */* ]]; then
    path_probe=${path_probe%/*}
    [[ -n $path_probe ]] || path_probe=/
  else
    path_probe=.
  fi
done
logical_path=$(cd -L -- "$path_probe" && pwd -L)
physical_path=$(cd -P -- "$path_probe" && pwd -P)
[[ $logical_path == "$physical_path" ]] || {
  printf 'Backup root path must not contain symlinked directories\n' >&2
  exit 1
}
[[ $backup_root != / && $backup_root != . && $backup_root != .. ]] || {
  printf 'Backup root must be a dedicated directory\n' >&2
  exit 1
}
if [[ -d $backup_root ]]; then
  current_dir=$(pwd -P)
  resolved_backup_root=$(cd -- "$backup_root" && pwd -P)
  if [[ $resolved_backup_root == / ]]; then
    printf 'Backup root must be a dedicated directory\n' >&2
    exit 1
  fi
  case "$current_dir/" in
    "$resolved_backup_root/"*)
      printf 'Backup root must not contain the project working directory\n' >&2
      exit 1
      ;;
  esac
fi
mkdir -p "$backup_root"
chmod 700 "$backup_root"

stamp=$(date -u +%Y%m%dT%H%M%SZ)
destination="$backup_root/ningbo-re-ai-$stamp-$$"
[[ ! -e $destination ]] || { printf 'Backup destination already exists\n' >&2; exit 1; }
temporary=$(mktemp -d "$backup_root/.backup.XXXXXX")
cleanup() {
  if [[ -n ${temporary:-} && -d $temporary ]]; then
    rm -rf -- "$temporary"
  fi
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

docker compose exec -T db sh -c \
  'pg_dump --no-owner --no-privileges --format=custom -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  > "$temporary/database.dump"
test -s "$temporary/database.dump"
docker compose exec -T db pg_restore --list < "$temporary/database.dump" > /dev/null
docker compose exec -u 0 -T api sh -c \
  'test -d /data/raw-pages && test ! -L /data/raw-pages && unsupported=$(find /data/raw-pages ! -type d ! -type f -print -quit) && test -z "$unsupported" && exec tar -czf - -C /data raw-pages' \
  > "$temporary/raw-pages.tar.gz"
tar -tzf "$temporary/raw-pages.tar.gz" > /dev/null
(cd "$temporary" && sha256sum database.dump raw-pages.tar.gz > SHA256SUMS)
chmod 600 "$temporary"/*
mv -- "$temporary" "$destination"
temporary=
trap - EXIT HUP INT TERM
printf '%s\n' "$destination"
