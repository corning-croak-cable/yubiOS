#!/usr/bin/env bats
# Static checks for the bootloader-update.service bcvk DirectBoot guard.
# Run: bats tests/unit/test-bootloader-update-unit.bats

DROPIN="usr/lib/systemd/system/bootloader-update.service.d/10-skip-bcvk-virtiofs-root.conf"
SCRIPT="usr/lib/yubiOS/skip-bootloader-update-if-bcvk.sh"

setup() {
  [ -f "$DROPIN" ] || DROPIN="/usr/lib/systemd/system/bootloader-update.service.d/10-skip-bcvk-virtiofs-root.conf"
  [ -f "$SCRIPT" ] || SCRIPT="/usr/lib/yubiOS/skip-bootloader-update-if-bcvk.sh"
}

@test "bootloader-update uses the bcvk runtime ExecCondition" {
  run grep -Fx 'ExecCondition=/usr/lib/yubiOS/skip-bootloader-update-if-bcvk.sh' "$DROPIN"
  [ "$status" -eq 0 ]
}

@test "bootloader-update ExecCondition is declared in the Service section" {
  section="$(awk '/^\[/{s=$0} /ExecCondition=/{print s}' "$DROPIN")"
  [ "$section" = "[Service]" ]
}

@test "bootloader-update helper identifies virtiofs root from proc mounts" {
  run grep -F '/proc/mounts' "$SCRIPT"
  [ "$status" -eq 0 ]
  run grep -F '$3 == "virtiofs"' "$SCRIPT"
  [ "$status" -eq 0 ]
}

@test "bootloader-update drop-in documents installed-system behavior" {
  run grep -F 'Real installed' "$DROPIN"
  [ "$status" -eq 0 ]
}


## Verification

- Read `test-bootloader-update-unit.bats` end-to-end against this section's claim.
- Run the relevant CI workflow on a draft branch (see `docs/CI_MAP.md`).

_Atomic RSI cycle-6 flip._


## Anti-patterns

- Don't claim structure without a null (per `curved-corpus-create` skill).
- Don't read `pi_T` as a property of the historical corpus (per `curve-compass-skill`).

_RSI cycle-7 atomic flip (gap-informed, NSS-axis(failure_modes))._
