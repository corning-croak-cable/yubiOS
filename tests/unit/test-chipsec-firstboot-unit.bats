#!/usr/bin/env bats
# Static checks for the CHIPSEC first-boot validation unit.
# Covers the TODO/FUTURE guardrail that CHIPSEC remains a one-shot exception:
# measured boot only, first boot only, no network, narrow write paths, and the
# documented raw-hardware capability exception.
# Run: bats tests/unit/test-chipsec-firstboot-unit.bats

UNIT="usr/lib/systemd/system/yubiOS-chipsec-firstboot.service"
WRAPPER="usr/lib/yubiOS/chipsec/run-firstboot-check.sh"

setup() {
  [ -f "$UNIT" ] || UNIT="/usr/lib/systemd/system/yubiOS-chipsec-firstboot.service"
  [ -f "$WRAPPER" ] || WRAPPER="/usr/lib/yubiOS/chipsec/run-firstboot-check.sh"
}

@test "chipsec unit gates on measured boot and first boot" {
  run grep -E '^[[:space:]]*ConditionSecurity[[:space:]]*=[[:space:]]*measured-os[[:space:]]*$' "$UNIT"
  [ "$status" -eq 0 ]

  run grep -E '^[[:space:]]*ConditionFirstBoot[[:space:]]*=[[:space:]]*yes[[:space:]]*$' "$UNIT"
  [ "$status" -eq 0 ]
}

@test "chipsec unit runs before enrollment as a one-shot service" {
  run grep -E '^[[:space:]]*Before[[:space:]]*=[[:space:]]*yubiOS-enroll\.service[[:space:]]*$' "$UNIT"
  [ "$status" -eq 0 ]

  run grep -E '^[[:space:]]*Type[[:space:]]*=[[:space:]]*oneshot[[:space:]]*$' "$UNIT"
  [ "$status" -eq 0 ]

  run grep -E '^[[:space:]]*RemainAfterExit[[:space:]]*=[[:space:]]*no[[:space:]]*$' "$UNIT"
  [ "$status" -eq 0 ]
}

@test "chipsec unit keeps the firmware-scan exception offline" {
  run grep -E '^[[:space:]]*PrivateNetwork[[:space:]]*=[[:space:]]*yes[[:space:]]*$' "$UNIT"
  [ "$status" -eq 0 ]
}

@test "chipsec unit keeps filesystem writes narrow" {
  run grep -E '^[[:space:]]*ProtectHome[[:space:]]*=[[:space:]]*yes[[:space:]]*$' "$UNIT"
  [ "$status" -eq 0 ]

  run grep -E '^[[:space:]]*ProtectSystem[[:space:]]*=[[:space:]]*strict[[:space:]]*$' "$UNIT"
  [ "$status" -eq 0 ]

  run grep -E '^[[:space:]]*ReadWritePaths[[:space:]]*=[[:space:]]*/run/yubiOS /tmp[[:space:]]*$' "$UNIT"
  [ "$status" -eq 0 ]
}

@test "chipsec unit capability exception stays explicit" {
  run grep -E '^[[:space:]]*CapabilityBoundingSet[[:space:]]*=[[:space:]]*CAP_SYS_RAWIO CAP_SYS_ADMIN CAP_DAC_OVERRIDE[[:space:]]*$' "$UNIT"
  [ "$status" -eq 0 ]

  run grep -E '^[[:space:]]*NoNewPrivileges[[:space:]]*=[[:space:]]*no[[:space:]]*$' "$UNIT"
  [ "$status" -eq 0 ]
}

@test "chipsec wrapper documents warning-mode result semantics" {
  run grep -F 'RESULT=PASS' "$WRAPPER"
  [ "$status" -eq 0 ]

  run grep -F 'RESULT=WARN' "$WRAPPER"
  [ "$status" -eq 0 ]

  run grep -F 'RESULT=FAILED' "$WRAPPER"
  [ "$status" -eq 0 ]

  run grep -F 'informational only -- it does not PASS/FAIL' "$WRAPPER"
  [ "$status" -eq 0 ]
}

@test "chipsec wrapper warning paths stay non-fatal and explicit" {
  run grep -F 'OVERALL=WARN' "$WRAPPER"
  [ "$status" -eq 0 ]

  run grep -F 'treating as inconclusive, not a hard failure' "$WRAPPER"
  [ "$status" -eq 0 ]

  run grep -F 'WPBT_PRESENT=$WPBT_SEEN' "$WRAPPER"
  [ "$status" -eq 0 ]
}

@test "systemd-analyze verify reports no errors for the chipsec unit" {
  command -v systemd-analyze >/dev/null 2>&1 || skip "systemd-analyze not installed"
  root="$(mktemp -d)"
  mkdir -p "$root/usr/lib/systemd/system"
  cp "$UNIT" "$root/usr/lib/systemd/system/"
  unit_base="$(basename "$UNIT")"
  grep -hoE '^[[:space:]]*Exec[A-Za-z]*[[:space:]]*=[[:space:]]*[-@!+]*/[^[:space:]]+' "$UNIT" \
    | sed -E 's/^[^=]*=[[:space:]]*[-@!+]*//' \
    | while read -r bin; do
        [ -n "$bin" ] || continue
        mkdir -p "$root$(dirname "$bin")"
        printf '#!/bin/sh\nexit 0\n' > "$root$bin"
        chmod +x "$root$bin"
      done
  run systemd-analyze verify --recursive-errors=no --root="$root" "usr/lib/systemd/system/$unit_base"
  rm -rf "$root"
  [ "$status" -eq 0 ]
}


## New Ideas -- cycle 3 (lens external)

This file's lens is **L414** in `lenses.json` (score 22/50, verdict **PARTIAL**, k=4/9). Full experiment: hypothesis `tests/unit/test-chipsec-firstboot-unit.bats covers all 9 primitives in the internal-big-picture basis`, method `9-D primitive binarization (purpose, examples, guidelines, constraints, verifica...`. See root `new-ideas-2026-08-12.md` for the cycle-3 summary.
