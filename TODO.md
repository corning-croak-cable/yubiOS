# yubiOS TODO

Last reviewed: 2026-07-14
Status: active task list
Latest targeted audit: [refs/systemd-v262-audit-2026-07-14.md](refs/systemd-v262-audit-2026-07-14.md).
Latest broad research note: [refs/research-refresh-2026-07-11.md](refs/research-refresh-2026-07-11.md).

Use this file for current work. Completed historical context belongs in merged PRs, ADRs, or dated refs.

## Current Documentation Tasks

- [x] Add a dated planning-cycle note for the 2026-07-11 research pass: [refs/planning-cycle-2026-07-11.md](refs/planning-cycle-2026-07-11.md).
- [x] Add a scheduled upstream research refresh note: [refs/research-refresh-2026-07-11.md](refs/research-refresh-2026-07-11.md).
- [x] Refresh refs that described v261, swu2f, swtpm, PKCS#11 signing, and zstd EFI zboot as future or stale.
- [x] Remove obsolete workflow-token warning language from repo guidance.
- [x] Make [PINNED.md](PINNED.md) the explicit live source for image digests.
- [x] Before systemd v262 adoption, audit docs/code for `/run/boot-loader-entries/`, `systemd-sysupdated` D-Bus, and `updatectl` assumptions: [refs/systemd-v262-audit-2026-07-14.md](refs/systemd-v262-audit-2026-07-14.md).
- [ ] Keep future planning cycles dated and scoped under `refs/`.

## Current CI Tasks

- [ ] Keep PQ TLS verification visible in CI for OpenSSL 3.5+ and Go 1.24+ defaults; when the repo toolchain reaches Go 1.26, include `SecP256r1MLKEM768` and `SecP384r1MLKEM1024` in accepted hybrid-group checks.
- [ ] Keep the QEMU zstd EFI zboot workaround version-gated until runner QEMU contains upstream zstd EFI zboot loader support.
- [ ] Keep `dev`/`dev-<sha>` swu2f images isolated from production build and publish paths.
- [ ] Treat old-sha workflow reruns as historical unless the workflow is rerun against current `main`.
- [ ] For workflow trigger edits, add narrow path-scoped push triggers only when required for validation.
- [ ] If build policy wiring moves into Bake, keep Docker `target.policy` keys aligned with CLI policy flags and avoid duplicate `Dockerfile.rego` loading assumptions.

## Current ARM64 Tasks

- [ ] Choose the first Path A board for production-root proof, with RK3588 still preferred.
- [ ] Rehearse ROTPK/fuse provisioning on sacrificial hardware before production language.
- [ ] Prove OP-TEE, StandaloneMM, RPMB-backed variables, fTPM NV, and U-Boot UEFI on hardware.
- [ ] Record exact TF-A, OP-TEE, StandaloneMM/RPMB, and U-Boot config evidence for Path A, including `CFG_RPMB_FS`, `CONFIG_EFI_MM_COMM_TEE`, and `CONFIG_SUPPORT_EMMC_RPMB`.
- [ ] Verify the same signed UKI boots across ARM64 and x86-64 paths.
- [ ] Document Path A vs Path B status per board.

## Current Security Tasks

- [ ] Audit services for `ConditionSecurity=measured-os` where enrollment or signing behavior must not run on an unmeasured boot.
- [ ] Audit `RestrictFileSystems=` separately from the v261 `RestrictFileSystemAccess=` control.
- [ ] Keep CHIPSEC first-boot validation scoped as a one-shot exception and document firmware-warning behavior.
- [ ] Add or refresh real-hardware YubiKey validation evidence for FIDO2 unlock and homed flows.
- [ ] Keep recovery paths documented before enabling any feature that can lock an owner out.

## Current Supply-Chain Tasks

- [ ] Update [PINNED.md](PINNED.md) for every base-image/tool digest change.
- [ ] Verify package floors after digest bumps: systemd target, pam-u2f >= 1.3.1, OpenSSL 3.5+, and Go 1.24+ where relevant.
- [ ] Audit bootc 1.11+ install docs/code for DPS behavior: `to-disk` still injects `root=UUID=`, while DPS auto-discovery requires the explicit `to-filesystem --root-mount-spec=""` path and a Boot Loader Interface-capable bootloader.
- [ ] Keep production, installer, firmware, and dev/test artifacts clearly labeled and non-overlapping.
- [ ] Preserve provenance/SBOM expectations for published artifacts.

## Watch List

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
