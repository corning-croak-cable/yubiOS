# RSI Priority List — Top-10 Highest-Residual Files (PR1)

The geodesic residual on the fitted curve γ(t) is the sparse-cell / RSI-priority
signal for the corpus. The 10 skills with the largest residual are the highest-
priority targets for the next RSI cycle (per the curve-guided-rsi + single-action-
curve-rsi composition rule: highest residual = furthest from the fitted curve =
largest expected single-primitive-flip Δ on S²).

| Rank | File | Residual | Missing primitives | Covered | t | (X, Y, Z) on S² |
|---|---|---|---|---|---|---|
| 1 | `recursive-self-improvement` | 1.4444 | `trust_chain`, `cryptographic_identity` | 7/9 | 0.2801 | (+0.183, +0.983, -0.033) |
| 2 | `bootc-images` | 0.8039 | `trust_chain`, `continuous_adaptive` | 7/9 | 0.2272 | (+0.070, -0.143, -0.987) |
| 3 | `slsa-provenance` | 0.8039 | `trust_chain`, `continuous_adaptive` | 7/9 | 0.2272 | (+0.070, -0.143, -0.987) |
| 4 | `learned-latent-curve` | 0.6854 | `trust_chain` | 8/9 | 0.1513 | (-0.206, +0.953, -0.223) |
| 5 | `github-stacked-pull-requests` | 0.6854 | `trust_chain` | 8/9 | 0.1513 | (-0.206, +0.953, -0.223) |
| 6 | `curve-guided-rsi` | 0.6854 | `trust_chain` | 8/9 | 0.1513 | (-0.206, +0.953, -0.223) |
| 7 | `observability-and-instrumentation` | 0.6591 | `least_privilege` | 8/9 | 0.1673 | (-0.185, +0.860, -0.475) |
| 8 | `doubt-driven-development` | 0.4391 | `least_privilege`, `continuous_adaptive` | 7/9 | 0.2433 | (+0.145, -0.498, -0.855) |
| 9 | `yubikey-operations` | 0.4391 | `least_privilege`, `continuous_adaptive` | 7/9 | 0.2433 | (+0.145, -0.498, -0.855) |
| 10 | `shipping-and-launch` | 0.3510 | `least_privilege`, `declarative_policy` | 7/9 | 0.3211 | (+0.499, +0.452, -0.739) |

## Why this list

Per `single-action-curve-rsi` §Composition Rule (Lemma 1 → Theorem 1):

- Each `delta_d ≥ 0` is guaranteed when the geodesic-only criterion selects
  one missing primitive flip per cycle.
- Cumulative corpus delta is monotone non-decreasing across cycles
  (Corollary 1 of `single-action-curve-rsi` §Composition Rule).
- High-residual skills contribute the largest per-cycle delta (largest gap
  between the projected point p and the fitted curve γ(t)).

## How to act on this list

Per skill in rank order, run one single-action cycle:

1. Pick the missing primitive whose flip minimizes d_post (geodesic-only criterion).
2. Apply the corresponding primitive-closure edit (e.g. add a `## Verification`
   section if `has_test` wins).
3. Re-fit and verify Δ ≥ 0.

Stop when the cumulative delta plateaus (RSI fixpoint). PR4
(`curve-drift-detector`) will close the loop across corpora.
