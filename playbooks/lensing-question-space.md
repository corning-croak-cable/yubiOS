# Lensing the Question Space + Spherical Diffusion (SLERP extension)
**2026-08-13.** Consolidates [lensing-question-space-brainstorm-2026-08-13.md](lensing-question-space-brainstorm-2026-08-13.md) and extends it: geodesic (SLERP-style) interpolation on the hypersphere as the generator of a diffusion process, tying the whole chain together. Source works: `is-this-x-2026-08-12-Final` and `learned-latent-curves-2026-08-06`.

---

## PART I — Lensing findings (consolidated)

### F1. The Möbius chart is already a lens (exact, not metaphor)
φθ ∈ PSL(2,ℂ) with index profile n(z) = |φθ′(z)| is Leonhardt's optical conformal mapping (Science 312:1777, 2006; lens designs: Schmiele et al., PRA 81:033837, 2010). Every run to date freezes φθ at identity: the framework has been carrying an **unpowered lens**. Refining φθ = lens design in the literal optical sense.

### F2. The atom is a ray tracer (exact)
The geodesic-only criterion is discrete Fermat's principle; the Φ(k) ladder is the eikonal S on coverage shells; Δ ≥ 0 = rays never move backward in optical path length. Snell's law is the corner condition of the same variational problem at an index discontinuity (Kalaba & Ueno 1974; Tyc 1997).

### F3. The null is the vacuum; the residual is the deflection (rigorous backing)
Null standardization = measuring deflection against the unlensed background, as in gravitational lensing. Lyu & Mukherjee (arXiv:2407.14942) prove fixed-margin random matrices converge to a tilted-iid ensemble with a variance profile (MP at constant margins), giving the curveball "medium" an analytic spectrum. The paper's 98%-marginal result is that medium; ΔV₂ = +0.0144 at z = +12.3 is the deflection angle. Standardization is a statistical equivalence principle: locally, coordinates always exist in which the medium is flat; what survives (ΔV₂z, directional Hodge statements, Parseval shares vs null) is curvature.

### F4. The exact-1.0000 gate passes are caustics
Rank-2 degeneracy = the ray map degenerating = over-focus that destroys information (all 14 machine-precision 1.0000 rows, pure noise included). Prop. 2's red flag is a caustic detector; classification is Thom/Arnold catastrophe theory; the transport analog is Brenier-map singularities.

### F5. Achromatic coordinates exist and are already in the paper
Parseval shares E_ℓm (same 16 entries at any N, d; scale-free along a fold) are dimension-invariant: the achromatic lens. Design rule twin to the membership condition: prefer achromatic coordinates for anything compared across the D-ladder.

### F6. The chain, formalized
- **Question space Q** = the is-this-x triple (Φ, M, V); corpora are rays, families are sources.
- **Null space N₀** = matched-null ensemble = vacuum metric (origin of the map).
- **Intent space I** = the sufficient-statistic quotient; by Čencov's theorem its unique invariant geometry is Fisher–Rao. Constructive version: NPE-style embedding networks from lensing cosmology (learned summary statistics between raw observation and physical parameters) are the direct prior art.
- **Latent space 0 → N dims** = Zhang's effective dimension D_λ = tr((T+λI)⁻¹T): a continuous dial from 0 (λ→∞) to numerical rank (λ→0). The discrete basis ladder becomes a dispersion relation; dimension plays wavelength. JL (k = O(ε⁻² log n)) floors how many dimensions a corpus needs.

### F7. Gap map from Part I
- **A** — which refractive index: √det(Fisher), 1/SD₀[statistic], or |φθ′|; test which predicts the measured power surface on the standard-candle grid (data already in `results/signal_recovery.json`).
- **B** — Snell invariant at basis interfaces: test n_D sin θ_D conservation across the ladder with n_D from the per-D nulls; pure re-analysis of `ladder_VD.json`.
- **C** — intent space must pass the membership condition: define I as the minimal embedding preserving all family verdicts; its null is the same embedding trained on curveball draws.
- **D** — power the lens: optimize φθ to concentrate a target family while the null image stays diffuse (null-standardized objective, never raw fit); anti-caustic constraint = design rank + condition number.
- **E** — caustic classification: perturb each degenerate basis by one column; fold vs structural collapse.
- **F** — Wasserstein channel (speculative): Benamou–Brenier geodesics between corpus and null row-distributions; admit only behind its own null.

---

## PART II — Interpolation on the hypersphere → diffusion (the SLERP extension)

