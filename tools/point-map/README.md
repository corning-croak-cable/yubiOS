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

## Ingestion modes (texts source)

- **Pasted lines**: one item per line (≥ 10 items).
- **Upload SKILL.md files**: each file = one item, labeled by its frontmatter `name:` (falls back to filename).
- **Upload a folder** (`webkitdirectory`): one digest item per immediate subfolder — all `.md`/`.txt` files in that subtree concatenated (SKILL.md first, then README, then alphabetical; ~2000-char cap, bge's context limit), labeled by the subfolder name or the SKILL.md frontmatter `name:`.
- **Repo path**: `owner/repo` or full URL, optional `/subdir` — `POST /api/repo-items` pulls the repo tarball server-side (codeload, in-memory, per the sos-agent egress-IP fix), filters text files to the subdir, one item per file (max 400), labeled by repo path. Folder + file + line + repo items can be mixed in one map.

- **Grouping rule**: the picked folder's own name is stripped; digests group by the next path segment, so picking `skills/` yields one digest per skill subfolder. Files directly in the picked root become one "(files at <root>)" digest.
- **Server-budget fallback**: if the Worker dies mid-map (Cloudflare 1102/503), the page automatically re-runs the identical pipeline client-side and marks the result `mapped client-side (server budget)`. Same code, same certificates; only the D1 row is missing.

## NSS ladder (`map.nss`)

12 azimuthal sectors → NSS axes (Audience … Recursion). Candidate atomic actions (add / change / remove) are each refit and measured (`pole_shift_geodesic`, `occupied_sectors_delta`, `isolated_delta`, `pc12_delta`), scored and ranked L1–L5 with a plain-English `recommendation`. Request field `ideal` (1–5) picks the target rung; the page shows the ladder under the Wall with a radio per rung.

## Other endpoints

- `POST /api/embed {texts, source}` — bge-base-en-v1.5, stored in Vectorize `sos-embeddings`.
- `POST /api/vector/search {text, topK}` — cosine search over everything embedded.
- `POST /api/repo-items {repo, subdir}` — tarball → items (max 400).
