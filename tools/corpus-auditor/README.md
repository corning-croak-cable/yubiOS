# Corpus Auditor

A self-contained, numpy-only CLI that audits any binary coverage matrix
(rows x columns of 0/1) using this repo's null-standardized "is-this-x"
methodology: **V2**, the top-2 eigenvalue share of the column correlation
matrix, compared against a **curveball** (Strona trade) null that
preserves both row and column margins exactly.

The `v2_corr` and `curveball` functions are copied verbatim from
[`papers/data/lean/verify_claims.py`](../../papers/data/lean/verify_claims.py)
to preserve exact fidelity with the repo's published methodology --
they are not reimplemented or approximated.

## Usage

```sh
python3 tools/corpus-auditor/auditor.py --input mydata.csv
python3 tools/corpus-auditor/auditor.py --input mydata.json --json
python3 tools/corpus-auditor/auditor.py --selftest
```

### Options

| flag | default | meaning |
| --- | --- | --- |
| `--input FILE` | (required) | CSV or JSON coverage matrix, see Input formats |
| `--nsamp N` | 50 | number of null samples drawn for each of the three nulls |
| `--trades-per-row N` | 20 | curveball trades per row, per null sample (mixing budget = N x rows) |
| `--seed N` | 20260822 | RNG seed, for reproducibility |
| `--json` | off | emit machine-readable JSON instead of the human report |
| `--selftest` | off | run the built-in reproduction check against the published real corpus and exit |

Exit code is always `0` on a successful run -- the SIGNAL /
NULL-COMPATIBLE verdict is reported in the output, not encoded as an exit
status. A nonzero exit means the input itself was invalid (bad path,
wrong shape, non-binary entries, etc).

## Input formats

- **CSV**: a plain 0/1 matrix, rows x columns, comma-delimited, no header.
- **JSON**, either:
  - a plain 2D array of 0/1, e.g. `[[1,0,1],[0,1,1],...]`, or
  - this repo's per-row format: `{"rows": [{"covered": [1,0,1,...]}, ...]}`
    (as used by `papers/is-this-x-2026-08-12-Final.zip`).

## What the numbers mean

- **real V2** -- the observed top-2 eigenvalue share of the column
  correlation matrix. Higher means the columns' co-occurrence structure
  is more concentrated into a low-dimensional (here, rank-2) shape than
  you'd expect from independent columns.
- **curveball null mean/sd** -- V2 computed on matrices produced by
  randomly "trading" 1s between rows (the curveball / Strona algorithm),
  which preserves every row's and every column's marginal totals exactly
  while destroying any higher-order dependency structure. This is the
  primary, margin-matched null -- the fairest baseline for this data type.
- **delta V2 / z** -- how far the real V2 sits from the curveball null,
  in null standard deviations.
- **column-permutation null mean** -- V2 after independently shuffling
  each column. Keeps each column's total fixed but not the row totals;
  reported for contrast, not as the primary null.
- **iid Bernoulli null mean** -- V2 on independent Bernoulli draws with
  each column's probability matched to its real mean. Keeps no margins
  fixed at all; the least conservative baseline, reported for contrast.
- **verdict** -- `SIGNAL` if `|z| > 3` against the curveball null,
  else `NULL-COMPATIBLE`.

## Honesty constraints

- **The matched (curveball) null is always reported alongside the real
  V2** -- a bare V2 number with no null is not interpretable on its own,
  since V2 depends heavily on matrix shape and row/column margins.
- **An exact V2 of 1.0000 is a red flag, not a strong result.** It
  typically indicates rank degeneracy: too few independent columns after
  dropping zero-variance ones, or near-duplicate columns collapsing the
  correlation structure. The CLI prints an explicit warning in this case
  -- investigate the input before trusting the verdict.
- **z is over-dispersed.** Because the null is a finite Monte Carlo
  sample (not an exact analytic distribution), `z` is not a calibrated
  normal-theory z-score -- values in the `2 < |z| < 4` band should be
  read as inconclusive rather than as a hard cutoff. The CLI states this
  caveat in every human-readable report. This mirrors the discussion in
  this repo's `papers/`.

## Self-test

`--selftest` reproduces this repo's published result on the real
2286x9 coverage matrix shipped in
`papers/is-this-x-2026-08-12-Final.zip` (member
`is-this-x-2026-08-12/data/real/per_row_coverage_v3.json`), assuming it
is run from the repo root:

- real V2 == `0.7235293730732693` to 1e-9
- curveball null (defaults: nsamp=40, trades-per-row=20, seed=20260822):
  `z > 6` and `0.005 < deltaV2 < 0.025`
- published reference: null `0.709180 +/- 0.001183`, `z = +12.13`
  (see `papers/data/lean/verify_claims.py`, CLAIM 5)

See the PR description for the actual numbers obtained when this tool
was built.

## Provenance

This repo's papers (methodology, claims, and the real coverage-matrix
dataset referenced above) live under [`papers/`](../../papers/). This
tool does not modify or duplicate that data -- it only reads the
already-published zip archive when `--selftest` is invoked, and
otherwise operates on whatever matrix the caller points `--input` at.
