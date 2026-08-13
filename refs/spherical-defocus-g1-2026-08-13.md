# Spherical Defocus (G1): the heat semigroup on the question space
**refs draft, 2026-08-13.** Executed experiment G1 from `session/FINDINGS.1.md`. Companion to `papers/is-this-x-2026-08-12-Final` and `papers/learned-latent-curves-2026-08-06`. Seed 20260813, numpy only. Script: `session/g1/g1_defocus.py`; record: `session/g1/g1-results.json`; input: `data/real/per_row_coverage_v3.json` from the shipped is-this-x evidence bundle (2286×9, column sums verified against Appendix A).

## Claim under test
The 16 real spherical harmonics of L=3 are eigenfunctions of the Laplace–Beltrami operator on S² (ΔY_ℓm = −ℓ(ℓ+1)Y_ℓm), so Brownian motion on the sphere acts diagonally on the paper's own basis:

  E[Y_ℓm(B_t^x)] = e^{−ℓ(ℓ+1)t} · Y_ℓm(x)      (semigroup identity)

and the Parseval per-degree energies of a fitted field should decay as e^{−2ℓ(ℓ+1)t} **when the design stays quasi-uniform**. "Diffusion toward the null" would then be a closed-form operation on the already-measured spectrum. Convention: dX = √2 dB_tangent so the generator is Δ (not Δ/2) and the kernel is e^{tΔ}.

## Leg 1 — semigroup identity: VERIFIED
Fibonacci lattice N = 2048, Euler–Maruyama tangent steps, 48 replicates, pooled per-degree regression of E[Y(X_t)] on Y(X_0):

| t | ℓ=1 meas/pred | ℓ=2 meas/pred | ℓ=3 meas/pred |
|---|---|---|---|
| 0.01 | 0.98024 / 0.98020 | 0.94187 / 0.94176 | 0.88712 / 0.88692 |
| 0.05 | 0.90522 / 0.90484 | 0.74160 / 0.74082 | 0.54962 / 0.54881 |
| 0.10 | 0.82118 / 0.81873 | 0.55367 / 0.54881 | 0.30642 / 0.30119 |
| 0.20 | 0.67374 / 0.67032 | 0.30578 / 0.30119 | 0.09324 / 0.09072 |

Ratio measured/predicted ∈ [1.000, 1.028]; the residual bias grows with t·ℓ(ℓ+1) exactly as first-order Euler discretization predicts. The identity holds on the lattice the generator samples on. This is the mathematical core of the diffusion channel and it is now empirically pinned, not just cited.

## Leg 2 — real 2286×9 corpus: closed form does NOT govern, and the deviation is the finding
Pipeline reproduced per the paper (z-score → PCA top-2 → RMS rescale → stereographic lift → ridge on 16 real SH, λ=10⁻³). Per-degree energy shares at t=0: E₀..E₃ = [0.3457, 0.3352, 0.2752, 0.0439]. Then the **point positions** were diffused (targets held fixed) and the fit re-run, 12 replicates per t:

| t | ℓ | measured E_ℓ(t)/E_ℓ(0) | closed form e^{−2ℓ(ℓ+1)t} |
|---|---|---|---|
| 0.005 | 1 / 2 / 3 | 0.388 / 0.100 / 0.323 | 0.980 / 0.942 / 0.887 |
| 0.020 | 1 / 2 / 3 | 0.366 / 0.030 / 0.167 | 0.923 / 0.787 / 0.619 |
| 0.050 | 1 / 2 / 3 | 0.395 / 0.018 / 0.085 | 0.819 / 0.549 / 0.301 |
| 0.100 | 1 / 2 / 3 | 0.386 / 0.014 / 0.067 | 0.670 / 0.301 / 0.091 |

Three observations, none of them a failure of the identity (Leg 1 pins the identity):
1. **The energy collapses at t = 0.005**, where RMS geodesic displacement is only ≈ 0.14 rad and the closed form predicts ≤ 6% loss. The fitted energy of this corpus is not carried by smooth harmonic structure; it is carried by **atomic coincidences**: only 176 distinct rows of 512 possible, so the "point cloud" is a set of heavy point masses, the Gram matrix is far from the (N/4π)I of Eq. 39 on the *distinct-support* scale, and the ridge fit resolves atoms, not fields. An infinitesimal diffusion splits each atom into a cloud and the coherent fit dies immediately.
2. **The decay is non-monotone in ℓ** (ℓ=3 outlives ℓ=2 at every t): impossible for heat-kernel decay of a smooth field, diagnostic of structure-specific (atomic) energy.
3. **A floor persists** (ℓ=1 stabilizes ≈ 0.39): the residual coherent part that does behave like a field, plus incoherent refit noise.

**Interpretation (honest form).** The closed-form defocus law is verified where its hypothesis holds (quasi-uniform design) and fails where the hypothesis fails (atomic corpus). The gap between measured and closed-form decay is therefore a new, cheap **atomicity diagnostic**: define
  A_ℓ(t) = [e^{−2ℓ(ℓ+1)t} − E_ℓ(t)/E_ℓ(0)] ,
large A at small t ⇔ the corpus's spherical energy is atomic rather than smooth. On yubiOS A₁(0.005) ≈ 0.59. This quantifies, in one scalar, the same fact the is-this-x paper reached through the Hodge channel (176 distinct rows; marginals dominate) and pre-answers FINDINGS.1 G5: any generative diffusion model on this corpus must smooth the atoms first (vMF bandwidth as a pre-diffusion), or it will model point masses.

## Membership condition status
- The semigroup identity needs no null (it is a theorem; Leg 1 is an implementation check, like the compass selftest).
- The atomicity diagnostic A_ℓ(t) is NOT yet admitted to the map: it needs its non-degenerate null (compute A_ℓ(t) on curveball draws; a null corpus with the same marginals has nearly the same atom structure, so the null prediction is A_null ≈ A_real, making the *difference* the corpus-specific part). Specified, not executed.

## What this unlocks (unchanged from FINDINGS.1, now on firmer ground)
- Scale-space channel z(t) with matched nulls (G3), with the caveat that for atomic corpora the interesting regime is the ultra-small-t de-atomization window.
- SLERP fold: geodesic rungs slerp(p, p*; t_k) as the intrinsic replacement for the log-odds amplitude ladder.
- Sphere Langevin dX = −∇Φ dt + √(2T) dB with stationary density ∝ e^{−Φ/T}: the continuum extension of the curve-compass ± atom (its π_T(k) is the k-shell marginal; T→0 recovers the absorbing log).
- Standard-candle generator v2 via Riemannian score-based diffusion (De Bortoli et al. 2022; Huang et al. 2022; exact sphere heat kernels per NeurIPS 2023) — gated on smoothing the atoms first, per Leg 2.

## Reproduction
`python3 session/g1/g1_defocus.py <path-to-per_row_coverage_v3.json>` — numpy only, ~3 min. Constants: N=2048 (Leg 1), reps 48/12, Euler steps ≥ 40 and ≥ 400·t (Leg 1) / 800·t (Leg 2), λ=10⁻³, seed 20260813.
