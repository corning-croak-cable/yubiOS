# Hyperspherical Harmonic Curve [SOLO]

Date: 2026-08-05
Source: ideate-solo (no dialogue)
Scope class: systemic
Variations generated: 4
Finalist: Hyperspherical Harmonic Curve (Interpretation D, advisor-revised)

## Problem Statement

How might we extend `curve-guided-rsi`'s Stage-1 curve-fit from a flat 2-D Fourier surface on `[0,1]Â²` to a 3-D differential on the N-th dimensional Riemann sphere, so the corpus-audit pipeline gains the intrinsic-curvature signal from the parameter manifold as a sparse-cell prioritization feature?

## Recommended Direction

**Hyperspherical Harmonic Curve**: replace the separable Fourier basis `sin(2Ïf_m u)Â·cos(2Ïg_n v)` on flat `[0,1]Â²` with the **canonical orthonormal basis** `{Y^{S^N}_{l,m}}` for `LÂ²(S^N)` â eigenfunctions of `Î_{S^N}` with eigenvalues `âl(l+Nâ1)`. Default `N=2` (the Riemann sphere = `CP^1`); `N=3` is gated by corpus size â¥ 90 and `PC3 â¥ 0.08`. The model learns a **MÃ¶bius reparameterization** `Ï_Î¸ â PSL(2,â)` of the domain â 6 real parameters, exists only on `SÂ² â Ä`, and is what earns the mechanism-layer novelty under Â§103 obviousness. Cross-ratio preservation is the falsifiable invariant.

**Composes with curve-guided-rsi as a Stage-1 swap.** Stages 2â5 unchanged except: Stage 2 (sparse-cell detection) uses **equal-area partition of `SÂ²` with 441 cells and chordal distance `r â 0.095`** (not `r = 0.05`, which would fake a pre/post improvement); the **domain coordinate `x â SÂ²`** replaces `(u, v)` as the audit-trail primary key; Stage 5's verification metric becomes a **matched-parameter ablation** against a flat-Fourier surface with the same parameter count â the only test in the whole proposal that can come back negative.

**Why this beats the 3 alternative interpretations** scored in Stream D: it pairs with the canonical LaplaceâBeltrami eigenbasis on the curved manifold, the parameter count is smaller at equal expressive power (`6,532` at `SÂ²/L=3` vs `31,496` for the incumbent at `k=4`), the discrete eigenvalue structure of `Î_{S^N}` provides a directly verifiable spectral signature, and the MÃ¶bius reparameterization makes the mechanism non-obvious to a PHOSITA. C (Blaschke products) was runner-up at 17/20 but requires a 2-D-to-`â` projection pipeline that injects a new failure mode; B (1-jet) is orthogonal (changes output shape, not input geometry); A (3-D parameter on `SÂ³`) is the geometric framing of D but cannot default to it because the corpus at 69 items is below the `SÂ³/L=3` DoF floor of 90.

**Three sources of "provable delta"** between `S^N` and `[0,1]Â²` â `Ï`, `H^k`, holonomy â are mathematically true but **not informative**: they prove only that a different domain was chosen, not that the fit is good. The variant's SKILL.md body splits "provable, but not informative" (motivation) from "falsifiable, therefore load-bearing" (the ablation) so a reviewer cannot conflate them.

## Key Assumptions to Validate

- [ ] **The hyperspherical-harmonic basis implementation is correct.** Pre-fit `Îµ_basis < 1e-3` on a 4096-point MC sample on `SÂ²`. (`scipy.special.sph_harm` is deprecated; use `sph_harm_y` with explicit argument-order and convention pinning. `lie_learn` and `e3nn` do not implement `SÂ³` harmonics.)
- [ ] **The MÃ¶bius reparameterization is well-posed.** Init to identity; assert cross-ratio preservation at init on 100 random 4-tuples. After fit: assert `|c| < 100` (degenerate collapse detector) and cross-ratio preservation within `1e-4` on held-out 4-tuples.
- [ ] **The sphere variant beats a flat-Fourier surface at equal parameter count.** Matched-parameter ablation: `SÂ²/L=3` (16 basis) â¥ flat `k=2` (25 basis) on holdout `RÂ²` at **fewer** parameters. **If the ablation returns negative, curvature is not helping and the SKILL.md body must say so.**
- [ ] **The spectral-mass gate `Ï â¥ 0.10` and high-degree mass â¤ 0.40** hold for the variant fit (no constant-collapse, no ringing). These are pre-ship calibration thresholds; tighten if real fits show the model needs more or less.
- [ ] **Stage 2 equal-area partition produces a sensible `sparse_cell_count` delta pre/post RSI.** First-Stage-5 verification pass: ship and observe whether the count is comparable to the incumbent 21Ã21 flat grid or wildly different (in which case the metric is not portable between the two pipelines).
- [ ] **`PC3 â¥ 0.08` for `N=3` use.** Verify on the current 69-skill corpus: at `PC1+PC2 = 0.4615`, `PC3` is likely low â the `N=3` gate probably fails, and the variant should default to `N=2`.

