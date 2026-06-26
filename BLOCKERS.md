# BLOCKERS.md — yubiOS Open Issue Dependency Map

_Last updated: 2026-06-26 (PR-CI: #33+#38 pull_request CI GREEN, swu2f Layer 2 shipped as PR #40; L-CI: BLOCKER-008 RESOLVED — build job dockerd native→overlayfs snapshotter (commit `e74dadf`); dispatch run `28230464416` completed GREEN (all 5 jobs success). BLOCKER-009 resolved. L-PRUNE: orphan branches `feat/bcvk-swtpm-ci` AND `feat/fido2-secure-boot` both deleted — fully superseded by merged main). Maintained alongside TODO.md and ADR.md._

---

## Merge order / dependency chain

```
#17 (PKCS#11 validate) → #16 (sbsign migration FinalizeScripts)

#14 (v261 digest bump)
  ↳ #15 (ConditionSecurity=measured-os)        [needs systemd 261]
  ↳ #18 (RestrictFileSystems=)            [needs systemd 261 + CONFIG_BPF_LSM]

#22 (CI deploy)                                [manual — token scope]
#19 (Renovate)                                 [manual — app install]

#20 (LUKS2 e2e test)                           [hardware + bcvk]
#21 (swtpm CI)                                 [cross-repo: yubi-OS/bcvk]

#23–26 (post-launch)                           [deferred until Phase 0 ships]
```

---

## Hard blockers

### BLOCKER-001: GitHub token lacks `workflow` scope

- **Blocks:** #22 (deploy CI workflows to `.github/workflows/`)
- **Why:** The API token cannot push files into `.github/workflows/`. GitHub requires
  the `workflow` scope for that path.
- **Resolution:** Commit with conn_.. you have onfile SU PAT
- **Workaround:** Yes

### BLOCKER-002: #14 (v261 digest bump) must land before #15 and #18

- **Blocks:** #15 (PR #27 `ConditionSecurity=measured-os`), #18 (PR #28 `RestrictFileSystems=`)
- **Why:** Both directives are systemd 261 features. Current base image predates the
  June 2026 Fedora 45 point release.
- **Resolution:** Merge PR #31 (`feat/v261-base-image`) first. Verify before merging:
  ```sh
  docker run --rm quay.io/fedora/fedora-bootc:45@sha256:6a60ff82da9d2f73aad315233fbffe2ed880a7d695ec9940c0754f84f13db9d6 \
    systemd --version  # must be >= 261
  docker run --rm quay.io/fedora/fedora-bootc:45@sha256:6a60ff82da9d2f73aad315233fbffe2ed880a7d695ec9940c0754f84f13db9d6 \
    rpm -q pam-u2f    # must be >= 1.3.1
  ```
- **New digest staged:** `sha256:6a60ff82da9d2f73aad315233fbffe2ed880a7d695ec9940c0754f84f13db9d6`
  (published 2026-06-24, PR #31 ready)

### BLOCKER-003: #17 (PKCS#11 validation) must complete before #16 FinalizeScripts

- **Blocks:** The FinalizeScripts `systemd-sbsign` invocation in PR #29 (`feat/sbsign-migration`)
- **Why:** The `pkcs11:token=...` URI must be validated against a physical YubiKey before
  writing it into the signed build path. An untested URI silently produces unsigned UKIs.
- **Current state:** PR #29 already removes `sbsigntool` from the package list. The
  FinalizeScripts command swap is the remaining piece, gated on PR #32 completing.
- **Resolution:** Run the validation test in #32, confirm `sbverify` exits 0, then update
  FinalizeScripts in #29.
- **Requires:** Physical YubiKey 5 with firmware >= 5.2.3 (see BLOCKER-005).

### BLOCKER-004: Renovate GitHub App not installed

- **Blocks:** PR #30 (`feat/renovate-digest-tracking`) activating
- **Why:** `renovate.json` is committed but the GitHub App must be enabled on the repo
  for automated PRs to open.
- **Resolution:** Install at https://github.com/apps/renovate and grant access to
  `yubi-OS/yubiOS`.

---

## Hardware / environment blockers

### BLOCKER-005: Physical YubiKey + bcvk required for #20 and #32

- **Blocks:** #20 (LUKS2 FIDO2 e2e test, PR #33), #32 (PKCS#11 URI validation, PR #32)
- **Why:** FIDO2 hmac-secret unlock, PKCS#11 signing, and pam-u2f auth require a physical
  YubiKey 5 (firmware >= 5.2.3). Cannot be emulated in current CI.
- **Workaround for CI:** swtpm (#21) covers measured-boot paths. Software FIDO2 emulator
  (#25) is tracked post-launch.

### BLOCKER-006: swtpm CI work is primarily in yubi-OS/bcvk — RESOLVED (2026-06-26)

- **Was blocking:** #21 (PR #34) landing on its own
- **Why:** Adding swtpm to CI VMs required changes to the bcvk test image definition and
  its workflow in `yubi-OS/bcvk`.
- **Resolution:** Parallel issue `yubi-OS/bcvk#3` opened; swtpm branch `feat/swtpm-ci`
  (commit `2cc8a75`) pushed to `yubi-OS/bcvk` and referenced on #3 — per the
  "bcvk is referenced, never merged" doctrine, #3 stays open as the tracking issue (no merge).
  yubiOS PR #34 (CI workflow integration side) merged June 26. A duplicate `feature/swtpm-ci`
  branch + draft PR #4 from a parallel run were superseded (PR #4 closed); `feat/swtpm-ci`
  is canonical and is what swu2f (#25) extends.

### BLOCKER-007: CONFIG_BPF_LSM=y not yet verified for #18 (`RestrictFileSystems=`)

- **Blocks:** PR #28 (`feat/v261-restrict-filesystem`) being merge-ready
- **Why:** `RestrictFileSystems=` is silently ignored if `CONFIG_BPF_LSM=y` is not
  set in the kernel.
- **Verification (run after #14 merges):**
  ```sh
  docker run --rm quay.io/fedora/fedora-bootc:45@sha256:6a60ff82da9d2f73aad315233fbffe2ed880a7d695ec9940c0754f84f13db9d6 \
    sh -c 'zcat /proc/config.gz | grep CONFIG_BPF_LSM'
  ```
- **Depends on:** BLOCKER-002 (#14) landing first.

### BLOCKER-008: yubiOS CI `build` job runs out of disk — RESOLVED (2026-06-26)

- **Was blocking:** all `yubiOS CI` runs red — only the `build` job failed,
  at `Build OCI image` (Containerfile:60) with
  `copy_file_range: no space left on device` (e.g. run 28219367332).
- **Root cause:** the build job's nested `dockerd` defaulted its data-root to
  the runner's small root disk (~14 GB). The bootc/ostree OCI build (ostree
  objects, native snapshotter full-copy per layer) overflowed it.
- **Fix (smallest targeted, no redesign — per Jenny's debug-mission constraint):**
  mounted the runner's large `/mnt` disk into the `build` container
  (`volumes: - /mnt:/mnt`) and pointed `dockerd --data-root=/mnt/docker`.
  Kept `--storage-driver=native`; no driver swap, no workflow reshape.
  Commit `819d427` on `main`. PARTIAL ONLY: dispatch run 28228309907 moved the
  failure past `Build OCI image`, but the `build` job still FAILED (completed:
  failure) — it now dies at the later `Verify symlinks and scripts` step with
  `no space left on device` on `/mnt/docker/...native/snapshots`. Root cause
  unchanged: the native snapshotter full-copies the ostree rootfs and the verify
  step re-extracts it, doubling the footprint on `/mnt`.
- **Real fix (PUSHED this pass — `e74dadf` on `main`):** swapped the build job's
  nested `dockerd` from `--storage-driver=native` to `--storage-driver=overlayfs`.
  The native containerd snapshotter full-copies every fedora-bootc rootfs layer
  (once on `buildx --load`, again when `docker run` re-extracts at `Verify symlinks`),
  doubling `/mnt/docker`; overlayfs is copy-on-write, so layers are not duplicated.
  Smallest root-cause change — one flag, no workflow reshape (kept `--data-root=/mnt/docker`
  from `819d427`). Dispatched run `28230464416` on `e74dadf` (09:47Z): completed **success** —
  all 5 jobs green (shellcheck, hadolint, mkosi, build, unit-tests). The native
  snapshotter double-extraction is gone; overlayfs COW keeps `/mnt/docker` within
  the disk budget. **CI status: GREEN on `main` @ `e74dadf`.** Verified live via the
  Actions runs+jobs API.

### BLOCKER-009: bcvk `feat/swtpm-ci` HEAD does not compile — swu2f two-impl divergence — RESOLVED (2026-06-26)

- **Blocks:** #20/#33 (LUKS2 FIDO2 e2e test, T4) — the e2e test references this bcvk branch via `bcvk ephemeral run --swtpm --swu2f`.
- **Why:** Two sibling commits chose conflicting swu2f designs. `crates/kit/src/run_ephemeral.rs:1420` calls `bcvk_qemu::swu2f::push_uhid_kargs(...)` (in-guest /dev/uhid route, commit `66fbf130`), but HEAD `be5f3858` rewrote `crates/bcvk-qemu/src/swu2f.rs` to the host-QEMU `u2f-emulated` route (`qemu_u2f_args`/`Swu2fConfig`) and dropped `push_uhid_kargs` — a dangling symbol, guaranteed build failure (not merely "untested").
- **Engineering call:** keep the IN-GUEST /dev/uhid CTAP2 route. QEMU `u2f-emulated` (libu2f-emu) is CTAP1/U2F-only with no `hmac-secret`, so it cannot drive `systemd-cryptenroll --fido2` for the LUKS2 unlock test; a uhid CTAP2 authenticator can. The wired `--swu2f` flag help text already says "expose /dev/uhid".
- **Resolution (landed):** the in-guest `/dev/uhid` CTAP2 route was restored on `feat/swtpm-ci` — `push_uhid_kargs` + uhid `Swu2fConfig` re-added in `crates/bcvk-qemu/src/swu2f.rs` (commit `2afd8778`, plus a redundant near-no-op follow-up `0440dd94` from a parallel run; HEAD = `0440dd94`). `run_ephemeral.rs` now resolves the symbol; both swu2f layers documented in `docs/swu2f.md`. bcvk stays a branch — NO merge.
- **Outstanding:** source-level fix only — NOT compile-verified in-sandbox (no `cargo`/KVM). Needs human `cargo check -p bcvk-qemu -p kit` + `nextest` + Signed-off-by before the branch is trusted. **Layer 2 in-guest CTAP2 authenticator now shipped** — yubiOS PR #40 (`feat/swu2f-layer2-ctap2-fixture` @ `ab37a34`) adds `passless` (pando85/passless v0.11.2, soft-fido2 hmac-secret) in a TEST-only mkosi profile and un-gates the #33 CTAP2 cryptenroll/homed legs; PR #40 is draft (leader merges once green + human cargo build). Both #33 (`4450fd4`) and #38 (`43c2728`) pull_request CI are now GREEN (5/5 jobs).
- **Verified:** live against `yubi-OS/bcvk` @ `0440dd94` — `swu2f.rs` now defines `push_uhid_kargs` (in-guest uhid route restored); dangling-symbol build break cleared.

---

## Branch reconciliation (L-PRUNE, 2026-06-26)

Two yubiOS branches had no open PR. Reconciled against live `main`:

- **`feat/bcvk-swtpm-ci` — DELETED.** `compare/main...feat/bcvk-swtpm-ci` = 0 ahead / 124 behind (`behind`): zero unique commits, tip is an ancestor of `main`. Fully merged. Deleted via refs API (HTTP 204, confirmed 404). Last tip recorded for recovery: `ae8d4d0e220934b09cf504b902df3b65788dc05f`.
- **`feat/fido2-secure-boot` — DELETED.** `compare/main...feat/fido2-secure-boot` = 5 ahead / 218 behind (`diverged`). Byte-level diff confirmed FULLY SUPERSEDED by merged main: identical-by-blob-SHA = the `enroll-*-wrapper.sh` set, bootc tomls, dracut conf, pam `yubiOS-sudo`, hidraw udev rules; the "different" files are all main being a STRICT SUPERSET (legacy `sbsign`->`systemd-sbsign` per ADR-008 in `enroll-sb-fido2.sh`/`sign-uki-fido2.sh`/`enroll-sb.sh`; `lib.sh` fixed the `yubicos_log`->`yubiOS_log` typo and ADDED `check_fido2_pin_length`+`enroll_pam_user`; `enroll.sh` shellcheck quoting fix). Nothing on the branch was absent from main; the branch held the older/buggier variant. Deleted via refs API (HTTP 204, confirmed 404). Tip recorded for recovery: `c5a84a0fad5ef1edc2e60056d45027fd5d3a99d5`. No PR / no BLOCKERS gap.

---

## Post-launch deferrals

| Issue | Reason deferred |
|---|---|
| #23 Phase F0 ARM64 fTPM | Post-launch; Phase 0 must ship first (FUTURE.md) |
| #24 chipsec portable service | Post-launch research item (ADR-010) |
| #25 bcvk FIDO2 software emulator | Post-launch CI hardening |
| #26 Post-quantum TLS | OpenSSL 3.5 not yet in Fedora 45; ADR not written yet |

---

## Suggested merge sequence

1. **Verify new digest** — run systemd + pam-u2f checks above against `6a60ff82...`
2. **Merge PR #31** (`feat/v261-base-image`) — digest bump + README 257→261
3. **Merge PR #29** (`feat/sbsign-migration`) — sbsigntool removed (FinalizeScripts partial, follows after step 7)
4. **Merge PR #30** (`feat/renovate-digest-tracking`) + install Renovate GitHub App
5. **Merge PR #27** (`feat/v261-measured-os`) — ConditionSecurity=measured-os
6. **Clear BLOCKER-007** (CONFIG_BPF_LSM check), then merge **PR #28** (`feat/v261-restrict-filesystem`)
7. **Run PKCS#11 validation** (PR #32) with physical YubiKey, then complete FinalizeScripts in PR #29
8. **Run e2e test** (PR #33) with YubiKey + bcvk
9. **Manual:** deploy CI workflows (#22) — copy staged files to `.github/workflows/`
