# point-map on a real embedding cloud: R0 vs Rabs (2026-09-06)

Spec: `refs/point-to-point-latent-map-2026-09-06.md`. Module: `tools/point-map/` (same `pointmap.js` deployed in the steady-orbit-sos Worker `/api/map` and the Sauna `sos-agent` app `/api/map`).

## Cloud
301 real texts → `@cf/baai/bge-base-en-v1.5` (768-D): 147 local `SKILL.md` files (first 1500 chars) + 154 yubiOS `refs/*.md` (first 1500 chars). Unlabeled to the map (labels carried only as identity keys).

**Stated preprocessing:** `PM.reduce(X, 24)` = top-24 PCA scores with the module's sign convention (largest-|component| positive). Reason: 301×768 raw exceeds the Cloudflare Worker resource budget (error 1102 in ~3 s) and killed one Sauna invocation; at d=9 the rules only read the top-9 subspace, which the 24-D projection preserves exactly. Top-9 share of the top-24 variance: 0.652.

## Results (d=9, seed 20260906, K=60 curveball draws unless noted)

| rule | runtime | rule_hash | classes (of 301) | largest | V₂ | E₀[V₂] | SD₀ | ΔV₂z | verdict |
|---|---|---|---|---|---|---|---|---|---|
| R0 (median) | local node | 708c8c7a1c5dc91b | 167 | 11 | 0.29702 | 0.27443 | 0.00754 | +3.00 | not-excluded (z rounds to the bar; unrounded < 3) |
| R0 (median) | CF Worker (map id 3) | 708c8c7a1c5dc91b | 167 | 11 | 0.29702 | 0.27443 | 0.00754 | +3.00 | not-excluded |
| R0 (median) | Sauna app (map id 6) | 708c8c7a1c5dc91b | 167 | 11 | 0.29702 | 0.27443 | 0.00754 | +3.00 | not-excluded |
| Rabs (zero) | local node | 38ffd985741dab5d | 163 | — | 0.29117 | 0.27460 | 0.00719 | +2.30 | not-excluded |
| Rabs (zero) | Sauna app (map id 7) | 38ffd985741dab5d | 163 | 12 | 0.29117 | 0.27460 | 0.00719 | +2.30 | not-excluded |
| Rabs (zero) | CF Worker (map id 4, K=40) | 38ffd985741dab5d | 163 | 12 | 0.29117 | 0.27501 | 0.00741 | +2.18 | not-excluded |

Identity certificates: 13/13 PASS on every run. Measurement certificates: membership PASS (SD₀ ≈ 0.007 ≫ 1e-3, both rules admissible); ΔV₂z red on every run.

## Reading
- **Determinism across runtimes holds:** identical `rule_hash` and identical numbers to the printed precision on local node, CF Worker, and Sauna app for the same input + seed (the K=40 CF row differs only because K differs).
- **R0 vs Rabs:** on this cloud R0 gives the slightly stronger deflection (+3.00 vs +2.30) with comparable null width; neither clears the exclusion bar. Both admissible. R0 stays the default; Rabs recorded as the weaker alternative here (one cloud, one seed: not a general verdict).
- **Ladder:** Φ(k) under R0 = 1.602 1.585 1.476 1.216 1.040 1.015 0.868 0.701 0.537 [0.537 interpolated: shell k=9 empty]; shells 2 5 25 54 63 67 51 32 2 0. Monotone, so T× exists in principle but the compass reports none because Φ(8)=Φ(9) after interpolation; the empty top shell is a real property of this cloud under R0.
- **Source split:** mean k for `refs/` items 3.99 vs 4.4–5.3 for skill files; the top-5 atom Δ items are all skill files (indices 43, 36, 283, 290, 204).
- **Budget note:** the CF Worker fails intermittently at K=60 on 301×24 (1102), passes at K=40; the Sauna app passes K=60 in 3–5 s. For N≥300 prefer K≤40 on CF or run client-side.

## Not claimed
Nothing here elevates the deflection to a corpus fact (papers' discipline). The pre-registered null-degeneracy bet from the framing log is settled: R0 on a real embedding cloud yields a non-degenerate curveball null.
