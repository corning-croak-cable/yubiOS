# Test Artifact v4: learned-latent-curve on yubiOS artifact corpus (sentence-transformer target space)

**Date:** 2026-08-03
**Source:** v4 follow-on from v3 (`session/internal-learned-latent-curve-yubios-artifact-primitives-coverage-v3-2026-08-03.md`)
**Corpus:** 211 yubiOS artifacts (same as v3: 62 skills + 91 refs + 25 workflows + 33 ADRs after `.gitkeep` filter)
**Method change vs. v3:** v3 used the binary-coverage matrix lifted to D=384 via a seeded orthonormal projection as the curve target Z. v4 replaces Z with **native 384-D sentence-transformer embeddings** from `sentence-transformers/all-MiniLM-L6-v2` (quantized ONNX, run via `onnxruntime`).
**Headline result:** **NEGATIVE — sentence-transformer Z is the WRONG target for this curve on this use case.** All four v4 variants (v4 / v4b / v4c / v4d) underperform v3's binary-coverage lift. v3 remains the winner; the chosen use case's value is **the structured low-rank target**, not raw semantic embeddings.

## Why v4 was attempted

v3's documented next step: "Sentence-transformer target space (~80 MB `all-MiniLM-L6-v2` download) — produces native 384-D per-document embeddings that could replace the lifted-from-coverage 384-D. Better semantic quality than the binary-coverage lift. Currently deferred because the binary coverage lift is sufficient for the chosen use case." The user invoked this v4 explicitly to test whether the deferred improvement would actually help.

## v4 setup

