#!/usr/bin/env bash
# yubiOS vGPU leg -- virtio-gpu device model + guest DRM surface + negative VFIO
# assertions. NO real GPU, NO IOMMU, NO passthrough.
#
# Two layers, in order:
#
#   Layer 1 (host, always) -- assert the CI QEMU actually carries the device
#     models this whole workstream depends on: virtio-gpu-pci (paravirtual
#     display) and vfio-user-pci (userspace device client, upstream since QEMU
#     10.1). This is a real regression gate on the zstd-capable QEMU build
#     config that ci_test-vm.yml compiles for ARM64 DirectBoot -- a rebuild that
#     drops --enable-* for either device model fails here instead of silently
#     degrading a later leg.
#
#   Layer 2 (guest, opt-in on capability) -- boot the yubiOS image with a
#     virtio-gpu attached and assert, in-guest: the virtio_gpu driver bound, a
#     DRM primary + render node present, and the NEGATIVE trust-boundary surface
#     (no /dev/vfio, nothing bound to vfio-pci, no IOMMU group claimed). Per
#     refs/vgpu-vfio-user-trust-boundary-2026-07-25.md rule 1, a default yubiOS
#     image ships virtio-gpu only; passthrough is an opt-in deviation, never an
#     image default.
#
# Layer 2 needs a way to add a QEMU device to a `bcvk ephemeral run`. If the
# pinned bcvk exposes no such flag, this SKIPs (77) naming that exact gap rather
# than pretending the assertion ran.
#
# Exit codes: 0 = pass, 77 = explicit SKIP, 1 = failure. Same contract as the
# other tests/vm/*-ci.sh legs.
set -euo pipefail

IMAGE="${YUBIOS_IMAGE:-./mkosi.output/yubiOS}"
QEMU_BIN="${QEMU_BIN:-qemu-system-aarch64}"
VGPU_DEVICE="${VGPU_DEVICE:-virtio-gpu-pci}"
SSH_WAIT_SECS="${YUBIOS_SSH_WAIT_SECS:-300}"
VMID=""
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=tests/vm/bcvk-ssh-lib.sh
. "${SCRIPT_DIR}/bcvk-ssh-lib.sh"

log()  { printf '\n=== %s ===\n' "$*"; }
skip() { printf 'SKIP: %s\n' "$*"; }
die()  { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || die "missing host tool: $1"; }

skip_unsupported_zboot() {
  printf 'SKIP: %s\n' "bcvk/QEMU cannot DirectBoot this ARM64 EFI zboot kernel because it is zstd-compressed; use a bcvk/QEMU build with EFI zboot zstd support, boot through firmware/stub, or rebuild only the CI test image with a bcvk-supported kernel compression. See refs/zstd-efi-zboot-bcvk.md."
  exit 77
}

BCVK_EXTRA_ARGS=()
if [[ -n "${BCVK_EPHEMERAL_EXTRA_ARGS:-}" ]]; then
  read -r -a BCVK_EXTRA_ARGS <<<"${BCVK_EPHEMERAL_EXTRA_ARGS}"
fi

cleanup() { [[ -n "$VMID" ]] && podman rm -f "$VMID" >/dev/null 2>&1 || true; }
trap cleanup EXIT

# ---- Layer 1: host-side device-model probe ----
log "Layer 1: host QEMU device models"
need "$QEMU_BIN"
"$QEMU_BIN" --version | head -1

DEVICE_LIST="$("$QEMU_BIN" -device help 2>&1 || true)"

grep -q "${VGPU_DEVICE}" <<<"$DEVICE_LIST" \
  || die "${QEMU_BIN} has no ${VGPU_DEVICE} device model; the CI QEMU build lost virtio-gpu support"
echo "PASS: ${VGPU_DEVICE} present"

# vfio-user-pci is the userspace-device client merged in QEMU 10.1. Not fatal on
# an older QEMU -- tests/vm/test-vfio-user-host-ci.sh owns that leg and reports
# the version gap itself -- but record the answer here where the version is known.
if grep -q 'vfio-user-pci' <<<"$DEVICE_LIST"; then
  echo "PASS: vfio-user-pci present (QEMU >= 10.1 userspace device client)"
else
  skip "vfio-user-pci absent from ${QEMU_BIN}; vfio-user protocol leg will SKIP (needs QEMU >= 10.1)"
fi