### F8. SLERP is the geodesic interpolant the framework already implies
Shoemake's slerp (SIGGRAPH 1985):
slerp(p, q; t) = [sin((1−t)Ω) p + sin(tΩ) q] / sin Ω, with cos Ω = p·q.
It is the constant-speed geodesic on S^n. Three objects in the papers are secretly discrete slerps:
- the atom's flip sequence (a geodesic walk toward the ideal pole, one quantum at a time);
- the fold ladder (constant-ratio steps along a 1-parameter family);
- the drift-alignment of curves across corpora (llc §E.4).
The continuous upgrade: **slerp(p_file, p*; t)** replaces the k-quantized ladder with a continuous bloom parameter t ∈ [0,1]. The precedent for why geodesic (not linear) interpolation is the right move in high dimension is White 2016, "Sampling Generative Networks": Gaussian latents concentrate on the shell of radius √n, so lerp leaves the data manifold while slerp stays on it. Concentration of measure makes every high-dim latent space effectively a hypersphere, which is why this generalizes beyond S².

### F9. The paper's basis diagonalizes diffusion (the structural gift)
The real spherical harmonics are the eigenfunctions of the Laplace–Beltrami operator: ΔY_ℓm = −ℓ(ℓ+1)Y_ℓm. The heat kernel on S² is
K_t(x·y) = Σ_ℓ (2ℓ+1)/(4π) · e^{−ℓ(ℓ+1)t} · P_ℓ(x·y).
Consequences, all free because the framework already computes in this basis:
1. **Diffusion is diagonal in the Parseval coordinates.** Under heat flow, each per-mode energy decays deterministically: E_ℓ(t) = E_ℓ(0)·e^{−2ℓ(ℓ+1)t} (before renormalization). Diffusing a corpus is a *closed-form operation on the already-measured spectrum*: no simulation needed.
2. **A diffusion-time estimator falls out.** Fit t̂ from the measured per-degree decay of E_ℓ against a reference: one scalar that says "how defocused is this corpus." Dimension-comparable by construction (F5).
3. **The null space is the t → ∞ endpoint of diffusion.** Brownian motion on a compact manifold converges to the uniform measure. So "lensing the question space to the null space" acquires an exact dynamical meaning: **forward diffusion is the map Q → N₀**, run continuously. The is-this-x program measured the two endpoints; the heat flow supplies every intermediate frame.

### F10. Reverse diffusion is the lens run backward (established, 2022–2023)
- De Bortoli, Mathieu, Hutchinson, Thornton, Teh, Doucet, **"Riemannian Score-Based Generative Modelling"** (NeurIPS 2022): forward Brownian motion on compact manifolds (sphere as the worked case), reverse SDE guided by the learned score.
- Huang, Aghajohari, Bose, Panangaden, Courville, **"Riemannian Diffusion Models"** (NeurIPS 2022): Stratonovich SDE formulation, Riemannian ELBO = Riemannian score matching.
- **"Scaling Riemannian Diffusion Models"** (NeurIPS 2023): exact heat-kernel computations on symmetric spaces (spheres, tori, Lie groups) — S² and S^n are the *easy* case with the closed-form kernel of F9.
Reading in the lensing dictionary: the forward process defocuses (corpus → uniform null), the learned score s(x,t) = ∇log p_t(x) is the **refractive-index gradient**, and the reverse SDE is a lens that focuses the uniform measure back into the corpus distribution. This is the general (non-conformal) lens; φθ (F1) is its 6-parameter interpretable subfamily.

