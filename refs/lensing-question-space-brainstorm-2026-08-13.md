# Lensing the Question Space: Academic Anchors and Gap Map
**Brainstorm, 2026-08-13.** Connects `is-this-x-2026-08-12` + `learned-latent-curves-2026-08-06` to established proofs, then names the gaps in the chain: question space (is-this-x) → intent space → null space → latent space (0 → N dims), with the goal of focusing a feature space the way Snell's law focuses light.

---

## 1. The dictionary: what in the papers already has a theorem behind it

| Paper construct | Established result | Status of the bridge |
|---|---|---|
| Möbius chart φθ ∈ PSL(2,ℂ) (Eq. 7, llc paper §3.2) | **Leonhardt, "Optical Conformal Mapping," Science 312:1777 (2006)**: an analytic map w(z) induces refractive index n(z) = \|w′(z)\|; straight rays in virtual space map to designed curved rays in physical space. Schmiele et al., PRA 81:033837 (2010) build flat lenses from exactly this. | **Exact, not metaphor.** The paper's φθ IS a 2-D conformal lens on the Riemann sphere. Frozen-at-identity = an unpowered lens (n ≡ 1). Refining φθ = lens design, with the "index profile" \|φθ′\| as the design variable. |
| Snell's law / focusing | **Fermat's principle**: rays are geodesics of the conformally flat metric g = n(x)²δ; the eikonal \|∇S\|² = n² has rays as characteristics; Snell's law is the corner condition at an index discontinuity (Kalaba & Ueno 1974; Tyc 1997; Leonhardt 2020 arXiv:2002.04390). | Exact once a metric is named. The missing piece on our side is *which* n(x): see Gap A. |
| Geodesic-only atom criterion (Lemma 1) | Fermat's principle in discrete form: each dispatch takes the flip that minimizes geodesic distance to the pole. | The atom is already a **ray tracer**. Δ ≥ 0 = rays never travel backward in optical path length. The Φ(k) ladder is the eikonal S evaluated on coverage shells. |
| The matched null as origin of Φ | **Gravitational lensing formalism**: deflection is only defined relative to the unlensed background. Also **Marchenko–Pastur (1967)** as the flat vacuum, and **Lyu & Mukherjee 2024 (arXiv:2407.14942)**: fixed-margin random matrices converge to a tilted iid ensemble with a variance profile, recovering MP at constant margins. | Strong. The paper's finding that 98% of V₂ is marginal-fixed has a rigorous reading: the curveball ensemble IS the "medium," and Lyu–Mukherjee gives its spectrum analytically. The +0.0144 residual is the deflection angle. The paper already checks MP lands on the destroyed-dependence nulls (0.2414 vs 0.2397/0.2398): that is the vacuum calibration. |
| V₂(D) dimension ladder (Prop. 1, Table 1) | **Participation ratio / stable rank / intrinsic dimension**: srank(A) = ‖A‖²_F/‖A‖², intdim(M) = tr M/‖M‖ (Tropp); scale-dependent dimensionality (Dahmen et al. 2022); **Zhang's effective dimension** D_λ = tr((T+λI)⁻¹T) controls kernel generalization; **Johnson–Lindenstrauss**: k = O(ε⁻² log n) dims preserve all pairwise distances. | Prop. 1 is a special case of known spectral-share behavior. JL gives the 0 → N direction a floor: the number of dimensions a corpus *needs* is log(rows), not the nominal D. Zhang's λ is a genuine **focal-length knob**: sweeping λ sweeps the effective dimension continuously, which is what "0 leading to N dimensions" should mean formally. |
| Family standardization z_{f,c}, exclusion verdicts | **Fisher–Rao information geometry**: Rao 1945; **Čencov's theorem**: the Fisher metric is the unique metric invariant under sufficient statistics (up to scale); Efron 1975 connects statistical curvature to information loss. | Partially built. Per-family z-scores are a diagonal approximation of Fisher–Rao distance to the family manifold. Upgrading max\|z\| > 3 to geodesic distance in the Fisher metric is well-posed. |
| Intent space (undefined in the papers) | **Simulation-based inference for lensing** (NPE with embedding networks, e.g. arXiv:2501.08524, ApJ 2023): a learned compression of high-dim observations into summary statistics sufficient for the posterior. Also the **information bottleneck** and classical sufficiency. | Direct prior art. In lensing cosmology the "intent space" already exists and has a name: the learned summary-statistic embedding between raw image (question space) and physical parameters (latent space). Čencov says the geometry that survives that compression is exactly Fisher. |
| Fold-aggregated detection (Empirical Result 2) | **Aperture synthesis / coherent integration**: single dim rays are below the detection floor; a constant-ratio family integrates the trend into one high-SNR test (t_fold = 45.19 where per-cell power = 0.067). | Analogy, but a productive one: the fold is a lens for *families* where no per-cell lens exists. Pairing (shared seed) = phase-coherent integration; its 2.4× variance cut is the coherence gain. |
| Boltzmann compass π_T(k) ∝ C(9,k)e^(−Φ(k)/T) | Standard MCMC / detailed-balance theory. | Already exact in the paper. T is the "aperture temperature": T → 0 collapses the ensemble to the absorbing point (over-focus), T → ∞ defocuses to pure entropy. T_× = 0.0411 is the focus crossover. |

