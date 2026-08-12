#!/bin/bash
# SPDX-License-Identifier: LGPL-2.1-or-later
# yubiOS SSH key enrollment via FIDO2 ed25519-sk (resident key)
#
# Protocol: FIDO2 via /dev/hidraw* (libfido2)
# ed25519-sk: private key stays on YubiKey; stub + pubkey stored on disk.
# -O resident: credential stored in YubiKey FIDO2 internal storage.
# Recovery: ssh-keygen -K regenerates stub from YubiKey on any new machine.
#
# Source: https://www.openssh.com/txt/release-8.2 (OpenSSH 8.2 FIDO2 support)
# Source: libfido2 v1.16.0 hidraw communication
# Requires: OpenSSH >= 8.2, YubiKey firmware >= 5.2.3, libfido2 >= 1.10

set -euo pipefail
# shellcheck source=lib.sh
source /usr/lib/yubiOS/lib.sh

SSH_DIR="${HOME}/.ssh"
KEY_FILE="${SSH_DIR}/id_ed25519_sk"
mkdir -p "$SSH_DIR" && chmod 700 "$SSH_DIR"

if [[ -f "$KEY_FILE" ]]; then
  yubiOS_warn "Existing key at $KEY_FILE. Skipping. Delete it first to re-enroll."
  exit 0
fi

yubiOS_log "Generating ed25519-sk resident key (touch YubiKey twice when prompted)..."
yubiOS_log "First touch: create credential. Second touch: verify."

# -O resident: store discoverable credential on YubiKey (limited slots)
# -O verify-required: require FIDO2 PIN on every use (not just touch)
# -O application: namespaced so credential is identifiable on the key
# Source: ssh-keygen(1) man page, OpenSSH 8.3+
ssh-keygen -t ed25519-sk \
  -O resident \
  -O verify-required \
  -O application=ssh:yubiOS \
  -f "$KEY_FILE" \
  -C "yubiOS@$(hostname --fqdn 2>/dev/null || hostname)"

chmod 600 "${KEY_FILE}" "${KEY_FILE}.pub"

echo ""
echo "SSH key generated: $KEY_FILE"
echo ""
echo "Your public key (add to remote ~/.ssh/authorized_keys):"
echo ""
cat "${KEY_FILE}.pub"
echo ""
echo "Copy to remote hosts:"
echo "  ssh-copy-id -i ${KEY_FILE}.pub user@hostname"
echo ""
echo "On a new machine, recover stub from YubiKey:"
echo "  ssh-keygen -K"
echo ""
echo "GitHub: Settings -> SSH Keys -> New -> paste the public key above."


## New Ideas -- cycle 2 (lens format)

This file was processed by the RSI cycle-2 lens generator (curve-compass-skill v1.1.0 + curved-corpus-create v1.1.0). Each cycle-2 patch IS a concrete experiment with a measurable delta -- not a templated section. The lens below documents the measured dynamics; the patch is the lens, not prose about the file.

```json
{
  "lens": "L539",
  "file": "usr/lib/yubiOS/enroll-ssh.sh",
  "hypothesis": "usr/lib/yubiOS/enroll-ssh.sh covers all 9 primitives in the internal-big-picture basis",
  "method": "9-D primitive binarization (purpose, examples, guidelines, constraints, verification, composition, changelog, references, anti-patterns) + chordal distance to ideal pole on Fibonacci lattice",
  "parameters": {
    "basis": "internal-big-picture",
    "d": 9,
    "seed": 20260812
  },
  "delta": {
    "k": 5,
    "missing_primitives": [
      "examples",
      "guidelines",
      "references",
      "anti-patterns"
    ],
    "chordal_resid": 0.0
  },
  "verdict": "PARTIAL",
  "score": 28,
  "caveat": "binarization is heuristic; a stricter regex pass might surface sub-primitives"
}
```
