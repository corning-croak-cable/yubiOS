#!/bin/bash
# SPDX-License-Identifier: LGPL-2.1-or-later
# yubiOS Secure Boot enrollment via YubiKey PIV (slot 9c)
#
# Protocol: PIV/PKCS#11 via CCID interface (not hidraw)
# See ADR-002 for why PIV is used instead of FIDO2 HMAC-secret for signing.
#
# References:
#   https://developers.yubico.com/yubico-piv-tool/
#   systemd-sbsign --private-key-source=engine:pkcs11 (ADR-008; replaces sbsign --engine pkcs11)
#   PKCS#11 URI format: https://www.rfc-editor.org/rfc/rfc7512

set -euo pipefail
source /usr/lib/yubiOS/lib.sh

CERT_OUT=/var/lib/yubiOS/yubiOS-sb.cer
CERT_PEM=/var/lib/yubiOS/yubiOS-sb.pem
mkdir -p /var/lib/yubiOS

yubiOS_log "Generating ECC key in YubiKey PIV slot 9c (Digital Signature)..."
yubiOS_log "Key material never leaves the YubiKey."
yubiOS_log "PIV PIN will be prompted by ykman."

# Generate key on device, export self-signed cert
# -a ECCP384 for ECC; YubiKey 5 supports EC P-256 and P-384
ykman piv keys generate \
  --algorithm ECCP384 \
  --pin-policy ALWAYS \
  --touch-policy ALWAYS \
  9c /tmp/yubiOS-sb-pubkey.pem

# Self-sign a Secure Boot db certificate
ykman piv certificates generate \
  --subject "CN=yubiOS Secure Boot,O=yubiOS" \
  --valid-days 3650 \
  9c /tmp/yubiOS-sb-pubkey.pem

# Export cert in PEM and DER form
ykman piv certificates export 9c "$CERT_PEM"
openssl x509 -in "$CERT_PEM" -outform DER -out "$CERT_OUT"

yubiOS_log "Cert exported to $CERT_OUT"

# Build PKCS#11 URI for systemd-sbsign
# Slot 9c on YubiKey = slot ID 0x9c = 156 decimal
# URI format: pkcs11:token=YubiKey%20PIV;id=%9c;type=private
PKCS11_KEY_URI="pkcs11:manufacturer=piv_II;id=%9c;type=private"

yubiOS_log "Signing UKIs with YubiKey PIV (touch required)..."
for uki in /efi/EFI/Linux/*.efi /boot/EFI/Linux/*.efi; do
  [ -f "$uki" ] || continue
  yubiOS_log "Signing: $uki"
  # ADR-008: systemd-sbsign via the OpenSSL pkcs11 engine. It cannot sign in
  # place, so write to a temp file and move over the original on success.
  SIGNED_TMP="$(mktemp /tmp/yubiOS-signed-XXXXXX.efi)"
  PKCS11_MODULE_PATH="$YUBIOS_PKCS11_LIB" \
    systemd-sbsign sign \
      --private-key "$PKCS11_KEY_URI" \
      --private-key-source "engine:pkcs11" \
      --certificate "$CERT_PEM" \
      --certificate-source file \
      --output "$SIGNED_TMP" \
      "$uki"
  mv -f "$SIGNED_TMP" "$uki"
done

echo ""
echo "Secure Boot signing complete."
echo ""
echo "To enable Secure Boot, enroll the Platform Key in your UEFI:"
echo "  1. Copy $CERT_OUT to a USB drive or /efi/"
echo "  2. Enter UEFI (power + volume up on Surface)"
echo "  3. Security -> Secure Boot -> Reset to Setup Mode"
echo "  4. Enroll Platform Key from file -> yubiOS-sb.cer"
echo ""
echo "Or with sbctl (if UEFI is in Setup Mode):"
echo "  sbctl enroll-keys --microsoft"