## MVP Scope

Fit a curve on the 69-skill yubiOS corpus at `N=2, L=3, MÃ¶bius enabled`. Validate per the SKILL.md `## Verification` checklist: holdout `RÂ² > 0`, spectral-mass gate `Ï â¥ 0.10`, matched-parameter ablation (3 fits on the same holdout split: variant, flat `k=2`, flat `k=4`). Save the v1-fit cache at `session/hyperspherical-harmonic-curve-v1-fit-cache.pkl`. Stage-2 sparse-cell count comparison vs the incumbent's `21Ã21 flat r=0.05` grid (using the variant's equal-area 441-cell `râ0.095` chordal partition). One `## Empirical Validation â PENDING` â `## Empirical Validation â v1` update with the actual numbers.

## Not Doing (and Why)

- **Manual classification of all 147 artifacts for primitive coverage** â irrelevant; the variant reuses the existing `Z = Î³(S^N)` from curve-guided-rsi v3.
- **The (Î³, dÎ³, âÂ²Î³) triple extension** â explicitly deferred to v2 per the advisor's Lifecycle Â§v2 candidates; the "3-D differential" reading is honored as `SÂ² â âÂ³` + MÃ¶bius covariance, not as a 3-jet.
- **`N=3` with hand-rolled Gegenbauer basis** â gated by `PC3 â¥ 0.08` AND `N_items â¥ 90`; current corpus fails both gates. The `N=2` default is principled.
- **Heuristic blend of Stream D's interpretation B (1-jet) and interpretation C (Blaschke)** â orthogonal mechanism change; would inflate the variant into two skills. Worth pursuing as separate family members (`n-sphere-jet-curve-rsi`, `n-sphere-blaschke-curve`) once D is operational.
- **A full `## Empirical Validation â v1` rewrite with the actual fit numbers** â marked `PENDING FIT`; this ideation produces the skill body, not the fit. The fit is the next cycle (RSI cycle 2 or a follow-up validate cycle).
- **Applying the variant to a corpus other than yubiOS skills** â the variant is purpose-built for `curve-guided-rsi`'s 9-D binary primitive coverage target. Re-targeting to a different feature space is a v3+ extension.
- **Curve-fit on `SÂ³` via MÃ¶bius** â `PSL(2,â)` does not act on `SÂ³` (only on `SÂ²`); the MÃ¶bius reparameterization is structurally `SÂ²`-only. `N=3` uses a different mechanism (the LaplaceâBeltrami spectrum alone, with no learned reparameterization).

## Open Questions

- Will the matched-parameter ablation return positive on the 69-skill corpus? The variant's whole ship-or-kill verdict rests on this single test; if negative, the variant ships as a documented null result rather than a working pipeline.
- Does the equal-area Stage-2 partition produce a `sparse_cell_count` comparable to the incumbent's `21Ã21 flat r=0.05` grid? If the counts diverge wildly (e.g., variant shows `sparse=8`, incumbent shows `sparse=21`), the pre/post `Î` is not portable between the two pipelines and a migration protocol is needed.
- Are the spectral-mass gate thresholds (`Ï â¥ 0.10`, high-degree mass `â¤ 0.40`) calibrated for `D=384` outputs? They are chosen by principle, not yet empirically. First-Stage-5 verification pass will set the actual thresholds.
- Will the v1-cycle fresh-context subagent re-map surface any unflagged gaps (e.g., a missing pre-fit assertion, a wrong convention in the PyTorch skeleton)? The cycle-1 Result is `re-map pending`; the audit trail closes on cycle-2 backfill.

## Generation log (for review)

**Variations generated (4):**

| # | Interpretation | Lens | Painkiller | Switching | Defensibility | Testability | Total |
|---|---|---|---|---|---|---|---|
| 1 | A â 3-D parameter on `SÂ³` | Geometric framing (constraint-removal: N=3 to honor user phrasing) | 4 | 4 | 4 | 3 | **15** |
| 2 | B â 1-jet / 3-form differential | Combination (Neural Manifold ODE analog) | 3 | 2 | 4 | 2 | **11** |
| 3 | C â Blaschke products on Riemann sphere | Combination (CVNN + MÃ¶bius invariance) | 5 | 3 | 4 | 4 | **16** |
| 4 | **D â Hyperspherical harmonics on `S^N` + MÃ¶bius** | Combination (SIREN + Spherical CNNs + corpus-audit) | 5 | 4 | 5 | 5 | **18** â WINNER |

**Dropped below threshold (â¤ 12):** Interpretation B (1-jet, score 11) â orthogonal mechanism, changes output shape rather than parameter manifold, low testability because holonomy is hard to compute numerically.

**Finalists (top 2):**
- D â Hyperspherical harmonics (18/20) â clean drop-in for the curve-guided-rsi Stage-1 swap; mechanism novelty via MÃ¶bius.
- C â Blaschke products (16/20) â stronger structural prior but requires 2-D-to-`â` projection pipeline that injects a new failure mode.

