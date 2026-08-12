#!/bin/bash
# Verify a signed yubiOS UKI against the YubiKey PIV Secure Boot certificate (ADR-008).
# This is the verify half of the sbsign chain: validate-pkcs11-uri.sh proves signing
# works; this proves a *shipped* UKI carries a signature that chains to the PIV cert.
#
# systemd-sbsign has no `verify` verb and sbverify (sbsigntool) is dropped per ADR-008,
# so osslsigncode is the Authenticode verifier that checks against a specific cert.
#
# Usage: ./tests/verify-uki-signature.sh [UKI.efi] [cert.pem]
#   Defaults: newest /boot/EFI/Linux/*.efi  +  /var/lib/yubiOS/yubiOS-sb.pem
set -euo pipefail

CERT_PEM="${2:-${CERT_PEM:-/var/lib/yubiOS/yubiOS-sb.pem}}"
UKI="${1:-${UKI:-}}"

if [[ -z "$UKI" ]]; then
  UKI="$(ls -t /boot/EFI/Linux/*.efi 2>/dev/null | head -n1 || true)"
fi

echo "=== yubiOS UKI signature verification ==="
echo "  UKI  : ${UKI:-<none found>}"
echo "  Cert : $CERT_PEM"

# 1. UKI present
echo -n "1/4 UKI present... "
if [[ -n "$UKI" && -f "$UKI" ]]; then
  echo "OK"
else
  echo "FAIL (no UKI; build/install yubiOS first or pass a path)"
  exit 1
fi

# 2. Certificate present + parseable
echo -n "2/4 Certificate present + parseable... "
if [[ -f "$CERT_PEM" ]] && openssl x509 -in "$CERT_PEM" -noout 2>/dev/null; then
  echo "OK"
else
  echo "FAIL (run yubiOS-enroll-sb first)"
  exit 1
fi

# 3. osslsigncode available
echo -n "3/4 osslsigncode available... "
if ! command -v osslsigncode >/dev/null 2>&1; then
  echo "SKIP (install osslsigncode to verify the signature)"
  exit 0
fi
echo "OK"

# 4. The gate: signature on the UKI chains to the PIV cert.
echo -n "4/4 Verifying UKI Authenticode signature against PIV cert... "
if osslsigncode verify -in "$UKI" -CAfile "$CERT_PEM" >/dev/null 2>&1; then
  echo "OK"
else
  echo "FAIL (UKI is unsigned or signed by a different key)"
  exit 1
fi

echo ""
echo "=== PASS: UKI carries a valid signature chaining to the yubiOS PIV cert ==="


## New Ideas -- cycle 2 (lens format)

This file was processed by the RSI cycle-2 lens generator (curve-compass-skill v1.1.0 + curved-corpus-create v1.1.0). Each cycle-2 patch IS a concrete experiment with a measurable delta -- not a templated section. The lens below documents the measured dynamics; the patch is the lens, not prose about the file.

```json
{
  "lens": "L486",
  "file": "tests/verify-uki-signature.sh",
  "hypothesis": "tests/verify-uki-signature.sh covers all 9 primitives in the internal-big-picture basis",
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
      "constraints",
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
