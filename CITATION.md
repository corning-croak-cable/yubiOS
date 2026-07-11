# Citations And Primary Sources

Last reviewed: 2026-07-11

This file lists the main upstream sources used by the yubiOS docs. Prefer primary upstream documentation, release notes, standards, and source repositories when updating architectural claims.

## systemd

- systemd v261 release: https://github.com/systemd/systemd/releases/tag/v261
- `systemd.exec(5)` sandboxing directives: https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html
- `systemd-cryptenroll(1)`: https://www.freedesktop.org/software/systemd/man/latest/systemd-cryptenroll.html
- `systemd-repart(8)`: https://www.freedesktop.org/software/systemd/man/latest/systemd-repart.html
- `systemd-sbsign(1)`: https://www.freedesktop.org/software/systemd/man/latest/systemd-sbsign.html
- Discoverable Partitions Specification: https://systemd.io/DISCOVERABLE_PARTITIONS
- Automatic Boot Assessment: https://systemd.io/AUTOMATIC_BOOT_ASSESSMENT

## FIDO2, YubiKey, And Local Auth

- Yubico PIV tool documentation: https://developers.yubico.com/yubico-piv-tool/
- Yubico pam-u2f security advisory YSA-2025-01: https://www.yubico.com/support/security-advisories/ysa-2025-01/
- OpenSSH 8.2 FIDO2 release notes: https://www.openssh.com/txt/release-8.2
- libfido2 project: https://github.com/Yubico/libfido2

## bootc, OCI, And Build Tooling

- bootc install documentation: https://bootc.dev/bootc/bootc-install.html
- bootc upstream repository: https://github.com/containers/bootc
- fedora-bootc registry source: https://quay.io/repository/fedora/fedora-bootc
- composefs upstream: https://github.com/containers/composefs
- Docker Buildx build policies: https://docs.docker.com/build/policies/intro/
- Docker attestations: https://docs.docker.com/build/attestations/

## TLS And Post-Quantum Defaults

- OpenSSL 3.5 release notes: https://openssl-library.org/news/openssl-3.5-notes/
- OpenSSL 3.5 group configuration documentation: https://docs.openssl.org/3.5/man3/SSL_CONF_cmd/
- Go 1.24 release notes: https://go.dev/doc/go1.24
- Go issue for default hybrid TLS group: https://github.com/golang/go/issues/69985

## Firmware, ARM64, And TPM Work

- ARM Trusted Firmware-A: https://trustedfirmware-a.readthedocs.io/
- OP-TEE documentation: https://optee.readthedocs.io/
- OP-TEE fTPM project: https://github.com/OP-TEE/optee_ftpm
- Microsoft TPM 2.0 reference implementation: https://github.com/microsoft/ms-tpm-20-ref
- U-Boot documentation: https://docs.u-boot.org/
- U-Boot EFI documentation: https://docs.u-boot.org/en/latest/develop/uefi/index.html
- U-Boot measured boot documentation: https://docs.u-boot.org/en/latest/develop/measured_boot.html

## Virtualization And zstd EFI zboot

- QEMU zstd EFI zboot patch discussion: https://lists.nongnu.org/archive/html/qemu-devel/2026-01/msg04080.html
- QEMU project: https://www.qemu.org/docs/master/
- swtpm project: https://github.com/stefanberger/swtpm

## yubiOS Internal References

- Planning cycle for this refresh: [refs/planning-cycle-2026-07-11.md](refs/planning-cycle-2026-07-11.md)
- v261 base-image research: [refs/v261-base-image.md](refs/v261-base-image.md)
- ARM64 fTPM planning: [refs/arm64-ftpm-phase-f0.md](refs/arm64-ftpm-phase-f0.md)
- zstd EFI zboot planning: [refs/zstd-efi-zboot-bcvk.md](refs/zstd-efi-zboot-bcvk.md)
- swtpm CI planning: [refs/bcvk-swtpm-ci.md](refs/bcvk-swtpm-ci.md)
- LUKS FIDO2 E2E planning: [refs/luks-fido2-e2e-test.md](refs/luks-fido2-e2e-test.md)
- PKCS#11 signing validation: [refs/sbsign-pkcs11-validate.md](refs/sbsign-pkcs11-validate.md)