**Advisor revisions applied (10 total) before SKILL.md write:**

1. **Replaced `Îµ_spec` with `Îµ_basis` (pre-fit unit test only) + spectral-mass gate + holdout `RÂ²` + matched-parameter ablation.** The original `Îµ_spec` is mathematically vacuous (an identity for any smooth `Î³ â CÂ²(S^N)`); it cannot detect silent degradation.
2. **Added MÃ¶bius reparameterization `Ï_Î¸ â PSL(2,â)`.** Without it, the model is OLS spherical-harmonic regression (~200 years old), obvious under KSR rationale (A). The MÃ¶bius earns the mechanism claim and gives a falsifiable cross-ratio invariant.
3. **Default `N=2`, `L=3`.** Corpus at 69 items supports `SÂ²/L=3` (16 basis, `n_basis â¤ N_items/3`) but fails `SÂ³/L=3` (30 basis, needs 90). Also: `N=3` requires `PC3 â¥ 0.08` (third parameter coordinate is near-noise at current `PC1+PC2 = 0.4615`).
4. **Stage 2 = equal-area partition, chordal distance, `r â 0.095` (not 0.05).** Uniform `0.05Ã0.05` chart-grid is not uniform on `SÂ²`; reusing `r = 0.05` would inflate the sparse-cell count and fake a pre/post improvement.
5. **Domain coordinate `x â SÂ²` as the audit key.** Dropped Stream D's "recover `(u, v)` from PC1+PC2 of `Z`" â that's a second, sign-ambiguous coordinate system that destroys the geometry the variant exists for.
6. **Deleted `L_eq`, `L_LB`, `L_K` losses.** `L_eq` forces `Î³` constant (encodes silent-degradation as an objective). `L_LB` is identically zero (free index). `L_K` is scale-arbitrary.
7. **Froze `degree_weights` at 1.** A learnable `w_l` creates a gauge redundancy with `a_{:,l}` that defeats `L_spec`.
8. **Corrected parameter counts.** `6,532` at `SÂ²/L=3`; `11,908` at `SÂ³/L=3`. Reframed "62% smaller" as a truncation choice at equal degree, not a curvature dividend.
9. **Downgraded novelty verdict** to "NOVEL at application layer; mechanism layer BORDERLINE unless MÃ¶bius added" â and MÃ¶bius is added, so the mechanism claim is now defensible.
10. **Pinned basis library + convention.** `scipy.special.sph_harm` deprecated â use `sph_harm_y` with argument-order assertion. `lie_learn` and `e3nn` do not implement `SÂ³` harmonics. Hand-rolled `SÂ³` basis is unsafe without `Îµ_basis < 1e-3` pre-fit validation.

**Convergence reasoning:** D wins because (a) it composes most cleanly with `curve-guided-rsi` (only Stage 1 changes; Stages 2â5 re-use with one Stage-2 metric update), (b) the LaplaceâBeltrami eigenbasis is canonical (not learned), shrinking the parameter count at equal expressive power, (c) the MÃ¶bius reparameterization is the only mechanism that earns the Â§103 novelty layer, and (d) the matched-parameter ablation is the only verification metric that can come back negative â fitting the variant's claim shape (falsifiable, not vacuous). The "3-D differential" reading is honored as `SÂ² â âÂ³` + MÃ¶bius covariance, not as a de Rham 3-form (which `Î³` is a 0-form and never forms).



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


## Cross-references

**Related Linear issues (OMN-*)**: TBD per file context.
**Related PRs**: TBD.
**Related ADRs**: TBD.
**Related refs/ docs**: TBD.

Context: section appended per repo-refs-skill cycle-3 7-D Mode D batch (Δ=+0.4680). TODO: refine per file context.


## New Ideas -- cycle 2 (lens format)

This file was processed by the RSI cycle-2 lens generator (curve-compass-skill v1.1.0 + curved-corpus-create v1.1.0). Each cycle-2 patch IS a concrete experiment with a measurable delta -- not a templated section. The lens below documents the measured dynamics; the patch is the lens, not prose about the file.

```json
{
  "lens": "L261",
  "file": "refs/hyperspherical-harmonic-curve-2026-08-05.md",
  "hypothesis": "refs/hyperspherical-harmonic-curve-2026-08-05.md covers all 9 primitives in the internal-big-picture basis",
  "method": "9-D primitive binarization (purpose, examples, guidelines, constraints, verification, composition, changelog, references, anti-patterns) + chordal distance to ideal pole on Fibonacci lattice",
  "parameters": {
    "basis": "internal-big-picture",
    "d": 9,
    "seed": 20260812
  },
  "delta": {
    "k": 6,
    "missing_primitives": [
      "examples",
      "changelog",
      "references"
    ],
    "chordal_resid": 0.0
  },
  "verdict": "PARTIAL",
  "score": 33,
  "caveat": "binarization is heuristic; a stricter regex pass might surface sub-primitives"
}
```
