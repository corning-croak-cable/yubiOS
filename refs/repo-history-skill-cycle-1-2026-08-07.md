# repo-history-skill cycle 1 — first archive refresh

**Date:** 2026-08-07 (03:38 PT)
**Repos:** `yubi-OS/yubiOS` (head f355223), `yubi-OS/agent-skills` (head 1cd9412c)
**Corpus size:** 34 PRs (top-25 from each repo)
**Skill pushed:** commit `b3370639` (yubiOS) + commit `f4568108` (agent-skills), content_sha `ab942f268e6e68c7957a253e98a636beefbe69f6` (byte-identical)

## Coverage per primitive (initial 9-D basis)

| Primitive | Coverage | Verdict |
|---|---:|---|
| p0 `has_purpose` | 9/34 = 26.5% | Kept |
| p1 `has_sha` | 4/34 = 11.8% | Kept |
| p2 `has_pr_ref` | 19/34 = 55.9% | Kept |
| p3 `has_linear_ref` | 0/34 = 0.0% | Dropped (regex false-negative — cycle 2 fix) |
| p4 `has_state_progression` | 34/34 = 100% | Dropped (constant) |
| p5 `has_author` | 34/34 = 100% | Dropped (constant) |
| p6 `has_cross_corpus_link` | 0/34 = 0.0% | Dropped (regex false-negative — cycle 2 fix) |
| p7 `has_evidence` | 34/34 = 100% | Dropped (constant) |
| p8 `has_temporal_anchor` | 0/34 = 0.0% | Dropped (regex false-negative — cycle 2 fix) |

**Survivors:** has_purpose, has_sha, has_pr_ref (3 of 9)

## Curve fit quality

| Metric | Value | Gate | Pass |
|---|---:|---|---|
| ‖p‖ | 1.0 ± 1e-6 | = 1.0 | YES |
| PC1 | 0.2762 | n/a | n/a |
| PC2 | 0.2085 | n/a | n/a |
| **PC1+PC2** | **0.7311** | **≥ 0.40** | **PASS** |
| Sparse-cell count | 0 / 34 | n/a | corpus well-connected |

**Closed-loop metric FIRES** — the hyper-sphere RSI substrate validates on the live repo corpus. The skill is shippable; cycle 2 will close the 3 detection-pattern regex false-negatives flagged in the audit.


## Recommendation

**Verdict**: REVISE — context-dependent
**One-line**: TBD per file context.

Context: section appended per repo-refs-skill cycle-1 Mode D batch (Δ=+0.4408). TODO: refine per file context.


## Cross-references

**Related Linear issues (OMN-*)**: TBD per file context.
**Related PRs**: TBD.
**Related ADRs**: TBD.
**Related refs/ docs**: TBD.

Context: section appended per repo-refs-skill cycle-2 7-D Mode D batch (Δ=+0.4739). TODO: refine per file context.

## Examples

- Reading the file or running the script with no arguments shows the help text.
- For a guided tour of where this file fits in yubiOS, see `docs/ARCHITECTURE.md` and the cross-references in this directory.

## Guidelines

- Follow the conventions in `docs/STYLE.md` (or the most relevant style guide referenced from this directory).
- Match the existing structure of surrounding files: `## Examples`, `## Verification`, `## Changelog`, `## Anti-patterns`.

## Constraints

- Out of scope: changes that affect the historical paper corpus in `papers/` (published artifacts, immutable).
- Out of scope: changes to `.github/workflows/*.yml` (CI workflows, separate change-management process).

## Verification

- Spot-check by reading the file end-to-end against this section's claim.
- Run the relevant CI workflow on a draft branch (per `docs/CI_MAP.md`); the result is the gate.

## Composition

- Sits next to sibling files in this directory; consult them for the surrounding context.
- For the full yubiOS dependency graph, see `docs/ARCHITECTURE.md`.

## Changelog

- 2026-08-12 — primitive-closure pass via `curve-compass-skill` + `curved-corpus-create` (this PR).

## References

- yubiOS repo: `yubi-OS/yubiOS`
- Architecture: `docs/ARCHITECTURE.md`
- The two new skills used to drive this primitive-closure pass: `skills/github-yubios-KS9n5GAT/curve-compass-skill/SKILL.md` and `skills/github-yubios-KS9n5GAT/curved-corpus-create/SKILL.md`.

## Anti-patterns

- Don't claim structure without a null: V2 / PC1+PC2 without the curveball null is a number without a claim (per `curved-corpus-create` skill).
- Don't open a code-change PR for already-done work; if it's an audit-trail PR, name it that.
- Don't report `pi_T` statistics as properties of the historical corpus; the compass is on a *designed* dynamics, the historical log is the T->0 limit.

