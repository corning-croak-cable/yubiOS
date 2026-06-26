#!/usr/bin/env bats
# T5(b,c) - yubiOS-enroll.service v261 hardening (ADR-016). No hardware required.
# Run: bats tests/unit/test-enroll-unit-hardening.bats
#   (b) ConditionSecurity=measured-os gates enrollment on a measured boot.
#   (c) RestrictFileSystems=~@network present + the unit stays valid on v261.

setup() {
  UNIT="usr/lib/systemd/system/yubiOS-enroll.service"
  [ -f "$UNIT" ] || UNIT="/usr/lib/systemd/system/yubiOS-enroll.service"
  [ -f "$UNIT" ] || skip "yubiOS-enroll.service not found"
}

@test "enroll unit declares RestrictFileSystems=~@network" {
  run grep -Eq '^RestrictFileSystems=~@network$' "$UNIT"
  [ "$status" -eq 0 ]
}

@test "RestrictFileSystems uses a deny-list (leading ~), not an allow-list" {
  # Leading ~ = deny the listed sets; local block/API filesystems stay usable.
  # An allow-list (no ~) would break btrfs/ext4/proc/sysfs for the enroll script.
  run grep -Eq '^RestrictFileSystems=~' "$UNIT"
  [ "$status" -eq 0 ]
}

@test "enroll unit declares ConditionSecurity=measured-os" {
  run grep -Eq '^ConditionSecurity=measured-os$' "$UNIT"
  [ "$status" -eq 0 ]
}

@test "measured-os condition is NOT satisfied on an unmeasured CI host" {
  # The service must be skipped unless the OS booted measured (UKI + sealed PCRs).
  command -v systemd-analyze >/dev/null || skip "systemd-analyze not installed"
  systemd-analyze condition --help >/dev/null 2>&1 || skip "no 'condition' verb (systemd too old)"
  if systemd-analyze condition 'ConditionSecurity=measured-os' >/dev/null 2>&1; then
    skip "host reports measured-os; gate is satisfied here"
  fi
  run systemd-analyze condition 'ConditionSecurity=measured-os'
  [ "$status" -ne 0 ]
}

@test "unit passes systemd-analyze verify" {
  command -v systemd-analyze >/dev/null || skip "systemd-analyze not installed"
  run systemd-analyze verify --man=no "$UNIT"
  [ "$status" -eq 0 ]
}

@test "unit keeps the first-boot guards intact" {
  run grep -Eq '^ConditionFirstBoot=yes$' "$UNIT"
  [ "$status" -eq 0 ]
  run grep -Eq 'ConditionPathExists=!/var/lib/yubiOS/' "$UNIT"
  [ "$status" -eq 0 ]
}
