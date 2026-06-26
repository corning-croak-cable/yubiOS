# Phase F0: QEMU ARM64 bring-up (ADR-018)

Goal: a reproducible QEMU `virt` ARM64 boot chain that brings up a live `/dev/tpm0`
backed by our own fTPM, with PCRs extending. Prove the firmware trust chain and the
RPMB bootstrap hazard in emulation **before** any hardware (F2: RK3588, ADR-019).

## Stack (all pinned)

| Layer | Component | Pin / identifier |
|---|---|---|
| BL1/BL2/BL31 | TF-A | `PLAT=qemu ARCH=aarch64 SPD=opteed` |
| BL32 (S-EL1) | OP-TEE OS | `PLATFORM=vexpress-qemu_armv8a` (QEMU runs it as `-machine virt`) |
| S-EL0 TA | ms-tpm-20-ref fTPM, Early TA | UUID `bc50d971-d4c9-42c4-82cb-343fb7f37896`; ms-tpm-20-ref @ `98b60a44aba79b15fcce1c0d1e46cf5918400f6a` |
| BL33 (NS) | U-Boot, UEFI mode | `CONFIG_TPM2_FTPM_TEE=y`, `CONFIG_MEASURED_BOOT=y`, `CONFIG_EFI_LOADER=y` |
| OS | Linux | `CONFIG_TEE=y CONFIG_OPTEE=y CONFIG_TCG_TPM=y CONFIG_TCG_FTPM_TEE=m` |

> Correction to earlier draft: the OP-TEE platform is `vexpress-qemu_armv8a`, **not**
> `vexpress-qemu_virt`. The "vexpress" name is legacy; the QEMU machine is `virt`.

## Critical: Early-TA RPMB bootstrap hazard (OP-TEE #5766)

The fTPM is built as an **Early TA** so it is alive before any rootfs (U-Boot and Linux
IMA both need the TPM pre-rootfs). But an Early TA's first persistent NV write to RPMB
happens before `tee-supplicant` is running, which **panics**. Mitigation for F0: run
`tee-supplicant` from the **initramfs** so it is up before Linux touches the fTPM, and
defer the first persistent write until then. This is the single biggest integration risk
and the whole reason F0 lives in emulation first.

## PCR layout (convention)

| PCR | Content |
|---|---|
| 0,1 | System firmware (BL31/BL32/BL33) + config |
| 7 | Secure Boot policy state |
| 8,9 | Kernel, DTB, initramfs (measured by U-Boot) |
| 10 | IMA runtime log |
| 16 | Debug / resettable â used by the F0 verify script |

## Deliverables (this PR â no merge)

- `tests/vm/build-arm64-ftpm-qemu.sh` â reproducible build of the full chain from the
  pinned OP-TEE `qemu_v8` manifest set + pinned ms-tpm-20-ref, embedding the fTPM Early TA.
- `tests/vm/verify-tpm0-pcr-extend.sh` â in-guest done-condition: OP-TEE bus up,
  `/dev/tpm0`+`/dev/tpmrm0` present, `TPM2_Startup` OK, and a PCR extend that changes the
  PCR value.

## Done condition

`build-arm64-ftpm-qemu.sh` boots QEMU virt; inside the guest `verify-tpm0-pcr-extend.sh`
prints `PASS` â live `/dev/tpm0` backed by ms-tpm-20-ref, PCR extend works. Human
validation required (Phase 0 is human-gated); no CI, no merge.

## fTPM vs YubiKey

The fTPM is platform integrity / measured-boot / attestation only. The **YubiKey stays
the disk-unlock root** (FIDO2 hmac-secret â LUKS2, ADR-003). If the fTPM ever becomes the
sole unlock gate, yubiOS has re-created the on-device vendor-shaped trust anchor it exists
to remove.

See FUTURE.md, ADR-016/017/018/019, skills `arm-trusted-firmware-optee` + `ftpm-optee-tpm`.
