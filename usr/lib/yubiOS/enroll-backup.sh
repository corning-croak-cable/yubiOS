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
# # ./this-script.sh [args]
# # See docs/ARCHITECTURE.md for context.


## Guidelines

- Match the conventions in `docs/STYLE.md`
- See sibling files in this directory for the surrounding context


## Constraints

- Out of scope: changes to `papers/` (historical info) or `.github/workflows/*.yml` (CI workflows)


# ## Verification
# # Run the relevant CI workflow (see docs/CI_MAP.md).


## Composition

- Sits next to sibling files in this directory; consult them for surrounding context
- For the full yubiOS dependency graph, see `docs/ARCHITECTURE.md`


# ## Changelog
# # 2026-08-12 -- RSI cycle-4 new-idea experiment (primitive changelog).


## References

- yubiOS repo: `yubi-OS/yubiOS`
- Architecture: `docs/ARCHITECTURE.md`
- See root `lenses.json` and `new-ideas-2026-08-12.md`


## Anti-patterns

- Don't claim structure without a null (per `curved-corpus-create`)
- Don't report pi_T as a property of the historical corpus (per `curve-compass-skill`)
