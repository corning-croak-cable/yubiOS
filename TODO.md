# yubiOS — TODO / Future Work
_Last updated: June 26, 2026_

## High priority

- [x] Wire yubiOS-sudo PAM config into /etc/pam.d/sudo via Containerfile (PR #1)
- [x] Add /usr/bin/ symlinks for yubiOS-enroll-* commands via Containerfile (PR #1)
- [x] mkosi profiles: desktop (GNOME), minimal, surface-x86, surface-arm64 (PR #2)
- [x] Merge PR #12 — shellcheck clean + OPA/Rego build policy (yubiOS.rego) — merged June 24
- [x] Merge PR #13 — systemd-homed LUKS2+FIDO2 home encryption (ADR-009) — merged June 24
- [x] ARM64 multi-arch profile documented — ADR-017, MITIGATE.md, README.md, ARCHITECTURE.md updated (June 24)
- [x] Bump fedora-bootc:45 to live post-June-19 digest for systemd 261 (ADR-016) (#14, PR #31) — merged June 26; live digest `sha256:b7b34d87…` (45.20260625.0); old `sha256:6a60ff82…` was dead/404
- [x] Validate systemd-sbsign + libykcs11 PKCS#11 URI for ECC slot 9c (ADR-008) (#17, PR #32) — merged June 26; spec-validated, test migrated to systemd-sbsign + osslsigncode
- [ ] Test LUKS2 FIDO2 unlock end-to-end in a VM with YubiKey passthrough (#20, PR #33) — needs physical YubiKey + bcvk (BLOCKER-005)

## Medium priority

- [x] FIDO2-only Secure Boot path — age-plugin-fido2-hmac (PR #6)
- [x] Backup YubiKey enrollment UI — yubiOS-enroll-backup (PR #3)
- [x] TOTP enrollment via ykman oath — yubiOS-enroll-totp (PR #3)
- [x] GPG/OpenPGP applet integration — yubiOS-enroll-gpg (PR #3)
- [x] surface-x86 and surface-arm64 mkosi profile integration (PR #2)
- [x] Migrate FinalizeScripts + enroll scripts: sbsigntool → systemd-sbsign (ADR-008) (#16, PR #29) — merged June 26
- [x] Remove sbsigntool package (part of #16, PR #29) — merged June 26; sign-uki-fido2.sh / enroll-sb.sh / enroll-sb-fido2.sh now use systemd-sbsign
- [x] Sync README + ADR-002/003/008/015 from systemd v257 → v261 (PR #36) — merged June 26
- [x] Set up Renovate config for fedora-bootc:45 digest tracking (ADR-015) (#19, PR #30) — merged June 26; **app install still manual (BLOCKER-004)**
- [x] Add ConditionSecurity=measured-os to yubiOS-enroll.service (ADR-016) (#15, PR #27) — merged June 26
- [x] Enable systemd-tpm2-swtpm.service in bcvk CI VMs for TPM2 coverage (ADR-016) (#21, PR #34) — merged June 26; **cross-repo `yubi-OS/bcvk` issue #3 still open (BLOCKER-006)**
- [x] Evaluate + add RestrictFileSystems= (BPF LSM) to enrollment units (ADR-016) (#18, PR #28) — merged June 26; CONFIG_BPF_LSM=y verified active on live base (BLOCKER-007 cleared)
- [ ] Deploy CI workflows to .github/workflows/ in yubiOS, bcvk, mkosi (manual — token lacks workflow scope) (#22) — drafts staged in `2026/` and `documents/.../ci-workflows/`
- [ ] Add `osslsigncode` to image (mkosi.conf + Containerfile) so the PKCS#11 verify step in tests/validate-pkcs11-uri.sh is live
- [ ] v261 test coverage scaffolding — systemd-sbsign UKI verify (osslsigncode vs PIV cert), ConditionSecurity=measured-os + RestrictFileSystems= enroll-unit gates, pam-u2f stack — draft PR #38 (`test/v261-coverage-T5`, commit `56b05b5`); no merge, pending CI

## Low priority / Research

- [x] composefs + verity full root verification (PR #5)
- [x] Multi-user YubiKey support — enroll_pam_user() in lib.sh (PR #3)
- [x] Investigate FIDO2 Large Blob extension — yubiOS-enroll-largblob (PR #7)
- [x] CTAP 2.1 minimum PIN length enforcement — check_fido2_pin_length() in lib.sh (PR #3)
- [ ] chipsec first-boot validation (portable service or sysext, per ADR-010 DPS) (#24)
- [ ] Post-quantum TLS for yubiOS services (X25519MLKEM768 / OpenSSL 3.5+) (#26)
- [ ] bcvk CI — software FIDO2 emulator (swu2f) for enrollment tests without physical YubiKey (#25, T3) — bcvk swtpm branch landed (T2): canonical `feat/swtpm-ci` now @`8896f1e6` (host-side QEMU vTPM emulator device: `swtpm socket` → `-tpmdev emulator` → arch-aware `tpm-crb`/`tpm-tis-device`). NOTE: in-guest `systemd-tpm2-swtpm.service` route abandoned — bcvk DirectBoot extracts kernel+initrd from the UKI, breaking the systemd-stub chain the service needs, so the guest path can’t yield `/dev/tpm0` (flagged ADR-016 §F1; see knowledge/swtpm-ci-approach.md). Duplicate `feature/swtpm-ci` (draft PR #4) closed as dup. swu2f T3 extends `feat/swtpm-ci` — in progress; bcvk referenced, never merged
- [ ] One-time hardware smoke test of the systemd-sbsign PKCS#11 path (slot 9c) before first production signing

## Post-launch (see FUTURE.md)

- [ ] ARM64-owned root of trust: TF-A + OP-TEE + ms-tpm-20-ref fTPM + U-Boot measured boot — gives ARM64 a yubiOS-owned TPM 2.0; YubiKey stays primary RoT. Decisions: **ADR-018** (owned secure-world stack), **ADR-019** (dual provisioning paths: fuse-enforcing vs measured/attested), **ADR-020** (U-Boot as UEFI firmware + StandaloneMM variable store). Full plan in FUTURE.md; diagrams in ARCHITECTURE.md §7. Skills: arm-trusted-firmware-optee, ftpm-optee-tpm. (#23, PR #35) — **Phase F0 active:** reproducible QEMU `virt` build recipe (TF-A `PLAT=qemu` + OP-TEE `vexpress-qemu_armv8a` + ms-tpm-20-ref `@98b60a44` fTPM + U-Boot/UEFI) + `/dev/tpm0` PCR-extend verifier pushed to `feat/arm64-ftpm-phase-f0` (draft PR #35, commit `d01075f`); live boot verification human-gated
- [ ] Easter egg: "Konami enrollment" — see FUTURE.md § Easter Egg
