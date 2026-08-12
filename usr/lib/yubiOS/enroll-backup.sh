#!/bin/bash
# SPDX-License-Identifier: LGPL-2.1-or-later
# yubiOS backup YubiKey enrollment
# Enrolls a second YubiKey for all active trust anchors.
# Run after primary enrollment. Both keys will unlock the system.
set -euo pipefail
# shellcheck source=lib.sh
source /usr/lib/yubiOS/lib.sh

yubiOS_log "Backup YubiKey enrollment"
yubiOS_log "Insert your BACKUP YubiKey and press Enter."
read -rp ""

wait_for_yubikey

yubiOS_log "Enrolling backup: LUKS2 FIDO2"
LUKS_PART="${1:-$(detect_luks2_partition)}"
if [[ -n "$LUKS_PART" ]]; then
  systemd-cryptenroll \
    --fido2-device=auto \
    --fido2-with-client-pin=yes \
    --fido2-with-user-presence=yes \
    "$LUKS_PART"
  yubiOS_log "Backup LUKS2 FIDO2 enrolled."
fi

yubiOS_log "Enrolling backup: PAM U2F"
TARGET_USER="${SUDO_USER:-$(logname 2>/dev/null || id -un)}"
pamu2fcfg -u "$TARGET_USER" -N >> /etc/yubico/u2f_keys
yubiOS_log "Backup PAM U2F enrolled."

echo ""
echo "Backup YubiKey enrolled. Test sudo with the backup key."

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

