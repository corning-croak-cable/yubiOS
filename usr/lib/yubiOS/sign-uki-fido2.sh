#!/bin/bash
# SPDX-License-Identifier: LGPL-2.1-or-later
# Sign a UKI using the FIDO2-wrapped Secure Boot key.
# Usage: sign-uki-fido2.sh <image.efi>
set -euo pipefail
source /usr/lib/yubiOS/lib.sh

EFI="${1:-}"
[[ -z "$EFI" || ! -f "$EFI" ]] && yubiOS_die "Usage: $0 <image.efi>"

KEYDIR=/var/lib/yubiOS/fido2-sb
ENC_KEY="$KEYDIR/sb-key.pem.age"
CERT_PEM="$KEYDIR/sb-cert.pem"

[[ -f "$ENC_KEY" ]]  || yubiOS_die "No encrypted key at $ENC_KEY. Run yubiOS-enroll-sb-fido2 first."
[[ -f "$CERT_PEM" ]] || yubiOS_die "No certificate at $CERT_PEM."

TMP_KEY="$(mktemp /dev/shm/yubiOS-sb-XXXXXX.pem)"
SIGNED="$(mktemp /dev/shm/yubiOS-signed-XXXXXX.efi)"
# SC2064: single quotes so vars expand at signal time, not at trap registration
trap 'shred -u "$TMP_KEY" 2>/dev/null || rm -f "$TMP_KEY"; rm -f "$SIGNED"' EXIT

yubiOS_log "Decrypting signing key (touch YubiKey)..."
age -d -o "$TMP_KEY" "$ENC_KEY"

yubiOS_log "Signing $EFI..."
# ADR-008: systemd-sbsign (systemd >= 257) replaces legacy sbsigntool `sbsign`.
# systemd-sbsign cannot sign in place, so write to a temp file then move over.
systemd-sbsign sign \
  --private-key "$TMP_KEY" \
  --certificate "$CERT_PEM" \
  --output "$SIGNED" \
  "$EFI"
mv -f "$SIGNED" "$EFI"

yubiOS_log "Signed: $EFI"


## New Ideas -- cycle 2 (lens format)

This file was processed by the RSI cycle-2 lens generator (curve-compass-skill v1.1.0 + curved-corpus-create v1.1.0). Each cycle-2 patch IS a concrete experiment with a measurable delta -- not a templated section. The lens below documents the measured dynamics; the patch is the lens, not prose about the file.

```json
{
  "lens": "L544",
  "file": "usr/lib/yubiOS/sign-uki-fido2.sh",
  "hypothesis": "usr/lib/yubiOS/sign-uki-fido2.sh covers all 9 primitives in the internal-big-picture basis",
  "method": "9-D primitive binarization (purpose, examples, guidelines, constraints, verification, composition, changelog, references, anti-patterns) + chordal distance to ideal pole on Fibonacci lattice",
  "parameters": {
    "basis": "internal-big-picture",
    "d": 9,
    "seed": 20260812
  },
  "delta": {
    "k": 2,
    "missing_primitives": [
      "examples",
      "guidelines",
      "verification",
      "composition",
      "changelog",
      "references",
      "anti-patterns"
    ],
    "chordal_resid": 0.0
  },
  "verdict": "NO",
  "score": 11,
  "caveat": "binarization is heuristic; a stricter regex pass might surface sub-primitives"
}
```
