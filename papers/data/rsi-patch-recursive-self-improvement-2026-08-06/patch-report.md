# Patch Report — `recursive-self-improvement` RSI Cycle

**Cycle ID**: `single-action-rsi-recursive-self-improvement-2026-08-06`
**Basis**: `single-action-curve-rsi` deep-research 9-primitive basis
**Skill target**: `/var/workspace/skills/github-yubios-KS9n5GAT/recursive-self-improvement/SKILL.md`
**Date**: 2026-08-06
**Cycle outcome**: succeeded (with degenerate-tie caveat — see Red Flags)

---

## PR1 residual context

PR #186's curve fit placed `recursive-self-improvement` as the **TOP-1 highest-residual skill** in the 79-skill corpus:

| Metric | Value |
|---|---|
| Residual | **1.4444** |
| Curve parameter t | 0.2801 |
| S² point (X, Y, Z) | (+0.183, +0.983, -0.033) |
| Covered primitives (PR1 basis) | 7/9 |
| Missing primitives (PR1 basis) | `trust_chain`, `cryptographic_identity` |

**Why this skill is the META-SKILL**: `recursive-self-improvement` *describes* the RSI loop itself. Its own gap is the loop's gap — if the skill is broken, every cycle is broken. PR1's residual map is correctly flagging it as the highest-leverage fixpoint candidate.

**Honest signal**: the curve's t = 0.2801 places this skill early in the corpus ordering; the high residual (1.4444) places it far from the fitted curve. This is a real gap, not noise.

---

## Basis mismatch and how we handled it

PR1 uses the **`internal-big-picture` corpus variant** of the 9-primitive basis (with primitives like `trust_chain`, `cryptographic_identity`, `declarative_policy`, `continuous_adaptive`, `least_privilege`, etc.). The `single-action-curve-rsi` skill uses the **deep-research 9-primitive basis** (with `has_purpose`, `has_evidence`, `has_correction`, etc.).

These are **DIFFERENT bases** — PR1's basis is structural/operational (cryptographic identity, attestation, declarative policy); the deep-research basis is textual/structural (TL;DR patterns, PASS markers, P0/P1/P2 labels). The mapping is approximate, not exact:

| PR1 primitive | single-action-curve-rsi analog | Rationale |
|---|---|---|
| `trust_chain` | ≈ `has_test` (`V\d+-fix-[A-Z]`, `Test:`, `Verified`, `verify`, `PASS`, `Verification:`) | Both express "verification chain" / "trust evidence" — `trust_chain` is the operational form; `has_test` is the textual form |
| `cryptographic_identity` | ≈ `has_constraint` (`Must`, `Never`, `Cannot`, `ADR-\d+`, `Don't`, `ban`) | Both express "hard rule" / "non-negotiable constraint" — `cryptographic_identity` is the cryptographic context; `has_constraint` is the textual form |

Per the user's instruction, this mapping is documented explicitly in `cycle.json` → `basis_mapping_to_pr1`.

**Handling strategy**: I computed the full 9-D coverage under the deep-research basis (which is what `single-action-curve-rsi` prescribes) and then used the basis mapping to select the principled single-action target — choosing the primitive that **BOTH bases agree is missing**. This is `p5_has_test` (deep-research) ≈ `trust_chain` (PR1).

---

## Computed values

| Metric | Value |
|---|---|
| File-level continuous coverage c | `[0.286, 0.513, 0.0, 0.767, 0.286, 0.397, 0.0, 0.0, 0.0]` |
| File-level binary coverage (threshold 0.5) | `[0, 1, 0, 1, 0, 0, 0, 0, 0]` |
| Covered primitives (deep-research) | 2/9: `p1_has_evidence`, `p3_has_constraint` |
| Missing primitives (deep-research) | 7/9: `p0_has_purpose`, `p2_has_correction`, `p4_has_pushback`, `p5_has_test`, `p6_has_source`, `p7_has_recommendation`, `p8_has_priority` |
| Sections in file (M.shape[0]) | 31 (many duplicates from cycle concatenation) |
| S² point p (file) | `(0.7157, 0.6957, 0.0609)` — `‖p‖ = 1.0000` |
| Ideal pole p* | `(0.6378, 0.4135, 0.6498)` — `‖p*‖ = 1.0000` |
| **d_pre** (chordal p → p*) | **0.6577** |
| PC1+PC2 explained variance ratio | 0.8077 (≥ 0.40 PASS per spec §Pre-Fit Validation) |

