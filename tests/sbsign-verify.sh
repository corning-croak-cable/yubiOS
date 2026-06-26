#!/bin/bash
# T5(a) - systemd-sbsign signed-UKI/EFI verify via osslsigncode (ADR-008).
#
# Two layers:
#   * SOFTWARE path (this script, CI-runnable): generate an ECC P-384 key +
#     self-signed cert, sign a PE/EFI binary with systemd-sbsign using a file
#     key, then verify the Authenticode signature with osslsigncode. Exercises
#     the exact verify gate without a YubiKey.
#   * HARDWARE path (PIV slot 9c, requires YubiKey): tests/validate-pkcs11-uri.sh
#     signs with --private-key-source engine:pkcs11 against libykcs11 + the PIV
#     cert, then osslsigncode-verifies. Run that on real hardware.
#
# sbverify is gone with sbsigntool and systemd-sbsign has no verify verb, so
# osslsigncode is the Authenticode verifier (matches 2026/sbsign-pkcs11-validate.md).
# Skips (exit 0 with SKIP) when tools or a PE input are unavailable - safe in CI.
set -euo pipefail

have() { command -v "$1" >/dev/null 2>&1; }

for t in openssl systemd-sbsign osslsigncode; do
  have "$t" || { echo "SKIP: $t not installed (software sbsign-verify path needs all three)"; exit 0; }
done

TEST_PE="${SBSIGN_TEST_PE:-}"
if [[ -z "$TEST_PE" ]]; then
  for c in /usr/lib/systemd/boot/efi/systemd-bootx64.efi \
           /usr/lib/systemd/boot/efi/systemd-bootaa64.efi; do
    [[ -f "$c" ]] && { TEST_PE="$c"; break; }
  done
fi
[[ -n "$TEST_PE" && -f "$TEST_PE" ]] || { echo "SKIP: no PE/EFI input (set SBSIGN_TEST_PE=)"; exit 0; }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

echo "=== T5(a) systemd-sbsign + osslsigncode verify (software path) ==="
echo "  input PE : $TEST_PE"

# 1. ECC P-384 key + self-signed cert (mirrors the PIV slot 9c ECC choice, ADR-008).
openssl ecparam -name secp384r1 -genkey -noout -out "$WORK/sb.key"
openssl req -new -x509 -key "$WORK/sb.key" -out "$WORK/sb.pem" -days 7 \
  -subj "/CN=yubiOS test Secure Boot/O=yubi-OS" >/dev/null 2>&1
openssl ecparam -name secp384r1 -genkey -noout -out "$WORK/other.key"
openssl req -new -x509 -key "$WORK/other.key" -out "$WORK/other.pem" -days 7 \
  -subj "/CN=not-yubiOS/O=attacker" >/dev/null 2>&1

# 2. Sign with systemd-sbsign using the file key (no PKCS#11).
echo -n "1/3 systemd-sbsign sign... "
systemd-sbsign sign \
  --private-key "$WORK/sb.key" \
  --private-key-source file \
  --certificate "$WORK/sb.pem" \
  --certificate-source file \
  --output "$WORK/signed.efi" \
  "$TEST_PE" >/dev/null 2>&1 && echo OK || { echo FAIL; exit 1; }

# 3. POSITIVE: osslsigncode verifies against the signing cert.
echo -n "2/3 osslsigncode verify against signing cert (expect PASS)... "
osslsigncode verify -in "$WORK/signed.efi" -CAfile "$WORK/sb.pem" >/dev/null 2>&1 \
  && echo OK || { echo FAIL; exit 1; }

# 4. NEGATIVE: verifying against an unrelated cert must fail.
echo -n "3/3 osslsigncode verify against wrong cert (expect FAIL)... "
if osslsigncode verify -in "$WORK/signed.efi" -CAfile "$WORK/other.pem" >/dev/null 2>&1; then
  echo "FAIL (verify accepted an unrelated cert!)"; exit 1
else
  echo OK
fi

echo ""
echo "=== PASS: systemd-sbsign output verifies under the signing cert and only that cert ==="
echo "Hardware/PIV path (YubiKey slot 9c): tests/validate-pkcs11-uri.sh"
