#!/bin/bash
# Validates sbsign + libykcs11 PKCS#11 URI for ECC slot 9c.
# Run with YubiKey inserted after running yubios-enroll-sb.
# Verifies: key accessible, cert matches, test sign succeeds.
set -euo pipefail

PKCS11_LIB="${PKCS11_LIB:-/usr/lib64/libykcs11.so}"
CERT_PEM="${CERT_PEM:-/var/lib/yubios/yubios-sb.pem}"
TEST_EFI="${1:-/usr/lib/systemd/boot/efi/systemd-bootx64.efi}"

echo "=== PKCS#11 URI validation for yubios Secure Boot ==="

# 1. Verify the module loads
echo -n "1/5 Loading PKCS11 module... "
pkcs11-tool --module "$PKCS11_LIB" --list-slots 2>/dev/null \
  | grep -q "Yubico" && echo "OK" || { echo "FAIL"; exit 1; }

# 2. Verify key in slot 9c
echo -n "2/5 Key in slot 9c... "
pkcs11-tool --module "$PKCS11_LIB" --list-objects --type privkey 2>/dev/null \
  | grep -q "PIV AUTH" && echo "OK" || { echo "FAIL (check: ykman piv keys info)"; exit 1; }

# 3. Verify cert exported
echo -n "3/5 Certificate at $CERT_PEM... "
[[ -f "$CERT_PEM" ]] && openssl x509 -in "$CERT_PEM" -noout 2>/dev/null \
  && echo "OK" || { echo "FAIL (run yubios-enroll-sb first)"; exit 1; }

# 4. Test sign a file
TMP_SIGNED="$(mktemp /tmp/yubios-test-signed.XXXXXX.efi)"
trap "rm -f $TMP_SIGNED" EXIT
echo -n "4/5 Test signing $TEST_EFI (touch YubiKey)... "
PKCS11_MODULE_PATH="$PKCS11_LIB" sbsign \
  --engine pkcs11 \
  --key "pkcs11:manufacturer=piv_II;id=%9c;type=private" \
  --cert "$CERT_PEM" \
  --output "$TMP_SIGNED" \
  "$TEST_EFI" 2>/dev/null && echo "OK" || { echo "FAIL"; exit 1; }

# 5. Verify the signature
echo -n "5/5 Verifying signature... "
sbverify --cert "$CERT_PEM" "$TMP_SIGNED" 2>/dev/null && echo "OK" || { echo "FAIL"; exit 1; }

echo ""
echo "=== PASS: PKCS#11 URI valid, sbsign works with libykcs11 ==="
echo "Use this URI in mkosi SecureBootKey=:"
echo "  pkcs11:manufacturer=piv_II;id=%9c;type=private"
