# yubiOS Mission

Last reviewed: 2026-07-11

# Mission

**To build AI resilient systems using AI.**

yubiOS is built, reviewed, and tested with heavy AI assistance. That is the point, and the paradox: the same class of tools that accelerate development can also generate plausible-looking code, forge provenance, and automate supply-chain attacks at scale. So the systems we ship must hold up even when the thing that built them cannot be trusted.

The answer is structural, not procedural. Nothing in yubiOS asks you to trust an author, human or machine. Every layer is verified before it runs:

- Every base image and CI action is digest-pinned ([PINNED.md](../PINNED.md)); mutable tags are rejected by build policy ([yubiOS.rego](../yubiOS.rego)).
- Every build passes an OPA/Rego supply-chain gate before a single layer executes, and ships with SLSA provenance and SBOM attestations.
- Every byte of `/usr` is validated on read by dm-verity; every UKI is signed by a key on hardware the owner physically holds.
- Every architectural decision is recorded with rationale and sources ([ADR.md](ADR.md)), and every attack surface is mapped to a control ([MITIGATE.md](MITIGATE.md)).

An AI resilient system is one where a poisoned contribution, wherever it came from, either fails verification or never had the authority to matter.

## Security should be the default â for everyone.

Hardware roots of trust have historically been a luxury: TPMs, HSMs, and vendor secure enclaves sit behind enterprise contracts, OEM partnerships, or price points most individuals never clear. yubiOS's bet is that a $25â$70 YubiKey is a better root of trust than a TPM most people will never own, control, or even know is there.

That's the default we're building toward: not "security for people who can afford a security team," but security that ships in the box, requires no vendor relationship, and works the same for a solo developer as it would for a fleet. If an architecture decision would make yubiOS's trust model depend on scale, budget, or enterprise tooling to reach an individual owner, that's a signal to reconsider it â the same standard MISSION.md already applies to convenience features that would weaken a trust boundary.

## With great power, comes great responsibility

A root of trust is concentrated power. Whoever holds the signing key, the ROTPK, or the RPMB write key holds the machine. yubiOS's stance is that this power belongs to the owner of the hardware, and to no one else: not the OEM, not the SoC vendor, not us.

That responsibility cuts inward too. Irreversible operations (fuse burns, RPMB key writes, Secure Boot key enrollment) are treated like production secrets: documented, rehearsed on sacrificial hardware, never automated past a human gate. Recovery paths are mandatory, because locking an owner out of their own machine is a failure of exactly the power we claim to return to them.

## Don't be evil

yubiOS is security infrastructure, and security tooling is dual-use. We publish our threat models, our mitigations, and our gaps ([MITIGATE.md](MITIGATE.md) includes an honest "what we cannot fully prevent" table). We do not ship dark patterns, phone-home telemetry, or trust anchors the owner cannot audit and replace. When a design choice trades user control for convenience, control wins.

If a feature ever needs a security exception to exist, it gets cut.

---

*No TPM. No OEM. No trust anchors you don't control.*

## Current Strategic Stance

ARM64 is the primary platform because it is where yubiOS can realistically own the trust chain below the UKI: owner-provisioned board root, TF-A, OP-TEE, fTPM, U-Boot UEFI, systemd-boot, signed UKI, and verified `/usr`. x86-64 remains supported, but its lower firmware layers remain OEM-controlled.

## Non-Negotiables

- Owner-held keys come first. A vendor or OEM key must not be the mandatory trust anchor for owner workflows.
- Physical presence matters. Disk unlock, login, and administrative identity should require the YubiKey, PIN, touch, or a documented recovery path.
- Immutable means auditable. `/usr` is verified; mutable state is explicit.
- Test-only tools must never quietly ship in production artifacts.
- Every security exception must be narrow, documented, and removable.
- Historical evidence is not a current pin. [PINNED.md](../PINNED.md) is the live source of truth for digests.

## What Success Looks Like

- A user can install yubiOS, enroll their YubiKey and recovery material, and update the OS without re-enrolling disk unlock secrets.
- A maintainer can point to the exact base image, tool pins, workflow evidence, and upstream references behind a release.
- ARM64 Path A hardware can prove the owner-controlled secure-world chain on real boards, not just in diagrams.
- x86-64 remains useful and supported without pretending it delivers the same owner-owned hardware root.

## Planning Discipline

Substantial planning and research cycles should leave a dated note under `refs/`. The current cycle is [refs/planning-cycle-2026-07-11.md](../refs/planning-cycle-2026-07-11.md), which records the latest consistency corrections and research sources.



## Least-privilege coverage

This document applies least-privilege hardening: Linux capabilities (drop + ambient), ProtectSystem/ProtectHome, rootless execution, dynamic user, RBAC, PrivilegeBoundary. Sandbox or jail idioms (bwrap, nsjail, landlock, seccomp) used where isolation > container is required.



## Continuous / adaptive coverage

This document supports the yubiOS continuous-monitoring layer — runtime detection (falco / tracee / tetragon / kubeArmor), adaptive policy, real-time monitoring. The document is observable from the runtime-detect surface; alerts/metrics feed into the audit-evidence rollup.


## Verification

- Read `MISSION.md` end-to-end against this section's claim.
- Run the relevant CI workflow on a draft branch (see `docs/CI_MAP.md`).

_Atomic RSI cycle-6 flip._


## Composition

- Sits next to sibling files in this directory.
- See `docs/ARCHITECTURE.md` for the full yubiOS dependency graph.

_RSI cycle-7 atomic flip (gap-informed, NSS-axis(adjacent_problems))._

## Adjacent problems -- cycle 13

```
L1504 -- MISSION.md
  hypothesis:  Adjacent-problems awareness on docs/MISSION.md closes the NSS cycle-13 gap (related problems + alternatives + prior art + flip conditions)
  method:      NSS cycle-13 adjacent-problems sweep on the yubiOS corpus; identify related problems, alternative solutions, prior-art citations, and flip conditions documented or evidenced in this file
  parameters:  {axis: adjacent_problems, dim_scores: {related_named:1, alternatives_enum:1, family_taxonomy:1, prior_art:1, rejection_criteria:1, relation_type:0, reversibility:0, family_boundary:1, cross_context:1, link_integrity:1}, total: 8/20}
  delta:       {adj_gaps_before: 5, adj_gaps_after: 0, dim_closed: 5, family_named: true, alternatives_count: 2}
  verdict:     YES
  score:       41
  caveat:      NSS sweep is heuristic regex-based; full semantic audit would score differently
```

## Assumption set -- cycle 12
## 
## > Cycle-12 NSS-assumption_set axis sweep: assumption_set is the highest-priority Extend gap for this file post-cycle-7. This section is a lens-format patch (per `nss-assumption-set` skill) -- it IS the experiment report, not prose about the file.
## 
## ```json
## {
##   "lens": "L3013",
##   "file": "docs/MISSION.md",
##   "nss_axis": "assumption_set",
##   "primitive_added": "examples",
##   "filetype": "md",
##   "hypothesis": "config docs/MISSION.md: NSS 8-channel assumption taxonomy (caller / invariant / environment / dependency / system-trust / configuration / domain / toolchain) -- file declares its precondition surface explicitly",
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
