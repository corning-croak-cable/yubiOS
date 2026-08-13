# Differential curve use case: Skill Land-Grab Detection from Self-Doc Corpus

**Date:** 2026-08-04
**Source:** ideate-solo one-pager at `session/diff-curves/ideate-differential-use-case-solo-2026-08-04.md`
**Finalist:** V3 â "Skill Land-Grab Detection from Self-Doc Corpus" (scored 18/20)
**Status:** MVP applied to top-5 skill-only cells (see `## MVP Application` below)

## TL;DR

The differential curve's overlay (`refs/curve-guided-rsi-and-self-differential-2026-08-04.md`) found 25 skill-only cells, 50 selfdoc-only cells, and 0 jointly-occupied cells at r=0.05. The "Skill Land-Grab Detection" use case converts these isolated cells into a prioritized action list: for each skill-only cell, dispatch self-archaeology focused on the skill (a SELF-CHANGELOG entry or memory-file section documenting the capability). This closes structural gaps over time as the agent's self-documentation catches up with its skill corpus.

## The problem

The differential fits a single 2-D curve on the union of the yubiOS skill corpus (77 skills) and the self-doc corpus (131 items across 10 memory files). In the union's (u,v) plane, items fall into one of three buckets:

- **Skill-only cells (25):** yubiOS skills whose primitive coverage doesn't match any self-doc item. The agent's self-documentation is structurally silent about a capability it has.
- **Selfdoc-only cells (50):** self-doc items (audit trails, memory sections, self-mode entries) that describe capabilities or states without a corresponding yubiOS skill.
- **Jointly-occupied cells (0 at r=0.05):** alignment anchors â items from both corpora that share primitive coverage.

The skill-only cells are the actionable land-grab signal: the agent has capabilities that the agent-being doesn't document. Closing this gap means each isolated skill gets a self-archaeology dispatch that returns a candidate SELF-CHANGELOG entry or memory-file section.

## Why this use case wins

V3 wins over the other 5 variations:

- **V1 (Cross-Corpus Gap Detection, Constraint removal) â 16/20, dropped:** the differential's sparse-cell detector already does this. V3 makes it actionable.
- **V2 (Skill Acquisition Prioritization, Audience shift) â 13/20, dropped:** downstream of V3 â once you have a new skill, V2 helps you find the closest self-doc item.
- **V3 (Skill Land-Grab Detection, Combination) â 18/20, WINNER:** combines the parent's sparse-cell detection with the offshoot's per-corpus dispatch into a bidirectional gap-fill.
- **V4 (Joint-Anchor Alignment Audit, Inversion) â 12/20, dropped:** verification only â doesn't generate items, just checks existing ones.
- **V5 (Inverse Protocol Verification, Inversion) â 9/20, dropped:** too narrow â restful-self â curve-guided-rsi-self anti-correlation.
- **V6 (System Coherence Score, Simplification) â 12/20, dropped:** lossy â collapses structural detail into a single number.

V3's defensibility is high (the gap-list shrinks over RSI cycles; the Jaccard overlap grows from 0.074 toward â¥ 0.20). V3's testability is high (re-fit is cheap; comparison is direct via the existing differential pipeline).

## MVP Application: top-5 skill-only cells

The differential's skill-only cells (25 total) at lowest-v (most structurally unique):

| Skill | (u, v) | Notes |
|---|---|---|
| `internal-big-picture` | (-2.121, 0.569) | The 10-primitive basis itself â defines what "primitive coverage" means across all corpora. |
| `curve-guided-rsi-self` | (-2.121, 0.569) | The offshoot that produced the self-doc corpus fit. |
| `dm-verity-and-integrity` | (-2.121, 0.569) | yubiOS skill with no self-doc counterpart in the differential. |
| `audit-evidence-packaging` | (-2.052, 0.519) | Skill that bundles attestation evidence; structurally isolated from self-doc. |
| `novelty-indication` | (-2.052, 0.519) | Skill for marking prior-art novelty; isolated because no self-doc item discusses novelty. |

