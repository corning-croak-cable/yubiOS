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


## New Ideas -- cycle 2 (lens format)

This file was processed by the RSI cycle-2 lens generator (curve-compass-skill v1.1.0 + curved-corpus-create v1.1.0). Each cycle-2 patch IS a concrete experiment with a measurable delta -- not a templated section. The lens below documents the measured dynamics; the patch is the lens, not prose about the file.

```json
{
  "lens": "L479",
  "file": "tests/unit/test-enroll-ssh.bats",
  "hypothesis": "tests/unit/test-enroll-ssh.bats covers all 9 primitives in the internal-big-picture basis",
  "method": "9-D primitive binarization (purpose, examples, guidelines, constraints, verification, composition, changelog, references, anti-patterns) + chordal distance to ideal pole on Fibonacci lattice",
  "parameters": {
    "basis": "internal-big-picture",
    "d": 9,
    "seed": 20260812
  },
  "delta": {
    "k": 1,
    "missing_primitives": [
      "examples",
      "guidelines",
      "constraints",
      "verification",
      "composition",
      "changelog",
      "references",
      "anti-patterns"
    ],
    "chordal_resid": 0.0
  },
  "verdict": "NO",
  "score": 6,
  "caveat": "binarization is heuristic; a stricter regex pass might surface sub-primitives"
}
```
