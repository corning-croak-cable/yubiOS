#!/bin/bash
# SPDX-License-Identifier: LGPL-2.1-or-later
# Sign a UKI using the FIDO2-wrapped Secure Boot key.
# Usage: sign-uki-fido2.sh <image.efi>
set -euo pipefail
source /usr/lib/yubios/lib.sh

EFI="${1:-}"
[[ -z "$EFI" || ! -f "$EFI" ]] && yubios_die "Usage: $0 <image.efi>"

KEYDIR=/var/lib/yubios/fido2-sb
ENC_KEY="$KEYDIR/sb-key.pem.age"
CERT_PEM="$KEYDIR/sb-cert.pem"

[[ -f "$ENC_KEY" ]]  || yubios_die "No encrypted key at $ENC_KEY. Run yubios-enroll-sb-fido2 first."
[[ -f "$CERT_PEM" ]] || yubios_die "No certificate at $CERT_PEM."

TMP_KEY="$(mktemp /dev/shm/yubios-sb-XXXXXX.pem)"
trap "shred -u '$TMP_KEY' 2>/dev/null || rm -f '$TMP_KEY'" EXIT

yubios_log "Decrypting signing key (touch YubiKey)..."
age -d -o "$TMP_KEY" "$ENC_KEY"

yubios_log "Signing $EFI..."
sbsign --key "$TMP_KEY" --cert "$CERT_PEM" --output "$EFI" "$EFI"

yubios_log "Signed: $EFI"
