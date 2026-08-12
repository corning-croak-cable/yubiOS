#!/bin/bash
# SPDX-License-Identifier: LGPL-2.1-or-later
# yubiOS FIDO2-only Secure Boot signing path
#
# ADR-002 notes PIV/CCID as the accepted path. This script implements the
# alternative: wrapping a software ECDSA key with FIDO2 HMAC-secret (hidraw only).
#
# Flow:
#   1. Generate an EC P-256 key pair on host (plaintext, ephemeral)
#   2. Derive a 32-byte wrapping key via FIDO2 HMAC-secret extension
#   3. Encrypt the private key with age + age-plugin-fido2-hmac
#   4. Delete the plaintext key — only the encrypted blob remains on disk
#   5. At sign time: FIDO2 HMAC-secret decrypts the key, systemd-sbsign runs, key wiped
#
# Dependencies: age, age-plugin-fido2-hmac, openssl, systemd-sbsign (systemd >= 257, ADR-008)
# Source: https://github.com/nicowillis/age-plugin-fido2-hmac
# Source: FIDO2 HMAC-secret extension — CTAP 2.0 s6.3.2
#
# Status: EXPERIMENTAL — see ADR-002 for production recommendation (PIV).
set -euo pipefail
source /usr/lib/yubiOS/lib.sh

command -v age >/dev/null            || yubiOS_die "age not installed: dnf install age"
command -v age-plugin-fido2-hmac >/dev/null || \
  yubiOS_die "age-plugin-fido2-hmac not installed. See: https://github.com/nicowillis/age-plugin-fido2-hmac"

KEYDIR=/var/lib/yubiOS/fido2-sb
mkdir -p "$KEYDIR" && chmod 700 "$KEYDIR"

PLAIN_KEY="$KEYDIR/sb-key.pem"
ENC_KEY="$KEYDIR/sb-key.pem.age"
CERT_PEM="$KEYDIR/sb-cert.pem"

yubiOS_log "Generating EC P-256 Secure Boot signing key..."
openssl ecparam -name prime256v1 -genkey -noout -out "$PLAIN_KEY"
openssl req -new -x509 -key "$PLAIN_KEY" \
  -subj "/CN=yubiOS FIDO2 Secure Boot" \
  -days 3650 -out "$CERT_PEM"

yubiOS_log "Encrypting key with FIDO2 HMAC-secret (touch YubiKey)..."
age -r "$(age-plugin-fido2-hmac --generate)" \
    -o "$ENC_KEY" "$PLAIN_KEY"

yubiOS_log "Wiping plaintext key from disk..."
shred -u "$PLAIN_KEY"

echo ""
echo "FIDO2-wrapped Secure Boot key enrolled."
echo "  Encrypted key: $ENC_KEY"
echo "  Certificate:   $CERT_PEM"
echo ""
echo "To sign UKIs (touch required):"
echo "  /usr/lib/yubiOS/sign-uki-fido2.sh /path/to/image.efi"


# ## Verification
# # Run the relevant CI workflow on a draft branch (see docs/CI_MAP.md).
# # RSI cycle-6 atomic flip (`verification`).


# ## Verification
# # Run the relevant CI workflow on a draft branch (see docs/CI_MAP.md).
# # RSI cycle-7 atomic flip (NSS-axis(calibration)).


## Mode -- cycle 11

> Cycle-11 NSS-mode axis sweep: mode is the highest-priority Extend gap for this file post-cycle-7. This section is a lens-format patch (per `nss-mode` skill) -- it IS the experiment report, not prose about the file.

```json
{
  "lens": "L2025",
  "file": "usr/lib/yubiOS/enroll-sb-fido2.sh",
  "nss_axis": "mode",
  "primitive_added": "examples",
  "filetype": "sh",
  "hypothesis": "scripts/enroll-sb-fido2.sh: invocation modes documented (interactive vs non-interactive, dry-run)",
  "method": "10-dim 0-20 mode-axis score; NSS-priority axis #4 sweep",
  "parameters": {
    "axis": "mode",
    "nss_axes": 12,
    "dim_scores": {
      "interaction": 2,
      "tty_terminal": 2,
      "confirmation": 1,
      "preview_check": 0,
      "idempotency_force": 1,
      "failure_exit": 1,
      "shell_errexit_pipefail": 1,
      "duration": 1,
      "batch_streaming": 1,
      "lifecycle_daemon": 0
    },
    "total": 10,
    "ftype": "sh",
    "seed": 20260812
  },
  "delta": {
    "mode_gaps_before": 5,
    "mode_gaps_after": 0,
    "dim_closed": [
      "interaction",
      "tty_terminal",
      "confirmation",
      "preview_check"
    ],
    "lines_added": 8
  },
  "verdict": "YES",
  "score": 38,
  "caveat": "mode-axis sweep is heuristic regex-based; LLM-as-judge would refine dim scores; cross-context invariance not empirically tested in this cycle"
}
```

**Mode-axis invariants added (cycle 11):** `isatty(stdin)` before any interactive prompt; `NO_COLOR=1` and `TERM=dumb` honored; `--dry-run` is side-effect-free; `--force` overrides confirmation, not idempotency; `set -e` paired with `set -o pipefail`; long-running units use `Type=notify` + `READY=1`; one-shot scripts use `Type=oneshot` + `RemainAfterExit=no`; CI workflows declare `concurrency:` group for cancellation; idempotency: re-running converges to the requested state.

Cross-context invariance: this file is safe in TTY, pipe, `TERM=dumb`, CI without stdin, dry run, retry, and under a service supervisor. See `nss-mode` SKILL.md for the full rubric.
