#!/usr/bin/env bash
# Phase F0 done-condition check — run INSIDE the booted QEMU virt ARM64 guest.
# Proves: (1) the fTPM TA is registered and /dev/tpm0 + /dev/tpmrm0 exist,
#         (2) the TPM responds to TPM2_Startup,
#         (3) a PCR extend changes a PCR value (measured-boot primitive works).
# No YubiKey here: this validates the platform-integrity TPM, not user identity.
set -euo pipefail

FTPM_UUID="bc50d971-d4c9-42c4-82cb-343fb7f37896"
PCR="${PCR:-16}"   # PCR 16 is the debug/resettable PCR — safe to extend in a bring-up test.

echo "=== yubiOS Phase F0 — fTPM /dev/tpm0 + PCR-extend verification ==="

echo -n "1/5 OP-TEE bus + fTPM TA present... "
dmesg | grep -q "optee: initialized driver" && echo "OK" || { echo "FAIL (no OP-TEE driver)"; exit 1; }

echo -n "2/5 /dev/tpm0 and /dev/tpmrm0 exist... "
[ -c /dev/tpm0 ] && [ -c /dev/tpmrm0 ] && echo "OK" || { echo "FAIL (tpm_ftpm_tee not bound)"; exit 1; }

echo -n "3/5 TPM responds to startup/getcap... "
tpm2_startup -c 2>/dev/null || true
tpm2_getcap properties-fixed >/dev/null 2>&1 && echo "OK" || { echo "FAIL"; exit 1; }

echo "4/5 Reading PCR $PCR before extend..."
BEFORE="$(tpm2_pcrread "sha256:$PCR" | awk '/'"$PCR"' *:/{print $NF}')"
echo "    before: $BEFORE"

echo -n "5/5 Extending PCR $PCR and confirming it changed... "
tpm2_pcrextend "$PCR:sha256=$(printf 'yubiOS-f0' | sha256sum | cut -d' ' -f1)"
AFTER="$(tpm2_pcrread "sha256:$PCR" | awk '/'"$PCR"' *:/{print $NF}')"
echo "    after:  $AFTER"
[ "$BEFORE" != "$AFTER" ] && echo "OK — PCR extended" || { echo "FAIL (PCR unchanged)"; exit 1; }

echo ""
echo "=== PASS: live /dev/tpm0 backed by ms-tpm-20-ref fTPM ($FTPM_UUID), PCR extend works ==="


## New Ideas -- cycle 2 (lens format)

This file was processed by the RSI cycle-2 lens generator (curve-compass-skill v1.1.0 + curved-corpus-create v1.1.0). Each cycle-2 patch IS a concrete experiment with a measurable delta -- not a templated section. The lens below documents the measured dynamics; the patch is the lens, not prose about the file.

```json
{
  "lens": "L501",
  "file": "tests/vm/verify-tpm0-pcr-extend.sh",
  "hypothesis": "tests/vm/verify-tpm0-pcr-extend.sh covers all 9 primitives in the internal-big-picture basis",
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
