# yubiOS TODO

Last reviewed: 2026-07-17
Status: active task list
Latest targeted audit: [refs/systemd-v262-audit-2026-07-14.md](refs/systemd-v262-audit-2026-07-14.md).
Latest broad research note: [refs/research-refresh-2026-07-11.md](refs/research-refresh-2026-07-11.md).
Latest VM e2e evidence: [refs/vm-e2e-run-29525332901.md](refs/vm-e2e-run-29525332901.md), plus SSH follow-up run [29543974333 / job 87776913919](https://github.com/yubi-OS/yubiOS/actions/runs/29543974333/job/87776913919).

Use this file for current work. Completed historical context belongs in merged PRs, ADRs, or dated refs.

## FUTURE.md Coverage Map

Use this map to keep [FUTURE.md](FUTURE.md) roadmap entries tied to active TODO work instead of letting roadmap-only sections drift.

| FUTURE.md section | Current TODO.md coverage | Follow-up |
|---|---|---|
| Near-Term Planning Cycle | Covered by Current Documentation Tasks | Keep dated `refs/` planning-cycle notes scoped to each research pass |
| Milestone F: ARM64 Owner-Owned Root Of Trust | Covered by Current ARM64 Tasks | Continue ROCK 5B/RK3588 Path A proof and ROCKPro64/RK3399 secondary evidence |
| Milestone SecTime: Secure-World Time Evidence | Missing before this map | Track OP-TEE/TF-A secure time evidence under Current Roadmap Research Tasks |
| Milestone Frost: Firmware-Assisted GPU Resource Lockout | Missing before this map | Track Panfrost, cgroup, and firmware lockout research under Current Roadmap Research Tasks |
| Milestone CI: Keep The Test Lanes Honest | Covered by Current CI Tasks | Keep PQ TLS, QEMU zstd EFI zboot, VM e2e, and dev/prod isolation checks visible |
| Milestone Docs: Prevent Snapshot Drift | Covered by Current Documentation Tasks | Keep refs, PINNED, CITATION, and hardening terminology aligned |
| Milestone Net: OpenWrt WireGuard Deception LAN | Partially covered by the Endlessh fit ref, not active TODOs | Add OpenWrt package proof, decoy scan evidence, notification policy, and ADR tasks |
| Post-Launch Hardware Work | Partially covered by Current ARM64 and Supply-Chain Tasks | Promote individual items only when they have a board target, evidence target, and recovery plan |
| Deferred Ideas | Watch-list only | Keep `systemd-sysinstall`, LUO/KHO, U-Boot FIDO2/U2F, and ORAS media types out of active scope until promoted |
| Exit Criteria For Moving Work Out Of FUTURE | Partially covered by security and docs tasks | Require trust boundary, recovery, evidence, pins, notification/retention policy, and prod/test separation before promotion |

## Current Documentation Tasks

- [x] Add a dated planning-cycle note for the 2026-07-11 research pass: [refs/planning-cycle-2026-07-11.md](refs/planning-cycle-2026-07-11.md).
- [x] Add a scheduled upstream research refresh note: [refs/research-refresh-2026-07-11.md](refs/research-refresh-2026-07-11.md).
- [x] Refresh refs that described v261, swu2f, swtpm, PKCS#11 signing, and zstd EFI zboot as future or stale.
- [x] Remove obsolete workflow-token warning language from repo guidance.
- [x] Make [PINNED.md](PINNED.md) the explicit live source for image digests.
- [x] Before systemd v262 adoption, audit docs/code for `/run/boot-loader-entries/`, `systemd-sysupdated` D-Bus, and `updatectl` assumptions: [refs/systemd-v262-audit-2026-07-14.md](refs/systemd-v262-audit-2026-07-14.md).
- [x] Record the 2026-07-16 VM e2e milestone from run 29525332901: [refs/vm-e2e-run-29525332901.md](refs/vm-e2e-run-29525332901.md).
- [x] Switch the active install docs from `bootc install to-disk` to `bootc install to-filesystem --root-mount-spec=""` so DPS auto-discovery remains explicit.
- [ ] Keep future planning cycles dated and scoped under `refs/`.

## Current Roadmap Research Tasks

These items map [FUTURE.md](FUTURE.md) sections that were missing or only partially represented in the active TODO list.

### Milestone SecTime

- [ ] Add a source-backed `refs/` note identifying the active OP-TEE secure time configuration for RK3399 and RK3588, including `CFG_SECURE_TIME_SOURCE_CNTPCT`, AArch64 timer handling, and TF-A `SPD=opteed` integration.
- [ ] Define what yubiOS may safely claim from secure-world time: monotonic within a boot, suspend/resume behavior, normal-world tamper resistance, and power-loss/reboot limits.
- [ ] Add or design an OP-TEE TA/smoke test that records monotonic secure-world reads and expected failure behavior on ROCK 5B/RK3588 and ROCKPro64/RK3399.
- [ ] Draft ADR coverage for which decisions may rely on secure-world time and which require stronger counters, sealed state, or remote-attestation freshness.

### Milestone Frost

- [ ] Add a source-backed `refs/` map of current Panfrost/Rockchip kernel patch points for probe/init, BO create/free, PRIME import, and submit guarding.
- [ ] Determine whether the target kernel can use DRM device-memory cgroup accounting for Panfrost, or whether a minimal cgroup-aware BO accounting prototype is required first.
- [ ] Sketch the U-Boot device-tree/reserved-memory handoff plus secure-monitor SMC or mailbox interface for context quarantine, IOMMU revocation, GPU reset, or power gating.
- [ ] Prove whether RK3399/RK3588 lockout can target an offending cgroup/context or must fall back to full-GPU reset behavior.
- [ ] Define tests for false positives, graphics stack recovery, telemetry, logs, owner notification, and owner recovery after a Frost event.
- [ ] Draft ADR coverage for the trust boundary between Linux policy, OP-TEE/TF-A hard cutoff, and user recovery.

### Milestone Net

- [ ] Turn [refs/endlessh-openwrt-fit-2026-07-17.md](refs/endlessh-openwrt-fit-2026-07-17.md) into an OpenWrt package proof plan with feed/package layout, UCI config, procd service behavior, firewall/nftables integration, and WireGuard-zone defaults.
- [ ] Build an OpenWrt VM or spare-router proof with a WireGuard-only decoy address pool and an owner-selected notification path.
- [ ] Capture packet-level evidence that scans hit decoys before the real SSH endpoint is discoverable.
- [ ] Define logging defaults that avoid storing attempted passwords, private keys, or sensitive payloads, while still preserving useful owner notification evidence.
- [ ] Draft ADR coverage for the deception trust boundary, notification model, evidence retention, lab-mode exposure, and failure behavior.

### FUTURE Promotion Gates

- [ ] Before moving any FUTURE item into ADR, SPEC, or implementation, record its trust boundary, recovery behavior, evidence target, required pins/upstream sources, notification/evidence-retention policy when relevant, and production/test artifact separation.
- [ ] Keep post-launch hardware and deferred ideas watch-listed until a specific owner, board or deployment target, evidence target, and recovery plan exist.

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
- [ ] Validate the documented `bootc install to-filesystem` path on a fresh VM or disposable disk, including external partition preparation, mounted `/mnt`, `--skip-finalize`, and omitted `root=` via `--root-mount-spec=""`.

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
- `bootc install to-filesystem --root-mount-spec=""` is now the documented install baseline for DPS auto-discovery; keep watching for installer UX that can prepare and mount the target filesystems safely.
- `systemd-sysinstall` may become useful for guided install UX, but the current repart/bootc model remains the baseline.
- LUO/KHO may matter for appliance/server deployments, but A/B reboot remains correct for the current desktop/laptop thesis.
- U-Boot FIDO2/U2F console authentication remains idea-stage until USB HID, crypto, and recovery risks are audited.
- ORAS artifact media types may replace `FROM scratch` carrier images when registry support and UX improve.

## Retired From Active TODO

- Treating OpenSSL PQ hybrid support as future-only: current OpenSSL 3.5+ defaults already include `X25519MLKEM768`.
- Treating swu2f Layer 2 as merely planned: the TEST-only dev image path exists and must stay isolated.
- Repeating old digest examples from workflow logs as current pins: use [PINNED.md](PINNED.md).
- Describing ARM64 as secondary: ADR-023 makes ARM64 primary and x86-64 supported secondary.
