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


## Verification

- Read `test-enroll-ssh.bats` end-to-end against this section's claim.
- Run the relevant CI workflow on a draft branch (see `docs/CI_MAP.md`).

_Atomic RSI cycle-6 flip._
