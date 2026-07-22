# yubiOS TODO

Last reviewed: 2026-07-21
Status: active task list
Latest requested-run evidence review: [refs/ci-evidence-2026-07-21.md](refs/ci-evidence-2026-07-21.md), covering the complete logs of runs 29869480442, 29869503301, 29869527608, 29872130447, 29872433355, 29872832727, 29876111887, and 29876466349.
Latest upstream progress review: [refs/systemd-upstream-progress-2026-07-21.md](refs/systemd-upstream-progress-2026-07-21.md).
Latest targeted audit: [refs/systemd-v262-audit-2026-07-14.md](refs/systemd-v262-audit-2026-07-14.md).
Latest broad research note: [refs/research-refresh-2026-07-11.md](refs/research-refresh-2026-07-11.md).
Latest VM e2e evidence: [run 29872832727](https://github.com/yubi-OS/yubiOS/actions/runs/29872832727); root SSH and the DirectBoot bootloader-update guard passed, while guest CTAP2 enumeration remained absent.
Latest bootc install evidence: [run 29884493346](https://github.com/yubi-OS/yubiOS/actions/runs/29884493346); native amd64 and arm64 fresh-runner legs installed digest `sha256:22140ef11deebac5643544434af1263368b72fa791fe53e98add677bbcadc08e` onto externally prepared DPS partitions, retained `/mnt` under `--skip-finalize`, and emitted no `root=` in the generated BLS entries.
Latest roadmap research pass: [refs/sectime-rk-secure-time-2026-07-17.md](refs/sectime-rk-secure-time-2026-07-17.md), [refs/frost-panfrost-lockout-2026-07-17.md](refs/frost-panfrost-lockout-2026-07-17.md), [refs/openwrt-deception-proof-plan-2026-07-17.md](refs/openwrt-deception-proof-plan-2026-07-17.md), and [refs/roadmap-promotion-gates-2026-07-17.md](refs/roadmap-promotion-gates-2026-07-17.md).
Latest firmware workflow split: [refs/firmware-rk-workflow-2026-07-17.md](refs/firmware-rk-workflow-2026-07-17.md).

Use this file for current work. Completed historical context belongs in merged PRs, ADRs, or dated refs.

## FUTURE.md Coverage Map

Use this map to keep [FUTURE.md](FUTURE.md) roadmap entries tied to active TODO work instead of letting roadmap-only sections drift.

| FUTURE.md section | Current TODO.md coverage | Follow-up |
|---|---|---|
| Near-Term Planning Cycle | Covered by Current Documentation Tasks | Keep dated `refs/` planning-cycle notes scoped to each research pass |
| Milestone F: ARM64 Owner-Owned Root Of Trust | Covered by Current ARM64 Tasks and [refs/arm64-rk-board-status-2026-07-17.md](refs/arm64-rk-board-status-2026-07-17.md) | Continue ROCK 5B/RK3588 Path A proof and ROCKPro64/RK3399 secondary evidence |
| Milestone SecTime: Secure-World Time Evidence | Covered by [refs/sectime-rk-secure-time-2026-07-17.md](refs/sectime-rk-secure-time-2026-07-17.md) | Hardware TA/smoke-test evidence remains open |
| Milestone Frost: Firmware-Assisted GPU Resource Lockout | Covered by [refs/frost-panfrost-lockout-2026-07-17.md](refs/frost-panfrost-lockout-2026-07-17.md) | Kernel prototype and RK hardware recovery proof remain open |
| Milestone CI: Keep The Test Lanes Honest | Covered by Current CI Tasks and [refs/firmware-rk-workflow-2026-07-17.md](refs/firmware-rk-workflow-2026-07-17.md) | Keep PQ TLS, QEMU zstd EFI zboot, VM e2e, firmware callback, and dev/prod isolation checks visible |
| Milestone Docs: Prevent Snapshot Drift | Covered by Current Documentation Tasks | Keep refs, PINNED, CITATION, CI_MAP, and hardening terminology aligned |
| Milestone Net: OpenWrt WireGuard Deception LAN | Covered by [refs/openwrt-deception-proof-plan-2026-07-17.md](refs/openwrt-deception-proof-plan-2026-07-17.md) | Build the VM/spare-router proof and packet evidence |
| Post-Launch Hardware Work | Covered by promotion gates and ARM64 board-status refs | Promote individual items only when they have a board target, evidence target, and recovery plan |
| Deferred Ideas | Watch-list only | Keep `systemd-sysinstall`, LUO/KHO, U-Boot FIDO2/U2F, and ORAS media types out of active scope until promoted |
| Exit Criteria For Moving Work Out Of FUTURE | Covered by [refs/roadmap-promotion-gates-2026-07-17.md](refs/roadmap-promotion-gates-2026-07-17.md) | Require trust boundary, recovery, evidence, pins, notification/retention policy, and prod/test separation before promotion |

## Current Documentation Tasks

- [x] Add a dated planning-cycle note for the 2026-07-11 research pass: [refs/planning-cycle-2026-07-11.md](refs/planning-cycle-2026-07-11.md).
- [x] Add a scheduled upstream research refresh note: [refs/research-refresh-2026-07-11.md](refs/research-refresh-2026-07-11.md).
- [x] Refresh refs that described v261, swu2f, swtpm, PKCS#11 signing, and zstd EFI zboot as future or stale.
- [x] Remove obsolete workflow-token warning language from repo guidance.
- [x] Make [PINNED.md](PINNED.md) the explicit live source for image digests.
- [x] Before systemd v262 adoption, audit docs/code for `/run/boot-loader-entries/`, `systemd-sysupdated` D-Bus, and `updatectl` assumptions: [refs/systemd-v262-audit-2026-07-14.md](refs/systemd-v262-audit-2026-07-14.md).
- [x] Record the 2026-07-16 VM e2e milestone from run 29525332901: [refs/vm-e2e-run-29525332901.md](refs/vm-e2e-run-29525332901.md).
- [x] Switch the active install docs from `bootc install to-disk` to `bootc install to-filesystem --root-mount-spec=""` so DPS auto-discovery remains explicit.
- [x] Keep future planning cycles dated and scoped under `refs/`: see the 2026-07-17 SecTime, Frost, OpenWrt, roadmap-gate, hardening, ARM64 board, and firmware workflow refs.
- [x] Record the complete requested-run review separately from green/red workflow status: [refs/ci-evidence-2026-07-21.md](refs/ci-evidence-2026-07-21.md).
- [x] Add a dated systemd-family upstream snapshot and area-scaled contributor map: [refs/systemd-upstream-progress-2026-07-21.md](refs/systemd-upstream-progress-2026-07-21.md) and [assets/upstream-contributor-bubbles.svg](assets/upstream-contributor-bubbles.svg).

## Current Roadmap Research Tasks

These items map [FUTURE.md](FUTURE.md) sections that were missing or only partially represented in the active TODO list.

### Milestone SecTime

- [x] Add a source-backed `refs/` note identifying the active OP-TEE secure time configuration for RK3399 and RK3588, including `CFG_SECURE_TIME_SOURCE_CNTPCT`, AArch64 timer handling, and TF-A `SPD=opteed` integration: [refs/sectime-rk-secure-time-2026-07-17.md](refs/sectime-rk-secure-time-2026-07-17.md).
- [x] Define what yubiOS may safely claim from secure-world time: monotonic within a boot, suspend/resume behavior, normal-world tamper resistance, and power-loss/reboot limits: [refs/sectime-rk-secure-time-2026-07-17.md](refs/sectime-rk-secure-time-2026-07-17.md).
- [x] Add or design an OP-TEE TA/smoke test that records monotonic secure-world reads and expected failure behavior on ROCK 5B/RK3588 and ROCKPro64/RK3399: [refs/sectime-rk-secure-time-2026-07-17.md](refs/sectime-rk-secure-time-2026-07-17.md).
- [x] Draft ADR coverage for which decisions may rely on secure-world time and which require stronger counters, sealed state, or remote-attestation freshness: [refs/sectime-rk-secure-time-2026-07-17.md](refs/sectime-rk-secure-time-2026-07-17.md).

### Milestone Frost

- [x] Add a source-backed `refs/` map of current Panfrost/Rockchip kernel patch points for probe/init, BO create/free, PRIME import, and submit guarding: [refs/frost-panfrost-lockout-2026-07-17.md](refs/frost-panfrost-lockout-2026-07-17.md).
- [x] Determine whether the target kernel can use DRM device-memory cgroup accounting for Panfrost, or whether a minimal cgroup-aware BO accounting prototype is required first: [refs/frost-panfrost-lockout-2026-07-17.md](refs/frost-panfrost-lockout-2026-07-17.md).
- [x] Sketch the U-Boot device-tree/reserved-memory handoff plus secure-monitor SMC or mailbox interface for context quarantine, IOMMU revocation, GPU reset, or power gating: [refs/frost-panfrost-lockout-2026-07-17.md](refs/frost-panfrost-lockout-2026-07-17.md).
- [ ] Prove whether RK3399/RK3588 lockout can target an offending cgroup/context or must fall back to full-GPU reset behavior. Requires kernel prototype plus RK hardware recovery evidence.
- [x] Define tests for false positives, graphics stack recovery, telemetry, logs, owner notification, and owner recovery after a Frost event: [refs/frost-panfrost-lockout-2026-07-17.md](refs/frost-panfrost-lockout-2026-07-17.md).
- [x] Draft ADR coverage for the trust boundary between Linux policy, OP-TEE/TF-A hard cutoff, and user recovery: [refs/frost-panfrost-lockout-2026-07-17.md](refs/frost-panfrost-lockout-2026-07-17.md).

### Milestone Net

- [x] Turn [refs/endlessh-openwrt-fit-2026-07-17.md](refs/endlessh-openwrt-fit-2026-07-17.md) into an OpenWrt package proof plan with feed/package layout, UCI config, procd service behavior, firewall/nftables integration, and WireGuard-zone defaults: [refs/openwrt-deception-proof-plan-2026-07-17.md](refs/openwrt-deception-proof-plan-2026-07-17.md).
- [ ] Build an OpenWrt VM or spare-router proof with a WireGuard-only decoy address pool and an owner-selected notification path.
- [ ] Capture packet-level evidence that scans hit decoys before the real SSH endpoint is discoverable.
- [x] Define logging defaults that avoid storing attempted passwords, private keys, or sensitive payloads, while still preserving useful owner notification evidence: [refs/openwrt-deception-proof-plan-2026-07-17.md](refs/openwrt-deception-proof-plan-2026-07-17.md).
- [x] Draft ADR coverage for the deception trust boundary, notification model, evidence retention, lab-mode exposure, and failure behavior: [refs/openwrt-deception-proof-plan-2026-07-17.md](refs/openwrt-deception-proof-plan-2026-07-17.md).

### FUTURE Promotion Gates

- [x] Before moving any FUTURE item into ADR, SPEC, or implementation, record its trust boundary, recovery behavior, evidence target, required pins/upstream sources, notification/evidence-retention policy when relevant, and production/test artifact separation: [refs/roadmap-promotion-gates-2026-07-17.md](refs/roadmap-promotion-gates-2026-07-17.md).
- [x] Keep post-launch hardware and deferred ideas watch-listed until a specific owner, board or deployment target, evidence target, and recovery plan exist: [refs/roadmap-promotion-gates-2026-07-17.md](refs/roadmap-promotion-gates-2026-07-17.md).

## Current CI Tasks

- [ ] Keep PQ TLS verification visible in CI for OpenSSL 3.5+ and Go 1.24+ defaults; run 29876466349 negotiated TLS 1.3 `X25519MLKEM768`. When the repo toolchain reaches Go 1.26, include `SecP256r1MLKEM768` and `SecP384r1MLKEM1024` in accepted hybrid-group checks.
- [ ] Keep the QEMU zstd EFI zboot workaround version-gated until runner QEMU contains upstream zstd EFI zboot loader support.
- [x] Validate the bcvk virtiofs-root `bootloader-update.service` guard: run 29872832727 reached the guest assertions without the old DirectBoot/virtiofs failure.
- [x] Validate the bcvk root SSH credential path: run 29872832727 authenticated and ran the ARM64 guest-side assertions.
- [x] Confirm `tests/vm/test-fido2-enrollment.sh` still runs when token-dependent operations skip: run 29872832727 executed the enrollment-surface script after the passless layer found no CTAP2 device.
- [ ] Make a swu2f CTAP2 token enumerate inside the ARM64 bcvk guest, then require the LUKS2 FIDO2, homed, and OpenSSH `ed25519-sk` operations to execute instead of skip. The VM scripts now pre-create passless's headless local store, launch it as an observable transient service, and fail closed on every token-dependent operation; completion awaits a fresh dev-image build and VM e2e run.
- [x] Add a native arm64 build/publish leg and multi-architecture manifest merge to `.github/workflows/ci_mkosi-installer.yml`; run 29876111887 proved only the amd64 path, and the workflow now stages both architectures before merging public tags.
- [ ] Keep `dev`/`dev-<sha>` swu2f images isolated from production build and publish paths.
- [ ] Treat old-sha workflow reruns as historical unless the workflow is rerun against current `main`.
- [x] For workflow trigger edits, add narrow path-scoped push triggers only when required for validation.
- [x] Keep Docker Build Policy wiring centralized in `yubiOS-bake.hcl`: every build target inherits the explicit `yubiOS.rego` filename with `reset=true` and `strict=true`, without relying on automatic `Dockerfile.rego` loading. See [refs/docker-bake-consolidation-2026-07-17.md](refs/docker-bake-consolidation-2026-07-17.md).
- [x] Add board variant fields to real-hardware firmware workflows before hardware lanes land: `rock5b-rk3588` as the Path A variant and `rockpro64-rk3399` as another Path A variant. See `.github/workflows/ci_firmware-rk.yml` and [refs/firmware-rk-workflow-2026-07-17.md](refs/firmware-rk-workflow-2026-07-17.md).
- [x] Validate the documented `bootc install to-filesystem` path on a fresh VM or disposable disk, including external partition preparation, mounted `/mnt`, `--skip-finalize`, and omitted `root=` via `--root-mount-spec=""`: [run 29884493346](https://github.com/yubi-OS/yubiOS/actions/runs/29884493346) passed on native amd64 and arm64.

## Current ARM64 Tasks

- [x] Choose the first Path A board for production-root proof: Radxa ROCK 5B / RK3588 is on pause; ROCKPro64 / RK3399 is supported per ADR-029.
- [ ] Rehearse ROTPK/fuse provisioning on sacrificial hardware before production language.
- [ ] Prove OP-TEE, StandaloneMM, RPMB-backed variables, fTPM NV, and U-Boot UEFI on ROCKPro64 hardware first, then carry the supported evidence to ROCK 5B.
- [ ] Record exact TF-A, OP-TEE, StandaloneMM/RPMB, and U-Boot config evidence for Path A, including `CFG_RPMB_FS`, `CONFIG_EFI_MM_COMM_TEE`, and `CONFIG_SUPPORT_EMMC_RPMB`.
- [ ] Supply ROCK 5B builds with a licensed, immutable, checksum-verified RK3588 DDR/TPL blob and require `u-boot-rockchip.bin`; run 29869527608 published a diagnostic bundle without that bootable image.
- [x] Document Path A vs Path B status per board, starting with `rock5b-rk3588` and `rockpro64-rk3399`: [refs/arm64-rk-board-status-2026-07-17.md](refs/arm64-rk-board-status-2026-07-17.md).

## Current Security Tasks

- [x] Audit services for `ConditionSecurity=measured-os` where enrollment or signing behavior must not run on an unmeasured boot: [refs/systemd-hardening-audit-2026-07-17.md](refs/systemd-hardening-audit-2026-07-17.md).
- [x] Audit `RestrictFileSystems=` separately from the v261 `RestrictFileSystemAccess=` control: [refs/systemd-hardening-audit-2026-07-17.md](refs/systemd-hardening-audit-2026-07-17.md).
- [x] Keep CHIPSEC first-boot validation scoped as a one-shot exception and document firmware-warning behavior: the unit and Bats coverage enforce the one-shot exception, while `run-firstboot-check.sh` documents `PASS`/`WARN`/`FAILED` semantics and informational WPBT/Computrace evidence.
- [ ] Add or refresh real-hardware YubiKey validation evidence for FIDO2 unlock and homed flows.
- [x] Keep recovery paths documented before enabling any feature that can lock an owner out: [refs/roadmap-promotion-gates-2026-07-17.md](refs/roadmap-promotion-gates-2026-07-17.md).

## Current Supply-Chain Tasks

- [ ] Update [PINNED.md](PINNED.md) for every base-image/tool digest change.
- [x] Pin the BuildKit daemon independently, derive `SOURCE_DATE_EPOCH` from the source commit, clamp OCI/layer timestamps, and enforce two isolated OCI-layout builds for production and dev: [refs/reproducible-builds-2026-07-22.md](refs/reproducible-builds-2026-07-22.md).
- [ ] Replace live Fedora/Debian repository resolution with immutable snapshots plus exact package/toolchain closure before claiming later rebuildability.
- [x] Separate installer and TF-A signature-bearing envelopes—including the root-resident `systemd-boot*.efi.signed` file—from canonical unsigned subjects in the blocking ARM64 comparisons; retain both envelope digests without treating random keys/signatures as equality subjects.
- [x] Preseed pinned EDK2 with commit- and platform-scoped deterministic stack-cookie lists, then enforce two clean ARM64 component builds for every firmware board.
- [ ] Approve a checksum-pinned RK3588 DDR/TPL input before firmware equality can cover the final bootable ROCK 5B image.
- [ ] Verify package floors after digest bumps: systemd target, pam-u2f >= 1.3.1, OpenSSL 3.5+, and Go 1.24+ where relevant.
- [x] Keep production, installer, firmware, and dev/test artifacts clearly labeled and non-overlapping: [refs/firmware-rk-workflow-2026-07-17.md](refs/firmware-rk-workflow-2026-07-17.md).
- [ ] Preserve provenance/SBOM expectations for published artifacts.
- [x] Keep production bootc (`latest`, `<sha>`), dev/test (`dev`, `dev-<sha>`), and installer (`installer`, `installer-<sha>`) tags board-neutral unless the OS or installer artifact actually diverges by board. Firmware is now the only board-scoped tag family.
- [x] Publish board-scoped firmware tags under the existing `0mniteck/yubios` namespace: `firmware-rock5b-rk3588`, `firmware-rock5b-rk3588-<sha>`, `firmware-rockpro64-rk3399`, and `firmware-rockpro64-rk3399-<sha>`, plus the QEMU baseline tags documented in [refs/arm64-rk-board-status-2026-07-17.md](refs/arm64-rk-board-status-2026-07-17.md).

## Watch List

- Run 29525332901 proved the ARM64 lane can boot the dev image to Fedora login with the pinned QEMU workaround; keep watching for runner QEMU refreshes before removing that workaround.
- Run 29872832727 retired the old root-SSH and DirectBoot bootloader-update blockers. Its remaining VM gap is narrower: passless starts, but no CTAP2 token enumerates, so token-dependent assertions skip.
- Run 29869527608 proves the QEMU fTPM/StandaloneMM integration and board-specific compilation, but not physical-board behavior. ROCK 5B additionally lacks the required real DDR/TPL input and combined boot image.
- `.github/workflows/ci_firmware-rk.yml` is the orchestrated firmware lane. The removed `ci_test-int.yml` workflow is historical context only; do not restore its `yubiOS firmware` state to the top-level `ci.yml` chain.
- systemd v262 removes `/run/boot-loader-entries/` support and the experimental `systemd-sysupdated` D-Bus API; the 2026-07-14 audit found no repo dependency, but future update UX should stay on UAPI.1/BLS and Varlink/systemd-sysupdate rather than removed interfaces or unaudited `updatectl` assumptions.
- systemd v262 renames `systemd-sysupdate.service`/`.timer` to `systemd-sysupdate-update.service`/`.timer`; verify compatibility symlinks before adding units against the old names.
- Go 1.26 expands default hybrid PQ TLS key exchanges beyond `X25519MLKEM768`; tests should assert acceptable policy rather than a single hard-coded group.
- `bootc install to-filesystem --root-mount-spec=""` is now the documented install baseline for DPS auto-discovery; keep watching for installer UX that can prepare and mount the target filesystems safely.
- `systemd-sysinstall` may become useful for guided install UX, but the current repart/bootc model remains the baseline.
- LUO/KHO may matter for appliance/server deployments, but A/B reboot remains correct for the current desktop/laptop thesis.
- U-Boot FIDO2/U2F console authentication remains idea-stage until USB HID, crypto, and recovery risks are audited.
- ORAS artifact media types may replace `FROM scratch` carrier images when registry support and UX improve.
- systemd v262 is active upstream work rather than the current pinned baseline; track credential-sealing compatibility, the sysupdate unit rename, cryptenroll's first-boot/Varlink work, and the FIDO2 zero-length-HMAC rejection in [refs/systemd-upstream-progress-2026-07-21.md](refs/systemd-upstream-progress-2026-07-21.md).

## Retired From Active TODO

- Treating OpenSSL PQ hybrid support as future-only: current OpenSSL 3.5+ defaults already include `X25519MLKEM768`.
- Treating swu2f Layer 2 as merely planned: the TEST-only dev image path exists and must stay isolated.
- Repeating old digest examples from workflow logs as current pins: use [PINNED.md](PINNED.md).
- Describing ARM64 as secondary: ADR-023 makes ARM64 primary and x86-64 supported secondary.
