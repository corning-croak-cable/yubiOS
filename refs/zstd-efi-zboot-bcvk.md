# ARM64 EFI zboot + zstd blocker (bcvk DirectBoot)

_Last updated: July 10, 2026_

## Executive summary

Fedora Rawhide/Fedora 45 ARM64 kernels can be packaged as EFI zboot images whose
embedded kernel payload is `zstd` compressed. The yubiOS VM e2e tests currently
launch `bcvk ephemeral run`, which uses QEMU's direct-kernel/DirectBoot path for
the kernel extracted from the bootc image. That QEMU path historically handled
EFI zboot `gzip`, but not `zstd`, and fails before the guest reaches SSH with:

```text
unable to handle EFI zboot image with "zstd" compression
```

The failure is therefore a host harness/kernel-loader compatibility issue, not a
yubiOS FIDO2, LUKS, swtpm, swu2f, systemd-homed, or PAM regression. yubiOS now
tackles this in CI by building a pinned upstream QEMU commit that contains
`hw/loader: Add support for zboot images compressed with zstd` and placing
that `qemu-system-aarch64` ahead of Ubuntu's packaged QEMU before bcvk runs.
The skip remains as a final fallback for stale self-hosted caches or manual runs
that still use an older QEMU.

## Research notes

- Red Hat Bugzilla 2385692 tracks the same symptom on aarch64: QEMU direct boot
  cannot boot current Fedora Rawhide kernels once they moved to zboot + zstd.
- dracut-ng issue 1406 reports Fedora ARM64 VM-test failures beginning with a
  Fedora kernel update from `6.14.11-300.fc42.aarch64`, with the same
  `unable to handle EFI zboot image with "zstd" compression` message.
- QEMU patch series `Add support for zboot images compressed with zstd` adds a
  zstd branch to `unpack_efi_zboot_image()` and preserves the same error message
  for unsupported compression types, confirming the string comes from QEMU's
  direct EFI zboot unpacker.
- Linux EFI zboot discussions explain why this only hits some boot paths: EFI
  zboot is a self-decompressing EFI wrapper, but direct-kernel boot bypasses the
  normal firmware/stub execution path and asks the VMM/loader to unpack the image
  itself.

## Tactical yubiOS stance

1. In `.github/workflows/ci_test-vm.yml`, install `qemu-system-aarch64` from
   upstream QEMU commit `3a18e8a25992d1643707e2cebdd6e9bb2bd7d3b9` for the ARM64
   VM job before building/running bcvk. That commit is the zstd EFI zboot loader
   fix and is cached under `/opt/qemu-zstd/<commit>` on the self-hosted runner.
2. Keep `tests/vm/test-luks-fido2-ci.sh` and
   `tests/vm/test-fido2-enrollment.sh` skip-tolerant for this exact host-side
   DirectBoot/zstd failure as a safety net for manual runs or stale runners.
3. Do **not** downgrade yubiOS production compression or kernel packaging just to
   satisfy an older CI harness; production should stay aligned with Fedora's
   ARM64 defaults unless the boot stack itself is affected.

## Strategic fixes to evaluate

- **Preferred harness fix:** keep the workflow-level pinned QEMU build until the
  runner distribution ships a QEMU release that includes commit
  `3a18e8a25992d1643707e2cebdd6e9bb2bd7d3b9`; then replace the source build with
  a version gate and remove the fallback skip once bcvk CI proves stable.
- **Alternate harness fix:** add a bcvk mode for ARM64 bootc images that boots
  through UEFI/systemd-stub rather than direct-kernel boot. This more closely
  resembles real Secure Boot flows and avoids duplicating decompressor support in
  QEMU's direct loader.
- **Image workaround:** if a short-lived CI lane must run before QEMU/bcvk is
  fixed, build a test-only ARM64 kernel/image variant that uses a
  bcvk-supported EFI zboot compression type. Keep this out of production and
  document the divergence.

## Source links

- Red Hat Bugzilla 2385692: <https://bugzilla.redhat.com/show_bug.cgi?id=2385692>
- dracut-ng issue 1406: <https://github.com/dracut-ng/dracut-ng/issues/1406>
- QEMU zstd EFI zboot patch: <https://patchew.org/QEMU/20251011081347.4063198-1-daan.j.demeyer%40gmail.com/20251011081347.4063198-4-daan.j.demeyer%40gmail.com/>
- Linux EFI zboot background: <https://lwn.net/Articles/906386/>
