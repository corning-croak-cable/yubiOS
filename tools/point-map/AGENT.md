# AGENT.md — SOS Agent latent space map, for agents

You are reading the agent experience guide for the point-to-point latent map at `/map/` on this site. It tells you what the endpoints are, how to get a corpus onto the map, how to read what comes back, and how to turn the result into your next edit. The map is a **wayfinder**: every run ends with one selected rung of an NSS ladder and a copy-ready prompt that names the literal file(s) to add, change, or remove. Do that edit, re-run, compare. That loop is the product.

Spec (the math and the certificates): `yubi-OS/yubiOS refs/point-to-point-latent-map-2026-09-06.md`. Machine-checked shadows: `papers/data/lean/CurvedCorpus.lean`.

## 0. Ground rules (read once)

- **Exclusion-only language.** A null is *excluded* or *not excluded*. Nothing here is confirmed.
- **Identity vs measurement certificates.** Identity certificates must all pass; a red one is a code defect, stop and report it. Measurement certificates may fail; a failure is a finding, not a bug.
- **`rule_hash` is the comparability key (C1).** Two maps are comparable only if their `rule_hash` matches. Keep `d`, `seed`, `threshold` fixed across an iteration loop or you are comparing different instruments.
- **The wall.** Every compass/null number is a property of a designed chain on a measured ladder under a stated binarization rule, not of the cloud itself.
- **Never say "toward the ideal pole."** Rungs are ranked by measured movement after a refit. Direction is free.

## 1. Endpoints

Base: `https://steady-orbit-sos.shant-b57.workers.dev` (the Sauna mirror at `https://sos-agent-lowr22fg.sauna.new` serves `/api/map`, `/api/maps`, `/api/maps/:id` for vectors only, no embedding).

| Method | Path | Body | Returns |
| --- | --- | --- | --- |
| POST | `/api/embed` | `{ texts: string[], source?: string }` | `{ vectors: number[][] }` (bge-base-en-v1.5, 768-D). Every embedding is also stored in Vectorize (`sos-embeddings`) with id `e<FNV>`, metadata `label/text/source/created`. |
| POST | `/api/repo-items` | `{ repo: "owner/repo" \| github URL, subdir?: "path" }` | `{ n, repo, subdir, items: [{ text, label }] }` — one item per text file from the repo tarball (max 400). `label` is the repo-relative path; use it as the file name. |
| POST | `/api/map` | `{ vectors: number[][] }` **or** `{ texts: string[] }`, plus `labels?`, `names?`, `d?=9 (≤24)`, `seed?=20260906`, `T?=0.05`, `K?≤40`, `threshold?="median"\|"zero"`, `ideal?=1..5` | `{ id, map }` — the MapResult (see §3). Stored in D1. |
| GET | `/api/maps` | | stored maps, metrics only |
| GET | `/api/maps/:id` | | full MapResult |
| DELETE | `/api/maps/:id` | | |
| POST | `/api/vector/search` | `{ text, topK?=5 }` | cosine neighbours over everything ever embedded |
| GET | `/llms.txt` | | one-screen endpoint summary |
| GET | `/AGENT.md` | | this file |

Limits: input `D > 40` returns **413**; reduce client-side first (`PM.reduce(X, 24)` in `pointmap.js`, top-24 PCA scores) and post the scores. `K` is capped at 40 on the Worker (runtime budget). Items: ≥10, ≤400.

**Always pass `names`.** `names[i]` is the file name (or repo path) of item `i`. Without it the ladder can only say `#212`; with it the wayfinder prompt names the literal file to open.

## 2. Getting a corpus onto the map

Three sources. Mix them; the page does.

**A. Repo path (fastest for an agent).**
```
POST /api/repo-items {"repo":"yubi-OS/agent-skills","subdir":"skills"}
→ items[]  (text, label=path)
POST /api/embed {"texts": items.map(i=>i.text), "source":"yubi-OS/agent-skills/skills"}
→ vectors  (768-D)
reduce to 24 dims (PM.reduce) if you are calling the API directly
POST /api/map {"vectors": scores, "labels": items.map(i=>i.label), "names": items.map(i=>i.label), "d":9, "seed":20260906, "threshold":"median", "K":40, "ideal":1}
```

