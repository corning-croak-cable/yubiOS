# yubiOS Blockers

Last reviewed: 2026-07-17
Status: active blocker register

This file lists current blockers only. Historical blockers that were resolved by merged work should move into ADRs, refs, or PR history rather than staying in the active list.

## Active Blockers

| ID | Area | Blocker | Current next step |
|---|---|---|---|
| B-ARM64-PATHA | ARM64 hardware | Path A is not production until a real board proves ROTPK/fuse provisioning, OP-TEE, RPMB-backed StandaloneMM variables, fTPM NV, U-Boot UEFI, and signed UKI boot. Board roles are documented in [refs/arm64-rk-board-status-2026-07-17.md](refs/arm64-rk-board-status-2026-07-17.md). | Run a documented sacrificial ROCK 5B / RK3588 rehearsal before production language, then carry secondary evidence to ROCKPro64 / RK3399. |
| B-VM-BOOTLOADER-UPDATE | VM CI | Runs 29525332901 and 29543974333 showed `bootloader-update.service` failing inside the bcvk guest. The first kernel-command-line guard missed because bcvk DirectBoot omits `rootfstype=virtiofs`; current `main` now detects bcvk by checking the live `/` mount type in `/proc/mounts`. | Validate a fresh VM e2e run on current `main`; retire this blocker only after the guest skips `bootloader-update.service` without failing real installed-system bootupd coverage. |
| B-VM-SSH | VM CI | Run 29702569137 booted both ARM64 VMs, started sshd, and proved the QEMU host-forward reached port 22. It then exposed two harness defects: the tests called the nonexistent top-level `bcvk ssh` command, and CI replaced bcvk's documented `tmpfiles.extra` credential with a direct credential before the guest rejected the offered key. Current `main` now uses the same in-container SSH transport as bcvk and preserves `tmpfiles.extra`. | Validate a fresh VM e2e run on current `main`; retire this blocker only after root public-key authentication succeeds and the guest assertions begin. |
| B-QEMU-ZBOOT | VM CI | zstd EFI zboot still depends on a pinned QEMU workaround until runner QEMU carries the upstream fix; run 29525332901 proved the workaround is no longer the active failure for the ARM64 lane. | Keep the workaround explicit, keep the stale-cache skip, and revisit removal only after runner image refresh. |
| B-PINS | Supply chain | Base-image digest changes require explicit [PINNED.md](PINNED.md) updates and package-floor checks. | Treat stale run-specific digests as historical evidence only. |
| B-HARDENING-RUNTIME | systemd hardening | Static hardening audit is complete in [refs/systemd-hardening-audit-2026-07-17.md](refs/systemd-hardening-audit-2026-07-17.md), but runtime evidence still needs the target image/base to run the Bats unit checks and `systemd-analyze verify`. | Run the hardening tests in a target image/base before adding `RestrictFileSystemAccess=` or claiming runtime enforcement beyond the existing `RestrictFileSystems=~@network` enrollment control. |
| B-REAL-FIDO2 | E2E unlock | swu2f/dev image proves software-authenticator flow; production confidence still needs real YubiKey hardware validation. | Validate the VM SSH/bootloader fixes, confirm enrollment-surface CI now runs after boot-step failures, and keep hardware-backed evidence as the production-confidence gate. |

## Not Current Blockers

These are no longer active blockers after the latest docs and CI work:

- Workflow-file writes are not blocked by a missing token scope in the current connected-app workflow. Keep workflow trigger changes narrow, but do not repeat the old manual-only guidance.
- PQ TLS implementation is not waiting for future OpenSSL support. OpenSSL 3.5+ and Go 1.24+ provide default `X25519MLKEM768` behavior; the active work is verification and regression gating.
- systemd v261 is not a future-only planning item in the docs. Current docs should describe completed v261 research as reviewed, while leaving specific implementation gates where evidence is still needed.
- swu2f Layer 2 is no longer merely a planned concept; the `dev` image path is live for TEST-only VM validation.
- The ARM64 VM e2e lane is no longer blocked at the pre-boot host/harness bring-up layer when the pinned QEMU workaround is active: recent runs reached a booted Fedora guest before failing on guest service/SSH reachability.
- The hardening documentation audit is no longer pending as a static docs task; the remaining hardening blocker is runtime validation inside the target image/base.

## Inconsistency Log

The 2026-07-11 planning cycle found and corrected these inconsistencies across docs:

- `RestrictFileSystems=` was described as a new v261 feature. It is the existing BPF-LSM filesystem-type limiter; `RestrictFileSystemAccess=` is the v261 addition.
- Older docs treated ARM64 as secondary even after ADR-023 made ARM64 primary.
- Old TODO/run notes included stale base-image digest examples. [PINNED.md](PINNED.md) is now called out as the only live digest source.
- Some refs described TEST-only swu2f and v261 work as pending after later PRs made them live or reviewed.
- `AGENTS.md` and tool docs repeated an obsolete warning about workflow-token scope.

## Reporting Rule

When a blocker changes state, update this file and the relevant issue or PR report. Do not leave resolved blockers in the active table just because they are historically important.
