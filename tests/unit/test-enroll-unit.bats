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
  # systemd-analyze verify also checks that every Exec*= binary exists. On a bare
  # CI runner the shipped binaries (/usr/lib/yubiOS/*.sh) and /bin/{mkdir,touch}
  # are not installed, so verify would exit non-zero on "is not executable" alone
  # â an environment artifact, not a unit defect. Stage a minimal root with an
  # executable stub for each Exec*= path the unit references, then verify against
  # that root. Real directive/syntax errors still fail honestly (a bogus key still
  # yields exit 1); only the missing-real-binary artifact is removed.
  root="$(mktemp -d)"
  mkdir -p "$root/usr/lib/systemd/system"
  cp "$UNIT" "$root/usr/lib/systemd/system/"
  unit_base="$(basename "$UNIT")"
  grep -hoE '''^[[:space:]]*Exec[A-Za-z]*[[:space:]]*=[[:space:]]*[-@!+]*/[^[:space:]]+''' "$UNIT" \
    | sed -E '''s/^[^=]*=[[:space:]]*[-@!+]*//''' \
    | while read -r bin; do
        [ -n "$bin" ] || continue
        mkdir -p "$root$(dirname "$bin")"
        printf '''#!/bin/sh\nexit 0\n''' > "$root$bin"
        chmod +x "$root$bin"
      done
  run systemd-analyze verify --recursive-errors=no --root="$root" "usr/lib/systemd/system/$unit_base"
  rm -rf "$root"
  [ "$status" -eq 0 ]
}

@test "RestrictFileSystems is a known directive on this systemd (>= v250)" {
  command -v systemd-analyze >/dev/null 2>&1 || skip "systemd-analyze not installed"
  ver="$(systemd-analyze --version | awk 'NR==1{print $2}')"
  [ "$ver" -ge 250 ]
}

## Examples

- Reading the file or running the script with no arguments shows the help text.
- For a guided tour of where this file fits in yubiOS, see `docs/ARCHITECTURE.md` and the cross-references in this directory.

## Guidelines

- Follow the conventions in `docs/STYLE.md` (or the most relevant style guide referenced from this directory).
- Match the existing structure of surrounding files: `## Examples`, `## Verification`, `## Changelog`, `## Anti-patterns`.

## Constraints

- Out of scope: changes that affect the historical paper corpus in `papers/` (published artifacts, immutable).
- Out of scope: changes to `.github/workflows/*.yml` (CI workflows, separate change-management process).

## Changelog

- 2026-08-12 — primitive-closure pass via `curve-compass-skill` + `curved-corpus-create` (this PR).

## References

- yubiOS repo: `yubi-OS/yubiOS`
- Architecture: `docs/ARCHITECTURE.md`
- The two new skills used to drive this primitive-closure pass: `skills/github-yubios-KS9n5GAT/curve-compass-skill/SKILL.md` and `skills/github-yubios-KS9n5GAT/curved-corpus-create/SKILL.md`.

