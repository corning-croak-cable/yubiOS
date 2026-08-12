#!/usr/bin/env bats
# Static/unit checks for bcvk VM SSH integration helpers.

SCRIPT="usr/lib/yubiOS/sshd-authorized-keys-bcvk.sh"
CONF="usr/lib/yubiOS/sshd_config.d/10-yubiOS-bcvk-root-key.conf"
VM_LIB="tests/vm/bcvk-ssh-lib.sh"
CONTAINERFILE="Containerfile"
VM_WORKFLOW=".github/workflows/ci_test-vm.yml"
BCVK_ARM64_PATCH=".github/patches/bcvk-arm64-directboot-ssh.patch"

setup() {
  [ -f "$SCRIPT" ] || SCRIPT="/usr/lib/yubiOS/sshd-authorized-keys-bcvk.sh"
  [ -f "$CONF" ] || CONF="/usr/lib/yubiOS/sshd_config.d/10-yubiOS-bcvk-root-key.conf"
}

@test "bcvk ssh authorized-keys command reads direct root ssh credential" {
  tmpdir="$(mktemp -d)"
  key="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBcvkDirectCredential bcvk-test"
  printf '%s\n' "$key" > "$tmpdir/ssh.authorized_keys.root"

  run env CREDENTIALS_DIRECTORY="$tmpdir" bash "$SCRIPT" root
  rm -rf "$tmpdir"

  [ "$status" -eq 0 ]
  [ "$output" = "$key" ]
}

@test "bcvk ssh authorized-keys command decodes root key from tmpfiles credential" {
  tmpdir="$(mktemp -d)"
  key="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCbcvkTest bcvk-test"
  encoded="$(printf '%s' "$key" | base64 -w0)"
  printf 'f+~ /root/.ssh/authorized_keys 700 - - - %s\n' "$encoded" > "$tmpdir/tmpfiles.extra"

  run env CREDENTIALS_DIRECTORY="$tmpdir" bash "$SCRIPT" root
  rm -rf "$tmpdir"

  [ "$status" -eq 0 ]
  [ "$output" = "$key" ]
}

@test "bcvk ssh authorized-keys command is root-only" {
  tmpdir="$(mktemp -d)"
  key="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCbcvkTest bcvk-test"
  encoded="$(printf '%s' "$key" | base64 -w0)"
  printf 'f+~ /root/.ssh/authorized_keys 700 - - - %s\n' "$encoded" > "$tmpdir/tmpfiles.extra"

  run env CREDENTIALS_DIRECTORY="$tmpdir" bash "$SCRIPT" ci
  rm -rf "$tmpdir"

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "sshd config wires bcvk authorized-keys helper for root only" {
  run grep -Fx 'Match User root' "$CONF"
  [ "$status" -eq 0 ]
  run grep -Fx '    AuthorizedKeysCommand /usr/lib/yubiOS/sshd-authorized-keys-bcvk.sh %u' "$CONF"
  [ "$status" -eq 0 ]
  run grep -Fx '    AuthorizedKeysCommandUser root' "$CONF"
  [ "$status" -eq 0 ]
}

@test "Containerfile installs bcvk sshd drop-in into /etc/ssh/sshd_config.d" {
  [ -f "$CONTAINERFILE" ] || skip "repo Containerfile unavailable in installed image context"
  run grep -F '/etc/ssh/sshd_config.d/10-yubiOS-bcvk-root-key.conf' "$CONTAINERFILE"
  [ "$status" -eq 0 ]
}

@test "VM SSH helper prints verbose host-side ssh diagnostics on timeout" {
  [ -f "$VM_LIB" ] || skip "repo VM helper unavailable in installed image context"
  run grep -F 'ssh -vvv' "$VM_LIB"
  [ "$status" -eq 0 ]
  run grep -F 'kernel-cmdline credential: present' "$VM_LIB"
  [ "$status" -eq 0 ]
}

@test "VM SSH helper uses bcvk container transport instead of nonexistent top-level CLI" {
  [ -f "$VM_LIB" ] || skip "repo VM helper unavailable in installed image context"
  run grep -F 'podman exec -- "$vmid" ssh' "$VM_LIB"
  [ "$status" -eq 0 ]
  run grep -F 'bcvk ssh "$vmid"' "$VM_LIB"
  [ "$status" -ne 0 ]

  for vm_test in tests/vm/test-luks-fido2-ci.sh tests/vm/test-fido2-enrollment.sh; do
    run grep -F 'g() { bcvk_ssh "$VMID" "$@"; }' "$vm_test"
    [ "$status" -eq 0 ]
  done
}

@test "VM workflow preserves bcvk tmpfiles root SSH credential" {
  [ -f "$VM_WORKFLOW" ] || skip "repo VM workflow unavailable in installed image context"
  run grep -F 'io.systemd.credential.binary:tmpfiles.extra={encoded}' "$VM_WORKFLOW"
  [ "$status" -eq 0 ]
  run grep -F 'ssh.authorized_keys.root' "$VM_WORKFLOW"
  [ "$status" -ne 0 ]
}

@test "ARM64 DirectBoot passes the bcvk public key through a kernel credential" {
  [ -f "$VM_WORKFLOW" ] || skip "repo VM workflow unavailable in installed image context"
  [ -f "$BCVK_ARM64_PATCH" ] || skip "repo bcvk patch unavailable in installed image context"

  run grep -F '.github/patches/bcvk-arm64-directboot-ssh.patch' "$VM_WORKFLOW"
  [ "$status" -eq 0 ]
  run grep -F 'cargo test --release -p bcvk-qemu test_karg_for_root_ssh' "$VM_WORKFLOW"
  [ "$status" -eq 0 ]
  run grep -F 'cfg!(target_arch = "aarch64")' "$BCVK_ARM64_PATCH"
  [ "$status" -eq 0 ]
  run grep -F 'karg_for_root_ssh(&pubkey)' "$BCVK_ARM64_PATCH"
  [ "$status" -eq 0 ]
  run grep -F 'systemd.set_credential_binary=tmpfiles.extra:' "$BCVK_ARM64_PATCH"
  [ "$status" -eq 0 ]
}


## Verification

- Read `test-bcvk-ssh-unit.bats` end-to-end against this section's claim.
- Run the relevant CI workflow on a draft branch (see `docs/CI_MAP.md`).

_Atomic RSI cycle-6 flip._
