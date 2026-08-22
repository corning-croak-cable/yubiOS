# boltzmann-collapse

**Deliverable D4** -- the exchangeability-collapse compute module for the
curve-compass +/- atom described in
\`papers/is-this-x-2026-08-12-Final.tex\` (sec. "designed-counterpart").

## The identity, and why it is exact

The compass runs a Metropolis-Hastings chain on coverage states
\`c in {0,1}^d\`. Its potential \`Phi(c)\` depends **only** on the coverage
count \`k = sum(c)\` -- it is an *exchangeable* potential: any two states
with the same number of covered coordinates get the same potential,
regardless of *which* coordinates are covered.

That single fact is enough to collapse the chain exactly:

- The Metropolis acceptance ratio between two states depends only on the
  potential difference, so for an exchangeable potential it depends only
  on \`k\` and \`k'\`, never on which coordinates flipped.
- There are exactly \`C(d, k)\` microstates sharing a given \`k\`.
- Therefore the equilibrium (detailed-balance) distribution over the full
  \`2^d\`-state space is *itself* a function of \`k\` alone, and grouping
  states by \`k\` gives the exact aggregated law:

\`\`\`
pi_T(k)  =  C(d, k) * exp(-Phi(k) / T) / Z_T,      k = 0 .. d
Z_T       =  sum_k C(d, k) * exp(-Phi(k) / T)
F_T(k)    =  Phi(k) - T * log C(d, k)               (free energy per shell)
\`\`\`

This is not an approximation, a mean-field truncation, or a large-\`d\`
asymptotic -- it is an identity that follows from "the potential only sees
\`k\`", true for every \`d\` and every \`T\`. \`collapse.py\`'s \`--verify\` /
self-test brute-force check enumerates the full \`2^d\`-state chain
directly and confirms the two distributions agree to float64 precision
(< 1e-12 absolute error).

## The d+1-shell reduction

Because the chain collapses onto \`k\`-shells, a state space of size
\`2^d\` (exponential in \`d\`) reduces to a state space of size \`d + 1\`
(linear in \`d\`) for every equilibrium quantity: the stationary
distribution, the free energy, the partition function, and the location
of the energy/entropy crossover temperature \`T_x\`. For \`d = 20\` that is
1,048,576 states collapsing to 21 shells; the module's \`--benchmark\`
flag reports the resulting closed-form vs brute-force speedup at each
\`d\` from 9 to 20.

\`T_x\` is where \`argmax_k pi_T(k)\` switches from the energy-dominated
shell (\`argmin_k Phi(k)\`) to the entropy-dominated shell
(\`argmax_k C(d,k)\`, i.e. \`k = d // 2\`) as \`T\` increases -- below
\`T_x\` the chain concentrates near the potential's minimum, above it the
combinatorial multiplicity of mid-range shells wins.

## The T-is-a-designer-knob caveat

\`T\` in this module is **designed dynamics, not a corpus observable**.
The papers are explicit that the compass's temperature is a parameter
chosen by whoever runs the chain (to trade off exploration vs
convergence to the potential's minimum), not something measured from a
corpus or fit to data the way \`Phi(k)\` is. Do not treat \`T\` (or
\`T_x\`) as an empirical property of a corpus -- it is a property of the
sampler you chose to run over that corpus's \`Phi\` ladder. Reusing a
measured \`T_x\` (e.g. the \`d=9\` value below) across a different \`Phi\`
ladder or a different \`d\` is not meaningful; \`T_x\` is a joint property
of \`(Phi, d)\`, recomputed here via \`crossover()\`, not a universal
constant.

## Library API

\`\`\`python
from collapse import pi_T, free_energy, partition, crossover, brute_force_pi

pi_T(phi, d, T)          # -> np.ndarray[d+1], exact closed-form equilibrium
free_energy(phi, d, T)   # -> np.ndarray[d+1], F_T(k) = Phi(k) - T*log C(d,k)
partition(phi, d, T)     # -> float, log Z_T (log-sum-exp stabilized)
crossover(phi, d, T_grid) # -> dict with T_x, refined by bisection on T_grid
brute_force_pi(phi, d, T) # -> np.ndarray[d+1], ground truth via direct 2^d enumeration (d <= 20)
\`\`\`

All of \`pi_T\`, \`free_energy\`, and \`partition\` are computed via a
log-sum-exp reduction, so they stay numerically stable even when
\`Phi(k)/T\` is large.

## CLI usage

\`\`\`sh
# Evaluate pi_T and F_T at a given T, with a brute-force cross-check
python collapse.py --phi "2.0,1.9758,1.908,1.8091,1.6933,1.5727,1.4552,1.3454,1.2451,1.1547" \\
    --d 9 --T 0.0411 --verify

# Find the energy/entropy crossover temperature over a log-spaced grid
python collapse.py --phi "..." --d 9 --crossover --T-grid 0.005:2.0:2000

# Machine-readable output
python collapse.py --phi "..." --d 9 --T 1.0 --json

# Time closed-form vs brute-force enumeration for d = 9 .. 20
python collapse.py --benchmark

# Run the full self-test suite (correctness, compass T_x reproduction, benchmark)
python collapse.py --selftest
\`\`\`

## Self-test

\`python collapse.py --selftest\` runs three checks:

1. **Correctness.** For \`d in {5, 9, 12}\` with a random seeded \`Phi\`
   ladder, the closed-form \`pi_T\` is asserted to equal the brute-force
   \`2^d\`-state enumeration to within \`1e-12\` absolute error, at
   \`T in {0.05, 0.2, 1.0, 5.0}\`.
2. **Compass reproduction.** The measured \`Phi(k)\` ladder for \`d = 9\`
   is loaded from the in-repo bundle
   \`papers/is-this-x-2026-08-12-Final.zip\`, member
   \`is-this-x-2026-08-12/results/curve-compass-results.json\`, field
   \`phi_ladder.Phi\` (cross-checked against the \`Phi(k)\` column of
   \`.../skills/curve-compass-skill/references/phi-ladder.md\`, which
   tabulates the identical ten values). \`crossover()\` is run over a
   4001-point log-spaced grid from \`T=0.005\` to \`T=2.0\` and the result
   is asserted within 5% of the published \`T_x = 0.041143\`. If the zip
   cannot be located on the filesystem this check is **skipped with an
   explicit warning**, not faked.
3. **Benchmark.** Closed-form vs brute-force timings are printed for
   \`d = 16\` (65,536 states).

## Limitations

- \`brute_force_pi\` is guarded to \`d <= 20\` (\`2^20\` states); beyond
  that, only the closed form is available (which is, of course, the
  point -- the closed form has no such ceiling).
- The exactness result depends entirely on \`Phi\` being a function of
  \`k\` alone. If a future potential depends on which coordinates are
  covered (not just how many), this collapse does **not** apply and the
  full \`2^d\`-state chain must be simulated.
- \`crossover()\`'s bisection assumes a single argmax switch in the
  supplied \`T_grid\`; a \`Phi\` ladder with multiple non-monotonic
  crossovers would need a finer grid or a different search strategy to
  find every switch point, not just the first.
