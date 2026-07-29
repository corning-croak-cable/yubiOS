#!/bin/bash
# End-to-end LUKS2 FIDO2 unlock test using bcvk native-to-disk + a host-attached YubiKey.
# Requires: bcvk, a physical YubiKey visible to the HOST's /dev/hidraw* (so systemd-cryptenroll
# can prompt for a tap), and a spare block device.
# Usage: sudo ./tests/vm/test-luks-fido2.sh /dev/sdX <yubiOS-image:tag>
#
# The image MUST be a production yubiOS image (mkosi without --profile test): if passless +
# the swu2f uhid forced-load are present, the flashed disk itself will enumerate a virtual
# FIDO2 device on next boot. That is harmless for THIS test (step 5 runs systemd-cryptenroll
# on the HOST against the HOST's HID bus, not inside the flashed image), but a test image
# would silently pass CI tests/vm/test-luks-fido2-ci.sh's enrollment against passless on
# the SAME host, which is the gap tests/vm/lib/real-u2f-guard.sh was added to catch.
#
# Step 5's `--fido2-device=auto --fido2-with-user-presence=yes` REQUIRES a real YubiKey
# tap to complete enrollment. If the host has no real key, the precondition below dies
# loudly BEFORE `systemd-cryptenroll` is invoked -- so the operator never sees a silent
# "no tap prompt, nothing happened" failure mode.
set -euo pipefail

DEVICE="${1:-}"
IMAGE="${2:-}"   # required: previous default (ghcr.io/corning-croak-cable/yubiOS:latest) was a stale org rename that 404s
PASS="testpassphrase123"

[[ -z "$DEVICE" || -z "$IMAGE" ]] && { echo "Usage: $0 <block-device> <image:tag>"; exit 1; }
[[ "$EUID" -ne 0 ]]  && { echo "Run as root (sudo)."; exit 1; }

echo "=== yubiOS LUKS2 FIDO2 end-to-end test ==="
echo "  Device : $DEVICE"
echo "  Image  : $IMAGE"
echo ""

# Step 1: Wipe any prior filesystem/RAID/LVM signatures on the target disk,
# then flash yubiOS to it. wipefs -a is bcvk's own suggested alternative
# when its "Detected existing partitions" error fires (see OMN-14), and it
# works across bcvk builds that don't yet expose a --wipe flag.
wipefs -a "$DEVICE" || true
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
echo -n "$PASS" | cryptsetup open "$LUKS_PART" yubiOS-test --batch-mode
cryptsetup status yubiOS-test
cryptsetup close yubiOS-test

# Step 4.5 (NEW): real-YubiKey precondition for the FIDO2 enrollment in step 5.
# systemd-cryptenroll --fido2-device=auto picks the FIRST HID FIDO2 device it
# enumerates. If the host has no real Yubico (VID 1050) device, --auto finds
# nothing and the enrollment silently exits without prompting -- exactly the
# "I havent been asked to tap/enroll" failure mode. This precondition matches
# the inverse of tests/vm/lib/real-u2f-guard.sh: the CI tests fail loud when a
# real key IS visible (so they don't accidentally exercise the real key instead
# of passless); this DESTRUCTIVE test fails loud when a real key is NOT visible
# (so the operator doesn't silently enroll against nothing).
real_key_seen=0
if [[ -d /sys/class/hidraw ]]; then
  for d in /sys/class/hidraw/*; do
    [[ -e "$d" ]] || continue
    if command -v udevadm >/dev/null 2>&1; then
      if udevadm info "$d" 2>/dev/null | grep -Eiq 'ID_VENDOR=Yubico|ID_VENDOR_ID=1050'; then
        real_key_seen=1
        echo "OK: real YubiKey on $d (will be used by step 5)"
        break
      fi
    fi
  done
fi
if [[ "$real_key_seen" -ne 1 ]]; then
  echo "FAIL: no real YubiKey visible to the HOST's HID bus." >&2
  echo "" >&2
  echo "Step 5 calls systemd-cryptenroll --fido2-device=auto --fido2-with-user-presence=yes" >&2
  echo "against $LUKS_PART. With no real Yubico (VID 1050) device on /dev/hidraw*, --auto" >&2
  echo "finds nothing and the enrollment exits silently without ever prompting for a tap." >&2
  echo "" >&2
  echo "Remedies (pick one):" >&2
  echo "  1. Plug in a YubiKey and re-run (preferred)." >&2
  echo "  2. Run on a host that already has a YubiKey attached." >&2
  exit 1
fi

# Step 5: Enroll FIDO2 (interactive — requires YubiKey touch)
echo "5/5 Enrolling FIDO2 (touch YubiKey when prompted)"
systemd-cryptenroll \
  --fido2-device=auto \
  --fido2-with-client-pin=yes \
  --fido2-with-user-presence=yes \
  "$LUKS_PART"

echo ""
echo "=== PASS: LUKS2 FIDO2 enrollment complete ==="
echo "Remove the passphrase slot after confirming FIDO2 works:"
echo "  systemd-cryptenroll --wipe-slot=password $LUKS_PART"
