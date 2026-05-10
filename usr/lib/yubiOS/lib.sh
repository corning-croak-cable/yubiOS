#!/bin/bash
# SPDX-License-Identifier: LGPL-2.1-or-later
# yubiOS shared library: detection, logging, gating functions

YUBIOS_STATE_DIR=/var/lib/yubiOS
YUBICOS_U2F_KEYS=/etc/yubico/u2f_keys
YUBIOS_PIV_SLOT=9c   # Digital Signature slot for Secure Boot
YUBIOS_PKCS11_LIB=/usr/lib64/libykcs11.so

yubiOS_log() { echo "[yubiOS] $*"; }
yubiOS_warn() { echo "[yubiOS WARN] $*" >&2; }
yubiOS_die() { echo "[yubiOS ERROR] $*" >&2; exit 1; }

# Detect first available FIDO2 device via libfido2
# Source: fido2-token -L lists hidraw paths
# Source: https://github.com/Yubico/libfido2
detect_fido2_device() {
  local dev
  dev=$(fido2-token -L 2>/dev/null | awk -F: 'NR==1{print $1}' | tr -d ' ')
  if [[ -z "$dev" ]]; then
    yubiOS_die "No FIDO2 device found. Plug in your YubiKey and try again."
  fi
  echo "$dev"
}

# Wait for YubiKey to appear on hidraw
wait_for_yubikey() {
  yubiOS_log "Waiting for YubiKey... (plug it in now)"
  local attempts=0
  while ! fido2-token -L 2>/dev/null | grep -q /dev/hidraw; do
    sleep 1
    attempts=$((attempts+1))
    [[ $attempts -gt 30 ]] && yubiOS_die "Timed out waiting for YubiKey."
  done
  yubiOS_log "YubiKey detected."
}

# Verify pam-u2f version >= 1.3.1 (CVE-2025-23013 fix)
# Source: https://www.yubico.com/support/security-advisories/ysa-2025-01/
check_pam_u2f_version() {
  local ver
  ver=$(rpm -q pam-u2f --queryformat '%{VERSION}' 2>/dev/null || \
       dpkg-query -W -f='${Version}' pam-u2f 2>/dev/null || echo 0)
  # Require >= 1.3.1
  if [[ "$(printf '%s\n%s' "1.3.1" "$ver" | sort -V | head -1)" != "1.3.1" ]]; then
    yubiOS_die "pam-u2f version $ver is < 1.3.1. Update before enrolling (CVE-2025-23013)."
  fi
}

# Detect root LUKS2 partition
detect_luks2_partition() {
  lsblk -J -o NAME,FSTYPE,MOUNTPOINT 2>/dev/null | \
    python3 -c "
import sys,json
d=json.load(sys.stdin)
def find(devs):
    for b in devs:
        if b.get("fstype") == "crypto_LUKS" and b.get("mountpoint") in (None, ""):
            print("/dev/" + b["name"])
            return
        find(b.get("children", []))
find(d["blockdevices"])
"
}
