# yubiOS TODO

Last reviewed: 2026-07-17
Status: active task list
Latest targeted audit: [refs/systemd-v262-audit-2026-07-14.md](refs/systemd-v262-audit-2026-07-14.md).
Latest broad research note: [refs/research-refresh-2026-07-11.md](refs/research-refresh-2026-07-11.md).
Latest VM e2e evidence: [refs/vm-e2e-run-29525332901.md](refs/vm-e2e-run-29525332901.md), plus SSH follow-up run [29543974333 / job 87776913919](https://github.com/yubi-OS/yubiOS/actions/runs/29543974333/job/87776913919).

Use this file for current work. Completed historical context belongs in merged PRs, ADRs, or dated refs.

## Current Documentation Tasks

- [x] Add a dated planning-cycle note for the 2026-07-11 research pass: [refs/planning-cycle-2026-07-11.md](refs/planning-cycle-2026-07-11.md).
- [x] Add a scheduled upstream research refresh note: [refs/research-refresh-2026-07-11.md](refs/research-refresh-2026-07-11.md).
- [x] Refresh refs that described v261, swu2f, swtpm, PKCS#11 signing, and zstd EFI zboot as future or stale.
- [x] Remove obsolete workflow-token warning language from repo guidance.
- [x] Make [PINNED.md](PINNED.md) the explicit live source for image digests.
- [x] Before systemd v262 adoption, audit docs/code for `/run/boot-loader-entries/`, `systemd-sysupdated` D-Bus, and `updatectl` assumptions: [refs/systemd-v262-audit-2026-07-14.md](refs/systemd-v262-audit-2026-07-14.md).
- [x] Record the 2026-07-16 VM e2e milestone from run 29525332901: [refs/vm-e2e-run-29525332901.md](refs/vm-e2e-run-29525332901.md).
- [ ] Keep future planning cycles dated and scoped under `refs/`.

## Current CI Tasks

- [ ] Keep PQ TLS verification visible in CI for OpenSSL 3.5+ and Go 1.24+ defaults; when the repo toolchain reaches Go 1.26, include `SecP256r1MLKEM768` and `SecP384r1MLKEM1024` in accepted hybrid-group checks.
- [ ] Keep the QEMU zstd EFI zboot workaround version-gated until runner QEMU contains upstream zstd EFI zboot loader support.
- [ ] Validate the bcvk virtiofs-root `bootloader-update.service` skip on a fresh VM e2e run. The current fix inspects `/proc/mounts` because bcvk DirectBoot omits `root=`, `rootfstype=`, and `rootflags=` from the kernel command line.
- [ ] Validate the bcvk root SSH key path on a fresh VM e2e run after the SSH follow-up fix. bcvk injects the root key through the `tmpfiles.extra` system credential; yubiOS now exposes that key to sshd through a root-only `AuthorizedKeysCommand` and prints `bcvk ssh` / `ssh -vvv` diagnostics on timeout.
- [ ] Confirm `tests/vm/test-fido2-enrollment.sh` runs in the same VM workflow even when the earlier LUKS/FIDO2 boot step fails; `.github/workflows/ci_test-vm.yml` now keeps the existing gates but wraps the enrollment step in `always()`.
- [ ] Keep `dev`/`dev-<sha>` swu2f images isolated from production build and publish paths.
- [ ] Treat old-sha workflow reruns as historical unless the workflow is rerun against current `main`.
- [x] For workflow trigger edits, add narrow path-scoped push triggers only when required for validation.
- [ ] If build policy wiring moves into Bake, keep Docker `target.policy` keys aligned with CLI policy flags and avoid duplicate `Dockerfile.rego` loading assumptions.
- [ ] Add board variant fields to real-hardware firmware workflows before hardware lanes land: `rock5b-rk3588` as the primary/default Path A variant and `rockpro64-rk3399` as the supported secondary variant.

## Current ARM64 Tasks

- [x] Choose the first Path A board for production-root proof: Radxa ROCK 5B / RK3588 is primary; ROCKPro64 / RK3399 is supported secondary per ADR-029.
- [ ] Rehearse ROTPK/fuse provisioning on sacrificial ROCK 5B hardware before production language.
- [ ] Prove OP-TEE, StandaloneMM, RPMB-backed variables, fTPM NV, and U-Boot UEFI on ROCK 5B hardware first, then carry the supported-secondary evidence to ROCKPro64.
- [ ] Record exact TF-A, OP-TEE, StandaloneMM/RPMB, and U-Boot config evidence for Path A, including `CFG_RPMB_FS`, `CONFIG_EFI_MM_COMM_TEE`, and `CONFIG_SUPPORT_EMMC_RPMB`.
- [ ] Verify the same signed UKI boots across ARM64 and x86-64 paths.
- [ ] Document Path A vs Path B status per board, starting with `rock5b-rk3588` and `rockpro64-rk3399`.

## Current Security Tasks

- [ ] Audit services for `ConditionSecurity=measured-os` where enrollment or signing behavior must not run on an unmeasured boot.
- [ ] Audit `RestrictFileSystems=` separately from the v261 `RestrictFileSystemAccess=` control.
- [x] Keep CHIPSEC first-boot validation scoped as a one-shot exception and document firmware-warning behavior: the unit and Bats coverage enforce the one-shot exception, while `run-firstboot-check.sh` documents `PASS`/`WARN`/`FAILED` semantics and informational WPBT/Computrace evidence.
- [ ] Add or refresh real-hardware YubiKey validation evidence for FIDO2 unlock and homed flows.
- [ ] Keep recovery paths documented before enabling any feature that can lock an owner out.

## Current Supply-Chain Tasks

- [ ] Update [PINNED.md](PINNED.md) for every base-image/tool digest change.
- [ ] Verify package floors after digest bumps: systemd target, pam-u2f >= 1.3.1, OpenSSL 3.5+, and Go 1.24+ where relevant.
- [ ] Audit bootc 1.11+ install docs/code for DPS behavior: `to-disk` still injects `root=UUID=`, while DPS auto-discovery requires the explicit `to-filesystem --root-mount-spec=""` path and a Boot Loader Interface-capable bootloader.
- [ ] Keep production, installer, firmware, and dev/test artifacts clearly labeled and non-overlapping.
- [ ] Preserve provenance/SBOM expectations for published artifacts.
- [ ] Keep production bootc (`latest`, `<sha>`), dev/test (`dev`, `dev-<sha>`), and installer (`installer`, `installer-<sha>`) tags board-neutral unless the OS or installer artifact actually diverges by board.
- [ ] If real-hardware firmware payloads diverge from the current QEMU/CI `firmware` bundle, publish board-scoped firmware tags under the existing `0mniteck/yubios` namespace: `firmware-rock5b-rk3588`, `firmware-rock5b-rk3588-<sha>`, `firmware-rockpro64-rk3399`, and `firmware-rockpro64-rk3399-<sha>`.

## Watch List

- Run 29525332901 proved the ARM64 lane can boot the dev image to Fedora login with the pinned QEMU workaround; keep watching for runner QEMU refreshes before removing that workaround.
- Run 29543974333 reached system targets and started sshd/networking, but root SSH did not become reachable through bcvk within 900s; the next failure should include the unsuppressed `bcvk ssh` error plus an in-container `ssh -vvv` attempt.
- systemd v262 removes `/run/boot-loader-entries/` support and the experimental `systemd-sysupdated` D-Bus API; the 2026-07-14 audit found no repo dependency, but future update UX should stay on UAPI.1/BLS and Varlink/systemd-sysupdate rather than removed interfaces or unaudited `updatectl` assumptions.
- systemd v262 renames `systemd-sysupdate.service`/`.timer` to `systemd-sysupdate-update.service`/`.timer`; verify compatibility symlinks before adding units against the old names.
- Go 1.26 expands default hybrid PQ TLS key exchanges beyond `X25519MLKEM768`; tests should assert acceptable policy rather than a single hard-coded group.
- bootc 1.11 DPS support may help future installer UX, but the current `to-disk` baseline still uses `root=UUID=` for compatibility.
- `systemd-sysinstall` may become useful for guided install UX, but the current repart/bootc model remains the baseline.
- LUO/KHO may matter for appliance/server deployments, but A/B reboot remains correct for the current desktop/laptop thesis.
- U-Boot FIDO2/U2F console authentication remains idea-stage until USB HID, crypto, and recovery risks are audited.
- ORAS artifact media types may replace `FROM scratch` carrier images when registry support and UX improve.

## Retired From Active TODO

- Treating OpenSSL PQ hybrid support as future-only: current OpenSSL 3.5+ defaults already include `X25519MLKEM768`.
- Treating swu2f Layer 2 as merely planned: the TEST-only dev image path exists and must stay isolated.
- Repeating old digest examples from workflow logs as current pins: use [PINNED.md](PINNED.md).
- Describing ARM64 as secondary: ADR-023 makes ARM64 primary and x86-64 supported secondary.
