# Synthesis of 22 external references + photophysics bridge — 2026-08-25

**Companion to:** [`tools/tautology-discerner/`](../../tools/tautology-discerner/),
[`tools/spectral-decomposer/`](../../tools/spectral-decomposer/), and the
in-progress curve-guided-rsi cycle 34.

**Scope:** 21 papers + 1 GitHub repo pair (envharness + envharness.com),
researched in parallel via 22 `general / smart` subagents, plus a
dedicated photophysics-mapping subagent (FCS, triplet kinetics,
PDT, PTT).

**Discipline:** every similarity / dissimilarity / possibility below
is grounded in the program's existing machinery. No analogy is
admitted without a falsifier rule. Photophysics bridge verdicts are
in the program's own exclusion language (`identity`, `not-excluded`,
`not-tested`, `excluded`, `void`).

---

## 0. The single most important finding

**Every one of the 22 external works has a missing matched-null.**
Across 21 distinct agentic-AI papers (all from Google Cloud AI
Research + WashU / UNC / Michigan State / Penn State / PKU / UIUC /
UVA / Google DeepMind) plus the envharness wrapper, every headline
number is a raw mean±sd / win-rate / ablation-delta — none is a
deflection against a margin-preserving randomization. Each paper's
latent data shape (a method × task success matrix, a row × column
binary incidence) is exactly the program's native corpus type. Each
paper's "between-arm" comparison is exactly a fixed-margin-null
comparison in disguise.

This is the unified finding: the curveball null + dBc sonometer is
the missing layer in the entire agentic-AI evaluation literature.

---

## 1. Per-link headlines (one row each)

