#!/usr/bin/env bash
set -euo pipefail

user="${1:-}"
[ "$user" = "root" ] || exit 0

candidates=(
  /run/credentials/@system/tmpfiles.extra
)
if [ -n "${CREDENTIALS_DIRECTORY:-}" ]; then
  candidates+=("${CREDENTIALS_DIRECTORY}/tmpfiles.extra")
fi

for credential in "${candidates[@]}"; do
  [ -r "$credential" ] || continue

  encoded_key="$(
    awk '$1 ~ /^f/ && $2 == "/root/.ssh/authorized_keys" { value=$NF } END { print value }' "$credential"
  )"
  [ -n "$encoded_key" ] || continue

  key="$(printf '%s' "$encoded_key" | base64 --decode 2>/dev/null || true)"
  case "$key" in
    ssh-*|ecdsa-*|sk-*)
      printf '%s\n' "$key"
      exit 0
      ;;
  esac
done
