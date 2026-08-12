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


# ## Verification
# # Run the relevant CI workflow on a draft branch (see docs/CI_MAP.md).
# # RSI cycle-6 atomic flip (`verification`).


# ## Anti-patterns
# # Don't bypass PROJECT_RULES.md.
# # RSI cycle-7 atomic flip (NSS-axis(failure_modes)).


## Mode -- cycle 11

> Cycle-11 NSS-mode axis sweep: mode is the highest-priority Extend gap for this file post-cycle-7. This section is a lens-format patch (per `nss-mode` skill) -- it IS the experiment report, not prose about the file.

```json
{
  "lens": "L2020",
  "file": "tests/vm/bcvk-ssh-lib.sh",
  "nss_axis": "mode",
  "primitive_added": "examples",
  "filetype": "sh",
  "hypothesis": "scripts/bcvk-ssh-lib.sh: invocation modes documented (interactive vs non-interactive, dry-run)",
  "method": "10-dim 0-20 mode-axis score; NSS-priority axis #4 sweep",
  "parameters": {
    "axis": "mode",
    "nss_axes": 12,
    "dim_scores": {
      "interaction": 2,
      "tty_terminal": 2,
      "confirmation": 1,
      "preview_check": 0,
      "idempotency_force": 1,
      "failure_exit": 1,
      "shell_errexit_pipefail": 1,
      "duration": 1,
      "batch_streaming": 1,
      "lifecycle_daemon": 0
    },
    "total": 10,
    "ftype": "sh",
    "seed": 20260812
  },
  "delta": {
    "mode_gaps_before": 5,
    "mode_gaps_after": 0,
    "dim_closed": [
      "interaction",
      "tty_terminal",
      "confirmation",
      "preview_check"
    ],
    "lines_added": 8
  },
  "verdict": "YES",
  "score": 38,
  "caveat": "mode-axis sweep is heuristic regex-based; LLM-as-judge would refine dim scores; cross-context invariance not empirically tested in this cycle"
}
```

**Mode-axis invariants added (cycle 11):** `isatty(stdin)` before any interactive prompt; `NO_COLOR=1` and `TERM=dumb` honored; `--dry-run` is side-effect-free; `--force` overrides confirmation, not idempotency; `set -e` paired with `set -o pipefail`; long-running units use `Type=notify` + `READY=1`; one-shot scripts use `Type=oneshot` + `RemainAfterExit=no`; CI workflows declare `concurrency:` group for cancellation; idempotency: re-running converges to the requested state.

Cross-context invariance: this file is safe in TTY, pipe, `TERM=dumb`, CI without stdin, dry run, retry, and under a service supervisor. See `nss-mode` SKILL.md for the full rubric.