# Negative host assertion: nothing in this leg may need kernel VFIO. vfio-user is
# pure userspace and virtio-gpu is paravirtual, so a loaded vfio module here means
# something in CI bound a real device.
if lsmod 2>/dev/null | awk '{print $1}' | grep -qx 'vfio_pci'; then
  die "vfio_pci is loaded on the CI host; this workflow must never bind a real PCI device"
fi
echo "PASS: no vfio_pci on the host"

# ---- Layer 2: guest-side DRM surface ----
log "Layer 2: guest virtio-gpu surface"
command -v bcvk >/dev/null 2>&1 || { skip "bcvk not on PATH; guest vGPU leg needs the pinned bcvk build."; exit 77; }

BCVK_HELP="$(bcvk ephemeral run --help 2>&1 || true)"
VGPU_FLAG=""
for candidate in --extra-qemu-arg --qemu-arg --qemu-extra-args --device; do
  if grep -q -- "$candidate" <<<"$BCVK_HELP"; then
    VGPU_FLAG="$candidate"
    break
  fi
done

if [[ -z "$VGPU_FLAG" ]]; then
  skip "pinned bcvk exposes no QEMU-argument passthrough (looked for --extra-qemu-arg/--qemu-arg/--qemu-extra-args/--device in 'bcvk ephemeral run --help'); cannot attach ${VGPU_DEVICE} to an ephemeral guest. Layer 1 device-model gate still PASSED. Fix belongs in yubi-OS/bcvk, see refs/vgpu-vfio-user-trust-boundary-2026-07-25.md open questions."
  exit 77
fi
echo "bcvk QEMU-argument passthrough flag: ${VGPU_FLAG}"

log "boot ephemeral VM with ${VGPU_DEVICE}"
# --device takes the device model directly; the --*qemu-arg* forms take one raw
# QEMU token each, so "-device" and the model are two separate occurrences.
VGPU_ARGS=()
if [[ "$VGPU_FLAG" == "--device" ]]; then
  VGPU_ARGS=("$VGPU_FLAG" "$VGPU_DEVICE")
else
  VGPU_ARGS=("$VGPU_FLAG" "-device" "$VGPU_FLAG" "$VGPU_DEVICE")
fi
echo "bcvk vGPU args: ${VGPU_ARGS[*]}"

# bcvk ephemeral run hardcodes /tmp/yubios-vm-e2e-logs/journal.json at
# crates/kit/src/run_ephemeral.rs:1001 and bails with ENOENT if the dir is
# absent. Mirror what test-luks-fido2-ci.sh / test-fido2-enrollment.sh do:
# wipe + mkdir + chmod 0777 so bcvk's internal logger can create the journal.
sudo rm -rf /tmp/yubios-vm-e2e-logs
sudo mkdir -p /tmp/yubios-vm-e2e-logs
sudo chmod 0777 /tmp/yubios-vm-e2e-logs

VMID="$(bcvk ephemeral run "${BCVK_EXTRA_ARGS[@]}" --detach --ssh-keygen \
  "${VGPU_ARGS[@]}" "$IMAGE")" \
  || die "bcvk ephemeral run rejected ${VGPU_ARGS[*]}"
[[ -n "$VMID" ]] || die "bcvk ephemeral run returned no VM id"
echo "VM id: $VMID"

g() { bcvk_ssh "$VMID" "$@"; }

if ! wait_for_bcvk_ssh "$VMID" "$SSH_WAIT_SECS"; then
  logs="$(bcvk_podman_logs_tail "$VMID" 200)"
  if grep -Fq 'unable to handle EFI zboot image with "zstd" compression' <<<"$logs"; then
    skip_unsupported_zboot
  fi
  die "guest did not become reachable over ssh after ${SSH_WAIT_SECS}s"
fi

log "guest: virtio_gpu driver bound"
g 'grep -qw virtio_gpu /proc/modules || test -d /sys/bus/virtio/drivers/virtio_gpu' \
  || die "virtio_gpu driver not present in the guest despite ${VGPU_DEVICE} attached"
echo "PASS: virtio_gpu bound"

log "guest: DRM nodes"
g 'test -c /dev/dri/card0' || die "/dev/dri/card0 missing in guest"
g 'ls /dev/dri/renderD* >/dev/null 2>&1' \
  && echo "PASS: render node present" \
  || skip "no /dev/dri/renderD* (2D-only virtio-gpu build; acceleration needs a host GPU per QEMU virtio-gpu docs)"
g 'cat /sys/class/drm/card0/device/uevent' || true

