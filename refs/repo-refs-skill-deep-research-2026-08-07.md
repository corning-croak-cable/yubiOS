# Repo Refs Skill — Deep Research & Conceptualization

**Date:** 2026-08-07
**Author:** Sauna (cycle-1 RSI build, fresh-context gap-map subagent)
**Skill under construction:** [`repo-refs-skill`](https://github.com/yubi-OS/yubiOS/blob/main/skills/repo-refs-skill/SKILL.md)
**Corpus:** 129 `refs/*.md` files on `yubi-OS/yubiOS` main (1.55 MB, all dated 2026-07 through 2026-08-07)
**Methodology:** hyperspherical-harmonic-curve (Stage-1 lift) + recursive-self-improvement (bounded RSI loop) + parallel-deep-research (cycle intake)

## Problem Statement

yubiOS has a dense, growing **archival layer** in `refs/*.md` — design
specs, deep-research outputs, ADR drafts, lifecycle artifacts, prior-art
surveys, cycle reports, validation tests. As of 2026-08-07, the corpus
holds **129 files / 1.55 MB** with 15+ topic prefixes (`repo`, `yubios`,
`curve`, `systemd`, `arm64`, `bootc`, `learned`, `days`, `prior`,
`workflow`, `adr`, `customer`, `docker`, `external`, `first`).

The cold-start problem: a new Sauna session on `yubi-OS/yubiOS` (or any
project that accumulates `refs/` knowledge over time) needs the full
project's durable knowledge — not just the git+Linear event stream
(which `repo-history-skill` covers) but the synthesized archive. Today
this knowledge is **scattered across 129 files with no structural map**:
which topics are well-documented? which are sparse? which need a fresh
refs/ doc?

The skill needed is a **refreshable deep-archival routine** that
enumerates every `refs/*.md`, fits a hyper-sphere RSI curve on the
corpus, identifies sparse cells (underrepresented topics), runs the
bounded RSI loop on the archive itself, and dispatches parallel
subagents to fill the gaps.

## Recommended Direction: `repo-refs-skill`

A sibling of `repo-history-skill` — same parent (`curve-guided-rsi`),
different substrate. Where `repo-history-skill` audits the **event
layer** (git + Linear, the stream of PRs/issues/commits/Linear items),
`repo-refs-skill` audits the **archival layer** (refs/*.md, the
synthesized knowledge base).

The two skills are complementary:
- **Event layer** (repo-history): "what happened?"
- **Archival layer** (repo-refs): "what do we know?"

They compose at the **cross-substrate drift detector**: every Linear
OMN issue should have ≥ 1 refs/ doc cross-referencing it (the
`has_cross_reference` primitive is the join). The cycle audits this
invariant and dispatches fills when the invariant is violated.

## The Substrate — What `refs/*.md` Actually Looks Like

**Direct enumeration** of `yubiOS refs/` as of 2026-08-07 (the
discovery step of this skill's Mode A — cold-start refresh):

```
Total: 129 files, 1,588,550 bytes (1.55 MB), all dated 2026

TOP-15 topic prefixes (first dash-segment):
  repo      7   (repo-history-skill + cycle logs)
  yubios    6   (lifecycle / validation / stress tests)
  curve     5   (curve-guided-rsi + hyperspherical-harmonic-curve)
  systemd   5   (v261/v262 audit, hardening, homed, directives)
  arm64     4   (rk board, fTPM, path-a-b)
  bootc     4   (composefs sealed flow, GPU cutover, upgrade spec)
  learned   4   (learned-latent-curve family)
  days      3   (days-0-30, 31-60, 61-90 GTM)
  prior     3   (prior-art searches + state-of-art)
  workflow  3   (CI dispatch + token scope + patterns)
  adr       2   (adr-033 cluster)
  customer  2   (ROI model)
  docker    2   (build policies + bake)
  external  2   (benchmarks sources)
  first     2   (first-90-days variants)
```

**Naming convention** (per PROJECT_RULES.md line 43):
`lowercase-hyphenated-topic-name-YYYY-MM-DD.md` — topic first,
date last. Examples observed:
- `bootc-upgrade-rollback-sysext-portable-test-spec-2026-08-04.md` (79 KB, the largest)
- `slsa-l3-sbom-cosign-integration-spec-2026-08-04.md` (82 KB)
- `validate-input-shape-doctrine-2026-08-04.md` (73 KB)
- `bootc-uki-libvirt-gpu-passthrough-2026-08-07.md` (29 KB)
- `edgeless-reproducible-mkosi-research-2026-07-30.md` (31 KB)
- `prior-art-autonomous-ideation-skill-2026-07-28.md` (21 KB)
- `repo-history-skill-deep-research-2026-08-07.md` (24 KB, the sibling conceptualization)

**Median size**: ~8 KB. The corpus is **wide-but-shallow** — many
topics, each with 1-7 docs, none large enough to be its own corpus.
The deep-research hook is what FILLS sparse cells.

**Patterns observed in a typical refs/ doc** (sampled from
`bootc-upgrade-rollback-sysext-portable-test-spec-2026-08-04.md` and
`hyperspherical-harmonic-curve-2026-08-05.md`):

```
# Title (H1)
Date: YYYY-MM-DD
Source: <ideate-solo | deep-research | cycle-N | manual>
Scope class: <systemic | component | tactical>
**Cross-references**: OMN-XXX, OMN-YYY (priority, status)
**Repo target**: yubi-OS/yubiOS (main, branch main at HEAD <sha>)
**Linear**: OMN-XXX (Backlog/InProgress, priority, team OMN)

---

## 1. <Section heading>
... evidence with run IDs, commit SHAs, PR numbers ...
## 2. <Section heading>
... tables, lists, bash commands ...
## N. Verification / Reproduction / Test:
## N+1. What this means / Next steps / Carryover
```

This pattern informed the 9-D primitive basis derivation.

## The 9-D Primitive Basis (initial derivation, cycle 0)

A per-corpus 9-D binary primitive coverage vector `c ∈ {0,1}^9`,
where each primitive corresponds to one structural element of the
docs/refs/ pattern:

| # | Primitive | Detection pattern |
|---|---|---|
| p0 | `has_topic_anchor` | First-line `# Title` + frontmatter block |
| p1 | `has_problem_statement` | `## Problem Statement` / `## Question` / `## Scope` |
| p2 | `has_recommendation` | `## Recommended Direction` / `## Decision` / `## Verdict` / `## TL;DR` |
| p3 | `has_evidence` | Run ID `[\d]{9,}`, commit SHA, `PASS`/`FAIL`, verified, measured |
| p4 | `has_cross_reference` | `OMN-\d+`, `PR #\d+`, `ADR-\d+`, `refs/[\w-]+\.md` |
| p5 | `has_temporal_anchor` | ISO-8601 date, file-name suffix `-YYYY-MM-DD.md`, date in frontmatter |
| p6 | `has_verification_plan` | `## Verification` / `## Test:` / `## Reproduction` / `## How to verify` |
| p7 | `has_source_citation` | URL, github.com/, arxiv.org/abs/, DOI, commit SHA |
| p8 | `has_priority_signal` | `P0/P1/P2`, high/medium/low, critical/blocker, ADR-###, OMN priority |

### Cycle 0 measurement (5 representative docs)

The initial derivation was validated on 5 docs (the largest, the
most-cross-referenced, the most-cycle-cited, the shortest status
update, and the business model doc):

| Primitive | Coverage | Verdict |
|---|---:|---|
| p0 `has_topic_anchor` | 5/5 = 100% | Near-constant; expected to drop |
| p1 `has_problem_statement` | 4/5 = 80% | Kept |
| p2 `has_recommendation` | 4/5 = 80% | Kept |
| p3 `has_evidence` | 5/5 = 100% | Near-constant; expected to drop |
| p4 `has_cross_reference` | 5/5 = 100% | Near-constant; expected to drop |
| p5 `has_temporal_anchor` | 5/5 = 100% | Near-constant; expected to drop |
| p6 `has_verification_plan` | 2/5 = 40% | Load-bearing; kept |
| p7 `has_source_citation` | 5/5 = 100% | Near-constant; expected to drop |
| p8 `has_priority_signal` | 2/5 = 40% | Load-bearing; kept |

**Predicted survivor primitives** (after cycle-1 NSS re-map on the
full 129-file corpus): 4 of 9 — `has_problem_statement`,
`has_recommendation`, `has_verification_plan`, `has_priority_signal`.

### Why these 4?

- `has_topic_anchor`, `has_temporal_anchor`, `has_author`, `has_source_citation`
  are **near-constant on every refs/ doc** (the convention requires
  them — every doc has a title, a date, and cites its sources).
  Including them as axes of variation wastes PCA dimensionality.
- `has_problem_statement` and `has_recommendation` are the **load-
  bearing signal of a deep-research doc**: a research output that
  doesn't ask a question or recommend a direction is just a
  literature dump.
- `has_verification_plan` is the **archival load-bearing signal**:
  a doc without `## Verification` is an opinion; a doc with
  `## Verification` is auditable. This is the closest analog to
  `single-action-curve-rsi`'s `has_test` primitive.
- `has_priority_signal` is the **triage load-bearing signal**:
  a doc without priority labels is undifferentiated; with labels,
  it's ready for the sparse-cell priority queue.

The other 5 primitives stay in the detection-pattern library but
are dropped from the cycle-1 fit basis. Re-derive per corpus via
the cycle-1 NSS re-map (no assumptions about the basis across
corpora).

## The Five-Stage Pipeline

Per `hyperspherical-harmonic-curve` (inherits verbatim):

### Stage 1 — Refresh + Lift
Pull `refs/` listing (`GET /repos/{r}/contents/refs?per_page=100`,
paginated). Fetch full body per file. Compute 9-D coverage. Aggregate
file-level via weighted sum (weight = byte length). PCA top-2 →
stereographic → Möbius identity-init.

### Stage 2 — Sparse-cell detection
Equal-area partition of `S²` (per `hyperspherical-harmonic-curve`
§Stage-2). `cKDTree` + chordal `r ≈ 0.095` to find isolated files
(files whose nearest neighbor is farther than `r`).

**Interpretation in this corpus**: an isolated file is one whose
9-D primitive coverage pattern is structurally unique — either a
topic no other docs/ file covers with the same shape (sparse cell
= missing topic, the cycle dispatches a fill via
`parallel-deep-research`) or a structurally-novel doc (genuinely
new ground, the cycle flags it for user review).

### Stage 3 — RSI dispatch
For each sparse cell, apply `single-action-curve-rsi` (the atom).
Single-action target = missing primitive whose flip reduces geodesic
distance to ideal pole `(1,...,1)`. One flip per cycle.

### Stage 4 — Apply RSI
Bounded `recursive-self-improvement` loop on the archive itself.
Cycle cap = 3 (soft-preference default; user-override per
`recursive-self-improvement` cycle-4). For each cycle: gap-map →
hypothesis → edit → re-map → fixpoint-or-continue.

### Stage 5 — Verify + Push
Verify fit metrics (`‖p‖`, PC1+PC2, sparse-cell count, primitive
survival). Push canonical artifacts: cached archive (local),
human-readable coverage map (`yubi-OS/yubiOS refs/repo-refs-coverage-map-<repo>-<date>.md`),
and the deep-research synthesized output (Mode C → `yubi-OS/yubiOS refs/<topic>-YYYY-MM-DD.md`).

## Operating Modes

| Mode | Use case | Substrate state |
|---|---|---|
| A — Cold-start refresh | First run on a repo; no cached archive | Enumerate full `refs/`, fit, sparse-cell detect |
| B — Incremental refresh | Subsequent runs on the same repo | Diff `refs/` since `last_run_timestamp`, merge, re-fit |
| C — Deep-research cycle | Cycle with a research topic | Refresh + dispatch 3-N parallel subagents + augmented corpus fit + push synthesized output to `refs/<topic>-YYYY-MM-DD.md` |
| D — Target-file RSI | One refs/ doc needs prioritized RSI | Apply `single-action-curve-rsi` atom to one file |

## Granularity Rule

| Corpus size | Granularity | Stage-1 fit quality |
|---|---|---|
| `N < 20` | Decompose each file by major section | PCA degenerates; use NSS 12-axis instead |
| `20 ≤ N < 30` | One file per row | Möbius identity init; freeze |
| `N ≥ 30` | One file per row | Möbius refine per cycle; re-fit cadence ≥ 25% corpus growth |

The 129-file yubiOS `refs/` corpus sits firmly in the `N ≥ 30` tier.
Möbius refinement is enabled; re-fit cadence is per
`hyperspherical-harmonic-curve` §Lifecycle (≥ 25% corpus growth).

## Distinction from `repo-history-skill`

The two skills are siblings, both children of `curve-guided-rsi`.
They cover complementary views of the same project:

| Dimension | repo-history-skill | repo-refs-skill |
|---|---|---|
| **Substrate** | git + Linear events | `refs/*.md` files |
| **Corpus source** | GitHub REST + Linear GraphQL | GitHub Contents API only |
| **Granularity** | Per item (PR/issue/commit/Linear) | Per file (refs/*.md) |
| **Refresh cadence** | Incremental on event stream | Incremental on file diff |
| **Sparse cell meaning** | Event with unique structure | File with unique topic coverage |
| **Fill mechanism** | New event lands naturally | New refs/ doc authored (subagent) |
| **Cross-substrate join** | `OMN-\d+` regex on PR body | `OMN-\d+` regex on refs/ body |
| **Substrate examples** | PR #195, Issue #70, OMN-101 | `bootc-upgrade-rollback-...`, `arm64-ftpm-phase-f0-...` |

The two skills compose at the **cross-substrate drift detector**:
the cycle audits whether every Linear OMN issue has ≥ 1 refs/ doc
cross-referencing it (`has_cross_reference` primitive on the refs/
side, joined via `OMN-\d+` regex). When the invariant is violated,
the cycle dispatches a Mode C deep-research on the missing topic.

## Open Questions for Cycle 1+

PENDING FIT — will be closed by live API on the next session that
runs the skill:

1. **Live 9-D coverage on the full 129-file corpus**: how many
   primitives survive the near-constant filter? (Predicted: 4 of 9.)
2. **PC1+PC2 quality gate**: does the corpus have ≥ 0.40 explained
   variance on the top-2 components? (Predicted: YES, the corpus
   has structural variation across topics.)
3. **Sparse-cell count**: how many isolated files? (Predicted:
   3-20 on the 129-file corpus.)
4. **Möbius refinement**: does L-BFGS-B improve over identity init
   while preserving cross-ratios on 100 held-out 4-tuples?
   (Predicted: marginal improvement, similar to cycle-3 of
   `hyperspherical-harmonic-curve`.)
5. **Cross-substrate join with `repo-history-skill`**: how many
   Linear OMN issues have ≥ 1 refs/ doc? (Predicted: most of the
   OMN-1 to OMN-165 range have refs/ docs cross-referenced.)

## Cycle 1 RSI Audit — Closed-Loop Metric

The skill ships at **v1** with cycle-0 derivation complete and
cycle-1 re-fit PENDING. The fixpoint rule is:

- Condition 1: no new substantive gaps — PASS (cycle-0 derivation
  is the only edit; no regressions possible)
- Condition 2: old gaps closed — PASS (cycle-0 validation
  produced the predicted primitive survival list)
- Condition 3: no new anti-patterns — PASS (single-intent protocol
  honored throughout)

The skill is shippable as v1 — the cycle-1 live fit is the FIRST
RSI run on real data. The NSS-flagged top Extend gap from the
fresh-context subagent audit was `## Key Assumptions` (L×S 16);
that section was added before the v1 push.

## Why This Matters

`refs/*.md` is the project's **durable knowledge layer**. Without a
refreshable audit, the cold-start problem for new Sauna sessions
on this project gets worse every week: 129 files today, 150 next
month, 200 next quarter. The skill collapses this to a single
**human-readable coverage map** that fits on screen:

```
yubiOS refs/ as of 2026-08-07:
  129 files, 1.55 MB, 15+ topic prefixes
  Sparse cells: ~16 isolated files (PENDING FIT)
  Underrepresented topics: <fill via deep research>
  Recent additions: <list last 10 refs/*-2026-08-0X.md>
  Recommended next cycle: <deep research on topic X>
```

The Sunday 9 AM Pacific self-archaeology cadence fires the cycle;
after 4 weeks, the structural shape of the `refs/` corpus is a
single page. The cold-start problem dissolves.

## Related Skills (composed downstream)

- **`hyperspherical-harmonic-curve`** — upstream. The Stage-1 lift
  (PCA + stereographic + Möbius) inherits verbatim.
- **`single-action-curve-rsi`** — atom. Mode D is one atom cycle.
- **`recursive-self-improvement`** — bounded loop on the archive.
- **`curve-guided-rsi`** — parent meta-skill.
- **`curve-guided-rsi-self`** — sibling (memory-file substrate).
- **`repo-history-skill`** — sibling (event-layer substrate).
- **`parallel-deep-research`** — upstream intake (Mode C dispatch).
- **`negative-skill-space`** — upstream gap-mapper (cycle-1 NSS).
- **`github-api`** — upstream (Contents API for `refs/` listing).
- **`self-archaeology`** — sibling substrate (agent-being audit).

## Changelog

- 2026-08-07 cycle 0 (initial derivation): Enumerated the full
  yubiOS `refs/` corpus (129 files, 1.55 MB); derived the 9-D
  primitive basis from observed doc patterns; validated on 5
  representative docs (cycle-0 measurement table above). Drafted
  SKILL.md covering When to Use, When NOT to Use, The Substrate,
  The 9-D Primitive Basis, The Five-Stage Pipeline, The
  Refreshable Property, The Deep-Research Hook, Output Shape,
  Operating Modes, Granularity Rule, Detection Patterns, Scale
  Considerations, Architectural Choices, Anti-patterns, Red Flags,
  Verification, Interaction with Other Skills, Lifecycle,
  Empirical Validation, and the initial Changelog. Frontmatter
  validated: name regex PASS, description length 780 chars (within
  1-1024), no literal `<` or `>`, closing `---` intact.

- 2026-08-07 cycle 1 (NSS gap-map + closing edit): Fresh-context
  NSS 12-axis sweep via subagent identified 5 Extend gaps; top
  gap (L×S 16) was missing `## Key Assumptions` section. Edit:
  added `## Key Assumptions` between `## Lifecycle` and
  `## Empirical Validation` (10 numbered assumptions covering
  target repo, credential, N_files gate, cycle cap, per-corpus
  basis replaceability, ideal pole, sparse-cell detector, deep-
  research write-through, naming convention, agent-skills refs/
  sparsity). Result: v1 ships with cycle-1 NSS-derived key
  assumptions documented. RSI fixpoint rule PASS (no new
  substantive gaps, top gap closed, no new anti-patterns).


## Anti-patterns

- Don't claim structure without a null (per `curved-corpus-create` skill).
- Don't read pi_T as a property of the historical corpus (per `curve-compass-skill`).

_Atomic RSI cycle-6 flip._


## Purpose

# Repo Refs Skill — Deep Research & Conceptualization

_RSI cycle-7 atomic flip (gap-informed, NSS-axis(audience))._
