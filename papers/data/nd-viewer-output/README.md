# N-D axis viewer — 24-D RSI corpus feature space

**PR3 of 4-PR hypersphere RSI series** — built build-nd-axis-viewer.py.

## What this is

For each row in `papers/data/rsi-79-corpus-multi-cycle-2026-08-06.json` (a corpus item
at a specific RSI cycle), we construct a **24-D feature vector** combining three bases:

1. **9 internal-big-picture primitives** (binary presence / missing-flag from the corpus)
2. **12 negative-skill-space axes** (scored 0..1 from each skill's SKILL.md text)
3. **3 run-metadata fields** (cycle#, geodesic delta, FIRES bool)

We PCA-project the standardized 24-D space to 2D, then expose:

- `nd-vectors.json` — every row's axis values + 2D PCA coordinates + cycle/delta/FIRES
- `nd-pca-static.png` — labeled scatter of all 474 items in PCA space
- `nd-viewer.html` — interactive Plotly scatter with **one slider per axis** (24 sliders)
- `nd-axis-correlation.csv` — pairwise Pearson correlation across all 24 axes
- this README

## Stats

- Corpus: **474 items** (79 unique skills × 6 cycles)
- FIRES count: **116 / 474** (24.5%)
- Mean Δ across all items: **+0.0238**
- PCA explained variance: **PC1 35.7%, PC2 11.9%** (sum 47.5%)

## Axis list

### 9 internal-big-picture primitives

- `attestation` — 1 if the skill has this primitive at the given cycle, 0 if it was in `missing_primitives`.
- `audit_evidence` — 1 if the skill has this primitive at the given cycle, 0 if it was in `missing_primitives`.
- `continuous_adaptive` — 1 if the skill has this primitive at the given cycle, 0 if it was in `missing_primitives`.
- `cryptographic_identity` — 1 if the skill has this primitive at the given cycle, 0 if it was in `missing_primitives`.
- `declarative_policy` — 1 if the skill has this primitive at the given cycle, 0 if it was in `missing_primitives`.
- `immutability` — 1 if the skill has this primitive at the given cycle, 0 if it was in `missing_primitives`.
- `least_privilege` — 1 if the skill has this primitive at the given cycle, 0 if it was in `missing_primitives`.
- `segmentation` — 1 if the skill has this primitive at the given cycle, 0 if it was in `missing_primitives`.
- `trust_chain` — 1 if the skill has this primitive at the given cycle, 0 if it was in `missing_primitives`.

### 12 negative-skill-space axes

- `audience` — 0..1 score from SKILL.md section-presence + keyword hit count (1 hit→0.4, 2→0.6, 3→0.8, 4+→1.0; falls back to slug-length proxy when SKILL.md missing).
- `inputs` — 0..1 score from SKILL.md section-presence + keyword hit count (1 hit→0.4, 2→0.6, 3→0.8, 4+→1.0; falls back to slug-length proxy when SKILL.md missing).
- `outputs` — 0..1 score from SKILL.md section-presence + keyword hit count (1 hit→0.4, 2→0.6, 3→0.8, 4+→1.0; falls back to slug-length proxy when SKILL.md missing).
- `mode` — 0..1 score from SKILL.md section-presence + keyword hit count (1 hit→0.4, 2→0.6, 3→0.8, 4+→1.0; falls back to slug-length proxy when SKILL.md missing).
- `assumption_set` — 0..1 score from SKILL.md section-presence + keyword hit count (1 hit→0.4, 2→0.6, 3→0.8, 4+→1.0; falls back to slug-length proxy when SKILL.md missing).
- `adjacent_problems` — 0..1 score from SKILL.md section-presence + keyword hit count (1 hit→0.4, 2→0.6, 3→0.8, 4+→1.0; falls back to slug-length proxy when SKILL.md missing).
- `failure_modes` — 0..1 score from SKILL.md section-presence + keyword hit count (1 hit→0.4, 2→0.6, 3→0.8, 4+→1.0; falls back to slug-length proxy when SKILL.md missing).
- `lifecycle` — 0..1 score from SKILL.md section-presence + keyword hit count (1 hit→0.4, 2→0.6, 3→0.8, 4+→1.0; falls back to slug-length proxy when SKILL.md missing).
- `composition` — 0..1 score from SKILL.md section-presence + keyword hit count (1 hit→0.4, 2→0.6, 3→0.8, 4+→1.0; falls back to slug-length proxy when SKILL.md missing).
- `knowledge_sources` — 0..1 score from SKILL.md section-presence + keyword hit count (1 hit→0.4, 2→0.6, 3→0.8, 4+→1.0; falls back to slug-length proxy when SKILL.md missing).
- `calibration` — 0..1 score from SKILL.md section-presence + keyword hit count (1 hit→0.4, 2→0.6, 3→0.8, 4+→1.0; falls back to slug-length proxy when SKILL.md missing).
- `recursion` — 0..1 score from SKILL.md section-presence + keyword hit count (1 hit→0.4, 2→0.6, 3→0.8, 4+→1.0; falls back to slug-length proxy when SKILL.md missing).

### 3 run-metadata fields

- `cycle` — the RSI cycle number (1..6)
- `delta` — the geodesic-distance improvement `d_pre − d_post` for that row
- `FIRES` — bool, true iff `delta > 0` (the verification metric satisfied its gate for this item)

## How to regenerate

```bash
python3 papers/scripts/build-nd-axis-viewer.py
```

The script will:
1. Fetch the corpus via GitHub API (`papers/data/rsi-79-corpus-multi-cycle-2026-08-06.json`,
   domain `api.github.com`) — falls back to the local cache at `session/cache/rsi-79-corpus.json`.
2. Load each skill's `SKILL.md` text from `skills/github-yubios-KS9n5GAT/<slug>/SKILL.md`
   (or `skills/personal-WbtUgeUv/<slug>/SKILL.md`) for NSS-axis scoring.
3. Build the 24-D matrix, standardize, PCA → 2D.
4. Emit all five artifacts to `papers/data/nd-viewer-output/`.

## How the viewer works

Open `nd-viewer.html` in any browser (no server needed — Plotly loads from CDN).
Each of the 24 sliders sets a **minimum threshold** for its axis; items with `axis ≥ threshold`
remain on the scatter. Drag any slider to filter live. FIRES is a checkbox (checked = show
only fired items; uncheck to allow no-fire items). The status bar at the bottom of the panel
shows live `shown / total` counts.

**Controls:**
- **Reset to median** — set every threshold to the per-axis median
- **Show all (zeros)** — set every threshold to the per-axis min + uncheck FIRES (show everything)

## Deviations from the spec

- **N = 24, not 23.** The spec lists 9 primitives + 12 NSS axes + 3 run-metadata
  fields (cycle#, delta, FIRES) = **24 axes**, not 23. The spec text says "23 sliders"
  (e.g. "9 + 12 + cycle# + delta + FIRES = 23 sliders") — that arithmetic is off by one.
  We use **24** because that matches the math (24 sliders are emitted).
- **Primitive list:** The corpus primitives file lists 9 (attestation,
  audit_evidence, continuous_adaptive, cryptographic_identity, declarative_policy,
  immutability, least_privilege, segmentation, trust_chain) — exactly the 9 the
  spec calls for. The internal-big-picture skill text mentions a 10th
  (self-describing) but the corpus file is the source of truth for this artifact.
- **FIRES definition:** Bool, true iff `delta_d > 0`. (Verification metric fires
  iff geodesic distance improved for that item at that cycle.)
- **NSS axis scores** are derived from SKILL.md text patterns; scores are coarse
  (0..1 in 0.2 steps based on keyword/section hit count) but stable.
- **Vector granularity:** one vector per (skill, cycle) row = 474 rows
  (79 skills × 6 cycles). Folding to one-per-skill would
  lose the per-cycle metadata the spec asks for.
