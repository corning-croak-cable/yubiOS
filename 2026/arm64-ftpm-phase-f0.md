# Phase F0: QEMU ARM64 bring-up (ADR-018)
Goal: /dev/tpm0 live with PCRs extending in QEMU virt ARM64.
Stack: TF-A PLAT=qemu + OP-TEE PLATFORM=vexpress-qemu_virt + fTPM Early TA (bc50d971) + U-Boot CONFIG_TPM2_FTPM_TEE + Linux CONFIG_TCG_FTPM_TEE.
Critical: resolve Early-TA RPMB bootstrap hazard (OP-TEE #5766) — tee-supplicant from initramfs.
Target hardware (F2): RK3588 (Orange Pi 5 / Rock 5B) per ADR-019.
See FUTURE.md, knowledge/arm64-ftpm-stack.md, skills arm-trusted-firmware-optee + ftpm-optee-tpm.