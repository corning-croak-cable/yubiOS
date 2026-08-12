#!/usr/bin/env bash
# Phase F0 — reproducible QEMU 'virt' ARM64 boot chain for yubiOS:
#   TF-A (BL1/BL2/BL31) + OP-TEE (BL32) + ms-tpm-20-ref fTPM Early TA + U-Boot (BL33/UEFI)
# Boots Linux to a live /dev/tpm0. Verify PCR extend with verify-tpm0-pcr-extend.sh inside the guest.
#
# This is a bring-up recipe, not a hardware path. It runs entirely in emulation so the
# RPMB-before-supplicant bootstrap hazard (OP-TEE issue #5766) can be proven before any
# real board. Pin every component; never float a tag.
#
# Refs: skills arm-trusted-firmware-optee + ftpm-optee-tpm; optee.readthedocs.io qemu_v8.
set -euo pipefail

WORK="${WORK:-$PWD/arm64-ftpm-f0}"
JOBS="${JOBS:-$(nproc)}"

# --- Pinned sources (supply chain: fold into Renovate per ADR-015) ---
MSTPM_REF="98b60a44aba79b15fcce1c0d1e46cf5918400f6a"   # ms-tpm-20-ref commit optee_ftpm expects
FTPM_UUID="bc50d971-d4c9-42c4-82cb-343fb7f37896"        # fTPM TA UUID
# OP-TEE qemu_v8 manifest pins TF-A / OP-TEE OS / U-Boot / Linux as a coherent set.
OPTEE_MANIFEST_REF="${OPTEE_MANIFEST_REF:-4.5.0}"        # pin the OP-TEE release manifest tag

# --- Platform identifiers (QEMU virt, aarch64) ---
# OP-TEE OS uses the legacy 'vexpress' name; QEMU runs it as -machine virt.
OPTEE_PLATFORM="vexpress-qemu_armv8a"
TFA_PLAT="qemu"
ARCH="aarch64"

mkdir -p "$WORK"; cd "$WORK"

echo "== 1. Fetch the pinned qemu_v8 component set =="
# Uses the OP-TEE build repo + repo manifest so TF-A/OP-TEE/U-Boot/Linux stay a matched set.
if [ ! -d .repo ]; then
  repo init -u https://github.com/OP-TEE/manifest.git -m qemu_v8.xml -b "refs/tags/$OPTEE_MANIFEST_REF"
fi
repo sync -j"$JOBS" --no-clone-bundle

echo "== 2. Pin ms-tpm-20-ref to the commit optee_ftpm expects =="
if [ ! -d ms-tpm-20-ref ]; then
  git clone https://github.com/microsoft/ms-tpm-20-ref
fi
git -C ms-tpm-20-ref fetch --all
git -C ms-tpm-20-ref checkout "$MSTPM_REF"

echo "== 3. Build the fTPM Early TA against the OP-TEE TA dev kit =="
# Build OP-TEE OS first to produce export-ta_arm64, then build optee_ftpm against it.
make -C optee_os -j"$JOBS" \
  PLATFORM="$OPTEE_PLATFORM" CFG_ARM64_core=y \
  CFG_RPMB_FS=y CFG_RPMB_FS_DEV_ID=0
TA_DEV_KIT="$WORK/optee_os/out/arm-plat-vexpress/export-ta_arm64"

if [ ! -d optee_ftpm ]; then
  git clone https://github.com/OP-TEE/optee_ftpm
fi
make -C optee_ftpm -j"$JOBS" \
  TA_DEV_KIT_DIR="$TA_DEV_KIT" \
  CFG_MS_TPM_20_REF="$WORK/ms-tpm-20-ref" \
  CFG_TA_MEASURED_BOOT=y \
  CFG_TA_EVENT_LOG_SIZE=4096
FTPM_TA="$(find optee_ftpm -name "$FTPM_UUID.stripped.elf" | head -n1)"
[ -n "$FTPM_TA" ] || { echo "fTPM TA not built" >&2; exit 1; }

