# Spectral Defocus + De-Atomization on S^2

Deliverable D5. Implements experiment G1 from `papers/curved-corpus-unified-2026-08-13.tex`
and the atomicity finding from `papers/is-this-x-2026-08-12-Final.tex`.

## The compute win: diagonal spectral defocus

On S^2, the real spherical harmonics are eigenfunctions of the Laplace-Beltrami
operator: Delta Y_lm = -l(l+1) Y_lm. Brownian motion on the sphere has generator
Delta, so its heat semigroup acts *diagonally* in the spherical-harmonic basis:

    E_l(t) = E_l(0) * exp(-2 l(l+1) t)

for the per-degree Parseval energy of a field truncated to L<=3 (16 real
harmonics). Instead of simulating thousands of point-diffusion trajectories
and refitting the field at each time step (an O(N) or worse Monte-Carlo
simulation per query), `closed_form_decay(E0, t)` is an O(L) = O(4) closed
form: 4 multiplications and 4 exponentials, evaluated once. That is the
compute win this module packages.

## Validity boundary

The closed form is only valid where the semigroup identity actually holds on
the sampling design:

- **Quasi-uniform point designs.** We verify it on Vogel's Fibonacci lattice --
  points close to a spherical spiral-arrangement with even angular spacing.
  `--selftest` plants a smooth L<=3 field on this lattice, diffuses it with
  tangent-space Euler-Maruyama Brownian motion, and checks that the measured
  per-degree decay matches the closed form within 10% (Leg 1 / "G1 Leg 1" in
  the paper).
- **Smooth fields.** The identity is a statement about the true continuous
  field's spectrum; it says nothing about how a *discrete, possibly atomic*
  empirical dataset's fitted coefficients will behave once you start moving
  points around.

Outside that regime -- non-uniform point clouds, or fields with sharp
structure at the sampling scale -- the closed form should not be trusted
without the atomicity check below.

## The atomicity diagnostic

The paper's Leg 2 finding: the real corpus in
`papers/is-this-x-2026-08-12-Final.zip` is *atomic* -- only 176 distinct rows
out of 2286 (heavy exact duplication after the N x 9 coverage matrix is
z-scored, PCA'd to 2 components, RMS-rescaled, and stereographically lifted to
S^2). When you diffuse points drawn from an atomic distribution, per-degree
energy collapses far faster (60-90% at t=0.005 in the paper) than the closed
form permits (<=6%), and non-monotonically in l. The diagnostic that captures
this gap:

    A_l(t) = exp(-2 l(l+1) t) - E_l(t)/E_l(0)

`atomicity(E0, Emeas, t)` computes this directly: the first term is what the
closed form predicts for the ratio, the second is what you actually measured.
A_l(t) near 0 means the closed form's ratio held; A_l(t) large and positive
means real energy collapsed much faster than diagonal diffusion predicts --
the field is behaving like a near-delta-function ensemble, not a smooth
function on the sphere.

`--real-corpus` loads the corpus (matrix = rows[*].covered from the in-repo
zip), runs the same PCA/RMS/stereographic pipeline, and reports A_1(0.005) on
it. **Convention note:** the paper's protocol text specifies how positions on
S^2 are built (PC1/PC2 -> stereographic lift) but not what scalar field the
spherical-harmonic fit targets. This module's documented choice is the
(z-scored) third principal component score of each row as the fitted field
value -- i.e. PC1/PC2 give position, PC3 gives the value being fit. That is a
specific, defensible convention for this deliverable, not a verbatim
replication of an unstated paper detail, so the exact A_1 number will differ
from the paper's ~0.59 even though both replicate the same qualitative
finding (atomicity blows well past what quasi-uniform diffusion predicts).

## De-atomization: vMF kernel smoothing

The paper proposes von Mises-Fisher (vMF) kernel smoothing as pre-diffusion to
de-atomize the point cloud. `vmf_smooth(points, kappa, m, seed)` replaces each
point by `m` draws from vMF(center=point, concentration=kappa) on S^2, using
the standard inverse-CDF method for the cosine-angle marginal in the p=3
(sphere-in-R^3) special case:

    W = 1 + (1/kappa) * log(u + (1-u) * exp(-2*kappa)),  u ~ Uniform(0,1)

with azimuth uniform in the tangent plane at the center. This breaks up exact
duplicate point locations -- turning the corpus's 176-cluster atomic mass
into a smoother continuum -- without touching the target values, which are
carried unchanged from parent to child (`vmf_smooth_with_targets`).

`--real-corpus` also runs the atomicity check *after* smoothing at kappa=200,
m=4 and reports the before/after A_1(0.005) pair. Report from a representative
run on this corpus (see PR body for the exact numbers from CI/dev execution):
smoothing reduces A_1 by roughly 10-15% at these parameters -- real, but far
short of the "drops by at least half" bound suggested as a rough target. This
is an honest negative result worth stating plainly: kappa=200 is a fairly
tight concentration (angular spread ~1/sqrt(kappa) radians, a few degrees),
enough to separate exact-duplicate points but not enough to meaningfully
smooth the *value* function's high-frequency structure, since target values
are carried unchanged rather than kernel-averaged across neighbors. A value-
level kernel-regression smoother (replacing each target by a vMF-weighted
average of nearby targets, not just jittering positions) would likely do much
better at reducing A_1, but that is a different algorithm than the one
specified ("replace each point by m draws from vMF(...)") and is out of scope
for this module; it's a natural follow-up if the diagnostic needs to move
further.

## The paper's caveat: A_l is not yet a coordinate

The atomicity diagnostic answers "how far is this corpus from the diagonal-
diffusion regime", not "here is the corrected map to use instead". The papers
are explicit that A_l(t) is not yet an admitted coordinate on any corrected
manifold model -- its null (what A_l should look like under a well-specified
alternative to naive diagonal diffusion) is specified in principle but not
executed in the current work. Treat A_l as a red flag / diagnostic signal for
when the O(L) shortcut is unsafe to use, not as an input to further modeling
until that null is actually built out.

## API

- `fit_field(points, targets, lam=1e-3) -> FitResult(coeffs, energy, share)` --
  ridge-regress a scalar field onto the 16 L<=3 real spherical harmonics.
- `closed_form_decay(E0, t) -> np.ndarray[4]` -- the O(L) diagonal decay.
- `simulate_decay(points, targets, t, reps, seed) -> np.ndarray[4]` --
  Monte-Carlo ground truth via tangent-space Euler-Maruyama diffusion
  (dt <= 1e-3), refitting and averaging over `reps` runs.
- `atomicity(E0, Emeas, t) -> np.ndarray[4]` -- the A_l(t) diagnostic.
- `vmf_smooth(points, kappa, m, seed)` / `vmf_smooth_with_targets(...)` --
  de-atomization by vMF positional jitter.
- `fibonacci_lattice(n)`, `load_real_corpus_matrix(...)`, `matrix_to_sphere(...)`
  -- data plumbing for the self-tests.

## CLI

```
python3 tools/spectral-defocus/defocus.py --selftest
python3 tools/spectral-defocus/defocus.py --selftest --real-corpus
python3 tools/spectral-defocus/defocus.py --selftest --real-corpus --json
```

Run from the repo root (the real-corpus test reads
`papers/is-this-x-2026-08-12-Final.zip` relative to the current directory;
pass `--zip-path` to point elsewhere). Numpy is the only dependency.
