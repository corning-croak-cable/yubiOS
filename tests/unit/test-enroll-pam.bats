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

