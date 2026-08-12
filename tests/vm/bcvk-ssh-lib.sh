#!/usr/bin/env bash
# Shared bcvk SSH wait and diagnostics helpers for tests/vm/*.sh.

bcvk_podman_logs_tail() {
  local vmid="$1"
  local lines="${2:-160}"
  podman logs --tail "$lines" "$vmid" 2>&1 || true
}

# bcvk's SSH transport is an ssh client inside the outer VM container. Keep
# the probe and guest-command path here so callers do not accidentally use the
# nonexistent top-level `bcvk ssh` command (the public CLI is nested under
# `bcvk ephemeral`, and adds its own readiness wait around every invocation).
bcvk_ssh() {
  local vmid="$1"
  shift

  podman exec -- "$vmid" ssh \
    -i /run/tmproot/var/lib/bcvk/ssh \
    -o IdentitiesOnly=yes \
    -o PasswordAuthentication=no \
    -o KbdInteractiveAuthentication=no \
    -o GSSAPIAuthentication=no \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -o BatchMode=yes \
    -o ConnectTimeout=2 \
    -o ServerAliveInterval=60 \
    -o LogLevel=ERROR \
    -p 2222 root@127.0.0.1 -- "$@"
}

dump_bcvk_ssh_diagnostics() {
  local vmid="$1"

  echo "--- bcvk container SSH stderr (single probe) ---"
  bcvk_ssh "$vmid" true 2>&1 || true

  echo "--- podman container state ---"
  podman inspect \
    --format 'Status={{.State.Status}} ExitCode={{.State.ExitCode}} Error={{.State.Error}}' \
    -- "$vmid" 2>&1 || true

  echo "--- podman logs (last 160 lines) ---"
  bcvk_podman_logs_tail "$vmid" 160

  echo "--- outer-container SSH path diagnostics ---"
  podman exec -- "$vmid" sh -lc '
    set +e
    echo "key files:"
    ls -la /run/tmproot/var/lib/bcvk /run/tmproot/var/lib/bcvk/ssh* 2>&1
    if [ -r /run/tmproot/var/lib/bcvk/ssh.pub ]; then
      printf "public key: "
      sed -n "1p" /run/tmproot/var/lib/bcvk/ssh.pub
    fi
    echo "listeners:"
    if command -v ss >/dev/null 2>&1; then
      ss -ltnp
    elif command -v netstat >/dev/null 2>&1; then
      netstat -ltnp
    else
      echo "no ss/netstat in outer container"
    fi
    echo "qemu credential transport:"
    qemu_pid="$(pgrep -o -f "[q]emu-system-" 2>/dev/null || true)"
    if [ -n "$qemu_pid" ] && [ -r "/proc/$qemu_pid/cmdline" ]; then
      qemu_cmdline="$(tr "\000" " " < "/proc/$qemu_pid/cmdline")"
      case "$qemu_cmdline" in
        *systemd.set_credential_binary=tmpfiles.extra:*)
          echo "kernel-cmdline credential: present"
          ;;
        *)
          echo "kernel-cmdline credential: absent"
          ;;
      esac
      case "$qemu_cmdline" in
        *io.systemd.credential.binary:tmpfiles.extra=*)
          echo "SMBIOS credential: present"
          ;;
        *)
          echo "SMBIOS credential: absent"
          ;;
      esac
    else
      echo "qemu process: unavailable"
    fi
    echo "ssh -vvv probe:"
    ssh -vvv -i /run/tmproot/var/lib/bcvk/ssh \
      -o IdentitiesOnly=yes \
      -o PasswordAuthentication=no \
      -o KbdInteractiveAuthentication=no \
      -o GSSAPIAuthentication=no \
      -o StrictHostKeyChecking=no \
      -o UserKnownHostsFile=/dev/null \
      -o BatchMode=yes \
      -o ConnectTimeout=5 \
      root@127.0.0.1 -p 2222 true
  ' 2>&1 || true
}

wait_for_bcvk_ssh() {
  local vmid="$1"
  local wait_secs="$2"
  local tries=$((wait_secs / 2))

  [ "$tries" -gt 0 ] || tries=1
  while [ "$tries" -gt 0 ]; do
    bcvk_ssh "$vmid" true >/dev/null 2>&1 && return 0
    tries=$((tries - 1))
    sleep 2
  done

  dump_bcvk_ssh_diagnostics "$vmid"
  return 1
}

# ## Examples
# # Reading the file with no arguments shows the help text.
# # See docs/ARCHITECTURE.md for where this fits in yubiOS.

# ## Guidelines
# # Follow the conventions in docs/STYLE.md. Match the structure of surrounding files.

# ## Constraints
# # Out of scope: changes to papers/ or .github/workflows/*.yml (separate change-management).

# ## Verification
# # Run the relevant CI workflow on a draft branch (see docs/CI_MAP.md); the result is the gate.

# ## Changelog
# # 2026-08-12 -- primitive-closure pass via curve-compass-skill + curved-corpus-create (this PR).

# ## References
# # yubiOS repo: yubi-OS/yubiOS
# # See docs/ARCHITECTURE.md and the two new skills in skills/github-yubios-KS9n5GAT/.

# ## Anti-patterns
# # Don't claim structure without a null (see curved-corpus-create skill).
# # Don't report pi_T statistics as properties of the historical corpus.

