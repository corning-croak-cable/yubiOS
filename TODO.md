# yubiOS TODO

Last reviewed: 2026-07-11
Status: active task list

Use this file for current work. Completed historical context belongs in merged PRs, ADRs, or dated refs.

## Current Documentation Tasks

- [x] Add a dated planning-cycle note for the 2026-07-11 research pass: [refs/planning-cycle-2026-07-11.md](refs/planning-cycle-2026-07-11.md).
- [x] Refresh refs that described v261, swu2f, swtpm, PKCS#11 signing, and zstd EFI zboot as future or stale.
- [x] Remove obsolete workflow-token warning language from repo guidance.
- [x] Make [PINNED.md](PINNED.md) the explicit live source for image digests.
- [ ] Keep future planning cycles dated and scoped under `refs/`.

## Current CI Tasks

- [ ] Keep PQ TLS verification visible in CI for OpenSSL 3.5+ and Go 1.24+ defaults.
- [ ] Keep the QEMU zstd EFI zboot workaround pinned until runner QEMU contains the upstream fix.
- [ ] Keep `dev`/`dev-<sha>` swu2f images isolated from production build and publish paths.
- [ ] Treat old-sha workflow reruns as historical unless the workflow is rerun against current `main`.
- [ ] For workflow trigger edits, add narrow path-scoped push triggers only when required for validation.

## Current ARM64 Tasks

- [ ] Choose the first Path A board for production-root proof, with RK3588 still preferred.
- [ ] Rehearse ROTPK/fuse provisioning on sacrificial hardware before production language.
- [ ] Prove OP-TEE, StandaloneMM, RPMB-backed variables, fTPM NV, and U-Boot UEFI on hardware.
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
- [ ] Keep production, installer, firmware, and dev/test artifacts clearly labeled and non-overlapping.
- [ ] Preserve provenance/SBOM expectations for published artifacts.

## Watch List

- `systemd-sysinstall` may become useful for guided install UX, but the current repart/bootc model remains the baseline.
- LUO/KHO may matter for appliance/server deployments, but A/B reboot remains correct for the current desktop/laptop thesis.
- U-Boot FIDO2/U2F console authentication remains idea-stage until USB HID, crypto, and recovery risks are audited.
- ORAS artifact media types may replace `FROM scratch` carrier images when registry support and UX improve.

## Retired From Active TODO

- Treating OpenSSL PQ hybrid support as future-only: current OpenSSL 3.5+ defaults already include `X25519MLKEM768`.
- Treating swu2f Layer 2 as merely planned: the TEST-only dev image path exists and must stay isolated.
- Repeating old digest examples from workflow logs as current pins: use [PINNED.md](PINNED.md).
- Describing ARM64 as secondary: ADR-023 makes ARM64 primary and x86-64 supported secondary.
