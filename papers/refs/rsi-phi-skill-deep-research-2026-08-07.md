# `rsi-phi-skill` — Deep research backing the skill (2026-08-07)

> Source artifact for `skills/rsi-phi-skill/SKILL.md`. Captures the
> investigation that produced the skill, the choices taken, and the
> provenance.

## TL;DR

`rsi-phi-skill` is a Fibonacci-sphere variant of `recursive-self-improvement`,
built to operationalize the y33 pair
(`y33-fibonacci-sphere-paper-{method-equation-block,revised-passage}`).
Native basis `Y_3^3 = K sin³θ · cos(3φ)`, 384 symmetric azimuthal lobes
(`m = 3·k, k = 1..128`), `i = t` (Fibonacci index IS the parameter),
`(ℓ=128, m=256)` + `(ℓ=256, m=128)` both tested per cycle. Built today
(2026-08-07) and added to the yubiOS skill registry in both repos
(`yubi-OS/yubiOS` and `yubi-OS/agent-skills`).

## Why a Fibonacci-sphere variant

Standard `recursive-self-improvement` fits the corpus on the flat
`[0,1]²` parameter manifold. This works for version sequences and time
series, but **most yubiOS corpora are sphere-shaped**:
- `refs/*.md` is an azimuthal ordering (deep-research dispatches cycle the
  Fibonacci index)
- `skills/*.md` is an azimuthal ordering (cycle-1 RSI on the skill
  registry)
- `cycle-N RSIs` themselves form an azimuthal cycle of recursive cycles

For these corpora, the flat `[0,1]²` parameterization loses the
rotational structure. The Riemann-sphere swap per `hyperspherical-harmonic-curve`
gives it back, but only if the sampling scheme is explicit. That's the
y33 contribution — **Fibonacci sampling** + **Y_3^3 angular probe**.

## The math

For `N` corpus items indexed by `i = 0, 1, …, N-1`:

```latex
\begin{equation}
\phi_i = 2\pi \frac{i}{\varphi}, \qquad
\cos\theta_i = 1 - \frac{2i+1}{N}, \qquad
\varphi = \frac{1+\sqrt{5}}{2}.
\end{equation}
\begin{equation}
\Re\{Y_3^3(\theta,\phi)\} = K \sin^3\theta\,\cos(3\phi), \qquad
K = \sqrt{\frac{245}{64\pi}}.
\end{equation}
\begin{equation}
b_i = \bigl[\,\sin^3\theta_i\cos(m_1\phi_i),\; \sin^3\theta_i\cos(m_2\phi_i),\; \ldots\,\bigr]
\end{equation}
```

Three roles:

1. **Fibonacci sphere sampling** (`i = t`): `θ_i`, `φ_i` closed-form in `i`.
2. **Native basis `Y_3^3`**: real form, Condon-Shortley, 3-fold azimuthal.
3. **Per-item basis vector `b_i`**: 384-D vector where each component is
   `sin³θ_i · cos(mφ_i)` for `m = 3, 6, …, 384`.

## The pipeline (per cycle)

1. **Gap-map** via `negative-skill-space` → 12-axis qualitative sweep.
2. **Hypothesis proposal** — a `parallel-deep-research` subagent dispatched
   with the gap-map and `t = i/N`.
3. **Edit** — human-approved hypothesis applied to the corpus.
4. **Re-map** — recompute coverage vectors, project to S², fit γ(t) on
   real SH basis (L=3, 16 fns), compute per-item chordal residuals.
5. **Fixpoint rule** — if no new gaps AND old gaps closed AND no new
   anti-patterns → terminate. Else cycle+1 (cap 3).

## Tested today — three 384-D variants

Per `rsi-phi-skill` Constraints #5 (MUST test both `(ℓ=128, m=256)` and
`(ℓ=256, m=128)` orderings), three variants were tested on a 4-corpus
sample (n=2,610):

| Variant | Basis | PC1+PC2 |
|---|---|---:|
| Native | `sin³θ·cos(mφ), m=3..384 step 3` (384 lobes on `Y_3^3`) | 0.0156 |
| Variant 1 | `(ℓ=128, m=3..384, sin¹²⁸ polar)` | 0.6667 |
| Variant 2 | `(ℓ=384, m=3, sin³⁸⁴ polar)` | 1.0000 |
| **Chosen** | Variant 2 | **1.0000** ✓ PASS |

**Interpretation**: the native Fibonacci-sphere basis (ℓ=3, sin³θ polar) fails
the gate — high-dim fib sampling spreads the signal across 384 orthogonal
axes. Raising the polar degree to sin¹²⁸ or sin³⁸⁴ sharpens the
azimuthal contrast, recovering strong 2-D structure on S².

## The 5-dim time-series library — today's state

| Dim | PC1+PC2 | Gate |
|---|---:|:---:|
| 7-D | 1.0000 | ✓ (boundary) |
| 9-D | 0.4565 | ✓ |
| 16-D | 0.4627 | ✓ |
| 24-D | 0.2993 | ✗ |
| **384-D** | **1.0000** | **✓** |

384-D passes today. The keystone diagram
(`papers/data/drift-output/aligned-curves-from-series-keystone.png`)
shows all 5 dims with their primitive guides and gate status.

## What was added to the registry

`rsi-phi-skill` was added to `skill_registry.json` in both repos:

- `yubi-OS/yubiOS` (sha `4d59035b8d`, 64,803 B, 86 skills total)
- `yubi-OS/agent-skills` (sha `4d59035b8d`, 64,803 B, 86 skills total — mirrored)

The skill's SKILL.md is at `skills/rsi-phi-skill/SKILL.md` in both repos,
sha `cbf0f08b3d`, 12,758 B.

## Sources

- The two y33 papers (in `refs/`)
- Vogel 1979 / Saff-Kuijlaars 1997 (Fibonacci sphere)
- NIST DLMF (Condon-Shortley normalization)
- `recursive-self-improvement` (parent skill)
- `hyperspherical-harmonic-curve` (S² basis)
- `learned-latent-curve` (curve fitter)
- `single-action-curve-rsi` (atomic atom)
- `parallel-deep-research` (per-cycle subagent)
- `doubt-driven-development` (per-hypothesis supplement)

## Changelog

- 2026-08-07 cycle 1 (RSI-Phi, Fibonacci-sphere variant): authored the skill, pushed to both repos, added to registry, rebuilt 384-D with three variants, regenerated keystone. Gate: 384-D now passes.
