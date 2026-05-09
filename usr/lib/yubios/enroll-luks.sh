#!/bin/bash
# SPDX-License-Identifier: LGPL-2.1-or-later
# yubios LUKS2 disk encryption enrollment via YubiKey FIDO2
#
# Protocol: FIDO2 HMAC-secret extension via /dev/hidraw*
# systemd-cryptenroll stores the FIDO2 credential in the LUKS2 token header.
# No TPM involved. Disk is unlockable on any machine with the YubiKey.
#
# Source: https://www.freedesktop.org/software/systemd/man/latest/systemd-cryptenroll.html
# Source: https://0pointer.net/blog/unlocking-luks2-volumes-with-fido2-security-tokens.html

set -euo pipefail
source /usr/lib/yubios/lib.sh

FIDO2_DEV=$(detect_fido2_device)
yubios_log "Using FIDO2 device: $FIDO2_DEV"

# Auto-detect LUKS2 root partition
LUKS_PART="${1:-$(detect_luks2_partition)}"
[[ -z "$LUKS_PART" ]] && yubios_die "No LUKS2 partition found. Pass device path as argument."
yubios_log "LUKS2 partition: $LUKS_PART"

echo ""
echo "IMPORTANT: If this is your only key slot, generate a recovery key first:"
echo "  systemd-cryptenroll --recovery-key $LUKS_PART"
echo "Store the recovery key offline (printed paper, not on this machine)."
echo ""
read -rp "Continue with FIDO2 enrollment? [Y/n]: " confirm
[[ "${confirm:-Y}" =~ ^[Nn] ]] && exit 0

yubios_log "Enrolling FIDO2 (touch YubiKey when prompted)..."
# --fido2-with-client-pin=yes: requires FIDO2 PIN at every boot unlock
# --fido2-with-user-presence=yes: requires physical touch
# Both options verified from systemd man page (systemd >= 248)
systemd-cryptenroll \
  --fido2-device="$FIDO2_DEV" \
  --fido2-with-client-pin=yes \
  --fido2-with-user-presence=yes \
  "$LUKS_PART"

# Update /etc/crypttab for boot-time FIDO2 unlock
LUKS_NAME=$(cryptsetup status 2>/dev/null | awk '/^  type:/{p=1} p && /cipher/{print FILENAME; exit}' /proc/self/mountinfo || lsblk -no NAME "$LUKS_PART" | tail -1)
LUKS_UUID=$(cryptsetup luksUUID "$LUKS_PART")

if ! grep -q "fido2-device=auto" /etc/crypttab 2>/dev/null; then
  yubios_log "Updating /etc/crypttab..."
  # Replace existing entry or append
  if grep -q "UUID=$LUKS_UUID" /etc/crypttab 2>/dev/null; then
    sed -i "s|UUID=$LUKS_UUID.*|UUID=$LUKS_UUID none luks,fido2-device=auto,fido2-with-client-pin=1|" /etc/crypttab
  else
    echo "luks0 UUID=$LUKS_UUID none luks,fido2-device=auto,fido2-with-client-pin=1" >> /etc/crypttab
  fi
fi

# Rebuild initramfs to include fido2 dracut module
yubios_log "Rebuilding initramfs with FIDO2 module..."
dracut --force --add fido2 2>/dev/null || \
  yubios_warn "dracut failed; run manually: dracut --force --add fido2"

echo ""
echo "FIDO2 disk encryption enrolled."
echo "On next boot: touch YubiKey when prompted, enter FIDO2 PIN."
echo ""
echo "To remove passphrase slot (only after confirming FIDO2 works):"
echo "  systemd-cryptenroll --wipe-slot=password $LUKS_PART"
