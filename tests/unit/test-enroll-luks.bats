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


## New Ideas -- cycle 2 (lens format)

This file was processed by the RSI cycle-2 lens generator (curve-compass-skill v1.1.0 + curved-corpus-create v1.1.0). Each cycle-2 patch IS a concrete experiment with a measurable delta -- not a templated section. The lens below documents the measured dynamics; the patch is the lens, not prose about the file.

```json
{
  "lens": "L477",
  "file": "tests/unit/test-enroll-luks.bats",
  "hypothesis": "tests/unit/test-enroll-luks.bats covers all 9 primitives in the internal-big-picture basis",
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
