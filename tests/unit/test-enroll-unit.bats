#!/usr/bin/env bats
# Static + verify tests for the shipped enrollment unit (no hardware required).
# Covers ADR-016 gates on usr/lib/systemd/system/yubiOS-enroll.service:
#   - ConditionSecurity=measured-os  (enrollment only on a measured-boot system)
#   - RestrictFileSystems=~@network  (deny network filesystems via BPF-LSM)
# Run: bats tests/unit/test-enroll-unit.bats

UNIT="usr/lib/systemd/system/yubiOS-enroll.service"

setup() {
  [ -f "$UNIT" ] || UNIT="/usr/lib/systemd/system/yubiOS-enroll.service"
}

# -- ConditionSecurity=measured-os ------------------------------------------

@test "enroll unit gates on ConditionSecurity=measured-os" {
  run grep -E '^[[:space:]]*ConditionSecurity[[:space:]]*=[[:space:]]*measured-os[[:space:]]*$' "$UNIT"
  [ "$status" -eq 0 ]
}

@test "ConditionSecurity is declared in [Unit], not [Service]" {
  run bash -c "awk '/^\[/{s=\$0} /ConditionSecurity/{print s}' '$UNIT'"
  [ "$output" = "[Unit]" ]
}

# -- RestrictFileSystems=~@network ------------------------------------------

@test "enroll unit sets RestrictFileSystems to deny @network" {
  run grep -E '^[[:space:]]*RestrictFileSystems[[:space:]]*=[[:space:]]*~@network[[:space:]]*$' "$UNIT"
  [ "$status" -eq 0 ]
}

@test "RestrictFileSystems uses deny-list (~) form, never an allow-list" {
  # An accidental allow-list (no leading ~) would block btrfs/ext4/proc and brick boot.
  line="$(grep -E '^[[:space:]]*RestrictFileSystems' "$UNIT" | head -n1)"
  [[ "$line" == *'~@network'* ]]
}

# -- unit validity on v261 --------------------------------------------------

@test "systemd-analyze verify reports no errors for the enroll unit" {
  command -v systemd-analyze >/dev/null 2>&1 || skip "systemd-analyze not installed"
  run systemd-analyze verify --recursive-errors=no "$UNIT"
  [ "$status" -eq 0 ]
}

@test "RestrictFileSystems is a known directive on this systemd (>= v250)" {
  command -v systemd-analyze >/dev/null 2>&1 || skip "systemd-analyze not installed"
  ver="$(systemd-analyze --version | awk 'NR==1{print $2}')"
  [ "$ver" -ge 250 ]
}
