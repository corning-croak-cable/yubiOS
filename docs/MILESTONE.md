# yubiOS Milestones

Last reviewed: 2026-07-25
Status: repo-native mirror of the Linear execution project. This is a planning-only document -- it summarizes workstreams and milestones, it does not duplicate TODO.md, BLOCKERS.md, or FUTURE.md. For current task details see TODO.md; for open blockers see BLOCKERS.md; for longer-horizon research see FUTURE.md.

Source: mirrors the Linear project "yubiOS Production Proof & Release Gates" (team OMNI-AGENT), per OMN-64/OMN-44.

## Goal

Drive yubiOS from research-backed roadmap items to production-proof evidence across ARM64 Path A, token-backed CI, sealed bootc flow, and runtime/supply-chain validation.

## Main workstreams

- **ARM64 Path A** -- real-hardware production proof for the ARM64 secure-boot chain (ROTPK, OP-TEE, fTPM, U-Boot UEFI Secure Boot).
- **VM/CI coverage** -- deterministic, token-dependent guest operations in CI (FIDO2 enumeration, LUKS2 unlock) with clear production/dev-test isolation.
- **Sealed boot chain** -- moving from the current unsealed fs-verity story to a signed-UKI plus Secure Boot proof.
- **Runtime hardening and supply chain** -- turning static hardening audits into target-image runtime evidence, with pinned inputs and provenance.

## The four milestones

### 1. ARM64 Path A production proof

Close the real-hardware production proof gaps for the targeted ARM64 path, including fuse/ROTPK rehearsal, OP-TEE and RPMB-backed evidence, U-Boot UEFI Secure Boot, and exact board configuration capture.

Seeded blocker-driven issues (from the live BLOCKERS.md as of 2026-07-22): B-ARM64-PATHA (no board has proven the full chain yet), B-RK3588-TPL (ROCK 5B build is diagnostic packaging, not flashable).

### 2. Token-backed VM and CI coverage

Make token-dependent guest operations execute deterministically in CI, keep PQ TLS verification visible, and preserve explicit isolation between production and dev/test paths.

Seeded blocker-driven issues: B-VM-CTAP2 (no FIDO2 token enumerates in the VM lane -- the single highest-leverage blocker per refs/readiness-gates-gtm-2026-07-25.md, OMN-73), B-QEMU-ZBOOT (contained workaround, not an open failure), B-REAL-FIDO2 (physical-hardware validation gated on B-VM-CTAP2 closing first).

### 3. Sealed composefs boot chain

Promote the current unsealed integrity path to a signed-UKI plus Secure Boot proof with negative tamper evidence on amd64 and arm64.

Seeded blocker-driven issue: B-BOOTC-SEAL (fs-verity currently proven through a mutable BLS digest anchor, not a sealed/signed UKI; see refs/bootc-composefs-sealed-flow-2026-07-22.md).

### 4. Runtime hardening and supply-chain validation

Back hardening and rebuildability claims with target-image runtime validation, pinned inputs, package-floor checks, immutable source resolution, and provenance expectations.

Seeded blocker-driven issues: B-HARDENING-RUNTIME (static audit complete, runtime Bats/systemd-analyze verify still needed against a target image), B-PINS (base-image digest changes require explicit PINNED.md updates).

## Relationship to the broader roadmap

This document is the concise, repo-native planning artifact aligned with the current Linear structure. It intentionally does not restate:

- **TODO.md** -- the active, detailed task list; check there for current work-in-progress.
- **BLOCKERS.md** -- the single source of truth for open blockers; this doc only names which blockers seed which milestone, it does not track their live status.
- **FUTURE.md** -- longer-horizon research and planning cycles, including Milestone F (ARM64 Owner-Owned Root of Trust) which overlaps with milestone 1 above but is tracked at a different altitude (research backlog vs execution milestone).

This is a planning-only repository documentation task, per OMN-44’s own framing: revisit implementation only after repo-side coding work resumes on each milestone.
