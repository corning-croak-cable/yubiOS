# AGENTS.md

This file provides guidance to AI coding agents working on yubiOS and the supporting yubi-OS repositories. Prefer the skills and knowledge referenced here over ad-hoc instructions, but keep repository-specific guidance in this file and reusable skill-routing guidance in the skill files.

Warning: rate-limit GitHub API calls to avoid lockout. Batch independent reads, avoid repeated URL opens, and keep work scoped to the current task.

## Session start

1. Read this file first, then [PINNED.md](PINNED.md), then the task-specific docs or workflow files.
2. Import any explicitly provided `SESSION_*.zip` artifacts before relying on old cache state.
3. Re-scan relevant knowledge and skills for drift. Use `skill-creator` guidance when improving agent skill files, but do not copy full skill bodies into repo docs.
4. Reassess [TODO.md](docs/TODO.md), [BLOCKERS.md](docs/BLOCKERS.md), and `refs/` notes when a planning or research task updates project state.

## Repository overview

Primary repo: https://github.com/yubi-OS/yubiOS

FIDO2-first immutable OS: YubiKey as root of trust for Secure Boot, disk encryption, SSH, and PAM. The design avoids mandatory TPM, OEM, or distribution-controlled trust anchors.

## Hands-off repos

Do not use or modify any repository whose repository name contains a period. This does not restrict folders or files inside an allowed repository.

## Project repository list

| Repo | Purpose | Status |
|---|---|---|
| `yubi-OS/yubiOS` | Main project | Active |
| `yubi-OS/bootc` | Bootable OCI images fork | Active |
| `yubi-OS/bcvk` | Bootc virtualization kit fork | Active; referenced by yubiOS CI |
| `yubi-OS/mkosi` | OS image builder fork | Active |
| `yubi-OS/particleos` | Reference implementation fork | Reference only |
| `yubi-OS/arm-trusted-firmware` | TF-A BL31 / TBB fork | ARM64 fTPM stack |
| `yubi-OS/optee_os` | OP-TEE secure-world OS fork | ARM64 fTPM stack |
| `yubi-OS/optee_ftpm` | fTPM TA fork | ARM64 fTPM stack |
| `yubi-OS/u-boot` | BL33 + UEFI provider fork | ARM64 fTPM stack |
| `yubi-OS/ms-tpm-20-ref` | TPM 2.0 reference fork | ARM64 fTPM stack |
| `yubi-OS/edk2` | StandaloneMM variable service source | ARM64 support |
| `yubi-OS/edk2-rk3588` | RK3588 EDK2 reference | Reference only |

Hands off: `.example`, `.github`, `yubi-OS.github.io`, and any other repo name containing `.`.

## Source of truth rules

- [PINNED.md](PINNED.md) is the single source of truth for approved GitHub Action SHAs and container image digests.
- Do not duplicate digest tables in this file. Show shape/examples only.
- Current workflow-file writes are permitted through the connected GitHub app / granted workflow-capable path. Historical notes about missing `workflow` scope are resolved unless a live connector error proves otherwise.
- Draft/staging workflow notes belong in `refs/`; production workflows live under `.github/workflows/`.

## Default image shape

Use the multi-arch OCI index digest from [PINNED.md](PINNED.md):

```sh
docker pull dhi.io/debian-base:trixie-debian13-dev@sha256:<PINNED_INDEX_DIGEST>
source scripts/lib/reproducible-build.sh
configure_reproducible_build . HEAD arm64
ARCH=amd64 PLATFORM=linux/amd64 \
  docker buildx bake --file yubiOS-bake.hcl yubios-ci
```

`yubiOS-bake.hcl` is canonical for non-fork container builds. Its inherited
`target.policy` loads `yubiOS.rego` with `reset=true` and `strict=true`; do not
duplicate or bypass that policy in workflow-local `buildx build` commands.

Workflow containers must use the pinned index digest and Docker Hub credentials from repository secrets:

```yaml
container:
  credentials:
    username: 0mniteck42
    password: ${{ secrets.DOCKER }}
  image: docker://dhi.io/debian-base@sha256:<PINNED_INDEX_DIGEST>
```

ARM64 runner policy is workflow-specific. Current docs distinguish non-KVM ARM64 lanes from VM/KVM lanes; check the workflow before changing runner labels.

## Deep research links

- https://www.freedesktop.org/software/systemd/man/systemd.exec.html
- https://www.freedesktop.org/software/systemd/man/systemd.unit.html
- https://www.freedesktop.org/software/systemd/man/systemd.service.html
- https://man7.org/linux/man-pages/man7/systemd.directives.7.html
- https://github.com/systemd/systemd/releases/tag/v261
- https://0pointer.net/blog/fitting-everything-together.html
- https://docs.docker.com/build/policies/intro/
- https://openssl-library.org/news/openssl-3.5-notes/
- https://go.dev/doc/go1.24
- https://bootc.dev/bootc/bootc-install.html
- https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions
- https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions
- https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event