## 2. The lensing chain, made formal

The requested chain: **question space → (lens) → intent space → null space → latent space (0..N dims)**. Candidate formalization, each arrow with the theorem that supports it:

1. **Question space Q** = the is-this-x triple (Φ, M, V). A "question" is a corpus + a family. Rays are corpora; sources are families.
2. **Null space N₀** = the matched-marginal ensemble, treated as the *vacuum metric*. Standardization (Eq. 13/43) is the statistical equivalence principle: at any point you can choose coordinates (z-scores against the local null) in which the medium looks flat. Lyu–Mukherjee supplies the vacuum's exact spectrum; MP is its constant-margin limit. What survives standardization (ΔV₂z, the Hodge directional statements, Parseval shares vs null) is *curvature*, i.e. what cannot be transformed away. This is exactly how GR/lensing separates coordinate effects from physical deflection.
3. **Intent space I** = the sufficient-statistic quotient of Q. Two constructions on the table:
   - *Learned*: an embedding network trained so the null-standardized verdicts are recoverable (the NPE pattern from lensing SBI, amortized: train once, place any corpus in seconds).
   - *Axiomatic*: the quotient by sufficiency, whose unique invariant geometry is Fisher–Rao (Čencov). This is the principled definition: intent = what any sufficient compression must preserve.
4. **Latent space, 0 → N dimensions** = the one-parameter family of effective dimensions D_λ = tr((T+λI)⁻¹T), λ ∈ (∞, 0], which runs continuously from 0 (λ→∞) to numerical rank (λ→0). The paper's discrete ladder (2, 3, 7, 9, 16, 24, 384) becomes a smooth dial. Prop. 1 and the fitted null laws (Eq. 18) are the medium's **dispersion relation**: how the vacuum V₂ varies with dimension. Dimension plays the role of wavelength.
5. **The lens** = φθ ∈ PSL(2,ℂ) with index profile \|φθ′\|, per Leonhardt. Focusing a feature space = choosing φθ (and λ) so that the corpus family of interest converges to a designed region of S² while the null stays flat. Snell's law appears at *basis interfaces*: crossing from one feature basis to another (9-D → 16-D → 384-D) refracts the signal with the ratio set by the two null means (Gap D makes this testable).

## 3. Reframes the optics language buys immediately

- **The V₂ = 1.0000 gate passes are caustics.** In optics a caustic is where the ray map degenerates: intensity diverges, imaging fails, and the image carries no information about the source. The paper's rank-2 degeneracies (2-D PCA, the ℓ=384/m=3 variant, all 14 rows at exactly 1.0000 including pure noise) are exactly this: over-focusing that destroys data content. The paper's red-flag rule ("exact 1.0000 → report rank and condition number") is the caustic detector. This gives Prop. 2 a geometric identity, and it inherits real theory: caustic classification (fold, cusp) is Thom/Arnold catastrophe theory, and the singularities of optimal transport maps are its measure-theoretic cousins.
- **Achromatic coordinates.** An achromatic lens focuses all wavelengths alike; a dimension-comparable coordinate is one whose value does not move along the D-ladder. The paper already found them: the Parseval shares E_ℓm (Eq. 40: same 16 entries whatever N and d; scale-free along a fold). So the design rule "no coordinate without a non-degenerate null" gets a twin: **prefer achromatic coordinates** (invariant along the dispersion relation) for anything meant to compare corpora across dimension.
- **The retraction discipline is dark-field microscopy.** Blocking the direct beam (subtracting the null) so only scattered light (the residual) is visible. 98% of the beam is unscattered; the +0.0144 is the scatter.

## 4. Gap map (what has no theorem yet, and the cheapest experiment for each)

**Gap A — Which refractive index?** Fermat needs an n(x). Candidates: (i) √det I(θ) from the Fisher metric (Čencov-canonical, invariant); (ii) the local null SD of the statistic (the medium is "denser" where the null fluctuates less, so a fixed signal bends more); (iii) \|φθ′\| directly (design choice, not measurement). These disagree and the disagreement is the content. *Experiment*: on the standard-candle grid, compute all three at each (N, d, s) cell and test which one predicts the measured detection-power surface as an eikonal. Cheap: the grid is already in `results/signal_recovery.json`.

