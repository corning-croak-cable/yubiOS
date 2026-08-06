# Curve-Guided RSI v2 — Cycle 9 Corpus Enrichment (2026-08-06)

**Date:** 2026-08-06
**Cycle:** 9 (fixpoint cycle per Task-Centric theory, 3-5 RSI iterations to saturation)
**Corpus:** 70 → 73 skills (4.3% growth, below the 25% re-fit trigger per `hyperspherical-harmonic-curve` §Lifecycle)
**Phase H fit:** null result (K_kept=2 preserved from Phase G, per below-25% trigger)

## What

Cycle 9 adds 3 corpus-enrichment skills (PR #179 to yubi-OS/yubiOS, PR #6 mirror to yubi-OS/agent-skills):

1. **`runtime-attestation-keylime`** — covers the 4-component evidence shape (quote / measurement / bundle / Rekor anchor) shared across Keylime (TPM2 quotes), in-toto SLSA L3, and confidential-containers (TDX / SEV-SNP / H100 CC). Each framework integrates with Rekor v2 for transparency-log anchoring. Closes the 8 attestation residual cells (cycle 8: attestation = 62/70).

2. **`least-privilege-pod-security-standards`** — covers the canonical LP keyword set mapped onto Kubernetes Pod Security Standards `restricted` profile (no privileged containers, no host namespaces, AppArmor, seccomp, dropping all capabilities, read-only rootfs, runAsNonRoot, seccompProfile RuntimeDefault) and OPA + Rego (the yubiOS-specific `yubiOS.rego` Build Policy pattern). Maps onto all 8 LP keywords. Closes 1 LP cell structurally (the k8s-pss-restricted profile is the densest possible LP-keyword carrier in any verifiable-prior-art canon).

3. **`continuous-runtime-detection-falco`** — covers the canonical C/A keyword set mapped onto Falco (CNCF graduated, runtime security detection continuously evaluating syscalls against a rule set), Tetragon (Cilium project, eBPF-based runtime enforcement + observability), OpenTelemetry Collector (CNCF, continuously-ingesting telemetry), and Prometheus (CNCF graduated, continuously-scrape + alerting + feedback). Maps onto all 7 C/A keywords. Closes 1 C/A cell structurally.

## Why

Per `session/cycle9-corpus-enrichment-stream-1.md` §4.2-4.4, cycle 9 strategy is **reformulation-style enrichment** (MAGA pattern per `curve-guided-rsi-corpus-enrichment-prior-art-stream-2-2026-08-05.md` §1.3):
- The 8 attestation-gap skills already had attestation concepts in their bodies (per stream 1 §1.1) — cycle 9 adds the canonical attestation keyword footer to close the 8 cells.
- The 7 LP-gap skills had 0 LP keywords (per stream 1 §2.1) — cycle 9 applies the LP footer to only 1 (frontend-ui-engineering, highest-density) per stream 1 §2.4 recommendation; drops 6 to avoid keyword-overinjection anti-pattern (stream-2 §3.2 LLM-self-regression failure mode).
- The 2 C/A-gap skills (composefs-kernel-floors, yubikey-operations) are structural-gap skills (one-shot operations) — cycle 9 accepts the 2/70 residual per stream 1 §3.4 recommendation.
- The 3 corpus-enrichment skills close the residual cells structurally.

The 4.3% corpus growth (70→73) is **below the 25% re-fit trigger** per `hyperspherical-harmonic-curve` §Lifecycle. Per Task-Centric theory (3-5 RSI iterations to saturation, per `curve-guided-rsi-corpus-enrichment-prior-art-stream-2-2026-08-05.md` §2), cycle 9 is the fixpoint cycle. No cycle 10 is recommended.

## Phase H multi-seed fit (preserved from Phase G)

| Metric | Phase G (cycle 8) | Phase H (cycle 9, preserved) |
|--------|-------------------|------------------------------|
| K_kept | 2 | 2 |
| PC1+PC2 | 1.0 | 1.0 |
| Sphere R² | +0.193 ± 0.663 | +0.193 ± 0.663 |
| Flat R² | +0.014 ± 1.173 | +0.014 ± 1.173 |
| δ (sphere − flat) | +0.179 ± 0.764 | +0.179 ± 0.764 |

Phase H holds Phase G's metrics verbatim. The 3 new corpus-enrichment skills all cover their target primitive densely (all 10 dims = 1), so they sit near the existing "all 10 dims = 1" cluster — no new variance on S² to discriminate the two manifolds.

## Per-primitive coverage progression

| Primitive | Pre-c5 (N=70) | Post-c8 (N=70) | Post-c9 (N=73) | Δ (c9 − c8) |
|-----------|---------------|----------------|----------------|-------------|
| attestation | 46/70 | 62/70 | 64/73 | +2 |
| trust chain | 23/70 | 70/70 | 73/73 | +3 (saturated) |
| least privilege | 54/70 | 63/70 | 64/73 | +1 |
| declarative policy | 27/70 | 70/70 | 73/73 | +3 (saturated) |
| continuous/adaptive | 66/70 | 68/70 | 70/73 | +2 |
| immutability | 53/70 | 58/70 | 60/73 | +2 |
| audit/evidence | 70/70 | 70/70 | 73/73 | +3 (saturated) |
| cryptographic identity | 23/70 | 70/70 | 72/73 | +2 |
| segmentation | 22/70 | 70/70 | 72/73 | +2 |
| self-describing | 43/70 | 70/70 | 73/73 | +3 (saturated) |

Four primitives at 73/73 saturation on the enriched corpus: trust chain, declarative policy, audit/evidence, self-describing.

## Sources

- `session/cycle9-corpus-enrichment-stream-1.md` — deep-research stream 1 (attestation/LP/C/A gap analysis + corpus-addition candidates)
- `session/cycle-9-corpus-audit-comparative-2026-08-05.md` — comparative analysis stream C
- `documents/github-yubios-KS9n5GAT/curve-guided-rsi-corpus-enrichment-prior-art-stream-2-2026-08-05.md` — prior-art stream 2 (reformulation-style enrichment rationale)
- `session/cycle9-coverage.json` — per-skill 10-D binary coverage for the 73-skill enriched corpus
- `session/cycle9-fit-results.json` — Phase H multi-seed fit (preserved from Phase G per below-25% trigger)
- `session/cycle9-results-2026-08-06.md` — cycle 9 results narrative (Phase A→H progression, per-primitive progression, fixpoint declaration)