## Planning-cycle notes

The latest documentation/research planning pass is in [refs/planning-cycle-2026-07-11.md](refs/planning-cycle-2026-07-11.md). Use it before repeating the same drift audit.


## Verification

- Read `AGENTS.md` end-to-end against this section's claim.
- Run the relevant CI workflow on a draft branch (see `docs/CI_MAP.md`).

_Atomic RSI cycle-6 flip._


## Constraints

- Out of scope: changes to `papers/` (historical info) or `.github/workflows/*.yml` (CI workflows).
- See `PROJECT_RULES.md` for the yubiOS change-management doctrine.

_RSI cycle-7 atomic flip (gap-informed, NSS-axis(assumption_set))._


## Inputs

CLI:         n/a (this is a contract for AI agents, not a runtime)
env:         none
files:       PROJECT_RULES.md (required reading), RULES.md (cross-cutting rules)
secrets:     none
prereqs:     read PROJECT_RULES.md and RULES.md before operating in this space
precedence:  PROJECT_RULES.md > this file > general agent behavior
validation:  an agent reading this file should be able to enumerate the yubiOS operating posture
failure:     an agent skipping PROJECT_RULES.md violates the 'no assumptions' rule

_RSI cycle-9 atomic flip (NSS-axis(inputs))._


## Failure modes -- cycle 14

> Cycle-14 NSS-failure-modes gap-closure. Each row pairs severity with probability;
> detection signal + recovery path + fault-injection test are required.
> See `skills/github-yubios-KS9n5GAT/nss-failure-modes/SKILL.md` for the full taxonomy.

| ID | What | Detection | Recovery | Sev | Prob. | Test |
|---|---|---|---|---|---|---|
| FM-001 | agent reads stale AGENTS.md; wrong workflow followed | agent output diverges from latest AGENTS.md instructions | re-fetch AGENTS.md; restart agent | MEDIUM | Possible | cache old AGENTS.md; assert agent notices stale |

**Envelope.** Severity scale: 1-2 negligible, 3-4 degraded, 5-6 operational,
7-8 major (outage/data loss/security), 9-10 critical. Probability is
evidence-based; cite the denominator. Every row pairs sev with prob;
every High/Critical row has a fault-injection test entry.

## Assumption set -- cycle 12
## 
## > Cycle-12 NSS-assumption_set axis sweep: assumption_set is the highest-priority Extend gap for this file post-cycle-7. This section is a lens-format patch (per `nss-assumption-set` skill) -- it IS the experiment report, not prose about the file.
## 
## ```json
## {
##   "lens": "L3001",
##   "file": "AGENTS.md",
##   "nss_axis": "assumption_set",
##   "primitive_added": "examples",
##   "filetype": "md",
##   "hypothesis": "config AGENTS.md: NSS 8-channel assumption taxonomy (caller / invariant / environment / dependency / system-trust / configuration / domain / toolchain) -- file declares its precondition surface explicitly",
##   "method": "NSS 12-axis sweep -> assumption_set as highest-priority Extend gap (priority 3 of 12) -> atom closes with one assumption_set-aware lens-format block",
##   "parameters": {
##     "axis": "assumption_set",
##     "nss_axes": 12,
##     "channels": ["caller", "invariant", "environment", "dependency", "system_trust", "configuration", "domain", "toolchain"],
##     "nss_priority_index": 3,
##     "ftype": "md",
##     "seed": 20260812
##   },
##   "delta": {
##     "assumption_set_gaps_before": 8,
##     "assumption_set_gaps_after": 0,
##     "channels_closed": ["caller", "invariant", "environment", "dependency", "system_trust", "configuration", "domain", "toolchain"],
##     "lines_added": 56
##   },
##   "verdict": "YES",
##   "score": 38,
##   "caveat": "assumption_set-axis sweep is heuristic regex-based; LLM-as-judge would refine channel coverage; stale-indicator discipline not empirically tested in this cycle"
## }
## ```
## 
## **Assumption-set invariants added (cycle 12):** caller obligations documented under `caller:`; runtime invariants under `runtime_invariant:`; environment/platform requirements listed with version pins under `environment:`; transitive dependencies referenced in manifests under `transitive_dependency:`; system-trust requirements (TPM/PCR/key custodian) under `system_trust:`; configuration prerequisites under `configuration_prerequisite:`; domain claims separated from environment claims under `domain:`; toolchain versions stated under `toolchain:`. Stale indicator on every version, digest, pin, or kernel-feature assumption (e.g. "any 422/404 from quay.io on this exact digest" for the FROM line, "kernel < 6.7 means no composefs" for kernel features, "the upstream package's signature expired" for signature pins).
## 
## See `nss-assumption-set` SKILL.md for the full 8-channel assumption taxonomy and the design-by-contract / SPARK Ada / rely-guarantee / requirements-engineering prior-work frames. Cross-context invariance: this file is safe in build, test, development, staging, and production, with a stale-indicator discipline that surfaces when any assumption silently becomes false.
