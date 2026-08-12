# yubiOS offer and pricing architecture

**Status:** draft, hypotheses unvalidated | **Owner:** follower session (the-cult FOLLOWER_2) | **Linear:** [OMN-71](https://linear.app/omni-agent/issue/OMN-71/offer-and-pricing-architecture)

## Why this exists

This is the offer catalog and pricing architecture OMN-71 asks for, scoped by
[refs/operating-covenant-2026-07-25.md](operating-covenant-2026-07-25.md) (OMN-70)
Â§2's commercial boundaries: everything below sells *around* the trust chain
(services, hardware, support), never access *to* it. No price in this document is
a committed number â every figure is an explicit hypothesis to validate in a paid
pilot (per OMN-71's own ask), not a fact grounded in a live customer conversation
or comparable-company data this session actually fetched.

## 1. Initial offer catalog

| Offer | Type | What it is | Covenant check |
|---|---|---|---|
| O1: Managed fleet enrollment | Recurring (subscription) | Onboarding + ongoing enrollment/rotation of YubiKeys across a fleet (PIV, FIDO2, LUKS2) via a hosted dashboard | Allowed â dashboard is convenience; `homectl`/`bootc`/API access to the same enrollment state stays unpaywalled per covenant Â§2 |
| O2: Hardware bundles | Non-recurring | Pre-flashed device + enrolled YubiKey shipped as a unit | Allowed â sells hardware, not trust-chain access |
| O3: Support contracts / SLAs | Recurring | Response-time-bound support for production yubiOS fleets | Allowed â security fixes still ship to everyone simultaneously per covenant Â§3 Disclosure; SLA buys *response time*, not the fix itself |
| O4: Managed CI / build infrastructure | Recurring | Hosted mkosi/bcvk build pipeline with PIV signing, so customers don't run their own signing infra | Allowed, with care â the customer's own PIV key material must stay customer-held per covenant Â§2 ("no feature that requires surrendering key material... as a condition of paying") |
| O5: Integration consulting | Non-recurring (project) | Scoped engagement: port yubiOS to a customer's hardware, wire ARM64 fTPM stack, etc. | Allowed |
| O6: Training | Non-recurring | Workshops on the trust model, ADR process, or ARM64 porting | Allowed |
| O7: Public-security grants/pilots | Non-recurring (external funding) | Paid pilots or grant-funded deployments with public-interest orgs (schools, municipalities, journalists) | Allowed â ties to OMN-86 (public-security funding targets), a separate Linear issue; not designed here |

This catalog deliberately excludes any SKU that gates a security fix, a trust-chain
feature, or requires key custody â those are the covenant Â§2 "not allowed" list,
and no offer here proposes one.

## 2. Starting price hypotheses

**None of these are committed prices.** Each is a hypothesis to be tested against
real customer conversations in a paid pilot, per OMN-71's own checklist item
("document assumptions that need validation in paid pilots"). Where useful,
directional framing (not a specific number) is given because a specific number
this session cannot ground in market data would be fabricated, which the
pulpit's doctrine rules out ("never invent a fact").

| Offer | Pricing shape hypothesis | What would validate/invalidate it |
|---|---|---|
| O1 Managed enrollment | Per-seat or per-device recurring fee, tiered by fleet size | A design partner willing to pay list price for a 10â50 device pilot, without a discount that erases the tier logic |
| O2 Hardware bundles | Cost-plus on top of the ~$25â70 YubiKey unit cost cited in MISSION.md, plus device cost and a margin for pre-flash/enrollment labor | Whether customers prefer buying a bundle vs. buying a bare YubiKey + self-flashing (a real substitution test, not a survey answer) |
| O3 Support/SLA | Percentage-of-deployment-value or flat recurring tier by response-time SLA | Whether a prospect will sign before a P1 incident happens, not just after one |
| O4 Managed CI | Recurring, scaled by build volume/concurrency | Whether customers trust a hosted signing pipeline enough to route real releases through it in the pilot, not just test builds |
| O5 Consulting | Time-and-materials or fixed-scope project fee | Whether a scoped SOW actually closes, vs. staying a "let's talk" conversation indefinitely |
| O6 Training | Flat fee per session/cohort | Attendance and repeat-booking rate from the first cohort |
| O7 Grants/pilots | Grant-scale, external-funder-set (see OMN-86) | Whether an actual grant or pilot contract is signed, not just a target list existing |

## 3. Readiness gates per offer

Per [refs/roadmap-promotion-gates-2026-07-17.md](roadmap-promotion-gates-2026-07-17.md),
nothing moves from "planned" to "implemented"/sellable without naming an owner,
evidence target, and recovery plan. Applied to each offer:

| Offer | Readiness gate before selling |
|---|---|
| O1 Managed enrollment | Requires B-REAL-FIDO2 real-hardware evidence run (per [refs/yubikey-hw-validation-scenarios-2026-07-25.md](yubikey-hw-validation-scenarios-2026-07-25.md), OMN-63) closed for the enrollment scenarios (H1, H4, H10, H11) â can't sell managed enrollment on a mechanism not yet proven on real hardware |
| O2 Hardware bundles | Requires a documented recovery path per bundle (MISSION.md: "recovery paths are mandatory") â a customer who loses/breaks the bundled key must have a tested recovery flow before this ships, not after |
| O3 Support/SLA | Requires B-VM-CTAP2 closed (deterministic software-level FIDO2 coverage) â an SLA on a feature whose CI can't yet reliably prove itself is a support promise with no evidence backing it |
| O4 Managed CI | Requires PR #32 (sbsign + libykcs11 PKCS#11) merged and a documented "customer key stays customer-held" architecture, per covenant Â§2 |
| O5 Consulting | Requires the ARM64 fTPM stack status the consulting scope covers (see arm64-ftpm-phase-f0 / arm64-path-a-b-board-status refs) â don't scope a port to hardware whose own board rehearsal (B-ARM64-PATHA) hasn't run |
| O6 Training | No trust-chain readiness gate â gated only on training material existing and being accurate against current docs |
| O7 Grants/pilots | Gated on OMN-86's target list landing first |

## 4. Revenue priority

Ordered by dependency on already-close-to-ready work, not by hypothesized size:

1. **O6 Training + O5 Consulting** â lowest readiness-gate dependency, can start
   once material/scoping exists; project-based, not recurring, so lowest
   commitment risk while other gates close.
2. **O3 Support/SLA** â recurring, but explicitly gated on B-VM-CTAP2 (already
   the leader's active CI mission per the pulpit) closing first.
3. **O1 Managed enrollment** â recurring, gated on the real-hardware validation
   scenarios (OMN-63, already drafted) actually being run, not just defined.
4. **O2 Hardware bundles** â non-recurring, gated on a recovery-path design that
   doesn't yet exist as a concrete doc.
5. **O4 Managed CI** â recurring but gated on PR #32 landing and a key-custody
   architecture that needs its own design work, not assumed here.
6. **O7 Grants/pilots** â external-funder timeline, gated on OMN-86, treated as
   upside rather than a near-term revenue line.

## 5. Assumptions requiring paid-pilot validation

- That fleet operators will pay a *recurring* fee for enrollment management
  rather than treating it as a one-time setup task they do themselves with
  `homectl`/`bootc` directly.
- That the ~$25â70 per-key hardware cost (MISSION.md) leaves enough margin at a
  bundle price point customers will actually pay, once pre-flash/enrollment
  labor is included â not validated by any pricing data fetched in this session.
- That a support SLA is sellable *before* B-VM-CTAP2 closes, or whether
  prospects wait for that evidence first â untested assumption in section 3.
- That customers will route real (not test) signing traffic through a
  yubiOS-managed CI service (O4) rather than treating key custody as a hard
  no regardless of architecture.
- That OMN-86's funding targets and O7 pilots are commercially distinct from
  O1/O3 rather than the same design partners double-counted across both.

## Dependencies

- Section 3 depends on OMN-63 (real-hardware validation scenarios, PR #104) and
  the leader's active B-VM-CTAP2 CI mission.
- Section 1's covenant checks depend on OMN-70/OMN-82 (PR #106, PR #107).
- Feeds **T9 (OMN-84 pilot collateral)** and **T17 (OMN-78 customer ROI model)**,
  both of which share this offer catalog per the pulpit's merge order.



## Attestation coverage

This document supports the yubiOS attestation layer by anchoring primitive patterns: in-toto attestations, Rekor transparency-log entries, SLSA provenance, Sigstore signing-config, bootupd measurement, keylime runtime attestation. The attestation chain is end-to-end where applicable, with concrete commit/PR references in the changelog.



## Least-privilege coverage

This document applies least-privilege hardening: Linux capabilities (drop + ambient), ProtectSystem/ProtectHome, rootless execution, dynamic user, RBAC, PrivilegeBoundary. Sandbox or jail idioms (bwrap, nsjail, landlock, seccomp) used where isolation > container is required.



## Continuous / adaptive coverage

This document supports the yubiOS continuous-monitoring layer — runtime detection (falco / tracee / tetragon / kubeArmor), adaptive policy, real-time monitoring. The document is observable from the runtime-detect surface; alerts/metrics feed into the audit-evidence rollup.


## Verification

- Read `offer-pricing-architecture-2026-07-25.md` end-to-end against this section's claim.
- Run the relevant CI workflow on a draft branch (see `docs/CI_MAP.md`).

_Atomic RSI cycle-6 flip._


## Composition

- Sits next to sibling files in this directory.
- See `docs/ARCHITECTURE.md` for the full yubiOS dependency graph.

_RSI cycle-7 atomic flip (gap-informed, NSS-axis(adjacent_problems))._

## Composition -- cycle 16

```json
L3055 -- refs/offer-pricing-architecture-2026-07-25.md
  hypothesis:  config refs/offer-pricing-architecture-2026-07-25.md: NSS 7-relation composition taxonomy (contains / imports / calls / publishes / subscribes / reads / writes / deploys-with / depends-on) -- file declares its in-graph and out-graph surface explicitly
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
  score:       38
  caveat:      composition-axis sweep is heuristic regex-based; LLM-as-judge would refine edge coverage; static-vs-runtime-vs-config edge distinction not empirically tested in this cycle
```

**Composition invariants added (cycle 16):** callers/consumers documented under `callers:`; callees/dependencies under `callees:`; integration points (protocol, payload, timeout, retry, owner) under `integrations:`; sibling files (parallel artifacts sharing responsibility) under `siblings:`; module boundary (public API vs private internals, allowed/forbidden edges) under `module_boundary:`; edge type distribution (static / runtime / config-discovered) under `edge_distribution:`; ownership and state boundary under `ownership_state:`. The 7-relation composition taxonomy (contains / imports / calls / publishes / subscribes / reads / writes / deploys-with / depends-on) is the controlled vocabulary; every composition claim is backed by a source path or build/CI artifact.

- Callers: docs/PLAN.md, refs/customer-roi-model-2026-07-25.md.
Callees: pricing tiers; sibling: refs/three-year-revenue-cost-model-2026-07-25.md.

See `nss-composition` SKILL.md for the full 7-relation taxonomy, the 10-dimension 0-20 scoring rubric, and the Parnas/SEI / arc42 Building Block View / C4 / dependency-cruiser / package-principles (REP/CCP/CRP/ADP/SDP/SAP) prior-work frames. Cross-context invariance: this file is safe for operator / developer / CI / architect, with a static-vs-runtime-vs-config edge distinction that prevents graph-type conflation.