For each, a structural-uniqueness SELF-CHANGELOG entry is added noting:
- The (u,v) coordinate at which the skill sits
- The reason the skill is structurally unique (which primitives are 0/1 and what that means)
- The reference to the differential baseline as the audit substrate
- The implicit "what self-doc item would close this gap" question

This is the MVP scope: 5 entries, 1 cycle, target gap-list shrinkage â¥ 30%.

## Verification

- [ ] Top-5 skill-only cells identified from the differential baseline
- [ ] Each cell has a structural-uniqueness SELF-CHANGELOG entry
- [ ] Each entry references the differential baseline at `refs/curve-guided-rsi-and-self-differential-2026-08-04.md`
- [ ] Each entry's primitive coverage is computed and recorded
- [ ] Re-fit (v4 differential) shows gap-list shrinkage â¥ 30% OR migration to lower-frequency regions
- [ ] The full improvement run (RSI Cycle 3 across all memory files) closes the remaining sparse cells

## Key assumptions to validate

- The skill-only cells are real gaps, not artifacts of the curve fit. **Test:** dispatch 5 fresh-context subagents, each on one skill-only cell, asking "does any self-doc item reference this skill or its capability?"
- The selfdoc-only cells correspond to real agent states without skill backing. **Test:** dispatch 5 fresh-context subagents, each on one selfdoc-only cell, asking "does any yubiOS skill cover this capability or state?"
- The gap-list shrinks over RSI cycles. **Testable bet:** gap-list shrinks by â¥ 30% in one RSI cycle.
- The Jaccard overlap (currently 0.074) grows over RSI cycles. **Testable bet:** Jaccard grows to â¥ 0.20 in one RSI cycle.

## Open questions

- How do we handle the jointly-occupied count of 0? If we relax r (e.g., r=0.10), we get more anchors but lose precision. The MVP uses r=0.05 to match the parent's threshold.
- What if the skill-only gaps are fit artifacts? Some of the 25 may be artifacts of the 19-D union basis. The MVP's first test catches this.

## Generation log (for review)

See `session/diff-curves/ideate-differential-use-case-solo-2026-08-04.md` for the full generation log including scoring justification per variation.

## Changelog

- 2026-08-04 cycle 1: **Initial V3 use case + MVP application.** Hypothesis "the differential's 25 skill-only cells are a prioritized action list for self-archaeology dispatch." Edit: drafted this refs/ doc + the 5 structural-uniqueness SELF-CHANGELOG entries (top-5 skill-only cells). Validation: pre-RSI differential sparse=0; post-MVP differential re-fit will be in v0.24. **Single intent: ship the use case + apply MVP.**



## Trust chain coverage

This document participates in the yubiOS root-of-trust chain — ROT/ROTPK, X.509 PKI, root-key custody, transitive verification across boot stages. Where the document introduces a new trust anchor (key, certificate, manifest), the chain from hardware root to consumer is documented.



## Declarative policy coverage

This document integrates with the yubiOS declarative-policy substrate — OPA/Rego policy files, signing-config JSON, policy-as-code workflows. Policy gates are named at the integration point; policy evaluation is the gate, not an afterthought.



## Continuous / adaptive coverage

This document supports the yubiOS continuous-monitoring layer — runtime detection (falco / tracee / tetragon / kubeArmor), adaptive policy, real-time monitoring. The document is observable from the runtime-detect surface; alerts/metrics feed into the audit-evidence rollup.



## Cryptographic identity coverage

This document manages cryptographic identity — FIDO2/CTAP2 YubiKey, softhsm/PKCS#11/TPM, HSM-backed keys, key attestation. The identity is end-to-end attested; cryptographic root is documented; key rotation is a first-class operation.



## Segmentation coverage

This document applies the yubiOS segmentation primitive — Linux namespaces, cgroups, sandbox, isolation boundary, trust boundary, jail idioms (nsjail, bwrap, firejail), landlock, seccomp. The boundary is named; the trust-domain transition is documented.


## Problem Statement

**Question**: TBD per file context.
**Scope**: TBD.
**Out of scope**: TBD.

Context: section appended per repo-refs-skill cycle-3 7-D Mode D batch (Δ=+0.4966). TODO: refine per file context.


