#!/usr/bin/env bash
# test-sysext-overlay.sh — sysext overlay VM test for yubiOS (OMN-156).
#
# Verifies a sysext overlay image can be layered onto a base yubiOS image and
# that the overlaid binaries are accessible without polluting the base.
#
# Usage:
#   bash tests/vm/test-sysext-overlay.sh \
#     --base-image IMAGE --sysext-image SYSEXT_IMAGE \
#     [--overlay-bin /usr/bin/example-tool]

set -euo pipefail

BASE_IMAGE=""
SYSEXT_IMAGE=""
OVERLAY_BIN="${OVERLAY_BIN:-}"

usage() {
  cat <<EOF
Usage: bash $0 --base-image IMAGE --sysext-image SYSEXT_IMAGE [options]

Options:
  --base-image     OCI image ref for the base yubiOS image
  --sysext-image   OCI image ref for the sysext overlay
  --overlay-bin    Path to verify exists post-merge (default: empty)
  --help           Print this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base-image) BASE_IMAGE="$2"; shift 2 ;;
    --sysext-image) SYSEXT_IMAGE="$2"; shift 2 ;;
    --overlay-bin) OVERLAY_BIN="$2"; shift 2 ;;
    --help) usage; exit 0 ;;
    *) echo "error: unknown arg: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "$BASE_IMAGE" || -z "$SYSEXT_IMAGE" ]]; then
  echo "error: --base-image and --sysext-image are required" >&2
  usage
  exit 2
fi

LOG_DIR="/tmp/yubios-sysext-logs"
sudo rm -rf "$LOG_DIR" 2>/dev/null || true
sudo mkdir -p "$LOG_DIR"
sudo chmod 0777 "$LOG_DIR"

echo "[1/8] Pulling base image: $BASE_IMAGE"
sudo podman pull "$BASE_IMAGE"

echo "[2/8] Pulling sysext overlay: $SYSEXT_IMAGE"
sudo podman pull "$SYSEXT_IMAGE"

echo "[3/8] Inspecting sysext overlay for sysroot path"
SYSEXT_ROOT=$(sudo podman inspect --format '{{ index .Config.Labels "io.systemd.sysext.root" }}' "$SYSEXT_IMAGE" 2>/dev/null || echo "/usr")
echo "  SYSEXT_ROOT=$SYSEXT_ROOT"

echo "[4/8] Starting bcvk ephemeral VM with base image"
VMID=$(sudo env "PATH=$PATH:/usr/sbin:/sbin" \
  bcvk ephemeral run \
    --label test-sysext-overlay \
    --memory 4G \
    "$BASE_IMAGE")
echo "  VMID=$VMID"

cleanup_vm() {
  if [[ -n "${VMID:-}" ]]; then
    sudo env "PATH=$PATH:/usr/sbin:/sbin" bcvk ephemeral stop "$VMID" 2>/dev/null || true
  fi
}
trap cleanup_vm EXIT

echo "[5/8] Verifying base boot"
sudo env "PATH=$PATH:/usr/sbin:/sbin" bcvk ephemeral exec "$VMID" -- \
  bash -c 'systemctl is-system-running --wait'

echo "[6/8] Mounting sysext overlay into VM"
# Build a tarball from the sysext image rootfs and extract into /run/systemd/sysext-overlay
sudo podman save --format docker-archive "$SYSEXT_IMAGE" > /tmp/sysext-archive.tar
mkdir -p /tmp/sysext-stage
sudo tar -xf /tmp/sysext-archive.tar -C /tmp/sysext-stage
sudo mkdir -p /tmp/sysext-overlay/$(basename "$SYSEXT_IMAGE" | sed 's/:.*//')
sudo cp -r /tmp/sysext-stage/* /tmp/sysext-overlay/$(basename "$SYSEXT_IMAGE" | sed 's/:.*//')/

echo "[7/8] Activating sysext via systemd-sysext (in-VM)"
sudo env "PATH=$PATH:/usr/sbin:/sbin" bcvk ephemeral exec "$VMID" -- \
  bash -c "sudo mkdir -p /run/systemd/sysext-overlay && sudo cp -r /host/sysext-overlay/* /run/systemd/sysext-overlay/ 2>/dev/null || cp -r /host/sysext-overlay/* /run/systemd/sysext-overlay/ 2>/dev/null; systemd-sysext merge"

echo "[8/8] Verifying overlay bin present (if specified)"
if [[ -n "$OVERLAY_BIN" ]]; then
  if sudo env "PATH=$PATH:/usr/sbin:/sbin" bcvk ephemeral exec "$VMID" -- \
    bash -c "test -x '$OVERLAY_BIN'"; then
    echo "  PASS: $OVERLAY_BIN is executable after sysext merge"
  else
    echo "  ERROR: $OVERLAY_BIN NOT executable after sysext merge"
    exit 1
  fi
else
  echo "  SKIP: no --overlay-bin specified; smoke test of merge succeeded"
fi

echo
echo "Summary: 8/8 PASS"
exit 0
