# RSI Priority List — Top-10 Highest-Residual Files — `skills` corpus

The geodesic residual on the fitted curve γ(t) is the sparse-cell / RSI-priority
signal for this corpus. The 10 files with the largest residual are the highest-
priority targets for the next RSI cycle (per the curve-guided-rsi + single-action-
curve-rsi composition rule: highest residual = furthest from the fitted curve =
largest expected single-primitive-flip Δ on S²).

| Rank | File | Residual | Missing primitives | Covered | t | (X, Y, Z) on S² |
|---|---|---|---|---|---|---|
| 1 | `learned-latent-curve` | 0.0201 | `has_purpose`, `has_evidence`, `has_correction`, `has_pushback`, `has_test`, `has_source`, `has_recommendation`, `has_priority` | 1/9 | 0.1434 | (+0.491, +0.734, -0.469) |
| 2 | `recursive-self-improvement` | 0.0201 | `has_purpose`, `has_evidence`, `has_correction`, `has_pushback`, `has_test`, `has_source`, `has_recommendation`, `has_priority` | 1/9 | 0.1434 | (+0.491, +0.734, -0.469) |
| 3 | `hyperspherical-harmonic-curve` | 0.0119 | `has_purpose`, `has_correction`, `has_constraint`, `has_pushback`, `has_test`, `has_source`, `has_recommendation`, `has_priority` | 1/9 | 0.1652 | (+0.431, -0.898, -0.091) |
| 4 | `internal-big-picture` | 0.0119 | `has_purpose`, `has_correction`, `has_constraint`, `has_pushback`, `has_test`, `has_source`, `has_recommendation`, `has_priority` | 1/9 | 0.1652 | (+0.431, -0.898, -0.091) |
| 5 | `the-follower` | 0.0119 | `has_purpose`, `has_correction`, `has_constraint`, `has_pushback`, `has_test`, `has_source`, `has_recommendation`, `has_priority` | 1/9 | 0.1652 | (+0.431, -0.898, -0.091) |
| 6 | `single-action-curve-rsi` | 0.0007 | `has_source` | 8/9 | 1.0000 | (+0.640, +0.062, +0.766) |
| 7 | `systemd-homed` | 0.0001 | `has_purpose`, `has_evidence`, `has_correction`, `has_constraint`, `has_pushback`, `has_test`, `has_source`, `has_recommendation`, `has_priority` | 0/9 | 0.0000 | (-0.134, +0.035, -0.990) |
| 8 | `systemd-hardening` | 0.0001 | `has_purpose`, `has_evidence`, `has_correction`, `has_constraint`, `has_pushback`, `has_test`, `has_source`, `has_recommendation`, `has_priority` | 0/9 | 0.0000 | (-0.134, +0.035, -0.990) |
| 9 | `the-cult` | 0.0001 | `has_purpose`, `has_evidence`, `has_correction`, `has_constraint`, `has_pushback`, `has_test`, `has_source`, `has_recommendation`, `has_priority` | 0/9 | 0.0000 | (-0.134, +0.035, -0.990) |
| 10 | `token-efficiency` | 0.0001 | `has_purpose`, `has_evidence`, `has_correction`, `has_constraint`, `has_pushback`, `has_test`, `has_source`, `has_recommendation`, `has_priority` | 0/9 | 0.0000 | (-0.134, +0.035, -0.990) |

## Why this list

Per `single-action-curve-rsi` §Composition Rule (Lemma 1 → Theorem 1):

- Each `delta_d ≥ 0` is guaranteed when the geodesic-only criterion selects
  one missing primitive flip per cycle.
- Cumulative corpus delta is monotone non-decreasing across cycles
  (Corollary 1 of `single-action-curve-rsi` §Composition Rule).
- High-residual files contribute the largest per-cycle delta (largest gap
  between the projected point p and the fitted curve γ(t)).

## How to act on this list

Per file in rank order, run one single-action cycle:

1. Pick the missing primitive whose flip minimizes d_post (geodesic-only criterion).
2. Apply the corresponding primitive-closure edit (e.g. add a `## Verification`
   section if `has_test` wins).
3. Re-fit and verify Δ ≥ 0.

Stop when the cumulative delta plateaus (RSI fixpoint). PR4
(`curve-drift-detector`) will close the loop across corpora.

