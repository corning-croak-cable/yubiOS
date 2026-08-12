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


## New Ideas -- cycle 3 (lens external)

This file's lens is **L466** in `lenses.json` (score 11/50, verdict **NO**, k=2/9). Full experiment: hypothesis `tests/unit/test-bootloader-update-unit.bats covers all 9 primitives in the internal-big-picture basis`, method `9-D primitive binarization (purpose, examples, guidelines, constraints, verifica...`. See root `new-ideas-2026-08-12.md` for the cycle-3 summary.
