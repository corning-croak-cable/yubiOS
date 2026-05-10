#!/bin/bash
# End-to-end LUKS2 FIDO2 unlock test using bcvk native-to-disk + YubiKey passthrough.
# Requires: bcvk, a physical YubiKey, and a spare block device (USB or loop).
# Usage: sudo ./tests/vm/test-luks-fido2.sh /dev/sdX [yubios-image:tag]
set -euo pipefail

DEVICE="${1:-}"
IMAGE="${2:-ghcr.io/corning-croak-cable/yubios:latest}"
PASS="testpassphrase123"

[[ -z "$DEVICE" ]] && { echo "Usage: $0 <block-device> [image]"; exit 1; }
[[ "$EUID" -ne 0 ]]  && { echo "Run as root (sudo)."; exit 1; }

echo "=== yubios LUKS2 FIDO2 end-to-end test ==="
echo "  Device : $DEVICE"
echo "  Image  : $IMAGE"
echo ""

# Step 1: Flash yubios to device
echo "1/5 Flashing $IMAGE -> $DEVICE"
bcvk native-to-disk --yes "$IMAGE" "$DEVICE"

# Step 2: Find the LUKS partition (second partition after ESP)
LUKS_PART=$(lsblk -J -o NAME,FSTYPE "$DEVICE" | \
  python3 -c "
import sys,json
d=json.load(sys.stdin)
for b in d['blockdevices']:
  for c in b.get('children',[]):
    if c.get('fstype')=='crypto_LUKS': print('/dev/'+c['name']); break
")
echo "2/5 LUKS partition: $LUKS_PART"
[[ -z "$LUKS_PART" ]] && { echo "ERROR: no LUKS partition found"; exit 1; }

# Step 3: Add a known passphrase slot for test automation
echo "3/5 Adding test passphrase slot"
echo -n "$PASS" | cryptsetup luksAddKey "$LUKS_PART" - --batch-mode

# Step 4: Verify passphrase unlocks
echo "4/5 Verifying passphrase unlock"
echo -n "$PASS" | cryptsetup open "$LUKS_PART" yubios-test --batch-mode
cryptsetup status yubios-test
cryptsetup close yubios-test

# Step 5: Enroll FIDO2 (interactive — requires YubiKey touch)
echo "5/5 Enrolling FIDO2 (insert YubiKey and touch when prompted)"
systemd-cryptenroll \
  --fido2-device=auto \
  --fido2-with-client-pin=yes \
  --fido2-with-user-presence=yes \
  "$LUKS_PART"

echo ""
echo "=== PASS: LUKS2 FIDO2 enrollment complete ==="
echo "Remove the passphrase slot after confirming FIDO2 works:"
echo "  systemd-cryptenroll --wipe-slot=password $LUKS_PART"
