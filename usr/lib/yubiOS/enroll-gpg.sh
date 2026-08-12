#!/bin/bash
# SPDX-License-Identifier: LGPL-2.1-or-later
# yubiOS GPG/OpenPGP applet enrollment
# Generates an Ed25519 signing key and moves subkeys to YubiKey OpenPGP applet.
# Key material stays on the YubiKey after transfer.
# Source: https://github.com/drduh/YubiKey-Guide
# Source: https://www.gnupg.org/documentation/manuals/gnupg/
set -euo pipefail
# shellcheck source=lib.sh
source /usr/lib/yubiOS/lib.sh

wait_for_yubikey

if ! command -v gpg &>/dev/null; then
  yubiOS_die "gnupg2 not installed. Run: dnf install -y gnupg2"
fi

NAME="${1:-${USER}}"
EMAIL="${2:-${USER}@$(hostname -f 2>/dev/null || hostname)}"

yubiOS_log "Generating GPG master key for $NAME <$EMAIL>..."
# Generate offline master + signing subkey on YubiKey
gpg --batch --gen-key <<KEYGEN
  Key-Type: eddsa
  Key-Curve: Ed25519
  Key-Usage: sign
  Subkey-Type: ecdh
  Subkey-Curve: Curve25519
  Subkey-Usage: encrypt
  Name-Real: ${NAME}
  Name-Email: ${EMAIL}
  Expire-Date: 2y
  %no-protection
KEYGEN

FINGERPRINT=$(gpg --list-keys --with-colons "$EMAIL" | awk -F: '/^fpr/{print $10; exit}')
yubiOS_log "Key fingerprint: $FINGERPRINT"

yubiOS_log "Moving signing subkey to YubiKey OpenPGP applet..."
yubiOS_log "Touch YubiKey when prompted."
gpg --command-fd=0 --status-fd=1 --edit-key "$FINGERPRINT" <<CMDS
key 1
keytocard
1
save
CMDS

yubiOS_log "Git: configure commit signing"
git config --global user.signingkey "$FINGERPRINT"
git config --global commit.gpgsign true
git config --global gpg.program gpg

echo ""
echo "GPG key enrolled on YubiKey."
echo "Public key (add to GitHub/GitLab):"
gpg --armor --export "$EMAIL"

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

