#!/usr/bin/env bash
# Shared bcvk SSH wait and diagnostics helpers for tests/vm/*.sh.

bcvk_podman_logs_tail() {
  local vmid="$1"
  local lines="${2:-160}"
  podman logs --tail "$lines" "$vmid" 2>&1 || true
}

dump_bcvk_ssh_diagnostics() {
  local vmid="$1"

  echo "--- bcvk ssh stderr (single probe) ---"
  bcvk ssh "$vmid" -- true 2>&1 || true

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
  local i

  [ "$tries" -gt 0 ] || tries=1
  for i in $(seq 1 "$tries"); do
    bcvk ssh "$vmid" -- true >/dev/null 2>&1 && return 0
    sleep 2
  done

  dump_bcvk_ssh_diagnostics "$vmid"
  return 1
}
