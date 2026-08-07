# RSI Regime — Playbook for yubiOS

> One-page operational playbook for the whole recursive-self-improvement regime
> in yubiOS. Read first before running any RSI loop. Last updated 2026-08-07.

## What the RSI regime is

A family of skills + scripts + render pipelines that lets any corpus (skill files,
refs/*.md, git history, Linear issues, etc.) be audited, gap-mapped, and improved
through a bounded recursive loop. The regime is **manifold-aware**: the
parameter `t` lives on the Riemann sphere `S²`, not on a flat `[0,1]²` line.

## Skills in the regime

| Skill | Role in the regime |
|---|---|
| `recursive-self-improvement` | The parent skill. Flat-line RSI loop. Use when corpus is 1-D (version sequences, time series). |
| `rsi-phi-skill` | **The Fibonacci-sphere variant.** Use when corpus has azimuthal ordering. Native basis `Y_3^3 = K sin³θ · cos(3φ)`, 384 symmetric azimuthal lobes, `i = t`. |
| `hyperspherical-harmonic-curve` | The `S²` basis swap + γ(t) closed-form ridge (L=3, 16 fns, λ=1e-3) on the sphere. The math engine. |
| `learned-latent-curve` | The learned-latent curve fitter; used when the basis itself is learnable from the corpus. |
| `single-action-curve-rsi` | The atomic atom — one corpus item, one S² point, one geodesic delta per cycle. The per-hypothesis primitive-flip selector. |
| `curve-guided-rsi` | The original 79-skill flat-line loop (deprecated for sphere corpora; superseded by `rsi-phi-skill`). |
| `curve-guided-rsi-self` | Self-mode variant — applies the loop to SELF.md and SELF-CHANGELOG.md. |
| `negative-skill-space` | 12-axis qualitative sweep (Audience, Inputs, Outputs, Mode, …) — the gap-mapper upstream of any RSI cycle. |
| `parallel-deep-research` | The deep-research subagent dispatched **per cycle** in `rsi-phi-skill` self-mode (improvement-mode uses single-agent). |

## The loop in 5 steps (per cycle)

1. **Gap-map** via `negative-skill-space` on the target corpus.
2. **Hypothesis proposal** — a `parallel-deep-research` subagent is dispatched with the gap-map and the Fibonacci-sphere parameter `t = i/N`. The subagent proposes **ONE** single-action edit per cycle (the lobe whose flip reduces the geodesic distance to the ideal pole the most).
3. **Edit** — the human-approved hypothesis is applied to the SKILL.md (or any corpus item).
4. **Re-map** — recompute the corpus's coverage vectors under the current basis, project to S² via PCA top-2 + stereographic lift, fit γ(t) on the real SH basis (L=3, 16 fns), compute per-item chordal residuals.
5. **Fixpoint rule** — if no new gaps opened AND the cycle's edited primitive closed a prior gap AND no new anti-patterns appeared → terminate the loop. Else cycle+1 (cap 3 cycles in default mode).

## Hard rules (silently substituting any of these voids the audit trail)

1. **Canonical Fibonacci indexing**: `φ_golden = (1+√5)/2`. Don't swap for `π` (Vogel variant) or `(1+√5)/2·π` (Saff-Kuijlaars variant) without explicit renaming.
2. **Condon-Shortley normalization** for `Y_3^3`: `K = √(245/(64π))`. Don't drop the phase.
3. **Test BOTH `(ℓ=128, m=256)` and `(ℓ=256, m=128)` orderings** in every cycle — the skill's gate is the higher PC1+PC2 of the two.
4. **`i = t`** — Fibonacci index IS the parameter. No lookup tables.
5. **NEVER** substitute latitude-longitude for Fibonacci sampling — the ablation answers "Fibonacci vs lat-long" but they are not equivalent.
6. **Fresh-context subagent per cycle** in self-mode — cycle-2+ in main-thread context re-introduces author bias that cycle 1 mitigated.
7. **`doubt-driven-development` is a per-hypothesis supplement, not a substitute** for the fresh-context subagent.

## Math conventions (frozen across the regime)

- PCA top-2 → stereographic lift from south pole → `S²`
- Identity-init Möbius (`a=d=1, b=c=0`; 6 real DOF; FROZEN — no L-BFGS-B refinement)
- Chordal `S²` distance for residuals (PR1's per-point gap-to-curve metric)
- Real spherical-harmonic basis via explicit Legendre + cos/sin split (`L=3 → 16` functions)
- Closed-form ridge `C* = (ΦᵀΦ + λI)⁻¹ Φᵀ Z` with `λ=1e-3`
- 1-D coordinate `t` from PC1 of the centered coverage matrix, min-max scaled to `[0,1]`
- Degree weights frozen (not learnable)
- Fit gate: `PC1+PC2 ≥ 0.40`

## The 5-dim time-series library (`papers/data/series/`)

The regime produces a per-cycle fit at 5 dimensions, indexed by
`papers/data/series/INDEX.json`:

- **7-D** — `repo-refs-skill` 7-D basis (problem_statement, recommendation, …) on `refs/*.md`. Gate: PC1+PC2 = 1.0000 (boundary).
- **9-D** — `internal-big-picture` 9-D basis (attestation, trust_chain, …) on `self + docs + refs` sections. Gate: 0.4565 ✓.
- **16-D** — Real SH basis values evaluated at each item's S² point (`L=3 → 16` fns). Gate: 0.4627 ✓.
- **24-D** — 9-D primitives + 12 NSS axes + 3 metadata (size_log, age_log, is_rsi). Gate: 0.2993 ✗.
- **384-D** — Fibonacci-sphere phi basis `sin³θ·cos(mφ)` with `m=3..384` step 3 (= 384 symmetric azimuthal lobes on `Y_3^3`), with `(ℓ=128)` and `(ℓ=384)` variants tested per `rsi-phi-skill` Constraints #5. Chosen variant: `(ℓ=384, m=3, sin³⁸⁴ polar)` PC1+PC2 = 1.0000 ✓.

## Renders

| Dir | Consumer |
|---|---|
| `papers/data/curve-map-output/` | 9-D + 7-D curve maps (original `fit-full-curve-map.py` + cycle-3-refs siblings) |
| `papers/data/nd-viewer-output/` | 14-D NSS + size bucket + t/residual viewer for refs |
| `papers/data/curve-map-output-384d/` | 384-D TF-IDF curve map (legacy, kept for backwards compat) |
| `papers/data/curve-map-output-multi-corpus/` | Per-corpus curve maps (docs/refs/skills + cycle-3-refs) |
| `papers/data/drift-output/` | Cross-corpus drift detector — Möbius warps anchored on `self`, plus the cycle-3↔cycle-4 intra-corpus warp (this PR), plus the aligned-{points,curves} PNGs. |
| `papers/data/series/<dim>-D/<dim>-D/graphs/fit.png` | Per-dim Mollweide/Aitoff curve + scatter, top-5 highest-residual annotated. |
| `papers/data/drift-output/aligned-curves-from-series-keystone.png` | The 5-dim keystone diagram (this PR). Primitive guide per dim, gate status, top-3 samples. |
| `papers/data/drift-output/aligned-curves-from-series.png` | The 5-dim S² overlay plot (this PR). |

## When to use which skill

- **1-D corpus** (versions, time series) → `recursive-self-improvement`
- **Sphere-shaped corpus** (refs/*.md, deep-research outputs, skill files) → `rsi-phi-skill`
- **Single file / single edit** → `single-action-curve-rsi`
- **Self-mode** (improving SELF.md) → `curve-guided-rsi-self`
- **Just an NSS sweep, no loop** → `negative-skill-space`

## Cycle cap

3 cycles default. User can override up or down via explicit protocol.

## Sources

- Vogel 1979 / Saff-Kuijlaars 1997 (Fibonacci sphere)
- NIST DLMF (spherical harmonics, Condon-Shortley)
- The two y33 papers at `yubi-OS/yubiOS/refs/y33-fibonacci-sphere-paper-{method-equation-block,revised-passage}-2026-08-07.md`
- `learned-latent-curves-2026-08-06.tex` (the yubiOS paper this playbook operationalizes)

## Changelog

- 2026-08-07: initial playbook. Codifies the regime from this session's work — `rsi-phi-skill` added, 384-D Fibonacci-sphere variant tested, keystone diagram built.
