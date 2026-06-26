# BLOCKERS.md — yubiOS Open Issue Dependency Map

_Last updated: 2026-06-26. Maintained alongside TODO.md and ADR.md._

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
