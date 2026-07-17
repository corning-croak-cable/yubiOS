#!/usr/bin/env bash
set -euo pipefail

user="${1:-}"
[ "$user" = "root" ] || exit 0

emit_key() {
  local key="$1"
  case "$key" in
    ssh-*|ecdsa-*|sk-*)
      printf '%s\n' "$key"
      return 0
      ;;
  esac
  return 1
}

# systemd's well-known root SSH credential is raw authorized_keys content.
# CI can inject it via SMBIOS as io.systemd.credential.binary:ssh.authorized_keys.root=...
raw_candidates=(
  /run/credentials/@system/ssh.authorized_keys.root
)
if [ -n "${CREDENTIALS_DIRECTORY:-}" ]; then
  raw_candidates+=("${CREDENTIALS_DIRECTORY}/ssh.authorized_keys.root")
fi

found=0
for credential in "${raw_candidates[@]}"; do
  [ -r "$credential" ] || continue
  while IFS= read -r key || [ -n "$key" ]; do
    if emit_key "$key"; then
      found=1
    fi
  done < "$credential"
done
[ "$found" -eq 0 ] || exit 0

# Older bcvk builds pass a tmpfiles.extra credential whose final field is the
# base64-encoded public key for /root/.ssh/authorized_keys.
tmpfiles_candidates=(
  /run/credentials/@system/tmpfiles.extra
)
if [ -n "${CREDENTIALS_DIRECTORY:-}" ]; then
  tmpfiles_candidates+=("${CREDENTIALS_DIRECTORY}/tmpfiles.extra")
fi

for credential in "${tmpfiles_candidates[@]}"; do
  [ -r "$credential" ] || continue

  encoded_key="$(
    awk '$1 ~ /^f/ && $2 == "/root/.ssh/authorized_keys" { value=$NF } END { print value }' "$credential"
  )"
  [ -n "$encoded_key" ] || continue

  key="$(printf '%s' "$encoded_key" | base64 --decode 2>/dev/null || true)"
  emit_key "$key" && exit 0
done
