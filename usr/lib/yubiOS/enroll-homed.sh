#!/bin/bash
# SPDX-License-Identifier: LGPL-2.1-or-later
# yubiOS homed enrollment: create a LUKS2+btrfs home with FIDO2 YubiKey auth.
#
# Creates a systemd-homed managed home for the given user:
#   - LUKS2 encrypted loopback file in /home/<user>.home
#   - btrfs filesystem inside the LUKS2 volume
#   - FIDO2 (hmac-secret) primary auth via YubiKey (PIN + touch required)
#   - Recovery key printed to stdout — store offline before removing passphrase
#
# Usage: yubiOS-enroll-homed <username> [--disk-size=SIZE] [--member-of=GROUP,...]
#
# Source: https://www.man7.org/linux/man-pages/man1/homectl.1.html
# Source: https://systemd.io/HOME_DIRECTORY

set -euo pipefail
# shellcheck source=lib.sh
source /usr/lib/yubiOS/lib.sh

USERNAME="${1:-}"
[[ -z "$USERNAME" ]] && yubiOS_die "Usage: $0 <username> [--disk-size=SIZE] [--member-of=GROUPS]"
shift

DISK_SIZE="20G"
MEMBER_OF="wheel"

for arg in "$@"; do
  case "$arg" in
    --disk-size=*) DISK_SIZE="${arg#*=}" ;;
    --member-of=*) MEMBER_OF="${arg#*=}" ;;
    *) yubiOS_die "Unknown option: $arg" ;;
  esac
done

wait_for_yubikey
check_pam_u2f_version

yubiOS_log "Creating homed home for $USERNAME"
yubiOS_log "  Storage : luks (LUKS2 loopback, /home/$USERNAME.home)"
yubiOS_log "  FS      : btrfs"
yubiOS_log "  Size    : $DISK_SIZE"
yubiOS_log "  Groups  : $MEMBER_OF"
yubiOS_log ""
yubiOS_log "A recovery key will be printed. Write it down and store offline."
yubiOS_log "Do NOT continue until the recovery key is safely stored."
echo ""
read -rp "Ready? [y/N]: " confirm
[[  "${confirm,,}" == "y" ]] || { yubiOS_log "Aborted."; exit 0; }

# Create home with recovery key + FIDO2 in one shot.
# --fido2-with-client-pin=yes  : FIDO2 PIN required at every unlock
# --fido2-with-user-presence=yes : physical touch required
# Source: homectl(1) --fido2-with-client-pin, --fido2-with-user-presence
homectl create "$USERNAME" \
  --storage=luks \
  --fs-type=btrfs \
  --disk-size="$DISK_SIZE" \
  --member-of="$MEMBER_OF" \
  --recovery-key \
  --fido2-device=auto \
  --fido2-with-client-pin=yes \
  --fido2-with-user-presence=yes

yubiOS_log ""
yubiOS_log "Home created for $USERNAME."
yubiOS_log "Inspect : homectl inspect $USERNAME --json=pretty"
yubiOS_log "Lock    : homectl lock $USERNAME"
yubiOS_log "Migrate : homectl inspect $USERNAME -EE | ssh root@target homectl create -i-"


## New Ideas -- cycle 3 (lens external)

This file's lens is **L515** in `lenses.json` (score 6/50, verdict **NO**, k=1/9). Full experiment: hypothesis `usr/lib/yubiOS/enroll-homed.sh covers all 9 primitives in the internal-big-picture basis`, method `9-D primitive binarization (purpose, examples, guidelines, constraints, verifica...`. See root `new-ideas-2026-08-12.md` for the cycle-3 summary.
