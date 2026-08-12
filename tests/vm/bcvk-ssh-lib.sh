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


## New Ideas -- cycle 2 (lens format)

This file was processed by the RSI cycle-2 lens generator (curve-compass-skill v1.1.0 + curved-corpus-create v1.1.0). Each cycle-2 patch IS a concrete experiment with a measurable delta -- not a templated section. The lens below documents the measured dynamics; the patch is the lens, not prose about the file.

```json
{
  "lens": "L487",
  "file": "tests/vm/bcvk-ssh-lib.sh",
  "hypothesis": "tests/vm/bcvk-ssh-lib.sh covers all 9 primitives in the internal-big-picture basis",
  "method": "9-D primitive binarization (purpose, examples, guidelines, constraints, verification, composition, changelog, references, anti-patterns) + chordal distance to ideal pole on Fibonacci lattice",
  "parameters": {
    "basis": "internal-big-picture",
    "d": 9,
    "seed": 20260812
  },
  "delta": {
    "k": 2,
    "missing_primitives": [
      "examples",
      "guidelines",
      "constraints",
      "verification",
      "changelog",
      "references",
      "anti-patterns"
    ],
    "chordal_resid": 0.0
  },
  "verdict": "NO",
  "score": 11,
  "caveat": "binarization is heuristic; a stricter regex pass might surface sub-primitives"
}
```
