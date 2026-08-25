# spectral-decomposer

A curve-guided-self-ideate tool. Given a corpus matrix, produces a
ranked list of "new idea" candidates in the **lens-format** pioneered by
`skills/curve-compass-skill` (cycle-34 L141-L146) and re-grounded in the
program's harmonic-fit machinery plus the Lean-4-proved
curveball fixed-margin null.

Every candidate IS a measurable experiment. The output `cycle-NN-lens.md`
artifact drops directly into a curve-guided-rsi cycle.

## What it does

1. Loads the corpus as a binary `N × d` coverage matrix.
2. Embeds rows via PCA-top-2 + stereographic lift (same pipeline as
   `tools/rsi-descent`), fits real spherical harmonics on the
   Fibonacci-lattice, and reports Parseval shares per degree.
3. Identifies the top-K sparsest cells, weighted by low-ℓ mass (the
   coarse structure that the corpus actually carries).
4. For each sparse cell, emits three candidates:
   - **real** — flip the cell on the original matrix, re-measure
     corpus level in dBc against the curveball vacuum.
   - **control** — same flip on a curveball-shuffled copy (Lean §8:
     trades preserve the fixed-margin fibre; the null is canonical
     per Lean §9).
   - **differential** — real minus control, in dBc, with verdict
     (YES / PARTIAL / NO) and score (0–50).
5. Renders the candidates as a lens-format `cycle-NN-lens.md`.

## Quick start

```bash
./spectral_decomposer.py --selftest
./spectral_decomposer.py --input <corpus.json|zip|csv> --cycle 34
./spectral_decomposer.py --input <corpus.json> --json
```

## Connection to the curved-corpus program

This tool is the deliverable-side analogue of `curve-guided-rsi-self`
and the measurement-side analogue of the cycle-34 lens-format patch
generation in `skills/curve-compass-skill`. Each candidate's delta is
reported in **dBc** against the curveball vacuum — so a YES verdict
means the candidate deflects above the +15.6 dBc detectability floor
established by `tools/corpus-sonometer` on the real corpus.

The control arm is the language-side analogue of Gap D's selection-null
control arm (ΔJ = +126.1, ~5× control) — every candidate carries both
a real and a curveball-control reading so a "YES" verdict is only as
good as the control's silence.

## Lean anchors

- **§8 `trade_preserves_rowSum / trade_preserves_colSum`** — the
  curveball null preserves row+column sums; the tool's control arm
  is a curveball-shuffled copy of the corpus, not a re-draw.
- **§9 `trade_reversible / uniform_inflow_constant`** — uniform is
  the canonical null on the fibre; the corpus-sonometer dBc reading
  is calibrated against this null, not against the corpus itself.
- **§10 `stationary_unique_uniform`** — uniqueness of the null
  via the discrete maximum principle; the tool does not generate
  alternative nulls and would reject them if it did.
- **§12 `bpow_add / level_double / level_injective`** — the dBc
  level laws; the tool's delta readout obeys all three (cascade
  additivity, squaring doubles the level, readings are injective).

## Honest negative (what this tool is NOT)

- It is not a substitute for `tools/rsi-descent` — it does not
  iterate cycles, only generates the lens pool for a single cycle.
- It is not an LLM — every candidate is computed from the matrix,
  no language model involved.
- It does not check the caustic detector (Lean §10) — the caveat
  field warns about rank-collapse on the primitive basis.

## Implementation

numpy only. Deterministic given `--seed`. The Fibonacci-lattice fit
and the curveball null are the same algorithms shipped in
`tools/corpus-sonometer` and `tools/corpus-auditor`.
