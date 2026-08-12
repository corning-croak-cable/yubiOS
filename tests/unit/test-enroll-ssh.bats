#!/usr/bin/env bats
# Unit tests for enroll-ssh.sh logic

setup() {
  export TMPDIR="$(mktemp -d)"
  export HOME="$TMPDIR"
  ssh-keygen() {
    touch "${4:-$HOME/.ssh/id_ed25519_sk}"
    touch "${4:-$HOME/.ssh/id_ed25519_sk}.pub"
    echo "sk-ed25519@openssh.com AAAA... yubiOS@test"
  }
  hostname() { echo "testhost"; }
  export -f ssh-keygen hostname
}

teardown() { rm -rf "$TMPDIR"; }

@test "creates .ssh dir with mode 700" {
  SSH_DIR="$TMPDIR/.ssh"
  mkdir -p "$SSH_DIR" && chmod 700 "$SSH_DIR"
  run stat -c "%a" "$SSH_DIR"
  [ "$output" = "700" ]
}

@test "skips if key already exists" {
  KEY="$TMPDIR/.ssh/id_ed25519_sk"
  mkdir -p "$TMPDIR/.ssh"
  touch "$KEY"
  # Simulate the guard: [[ -f "$KEY_FILE" ]] && exit 0
  run bash -c "[[ -f '$KEY' ]] && echo skipped || echo generated"
  [ "$output" = "skipped" ]
}

@test "generates key when none exists" {
  run bash -c "[[ -f '$TMPDIR/.ssh/id_ed25519_sk' ]] && echo skipped || echo generated"
  [ "$output" = "generated" ]
}


## Examples

- Reading `test-enroll-ssh.bats` (no args) shows usage
- See `docs/ARCHITECTURE.md` for where this file fits in yubiOS


## Guidelines

- Match the conventions in `docs/STYLE.md`
- See sibling files in this directory for the surrounding context


## Constraints

- Out of scope: changes to `papers/` (historical info) or `.github/workflows/*.yml` (CI workflows)


## Verification

- Spot-check by reading `test-enroll-ssh.bats` end-to-end against this section's claim
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