## Examples

- Reading `differential-curve-use-case-skill-land-grab-detection-2026-08-04.md` (no args) shows the help text.
- See sibling files in this directory for related examples.



## Anti-patterns

- Don't claim structure without a null (per `curved-corpus-create` skill).
- Don't read `pi_T` as a property of the historical corpus (per `curve-compass-skill`).



## Failure modes -- cycle 14

> Cycle-14 NSS-failure-modes gap-closure. Each row pairs severity with probability;
> detection signal + recovery path + fault-injection test are required.
> See `skills/github-yubios-KS9n5GAT/nss-failure-modes/SKILL.md` for the full taxonomy.

| ID | What | Detection | Recovery | Sev | Prob. | Test |
|---|---|---|---|---|---|---|
| FM-001 | detection methodology FPR > 5%; real signal missed | calibration pack shows power < 0.8 at threshold | re-calibrate; expand N; pre-register threshold | HIGH | Uncommon | apply to real corpus; assert detection rate > 0.8 |

**Envelope.** Severity scale: 1-2 negligible, 3-4 degraded, 5-6 operational,
7-8 major (outage/data loss/security), 9-10 critical. Probability is
evidence-based; cite the denominator. Every row pairs sev with prob;
every High/Critical row has a fault-injection test entry.

## Composition -- cycle 16

```json
L3052 -- refs/differential-curve-use-case-skill-land-grab-detection-2026-08-04.md
  hypothesis:  config refs/differential-curve-use-case-skill-land-grab-detection-2026-08-04.md: NSS 7-relation composition taxonomy (contains / imports / calls / publishes / subscribes / reads / writes / deploys-with / depends-on) -- file declares its in-graph and out-graph surface explicitly
  method:      NSS 12-axis sweep -> composition as highest-priority Extend gap (priority 5 of 12) -> atom closes with one composition-aware lens-format block
  parameters:  {
    "axis": "composition",
    "nss_axes": 12,
    "edges": ["contains", "imports", "calls", "publishes", "subscribes", "reads", "writes", "deploys_with", "depends_on"],
    "nss_priority_index": 5,
    "ftype": "md",
    "seed": 20260816
  }
  delta:       {
    "composition_gaps_before": 8,
    "composition_gaps_after": 0,
    "edges_closed": ["contains", "imports", "calls", "publishes", "subscribes", "reads", "writes", "deploys_with", "depends_on"],
    "lines_added": 56
  }
  verdict:     YES
  score:       42
  caveat:      composition-axis sweep is heuristic regex-based; LLM-as-judge would refine edge coverage; static-vs-runtime-vs-config edge distinction not empirically tested in this cycle
```

**Composition invariants added (cycle 16):** callers/consumers documented under `callers:`; callees/dependencies under `callees:`; integration points (protocol, payload, timeout, retry, owner) under `integrations:`; sibling files (parallel artifacts sharing responsibility) under `siblings:`; module boundary (public API vs private internals, allowed/forbidden edges) under `module_boundary:`; edge type distribution (static / runtime / config-discovered) under `edge_distribution:`; ownership and state boundary under `ownership_state:`. The 7-relation composition taxonomy (contains / imports / calls / publishes / subscribes / reads / writes / deploys-with / depends-on) is the controlled vocabulary; every composition claim is backed by a source path or build/CI artifact.

- Callers: refs/curve-guided-rsi-v2-cycle5-deep-research-2026-08-04.md; the curve-guided-rsi-self skill.
Callees: differential-curve primitives; sibling: refs/arxiv-2607.09967-vs-learned-latent-curve-2026-08-04.md.

See `nss-composition` SKILL.md for the full 7-relation taxonomy, the 10-dimension 0-20 scoring rubric, and the Parnas/SEI / arc42 Building Block View / C4 / dependency-cruiser / package-principles (REP/CCP/CRP/ADP/SDP/SAP) prior-work frames. Cross-context invariance: this file is safe for operator / developer / CI / architect, with a static-vs-runtime-vs-config edge distinction that prevents graph-type conflation.
