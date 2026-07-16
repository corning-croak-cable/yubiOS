#!/usr/bin/env bats
# Static checks for the bootloader-update.service bcvk DirectBoot guard.
# Run: bats tests/unit/test-bootloader-update-unit.bats

DROPIN="usr/lib/systemd/system/bootloader-update.service.d/10-skip-bcvk-virtiofs-root.conf"

setup() {
  [ -f "$DROPIN" ] || DROPIN="/usr/lib/systemd/system/bootloader-update.service.d/10-skip-bcvk-virtiofs-root.conf"
}

@test "bootloader-update drop-in skips bcvk ephemeral virtiofs roots only" {
  run grep -Fx 'ConditionKernelCommandLine=!rootfstype=virtiofs' "$DROPIN"
  [ "$status" -eq 0 ]
}

@test "bootloader-update condition is declared in the Unit section" {
  section="$(awk '/^\[/{s=$0} /ConditionKernelCommandLine/{print s}' "$DROPIN")"
  [ "$section" = "[Unit]" ]
}

@test "bootloader-update drop-in documents installed-system behavior" {
  run grep -F 'real installed systems' "$DROPIN"
  [ "$status" -eq 0 ]
}