### F11. The compass atom is the zero-temperature discretization of a sphere Langevin
Riemannian Langevin on S²: dX = −∇_g Φ(X) dt + √(2T) dB_{S²}, stationary density ∝ e^{−Φ(x)/T}. This extends the curve-compass ± atom from the 10-state k-shell chain to the full sphere:
- the compass's π_T(k) ∝ C(9,k)e^{−Φ(k)/T} is the k-shell marginal of the sphere Langevin with an exchangeable potential;
- T → 0 recovers greedy geodesic descent = the atom = the historical absorbing log (matching the paper's T→0 verification exactly);
- one Euler–Maruyama step on the sphere is literally "slerp toward the pole + tangential noise": **slerp is the deterministic half of the diffusion step**. That is the precise sense in which "interpolation on the hypersphere creates diffusion."
- The natural stationary families are von Mises–Fisher, ∝ e^{κ μ·x}: the sphere's Gaussians. κ is the concentration (focus) knob, κ ~ 1/T. The two-population mixture family M₄ becomes a 2-component vMF mixture on S², which finally gives yubiOS's nearest family a *generative* spherical form.

### F12. What this buys the is-this-x map
1. **A scale-space channel.** Diffuse corpus AND its matched null with the same t; a signal is *diffusion-stable at scale t* if its null-standardized z survives. This is Gaussian scale-space (vision) transplanted to the question space, and it gives every coordinate a persistence profile z(t) instead of a single number: features that die at small t are texture, features that survive are structure. (Analogy discipline: each z(t) inherits the same over-dispersion caveat; use empirical null quantiles.)
2. **Standard-candle generator v2.** Train an RSGM on the Fibonacci-lattice corpus points: a generative sampler whose reverse trajectories synthesize corpora *between* the null and the data. Reference families become checkpoints along diffusion time rather than hand-built generators; "widen the grid" becomes "sample more of the bridge."
3. **The SLERP fold.** Replace the amplitude ladder s = 0.25...2 with geodesic rungs slerp(p₀, p*; t_k), t_k a constant-ratio grid. Same fold-slope statistic, same empirical null-ladder quantile, but the rungs are now intrinsic to the sphere (no log-odds units), so the fold becomes basis-independent and composes with F5's achromatic coordinates.
4. **Unification with transport (closes Part I Gap F properly).** The Schrödinger bridge between the null measure and the corpus measure interpolates between entropic diffusion (T > 0) and Benamou–Brenier optimal transport (T → 0). Diffusion and the Wasserstein channel are one family with T as the knob, the same T the compass already swept: T_× = 0.0411 was measured on the k-marginal; the sphere version has its own crossover to find.

### F13. New gaps (Part II), each with the cheapest test
- **G1 — closed-form defocus, verify against simulation.** Apply e^{−ℓ(ℓ+1)t} decay to the measured Parseval shares of the 2286×9 corpus and confirm against explicit Brownian simulation on the Fibonacci lattice. One script; the spectrum is already in `results/real-gwtc-results.json` shape.
- **G2 — diffusion-time null.** t̂ needs its own non-degenerate null (membership condition): compute t̂ on curveball draws; if the null's t̂ distribution is degenerate, the coordinate is inadmissible.
- **G3 — scale-space sweep.** z(t) profiles for ΔV₂z and E_{3,3} on yubiOS and GWTC at 5–10 log-spaced t. Prediction worth pre-registering: the m=3 starvation effect (below-null shares) should *invert or die* at moderate t, since diffusion scrambles the PC1-ordering mechanism that causes it.
- **G4 — sphere Langevin vs compass.** Run the S² Langevin with Φ = chordal distance to pole at the compass's T grid; verify the k-shell marginal reproduces π_T(k) and locate the sphere-native crossover. Extends the compass's 8/8 selftest to the continuum.
- **G5 — RSGM feasibility.** N = 2286 points on S² is tiny by RSGM standards; the exact S² heat kernel removes the usual approximation pain (NeurIPS 2023 result). Risk: the corpus is 176 distinct rows, so the point cloud is heavily atomic; may need kernel-smoothed targets first (vMF bandwidth = another t).
- **G6 — caustics of the reverse flow.** Where the learned score focuses mass onto lower-dimensional sets, the reverse flow develops the same rank-collapse signature as F4. The anti-caustic guard (rank + condition number) should be monitored *along diffusion time*, not just at endpoints.

---

## Order of attack (merged)
1. **G1** (closed-form defocus check): hours, pure verification, unlocks everything in Part II.
2. **B** (Snell invariant on the ladder): re-analysis only.
3. **G3** (scale-space sweep with matched nulls): first new science; the m=3 inversion prediction is falsifiable.
4. **D** (power the Möbius lens, null-constrained objective): flagship of Part I.
5. **G4** (Langevin ↔ compass continuum check): extends an already-green selftest.
6. **A, C, G2** (theory choices + admissibility nulls).
7. **G5, E, G6, F** (generative model, caustic classification, bridge unification).

## Honesty constraints (carried over, apply to Part II too)
- No coordinate enters the map without a demonstrated non-degenerate null (t̂ included).
- Empirical null quantiles, never Gaussian tails, for any statistic built from over-dispersed z.
- "Diffusion," "lens," "focus" stay in this document until the corresponding construction passes the membership condition; the compass set the precedent for how to do this cleanly (designed dynamics, wall between corpus facts and design facts).
- T is a knob of designed dynamics, not an observable of the corpus (paper's own rule; applies verbatim to diffusion time t).

## Load-bearing sources
Part I: Leonhardt Science 312:1777 (2006); Schmiele et al. PRA 81:033837 (2010); Kalaba & Ueno JOSA 64:317 (1974); Tyc JOSA A 14:2850 (1997); Rao (1945); Čencov uniqueness; Efron Ann. Stat. 3:1189 (1975); Marchenko–Pastur (1967); Lyu & Mukherjee arXiv:2407.14942; Dasgupta & Gupta JL (2003); Zhang effective dimension (NeurIPS 2002 / NC 2005); Ambrosio–Gigli–Savaré OT; lensing SBI: arXiv:2501.08524, arXiv:2309.16063.
Part II: Shoemake, SIGGRAPH 1985 (slerp); White, arXiv:1609.04468 (spherical latent interpolation); De Bortoli et al., Riemannian Score-Based Generative Modelling, NeurIPS 2022; Huang et al., Riemannian Diffusion Models, NeurIPS 2022; Scaling Riemannian Diffusion Models, NeurIPS 2023 (exact heat kernels on symmetric spaces); standard S² heat kernel via Legendre expansion; von Mises–Fisher family; Schrödinger bridge ↔ entropic OT (Léonard survey; De Bortoli et al. Diffusion Schrödinger Bridge, NeurIPS 2021).