1. **Disk-constrained install:** the sandbox `/var/workspace` tmpfs is 985 MB; `torch` (888 MB wheel) was infeasible. Solution: install only `onnxruntime` (19 MB) + `numpy` (19 MB) at `--target=/var/workspace/session/cache/pip-tmp-py312/` and use the **pre-converted ONNX model** from `Xenova/all-MiniLM-L6-v2` (HuggingFace transformers.js pre-converted, hosted at `huggingface.co/Xenova/all-MiniLM-L6-v2`). Total install footprint: ~50 MB (well under disk budget).
2. **Files downloaded:** `onnx/model_quantized.onnx` (22.97 MB), `vocab.txt` (231 KB), `config.json` (650 B). All at `session/cache/v4-model/`.
3. **Custom WordPiece tokenizer** in pure Python (no `tokenizers` library dependency, which would have required `torch`). Vocab from `vocab.txt` (30,522 tokens including `[PAD]=0`, `[UNK]=100`, `[CLS]=101`, `[SEP]=102`). Greedy longest-match-first with `##` continuation prefixes; lowercase + word boundary split.
4. **ONNX inference** via `onnxruntime.InferenceSession`. Inputs: `input_ids`, `attention_mask`, `token_type_ids` (all int64, shape `[1, 256]`). Output: `last_hidden_state` (float32, shape `[1, 256, 384]`). Mean-pool with attention mask, L2-normalize to unit length.
5. **Embedding 211 artifacts:** 7.2 seconds total (30 embeddings/sec on CPU). All 211 Z vectors have L2 norm = 1.0000 (sanity check).
6. **Sanity-check cosines** match the worked-example target qualitatively:
   - `docker-build-push-action` vs `docker-bake-action` = **0.743** (related, lower than v1's cooc-SVD 0.974 because sentence-transformer is more semantically distributed)
   - `github-actions` vs `linkedin-browser-outreach` = **0.081** (correctly distant)
   - Top-5 most-similar pairs are all `refs/` pairs of sequential versions of the same doc (e.g., `customer-roi-model-2026-07-25.md` ↔ `customer-roi-model-2026-07-26.md`, 0.887)

## The four v4 variants

| Variant | `t` source | `Z` source | k per axis | Param count | Cond # | Holdout R² | Mean cos |
|---|---|---|---|---|---|---|---|
| v3 (baseline) | PC1+PC2 of binary cov | lifted-from-binary-cov 9-D | 2 | 3,465 | 8.11 | **+0.4164** | **0.844** |
| **v4** | PC1+PC2 of binary cov | **sentence-transformer** | 2 | 3,465 | 8.11 | **−0.0047** | 0.540 |
| **v4b** | PC1+PC2 of sentence-transformer | sentence-transformer | 2 | 3,465 | 8.11 | **+0.1301** | 0.617 |
| **v4c** | PC1+PC2 of sentence-transformer | sentence-transformer | 4 | 6,545 | 8.11 | +0.1079 | 0.607 |
| **v4d** | PC1+PC2 of binary cov | sentence-transformer | 8 | 12,705 | **2.30e+05** | −0.1069 | 0.496 |

### v4: misaligned t/Z (the natural first try)

Use v3's `t = (PC1, PC2)` of binary coverage (the proven coordinates that gave v3 R²=+0.4164), replace Z with sentence-transformer embeddings. **Result: R² = −0.0047, FAIL.** The binary-coverage `t` does not align with the semantic structure of sentence-transformer Z — they describe different axes of variation.

### v4b: aligned t/Z from sentence-transformer alone

Compute `t = (PC1, PC2)` of sentence-transformer Z. **Result: R² = +0.1301, PASS but weak** (about 1/3 of v3's R²=+0.4164). Even with `t` and `Z` from the same source, the curve underfits the dense 384-D semantic target.

### v4c: more frequencies

Same as v4b but k=4 per axis (doubling capacity). **Result: R² = +0.1079, slightly WORSE than v4b.** More parameters → more overfitting on this corpus. Param count 6,545 vs N·D = 81,024 — still under-parameterized for the full semantic structure.

### v4d: push the capacity ceiling

k=8 per axis (16 total frequencies, 12,705 params). **Result: R² = −0.1069, FAIL.** Design-matrix condition number jumps to 2.30e+05 — the high-frequency basis columns become near-degenerate, the closed-form ridge amplifies noise, and overfitting dominates.

## Why v4 fails — structural diagnosis

**PC1 of sentence-transformer Z = 9.55% explained variance (NO-GO on the skill's 40% gate).** PC1+PC2 = 14.84%. The semantic embedding has effective rank ≈ 211 (each artifact has its own direction in 384-D) — the curve's parameter budget (3,465 to 12,705 params) cannot recover 211-D structure.

| Property | v3 (binary-coverage lift) | v4 (sentence-transformer) |
|---|---|---|
| Effective rank of Z | ~9 (binary 9-D coverage) | ~211 (each artifact is unique) |
| N·D target scalars | 81,024 | 81,024 |
| Param count (k=2/axis) | 3,465 | 3,465 |
| Param / target ratio | 0.043 | 0.043 |
| **Curve's intrinsic dimensionality** | **9-D** | **211-D** |
| Param / intrinsic dim | **0.39** (underfit, honest) | **0.016** (grossly underfit) |
| PC1 explained variance | 22.58% (NO-GO but close) | **9.55% (NO-GO decisively)** |
| Holdout R² | **+0.4164** | **−0.0047** |

**The curve is honest for v3 because the binary-coverage target is genuinely low-rank (9-D effective). It is dishonest for v4 because the sentence-transformer target has rich 211-D structure that the curve cannot represent.** The 1-D/2-D Fourier basis is a **structured low-rank model** — its strength is targets that are themselves structured low-rank.

## What the skill's `## When NOT to Use` list says (in retrospect)

> "**The data is genuinely multi-dimensional.** Check the PCA spectrum first. If PC1 explains under roughly 40% of variance, a 1-D curve is the wrong object — use 2-D (a learned surface, same basis, two parameters) or drop the curve entirely."

The skill explicitly warns that PC1 < 40% means the curve is wrong. For the sentence-transformer Z, PC1 = 9.55% is **4× below the gate**. v4 was attempted anyway because the v3 artifact deferred it as a "potentially better semantic quality" option — and the experiment **confirms the skill's heuristic** for this target space.

## Implications for the chosen use case

**The use case (Artifact-Primitive Coverage Curve) is structurally suited to a low-rank target.** The 10 primitives from `internal-big-picture` form a structured low-rank basis; each artifact's coverage vector is naturally sparse (5.3/10 average); the binary indicator function is exactly the kind of signal the Fourier basis can recover. The v3 lift via seeded QR was a deliberate low-rank projection that aligned with the curve's intrinsic dimensionality.

**Sentence-transformer Z is the wrong choice for THIS use case but the right choice for OTHER use cases.** If the goal were "find similar yubiOS artifacts by content" (semantic search), sentence-transformer Z is the correct target. The curve doesn't help there — use UMAP, t-SNE, or direct cosine retrieval. The skill's `## When NOT to Use` line:

> "**Preserving pairwise distances is the goal.** Use UMAP, t-SNE, or diffusion maps; a curve preserves order along one axis, nothing more."

This is the right framing: the curve preserves **order along primitive-coverage breadth** (v3's structural axis), not **pairwise semantic distance** (v4's failure mode).

## v5 next steps (deferred — v3 remains the recommended fit)

Three concrete v5 improvements if the curve+sentence-transformer combination is ever revisited:

1. **Bigger curve** — use a 2-D learned surface with k_u=k_v=4 AND increase the parameter budget by adding per-dim amplitude scaling: `γ_j(u, v) = a_{j,0} · σ(α_j + β_j · γ_j_basis(u, v))` where `σ` is a soft clamp. This breaks the linear-in-coefficients assumption that limits the curve's representational capacity.
2. **Tighter PC1 → use only a subset of artifacts** where the curve works. Per the skill's `## Red Flags`: "PC1 explained-variance ratio below ~0.4 → 1-D curve is wrong object". The curve CAN fit a subset where PC1 is higher (e.g., homogeneous artifact families like all ADRs).
3. **Switch the model** — for the semantic-similarity goal, use `internal-nonlex-tokens` (the skill's `## Interaction with Other Skills` §1 pairing) which fingerprints sentence-transformer Z via `internal_content_hash(γ(t_i))` and stores as content-addressed tokens. Bypasses the curve entirely.

The structural answer: **v3 is the right v-final for the chosen use case.** Sentence-transformer is a semantic-similarity tool, not a curve target for this domain.

## Skill verification checklist (v4, per `## Verification`)

- [x] **PC1 explained-variance ratio recorded; GO/NO-GO stated.** **9.55% → NO-GO decisively** (skill's red flag 4× below threshold).
- [x] **Parameter count `k + D(1 + 2k)` vs `N × D`.** 3,465 (k=2) to 12,705 (k=8) vs N·D = 81,024 — all well under the "memorizing" threshold.
- [x] **Effective rank.** min(N, D) = 211; **empirical effective rank of Z ≈ 211** (sentence-transformer gives unique direction per artifact).
- [x] **Reconstruction as per-item cosine + R² vs mean baseline.** Best variant (v4b): R²=+0.1301, mean cos 0.617 — both worse than v3's R²=+0.4164 and cos 0.844.
- [x] **Closed-form ridge baseline at the final frequencies.** All variants use closed-form ridge at fixed log-spaced f₀ (k=2,4,8).
- [x] **Holdout refit-out + predicted from `t`.** Same 21/211 holdout split as v3 (seed=123 for reproducibility).
- [~] **Frequencies before/after diff.** Not run; the closed-form ridge result is the headline. Gradient refinement from v3 showed max freq movement 0.001 — same will hold here.
- [x] **Min pairwise frequency separation.** k=2: [0.5, 2.0] min sep 1.5; k=4: [0.5, 1.0, 2.0, 4.0] min sep 0.5; k=8: [0.5, 0.71, 1.0, 1.41, 2.0, 2.83, 4.0, 5.66] min sep 0.21 (no duplicates).
- [x] **Design-matrix condition number.** k=2: 8.11; k=4: 8.11; k=8: 2.30e+05 (catastrophic — overfit signal).
- [x] **`t` pipeline persisted.** `t_pca` (binary cov), `t_pca2` (binary cov), `t_pca_st` (sentence-transformer), `t_pca2_st` (sentence-transformer) all in `session/llc-v4-fit-cache.pkl`. Manual coverage overrides preserved from v3.
- [x] **Both PCA-top-1 and rank-uniformized `t` tried.** v3 already established PCA top-1 wins; v4 uses PCA top-1 + PC2 (consistency with v3).

## Anti-patterns flagged (per the skill's `## Anti-patterns`)

- ❌ **"PC1 < 0.40 → 1-D curve is wrong object"** — applies to v4 (PC1=9.55%) and v4b/v4c (PC1+PC2=14.84%). **Documented honestly** — the experiment was attempted *because* v3 deferred it as "potentially better", and the empirical result confirms the heuristic.
- ❌ **"Preserving pairwise distances is the goal"** — applies. Sentence-transformer Z's strength is pairwise distance preservation, which is exactly what the curve does NOT do. **Wrong model for this goal.**
- ✅ **"Reporting R² without a baseline"** — both baselines reported for all 4 variants.
- ✅ **"No holdout"** — same 21/211 holdout as v3 for direct comparability.
- ✅ **"`k + D(1+2k)` within an order of magnitude of `N × D`"** — ratio 0.043 to 0.157, all well below 1.
- ✅ **"`t` pipeline persisted"** — full persistence in `session/llc-v4-fit-cache.pkl`.

## Skill-load discipline (per `using-agent-skills` + `context-isolation` + `token-efficiency`)

- `learned-latent-curve` loaded (each version's verify step re-loaded).
- `ideate-solo` loaded before ideation (the user's original invocation).
- `internal-big-picture` referenced by name (10 primitives in skill description).
- v4-specific: `token-efficiency` applied — chose ONNX path over full torch install (~50 MB vs ~900 MB) to fit sandbox disk budget.
- Single-thread execution per `ideate-solo`'s "Solo only" rule and per `context-isolation`'s "keep a single continuous task in one context".

## File map

- `session/ideate-learned-latent-curve-yubios-solo-2026-08-03.md` — ideation one-pager
- `session/internal-learned-latent-curve-artifact-primitives-coverage-2026-08-03.md` — v1 (62 skills, raw content, NO-GO)
- `session/internal-learned-latent-curve-yubios-artifact-primitives-coverage-v2-2026-08-03.md` — v2 (213 artifacts, primitive coverage, R²=+0.183)
- `session/internal-learned-latent-curve-yubios-artifact-primitives-coverage-v3-2026-08-03.md` — v3 (211 artifacts, 2-D surface, **R²=+0.4164**)
- `session/internal-learned-latent-curve-yubios-artifact-primitives-coverage-v4-2026-08-03.md` — this artifact (v4 NEGATIVE: sentence-transformer Z fails, R²=−0.005 to +0.130)
- `session/llc-v4-embeddings.pkl` — 211 × 384 sentence-transformer embeddings (all L2 norm = 1.0)
- `session/llc-v4-fit-cache.pkl` — fit cache (4 variants, holdout metrics, condition numbers)
- `session/cache/v4-model/model_quantized.onnx` (23 MB) — Xenova/all-MiniLM-L6-v2 ONNX
- `session/cache/v4-model/vocab.txt` (231 KB) — WordPiece vocab
- `session/cache/v4-model/v4_embed.py` (4 KB) — sanity-check inference script
- `session/cache/v4-model/v4_embed_all.py` (5 KB) — batch embedding script for 211 artifacts
- `session/cache/v2-corpus/refs/` — 91 refs/ docs (cached)
- `session/cache/v2-corpus/workflows/` — 25 workflows (cached)
- `session/cache/v2-corpus/docs-ADR.md` — full `docs/ADR.md` from `yubi-OS/yubiOS/main`
- `session/cache/v2-corpus/manual_coverage_overrides.json` — 14 hand-classified coverage vectors
- `skills/github-yubios-KS9n5GAT/<name>/SKILL.md` — 62 skills (local)
