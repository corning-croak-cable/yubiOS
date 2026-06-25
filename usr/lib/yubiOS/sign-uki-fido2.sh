#!/bin/bash
# SPDX-License-Identifier: LGPL-2.1-or-later
# Sign a UKI using the FIDO2-wrapped Secure Boot key.
# Usage: sign-uki-fido2.sh <image.efi>
set -euo pipefail
# shellcheck source=lib.sh
source /usr/lib/yubiOS/lib.sh

EFI="${1:-}"
[[ -z "$EFI" || ! -f "$EFI" ]] && yubiOS_die "Usage: $0 <image.efi>"

KEYDIR=/var/lib/yubiOS/fido2-sb
ENC_KEY="$KEYDIR/sb-key.pem.age"
CERT_PEM="$KEYDIR/sb-cert.pem"

[[ -f "$ENC_KEY" ]]  || yubiOS_die "No encrypted key at $ENC_KEY. Run yubiOS-enroll-sb-fido2 first."
[[ -f "$CERT_PEM" ]] || yubiOS_die "No certificate at $CERT_PEM."

TMP_KEY="$(mktemp /dev/shm/yubiOS-sb-XXXXXX.pem)"
# SC2064: use single quotes so $TMP_KEY expands at signal time, not at trap registration
trap 'shred -u "$TMP_KEY" 2>/dev/null || rm -f "$TMP_KEY"' EXIT

yubiOS_log "Decrypting signing key (touch YubiKey)..."
age -d -o "$TMP_KEY" "$ENC_KEY"

yubiOS_log "Signing $EFI..."
sbsign --key "$TMP_KEY" --cert "$CERT_PEM" --output "$EFI" "$EFI"

yubiOS_log "Signed: $EFI"
