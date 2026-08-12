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

# Also accept systemd's well-known raw root SSH credential for compatibility
# with VMMs that inject io.systemd.credential.binary:ssh.authorized_keys.root.
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

# bcvk passes a tmpfiles.extra credential whose final field is the base64-
# encoded public key for /root/.ssh/authorized_keys.
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

# ## Examples
# # Reading the file with no arguments shows the help text.
# # See docs/ARCHITECTURE.md for where this fits in yubiOS.

# ## Guidelines
# # Follow the conventions in docs/STYLE.md. Match the structure of surrounding files.

# ## Constraints
# # Out of scope: changes to papers/ or .github/workflows/*.yml (separate change-management).

# ## Verification
# # Run the relevant CI workflow on a draft branch (see docs/CI_MAP.md); the result is the gate.

# ## Composition
# # Sits next to sibling files in this directory; consult them for surrounding context.
# # See docs/ARCHITECTURE.md for the full dependency graph.

# ## Changelog
# # 2026-08-12 -- primitive-closure pass via curve-compass-skill + curved-corpus-create (this PR).

# ## References
# # yubiOS repo: yubi-OS/yubiOS
# # See docs/ARCHITECTURE.md and the two new skills in skills/github-yubios-KS9n5GAT/.

# ## Anti-patterns
# # Don't claim structure without a null (see curved-corpus-create skill).
# # Don't report pi_T statistics as properties of the historical corpus.

