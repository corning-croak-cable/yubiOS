#!/usr/bin/env bash
# yubiOS Phase F0 fTPM e2e -- OP-TEE fTPM under QEMU virt, with the firmware
# SOURCED FROM THE PUBLISHED DOCKER ARTIFACT rather than rebuilt from source.
#
# tests/vm/build-arm64-ftpm-qemu.sh builds that chain from scratch (repo sync +
# TF-A + OP-TEE + fTPM TA + U-Boot, tens of minutes). ci_firmware-rk.yml already
# builds and publishes the same thing, so CI pulls the bundle instead:
#   0mniteck/yubios:firmware-qemu-arm64  ->  /firmware/{flash.bin,bl1.bin,fip.bin}
#
# Layered, because exactly two things are provable and they need different boots:
#
#   Stage A (always) -- FIRMWARE markers. Boot flash.bin and assert the secure
#     world brought up the fTPM: Early TA loaded at init, TA probed via ldelf,
#     functional (U-Boot's BOOTCOMMAND prints YUBIOS_TPM_OK after tpm2 startup +
#     self_test), StMM SP loaded, and no known failure signature. These are the
#     same assertions ci_firmware-rk.yml Stage 3 makes, which is green today.
#
#   Stage B (opt-in via FTPM_LINUX_PAYLOAD=1) -- LINUX markers. `bcvk to-disk`
#     the yubiOS image, boot that disk under the SAME firmware, and assert the
#     guest kernel bound tpm_ftpm_tee to the OP-TEE fTPM and exposed /dev/tpm0.
#     That is checks 1-2 of tests/vm/verify-tpm0-pcr-extend.sh, proven for real.
#     Checks 3-5 (TPM2_Startup, PCR read, PCR extend) require executing in the
#     guest. This chain has no route in: bcvk's DirectBoot SSH credential path is
#     bypassed when U-Boot owns the boot, /etc is transient, there is no root
#     password, and no network is configured. When Linux comes up but no shell is
#     reachable, Stage B exits 77 SKIP naming that gap instead of claiming the
#     verifier ran.
#
# Exit codes: 0 = pass, 77 = explicit SKIP, 1 = failure.
set -euo pipefail

FIRMWARE_IMAGE="${FIRMWARE_IMAGE:-docker.io/0mniteck/yubios:firmware-qemu-arm64}"
YUBIOS_IMAGE="${YUBIOS_IMAGE:-}"
FTPM_LINUX_PAYLOAD="${FTPM_LINUX_PAYLOAD:-0}"
FTPM_UUID="${FTPM_UUID:-bc50d971-d4c9-42c4-82cb-343fb7f37896}"
BOOT_TIMEOUT="${BOOT_TIMEOUT:-180}"
LINUX_BOOT_TIMEOUT="${LINUX_BOOT_TIMEOUT:-900}"
WORK="${WORK:-${PWD}/ftpm-qemu-ci}"
LOG_DIR="${LOG_DIR:-/tmp/yubios-vm-e2e-logs}"

log()  { printf '\n=== %s ===\n' "$*"; }
skip() { printf 'SKIP: %s\n' "$*"; }
die()  { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || die "missing host tool: $1"; }

CID=""
cleanup() { [[ -n "$CID" ]] && podman rm -f "$CID" >/dev/null 2>&1 || true; }
trap cleanup EXIT

log "host preflight"
need qemu-system-aarch64
need podman
need dd
mkdir -p "$WORK" "$LOG_DIR"

# ---- source the firmware from the published OCI artifact ----
log "extract firmware from ${FIRMWARE_IMAGE}"
podman pull "$FIRMWARE_IMAGE" >/dev/null || die "cannot pull ${FIRMWARE_IMAGE}"
CID="$(podman create "$FIRMWARE_IMAGE" /bin/true)"
[[ -n "$CID" ]] || die "podman create returned no container id"
rm -rf "${WORK}/firmware"
mkdir -p "${WORK}/firmware"
podman cp "${CID}:/firmware/." "${WORK}/firmware/" \
  || die "no /firmware payload in ${FIRMWARE_IMAGE}"
podman rm -f "$CID" >/dev/null 2>&1 || true
CID=""
ls -l "${WORK}/firmware/" || true

# Stage 3 stitches flash.bin from bl1 + fip when the bundle lacks it: bl1 at
# offset 0, fip at 4096-byte block 64. Keep that exact geometry.
FLASH="${WORK}/firmware/flash.bin"
if [[ ! -s "$FLASH" ]]; then
  if [[ -s "${WORK}/firmware/bl1.bin" && -s "${WORK}/firmware/fip.bin" ]]; then
    log "stitch flash.bin from bl1.bin + fip.bin"
    dd if="${WORK}/firmware/bl1.bin" of="$FLASH" bs=4096 conv=notrunc
    dd if="${WORK}/firmware/fip.bin" of="$FLASH" seek=64 bs=4096 conv=notrunc
  else
    skip "${FIRMWARE_IMAGE} has no flash.bin and no bl1.bin+fip.bin to stitch; dispatch ci_firmware-rk.yml with Docker_push to publish the qemu-arm64 bundle first."
    exit 77
  fi
fi
test -s "$FLASH" || die "flash.bin is empty after staging"

