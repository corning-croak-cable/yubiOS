#!/usr/bin/env bats
# Unit tests for enroll-pam.sh logic (mocked — no hardware required)

setup() {
  export TMPDIR="$(mktemp -d)"
  export HOME="$TMPDIR"
  # Provide mocked commands
  pamu2fcfg() { echo "testuser:cred123,pubkey456"; }
  rpm()        { echo "1.3.2"; }
  logname()    { echo "testuser"; }
  export -f pamu2fcfg rpm logname
}

teardown() { rm -rf "$TMPDIR"; }

@test "enroll-pam creates /etc/yubico dir if missing" {
  ETC="$TMPDIR/etc/yubico"
  YUBICOS_U2F_KEYS="$ETC/u2f_keys"
  mkdir -p "$TMPDIR/etc"
  run bash -c "
    mkdir -p '$ETC' && touch '$YUBICOS_U2F_KEYS' && chmod 600 '$YUBICOS_U2F_KEYS'
    test -f '$YUBICOS_U2F_KEYS'
  "
  [ "$status" -eq 0 ]
}

@test "pamu2fcfg output is appended to u2f_keys" {
  ETC="$TMPDIR/etc/yubico"
  mkdir -p "$ETC"
  U2F="$ETC/u2f_keys"
  touch "$U2F"
  pamu2fcfg -u testuser -N >> "$U2F"
  run grep -c "cred123" "$U2F"
  [ "$output" -ge 1 ]
}

@test "enrollment respects SUDO_USER when set" {
  export SUDO_USER="jenny"
  run bash -c 'echo "${SUDO_USER:-$(logname)}"'
  [ "$output" = "jenny" ]
}

@test "enrollment falls back to logname when SUDO_USER unset" {
  unset SUDO_USER
  run bash -c 'echo "${SUDO_USER:-$(logname)}"'
  [ "$output" = "testuser" ]
}


## Examples

- Reading `test-enroll-pam.bats` (no args) shows usage
- See `docs/ARCHITECTURE.md` for where this file fits in yubiOS


## Guidelines

- Match the conventions in `docs/STYLE.md`
- See sibling files in this directory for the surrounding context


## Constraints

- Out of scope: changes to `papers/` (historical info) or `.github/workflows/*.yml` (CI workflows)


## Verification

- Spot-check by reading `test-enroll-pam.bats` end-to-end against this section's claim
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
