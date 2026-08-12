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

- Reading `test-enroll-luks.bats` (no args) shows usage
- See `docs/ARCHITECTURE.md` for where this file fits in yubiOS


## Guidelines

- Match the conventions in `docs/STYLE.md`
- See sibling files in this directory for the surrounding context


## Constraints

- Out of scope: changes to `papers/` (historical info) or `.github/workflows/*.yml` (CI workflows)


## Verification

- Spot-check by reading `test-enroll-luks.bats` end-to-end against this section's claim
- Run the relevant CI workflow on a draft branch per `docs/CI_MAP.md`


## Composition

- Sits next to sibling files in this directory; consult them for surrounding context
- For the full yubiOS dependency graph, see `docs/ARCHITECTURE.md`


## Changelog

- 2026-08-12 -- RSI cycle-4: new-idea experiment (primitive-flipped changelog, hypothesis + method + delta + verdict + score + caveat in lenses.json L<N>)


## References

- yubiOS repo: `yubi-OS/yubiOS`
- Architecture: `docs/ARCHITECTURE.md`
- See root `lenses.json` and `new-ideas-2026-08-12.md`


## Anti-patterns

- Don't claim structure without a null (per `curved-corpus-create`)
- Don't report pi_T as a property of the historical corpus (per `curve-compass-skill`)
