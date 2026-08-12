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


## New Ideas -- cycle 3 (lens external)

This file's lens is **L512** in `lenses.json` (score 6/50, verdict **NO**, k=1/9). Full experiment: hypothesis `usr/lib/yubiOS/enroll-backup.sh covers all 9 primitives in the internal-big-picture basis`, method `9-D primitive binarization (purpose, examples, guidelines, constraints, verifica...`. See root `new-ideas-2026-08-12.md` for the cycle-3 summary.
