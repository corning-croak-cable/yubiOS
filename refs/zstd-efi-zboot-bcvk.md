# ARM64 EFI zboot + zstd blocker (bcvk DirectBoot)

_Last reviewed: 2026-07-11_

## Executive summary

Fedora ARM64 kernels can be packaged as EFI zboot images whose embedded kernel payload is `zstd` compressed. The yubiOS VM e2e harness launches `bcvk ephemeral run`, which uses QEMU's direct-kernel/DirectBoot path for the kernel extracted from the bootc image. Older QEMU direct loaders handled EFI zboot `gzip` but not `zstd`, producing:

```text
unable to handle EFI zboot image with "zstd" compression
```

This is a host harness/kernel-loader compatibility issue, not a yubiOS FIDO2, LUKS2, swtpm, swu2f, systemd-homed, or PAM regression.

## Current yubiOS stance

1. Keep production aligned with Fedora ARM64 defaults; do not downgrade production compression solely for CI.
2. In `.github/workflows/ci_test-vm.yml`, use the pinned upstream QEMU commit `3a18e8a25992d1643707e2cebdd6e9bb2bd7d3b9` for the ARM64 bcvk lane until runner distributions ship the zstd EFI zboot loader fix.
3. Bind-mount the QEMU prefix/wrapper into bcvk's inner container so DirectBoot uses the zstd-capable QEMU binary and the matching ROM search path.
4. Keep the exact-error skip as a fallback for stale self-hosted caches and manual runs with an older QEMU.

## Research notes

- Fedora/Rawhide ARM64 moved through kernel images that exposed this direct-loader limitation.
- QEMU's fix adds a zstd branch to the EFI zboot unpacker and keeps the unsupported-compression error path for other cases.
- Firmware/stub boot is strategically cleaner than DirectBoot because the EFI stub owns decompression, which more closely resembles Secure Boot production flow.

## Strategic fixes

- Preferred short-term: pinned QEMU until distro QEMU contains the fix.
- Preferred medium-term: bcvk ARM64 firmware/stub boot mode for better fidelity.
- Last-resort CI workaround: test-only ARM64 image variant with older supported compression, never production.

## Sources

- QEMU pull mail: https://lists.nongnu.org/archive/html/qemu-devel/2026-01/msg04080.html
- QEMU patch discussion: https://patchew.org/QEMU/20251011081347.4063198-1-daan.j.demeyer%40gmail.com/20251011081347.4063198-4-daan.j.demeyer%40gmail.com/
- dracut-ng issue 1406: https://github.com/dracut-ng/dracut-ng/issues/1406
- Linux EFI zboot background: https://lwn.net/Articles/906386/
