# Gap D: Power the Lens

## What this is

Gap D is the papers' flagship open experiment on the Mobius chart
\`phi_theta\` that reparameterizes the S^2 domain ahead of the frozen
16-real-spherical-harmonic (L<=3) ridge fit used throughout this repo's
curved-corpus regime. The chart is a Mobius transformation applied via
stereographic projection:

\`\`\`
sphere --(stereographic projection)--> C --(Mobius: w -> (aw+b)/(cw+d))--> C --(inverse stereographic)--> sphere
\`\`\`

with a, b, c, d complex and ad - bc = 1 (6 real degrees of freedom: 4
complex numbers = 8 real, minus 2 real dof used up by the determinant
constraint). In every run in this repo's papers to date, phi_theta was
FROZEN at the identity Mobius map (a=d=1, b=c=0) -- an "unpowered lens".
Gap D asks: does OPTIMIZING phi_theta do anything useful?

Specifically: can the lens concentrate a planted target family's spectral
energy in the target (L=3) harmonic block, relative to a matched pure-noise
null evaluated under the exact same lens, without the lens itself becoming
a numerically pathological ("caustic") reparameterization?

## Design

1. **Lattice.** N=512 points on S^2, sampled with the canonical Vogel
   Fibonacci golden-angle construction: z_i = 1 - (2i+1)/N,
   phi_i = 2*pi*i / phi_golden, theta_i = arccos(z_i).
2. **Basis.** The frozen 16-function real spherical-harmonic basis, L=0..3,
   column order (0,0) (1,-1)(1,0)(1,1) (2,-2)..(2,2) (3,-3)..(3,3), using
   the corrected Y_3^3 constant K = sqrt(70/(64*pi)). Identical to
   create_corpus.py's real_sh_basis.
3. **Planted target family.** A continuous field
   y_i = s * combo(x_i) + noise_i, noise_i ~ N(0,1) iid, s = 1, where
   combo is a fixed standardized combination of two L=3 probe channels
   (Y_3^3 and Y_3^{-3}, i.e. basis columns 15 and 9 -- the same probe
   channels create_corpus.py uses for its planted corpora). This is a
   simplified, continuous adaptation of create_corpus.py's binary
   standard-candle generator, chosen because Gap D's objective needs a
   directly Parseval-decomposable real-valued target; see the fidelity note
   in gapD_lens_power.py's docstring for the exact relationship.
4. **Matched null.** The same pipeline with combo replaced by pure
   N(0,1) noise (no planted structure), R=20 replicates, drawn fresh for
   every lens evaluation.
5. **Objective J(theta).** Fit the 16-harmonic ridge (lambda=1e-3) to the
   field evaluated at phi_theta-transformed lattice points (the design
   matrix is the SH basis evaluated at the lensed points; the target values
   y stay fixed on the original lattice). Compute the Parseval energy
   share of the fitted coefficients that falls in the target L=3 block
   (columns 9-15) for the planted field, and for each of the 20 null
   replicates, ALL under the SAME phi_theta. J(theta) is the
   null-standardized z-score of the planted share against the null shares'
   mean/sd -- never raw fit quality, per the papers' discipline.
6. **Anti-caustic guard.** Any phi_theta for which the 16-column design
   matrix's numerical rank drops below 16, or whose condition number exceeds
   1e3, is rejected outright (assigned a large negative objective and
   excluded from consideration). The identity chart's own condition number
   is the sanity baseline (papers report ~1.003-1.006).
7. **Optimizer.** No scipy is available, so a simple two-stage search over
   the 6 real Mobius dof: (a) 200 random draws, parameterizing
   a,b,c,d = identity + eps * complex Gaussian then renormalizing by a
   single complex scalar so ad - bc = 1 exactly; (b) coordinate-wise
   refinement around the best draw, with a shrinking step size. Total
   budget ~400-600 objective evaluations.

## Pre-registration

Fixed before the run was inspected:

- **H1**: optimized J exceeds identity J by more than 2 null standard
  deviations -- the lens materially concentrates the planted family's L=3
  spectral energy beyond what the frozen identity chart achieves.
- **H0**: it does not -- the lens adds nothing useful at s=1, N=512.

Both outcomes were treated as publishable; gapD-results.json reports
whichever one actually held, honestly, with the full numbers.

## Self-checks

Before trusting the full run, two checks must pass:

- **Identity baseline sanity.** At theta = identity, the design matrix's
  condition number should be close to the papers-reported ~1.003-1.006
  range, and the ridge fit residual must be finite.
- **Cross-ratio preservation.** A genuine Mobius transformation preserves
  the cross-ratio of any 4 points in C to numerical precision (~1e-9). This
  is the correctness test for the Mobius implementation itself, independent
  of anything sphere- or basis-related.

Both are recorded in gapD-results.json under self_checks.

## Files

- papers/scripts/gapD_lens_power.py -- the canonical, self-contained
  numpy implementation (stdlib + numpy only, no scipy). Deterministic given
  --seed (default 20260822).
- papers/data/gapD/gapD-results.json -- the results of an actual run.
  See status and implementation_note in that file for an important
  caveat: the numbers were produced by a from-scratch TypeScript port of
  the identical algorithm, because the Python sandbox needed to execute the
  .py script directly was unavailable (HTTP 502) for the entire session in
  which this deliverable was built. Re-running the shipped .py script once
  the sandbox is healthy, and diffing against this file, is the natural
  immediate follow-up.
- papers/data/gapD/README.md -- this file.

## How to re-run

\`\`\`sh
python3 papers/scripts/gapD_lens_power.py --seed 20260822 --out papers/data/gapD/gapD-results.json
\`\`\`

Optional flags: --n-lattice, --n-null-reps, --n-random, --n-coord-rounds,
--amplitude. All default to the values used for the shipped results file.

## Limitations

- Single seed, single amplitude (s=1.0); no multi-seed or amplitude-sweep
  replication in this deliverable.
- The optimizer is a simple random-search + coordinate-refinement scheme
  with a small (~600-evaluation) budget, not a proper gradient-based or
  global optimizer -- reported best_J is a lower bound on what a stronger
  search could find.
- The planted-field generator is a simplified continuous adaptation of
  create_corpus.py's binary standard-candle scheme, not that exact
  procedure (see the fidelity note in the script's docstring).
- The shipped results were produced by a TypeScript reimplementation of the
  algorithm rather than an execution of the shipped Python script, due to
  Python sandbox unavailability during this session (see
  implementation_note in gapD-results.json).
