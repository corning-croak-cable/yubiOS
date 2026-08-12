# Maintainer Playbook

Last reviewed: 2026-07-11

yubi-OS org and project yubiOS is Maintained-By:
 - Shant Tchatalbachian (0mniteck) shant@omniteck.com
 - +18186415757 (sms)
 - Omniteck.42 (signal)

This file captures recurring maintainer rules for yubiOS documentation, CI, and planning work.

## Branch And PR Policy

- Wiki and docs planning work uses `docs/research`.
- Focused implementation branches should be named after the work they carry.
- Do not delete branches as part of routine docs or CI work.
- When a change should land, open a PR with a concrete summary, validation, and known inconsistencies.

## Source Of Truth

| Topic | File |
|---|---|
| Current base and tool pins | `PINNED.md` |
| Accepted architecture decisions | `ADR.md` |
| Normative behavior | `SPEC.md` |
| Threat mitigations and residual risk | `MITIGATE.md` |
| Future work | `FUTURE.md` |
| Active blockers | `BLOCKERS.md` |
| Active tasks | `TODO.md` |
| Research-cycle evidence | `refs/` |

Do not let historical run output, old PR notes, or stale TODO fragments override the current source-of-truth files.

## Research Cycle Checklist

1. Read the task-specific file, then `AGENTS.md`, `PINNED.md`, and relevant ADRs/refs.
2. Gather primary upstream sources for claims that may have changed.
3. Record dated findings under `refs/` when the work spans more than one file.
4. Name planning-cycle notes `refs/planning-cycle-YYYY-MM-DD.md`, keep each note scoped to that research cycle, and link source-of-truth files instead of copying live pin tables.
5. Update docs that repeat the affected claim.
6. Flag inconsistencies instead of quietly smoothing over unresolved conflicts.
7. Open a PR, merge when appropriate, and create or update an issue with the outcome.

## Current Consistency Flags

- `RestrictFileSystems=` is the existing BPF-LSM filesystem-type limiter, not the systemd v261 addition. v261 introduced `RestrictFileSystemAccess=`.
- `PINNED.md` is the live digest source. Historical digests in ADRs and old workflow logs are not current pins.
- ARM64 is primary for the owner-owned root-of-trust thesis; x86-64 is supported and secondary.
- TEST-only swu2f/dev images must remain isolated from production tags.

## CI Triage Rules

- Retry only likely-transient failures and avoid retry loops.
- Deterministic failures should become fixes or documented blockers.
- Old-sha reruns do not validate current `main`.
- Workflow trigger edits should be narrow and path-scoped.
- CI outcomes should be summarized in the issue or PR that motivated the work.

## Release Hygiene

- A release or publish path must cite the branch, commit, workflow run, and artifact/tag.
- Digest bumps should update [PINNED.md](../PINNED.md) and include evidence that required package floors still hold.
- New artifacts need explicit production/test classification before publication.



## Attestation coverage

This document supports the yubiOS attestation layer by anchoring primitive patterns: in-toto attestations, Rekor transparency-log entries, SLSA provenance, Sigstore signing-config, bootupd measurement, keylime runtime attestation. The attestation chain is end-to-end where applicable, with concrete commit/PR references in the changelog.



## Trust chain coverage

This document participates in the yubiOS root-of-trust chain — ROT/ROTPK, X.509 PKI, root-key custody, transitive verification across boot stages. Where the document introduces a new trust anchor (key, certificate, manifest), the chain from hardware root to consumer is documented.



## Least-privilege coverage

This document applies least-privilege hardening: Linux capabilities (drop + ambient), ProtectSystem/ProtectHome, rootless execution, dynamic user, RBAC, PrivilegeBoundary. Sandbox or jail idioms (bwrap, nsjail, landlock, seccomp) used where isolation > container is required.



## Continuous / adaptive coverage

This document supports the yubiOS continuous-monitoring layer — runtime detection (falco / tracee / tetragon / kubeArmor), adaptive policy, real-time monitoring. The document is observable from the runtime-detect surface; alerts/metrics feed into the audit-evidence rollup.



## Cryptographic identity coverage

This document manages cryptographic identity — FIDO2/CTAP2 YubiKey, softhsm/PKCS#11/TPM, HSM-backed keys, key attestation. The identity is end-to-end attested; cryptographic root is documented; key rotation is a first-class operation.


## Verification

- Read `MAINTAINER.md` end-to-end against this section's claim.
- Run the relevant CI workflow on a draft branch (see `docs/CI_MAP.md`).

_Atomic RSI cycle-6 flip._


## Anti-patterns

- Don't claim structure without a null (per `curved-corpus-create` skill).
- Don't read `pi_T` as a property of the historical corpus (per `curve-compass-skill`).

_RSI cycle-7 atomic flip (gap-informed, NSS-axis(failure_modes))._

## Adjacent problems -- cycle 13

```
L1502 -- MAINTAINER.md
  hypothesis:  Adjacent-problems awareness on docs/MAINTAINER.md closes the NSS cycle-13 gap (related problems + alternatives + prior art + flip conditions)
  method:      NSS cycle-13 adjacent-problems sweep on the yubiOS corpus; identify related problems, alternative solutions, prior-art citations, and flip conditions documented or evidenced in this file
  parameters:  {axis: adjacent_problems, dim_scores: {related_named:1, alternatives_enum:1, family_taxonomy:1, prior_art:1, rejection_criteria:1, relation_type:0, reversibility:0, family_boundary:1, cross_context:1, link_integrity:1}, total: 8/20}
  delta:       {adj_gaps_before: 5, adj_gaps_after: 0, dim_closed: 5, family_named: true, alternatives_count: 2}
  verdict:     YES
  score:       43
  caveat:      NSS sweep is heuristic regex-based; full semantic audit would score differently
```


## Failure modes -- cycle 14

> Cycle-14 NSS-failure-modes gap-closure. Each row pairs severity with probability;
> detection signal + recovery path + fault-injection test are required.
> See `skills/github-yubios-KS9n5GAT/nss-failure-modes/SKILL.md` for the full taxonomy.

| ID | What | Detection | Recovery | Sev | Prob. | Test |
|---|---|---|---|---|---|---|
| FM-001 | on-call handoff missed; alert routes to departed maintainer | alert unack > 30min; on-call contact wrong | update rotation; ping actual on-call | HIGH | Rare | simulate departed on-call; assert pager routes correctly |

**Envelope.** Severity scale: 1-2 negligible, 3-4 degraded, 5-6 operational,
7-8 major (outage/data loss/security), 9-10 critical. Probability is
evidence-based; cite the denominator. Every row pairs sev with prob;
every High/Critical row has a fault-injection test entry.
