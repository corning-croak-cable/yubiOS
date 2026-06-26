#!/usr/bin/env bats
# T5(d) - pam-u2f auth path for yubiOS (no hardware required; static stack audit).
# Run: bats tests/unit/test-pam-u2f-stack.bats
# Audits usr/lib/pam.d/yubiOS-system-auth and yubiOS-sudo: pam_u2f is a REQUIRED
# factor, correctly placed, with the right authfile/cue/origin, behind a homed
# short-circuit, and the version floor (>= 1.3.1, CVE-2025-23013) is documented.

setup() {
  SA="usr/lib/pam.d/yubiOS-system-auth"
  SUDO="usr/lib/pam.d/yubiOS-sudo"
  [ -f "$SA" ]   || SA="/usr/lib/pam.d/yubiOS-system-auth"
  [ -f "$SUDO" ] || SUDO="/usr/lib/pam.d/yubiOS-sudo"
  [ -f "$SA" ] && [ -f "$SUDO" ] || skip "yubiOS PAM stacks not found"
}

line_of() { grep -nE "$2" "$1" | head -1 | cut -d: -f1; }

@test "system-auth: pam_u2f is required (touch always enforced), not sufficient" {
  run grep -Eq '^auth[[:space:]]+required[[:space:]]+pam_u2f\.so' "$SA"
  [ "$status" -eq 0 ]
}

@test "system-auth: pam_u2f uses central authfile + cue + matching origin" {
  l="$(grep -E 'pam_u2f\.so' "$SA")"
  [[ "$l" == *"authfile=/etc/yubico/u2f_keys"* ]]
  [[ "$l" == *"cue"* ]]
  [[ "$l" == *"origin=pam://yubiOS"* ]]
}

@test "system-auth: classic auth stack terminates in pam_deny.so" {
  run grep -Eq '^auth[[:space:]]+required[[:space:]]+pam_deny\.so' "$SA"
  [ "$status" -eq 0 ]
}

@test "system-auth: homed short-circuit comes before the classic pam_u2f line" {
  homed="$(line_of "$SA" 'pam_systemd_home\.so')"
  u2f="$(line_of "$SA" 'pam_u2f\.so')"
  [ -n "$homed" ] && [ -n "$u2f" ]
  [ "$homed" -lt "$u2f" ]
}

@test "system-auth: pam_u2f precedes pam_unix (2nd factor before password)" {
  u2f="$(line_of "$SA" '^auth.*pam_u2f\.so')"
  unix="$(line_of "$SA" '^auth.*pam_unix\.so')"
  [ -n "$u2f" ] && [ -n "$unix" ]
  [ "$u2f" -lt "$unix" ]
}

@test "sudo: pam_u2f required and placed before 'include system-auth'" {
  u2f="$(line_of "$SUDO" '^auth[[:space:]]+required[[:space:]]+pam_u2f\.so')"
  inc="$(line_of "$SUDO" '^auth[[:space:]]+include[[:space:]]+system-auth')"
  [ -n "$u2f" ] && [ -n "$inc" ]
  [ "$u2f" -lt "$inc" ]
}

@test "pam-u2f >= 1.3.1 floor (CVE-2025-23013) documented in the stack" {
  run grep -Eq '1\.3\.1' "$SA" "$SUDO"
  [ "$status" -eq 0 ]
}

@test "pamtester smoke (optional, needs module+user; skips otherwise)" {
  command -v pamtester >/dev/null || skip "pamtester not installed"
  skip "live pam_u2f auth needs a real YubiKey + enrolled user; run on hardware"
}
