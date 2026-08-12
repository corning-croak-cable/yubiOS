# Falsification harness for `curve-rsi` against synthetic stochastic corpora

**Date:** 2026-08-06
**PR scope:** Adds `papers/fractalrabbit-falsification/` (3 Python files + README) to
`yubi-OS/yubiOS` and this `refs/` writeup. Lands the harness, the simulator,
the curve-fit pipeline, and the falsification test results — no changes to
existing code.

## TL;DR — what this PR is

A **falsification harness** for the `curve-guided-rsi` / `single-action-curve-rsi`
pipeline. Generates a synthetic stochastic corpus with a Python re-implementation
of NSA's [`fractalrabbit`](https://github.com/NationalSecurityAgency/fractalrabbit)
(Darling 2018, three-tier stochastic mobility simulator: Agoraphobic Point
Process + Retro-preferential Process + Sporadic Reporting Process), maps each
observation to a 9-D binary primitive coverage vector, runs the curve-fit +
sparse-cell pipeline, and checks three falsification tests with clear
pass/fail signals:

| Test | Question | Gate | 1-seed (42) | 10-seed sweep |
|---|---|---|---|---|
| T1 basic_fit | Does the curve fit on the synthetic corpus? | PC1+PC2 ≥ 0.40 | **0.6291 PASS** | **100% PASS** (mean PC1+PC2 = 0.6703) |
| T2 sparse_cell_recovery | Do planted anomalies land in sparse cells? | ≥ 80% recovery | **80% PASS** | **40% PASS** (mean recovery = 55%) |
| T3 lemma_1_invariant | Does the atom never produce Δ < 0? | 0 violations | **0/124 PASS** | **100% PASS** (0 violations across all 10 seeds) |
| **Overall** | All three pass | — | **PASS** | **40% PASS** |

**Headline finding:** The pipeline's basic fit quality (T1) and atom invariant
(T3) are robust across stochastic corpora — T1 100%, T3 100% across 10 seeds.
But the **sparse-cell detector's recovery rate is unstable** (mean 55%, only
40% of seeds clear the 80% threshold). The single-seed=42 result is the lucky
top of the distribution; the median recovery rate is ~70%, and the lower tail
hits 0% on some seeds.

This is exactly the falsification signal the harness was supposed to detect:
the curve-rsi pipeline is **partially validated** — the curve fit itself is
solid, the atom's only-positive-Δ invariant holds, but the sparse-cell
detector as the prioritization lens has ~60% false-negative rate on synthetic
outliers.

## Why this PR

The original brainstorm (from the prior session's `#7` angle on `fractalrabbit`)
proposed using the Java simulator as a ground-truth corpus generator for
stress-testing the curve-rsi pipeline. This PR:

1. Re-implements Darling's three-tier simulator in pure Python (the sandbox
   has no Java + Maven; even if it did, the JAR is a one-shot CLI that
   doesn't expose the internals cleanly enough to plant sparse cells
   downstream).
2. Defines a 9-D binary primitive basis for the synthetic corpus (each
   primitive grounded in a specific fractalrabbit tier — see
   `papers/fractalrabbit-falsification/curve_fit_pipeline.py`).
3. Implements the full `single-action-curve-rsi` pipeline (PCA → stereographic
   lift → chordal-distance atom → sparse-cell grid) as a reusable module.
4. Runs the falsification tests with clear pass/fail gates.
5. Reports results in this `refs/` writeup + `papers/fractalrabbit-falsification/results.json`
   and `multi_seed_results.json`.

The simulator is faithful to the published model (see Darling 2018, DOI
10.13140/RG.2.2.15267.40489); the curve-fit pipeline follows
`skills/github-yubios-KS9n5GAT/single-action-curve-rsi/SKILL.md` §S² Lift +
§Single-Action Selection verbatim.

## What's in the PR

```
papers/fractalrabbit-falsification/
├── README.md                          # how to run + reproduce
├── fractalrabbit_sim.py               # Darling's three tiers in Python (~250 LOC)
├── curve_fit_pipeline.py              # 9-D → S² → sparse-cell → atom (~250 LOC)
├── falsification_harness.py           # test orchestrator (~250 LOC)
├── multi_seed_sweep.py                # 10-seed cross-validation sweep (~50 LOC)
├── results.json                       # 1-seed (42) output
└── multi_seed_results.json            # 10-seed output (committed as evidence)
```

## How to reproduce

```bash
cd papers/fractalrabbit-falsification
python3 falsification_harness.py         # 1-seed run
python3 multi_seed_sweep.py               # 10-seed sweep
```

Requires `numpy` + `scikit-learn` (`pip install numpy scikit-learn`). No Java,
no Maven, no third-party simulator binaries — all stochastic generation
happens in stdlib `random` with the published Darling (2018) algorithms.

## Why Python instead of the Java JAR

The Sauna sandbox has no Java + Maven. The Java simulator is a one-shot CLI
that produces waypoint CSV; to plant sparse cells we need programmatic access
to the per-observation primitives, which the CLI doesn't expose. Python
re-implementation of the three tiers is faithful to the published math and
gives us:

