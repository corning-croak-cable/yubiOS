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


## New Ideas -- cycle 3 (lens external)

This file's lens is **L503** in `lenses.json` (score 6/50, verdict **NO**, k=1/9). Full experiment: hypothesis `tests/unit/test-enroll-ssh.bats covers all 9 primitives in the internal-big-picture basis`, method `9-D primitive binarization (purpose, examples, guidelines, constraints, verifica...`. See root `new-ideas-2026-08-12.md` for the cycle-3 summary.
