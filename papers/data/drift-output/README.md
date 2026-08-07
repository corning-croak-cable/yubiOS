# Curve drift detector (PR4, 4-corpus version)

## What this is

Cross-corpus drift detector for FOUR corpora, all anchored on `self` (the
canonical self-archaeology dispatch target):

| Corpus | Path | Item unit | Items |
|---|---|---|---|
| `self` (anchor) | `memory/personal-WbtUgeUv/` | `## Section` header | 111 |
| `docs` | `documents/personal-WbtUgeUv/` | `## Section` header | 37 |
| `refs` | `documents/github-yubios-KS9n5GAT/refs/` | `## Section` header | 55 |
| `cycle4` | `papers/data/repo-history-skill-cycle-4-archive-2026-08-07.json` | per-event row | 324 |

Each corpus's `## Section` rows are scored against the SHARED 9-D
`internal-big-picture` primitive basis (text-keyword for self/docs/refs/cycle4;
the cycle4 items additionally keep their native repo-history 9-D coverage in
the archive). Three Möbius φ_θ ∈ PSL(2,ℂ) warps fit self → docs, self → refs,
self → cycle4 (all anchored on self). Drift signals (warp magnitude × NSS-axis
score) are aggregated across all 3 alignments and ranked in
`drift-priority-list.md`.

## Outputs

| File | Description |
|---|---|
| `self-corpus-listing.json` | Listing of self-corpus items (sections) |
| `docs-corpus-listing.json` | Listing of docs-corpus items (sections) |
| `refs-corpus-listing.json` | Listing of refs-corpus items (sections) |
| `cycle4-corpus-listing.json` | Listing of cycle4-corpus items (events) |
| `mobius-transform.json` | Fitted φ_θ params for all 3 alignments |
| `warp-by-region.csv` | Per-region warp + NSS scores for all 3 alignments |
| `drift-priority-list.md` | Top-10 flagged drift regions (aggregated) |
| `aligned-curves.png` | 4 corpus point clouds + 3 warped-A point clouds on S^2 |
| `README.md` | This file |

## Math conventions (frozen)

- **9-D `internal-big-picture` primitive basis** (9 of 10 primitives;
  `self_describing` dropped at 94% coverage). SHARED across all 4 corpora
  (cross-corpus deviation from per-corpus basis rule).
- **Extended keyword vocab** (vs the 2-corpus version) — adds git/Linear/
  PR/commit vocabulary so cycle4 items register meaningfully on the same
  basis as self/docs/refs. New terms per primitive include `cosign`,
  `provenance`, `gpg`, `signed commit`, `branch protection`, `ci`,
  `workflow`, `changelog`, `commit history`, `sha`, etc.
- **LOOSE-UNION kept-cols rule** — a primitive is kept if ANY of the 4
  corpora has informative coverage on it (coverage ∈ [0.10, 0.90]).
  Strict-and-union collapsed too aggressively when self/docs/refs are
  saturated on `attestation` but cycle4 has meaningful variation.
- **Identity-init Möbius**: φ_θ = (a=1, b=0, c=0, d=1), refined via
  L-BFGS-B with 6 random perturbations; objective = mean squared chordal
  distance in the stereographed C plane.
- **Frozen degree weights**: frequencies are the cold-start harmonic
  series 1, 2, ..., k (k=8); NOT refined.
- **Chordal S² distance**: used as proxy for geodesic distance.
- **Sub-20 decomposition rule**: NOT applied; all 4 corpora are above 20
  items.

## How to regenerate

```bash
python3 documents/github-yubios-KS9n5GAT/papers/scripts/curve-drift-detector.py
```

No external API calls — all 4 corpora are loaded from local disk.
Outputs land in `documents/github-yubios-KS9n5GAT/papers/data/drift-output/`.

## How to read drift signals

- `warp-by-region.csv`: one row per sampled region, prefixed by the
  alignment name (`self-to-docs`, `self-to-refs`, `self-to-cycle4`).
  `flagged=true` rows are candidates for self-archaeology dispatch.
- `drift-priority-list.md`: top 10 flagged regions ranked by drift_score,
  aggregated across all 3 alignments with nearest self + target items
  per region.
- `mobius-transform.json`: the fitted φ_θ per alignment (a, b, c, d ∈ ℂ
  with ad - bc = 1). Apply this Möbius to future curve fits to project
  onto the same warped coordinate system — enables cross-cycle comparison.
- `aligned-curves.png`: visual overlay of all 4 corpus point clouds on
  S² (Mollweide-style projection). 3 warped-self point clouds highlight
  the warp magnitude per alignment.

## Deviations from prior skills

- **Per-corpus basis rule violated** (same as the 2-corpus version):
  `curve-guided-rsi-self` says use a per-corpus basis; this artifact uses
  the SHARED internal-big-picture 9-D for all 4 corpora. Documented.
- **cycle4 scoring uses text-keyword OR'd with native binary coverage**:
  the cycle4 archive has its own 9-D repo-history basis (has_purpose,
  has_sha, ...). For cross-corpus comparison, we re-score cycle4 items
  against the internal-big-picture 9-D keyword vocab (extended to cover
  git/Linear terms). The native coverage is preserved in the cycle4
  archive as ground truth; the cross-corpus score is the proxy.
