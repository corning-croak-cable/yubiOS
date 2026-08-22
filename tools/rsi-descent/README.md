# rsi-descent

**Deliverable D2** -- the single-action atom (papers/learned-latent-curves-2026-08-06.tex, Lemma 1) shipped as a runnable primitive. Reads a binary coverage matrix, drives it to full coverage by geodesic-only primitive flips toward the ideal pole on S^2, and asserts the Lean-proved monotone invariant at every dispatch.

## What this is

For each item (row) in a d-dimensional binary coverage matrix:
- Z-score the full N x d matrix, PCA top-2, stereographic lift to S^2.
- Compute geodesic gap d(f) = ||p - p*|| to the ideal pole p* (lift of the all-ones vector's PCA projection).
- Argmin over single missing-primitive flips: pick the one minimizing post-flip distance.
- Apply the flip if Delta = d_pre - d_post > epsilon; otherwise skip.
- Repeat per cycle until cycle-Delta falls below epsilon (fixpoint).

## The invariant

`papers/data/lean/CurvedCorpus.lean` proves `atom_delta_nonneg` (Lemma 1: every atomic Delta >= 0), `corpus_sum_nonneg` (Theorem 1: corpus total Delta >= 0), and `cumulative_monotone` (Corollary 1: cumulative sum is non-decreasing). This script enforces `delta >= -1e-12` at every dispatch and aborts loudly if it ever fails -- which would mean the script deviates from the proved mathematical model.

## Usage

```sh
python3 tools/rsi-descent/rsi_descent.py --input mydata.csv
python3 tools/rsi-descent/rsi_descent.py --input papers/is-this-x-2026-08-12-Final.zip --json
python3 tools/rsi-descent/rsi_descent.py --selftest
```

| flag | default | meaning |
| --- | --- | --- |
| `--input FILE` | (required) | CSV (rows of 0/1), JSON (2D array OR the repo's per_row_coverage_v3.json shape with `rows[*].covered`), or the in-repo evidence-bundle zip |
| `--epsilon` | `0.001` | Fixpoint threshold: cycle-Delta below this stops the loop |
| `--max-cycles` | `50` | Hard upper bound on cycles |
| `--seed` | `20260822` | Per-cycle item order |
| `--selftest` | | Run a 60x9 seeded matrix to fixpoint, assert no negative Delta |
| `--json` | | Emit the report as JSON |

## What fixpoint means

Per the papers' own discipline, the atom is **designed dynamics**, not an equilibrium claim: there is no equilibrium ensemble in the historical log (zero backward transitions over 1,178 measurements). Fixpoint here = no single flip moves the corpus further toward the ideal pole by more than `epsilon`. It is the end of a bounded exchangeable coverage potential's descent, not a thermodynamic equilibrium.

## Caveats

- Single-seed runs by default; re-run with `--seed` varied to see the per-k Delta ladder's robustness (the paper reports the ladder is identical across all three corpora, single-seed point estimates).
- The 9-bit basis is the paper's primitive basis for software-skill coverage. Other binary matrices with d != 9 are supported but the paper's k=5 ladder peak is d=9-specific.
- The pipeline (z-score -> PCA -> stereographic lift) is the paper's exact protocol. The ideal-pole construction is the lift of the all-ones vector projected through the same PCA basis; this matches the paper's `p* = sigma(u*, v*)` definition.