**B. Files / folder (browser).** On `/map/` choose *texts → server embed + map*, then either **upload .md files (skill/doc/ref)** (one item per file, first 2000 chars, label from frontmatter `name:` else filename, `name` = filename) or **upload a skills folder (digest per subfolder)** (one item per subfolder: SKILL.md first, then README, then the rest, up to ~2400 chars; label from SKILL.md `name:`; `name` = `<folder>/SKILL.md`). Or type `owner/repo[/subdir]` in the repo box and click *fetch repo*.

**C. Raw vectors.** Paste `[[...],[...]]` (≥10 rows) as *paste vectors JSON*, or POST them. Pasted lines have no file, so the ladder falls back to the label text.

## 3. Reading the MapResult

Top level: `version, rule_hash, rule{rule,d,threshold,axes,thresholds,note}, n, D, d, keys[], bits[], pc12, v2, pole, pts[], gaps[], shells[], classes, ladder{Phi}, null{K,E0,SD0,z,verdict}, compass{T,pi,kmean_*,acceptance,Tx}, atoms[], certificates[], nss{...}`.

- `keys[i] = { ordinal, hash, label?, name? }` — the identity layer. `ordinal` is the injective key (D6).
- `bits[i]` — the d-bit measurement of item i under the rule (`R0` = per-column median, `Rabs` = sign).
- `pts[i]` — the S² point; `pole` is the all-ones pole; `gaps[i]` is geodesic distance to it.
- `null.z` — ΔV₂z against the curveball fixed-margin null; `null.verdict` is exclusion-only.
- `atoms[i] = { i, flip, delta }` — the single-action atom for item i (Lean §1): which bit to flip and the geodesic gain.
- `certificates[] = { class: "identity"|"measurement", name, ok, detail }`.

### 3.1 `nss` — the ladder

```
nss: {
  axes: [12 NSS axis names],          // Audience … Recursion, one per 30° azimuthal sector
  sector_counts: [12 ints],
  empty_sectors: [names],
  base: { occupied_sectors, isolated },
  ladder: [ L1..L5 ],
  ideal: "L1",                        // the selected rung (request field `ideal`)
  recommendation: "...",              // plain English for the ideal rung
  prompt: "[L1 · change · Lifecycle] CHANGE: open \"skills/foo/SKILL.md\". ..."   // the wayfinder prompt
}
```

Each rung: `{ rung, action: "add"|"change"|"remove", axis, item?, label?, exemplars?[] | nearest?, flip_bit?, atom_delta?, pattern?, fill_size?, delta{pole_shift_geodesic, occupied_sectors_delta, isolated_delta, pc12_delta}, score, verdict: "moves"|"no measurable move", hypothesis, method, recommendation, prompt, caveat }`.

How each rung was produced: the candidate action was **applied to the bit matrix, the sphere was refit, and the movement measured**. `score = occupied_Δ − 0.5·isolated_Δ + pole_shift`. Rungs are ranked by score; L1 is the largest measured move, not the "best" edit in any moral sense.

## 4. The wayfinder loop

1. Run the map with `ideal` unset (defaults to L1). Read `nss.ladder`.
2. Pick the rung you want to act on. In the browser, click its radio under **NSS ladder**; via API, re-post with `ideal: <n>` (cheap, same rule_hash) or just read `ladder[n-1].prompt`.
3. Copy `nss.prompt`. It is written to be handed to an editing agent as-is. It always contains:
   - the **action** (ADD / CHANGE / REMOVE),
   - the **literal file(s)**: the file to open (`change`, `remove`), the nearest neighbour to fold into (`remove`), or the exemplar files to model new content on (`add`, `change`),
   - the **axis/sector** the move concerns,
   - the **re-run check**: same `d/seed/threshold`, `rule_hash` must match, and the predicted `pole shift / occupied Δ / isolated Δ` to compare against.
