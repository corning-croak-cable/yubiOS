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

# ## Examples
# # Reading the file with no arguments shows the help text.
# # See docs/ARCHITECTURE.md for where this fits in yubiOS.

# ## Guidelines
# # Follow the conventions in docs/STYLE.md. Match the structure of surrounding files.

# ## Verification
# # Run the relevant CI workflow on a draft branch (see docs/CI_MAP.md); the result is the gate.

# ## Composition
# # Sits next to sibling files in this directory; consult them for surrounding context.
# # See docs/ARCHITECTURE.md for the full dependency graph.

# ## Changelog
# # 2026-08-12 -- primitive-closure pass via curve-compass-skill + curved-corpus-create (this PR).

# ## References
# # yubiOS repo: yubi-OS/yubiOS
# # See docs/ARCHITECTURE.md and the two new skills in skills/github-yubios-KS9n5GAT/.

# ## Anti-patterns
# # Don't claim structure without a null (see curved-corpus-create skill).
# # Don't report pi_T statistics as properties of the historical corpus.