**Gap B — Snell's law at a basis interface.** Claim to test: crossing bases, the null-standardized signal obeys n₁ sin θ₁ = n₂ sin θ₂ with n_D determined by the null (e.g. n_D ∝ 1/SD₀[V₂](D)). The ladder data (Table 1 + per-D nulls) can falsify a specific conservation law in an afternoon. If no invariant survives basis changes, that is itself a result: the medium is dispersive with no achromatic pair beyond Parseval shares.

**Gap C — Intent space needs its non-degenerate null.** By the paper's own membership rule, "intent space" is inadmissible until it has a construction under which it could have been different. Proposal: define I as the minimal embedding (learned, NPE-style) that preserves all family verdicts on the reference set; its null is the same embedding trained on curveball draws. If the null-trained embedding recovers the same verdicts, intent space is vacuous; if not, its dimension is measurable. This makes "intent" falsifiable instead of decorative.

**Gap D — Actually power the lens.** Every run so far freezes φθ at identity. Leonhardt's prescription says what refinement means: pick a target region on S² for a named family and solve for the conformal map that sends that family's arc there while the curveball ensemble's image stays diffuse. The objective is new: maximize *null-standardized* concentration, not raw fit (raw-fit optimization would just manufacture a caustic; the null constraint is the anti-caustic guard). This is the concrete "focus any feature space" deliverable, and it stays inside PSL(2,ℂ), 6 real parameters, L-BFGS-B as already spec'd in llc §3.2.
  - Anti-caustic constraint, explicitly: reject any φθ whose design rank drops or whose condition number blows up (Prop. 2's red flag becomes an optimization constraint).

**Gap E — Caustic classification.** If B and D work, the degeneracies should classify: which of the 14 exact-1.0000 rows are fold caustics (recoverable by a small perturbation of basis) vs structural rank collapse (2-D PCA, unrecoverable)? Perturb each degenerate basis by one column and measure whether V₂ leaves 1.0000 continuously or discontinuously. Catastrophe-theoretic normal forms predict which.

**Gap F — Wasserstein channel (speculative, flag as such).** Benamou–Brenier gives a genuine least-action geodesic between corpus distributions, and Brenier-map singularities are the transport analog of caustics. There is *no* general theorem that data exhibits optical caustics (deepresearch was blunt about this), so this channel enters only with a model-specific hypothesis and its own null. Candidate: W₂ geodesic between a corpus's row distribution and its curveball null's, with column-shuffle as the second null. Do not admit it to the map before it passes the membership condition.

## 5. Honesty constraints carried over from the paper

- Every optical coordinate proposed above must clear the same bar as Section 6.5: a demonstrated non-degenerate null. "Refractive index," "focus," and "caustic" are banned from the map until then; they live in this brainstorm, not in results.
- The z over-dispersion (sd 1.320 at s=0) applies to any new statistic built from ΔV₂z; lens-design objectives must use the empirical null quantile, never Gaussian tails (the fold-ladder already set this precedent).
- Snell's-law language is only exact where a metric and variational problem are both specified (deepresearch synthesis). The one place both already exist in the corpus is the atom (metric: chordal on S²; variational problem: geodesic-only argmin). Build outward from there.

## 6. Suggested order of attack

1. Gap B (Snell invariant on existing ladder data): zero new data collection, pure re-analysis.
2. Gap D (power the lens with the null-constrained φθ objective): the flagship, produces the "focusing tool."
3. Gap A (which index predicts the power surface): decides the theory underneath D.
4. Gap C (intent-space null): makes the chain's middle term admissible.
5. Gap E, then F, in that order, each behind its own null.

## Sources (load-bearing)
- Leonhardt, Optical Conformal Mapping, Science 312:1777 (2006); arXiv:physics/0602092
- Schmiele et al., PRA 81:033837 (2010)
- Kalaba & Ueno, JOSA 64:317 (1974); Tyc, JOSA A 14:2850 (1997); Leonhardt arXiv:2002.04390
- Rao (1945); Čencov uniqueness; Bauer–Bruveris–Michor (Fisher–Rao uniqueness); Efron, Ann. Stat. 3:1189 (1975)
- Marchenko & Pastur (1967); Lyu & Mukherjee arXiv:2407.14942 (fixed-margin → variance-profile MP)
- Dasgupta & Gupta, JL proof (2003); Zhang, effective dimension (NeurIPS 2002 / NC 2005); Tropp, stable rank notes
- Benamou–Brenier via Ambrosio–Gigli–Savaré; Gangbo & McCann
- Lensing SBI / NPE embedding networks: arXiv:2501.08524, ApJ 941 (2023), arXiv:2309.16063
