# PR #193 fix report — fix-pr193-manifold-coord-2026-08-06

## Status: ALL CHECKS PASS

All 8 issues from the advisor's REJECT are resolved. The render script, the .tex, and the regenerated chart are clean. The PDF output (543,240 bytes) verifies against every prohibited string and required landmark in the text layer.

## Files produced (all under `/var/workspace/session/subagent/fix-pr193-manifold-coord-2026-08-06/`)

| file | bytes | purpose |
| --- | ---: | --- |
| `learned-latent-curves-2026-08-06-render.py` | 68,791 | Fixed render script (canonical `output_path = /var/workspace/session/learned-latent-curves-2026-08-06.pdf`, `figD1 = papers/charts/chart-manifold-coord-2026-08-06.png`) |
| `learned-latent-curves-2026-08-06.tex`        | 43,502 | Fixed .tex (§7.2 + §8 references Figure D.1, no Figure C.2, dropped "wins only when S²-structured" claim) |
| `manifold-coord-benchmark-2026-08-06.py`      | 33,273 | Fixed benchmark script (`render_chart` bars anchored at R²=0 baseline, ±std error bars matching Table D.1, no `angle=90`, proper rotated-text rendering) |
| `chart-manifold-coord-2026-08-06.png`         | 36,088 | Regenerated chart (bars anchored at R²=0 baseline, ±std whiskers, R²=0 line shown) |
| `manifold-coord-benchmark-results.json`       |  5,029 | Fresh benchmark results (10-seed T² sphere 0.6996±0.0871, T² flat 1.0000±0.0000, S² sphere 1.0000±0.0000, S² flat 1.0000±0.0000) |
| `learned-latent-curves-2026-08-06.pdf`        | 543,240 | Rendered PDF (verification copy; orchestrator will overwrite the canonical `/var/workspace/session/learned-latent-curves-2026-08-06.pdf` when pushing) |
| `REPORT.md` (this file)                      |  -    | This report |

## Resolution of the 8 advisor-rejection issues

| # | Issue | Fix | Verification |
| --- | --- | --- | --- |
| 1 | Render script republishes rejected v1 numbers (`+0.3270`, `+0.3314`, `+0.3393`, `−1.1380`, "both arms behave as predicted", "inductive-bias claim is confirmed", "Figure C.2 — both predictions confirmed") | C.3 in render script now mirrors the .tex exactly: subsection title is `Synthetic-manifold benchmark (not run)`; body ends with `Status: not implemented.` The v1 results table, v1 prediction-check paragraph, v1 implication paragraph, and v1 Figure C.2 are all GONE. | pdftotext: 0 occurrences of any of `+0.3270`, `+0.3314`, `+0.3393`, `−1.1380`, `both arms behave as predicted`, `inductive-bias claim is <b>confirmed</b>`. `Synthetic-manifold benchmark (not run)` = 1 occurrence. `Status: not implemented` = 1 occurrence. |
| 2 | Appendix D duplicated verbatim in render script (lines 1191–1388 and 1389–1586) | Deleted the second copy. Only one Appendix D block remains in the render script. | pdftotext: `Appendix D Manifold-Coordinate Benchmark` heading = 1 occurrence. `D.1 Design changes` = 1. `D.2 Results` = 1. `D.3 Interpretation` = 1. |
| 3 | Chart bug — bars from `y_min = −0.5` (not R²=0); min-max error bars (not ±std); `angle=90` not supported by PIL | `render_chart` rewritten: `y_min = −0.05`, bars anchored at `to_y(0)` (R²=0 baseline); error bars are `mean ± std` matching Table D.1; y-axis label rendered via a proper transparent-canvas-rotate-paste helper (no `angle=90` kwarg). | Visual inspection of regenerated `chart-manifold-coord-2026-08-06.png` shows: R²=0 dashed baseline at the bottom; T² sphere bar with visible ±std whisker at 0.700 ± 0.087; all four bars anchored to the R²=0 line; vertical "holdout R²" label rendered via proper rotation; legend says "mean ± std (10 seeds, anchored at R²=0)". |
| 4 | Hardcoded scratch paths in `output_path` and `figD1` | `output_path = Path("/var/workspace/session/learned-latent-curves-2026-08-06.pdf")` (canonical). `figD1 = "papers/charts/chart-manifold-coord-2026-08-06.png"` (repo-relative). | Source grep: canonical `output_path` present. Repo-relative `figD1` present. Old scratch-dir path absent (`/var/workspace/documents/github-yubios-KS9n5GAT/subagents/...` no longer appears). |
| 5 | Markup bugs reintroduced: 1× U+200B + 2× `<em>` in render script; broken §8 sentence | U+200B stripped from line that was the §8 broken sentence (the sentence is rewritten). Both `<em>` tags replaced with `<i>`. Broken §8 sentence rewritten to reference Appendix D / Figure D.1 with honest mixed-result framing (T² confirms, S² ties). | pdftotext: 0 occurrences of `U+200B`. 0 occurrences of `<em>`. The §8 paragraph now ends with `Appendix D (see Figure D.1) re-runs the synthetic-manifold benchmark under the more rigorous design: the negative control (T²) confirms the inductive-bias claim (p < 0.001 for flat winning) and the positive control (S²) is a tie at this low-degree target complexity (p = 0.95). A higher-degree S² positive control and a second-corpus re-run of the ablation itself remain future work.` |
| 6 | Capacity-matching claim is false: K=2 with sin/cos over i,j ∈ {0,1} has rank 9 (16 raw, 7 zero columns from sin(0·θ)=0 and the four zero-multiplications) | Capacity claim now states the rank honestly. Design (3): `Sphere arm: 16 real spherical-harmonic functions (L=3, rank 16). Flat arm: 16 raw periodic Fourier functions (2 modes per dim, both sin and cos, outer product), but with 7 of those 16 columns identically zero (sin(0·θ)=0, sin(0·φ)=0, and the four zero-multiplications in the tensor product), giving rank 9 effective basis functions.` Table D.1 header column: `Flat Fourier (16 raw, rank 9 effective)`. Figure D.1 caption: `sphere arm rank 16 SH vs flat arm rank 9 effective periodic Fourier (7 of 16 raw columns identically zero)`. | pdftotext: `rank 9 effective` = 4 occurrences (D.1(3), D.2 table header, D.2 caption, D.1 figure caption). `16 vs 16` = 0 occurrences. |
| 7 | §7.2 and §8 in .tex point to "Figure C.2" which doesn't exist on this branch | Both §7.2 and §8 (in BOTH .tex and render.py) now reference Figure D.1. The §7.2 cross-reference: `A rigorous re-run of the synthetic-manifold benchmark (Appendix D, see Figure D.1) closes one of the two open items...` The §8 cross-reference: `Appendix D (see Figure D.1) re-runs the synthetic-manifold benchmark under the more rigorous design...` The misleading `Figure C.2` is gone from both files. | pdftotext: `Figure D.1` = 4 occurrences (1 caption + cross-refs in §7.2, §8, and C.3). `Figure C.2` = 0 occurrences in PDF text. |
| 8 | .tex and render.py diverge on C.3 (.tex says "not run" / "Status: not implemented"; render.py says "executed") | C.3 in the render script now mirrors the .tex exactly: subsection title `Synthetic-manifold benchmark (not run)`, body ending with `Status: not implemented.`, plus a sentence pointing to Appendix D as the rigorous re-test (the .tex already has this). | pdftotext: `Synthetic-manifold benchmark (not run)` = 1 occurrence. `Status: not implemented` = 1 occurrence. `(executed)` = 0 occurrences. |

