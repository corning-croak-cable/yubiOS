# yubiOS — TODO / Future Work
_Last updated: June 24, 2026_

## High priority

- [x] Wire yubiOS-sudo PAM config into /etc/pam.d/sudo via Containerfile (PR #1)
- [x] Add /usr/bin/ symlinks for yubiOS-enroll-* commands via Containerfile (PR #1)
- [x] mkosi profiles: desktop (GNOME), minimal, surface-x86, surface-arm64 (PR #2)
- [x] Merge PR #12 — shellcheck clean + OPA/Rego build policy (yubiOS.rego) — merged June 24
- [x] Merge PR #13 — systemd-homed LUKS2+FIDO2 home encryption (ADR-009) — merged June 24
- [x] ARM64 multi-arch profile documented — ADR-017, MITIGATE.md, README.md, ARCHITECTURE.md updated (June 24)
- [ ] Test LUKS2 FIDO2 unlock end-to-end in a VM with YubiKey passthrough
- [ ] Validate systemd-sbsign + libykcs11 PKCS#11 URI for ECC slot 9c (ADR-008)

## Medium priority

- [x] FIDO2-only Secure Boot path — age-plugin-fido2-hmac (PR #6)
- [x] Backup YubiKey enrollment UI — yubiOS-enroll-backup (PR #3)
- [x] TOTP enrollment via ykman oath — yubiOS-enroll-totp (PR #3)
- [x] GPG/OpenPGP applet integration — yubiOS-enroll-gpg (PR #3)
- [x] surface-x86 and surface-arm64 mkosi profile integration (PR #2)
- [ ] Migrate FinalizeScripts: sbsigntool → systemd-sbsign (ADR-008)
- [ ] Remove sbsigntool package from Containerfile once systemd-sbsign migration done
- [ ] Deploy CI workflows to .github/workflows/ in yubiOS, bcvk, mkosi (manual — token lacks workflow scope)
- [ ] Set up Renovate/Dependabot for fedora-bootc:45 digest tracking (ADR-015)
- [ ] Bump fedora-bootc:45 digest to post-June-19 point release for systemd 261 (ADR-016)
- [ ] Add ConditionSecurity=measured-os to yubiOS-enroll.service (ADR-016)
- [ ] Enable systemd-tpm2-swtpm.service in bcvk CI VMs for TPM2 code path coverage (ADR-016)

## Low priority / Research

- [x] composefs + verity full root verification (PR #5)
- [x] Multi-user YubiKey support — enroll_pam_user() in lib.sh (PR #3)
- [x] Investigate FIDO2 Large Blob extension — yubiOS-enroll-largblob (PR #7)
- [x] CTAP 2.1 minimum PIN length enforcement — check_fido2_pin_length() in lib.sh (PR #3)
- [ ] Evaluate RestrictFileSystemAccess= (BPF LSM) for enrollment units — verify CONFIG_BPF_LSM=y first (ADR-016)
- [ ] chipsec first-boot validation (portable service or sysext, per ADR-010 DPS)
- [ ] Post-quantum TLS for yubiOS services (X25519MLKEM768 / OpenSSL 3.5+)
- [ ] bcvk CI — software FIDO2 emulator for enrollment tests without physical YubiKey

## Post-launch (see FUTURE.md)

- [ ] ARM64-owned root of trust: TF-A + OP-TEE + ms-tpm-20-ref fTPM + U-Boot measured boot — gives ARM64 a yubiOS-owned TPM 2.0; YubiKey stays primary RoT. Decisions: **ADR-018** (owned secure-world stack), **ADR-019** (dual provisioning paths: fuse-enforcing vs measured/attested), **ADR-020** (U-Boot as UEFI firmware + StandaloneMM variable store). Full plan in FUTURE.md; diagrams in ARCHITECTURE.md §7. Skills: arm-trusted-firmware-optee, ftpm-optee-tpm.
