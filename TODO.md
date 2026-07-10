# yubiOS — TODO / Future Work
_Last updated: July 10, 2026 (ARM64 CI runner policy updated: non-KVM lanes use self-hosted Linux ARM64 GPU runners; VM/KVM lane remains self-hosted Linux ARM64 KVM)_

## High priority

- [x] Wire yubiOS-sudo PAM config into /etc/pam.d/sudo via Containerfile (PR #1)
- [x] Add /usr/bin/ symlinks for yubiOS-enroll-* commands via Containerfile (PR #1)
- [x] mkosi profiles: desktop (GNOME), minimal, surface-x86, surface-arm64 (PR #2)
- [x] Merge PR #12 — shellcheck clean + OPA/Rego build policy (yubiOS.rego) — merged June 24
- [x] Merge PR #13 — systemd-homed LUKS2+FIDO2 home encryption (ADR-009) — merged June 24
- [x] ARM64 multi-arch profile documented — ADR-017, MITIGATE.md, README.md, ARCHITECTURE.md updated (June 24)
- [x] Bump fedora-bootc:45 to live post-June-19 digest for systemd 261 (ADR-016) (#14, PR #31) — merged June 26; live digest `sha256:b7b34d87…` (45.20260625.0); old `sha256:6a60ff82…` was dead/404
- [x] Validate systemd-sbsign + libykcs11 PKCS#11 URI for ECC slot 9c (ADR-008) (#17, PR #32) — merged June 26; spec-validated, test migrated to systemd-sbsign + osslsigncode
- [ ] Test LUKS2 FIDO2 unlock end-to-end in a VM (#20, PR #33) — hardware-free e2e test on `feat/luks-fido2-e2e-test` (`tests/vm/test-luks-fido2-ci.sh` drives `bcvk ephemeral run --swtpm --swu2f`). **PR CI now GREEN** — the pull_request build was hitting BLOCKER-008 disk exhaustion (native snapshotter); fixed on the PR branch (dockerd native→overlayfs, commit `4450fd4`, mirrors main `e74dadf`); all 5 jobs success @ `4450fd4` (run 28231776269). swtpm `/dev/tpm0` + measured-os + swu2f Layer 1/CTAP1 (pam-u2f) legs run; CTAP2 legs (cryptenroll `--fido2` + homed) now have an in-guest authenticator via **PR #40** (swu2f Layer 2, below). Follow-up from run 29065584237/job 86297785033: the throwaway LUKS reopen path now uses `systemd-cryptsetup attach ... fido2-device=auto`, because `systemd-cryptenroll` writes a systemd FIDO2 token that plain `cryptsetup open --token-only` cannot consume. Follow-up from run 29077714028/job 86313067649: ARM64 `docker.io/0mniteck/yubios:dev` now reaches a known bcvk harness limitation (`unable to handle EFI zboot image with "zstd" compression`); VM scripts classify that exact DirectBoot/zstd case as an explicit skip (exit 77) so push-triggered workflow runs stay actionable until bcvk gains zstd EFI zboot support or the test image switches compression. Research and CI remediation captured in `refs/zstd-efi-zboot-bcvk.md`; `ci_test-vm.yml` now builds pinned upstream QEMU commit `3a18e8a25992d1643707e2cebdd6e9bb2bd7d3b9` for the ARM64 bcvk lane and bind-mounts it into bcvk's inner podman container so DirectBoot can unpack zstd EFI zboot kernels, with firmware/stub boot mode still tracked as the longer-term fidelity improvement. BLOCKER-009 compile-fix RESOLVED. Physical-YubiKey passthrough still needs hardware (BLOCKER-005). Draft — no merge (merge-ready alongside #40, pending Jenny).

- [x] **Multi-arch main CI green + OS published to Docker Hub.** `docker.io/0mniteck/yubios:latest` (linux/amd64 + linux/arm64) is the **primary download**, built by `yubiOS-ci.yml` `merge-manifest` (run #113, `bfbc38f`); SLSA provenance + SBOM attached. Containerfile base bumped to live quay `fedora-bootc:45` digest `sha256:8a1c786…` (old `b7b34d8…` 404d). README `Get yubiOS` + design diagram updated; PINNED.md synced.

## ARM64 Phase F — fork-CI + integration (in progress)

Owned ARM64 fTPM trust-chain CI (ADR-018/019/020). Each component fork now has a `ci_test.yml` that cross-builds it for aarch64; ARM64 non-KVM lanes are now targeted at `[self-hosted, Linux, ARM64, GPU]`, while the VM/e2e KVM lane stays on `[self-hosted, Linux, ARM64, KVM]` (bare runners, fail-fast:false, pinned SHAs): The top-level `ci.yml` orchestrator sequences these fork, integration, image, installer, VM, and verification workflows through explicit callbacks from each `.yml` workflow into `ci.yml`, carrying the current state plus the original dispatch defaults across the chain.

- [x] C1 — arm-trusted-firmware: TF-A BL31 + TBB FIP (`f9e1064`)
- [x] C2 — optee_os: OP-TEE core + TA-devkit (`cc18472`)
- [x] C3 — optee_ftpm: fTPM TA, UUID bc50d971… (`28abbe7`)
- [x] C4 — ms-tpm-20-ref: TPM 2.0 reference build (`db43de7`)
- [x] C5 — u-boot: BL33 + fTPM/measured-boot configs (`ef2ab32`)
- [x] C6 — edk2: StandaloneMM core (`9f13e2a`)
- [x] R1 — `yubiOS.rego` build policy live + passing on the main CI build job
- [x] V1 — `tests/vm/*.sh` wired into `ci_test-vm.yml` (`3f46cf0`), honest skips where HW/CTAP2-gated
- [x] edk2-platforms forked into the org — supplies `PlatformStandaloneMmRpmb.dsc` → `BL32_AP_MM.fd` (C6 fork ships StMM core only)
- [x] **INT** integration CI (`ci_test-int.yml`): **GREEN on both arches, fully restored** (run 28903617073, commit `5476e1f`, July 7) — Stage 1 (BL32_AP_MM.fd) + Stage 2 (OP-TEE fold w/ StMM + fTPM + TF-A FIP) + Stage 3 (QEMU e2e: StMM loads at 0x40004000 with FVB init, fTPM Early TA probed + functional, `tpm2 init/startup/self_test` → YUBIOS_TPM_OK). #41 closed: root cause was missing `CFG_CORE_HEAP_SIZE=524288 CFG_TEE_RAM_VA_SIZE=0x00400000` plus QEMU-has-no-RPMB (OpTeeRpmbFv init fails → FixupPcd garbage → deref 0); fixed with those mem flags + `CFG_STMM_VOLATILE_STORAGE` (optee_os `feat/stmm-volatile-storage-ci` @ `440b10c`). fTPM `TA_FLAG_DEVICE_ENUM_TEE_STORAGE_PRIVATE` restored as production default; the QEMU lane opts out via `CFG_FTPM_VOLATILE_NV=y` (optee_ftpm `feat/volatile-nv-ci` @ `5e09cdb`). `CONFIG_EFI_MM_COMM_TEE=y` and `CFG_RPMB_FS=y` restored. All in-CI sed/python patches removed; CI-only behavior lives on the two unmerged feature branches pinned by SHA. Real hardware keeps RPMB-backed storage for both StMM and fTPM.

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
- [x] CI deployed + green across yubiOS (multi-arch native matrix), bcvk (multi-arch Rust test/clippy), mkosi (profile + shellcheck + ruff) on `.github/workflows/` via the fine-grained PAT (Workflows: Write). Specs live in `refs/`; yml staged in `documents/.../ci-workflows/` (#22)
- [ ] Add `osslsigncode` to image (mkosi.conf + Containerfile) so the PKCS#11 verify step in tests/validate-pkcs11-uri.sh is live
- [x] Merge `yubi-OS/mkosi#2` (yubiOS build profile) — merged July 8 (`b2b1ea6`); yubiOS-ci.yml installs mkosi from `@main` (#10)
- [x] CI mkosi image build + SoftHSM PKCS#11 signing — `ci_mkosi-installer.yml` green July 8; publishes `0mniteck/yubios:installer` (+`installer-<sha>`) per ADR-022 (#10 closed)
- [x] Firmware bundle tag — `ci_test-int.yml` Stage 4 publishes QEMU-validated `0mniteck/yubios:firmware` (+`firmware-<sha>`) after the e2e gate (ADR-022)
- [ ] v261 test coverage scaffolding — systemd-sbsign UKI verify (osslsigncode vs PIV cert), ConditionSecurity=measured-os + RestrictFileSystems= enroll-unit gates, pam-u2f stack — draft PR #38 (`test/v261-coverage-T5`). **PR CI now GREEN** @ `43c2728` (run 28231778451, all 5 jobs success): build fixed (mkdir /mnt/docker + dockerd overlayfs `--data-root=/mnt/docker`, commit `4c19b1d`); unit-test 14 `systemd-analyze verify` had a REAL fail (Exec* binaries absent on the bare runner) — rewritten to stage a minimal root with exec stubs per Exec*= path so directives validate honestly (bogus key still → exit 1), commit `43c2728`. Draft — no merge (merge-ready, pending Jenny).

## Low priority / Research

- [x] composefs + verity full root verification (PR #5)
- [x] Multi-user YubiKey support — enroll_pam_user() in lib.sh (PR #3)
- [x] Investigate FIDO2 Large Blob extension — yubiOS-enroll-largblob (PR #7)
- [x] CTAP 2.1 minimum PIN length enforcement — check_fido2_pin_length() in lib.sh (PR #3)
- [ ] chipsec first-boot validation (portable service or sysext, per ADR-010 DPS) (#24)
- [ ] Post-quantum TLS for yubiOS services (X25519MLKEM768 / OpenSSL 3.5+) (#26)
- [ ] bcvk CI — software FIDO2 emulator (swu2f) for enrollment tests without physical YubiKey (#25 — `[post-launch]`; T3 branch work DONE) — swu2f landed on canonical bcvk branch `feat/swtpm-ci` (referenced directly, NEVER merged, like the mkosi fork). Two-layer design: Layer 1 = QEMU `u2f-emulated` (libu2f-emu) USB-HID CTAP1 token, covers pam-u2f; Layer 2 = in-guest `/dev/uhid` CTAP2 authenticator for systemd-cryptenroll `--fido2-device` (hmac-secret). **Layer 2 now shipped as yubiOS PR #40** (`feat/swu2f-layer2-ctap2-fixture`, commit `ab37a34`): in-guest `passless` (pando85/passless v0.11.2, soft-fido2 backend with full hmac-secret) in a TEST-only mkosi profile (NOT prod RoT — YubiKey stays, ADR-003), wired into the #33 e2e to un-gate the SKIP'd cryptenroll/homed legs. Commented on #33 + #25. Draft — no follower merge (leader merges once green; needs human cargo build + Signed-off-by). swtpm (T2) on the same branch = host-side QEMU vTPM emulator device (DirectBoot breaks the in-guest systemd-tpm2-swtpm.service path; ADR-016 §F1, see knowledge/swtpm-ci-approach.md). Dup `feature/swtpm-ci` (draft PR #4) closed.
- [ ] One-time hardware smoke test of the systemd-sbsign PKCS#11 path (slot 9c) before first production signing

## Post-launch (see FUTURE.md)

- [ ] ARM64-owned root of trust: TF-A + OP-TEE + ms-tpm-20-ref fTPM + U-Boot measured boot — gives ARM64 a yubiOS-owned TPM 2.0; YubiKey stays primary RoT. Decisions: **ADR-018** (owned secure-world stack), **ADR-019** (dual provisioning paths: fuse-enforcing vs measured/attested), **ADR-020** (U-Boot as UEFI firmware + StandaloneMM variable store). Full plan in FUTURE.md; diagrams in ARCHITECTURE.md §7. Skills: arm-trusted-firmware-optee, ftpm-optee-tpm. (#23, PR #35) — **Phase F active (fork-CI matrix green — see the ARM64 Phase F section above; INT in flight):** originally reproducible QEMU `virt` build recipe (TF-A `PLAT=qemu` + OP-TEE `vexpress-qemu_armv8a` + ms-tpm-20-ref `@98b60a44` fTPM + U-Boot/UEFI) + `/dev/tpm0` PCR-extend verifier pushed to `feat/arm64-ftpm-phase-f0` (draft PR #35, commit `d01075f`); live boot verification human-gated
- [ ] Easter egg: "Konami enrollment" — see FUTURE.md § Easter Egg
- [ ] U-Boot console/shell authentication gate (FIDO2/U2F) — scoped in **ADR-027** (ARM64-only, CTAP1/U2F, hooks abortboot() alongside CONFIG_AUTOBOOT_ENCRYPTION); not yet implemented, waiting on Phase F0-F3 + a standalone QEMU USB-HID spike. See FUTURE.md § Idea (unscoped).
