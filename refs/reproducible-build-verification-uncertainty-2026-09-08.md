# Reproducible-Build Verification Uncertainty — Calibration Note

**Date:** 2026-09-08
**Scope:** What a "reproducible" verdict from the two-build verifier means, and its uncertainty.

---

## TL;DR

The two-build verifier (build twice, diff canonical unsigned content) answers a narrower question than it appears: did these two builds, on this host, with this toolchain, produce the same bytes for the compared surfaces? A pass is evidence, not proof.

## Thresholds

- Pass/fail is exact: any diff in compared manifests, mtree digests, or verity root hashes fails the run. No tolerance band.
- The comparison boundary is explicit — signed envelopes and machine-specific metadata are excluded, so a pass never claims those surfaces are reproducible.

## False-positive expectations

- A false pass happens when the diff surface is too narrow (excluded-but-material paths, or a verifier comparing its own manifests). The boundary list is reviewed when the build output layout changes.
- A false fail is preferable to a false pass; the verifier fails loudly.

## Ground truth

- Ground truth is a known-divergent pair: a deliberately non-deterministic input (e.g. an unpinned timestamp source) must make the verifier fail. Validation uses that, not only passing builds.

## Measurement uncertainty

- Repeated-trial discipline: a claim should hold across repeated runs before being recorded; one passing run is a data point, not a property.
- Host-to-host and toolchain-update variation are outside a single run's verdict and reported as such.

## Sources

- The edgeless-reproducible-mkosi and yubios-reproducibility-equivalents notes describe the verifier pattern this note calibrates.

## Declarative policy coverage

The verifier's comparison boundary is declared in the verification scripts; the declared boundary is the gate.

## Continuous / adaptive coverage

Verification runs on a schedule; boundary drift after layout changes is re-checked against the known-divergent pair.