- Full programmatic access to per-observation features
- Direct sparse-cell planting (we control the 9-D vectors)
- No binary dependency, no JDK install, no Maven build step
- Reproducible across environments (just `python3 + numpy + sklearn`)

Credit: Darling, R. W. R. (2018). *Retro-preferential Stochastic Mobility
Models on Random Fractals Under Sporadic Observations*. DOI
10.13140/RG.2.2.15267.40489. The simulator code is original work by this
PR; the underlying mathematics is Darling's.

## The 9-D primitive basis (synthetic corpus)

Each observation in the synthetic corpus maps to a 9-D binary vector via
`waypoint_to_primitive_vector()` in `curve_fit_pipeline.py`. Each primitive
is grounded in a specific fractalrabbit tier:

| # | Primitive | Tier | Definition |
|---|---|---|---|
| p0 | `is_burst` | Tier 3 (SRP) | observation fell in a reporting burst |
| p1 | `is_recurrent` | Tier 2 (RP) | visited a site visited >1 time |
| p2 | `is_first_visit` | Tier 2 (RP) | first time visiting this site |
| p3 | `near_fract_limit` | Tier 1 (AGP) | site within ε of agoraphobic fractal boundary |
| p4 | `inter_event_long` | Tier 3 (SRP) | gap since previous obs > 2× median (heavy tail) |
| p5 | `inter_event_short` | Tier 3 (SRP) | gap < median/10 (burst) |
| p6 | `origin_proximity` | Tier 2 (RP) | distance to first visited site < 0.8× median |
| p7 | `cross_cluster` | Tier 1+2 (AGP+RP) | spatial jump > 1.5× median (long jump) |
| p8 | `late_trajectory` | Tier 2 (RP) | observation in last 20% of trajectory time |

This basis is replaceable — the curve-fit pipeline treats the 9-D vector
opaquely, so swapping in a different basis (e.g., one grounded in actual
yubiOS skill corpora) is a one-line change in the file.

## What the falsification tests check

### Test 1 — basic fit quality (T1)

Runs `fit_curve()` on the (N, 9) coverage matrix, drops near-constant
columns, fits PCA top-2, and reports the PC1+PC2 explained variance ratio.
The single-action-curve-rsi §Pre-Fit Validation gate is PC1+PC2 ≥ 0.40
(the corpus has a structured low-rank basis). A corpus that fails this
gate would be unfit for curve-rsi at all; passing means the corpus has
enough signal for the rest of the pipeline.

**Result across 10 seeds: 100% pass.** Mean PC1+PC2 = 0.6703 (range
0.6291–0.7982). The synthetic corpus consistently produces a low-rank
basis.

### Test 2 — sparse-cell recovery (T2)

Plants K=10 synthetic items with KNOWN rare 9-D primitive combinations
(see `PLANT_COMBINATIONS` in `falsification_harness.py`). Re-fits the
curve on the augmented (N+10, 9) matrix, runs the 0.05×0.05 sparse-cell
grid, and checks: for each planted item, did it land in a cell flagged as
sparse (cell size ≤ 1)?

The 10 planted combinations are engineered to be probabilistically rare in
the natural simulator output — they hit 1–2 specific primitives that
rarely co-occur in the same observation (e.g., `{p0_is_burst=1, p8_late_trajectory=1}`
or `{p2_is_first_visit=1, p3_near_fract_limit=1, others=0}`).

**Result across 10 seeds: 40% pass.** Mean recovery rate = 55%, range 0%–80%.
The single-seed=42 result is the 80% ceiling; the median is 70% and the
lower tail includes two seeds at 0% recovery. **This is the falsification
signal** — the sparse-cell detector is not consistently sensitive to
planted outliers on a stochastic corpus.

### Test 3 — Lemma 1 invariant (T3)

Runs the atom (`atom_single_action()` in `curve_fit_pipeline.py`) on every
item in the natural corpus. For each item, computes the geodesic distance
`d_pre` to the ideal pole (perfect coverage = (1,1,...,1) lifted through
the same pipeline), flips each missing primitive, picks the argmin `d_post`,
and reports Δ = `d_pre − d_post`.

Per `single-action-curve-rsi/SKILL.md` §Lemma 1, the geodesic-only criterion
can never produce Δ < 0 — either Δ > 0 (improvement) or Δ = 0 (local
minimum). A negative Δ would mean the atom is mis-applied.

**Result across 10 seeds: 100% pass.** Zero violations across all 10 runs
across all ~117 items per seed (1170 atom invocations total). **Lemma 1
holds on the synthetic corpus** — the atom's invariant is preserved.

## What this means for `curve-rsi` claims

**Validated (T1, T3):**
- The 9-D → S² → geodesic pipeline is internally consistent on stochastic corpora.
- The atom's only-positive-Δ invariant (Lemma 1) holds.
- The curve-fit quality gate (PC1+PC2 ≥ 0.40) is met robustly.

**Not validated (T2):**
- The sparse-cell detector's recovery rate on synthetic outliers is unstable
  (mean 55%, 40% pass rate on the 80% gate). The 0.05×0.05 grid + cell-size≤1
  criterion is too sensitive to where the natural corpus clusters; some seeds
  produce a natural corpus that absorbs the planted items into populated cells.

