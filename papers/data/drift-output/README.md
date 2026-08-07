# Curve drift detector (PR4, 4-corpus, repo-sourced)

## Sourcing rule (per operator standing instruction)

All corpus listings + content are sourced DIRECTLY from the GitHub repos via
the Contents API + `raw.githubusercontent.com` — NO local file reads. One
documented exception:

- **self**: no repo `self/` directory exists on any of the user's repos
  (verified via Contents API on `yubi-OS/yubiOS` and `yubi-OS/agent-skills`).
  Reading from workspace `memory/personal-WbtUgeUv/` and surfacing the
  exception in `self-corpus-listing.json` + this README. See
  `load_self_corpus` in the script for the resolution path
  (push the 10 files to a `yubi-OS/self` repo or add a `self/` dir under
  an existing repo, update `REPO_SELF_PATH`).

## Corpora

| Corpus | Source | Items |
|---|---|---|
| `self` (anchor) | workspace `memory/personal-WbtUgeUv/` (EXCEPTION) | 111 |
| `docs` | `yubi-OS/yubiOS/docs/` via Contents API | 284 |
| `refs` | `yubi-OS/yubiOS/refs/` via Contents API | 1444 |
| `cycle4` | `yubi-OS/yubiOS/papers/data/repo-history-skill-cycle-4-archive-2026-08-07.json` via raw.githubusercontent.com | 324 |

Each corpus's `## Section` rows (or per-event rows for cycle4) are scored
against the SHARED 9-D `internal-big-picture` primitive basis (text-keyword
for self/docs/refs; cycle4 also has its native repo-history 9-D coverage
preserved in the archive). Three Möbius φ_θ ∈ PSL(2,ℂ) warps fit
self → docs, self → refs, self → cycle4 (all anchored on self). Drift
signals (warp magnitude × NSS-axis score) are aggregated across all 3
alignments and ranked in `drift-priority-list.md`.

## Outputs

| File | Description |
|---|---|
| `self-corpus-listing.json` | Listing of self corpus items (EXCEPTION: workspace-local) + `_sourcing_exception` block |
| `docs-corpus-listing.json` | Listing of docs corpus items + `files_listed_in_repo` (Contents API) |
| `refs-corpus-listing.json` | Listing of refs corpus items + `files_listed_in_repo` (Contents API) |
| `cycle4-corpus-listing.json` | Listing of cycle4 corpus items + `source_file_meta` (Contents API) |
| `mobius-transform.json` | Fitted φ_θ params for all 3 alignments + sourcing block |
| `warp-by-region.csv` | Per-region warp + NSS scores for all 3 alignments |
| `drift-priority-list.md` | Top-10 flagged drift regions (aggregated) |
| `aligned-curves.png` | 4 corpus point clouds + 3 warped-A point clouds on S^2 |
| `README.md` | This file |

## How to regenerate

```bash
python3.12 documents/github-yubios-KS9n5GAT/papers/scripts/curve-drift-detector.py
```

All GitHub fetches go through the `MASTER GIT SU` connection
(`conn_1KXnkOHGgyE4`). No local file reads except for the documented
`self/` exception.

## Math conventions (frozen)

- **9-D `internal-big-picture` primitive basis** (9 of 10 primitives;
  `self_describing` dropped at 94% coverage). SHARED across all 4 corpora.
- **Extended keyword vocab** (git/Linear/PR/commit terms) so cycle4 items
  register meaningfully on the same basis as self/docs/refs.
- **LOOSE-UNION kept-cols rule** — a primitive is kept if ANY of the 4
  corpora has informative coverage on it.
- **Identity-init Möbius**: φ_θ = (a=1, b=0, c=0, d=1), refined via
  L-BFGS-B with 6 random perturbations.
- **Frozen degree weights**: frequencies = harmonic series 1..k (k=8).
- **Chordal S² distance**: used as proxy for geodesic distance.
