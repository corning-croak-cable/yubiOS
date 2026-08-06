# RSI Priority List — Top-10 Highest-Residual Files — `docs` corpus

The geodesic residual on the fitted curve γ(t) is the sparse-cell / RSI-priority
signal for this corpus. The 10 files with the largest residual are the highest-
priority targets for the next RSI cycle (per the curve-guided-rsi + single-action-
curve-rsi composition rule: highest residual = furthest from the fitted curve =
largest expected single-primitive-flip Δ on S²).

| Rank | File | Residual | Missing primitives | Covered | t | (X, Y, Z) on S² |
|---|---|---|---|---|---|---|
| 1 | `USER_RELATIONSHIPS` | 0.0011 | `has_purpose`, `has_evidence`, `has_correction`, `has_constraint`, `has_pushback`, `has_test`, `has_recommendation`, `has_priority` | 1/9 | 0.0852 | (-0.850, +0.411, +0.329) |
| 2 | `SAUNA_IDENTITY` | 0.0009 | `has_purpose`, `has_evidence`, `has_correction`, `has_constraint`, `has_pushback`, `has_test`, `has_source`, `has_recommendation`, `has_priority` | 0/9 | 0.0000 | (-0.931, +0.000, +0.364) |
| 3 | `SELF-CHANGELOG` | 0.0006 | `has_recommendation`, `has_priority` | 7/9 | 1.0000 | (+0.532, +0.755, +0.384) |
| 4 | `RULES` | 0.0002 | `has_purpose`, `has_correction`, `has_pushback`, `has_source`, `has_recommendation`, `has_priority` | 3/9 | 0.6951 | (+0.220, -0.876, -0.430) |
| 5 | `SELF` | 0.0002 | `has_purpose`, `has_correction`, `has_pushback`, `has_source`, `has_recommendation`, `has_priority` | 3/9 | 0.6951 | (+0.220, -0.876, -0.430) |
| 6 | `USER_PREFERENCES` | 0.0002 | `has_purpose`, `has_correction`, `has_pushback`, `has_source`, `has_recommendation`, `has_priority` | 3/9 | 0.6951 | (+0.220, -0.876, -0.430) |
| 7 | `RECENT_ACTIVITY` | 0.0001 | `has_purpose`, `has_correction`, `has_pushback`, `has_recommendation`, `has_priority` | 4/9 | 0.7803 | (+0.626, -0.000, -0.780) |
| 8 | `SAUNA_TOOLS` | 0.0001 | `has_purpose`, `has_correction`, `has_pushback`, `has_recommendation`, `has_priority` | 4/9 | 0.7803 | (+0.626, -0.000, -0.780) |
| 9 | `COMPANY` | 0.0001 | `has_purpose`, `has_correction`, `has_pushback`, `has_recommendation`, `has_priority` | 4/9 | 0.7803 | (+0.626, -0.000, -0.780) |
| 10 | `USER_PROFILE` | 0.0001 | `has_purpose`, `has_correction`, `has_pushback`, `has_recommendation`, `has_priority` | 4/9 | 0.7803 | (+0.626, -0.000, -0.780) |

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

