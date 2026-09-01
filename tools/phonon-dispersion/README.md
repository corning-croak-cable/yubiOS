# phonon-dispersion

The acoustic/optical phonon reading of the curved-corpus program, as a
deterministic instrument. Companion to
[`refs/acoustic-optical-phonons-bridge-2026-09-01.md`](../../refs/acoustic-optical-phonons-bridge-2026-09-01.md)
and Lean section 14 ([`papers/data/lean/CurvedCorpus.lean`](../../papers/data/lean/CurvedCorpus.lean)).
Pure stdlib, no numpy.

## What it checks (`--selftest`, wired into the `verify-tools` CI job)

1. **Diatomic chain anatomy** — the two-branch dispersion
   `ω²±(q) = C(1/m₁+1/m₂) ± C·√((1/m₁+1/m₂)² − 4sin²(qa/2)/(m₁m₂))`:
   acoustic branch exactly gapless at the zone center (the sum-rule zero mode),
   optical zone-center `√(2C(1/m₁+1/m₂))`, zone-boundary values `√(2C/m₁)`,
   `√(2C/m₂)`, gap open iff masses differ, equal-mass collapse onto the
   monatomic branch `2√(C/m)|sin(qa/2)|`.
2. **Klemens energy condition** — zone-center optical → two zone-boundary
   acoustic quanta allowed iff `m_heavy/m_light ≤ 3` (threshold exact; the
   Lean twin is `klemens_condition`).
3. **Acoustic sum rule, exactly** — the Hamming-graph H(d,2) Laplacian applied
   to every character `χ_r(a) = (−1)^{r·a}` gives `2·wt(r)·χ_r` in exact
   integer arithmetic (d = 4, all 16 characters); the `j = 0` all-ones mode is
   annihilated — the discrete twin of the program's conserved `ℓ = 0` mode.
4. **Level-penalty comparison** — S² eigenvalues `ℓ(ℓ+1)` (energy rate
   `2ℓ(ℓ+1)`) vs the Hamming ladder's linear `2j`: quadratic dominates beyond
   the shared zero mode.
5. **Gaunt selection rules, three routes** — the S² momentum-conservation
   analogue (triangle `|ℓ₁−ℓ₂| ≤ ℓ₃ ≤ ℓ₁+ℓ₂` + even parity) verified by
   (a) direct enumeration at L = 3 (64 triads → 34 triangle → 23 allowed,
   41 forbidden — the structure is **not** vacuous at the program's
   truncation), (b) the exact Wigner `3j(ℓ₁ℓ₂ℓ₃;000)` zero pattern for all
   ℓ ≤ 5, (c) Simpson integration of `∫P_{ℓ₁}P_{ℓ₂}P_{ℓ₃}` for all ℓ ≤ 4.
6. **Fermi–Dirac/Binomial identity** — at linear `Φ(k) = εk` the compass
   stationary law `π_T(k) ∝ C(9,k)e^{−εk/T}` **is** `Binomial(9, p)` with the
   FD per-primitive occupancy `p = 1/(1+e^{ε/T})`, to machine precision
   (0 new parameters; the Bose–Einstein reading is excluded — see the refs doc).

## Other modes

```
python3 tools/phonon-dispersion/phonon.py --dispersion 1.0 3.0   # branch table
python3 tools/phonon-dispersion/phonon.py --gaunt 3              # triad counts
python3 tools/phonon-dispersion/phonon.py --fd 0.5 0.05          # pi_T vs Binomial
```

## Discipline

Everything here is identity-side: closed-form algebra and exact spectra, no
corpus statistic, hence no curveball null needed. The one proposed
corpus-facing readout (the FD-residual "interaction beyond the ideal two-state
gas" on the measured Φ ladder) is **not** implemented here — it must first
pass its own curveball admission null, per the membership condition. Verdicts
and parameter accounting live in the refs bridge doc; designed-chain wall
applies to everything touching `π_T` or `T_×`.