4. Make the edit in the corpus.
5. Re-run the map on the edited corpus with the **same** `d`, `seed`, `threshold` (and the same `names`). Confirm `rule_hash` matches. Compare the measured `pole_shift_geodesic`, `occupied_sectors_delta`, `isolated_delta` to the prediction (compute pole shift as geodesic between the two `pole` vectors; sector/isolation deltas from the two `nss.base` blocks).
6. **Decision rule:** keep the edit if the measured move matches the prediction in sign. Otherwise revert and take the next rung. Then go to 1. Each pass is one atomic action; do not batch rungs.

What the three actions mean in the corpus:

- **CHANGE** `"<file>"`: item sits with bit *j* off; the prompt lists the nearest neighbours that have bit *j* on. Add the sections, terms, and structure those exemplars share and this file lacks. Leave the rest alone.
- **ADD**: the thinnest sector needs mass. The prompt names the existing files nearest the target bit pattern; create `fill_size` new files (default 3) that combine what those exemplars share. Name each for its subject, not the sector.
- **REMOVE** `"<file>"`: the most isolated point, or the point farthest from the pole. Fold anything worth keeping into the named nearest neighbour, then delete.

`caveat` is real: a re-embed of new text lands *near*, not on, the synthetic pattern that was measured. Expect the sign to match, not the digits.

## 5. Interacting with the map page

- Sphere: drag to rotate, wheel to zoom, **auto-rotate**, **reset view**, **labels** toggle. Hover a point for label / k-shell / gap / atom Δ / hash. Hue = Hamming shell k; the magenta segment is the slerp bridge from the farthest point to the pole (identity: geodesic non-increasing).
- Cards on the right: identity (D6), placement + Φ ladder, null, compass, bridges, result (**download MapResult.json**), certificates table.
- Under the Wall paragraph: **rule** line (rule + `rule_hash`), the **NSS ladder** table (radio = ideal rung), the recommendation, and the **wayfinder prompt** with a copy button.
- If the server 502s on a big cloud the page maps client-side with the same `pointmap.js` (identical numbers; `source` notes "mapped client-side").

## 6. Minimal agent recipe (no browser)

```js
import { PM } from "./pointmap.js";          // or fetch tools/point-map/pointmap.js from yubi-OS/yubiOS
const items = (await post("/api/repo-items", { repo: "owner/repo", subdir: "skills" })).items;
const { vectors } = await post("/api/embed", { texts: items.map(i => i.text), source: "owner/repo/skills" });
const scores = PM.reduce(vectors, 24, 1).scores;
const names = items.map(i => i.label);
const r1 = await post("/api/map", { vectors: scores, labels: names, names, d: 9, seed: 20260906, threshold: "median", K: 40 });
console.log(r1.map.rule_hash, r1.map.nss.prompt);   // hand this prompt to your editor
// ... edit the corpus per the prompt ...
// re-fetch items, re-embed, re-reduce with the same k/seed, re-post with the same d/seed/threshold
// assert r2.map.rule_hash === r1.map.rule_hash before comparing deltas
```

`post` is a JSON POST with retries on 502/503. Store `id` from each response; `GET /api/maps/:id` returns the full result later, so the iteration trail is recoverable.

## 7. Things that will bite you

- Forgetting `names` → prompts say `#212` instead of a file. Fix: pass `names`.
- Changing `d`, `seed`, or `threshold` between runs → `rule_hash` differs → deltas are meaningless. The prompt repeats the values to reuse.
- Posting raw 768-D vectors → 413. Reduce first.
- Fewer than 10 items → 422. `remove` rungs are suppressed when N ≤ 10.
- Reading `score` as quality. It is measured movement. A high-scoring `remove` is not a recommendation to delete good work; read `why` in the recommendation and decide.
