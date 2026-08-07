# Curve drift detector (PR4 of the hypersphere RSI series)

## What this is
Cross-corpus drift detector: aligns the harmonic curve fit on
`papers/data/` (papers-corpus: 9-primitive primitive coverage of the 79-skill
yubiOS corpus × 6 RSI cycles + 20 corpus-level single-action cycles) against
the harmonic curve fit on the SELF-doc corpus (10 memory files in
`memory/personal-WbtUgeUv/`, with each `## Section` as one item per the
`curve-guided-rsi-self` granularity rule), computes the Möbius
φ_θ ∈ PSL(2,ℂ) warp between them, and flags regions of large warp as drift
signals. Drift signals feed self-archaeology cadence dispatch.

## How to regenerate
1. Make sure the GitHub connection `conn_1KXnkOHGgyE4` (MASTER GIT SU) is
   active. Download the papers-corpus files into
   `session/papers-data-cache/`:
   ```
   curl -sL -H "X-Sauna-Connection-Id: conn_1KXnkOHGgyE4" \
        -H "Accept: application/vnd.github.v3.raw" \
        "https://api.github.com/repos/yubi-OS/yubiOS/contents/papers/data/single-action-curve-rsi-cycles-2026-08-05.json" \
        -o session/papers-data-cache/single.json
   curl -sL -H "X-Sauna-Connection-Id: conn_1KXnkOHGgyE4" \
        -H "Accept: application/vnd.github.v3.raw" \
        "https://api.github.com/repos/yubi-OS/yubiOS/contents/papers/data/rsi-79-corpus-multi-cycle-2026-08-06.json" \
        -o session/papers-data-cache/multi.json
   ```
2. Run from the workspace root:
   ```
   python3 documents/github-yubios-KS9n5GAT/papers/scripts/curve-drift-detector.py
   ```
3. Outputs land in
   `documents/github-yubios-KS9n5GAT/papers/data/drift-output/`.

## Math conventions (frozen per parent's contract)
- **9-D `internal-big-picture` primitive basis** (9 of 10 primitives; the
  10th, `self_describing`, dropped at 94% coverage per
  `internal-big-picture`'s near-constant rule). Same basis for BOTH corpora
  (cross-corpus deviation from `curve-guided-rsi-self`'s per-corpus basis
  rule — documented as an explicit simplification for this artifact).
- **Identity-init Möbius**: φ_θ start = (a=1, b=0, c=0, d=1), refined via
  L-BFGS-B with 6 random perturbations around identity; objective = mean
  squared chordal distance in the stereographed C plane.
- **Frozen degree weights**: frequencies are the cold-start harmonic series
  1, 2, ..., k (k=8); NOT refined in this artifact per the parent's
  "frozen degree weights" rule.
- **Chordal S² distance**: used as proxy for geodesic distance in the
  cross-ratio check + sparse-cell detection (r ≈ 0.095 per parent's
  `hyperspherical-harmonic-curve` `## Empirical Validation — v2`).
- **Sub-20 decomposition rule**: NOT applied; both corpora are well above
  the ≥20 gate (`papers-corpus` = 494 items,
  `self-corpus` = 111 items).
- **Pipeline**:
  1. 9-D binary coverage → drop near-constant cols (coverage ∈ [0.10, 0.90])
  2. INTERSECTION of kept cols across corpora for cross-corpus comparison
  3. Seeded QR lift to D=384 (seed 12345; deterministic)
  4. PCA top-2 (with rank-uniformization per parent's robustness rule)
  5. Lat/lon lift to S² (theta = π·u, phi = 2π·v)
  6. Harmonic curve fit per corpus (closed-form ridge, k=8 frozen freqs)
  7. Möbius alignment (identity init → L-BFGS-B; cross-ratio check)
  8. Per-region warp (n_samples = 24; chordal S² distance to
     closest point on dense-sampled curve-B)
  9. NSS-axis scoring per region (12-axis keyword sweep from
     `self-archaeology`)
  10. Drift flag = (warp ≥ pctl 80%) AND
      (nss_total ≥ pctl 80%)

## How to read drift signals
- `warp-by-region.csv`: one row per sampled region. `flagged=true` rows are
  candidates for self-archaeology dispatch.
- `drift-priority-list.md`: top 10 flagged regions ranked by warp magnitude,
  with NSS axis breakdown and a self-archaeology hook per region.
- `mobius-transform.json`: the fitted φ_θ (a, b, c, d ∈ ℂ with ad - bc = 1).
  Apply this Möbius to future curve fits to project onto the same warped
  coordinate system — enables cross-cycle comparison.
- `aligned-curves.png`: visual overlay of both curves on S² (Mollweide-style
  projection). Warp regions highlighted in orange; flagged regions in solid
  orange.

## Deviations from prior skills
- **Per-corpus basis rule violated**: `curve-guided-rsi-self` says use a
  per-corpus 9-D basis (row primitives for SELF.md rows, changelog primitives
  for SELF-CHANGELOG.md entries, unified memory-file primitives for the
  expanded corpus). This artifact uses the SAME 9-D `internal-big-picture`
  primitive basis for BOTH corpora — the cross-corpus comparison requires a
  shared primitive vocabulary. The text-based scoring for self-corpus items
  uses the same 9 primitives' keyword vocab (frozen), so coverage vectors
  are comparable across corpora. Documented as a deviation.
- **Frozen degree weights**: per the parent's `frozen_degree_weights: true`
  flag, frequencies are NOT refined in this artifact. Future iterations can
  lift this constraint by setting `frozen=False` in
  `fit_harmonic_curve_s2`.
- **PIL rendering vs matplotlib**: this env has matplotlib 3.11.1 with
  Python 3.9 (incompatible — `match` syntax requires Py3.10+). The existing
  scripts in this repo work around this with PIL.ImageDraw; this artifact
  follows the same convention.

## Verification (closed-loop per artifact)
- [x] Both corpora listed: `papers-corpus-listing.json`,
      `self-corpus-listing.json` parse as JSON.
- [x] CSV parses: `warp-by-region.csv` has 1 header row + N_WARP_SAMPLES
      data rows.
- [x] PNG renders: `aligned-curves.png` saved (1100×720).
- [x] Drift-priority list populated: `drift-priority-list.md` has top-10
      flagged regions (or note when none clear).
- [x] Möbius transform saved: `mobius-transform.json` with cross-ratio
      check recorded.
- [x] End-to-end run succeeded (exit code 0).