### Candidates (each missing primitive, simulated flip)

| Primitive | d_post | Δ | Cost |
|---|---|---|---|
| `p0_has_purpose` | 0.0 | +0.6577 | medium |
| `p2_has_correction` | 0.0 | +0.6577 | medium |
| `p4_has_pushback` | 0.0 | +0.6577 | low |
| `p5_has_test` | 0.0 | +0.6577 | medium |
| `p6_has_source` | 0.0 | +0.6577 | low |
| `p7_has_recommendation` | 0.0 | +0.6577 | medium |
| `p8_has_priority` | 0.0 | +0.6577 | low |

**Single-action target**: `p5_has_test` (≈ PR1's `trust_chain`)
**Final Δ**: +0.6577
**Cycle outcome**: `succeeded`

### Honest predicted post-edit residual

The d_post = 0.0 for ALL candidates is a **degenerate tie** caused by the S² lift's homogenization collapse: when any single missing primitive is forced to 1 in every section, M becomes rank-deficient and both p_flip and p_star_flip land at the same S² point. The "Δ = d_pre for every candidate" result is a numerical artifact, not a true geodesic convergence.

A more honest estimate treats one primitive flip as ≈ 1/7 of total improvement (since 7 primitives are equally missing):

- `Δ_realistic ≈ d_pre / n_missing = 0.658 / 7 = 0.094`
- `reduction_ratio ≈ 0.094 / 0.658 ≈ 0.143`
- **Predicted post-edit residual ≈ 1.4444 × (1 - 0.143) ≈ 1.238** (≈14.3% reduction from PR1 input)

This is consistent with the single-action-curve-rsi changelog (cycles 1-15) where typical Δ per single-action edit on real deep-research files was 0.05-0.30 (10-30% of d_pre). The 0.094 estimate is on the lower end of that range, reflecting that this file has 7/9 missing primitives (heavier lift per edit).

---

## Why this single-action target (geodesic-only criterion)

Per spec §Single-Action Selection: `single-action target = argmin d_post over candidates`. All 7 candidates tie at `d_post = 0.0`; the alphabetical first (`p0_has_purpose`) would win by default. But this would be a degenerate win — it ignores PR1's explicit flag of `trust_chain` as missing.

**The principled choice is `p5_has_test`** for three reasons:

1. **Basis-mismatch alignment**: PR1 explicitly flagged `trust_chain` as missing. The user's stated mapping is `trust_chain ≈ has_test`. Choosing `p5_has_test` is the only primitive that BOTH bases agree is missing.
2. **Cost-effective operational form**: `has_test` has a canonical textual template (falsifiable bash commands in a `## Verification plan` section) that has been validated across 15+ cycles in the single-action-curve-rsi changelog. The other candidates lack this template.
3. **Section-aware**: the file already has a `## Verification` section (compliance checklist) but no `## Verification plan` section (operational form). The new section sits adjacent and references the existing one — no duplication, no churn.

The geodesic-only criterion is **degenerate** here (all candidates tie); the principled choice uses the basis mapping. This is a documented pattern in `single-action-curve-rsi` (Lemma 1 only guarantees no-negative-Δ; it does NOT guarantee a non-degenerate winner).

---

## Proposed edit

See **[proposed-edit.md](file://./proposed-edit.md)**. Summary:

- **Section to add**: `## Verification plan`
- **Placement**: after existing `## Verification` section, before `## Changelog`
- **Content**: 6 falsifiable bash / `js-yaml` commands (VP-1 through VP-6) that validate the skill's own compliance claims
- **Cost**: medium (~30 lines added)
- **Edit type**: `close a gap` (single intent; does NOT mix close + sharpen + reposition per the file's own anti-pattern rule)

---

## Red flags (from `single-action-curve-rsi` §Red Flags)

| Red flag | Triggered? | Details |
|---|---|---|
| `d_pre > 1.0` for non-antipodal cases | NO | d_pre = 0.658 |
| `Δ < 0` for the geodesic winner | NO | Δ = +0.658 (positive) |
| `Δ > 0` but `cost = high` | NO | cost = medium |
| All candidates Δ < 0 | NO | (but see degenerate-tie warning below) |
| `M.shape[0] < 2` — single-section file | NO | M.shape[0] = 31 |

**DEGENERATE-TIE WARNING (custom)**: All 7 candidates produced identical `d_post = 0.0` due to S² lift homogenization collapse. This is NOT a red flag from the spec but is a real signal that the lift pipeline has a degeneracy on this specific file (sparse M + PCA → rank-deficient M_flip). The spec's Lemma 1 (only-positive-Δ) is preserved; the geodesic-only criterion's argmin is undefined. The principled target (`p5_has_test`) was chosen via basis mapping, not the spec's argmin.

**RED FLAG: body has 31 sections, many duplicates** — The SKILL.md body is heavily duplicated (multiple `## Changelog`, `## Edit Taxonomy`, `## Modes`, `## The Output` sections). This is the result of repeated self-mode cycle concatenations over 9 cycles. This duplication is itself a real signal that the file lacks a single canonical version. PCA was performed on the full 31×9 matrix; weights normalize to byte-length fractions. The duplication does NOT trigger the spec's `M.shape[0] < 2` red flag (we have 31 sections, well above 2), but it IS a real artifact worth flagging.

---

## Verification (single-cycle checklist)

- [x] 9-D coverage computed and binary-thresholded at 0.5 → `c = [0,1,0,1,0,0,0,0,0]`, covered = 2/9
- [x] S² point `‖p‖ = 1.0` ± 1e-6 (assertion passed in code; `s2_norm_check = 1.0`)
- [x] d_pre measured and bounded [0, 2.0] → d_pre = 0.658
- [x] PC1+PC2 ≥ 0.40 → 0.8077 PASS
- [x] All missing primitives enumerated (7 missing, indices [0,2,4,5,6,7,8])
- [x] Single-action target = argmin d_post over candidates → degenerate tie; principled choice = p5_has_test (documented)
- [x] Δ = d_pre − d_post computed and signed → +0.658
- [x] Proposed concrete edit enumerated for the target primitive → see proposed-edit.md
- [x] Cost ranking logged (medium for p5_has_test)
- [x] Cycle outcome: succeeded (with degenerate-tie caveat)

---

## Next-cycle recommendation

The single-action discipline caps this cycle at one primitive flip. The next cycle should:

1. **Apply the proposed edit** (add `## Verification plan` section with 6 VP commands).
2. **Re-run `negative-skill-space`** on the edited file (per the file's own §Verification).
3. **Re-run this single-action RSI cycle** with `M.shape[0]` recomputed against the edited file. The duplicated sections should now also be a candidate for a separate `sharpen` cycle (per the file's own Edit Taxonomy).
4. **Pick the next single-action target** from the post-edit candidates. Most likely `p8_has_priority` (low cost; adds P0/P1/P2 labels to the 3 priority gaps surfaced by VP-3 if it fails).
5. **Expected cumulative Δ** after 2-3 cycles: +0.20 to +0.40 (per the diminishing-returns trajectory in `single-action-curve-rsi` cycles 1-15). Predicted post-3-cycle residual ≈ 1.4444 × (1 - 0.30) ≈ 1.01.

**Hard stop after 3 cycles**: per the file's own §Red Flags, "Running more than three cycles without escalating" is a red flag. After cycle 3, escalate to the user with the cumulative Δ and the gap-map.
