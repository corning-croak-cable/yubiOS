#!/bin/bash
# SPDX-License-Identifier: LGPL-2.1-or-later
# yubiOS TOTP enrollment via ykman oath
# Stores TOTP secret in YubiKey OATH applet (hidraw).
# Usage: yubiOS-enroll-totp <name> <secret-uri>
#   e.g: yubiOS-enroll-totp "GitHub" "otpauth://totp/..."
# Source: https://docs.yubico.com/software/yubikey-manager/yubikey-manager-manual.html
set -euo pipefail
# shellcheck source=lib.sh
source /usr/lib/yubiOS/lib.sh

wait_for_yubikey

ACCOUNT="${1:-}"
URI="${2:-}"

if [[ -z "$ACCOUNT" || -z "$URI" ]]; then
  echo "Usage: yubiOS-enroll-totp <account-name> <otpauth-uri>"
  echo "  e.g: yubiOS-enroll-totp \"GitHub\" \"otpauth://totp/GitHub:user@example.com?secret=BASE32...\""
  exit 1
fi

yubiOS_log "Adding TOTP account: $ACCOUNT"
ykman oath accounts uri "$URI"
yubiOS_log "Done. List accounts: ykman oath accounts list"
# SC2027/SC2086: escape inner quotes so $ACCOUNT is properly quoted
yubiOS_log "Get code:            ykman oath accounts code \"$ACCOUNT\""


## New Ideas -- cycle 2 (lens format)

This file was processed by the RSI cycle-2 lens generator (curve-compass-skill v1.1.0 + curved-corpus-create v1.1.0). Each cycle-2 patch IS a concrete experiment with a measurable delta -- not a templated section. The lens below documents the measured dynamics; the patch is the lens, not prose about the file.

```json
{
  "lens": "L541",
  "file": "usr/lib/yubiOS/enroll-totp.sh",
  "hypothesis": "usr/lib/yubiOS/enroll-totp.sh covers all 9 primitives in the internal-big-picture basis",
  "method": "9-D primitive binarization (purpose, examples, guidelines, constraints, verification, composition, changelog, references, anti-patterns) + chordal distance to ideal pole on Fibonacci lattice",
  "parameters": {
    "basis": "internal-big-picture",
    "d": 9,
    "seed": 20260812
  },
  "delta": {
    "k": 1,
    "missing_primitives": [
      "examples",
      "guidelines",
      "constraints",
      "verification",
      "composition",
      "changelog",
      "references",
      "anti-patterns"
    ],
    "chordal_resid": 0.0
  },
  "verdict": "NO",
  "score": 6,
  "caveat": "binarization is heuristic; a stricter regex pass might surface sub-primitives"
}
```