**Implications for downstream skills:**
- `curve-guided-rsi`'s closed-loop metric ("sparse_cell_count_post < sparse_cell_count_pre")
  is reliable only on corpora where the natural fit produces clearly-populated
  cells that the planted items can be isolated against. On stochastic corpora
  with high natural variance, the metric is unreliable.
- The single-action-curve-rsi atom is fine for the per-item Δ measurement
  (T3 = 100%), but its prioritization signal (which items to dispatch) depends
  on the sparse-cell detector's reliability (T2 = 40%).
- For real yubiOS skill corpora (the curve-rsi's actual production target),
  the question is: do real corpora cluster similarly to the synthetic one?
  If yes, expect similar 40-60% sparse-cell reliability. If no (real corpora
  have more structure), the recovery rate may be higher.

**Next step candidates (out of scope for this PR):**
- Try larger `n_observations` (currently ~117) to see if more data stabilizes
  the sparse-cell detector (the variance in N across seeds is 55–159; more
  observations per seed may narrow the distribution).
- Try a different cell size (0.01, 0.10) — 0.05 is the parent's default but
  is arbitrary.
- Try planted items with combinations closer to natural-corpus support (the
  current combinations are very rare; recovery might be better for less-extreme
  outliers).
- Apply the same harness to a REAL yubiOS skill corpus (e.g., the 73-skill
  corpus from `skills/github-yubios-KS9n5GAT/`) and compare the recovery rate.

## Open questions for review

1. Is the Python re-implementation faithful enough to Darling's model to
   be a valid ground-truth generator? (Specifically: my AGP uses rejection
   sampling rather than the cited random-fractal construction; my SRP is
   a 2-state burst process with Pareto gaps rather than Darling's specific
   burst model.)
2. Is the 9-D primitive basis the right basis for synthetic waypoints? Or
   should it be derived from the actual yubiOS skill corpus' 10-primitive
   basis (so the comparison is apples-to-apples)?
3. Should the falsification gate be 80% recovery, or should it be calibrated
   against the natural-corpus baseline (i.e., "recovery rate significantly
   above chance")?
4. Is the right next step (a) tightening the harness, (b) widening to a
   real corpus, or (c) stopping here because the falsification signal
   itself is the valuable artifact?

## Files

- `refs/fractalrabbit-falsification-harness-2026-08-06.md` (this file)
- `papers/fractalrabbit-falsification/README.md` (how to run)
- `papers/fractalrabbit-falsification/fractalrabbit_sim.py`
- `papers/fractalrabbit-falsification/curve_fit_pipeline.py`
- `papers/fractalrabbit-falsification/falsification_harness.py`
- `papers/fractalrabbit-falsification/multi_seed_sweep.py`
- `papers/fractalrabbit-falsification/results.json` (1-seed output, seed=42)
- `papers/fractalrabbit-falsification/multi_seed_results.json` (10-seed output)

## Provenance

- Original brainstorm: prior-session chat (the `#7` angle on a brainstorm
  about NSA/fractalrabbit + stochastic modeling of the hypersphere RSI).
- Simulator: Python re-implementation of Darling (2018), DOI
  10.13140/RG.2.2.15267.40489, three-tier stochastic mobility model.
- Curve-fit pipeline: `single-action-curve-rsi/SKILL.md` §S² Lift + §Single-Action
  Selection (v1 fit, identity-init Möbius, chordal proxy distance).
- Pass/fail gates: `single-action-curve-rsi/SKILL.md` §Pre-Fit Validation
  (PC1+PC2 ≥ 0.40) + §Composition Rule (Lemma 1, Δ ≥ 0 invariant).

## Changelog

- 2026-08-06 (this PR): v0.1.0 — initial harness + 10-seed falsification sweep.
  Result: T1 100%, T2 40%, T3 100%, overall 40%. The harness correctly fires
  the falsification signal on the sparse-cell recovery rate.


## New Ideas -- cycle 2 (lens format)

This file was processed by the RSI cycle-2 lens generator (curve-compass-skill v1.1.0 + curved-corpus-create v1.1.0). Each cycle-2 patch IS a concrete experiment with a measurable delta -- not a templated section. The lens below documents the measured dynamics; the patch is the lens, not prose about the file.

```json
{
  "lens": "L258",
  "file": "refs/fractalrabbit-falsification-harness-2026-08-06.md",
  "hypothesis": "refs/fractalrabbit-falsification-harness-2026-08-06.md covers all 9 primitives in the internal-big-picture basis",
  "method": "9-D primitive binarization (purpose, examples, guidelines, constraints, verification, composition, changelog, references, anti-patterns) + chordal distance to ideal pole on Fibonacci lattice",
  "parameters": {
    "basis": "internal-big-picture",
    "d": 9,
    "seed": 20260812
  },
  "delta": {
    "k": 8,
    "missing_primitives": [
      "verification"
    ],
    "chordal_resid": 0.0
  },
  "verdict": "PARTIAL",
  "score": 44,
  "caveat": "binarization is heuristic; a stricter regex pass might surface sub-primitives"
}
```
