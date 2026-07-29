# yubiOS Blockers

Last reviewed: 2026-07-25
Status: active blocker register

This file lists current blockers only. Historical blockers that were resolved by merged work should move into ADRs, refs, or PR history rather than staying in the active list.

## Active Blockers

| ID | Area | Blocker | Current next step |
|---|---|---|---|
| B-ARM64-PATHA | ARM64 hardware | Path A is not production until a real board proves ROTPK/fuse provisioning, OP-TEE, RPMB-backed StandaloneMM variables, fTPM NV, U-Boot UEFI, and signed UKI boot. Board roles are documented in [refs/arm64-rk-board-status-2026-07-17.md](../refs/arm64-rk-board-status-2026-07-17.md). | Run a documented sacrificial ROCK 5B / RK3588 rehearsal before production language, then carry secondary evidence to ROCKPro64 / RK3399. |
| B-RK3588-TPL | ROCK 5B firmware | Run 29869527608 compiled the RK3588 components but recorded that U-Boot requires a real external DDR/TPL blob. The bundle lacked the expected `u-boot-rockchip.bin`, so its green publish job is diagnostic packaging, not a flashable image. | Select a legally redistributable source, pin its immutable ref and checksum, fail closed when it is absent, and prove the resulting combined image on sacrificial ROCK 5B hardware. |
| B-QEMU-ZBOOT | VM CI | zstd EFI zboot still depends on a pinned QEMU workaround until runner QEMU carries the upstream fix; run 29525332901 proved the workaround is no longer the active failure for the ARM64 lane. | Keep the workaround explicit, keep the stale-cache skip, and revisit removal only after runner image refresh. |
| B-PINS | Supply chain | Base-image digest changes require explicit [PINNED.md](../PINNED.md) updates and package-floor checks. | Treat stale run-specific digests as historical evidence only. |
| B-HARDENING-RUNTIME | systemd hardening | Static hardening audit is complete in [refs/systemd-hardening-audit-2026-07-17.md](../refs/systemd-hardening-audit-2026-07-17.md), but runtime evidence still needs the target image/base to run the Bats unit checks and `systemd-analyze verify`. | Run the hardening tests in a target image/base before adding `RestrictFileSystemAccess=` or claiming runtime enforcement beyond the existing `RestrictFileSystems=~@network` enrollment control. |
| B-REAL-FIDO2 | E2E unlock | SoftHSM and swu2f exercise interfaces, but production confidence still needs a physical YubiKey to validate FIDO2 unlock, homed, resident SSH keys, PAM presence, PIV signing, recovery, and failure handling. | First close B-VM-CTAP2 for deterministic software coverage, then retain a real-hardware evidence run as the production-confidence gate. |
| B-BOOTC-SEAL | bootc composefs | The pinned Fedora bootc image records bootc 1.16.3, which lacks `container split-kernel-and-rootfs`; run 29884493346 proves strict fs-verity through a mutable BLS digest anchor, not a sealed UKI or Secure Boot boot. **2026-07-29 partial progress:** the kernel-side artifact split is now shipped (`docker.io/0mniteck/yubios:uki-<sha>-<arch>` per ADR-022 / ADR-032, see `refs/kernel-rootfs-split-2026-07-29.md`); bootc install config pins `[install] kargs` so the auto-generated UKI matches the mkosi cmdline. | Complete the install-time BLSConfig wiring to use the pre-built UKI artifact (Phase 2 of ADR-032): either (a) bootc-side patch mirroring the secureboot-keys flow at `/usr/lib/bootc/install/loader-entries/*.conf`, or (b) bump the base to a fedora-bootc carrying bootc v1.16.4+ for `bootc container split-kernel-and-rootfs`. Then require Secure Boot and negative tamper boots on amd64 and arm64. See [refs/kernel-rootfs-split-2026-07-29.md](../refs/kernel-rootfs-split-2026-07-29.md) and [refs/bootc-composefs-sealed-flow-2026-07-22.md](../refs/bootc-composefs-sealed-flow-2026-07-22.md). |

## Not Current Blockers

These are no longer active blockers after the latest docs and CI work:

- Workflow-file writes are not blocked by a missing token scope in the current connected-app workflow. Keep workflow trigger changes narrow, but do not repeat the old manual-only guidance.
- PQ TLS implementation is not waiting for future OpenSSL support. OpenSSL 3.5+ and Go 1.24+ provide default `X25519MLKEM768` behavior; the active work is verification and regression gating.
- systemd v261 is not a future-only planning item in the docs. Current docs should describe completed v261 research as reviewed, while leaving specific implementation gates where evidence is still needed.
- swu2f Layer 2 is no longer merely a planned concept; the `dev` image path is live for TEST-only VM validation.
- The ARM64 VM e2e lane is no longer blocked at the pre-boot host/harness or guest-SSH layer when the pinned QEMU workaround is active; the remaining software-authenticator gap is tracked as `B-VM-CTAP2`.
- **B-VM-CTAP2 RESOLVED (2026-07-25).** Two real bugs were root-caused and fixed: (1) `pamu2fcfg` was missing from the built image (Fedora Rawhide splits it into its own subpackage from `pam-u2f`) -- fixed in the production `Containerfile` (PR #125) after an earlier fix to the wrong build path (`mkosi.conf`, PR #102) didn't take effect; (2) `test-luks-fido2-ci.sh`'s `homectl create` FIDO2 home-create leg was hanging 5 minutes on an empty `NEWPASSWORD=` instead of failing fast -- fixed with `--enforce-password-policy=no` (PR #102). [Run 30139433902 / job 89629762908](https://github.com/yubi-OS/yubiOS/actions/runs/30139433902/job/89629762908) proves the full chain end-to-end with no skips: host `bcvk --swu2f` uhid load -> in-guest `passless` -> `/dev/hidraw0` CTAP2 hmac-secret enumeration -> LUKS2 FIDO2 enroll/unlock PASS -> systemd-homed FIDO2 home create PASS -> `pamu2fcfg` FIDO2 registration OK -> `ssh-keygen -t ed25519-sk` OK. Both test scripts report PASS. Tracked in Linear OMN-48 (Done).
- `B-VM-SSH` and `B-VM-BOOTLOADER-UPDATE` are retired by [run 29872832727](https://github.com/yubi-OS/yubiOS/actions/runs/29872832727): root public-key authentication succeeded, guest assertions ran, and the DirectBoot/virtiofs bootloader-update guard did not reproduce the old failure.
- Strict composefs fs-verity is not itself blocked: the offline install lane can
  and does test it. `B-BOOTC-SEAL` is the narrower authenticity gap between a
  mutable BLS digest anchor and a signed UKI plus Secure Boot chain.
- The hardening documentation audit is no longer pending as a static docs task; the remaining hardening blocker is runtime validation inside the target image/base.

## Inconsistency Log

The 2026-07-11 planning cycle found and corrected these inconsistencies across docs:

- `RestrictFileSystems=` was described as a new v261 feature. It is the existing BPF-LSM filesystem-type limiter; `RestrictFileSystemAccess=` is the v261 addition.
- Older docs treated ARM64 as secondary even after ADR-023 made ARM64 primary.
- Old TODO/run notes included stale base-image digest examples. [PINNED.md](../PINNED.md) is now called out as the only live digest source.
- Some refs described TEST-only swu2f and v261 work as pending after later PRs made them live or reviewed.
- `AGENTS.md` and tool docs repeated an obsolete warning about workflow-token scope.

## Reporting Rule

When a blocker changes state, update this file and the relevant issue or PR report. Do not leave resolved blockers in the active table just because they are historically important.
