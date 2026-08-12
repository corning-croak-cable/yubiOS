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

# ## Examples
# # Reading the file with no arguments shows the help text.
# # See docs/ARCHITECTURE.md for where this fits in yubiOS.

# ## Guidelines
# # Follow the conventions in docs/STYLE.md. Match the structure of surrounding files.

# ## Constraints
# # Out of scope: changes to papers/ or .github/workflows/*.yml (separate change-management).

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

