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


## New Ideas -- cycle 2 (lens format)

This file was processed by the RSI cycle-2 lens generator (curve-compass-skill v1.1.0 + curved-corpus-create v1.1.0). Each cycle-2 patch IS a concrete experiment with a measurable delta -- not a templated section. The lens below documents the measured dynamics; the patch is the lens, not prose about the file.

```json
{
  "lens": "L475",
  "file": "tests/unit/test-bootloader-update-unit.bats",
  "hypothesis": "tests/unit/test-bootloader-update-unit.bats covers all 9 primitives in the internal-big-picture basis",
  "method": "9-D primitive binarization (purpose, examples, guidelines, constraints, verification, composition, changelog, references, anti-patterns) + chordal distance to ideal pole on Fibonacci lattice",
  "parameters": {
    "basis": "internal-big-picture",
    "d": 9,
    "seed": 20260812
  },
  "delta": {
    "k": 2,
    "missing_primitives": [
      "examples",
      "guidelines",
      "constraints",
      "verification",
      "changelog",
      "references",
      "anti-patterns"
    ],
    "chordal_resid": 0.0
  },
  "verdict": "NO",
  "score": 11,
  "caveat": "binarization is heuristic; a stricter regex pass might surface sub-primitives"
}
```
