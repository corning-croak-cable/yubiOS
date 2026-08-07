# RSI Priority List — Top-10 Highest-Residual Files (PR1)

The geodesic residual on the fitted curve γ(t) is the sparse-cell / RSI-priority
signal for the corpus. The 10 skills with the largest residual are the highest-
priority targets for the next RSI cycle (per the curve-guided-rsi + single-action-
curve-rsi composition rule: highest residual = furthest from the fitted curve =
largest expected single-primitive-flip Δ on S²).

| Rank | File | Residual | Missing primitives | Covered | t | (X, Y, Z) on S² |
|---|---|---|---|---|---|---|
| 1 | `runtime-attestation-keylime` | 1.8152 | `trust_chain`, `segmentation` | 7/9 | 0.2437 | (+0.052, +0.999, -0.013) |
| 2 | `learned-latent-curve` | 1.2360 | `trust_chain` | 8/9 | 0.1644 | (-0.198, +0.953, -0.231) |
| 3 | `curve-guided-rsi` | 1.2360 | `trust_chain` | 8/9 | 0.1644 | (-0.198, +0.953, -0.231) |
| 4 | `github-stacked-pull-requests` | 1.2360 | `trust_chain` | 8/9 | 0.1644 | (-0.198, +0.953, -0.231) |
| 5 | `observability-and-instrumentation` | 1.0944 | `least_privilege` | 8/9 | 0.1694 | (-0.224, +0.823, -0.522) |
| 6 | `slsa-provenance` | 0.8061 | `trust_chain`, `continuous_adaptive` | 7/9 | 0.2280 | (+0.018, -0.101, -0.995) |
| 7 | `bootc-images` | 0.8061 | `trust_chain`, `continuous_adaptive` | 7/9 | 0.2280 | (+0.018, -0.101, -0.995) |
| 8 | `recursive-self-improvement` | 0.7307 | `trust_chain`, `cryptographic_identity` | 7/9 | 0.3031 | (+0.227, +0.970, -0.081) |
| 9 | `code-review-and-quality` | 0.3919 | `least_privilege`, `declarative_policy`, `continuous_adaptive` | 6/9 | 0.3731 | (+0.499, -0.828, -0.256) |
| 10 | `shipping-and-launch` | 0.3826 | `least_privilege`, `declarative_policy` | 7/9 | 0.3095 | (+0.421, +0.307, -0.853) |

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