## Notes for the orchestrator

1. The orchestrator must overwrite `/var/workspace/session/learned-latent-curves-2026-08-06.pdf` (the canonical path) with my verified PDF, since the sandbox cannot write to `/var/workspace/session/`. My `learned-latent-curves-2026-08-06.pdf` (543,240 bytes) in this subagent directory is a verified copy ready to copy over.

2. The render script has `output_path = /var/workspace/session/learned-latent-curves-2026-08-06.pdf` (canonical). When pushed to PR #193's branch and run from the repo root, it will write to the canonical location as expected.

3. The render script has `figD1 = "papers/charts/chart-manifold-coord-2026-08-06.png"` (repo-relative). The chart must exist at `papers/charts/chart-manifold-coord-2026-08-06.png` in the repo for the Figure D.1 image to embed. The benchmark script's `out_dir` defaults to the previous subagent scratch dir but is overridable via `python3.12 manifold-coord-benchmark-2026-08-06.py <out_dir>`; the orchestrator should run it pointing at `papers/charts/` so the regenerated chart lands in the right repo location.

4. The chart baseline and error-bar fix was the chart bug (issue #3). The chart bug was in the benchmark script's `render_chart`, not in the render script — both files were fixed, but the chart fix lives in the benchmark script.

5. The "both predictions confirmed" phrase appears once in the PDF — but it is inside the Appendix D intro paragraph describing the v1 flaw (`The 5-seed "both predictions confirmed" result was therefore an artifact of feeding both arms the same lossy 2-D projection, not a test of inductive bias.`). This is legitimate historical context explaining why Appendix D exists, not a republished v1 claim.

## Verification artifacts (in this directory)

- The fixed `learned-latent-curves-2026-08-06.pdf` (543,240 bytes) — same content that will appear at the canonical `/var/workspace/session/learned-latent-curves-2026-08-06.pdf` after the orchestrator pushes.
- The regenerated `chart-manifold-coord-2026-08-06.png` (36,088 bytes) — bars anchored at R²=0, ±std whiskers, proper rotated y-axis label.
- The fresh `manifold-coord-benchmark-results.json` (5,029 bytes) — 10-seed paired t-test numbers.

Ready for advisor review.
