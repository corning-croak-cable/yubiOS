# point-map: proof-carrying map for unlabeled latent space

Browser prototype of the scheme in `refs/point-to-point-latent-map-2026-09-06.md`.
Open `index.html` in a browser (no build, no deps). Same geometry as the SOS agent's
`fit.ts` (PCA2 → stereographic lift → S²), so the module drops into the Worker.

Pipeline: identity keys (ordinal + FNV-1a hash) → binarization rule R0 (top-d PCA axes,
per-column median; `rule_hash` printed) → k-shell + S² placement + Φ ladder → atom edges
(Lean §1–3 shadows) → curveball null with per-trade margin certificates (Lean §8–10) →
compass Metropolis on F_T (Lean §7) → slerp bridge + closed-form defocus (Lean §6, §14).

Certificates are split into `identity` (must all pass; a red one is a code defect) and
`measurement` (may fail; a failure is a finding). Exclusion-only language throughout.
