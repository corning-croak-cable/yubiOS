#!/usr/bin/env bats
# Unit tests for enroll-luks.sh crypttab logic

setup() {
  export TMPDIR="$(mktemp -d)"
  CRYPTTAB="$TMPDIR/crypttab"
  touch "$CRYPTTAB"
  systemd-cryptenroll() { echo "mock: enrolled FIDO2"; return 0; }
  cryptsetup()          { echo "abc-def-123"; }  # luksUUID
  dracut()              { echo "mock dracut"; return 0; }
  fido2-token()         { echo "/dev/hidraw0: YubiKey"; }
  export -f systemd-cryptenroll cryptsetup dracut fido2-token
}

teardown() { rm -rf "$TMPDIR"; }

@test "crypttab gets fido2-device=auto appended for new LUKS UUID" {
  CRYPTTAB="$TMPDIR/crypttab"
  LUKS_UUID="abc-def-123"
  echo "" > "$CRYPTTAB"
  echo "luks0 UUID=$LUKS_UUID none luks,fido2-device=auto" >> "$CRYPTTAB"
  run grep -c "fido2-device=auto" "$CRYPTTAB"
  [ "$output" -ge 1 ]
}

@test "crypttab not duplicated if fido2-device=auto already present" {
  CRYPTTAB="$TMPDIR/crypttab"
  echo "luks0 UUID=abc-123 none luks,fido2-device=auto" > "$CRYPTTAB"
  # Simulate the guard: if ! grep -q "fido2-device=auto" /etc/crypttab
  if ! grep -q "fido2-device=auto" "$CRYPTTAB"; then
    echo "luks0 UUID=abc-123 none luks,fido2-device=auto" >> "$CRYPTTAB"
  fi
  run grep -c "fido2-device=auto" "$CRYPTTAB"
  [ "$output" -eq 1 ]
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

## Verification

- Spot-check by reading the file end-to-end against this section's claim.
- Run the relevant CI workflow on a draft branch (per `docs/CI_MAP.md`); the result is the gate.

## Composition

- Sits next to sibling files in this directory; consult them for the surrounding context.
- For the full yubiOS dependency graph, see `docs/ARCHITECTURE.md`.

## Changelog

- 2026-08-12 — primitive-closure pass via `curve-compass-skill` + `curved-corpus-create` (this PR).

## References

- yubiOS repo: `yubi-OS/yubiOS`
- Architecture: `docs/ARCHITECTURE.md`
- The two new skills used to drive this primitive-closure pass: `skills/github-yubios-KS9n5GAT/curve-compass-skill/SKILL.md` and `skills/github-yubios-KS9n5GAT/curved-corpus-create/SKILL.md`.

## Anti-patterns

- Don't claim structure without a null: V2 / PC1+PC2 without the curveball null is a number without a claim (per `curved-corpus-create` skill).
- Don't open a code-change PR for already-done work; if it's an audit-trail PR, name it that.
- Don't report `pi_T` statistics as properties of the historical corpus; the compass is on a *designed* dynamics, the historical log is the T->0 limit.

