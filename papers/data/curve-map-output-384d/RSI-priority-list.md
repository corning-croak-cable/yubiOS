# RSI Priority List â Top-10 Highest-Residual Files (384-D sibling of PR1)

Embedding basis: **tfidf-384** (384-D).

The geodesic residual on the fitted curve Î³(t) is the sparse-cell / RSI-priority
signal for the corpus. The 10 skills with the largest residual are the highest-
priority targets for the next RSI cycle (per the curve-guided-rsi + single-action-
curve-rsi composition rule: highest residual = furthest from the fitted curve =
largest expected single-primitive-flip Î on SÂ²).

| Rank | File | Residual | Missing primitives | Covered | t | (X, Y, Z) on SÂ² |
|---|---|---|---|---|---|---|
| 1 | `nspawn-containers` | 1.0977 | `continuous_adaptive` | 8/9 | 0.6161 | (+0.477, -0.197, -0.857) |
| 2 | `yubikey-operations` | 0.6802 | `least_privilege`, `continuous_adaptive` | 7/9 | 0.6553 | (+0.538, -0.212, -0.816) |
| 3 | `composefs-kernel-floors` | 0.5700 | `least_privilege`, `declarative_policy`, `continuous_adaptive`, `audit_evidence` | 5/9 | 0.9202 | (+0.803, +0.423, -0.420) |
| 4 | `recursive-self-improvement` | 0.5299 | `trust_chain`, `cryptographic_identity` | 7/9 | 0.9157 | (+0.809, +0.388, -0.441) |
| 5 | `planning-and-task-breakdown` | 0.3663 | `declarative_policy` | 8/9 | 0.6334 | (+0.333, +0.919, -0.213) |
| 6 | `ci-cd-and-automation` | 0.3645 | `declarative_policy` | 8/9 | 0.6343 | (+0.337, +0.914, -0.225) |
| 7 | `shipping-and-launch` | 0.3509 | `least_privilege`, `declarative_policy` | 7/9 | 0.6340 | (+0.339, +0.911, -0.234) |
| 8 | `incremental-implementation` | 0.2546 | `declarative_policy` | 8/9 | 0.6196 | (+0.319, +0.920, -0.226) |
| 9 | `performance-optimization` | 0.2528 | `declarative_policy` | 8/9 | 0.6170 | (+0.314, +0.923, -0.221) |
| 10 | `interview-me` | 0.2172 | `declarative_policy`, `continuous_adaptive` | 7/9 | 0.0063 | (-0.640, +0.113, -0.760) |

## Why this list

Per `single-action-curve-rsi` Â§Composition Rule (Lemma 1 â Theorem 1):

- Each `delta_d â¥ 0` is guaranteed when the geodesic-only criterion selects
  one missing primitive flip per cycle.
- Cumulative corpus delta is monotone non-decreasing across cycles
  (Corollary 1 of `single-action-curve-rsi` Â§Composition Rule).
- High-residual skills contribute the largest per-cycle delta (largest gap
  between the projected point p and the fitted curve Î³(t)).

## How to act on this list

Per skill in rank order, run one single-action cycle:

1. Pick the missing primitive whose flip minimizes d_post (geodesic-only criterion).
2. Apply the corresponding primitive-closure edit (e.g. add a `## Verification`
   section if `has_test` wins).
3. Re-fit and verify Î â¥ 0.

Stop when the cumulative delta plateaus (RSI fixpoint).

## How this list differs from PR1's 9-D list

PR1 (`fit-full-curve-map.py`) uses a **9-D binary primitive coverage vector**;
this sibling variant uses a **384-D embedding** of the same text representations.
The math (PCAâSÂ²âMÃ¶biusâreal SH basisâchordal residual) is identical, so
rank-order differences reflect which embedding groups similar corpus items more
tightly. See `README.md` â Comparison vs 9-D PR1 for the top-3 from each side.