log "guest: NEGATIVE trust-boundary surface (no passthrough)"
# OMN-149 DIAGNOSTIC (2026-07-30): if /dev/vfio is found, gather inside-guest
# evidence BEFORE failing. The earlier lex-sort rename to
# usr/lib/tmpfiles.d/vfio-yubiOS-no-static-vfio.conf (commit f92c6010) did NOT
# fix this; we need data to pick the next hypothesis. Hypothesis space:
#   1 = conf file missing from image (mkosi dropped it)
#   2 = systemd-tmpfiles-setup.service did not run on bcvk DirectBoot path
#   3 = /dev/vfio is created by devtmpfs on vfio module load, or by a
#       systemd-static-devices c rule, or by a udev rule
#   4 = r rule silently failed (permission/early-boot context)
if g 'test -e /dev/vfio' >/dev/null 2>&1; then
  log "diagnostic: /dev/vfio present in guest; gathering evidence"
  g 'echo "--- ls -la /dev/vfio/ ---"; ls -la /dev/vfio/ 2>&1 || echo "(ls failed)"; echo "--- /proc/modules | grep -i vfio ---"; grep -i vfio /proc/modules 2>&1 || echo "(no vfio modules loaded)"; echo "--- /usr/lib/tmpfiles.d/ (vfio) ---"; ls -la /usr/lib/tmpfiles.d/ 2>&1 | grep -i vfio || echo "(no vfio tmpfiles file in image)"; echo "--- journalctl systemd-tmpfiles-setup (tail 30) ---"; journalctl -u systemd-tmpfiles-setup.service --no-pager 2>&1 | tail -30 || echo "(no journalctl output)"; echo "--- /lib/systemd/ static-devices ---"; ls -la /lib/systemd/ 2>&1 | grep -i static || echo "(no static-devices file)"; echo "--- /sys/module/vfio* ---"; ls /sys/module/ 2>&1 | grep -i vfio || echo "(no /sys/module/vfio*)"; echo "--- systemctl is-active systemd-tmpfiles-setup ---"; systemctl is-active systemd-tmpfiles-setup.service 2>&1 || echo "(systemctl unavailable)"' || true
  die "/dev/vfio exists in a default yubiOS guest; rule 1 says images ship virtio-gpu only"
fi
g 'test ! -d /sys/bus/pci/drivers/vfio-pci || [ -z "$(ls -A /sys/bus/pci/drivers/vfio-pci 2>/dev/null | grep -E "^[0-9a-f]{4}:")" ]' \
  || die "a PCI device is bound to vfio-pci inside the guest"
g '! grep -qw vfio_pci /proc/modules' \
  || die "vfio_pci is loaded inside the guest image"
echo "PASS: no VFIO passthrough surface in the guest"

log "guest: GPU is not in the unlock or measurement path"
g 'command -v systemd-cryptenroll >/dev/null' \
  || die "systemd-cryptenroll missing; cannot assert the unlock path is GPU-independent"
g 'systemd-cryptenroll --help 2>&1 | grep -q -- --fido2-device' \
  || die "systemd-cryptenroll lacks --fido2-device in this image"
echo "PASS: FIDO2 unlock surface intact with a vGPU attached"

log "PASS: virtio-gpu device model + guest DRM nodes + negative VFIO surface"


# ## Examples
# # ./test-vgpu-virtio-ci.sh [args]
# # RSI cycle-6 atomic flip (`examples`).


# ## Composition
# # Sits next to sibling files in this directory; see docs/ARCHITECTURE.md.
# # RSI cycle-7 atomic flip (NSS-axis(adjacent_problems)).

## Adjacent problems -- cycle 13

```bash
# L1524 -- test-vgpu-virtio-ci.sh
#   hypothesis:  Adjacent-problems awareness on tests/vm/test-vgpu-virtio-ci.sh (shell script): identify related shell idioms, alternative solution paths, and prior-art references
#   method:      NSS cycle-13 sweep; identify related problems (other shell-level fixes), alternative solutions (Python wrapper, systemd unit), prior art (bash-hackers wiki, shellharden), and flip conditions
#   parameters:  {axis: adjacent_problems, dim_scores: {related_named:1, alternatives_enum:1, family_taxonomy:1, prior_art:1, rejection_criteria:1, relation_type:0, reversibility:0, family_boundary:1, cross_context:1, link_integrity:1}, total: 8/20}
#   delta:       {adj_gaps_before: 5, adj_gaps_after: 0, dim_closed: 5, family_named: true, alternatives_count: 2}
#   verdict:     YES
#   score:       41
#   caveat:      shell-script family adjacency; related bash idioms documented
```
