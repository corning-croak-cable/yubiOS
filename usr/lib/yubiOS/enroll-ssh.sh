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

# ## Examples
# # Reading the file with no arguments shows the help text.
# # See docs/ARCHITECTURE.md for where this fits in yubiOS.

# ## Guidelines
# # Follow the conventions in docs/STYLE.md. Match the structure of surrounding files.

# ## References
# # yubiOS repo: yubi-OS/yubiOS
# # See docs/ARCHITECTURE.md and the two new skills in skills/github-yubios-KS9n5GAT/.

# ## Anti-patterns
# # Don't claim structure without a null (see curved-corpus-create skill).
# # Don't report pi_T statistics as properties of the historical corpus.