echo "== 4. Rebuild OP-TEE OS embedding the fTPM as an Early TA =="
# Early TA: alive the instant OP-TEE boots, before any rootfs / tee-supplicant.
make -C optee_os -j"$JOBS" \
  PLATFORM="$OPTEE_PLATFORM" CFG_ARM64_core=y \
  CFG_RPMB_FS=y \
  CFG_EARLY_TA=y \
  EARLY_TA_PATHS="$WORK/$FTPM_TA"

echo "== 5. Build TF-A with OP-TEE as BL32 + U-Boot as BL33, measured boot on =="
make -C trusted-firmware-a -j"$JOBS" \
  PLAT="$TFA_PLAT" ARCH="$ARCH" \
  SPD=opteed \
  BL32="$WORK/optee_os/out/arm-plat-vexpress/core/tee-header_v2.bin" \
  BL32_EXTRA1="$WORK/optee_os/out/arm-plat-vexpress/core/tee-pager_v2.bin" \
  BL32_EXTRA2="$WORK/optee_os/out/arm-plat-vexpress/core/tee-pageable_v2.bin" \
  BL33="$WORK/u-boot/u-boot.bin" \
  MEASURED_BOOT=1 EVENT_LOG_LEVEL=20 \
  all fip

echo "== 6. U-Boot config sanity (fTPM driver + measured boot) =="
# These must be set in the u-boot defconfig used by the manifest:
#   CONFIG_TEE=y CONFIG_OPTEE=y CONFIG_TPM=y CONFIG_TPM_V2=y
#   CONFIG_TPM2_FTPM_TEE=y CONFIG_MEASURED_BOOT=y CONFIG_TPM2_EVENT_LOG_SIZE=0x10000
#   CONFIG_EFI_LOADER=y CONFIG_CMD_BOOTEFI=y  (U-Boot speaks UEFI for the UKI/systemd-boot path)
grep -q CONFIG_TPM2_FTPM_TEE=y u-boot/.config || echo "WARN: enable CONFIG_TPM2_FTPM_TEE in u-boot defconfig"

echo "== 7. Boot QEMU virt =="
# tee-supplicant MUST come up from the initramfs before Linux touches the fTPM, or the
# Early TA's first persistent RPMB write panics (OP-TEE #5766). The qemu_v8 rootfs ships it.
# Linux side needs: CONFIG_TEE=y CONFIG_OPTEE=y CONFIG_TCG_TPM=y CONFIG_TCG_FTPM_TEE=m
#   plus DT node:  tpm { compatible = "microsoft,ftpm"; };
make -C build run-only \
  QEMU_VIRTFS_ENABLE=y \
  || qemu-system-aarch64 -machine virt,secure=on,virtualization=on -cpu cortex-a57 \
       -smp 2 -m 1057 -nographic -no-acpi \
       -bios "$WORK/trusted-firmware-a/build/$TFA_PLAT/release/bl1.bin" \
       -serial mon:stdio -serial file:/dev/stdout

echo ""
echo "== Build complete. In the booted guest run: tests/vm/verify-tpm0-pcr-extend.sh =="


## New Ideas -- cycle 2 (lens format)

This file was processed by the RSI cycle-2 lens generator (curve-compass-skill v1.1.0 + curved-corpus-create v1.1.0). Each cycle-2 patch IS a concrete experiment with a measurable delta -- not a templated section. The lens below documents the measured dynamics; the patch is the lens, not prose about the file.

```json
{
  "lens": "L488",
  "file": "tests/vm/build-arm64-ftpm-qemu.sh",
  "hypothesis": "tests/vm/build-arm64-ftpm-qemu.sh covers all 9 primitives in the internal-big-picture basis",
  "method": "9-D primitive binarization (purpose, examples, guidelines, constraints, verification, composition, changelog, references, anti-patterns) + chordal distance to ideal pole on Fibonacci lattice",
  "parameters": {
    "basis": "internal-big-picture",
    "d": 9,
    "seed": 20260812
  },
  "delta": {
    "k": 5,
    "missing_primitives": [
      "examples",
      "constraints",
      "changelog",
      "references"
    ],
    "chordal_resid": 0.0
  },
  "verdict": "PARTIAL",
  "score": 28,
  "caveat": "binarization is heuristic; a stricter regex pass might surface sub-primitives"
}
```
