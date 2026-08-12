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


## Examples

- Reading `test-bootloader-update-unit.bats` (no args) shows usage
- See `docs/ARCHITECTURE.md` for where this file fits in yubiOS


## Guidelines

- Match the conventions in `docs/STYLE.md`
- See sibling files in this directory for the surrounding context


## Constraints

- Out of scope: changes to `papers/` (historical info) or `.github/workflows/*.yml` (CI workflows)


## Verification

- Spot-check by reading `test-bootloader-update-unit.bats` end-to-end against this section's claim
- Run the relevant CI workflow on a draft branch per `docs/CI_MAP.md`


## Changelog

- 2026-08-12 -- RSI cycle-4: new-idea experiment (primitive-flipped changelog, hypothesis + method + delta + verdict + score + caveat in lenses.json L<N>)


## References

- yubiOS repo: `yubi-OS/yubiOS`
- Architecture: `docs/ARCHITECTURE.md`
- See root `lenses.json` and `new-ideas-2026-08-12.md`


## Anti-patterns

- Don't claim structure without a null (per `curved-corpus-create`)
- Don't report pi_T as a property of the historical corpus (per `curve-compass-skill`)