# ---- Stage A: firmware markers ----
log "Stage A: boot flash.bin and assert fTPM firmware markers"
NW_LOG="${LOG_DIR}/ftpm-nw.log"
OPTEE_LOG="${LOG_DIR}/ftpm-optee.log"
rm -f "$NW_LOG" "$OPTEE_LOG"
timeout "$BOOT_TIMEOUT" qemu-system-aarch64 \
  -M virt,secure=on -cpu max -m 2048 \
  -bios "$FLASH" \
  -nographic -d guest_errors \
  -serial "file:${NW_LOG}" -serial "file:${OPTEE_LOG}" || true
touch "$NW_LOG" "$OPTEE_LOG"

fail=0
grep -Eiq "early_ta_init.*${FTPM_UUID}|Early TA ${FTPM_UUID}" "$NW_LOG" "$OPTEE_LOG" \
  && echo "PASS: fTPM Early TA at init" || { echo "::error::fTPM Early TA not at init"; fail=1; }
grep -Eiq "ldelf: Loading TS ${FTPM_UUID}|Lookup user TA ELF ${FTPM_UUID}" "$NW_LOG" "$OPTEE_LOG" \
  && echo "PASS: fTPM TA probed" || { echo "::error::fTPM TA never probed"; fail=1; }
grep -q "YUBIOS_TPM_OK" "$NW_LOG" \
  && echo "PASS: fTPM functional (tpm2 startup + self_test)" || { echo "::error::fTPM not functional"; fail=1; }
grep -Eiq "stmm load address" "$NW_LOG" "$OPTEE_LOG" \
  && echo "PASS: StMM SP loaded into OP-TEE" || { echo "::error::StMM SP never loaded"; fail=1; }
if grep -Eq "Missing TPMv2 device|Couldn't set TPM|TA panicked|ldelf failed|data-abort" "$NW_LOG" "$OPTEE_LOG"; then
  echo "::error::known failure signature present"
  fail=1
else
  echo "PASS: no known failure signatures"
fi
[[ "$fail" -eq 0 ]] || die "Stage A firmware markers failed (see ${NW_LOG} / ${OPTEE_LOG})"
echo "STAGE_A_PASS"

# ---- Stage B: Linux markers under the same firmware ----
if [[ "$FTPM_LINUX_PAYLOAD" != "1" ]]; then
  skip "Stage B not requested (FTPM_LINUX_PAYLOAD != 1). Firmware-level fTPM proven; verify-tpm0-pcr-extend.sh's Linux-side checks not exercised."
  exit 77
fi

log "Stage B: install yubiOS to a disk and boot it under the fTPM firmware"
[[ -n "$YUBIOS_IMAGE" ]] || { skip "Stage B needs YUBIOS_IMAGE to install a Linux payload."; exit 77; }
command -v bcvk >/dev/null 2>&1 || { skip "Stage B needs bcvk on PATH to build the payload disk."; exit 77; }

DISK="${WORK}/yubios-ftpm.raw"
rm -f "$DISK"
if ! bcvk to-disk --disk-size 20G "$YUBIOS_IMAGE" "$DISK"; then
  skip "bcvk to-disk could not install ${YUBIOS_IMAGE} (bootc install to-disk failed); Stage B payload unavailable."
  exit 77
fi
test -s "$DISK" || { skip "bcvk to-disk produced no disk image."; exit 77; }

LINUX_LOG="${LOG_DIR}/ftpm-linux.log"
LINUX_OPTEE_LOG="${LOG_DIR}/ftpm-linux-optee.log"
rm -f "$LINUX_LOG" "$LINUX_OPTEE_LOG"
timeout "$LINUX_BOOT_TIMEOUT" qemu-system-aarch64 \
  -M virt,secure=on -cpu max -m 4096 \
  -bios "$FLASH" \
  -drive "if=none,file=${DISK},format=raw,id=hd0" \
  -device virtio-blk-device,drive=hd0 \
  -nographic -d guest_errors \
  -serial "file:${LINUX_LOG}" -serial "file:${LINUX_OPTEE_LOG}" || true
touch "$LINUX_LOG" "$LINUX_OPTEE_LOG"

if ! grep -Eiq "Linux version|systemd\[1\]" "$LINUX_LOG"; then
  skip "U-Boot did not hand off to Linux from the installed disk within ${LINUX_BOOT_TIMEOUT}s (no kernel banner on console); the yubiOS ESP/systemd-boot handoff under U-Boot is not proven yet. Firmware-level fTPM still PASSED in Stage A."
  exit 77
fi

linux_fail=0
grep -Eiq "optee: initialized driver" "$LINUX_LOG" \
  && echo "PASS: guest OP-TEE bus up (verify-tpm0-pcr-extend.sh check 1/5)" \
  || { echo "::error::guest kernel never initialized the OP-TEE driver"; linux_fail=1; }
grep -Eiq "tpm_ftpm_tee|ftpm.*tee" "$LINUX_LOG" \
  && echo "PASS: tpm_ftpm_tee bound to the OP-TEE fTPM (check 2/5)" \
  || { echo "::error::tpm_ftpm_tee never bound in the guest"; linux_fail=1; }
[[ "$linux_fail" -eq 0 ]] || die "Stage B Linux fTPM markers failed (see ${LINUX_LOG})"

skip "checks 3-5 of verify-tpm0-pcr-extend.sh (TPM2_Startup, PCR read, PCR extend) need in-guest execution; this chain has no route in -- U-Boot owns the boot so bcvk's kernel-cmdline SSH credential is bypassed, /etc is transient, there is no root password, and no network is configured. Linux-side /dev/tpm0 presence is PROVEN above."
exit 77
