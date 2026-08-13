# Fractalrabbit-Inspired Falsification Harness for `curve-rsi`

Self-contained test harness for the `curve-guided-rsi` /
`single-action-curve-rsi` pipeline. Generates a synthetic stochastic corpus
with a Python re-implementation of NSA's [`fractalrabbit`](https://github.com/NationalSecurityAgency/fractalrabbit)
(Darling 2018, three-tier stochastic mobility simulator), runs the curve-fit
+ sparse-cell pipeline, and checks three falsification tests with clear
pass/fail gates.

## Layout

| File | What it does |
|---|---|
| `fractalrabbit_sim.py` | Darling's three tiers in Python — Agoraphobic Point Process (Tier 1), Retro-preferential Process (Tier 2), Sporadic Reporting Process (Tier 3). Stdlib-only. |
| `curve_fit_pipeline.py` | The full `single-action-curve-rsi` pipeline in Python: 9-D binary coverage → PCA top-2 → stereographic projection from south pole → chordal-distance atom (Lemma 1) + 0.05×0.05 sparse-cell grid. |
| `falsification_harness.py` | Orchestrator that runs the three falsification tests (T1 basic_fit, T2 sparse_cell_recovery, T3 lemma_1_invariant). |
| `multi_seed_sweep.py` | 10-seed cross-validation sweep for robustness. |
| `results.json` | 1-seed output (seed=42, the headline run). |
| `multi_seed_results.json` | 10-seed output (the cross-validation evidence). |

## How to run

```bash
cd papers/fractalrabbit-falsification
python3 falsification_harness.py        # 1-seed run
python3 multi_seed_sweep.py              # 10-seed sweep
```

Requires `numpy` + `scikit-learn`. No Java, no Maven, no third-party
simulator binaries.

## Why a Python reimplementation instead of the Java JAR

The Sauna sandbox has no Java + Maven. The Java `fractalrabbit.jar` is a
one-shot CLI; to plant sparse cells we need programmatic access to
per-observation features, which the CLI doesn't expose. The Python
reimplementation is faithful to Darling (2018, DOI 10.13140/RG.2.2.15267.40489)
and gives us:

- Full programmatic access to per-observation primitives
- Direct sparse-cell planting (we control the 9-D vectors)
- No binary dependency, no JDK install, no Maven build step
- Reproducible across environments

Credit: Darling, R. W. R. (2018). *Retro-preferential Stochastic Mobility
Models on Random Fractals Under Sporadic Observations*. DOI
10.13140/RG.2.2.15267.40489.

## See also

- `refs/fractalrabbit-falsification-harness-2026-08-06.md` — full writeup
  with the falsification findings.
- `skills/github-yubios-KS9n5GAT/single-action-curve-rsi/SKILL.md` — the
  curve-fit math this harness tests against.

## License

Apache 2.0 (matching the original fractalrabbit license).
