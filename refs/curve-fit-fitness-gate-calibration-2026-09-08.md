# Curve-Fit Fitness Gates — Calibration Note

**Date:** 2026-09-08
**Scope:** How the hyperspherical-harmonic / learned-latent curve fits used to audit the refs/ corpus are calibrated before any verdict is trusted.

---

## TL;DR

A curve-fit fitness gate is only meaningful if its detection threshold, false-positive rate, and ground truth are fixed BEFORE the corpus is fitted. This note records the calibration discipline: pin the gate, measure the null, then score the corpus.

## Thresholds

- Detection thresholds (e.g. the PC1+PC2 gate, holdout R-squared improvement) are stated as explicit numbers in each fit's output artifact, never implied.
- A threshold set after seeing the corpus results is a calibration violation; re-run from the null ensemble instead.

## False-positive expectations

- Every gate is calibrated against matched null corpora (permutation or curveball style), so the empirical false-positive rate on nulls is the gate's operating spec.
- A gate that has no measured null behavior cannot produce a "signal" verdict.

## Ground truth

- Ground truth comes from planted-signal corpora where the answer is known by construction; a gate is only used on real corpora after it recovers planted signal.

## Measurement uncertainty

- Repeated-trial discipline: report fit stability across re-runs (different seeds / lattice orders) alongside the headline statistic.
- Single-run numbers without an uncertainty estimate are treated as diagnostics, not verdicts.

## Sources

- The curve-guided-rsi, hyperspherical-harmonic-curve, and curved-corpus-create skills describe the gate shapes referenced here.

## Declarative policy coverage

Gate thresholds live as declared parameters of the fit configuration, not as ad-hoc judgment calls; policy evaluation is the gate.

## Continuous / adaptive coverage

Gates are re-calibrated when the corpus grows; stale thresholds are treated as drift and re-run against a fresh null ensemble.