# Point-to-point latent map [SOLO]

Date: 2026-09-06
Source: ideate-solo (no dialogue)
Scope class: systemic (architecture: proof → tool → deployable)
Variations generated: 7
Finalist: V4 "Proof-carrying point map" (with V5 as MVP cut, V6 as v2 channel)

## Problem Statement

How might we take the Lean-checked identities of `CurvedCorpus.lean` (atom Δ≥0, linear composition, curveball trades stay on the fixed-margin fibre, uniform is the unique stationary law, heat exponents, MH flux symmetry) and the compass's designed Metropolis-on-Φ dynamics, and turn them into a mapping that (a) places every point of an *unlabeled* latent cloud (no primitive names, no slugs) on the audit sphere and (b) defines point→point edges (atom moves, null trades, geodesic bridges) that each carry a runtime-checkable certificate, running as one dependency-free TS module in a Cloudflare Worker and in the browser?

## Ingest that shaped the variations

- Lean file proves *identities only*; the scope block explicitly disowns measurement claims. So a deployable can honestly "enforce" the theorems as runtime assertions (D2 `rsi-descent` already does this for Δ≥0) but must never claim the null is adequate or the effect genuine.
- D6 `injective-mapping`: 2286 items → 176 measurement classes; even slugs collide (2169 distinct); only the row ordinal is injective. Point-to-point on measurement alone is class-to-class. Identity has to be a separate layer.
- Compass: all measured quantities are properties of a *designed* chain on a *measured* ladder; binary `{0,1}^{N×d}` is the admitted state, continuous data must be binarized under a stated rule; never compare V₂ across d.
- papers/README Part II: slerp is the geodesic interpolant the program already implies; the SH basis diagonalizes diffusion so defocus is closed-form on the spectrum; forward diffusion is the map Q → N₀.
- sos-agent (deploy target): already has PCA2 → stereographic lift → SH ℓ≤3 ridge fit, NSS cells, learned binary basis. Gap vs papers: it uses a **column-permutation** null, not the fixed-margin curveball null the Lean file certifies. Its "latent" is bag-of-terms clusters, not embeddings.

## Variations

| # | Lens | Name | One line | P | S | D | T | Σ |
|---|---|---|---|---|---|---|---|---|
| V1 | Inversion | Null-first map | Place the fixed-margin fibre (the vacuum) first; every item is rendered as its deflection from the null, never as an absolute position | 3 | 3 | 4 | 4 | 14 |
| V2 | Constraint removal | RSGM in WebGPU | Full Riemannian score-based reverse diffusion in-browser; the lens run backward | 3 | 2 | 4 | 1 | 10 |
| V3 | Audience shift | SMB "is this X" | Stable Orbit client drops any CSV/embedding dump, gets a null-standardized map; zero yubiOS vocabulary | 4 | 4 | 2 | 4 | 14 |
| V4 | Combination | Proof-carrying point map | D6 identity layer + median-binarized latent + S² placement + three edge types (atom / curveball trade / slerp bridge), each edge emitting a certificate that names the Lean theorem it shadows; single TS module for Worker + browser | 5 | 4 | 5 | 5 | 19 |
| V5 | Simplification | Static sphere | One HTML file: paste vectors → binarize → k-shell → S² → geodesic gap → next atom. No null, no LLM, no DB | 3 | 5 | 1 | 5 | 14 |
| V6 | Combination | Continuous slerp channel | Skip binarization; unit-normalize to S^{D−1}, edges are slerps, concentration is vMF κ; only Δ≥0 on geodesic distance is certifiable | 4 | 3 | 3 | 3 | 13 |
| V7 | Inversion | Hamming-native map | Drop S²; live on H(d,2) shells with the Krawtchouk spectrum (Lean §14 `heat_exp_dominates_hamming`) | 3 | 2 | 4 | 4 | 13 |

P = painkiller, S = switching cost (higher = easier), D = defensibility, T = testability. Threshold 8: nothing dropped.

Outlier justifications:
- V4 P=5: the recurring pain in the program is *claims outrunning evidence* (retracted z=−45.8, PR #202 templated patches, unexecuted A₁ null). A map that refuses to draw an edge without a passing certificate attacks that pain directly.
- V4 D=5: nobody else has a Lean-anchored corpus-audit tool; the identity/measurement wall is the moat.
- V2 T=1: WebGPU score training on N≈2000 atomic points needs kernel-smoothed targets first (G5 risk), months of work before the first honest number.
- V5 D=1: it's a visualization; anyone can rebuild it in an afternoon.

## Finalists, stress-tested

**V4 Proof-carrying point map**
- Strongest critique: binarization is a *design choice*. "Unlabeled latent → 9 bits by per-axis median" is a stated rule, but a different rule gives a different fibre and a different null. The certificates are only as strong as the rule is explicit. Mitigation: the rule is part of the map's key (hash of `{d, axis-selection, threshold}`) and printed on the artifact.
- Second-order: once edges carry certificates, the natural next step is a Rekor-style log of certificates (audit-evidence-packaging composes). Bad second-order: certificate theater, 100% pass rates because the checks are identities (compass red flag: "100+ lenses all verdict YES"). Mitigation: certificates split into *identity* checks (must always pass; a fail is a code bug) and *measurement* checks (curveball z, PC1+PC2 gate) that may honestly fail.
- Un-testable bet: that a median-binarized embedding cloud produces a **non-degenerate** curveball null (the membership condition). Actually testable, and cheaply: run the null and look at SD₀. Pre-register: if SD₀[V₂] < 1e-3 the coordinate is inadmissible and the app says so.

**V1 Null-first map**
- Critique: it's an ordering discipline, not a product; folded into V4 as "render the fibre statistics before the items."
- Un-testable bet: none beyond V4's.

**V3 SMB audience**
- Critique: the SMB user doesn't care about Φ ladders; they care about "is my data structured or noise." That's a UX skin on V4's `/api/map` output. Keep as the Stable Orbit deployment target, not the core.

**V6 Continuous slerp**
- Critique: no fixed-margin fibre exists for continuous rows, so the only certified statement is Δ≥0 on geodesic distance; the null must be a rotation-invariant one (uniform on the sphere), which is a different (weaker) medium. Defer to v2, gate on its own admission null.

## Converged direction

V4, built as V5-first: ship the identity layer + binarization rule + S² placement + atom edges + curveball null + slerp bridge as one module, client-side first (verifies in a browser with zero infra), then mount the same module behind `/api/map` in the Worker with D1 persistence. V6 is the v2 channel behind its own admission null. V2 stays in papers/README as G5.

## Generation log

- Lenses forced outside habit: Inversion twice (V1, V7), Audience shift (V3).
- Dropped: none below 8; V2 kept in log as the long-horizon item (G5).
- Winner's un-testable bet reclassified as testable (null degeneracy check) and pre-registered into the MVP.