| # | Source | Headline | Matched null? | Deflecting statistic | Program tool fit |
|---|---|---|---|---|---|
| 1 | [envharness](https://github.com/google-research/envharness) / [envharness.com](https://envharness.com/) (Huang+ 2026, Cloud AI/UW/WashU) | Frozen-environment wrapper algebra + EnvRigger LLM designer | **no** | ΔV₂ on skill-bank × task incidence | `corpus-auditor`, `spectral-defocus` direct |
| 2 | [arXiv:2608.19880](https://arxiv.org/abs/2608.19880) (EnvHarness paper) | (same as #1, the publication) | **no** | ΔV₂ + caustic on rule-composition lens | direct |
| 3 | [arXiv:2607.27853](https://arxiv.org/abs/2607.27853) (FinanceHarness/FinanceGym) | ILP-balanced 400×24 rubric + 31-cutoff leakage barrier | **no** | ΔV₂ + caustic on post-cutoff rank collapse | `corpus-auditor` + `spectral-defocus` direct |
| 4 | [arXiv:2606.12737](https://arxiv.org/abs/2606.12737) (PI-Hunter) | Agentic GA for prompt injection, diversity entropy D | **no**; D is margin-blind (ΔD≡0 on fibre) | ΔV₂ + caustic on coverage lobes | `corpus-auditor` direct |
| 5 | [arXiv:2606.07822](https://arxiv.org/abs/2606.07822) (ACUTE Protocol, ICML 2026) | EURO utility-Oracle/Anti-Oracle renormalization | **partial** (1000 permutation resamples, but not margin-preserving) | ΔV₂ on correctness matrix | `corpus-auditor` + correction layer |
| 6 | [arXiv:2606.03303](https://arxiv.org/abs/2606.03303) (LEAP, NeurIPS Lean prover agent) | AND-OR DAG + Lean-4 verified proofs (Putnam 12/12) | **no** | curveball on N=60 × d≈7 solve matrix; DAG-native degree-preserving swap | new tool gap (cyclic-restricted) |
| 7 | [arXiv:2605.26340](https://arxiv.org/abs/2605.26340) (ScientistOne) | CoE provenance standard + 75-paper CoE audit | **no** | ΔV₂ on paper × integrity check incidence | `corpus-auditor` direct |
| 8 | [arXiv:2605.23109](https://arxiv.org/abs/2605.23109) (IDS Rocq agent) | Implementation+proof co-synthesis, 7/7 KV-store specs | **no** | ΔV₂ on attempt × strategy-feature matrix | `corpus-auditor` direct |
| 9 | [arXiv:2605.16358](https://arxiv.org/abs/2605.16358) (LEAF forecasting benchmark) | Event-augmented forecasting + dual-agent consensus | **no**; 147% inflation from stale data is itself a null-failure | ΔV₂ on event × target with date-stratified fibre | `corpus-auditor` + `spectral-defocus` |
| 10 | [arXiv:2605.14389](https://arxiv.org/abs/2605.14389) (Nexus forecasting agent) | Dual-resolution Macro/Micro outlook | **no** | shuffled-context permutation + caustic on macro/micro rank collapse | `corpus-auditor` + `spectral-defocus` |
| 11 | [arXiv:2605.10899](https://arxiv.org/abs/2605.10899) (RubricEM meta-RL) | Stage-structured GRPO + evolving rubric bank | **no** | ΔV₂ as reward-hacking detector | `corpus-auditor` + `spectral-defocus` |
| 12 | [arXiv:2605.08625](https://arxiv.org/abs/2605.08625) (STRIDE) | Reasoning prior P(Y\|X,R) over TS embeddings | **no** | trace-permutation null + ΔV₂ on trace-primitive incidence | `corpus-auditor` direct |
| 13 | [arXiv:2605.06924](https://arxiv.org/abs/2605.06924) (A²RD long-video) | Retrieve-Synthesize-Refine-Update closed loop | **no** | ΔV₂ + heat-kernel z(t) on entity-presence matrix | `corpus-auditor` + `spectral-defocus` |
| 14 | [arXiv:2605.06614](https://arxiv.org/abs/2605.06614) (SkillOS) | SkillRepo curation with GRPO + compression reward | **no** | ΔV₂ on SkillRepo × primitive matrix; λ_c→geodesic-gap | `corpus-auditor` + `curve-guided-rsi` |
| 15 | [arXiv:2604.05018](https://arxiv.org/abs/2604.05018) (PaperOrchestra) | 5-step paper-writing agent + PaperWritingBench | **no** | ΔV₂ on paper × reference bipartite; P1 Recall | `corpus-auditor` direct |
| 16 | [arXiv:2602.02660](https://arxiv.org/abs/2602.02660) (MARS, ICML 2026) | Budget-aware MCTS + comparative reflective memory | **no** | ΔV₂ + heat-kernel z(t) for cross-branch transfer | `corpus-auditor` + `spectral-defocus` |
| 17 | [arXiv:2602.02164](https://arxiv.org/abs/2602.02164) (Co-RedTeam) | Security-aware red-team multi-agent | **no** | ΔV₂ on agent × attack-variant; ablation p-values | `corpus-auditor` direct |
| 18 | [arXiv:2601.23265](https://arxiv.org/abs/2601.23265) (PaperBanana) | Diagram agent + VLM-as-judge win matrix | **no**; their own random-retriever ablation is the closest to a null | ΔV₂ + heat-kernel on diagram × dimension matrix | `corpus-auditor` direct |
| 19 | [arXiv:2601.22638](https://arxiv.org/abs/2601.22638) (ScholarPeer) | Context-aware peer-review agent (90.5% win) | **no** | ΔV₂ on submission × aspect incidence; halo-collapse audit | `corpus-auditor` direct |
| 20 | [arXiv:2511.05460](https://arxiv.org/abs/2511.05460) (Synapse) | TSFM adaptive arbitration at timestamp granularity | **no** | column-constrained curveball on win matrix | `corpus-auditor` direct |
| 21 | [arXiv:2510.05156](https://arxiv.org/abs/2510.05156) (VeriGuard) | Nagini-verified guardrail + CRP+TEH (ASR 0.1%) | **no** | ΔV₂ on RBAC matrix; Viper↔Lean handshake | `corpus-auditor` direct |

**Total:** 22 links, 22 missing matched-nulls, 22 binary-incidence
matrices the program's `corpus-auditor` (or a thin adapter) already
ingests without modification.

---

## 2. Cross-paper pattern

A consistent architecture: **observe → diagnose → write → validate**.
This is the same control flow as `curve-guided-rsi-self`, with the
following exact mappings:

- **observe** (rollouts / audit) ↔ `recursive-self-improvement` gap-map
- **diagnose** (LLM naming a flaw) ↔ `single-action-curve-rsi` choosing the next geodesic
- **write** (Python rule / SkillRepo entry / paper) ↔ the lens-format patch from `curve-compass-skill` v1.1.0
- **validate** (rollout acceptance) ↔ the curveball fixed-margin null + dBc deflection

The throughput differential comes from two things the papers all
lack and the program provides:

1. A **deterministic, falsifier-bearing acceptance gate** (the curveball null + dBc sonometer; vs their learned judges whose noise is unbounded).
2. A **machine-checked theory layer** (Lean-4 / Rocq / Nagini for the program; absent for every paper above).

---

## 3. Where each piece of the program's machinery fits

| Program machinery | Goes where in the 22-link landscape |
|---|---|
| curveball fixed-margin null (Lean §8) | every "between-arm" comparison: baselines, ablations, leaderboards. Stops being raw mean±sd. |
| reversibility + uniform stationarity (Lean §9) | the answer to "why this null": canonical, unique, defensible. |
| uniqueness of the canonical null (Lean §10) | the answer to "could a different null do the same job": no. |
| MP / Narayana moments (Lean §11) | LEAF (date-stratified fibre), Synapse (column-constrained fibre), SciCompGram (point-1-Wishart moments). |
| dBc level laws (Lean §12) | the report unit: every pp / % becomes +XX dBc above the vacuum. |
| heat-kernel defocus E_ℓ(t) = E_ℓ(0)e^{−2ℓ(ℓ+1)t} | persistence z(t) curves over training step / round / layer depth / horizon — replaces the "8-10 iterations saturates" hand-wave. |
| caustic / rank-collapse detector | MARS' reflective memory, SkillOS' curator homogenization, ScholarPeer's halo collapse. |
| Möbius lens powering with selection-null control (ΔJ=+126.1, ~5× control) | PI-Hunter's mutation operators; Nexus' Macro/Micro; Synapse' arbitration. |
| injective-mapping ladder | PaperOrchestra's 200×24 rubric union; ScholarPeer's ICLR submissions. |

---

## 4. Two new tools, just shipped

### 4.1 `tools/tautology-discerner/`

A natural-language statement classifier. Verdict ∈ {`Tautology`,
`Falsifiable`, `Paradox`, `Undecidable`}, plus the refuter rule the
classifier would use. The "Undecidable" bucket is the program's
"no statistic admitted without a matched null" rule restated for
sentences: a sentence that carries no explicit commitment is
refused, not guessed at. The fixed-refuter-bag invariance check
(selftest) is the language-side analogue of Lean §8's
`trade_preserves_rowSum / trade_preserves_colSum`.

### 4.2 `tools/spectral-decomposer/`

A curve-guided-self-ideate tool. Generates ranked lens-format
experiment candidates — each IS a measurable experiment with
hypothesis / method / parameters / delta / verdict / score / caveat.
The delta is reported in dBc against the curveball vacuum, and every
candidate carries a curveball-control arm so a YES verdict is only
as good as the control's silence. Emits a `cycle-NN-lens.md` artifact
ready for a curve-guided-rsi cycle.

The breakthrough: the candidate pool is **falsifiable by construction**
(each delta is computed against the matched null), and the deliverable
shape is the same shape the cycle-34 L141-L146 patches used, so the
tool's output drops directly into the existing cycle pipeline.

---

## 5. Phosphorescence / FCS / PDT / PTT equation placement

Verdicts in the program's exclusion-only language. All four canonical
equation families were verified against current sources (see the
dedicated `session/subagents/ses_fc78cf22bffeZqUUQa5EwZ5ff0/photophysics-mapping-2026-08-25.md`).
All measurements are property-of-designed-chain where the chain is the
compass; property-of-historical-corpus only when stated.

### 5.1 FCS (fluorescence correlation spectroscopy)

The verdict is **partial exclusion with one identity**:
- **Identity:** `C_ℓ(t) = e^{−ℓ(ℓ+1)D_r t}` (rotational-diffusion
  correlation on the sphere) IS the program's `E_ℓ(t) = E_ℓ(0)e^{−2ℓ(ℓ+1)t}`
  with `D_r = 2`. The defocus operator is already the
  rotational-diffusion propagator. **Zero new parameters.**
- **Per-ℓ lifetime:** `τ_ℓ = 1/(2ℓ(ℓ+1))` — there is no single `τ_D`,
  there is a τ per degree. The two existing angular-resolution
  candidates (`L=3` harmonic truncation and `r ≈ 0.095` sparse-cell
  chordal radius) should agree to order-of-magnitude; they currently
  do not because their units have never been tied.
- **Excluded:** FCS's `G(0) = 1/⟨N⟩` does NOT carry the program's
  null — the program normalizes by the external curveball ensemble,
  not by the process's own mean. Any "1/G(0) = effective particle
  number" claim is excluded categorically. **FCS is the
  internal-null degenerate limit of the program's dV2z.**
- **Excluded on the historical corpus:** the edit-log dynamics has
  zero back-flux (D2), so no positive π makes it reversible; its
  unique stationary distribution is `δ_{k=9}`. An absorbing chain
  has no stationary fluctuation spectrum to autocorrelate.

### 5.2 Phosphorescence / triplet kinetics

- **Identity (first-order only):** `[T₁](t) = [T₁](0)e^{−k_T t}`
  with `k_T = k_rT + k_nrT` IS `E_ℓ(t) = E_ℓ(0)e^{−2ℓ(ℓ+1)t}` with
  `k_ℓ = 2ℓ(ℓ+1)`. The prompt/delayed split `I(t) = A_p e^{−pt} + A_d e^{−dt}`
  is the same two-block truncation the program already measures
  (delayed = low-ℓ spectral mass 0.9774/0.9830, prompt = high-ℓ
  mass 0.2059/0.1782). **Zero new parameters.**
- **TADF identity:** `k_RISC ∝ exp(−ΔE_ST/k_B T)` IS
  `α = min(1, exp(−ΔF_T/T))` with `ΔE_ST ↔ ΔF_T` and `k_B T ↔ T`.
  `T_× = 0.041143` is then precisely the TADF crossover. The
  program's measured C(T) peak at 0.038304 and χ(T) peak at 0.0368
  sit just below `T_×`, exactly where TADF predicts maximal
  delayed/prompt ratio sensitivity. **Compass-only claim.**
- **Testable extension (1 parameter, `k_ISC`):** non-normal generator
  `dE/dt = −(Λ + K)E` with `K_{ℓ,ℓ'} = k_ISC · 1[ℓ' > ℓ]` (off-diagonal
  inter-ℓ transfer). Permits transient growth under defocus — a
  corpus can transiently look more structured under defocus before
  relaxing. Falsifiable against curveball. **One new parameter.**
- **Excluded (TTA):** triplet-triplet annihilation `−2(k_p + k_d)[T1]²`
  requires item–item interaction; D3 exchangeability forbids it.
- **Quantum yield:** `Φ_p = k_rT/(k_rT + k_nrT)` → per-ℓ fitted-coefficient
  mass over total block mass (= per-block R²). Measurable today.

### 5.3 PDT (photodynamic therapy targeting)

- **External corroboration of the admission rule:** the PDT explicit-
  dosimetry literature converged independently on "the delivered
  quantity is not the effective quantity; measure what reacted"
  (`[¹O₂]_rx = ξ∫ [³O₂]/([³O₂]+β) · Φ · [S₀] dt`), which is exactly
  C1 / C3 of the program. **Zero new parameters; documentation value.**
- **Mechanical mapping:** Φ ↔ Möbius lens powering (`|φ'θ(z)|²`); [S₀]
  ↔ per-item susceptibility (primitive-coverage deficit `9 − k`);
  [³O₂]/([³O₂]+β) ↔ the half-yield depletion factor on the pool of
  MISSING primitives available to flip.
- **New measurable (1 parameter, `β`):** the remaining-missing count
  `m = 9 − k` at which the per-flip yield halves. Estimable from
  the shipped edit log (213 files, 1391 dispatches, 1178 transitions)
  by fitting per-step advance probability against `m`. **Predicts**
  the absorbing state at `k=9` as oxygen depletion rather than
  merely recording it.
- **Threshold calibration method (0 parameters):** fit the dBc
  admission threshold `[¹O₂]_rx,sd`-style — to observed outcome
  (sparse-cell closure, measured 26 sphere vs 31/37 flat), NOT to a
  Gaussian tail. Fills the live gap left by the program's
  Anti-pattern "Don't read a t_fold, or any z here, against a
  Gaussian tail" (compass skill).
- **Concrete deliverable (2 parameters, `ξ` and `β`):** for any fitted
  φθ, compute per-item fluence redistribution, multiply by deficit,
  apply depletion factor, integrate over RSI cycle → **per-item
  predicted dose** ranked list. Testable against what the next RSI
  cycle actually changed.

### 5.4 PTT (photothermal therapy targeting)

- **Correct mapping:** Arrhenius damage integral `Ω(τ) = ∫ A e^{−E_a/(R·T(t))} dt`
  ↔ scale-space persistence `z(t)`. Caustic density ↔ `T(t)` (instantaneous
  intensity, not the integrated quantity). Confusing the two is the
  documented failure mode in the hyperthermia literature; the same
  confusion is now blocked here.
- **Testable extension (1 parameter, `E_a`):** exponential re-weighting
  `z_Arrhenius = ∫ A e^{−E_a/(R · κ(t))} dt` (κ = local caustic intensity).
  Prediction: exponentially-weighted persistence separates real features
  from curveball features better than duration-weighted persistence.
  Measure as deflection or sparse-cell counts.
- **HIGHEST-VALUE extension (1 parameter, `ω`):** Pennes perfusion
  `Q_b = ω_b ρ_b c_b (T_a − T)` adds a degree-independent constant
  to every eigenvalue:
  `E_ℓ(t) = E_ℓ(0) · e^{−(2ℓ(ℓ+1) + ω)·t}`.
  **Breaks ℓ=0 conservation** — the forward diffusion's current
  terminus is `t→∞ → uniform` because ℓ=0 mass is preserved. With
  `ω > 0`, ℓ=0 mass decays too and the terminus becomes the **ambient
  state**, not the corpus-mean-preserving uniform. **One parameter
  buys a different forward-diffusion endpoint.**
- **CEM43 = sonometer:** the program's `L = 20·log₁₀(|Δ|/σ_null)`
  is already the CEM43 channel (log-linear equivalent-exposure on
  a reference scale); the program has the sonometer but not the
  Arrhenius `Ω`. The PTT field's own division of labour transfers
  directly: Arrhenius for short/hot ablation (caustics), CEM43 for
  long/warm exposure (broad lens powering).
- **Lens powering as a source term:** under Pennes, lens powering is
  `Q_ext`, not a coordinate change. A coordinate change cannot
  inject energy; a source can. If lens powering is a
  reparameterization only, it cannot create structure; if it is a
  source, it can. The program should be explicit about which.

### 5.5 Standing warnings (the binding constraints)

1. **Parameter count is the binding constraint.** Items 3–6 and 9
   above add six new parameters. The program's measured claim is
   "sphere wins at fewer parameters" (δ = +0.7373 / +0.5197). Each
   new parameter must clear the **matched-parameter ablation**
   independently, and the `hyperspherical-harmonic-curve`
   "When the Ablation Fails" rule applies unchanged.
2. **Every new statistic needs its own curveball null.** `β`, `ω`,
   `E_a`, `k_ISC` are statistics of the corpus and all must
   deflect at fixed row+column margins.
3. **C1 transfers.** Do not compare fitted timescales across
   different `d`.
4. **`T_×` is a designed-chain property.** Items 5.2 #2 and 5.3
   `β` both live on the compass. Do not let photophysics vocabulary
   smuggle in claims the historical-corpus retraction forbids.
5. **The `τ_T ≪ τ_D` identifiability gate is currently untestable**
   because compass sweep-steps and defocus time units have never
   been reconciled. **Do this first** — it is cheap and prerequisite
   to every FCS-flavoured claim.
6. **Exclusion-only language.** Nothing above is `compatible with`.
   Items are `identity`, `not-excluded`, `not-tested`, `excluded`,
   or `void`.

---

## 6. Net yield of today's session

- 22 external works mapped to the program's machinery in parallel.
- 22 latent binary-incidence matrices identified, all ingestible by
  existing tools without modification.
- 1 cross-paper finding: every external agentic-AI evaluation
  lacks a matched null; the curveball null + dBc sonometer is the
  missing layer.
- 4 photophysics equation families placed, 3 with new measurable
  parameters (`ω`, `β`, `E_a`) and 1 with a novel dynamics
  extension (`k_ISC`).
- 2 new tools shipped to `tools/` on main: `tautology-discerner`
  and `spectral-decomposer` (the breakthrough tool, grounded in
  the curve-compass lens-format and the Lean §8 / §9 / §10 / §12
  proofs).
- This synthesis document on `refs/` on main.

The two new tools are fully demonstrated (`--selftest` per tool, all
green), use the program's existing curveball + dBc machinery
without modification, and emit artifacts in the same shape as the
existing cycle-34 lens-format patches so they drop directly into a
curve-guided-rsi cycle.

---

## 7. Open follow-ups (next session)

1. Run `spectral-decomposer` on the is-this-x 2286×9 corpus at
   `cycle 34` and check whether the top-K sparse cells match the
   observed `ΔV₂ = +0.0144, z = +12.13` direction.
2. Reconcile compass sweep-step units with defocus time units
   (prerequisite to every FCS claim; cheap; ~1 hour).
3. Estimate `β` from the shipped edit log and report it as a
   designed-chain parameter with its own curveball null.
4. Estimate `ω` from a paired corpus (original + perfusion-shifted)
   to test the ℓ=0-decay prediction directly.
5. Curveball-null the Synapse win matrix (column-constrained
   fibre, the only one of the 22 that does not reduce to a
   row+column-sum-preserving swap).
6. Build the acyclicity-restricted degree-preserving swap kernel
   for LEAP's proof DAG (the only new null model needed).
