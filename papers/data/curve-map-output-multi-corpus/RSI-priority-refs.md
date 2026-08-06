# RSI Priority List — Top-10 Highest-Residual Files — `refs` corpus

The geodesic residual on the fitted curve γ(t) is the sparse-cell / RSI-priority
signal for this corpus. The 10 files with the largest residual are the highest-
priority targets for the next RSI cycle (per the curve-guided-rsi + single-action-
curve-rsi composition rule: highest residual = furthest from the fitted curve =
largest expected single-primitive-flip Δ on S²).

| Rank | File | Residual | Missing primitives | Covered | t | (X, Y, Z) on S² |
|---|---|---|---|---|---|---|
| 1 | `sealed-uki-vm-pkcs11-ecdsa-deepdive-VERIFIED-2026-07-31` | 0.0002 | `has_purpose`, `has_evidence`, `has_correction`, `has_constraint`, `has_pushback`, `has_test`, `has_recommendation`, `has_priority` | 1/9 | 1.0000 | (+0.998, +0.000, -0.069) |
| 2 | `sealed-uki-vm-prior-art-report-V52-2026-07-31` | 0.0000 | `has_purpose`, `has_evidence`, `has_correction`, `has_constraint`, `has_pushback`, `has_test`, `has_source`, `has_recommendation`, `has_priority` | 0/9 | 0.0000 | (-0.133, +0.000, -0.991) |
| 3 | `sealed-uki-vm-prior-art-report-2026-07-31` | 0.0000 | `has_purpose`, `has_evidence`, `has_correction`, `has_constraint`, `has_pushback`, `has_test`, `has_source`, `has_recommendation`, `has_priority` | 0/9 | 0.0000 | (-0.133, +0.000, -0.991) |
| 4 | `sealed-uki-vm-pkcs11-ecdsa-deepdive-2026-07-31` | 0.0000 | `has_purpose`, `has_evidence`, `has_correction`, `has_constraint`, `has_pushback`, `has_test`, `has_source`, `has_recommendation`, `has_priority` | 0/9 | 0.0000 | (-0.133, +0.000, -0.991) |
| 5 | `sealed-uki-vm-comparative-report-2026-07-31` | 0.0000 | `has_purpose`, `has_evidence`, `has_correction`, `has_constraint`, `has_pushback`, `has_test`, `has_source`, `has_recommendation`, `has_priority` | 0/9 | 0.0000 | (-0.133, +0.000, -0.991) |
| 6 | `sealed-uki-vm-comparative-report-V52-refresh-2026-07-31` | 0.0000 | `has_purpose`, `has_evidence`, `has_correction`, `has_constraint`, `has_pushback`, `has_test`, `has_source`, `has_recommendation`, `has_priority` | 0/9 | 0.0000 | (-0.133, +0.000, -0.991) |
| 7 | `sealed-uki-vm-debugging-journal-2026-07-30` | 0.0000 | `has_purpose`, `has_evidence`, `has_correction`, `has_constraint`, `has_pushback`, `has_test`, `has_source`, `has_recommendation`, `has_priority` | 0/9 | 0.0000 | (-0.133, +0.000, -0.991) |
| 8 | `falco-runtime-detection-prior-art-2026-08-05` | 0.0000 | `has_purpose`, `has_evidence`, `has_correction`, `has_constraint`, `has_pushback`, `has_test`, `has_source`, `has_recommendation`, `has_priority` | 0/9 | 0.0000 | (-0.133, +0.000, -0.991) |
| 9 | `curve-guided-rsi-rsphere-prior-art-stream-C-2026-08-05` | 0.0000 | `has_purpose`, `has_evidence`, `has_correction`, `has_constraint`, `has_pushback`, `has_test`, `has_source`, `has_recommendation`, `has_priority` | 0/9 | 0.0000 | (-0.133, +0.000, -0.991) |
| 10 | `curve-guided-rsi-corpus-enrichment-prior-art-stream-2-2026-08-05` | 0.0000 | `has_purpose`, `has_evidence`, `has_correction`, `has_constraint`, `has_pushback`, `has_test`, `has_source`, `has_recommendation`, `has_priority` | 0/9 | 0.0000 | (-0.133, +0.000, -0.991) |

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

