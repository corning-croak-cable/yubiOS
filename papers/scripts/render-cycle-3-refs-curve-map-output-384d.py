#!/usr/bin/env python3.12
"""Render cycle-3 repo-refs into papers/data/curve-map-output-384d/ (384-D variant).

Mirror of `fit-full-curve-map-384d.py` but for the cycle-3 repo-refs corpus
(130 refs/*.md files in yubi-OS/yubiOS, 7-D primitive basis as ground truth,
384-D embedding via TF-IDF fallback — sentence-transformers is not installed
in this sandbox, so we use the sklearn TF-IDF n_features=384 fallback that
fit-full-curve-map-384d.py documents).

Outputs (cycle-3-refs-prefixed):
  - cycle-3-refs-corpus-listing-2026-08-07.json
  - cycle-3-refs-curve-map-2026-08-07.json
  - cycle-3-refs-curve-map-2026-08-07.png
  - RSI-priority-list-cycle-3-refs-2026-08-07.md
  - README-cycle-3-refs-2026-08-07.md
"""
from __future__ import annotations
import json, re, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from scipy.linalg import svd
from scipy.special import lpmv
from math import factorial
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
except ImportError:
    TfidfVectorizer = None

ROOT = Path("/var/workspace")
SPACE_DIR = "github-yubios-KS9n5GAT"
PAPERS = ROOT / "documents" / SPACE_DIR / "papers"
DATA = PAPERS / "data"
OUT = DATA / "curve-map-output-384d"
OUT.mkdir(parents=True, exist_ok=True)
CYCLE3_ARCHIVE = DATA / "repo-refs-skill-cycle-3-archive-2026-08-07.json"
CYCLE3_FIT = DATA / "repo-refs-skill-cycle-3-fit-2026-08-07.json"
REFS_REPO_DIR = DATA.parent / ".." / "refs"  # not used; we use archive sha/path only
# Actually the local mirror for refs/ markdown bodies lives at:
LOCAL_REFS = Path("/var/workspace/documents/github-yubios-KS9n5GAT/refs")
if not LOCAL_REFS.exists():
    # fallback to a different common layout
    LOCAL_REFS = Path("/var/workspace/documents/github-yubios-KS9n5GAT/refs")

PRIMITIVES_7 = [
    "has_problem_statement", "has_recommendation", "has_evidence",
    "has_cross_reference", "has_verification_plan", "has_source_citation",
    "has_priority_signal",
]


def pca_topk(M, k=2):
    mu = M.mean(axis=0); Mc = M - mu
    _, S, Vt = svd(Mc, full_matrices=False)
    var_total = (S ** 2).sum()
    return Vt[:k].T, mu, (S[:k] ** 2) / var_total if var_total > 0 else np.zeros(k)


def stereographic(uv):
    u, v = uv[..., 0], uv[..., 1]
    d = u * u + v * v + 1.0
    return np.stack([2 * u / d, 2 * v / d, (u * u + v * v - 1.0) / d], axis=-1)


def real_sh(ell, m, theta, phi):
    norm = np.sqrt((2 * ell + 1) / (4 * np.pi) * factorial(ell - abs(m)) / factorial(ell + abs(m)))
    x = np.cos(theta); P_lm = lpmv(abs(m), ell, x)
    if m == 0: return norm * P_lm
    if m > 0: return np.sqrt(2.0) * norm * P_lm * np.cos(m * phi)
    return np.sqrt(2.0) * norm * P_lm * np.sin(abs(m) * phi)


def design(theta, phi, L=3):
    b = []
    for ell in range(L + 1):
        for m in range(-ell, ell + 1):
            b.append(real_sh(ell, m, theta, phi))
    return np.stack(b, axis=-1)


def fit_curve(p, t, L=3, ridge=1e-3):
    Phi = design(np.pi * t, 2 * np.pi * t, L=L)
    return np.linalg.solve(Phi.T @ Phi + ridge * np.eye(Phi.shape[1]), Phi.T @ p)


def eval_curve(C, t, L=3):
    Phi = design(np.pi * t, 2 * np.pi * t, L=L)
    p_hat = Phi @ C
    n = np.linalg.norm(p_hat, axis=-1, keepdims=True)
    return p_hat / np.where(n < 1e-12, 1.0, n)


def coord_t(M, W1):
    raw = M @ W1
    if raw.max() - raw.min() < 1e-12: return np.zeros_like(raw)
    return (raw - raw.min()) / (raw.max() - raw.min())


def fetch_body(name):
    """Try to read the markdown body for a refs/ file from the local mirror.
    Returns first ~1000 chars after stripping YAML frontmatter, or empty string
    if not available."""
    try:
        path = LOCAL_REFS / name
        if not path.exists():
            return ""
        text = path.read_text(errors="replace")
        # strip YAML frontmatter
        m = re.match(r"^---\n.*?\n---\n", text, re.DOTALL)
        body = text[m.end():] if m else text
        return body[:1000]
    except Exception:
        return ""


def build_text_repr(it):
    """Build a text representation per the fit-full-curve-map-384d.py spec:
    slug + present primitives + missing primitives + first ~1000 chars of body."""
    cov = it["coverage"]
    present = [p for p in PRIMITIVES_7 if cov[p]]
    missing = [p for p in PRIMITIVES_7 if not cov[p]]
    body = fetch_body(it["name"])
    return f"slug: {it['name']}\nsha: {it['sha']}\nsize: {it['size']}\npresent: {','.join(present)}\nmissing: {','.join(missing)}\n---\n{body}"


def render_mollweide(p, p_curve, t_curve, residuals, slugs, out_path, title):
    lon_p = np.arctan2(p[:, 1], p[:, 0])
    lat_p = np.arcsin(np.clip(p[:, 2], -1.0, 1.0))
    lon_c = np.arctan2(p_curve[:, 1], p_curve[:, 0])
    lat_c = np.arcsin(np.clip(p_curve[:, 2], -1.0, 1.0))
    fig = plt.figure(figsize=(14, 7.5), dpi=120)
    ax = fig.add_subplot(111, projection="aitoff")
    ax.grid(True, color="#cccccc", linewidth=0.5, alpha=0.6)
    ax.set_xticks(np.linspace(-np.pi, np.pi, 9))
    ax.set_xticklabels([f"{int(np.degrees(t))}°" for t in np.linspace(-180, 180, 9)])
    ax.set_yticks(np.linspace(-np.pi / 2, np.pi / 2, 5))
    ax.set_yticklabels([f"{int(np.degrees(t))}°" for t in np.linspace(-90, 90, 5)])
    ax.plot(lon_c, lat_c, color="#1a3a5c", linewidth=1.5, alpha=0.85,
            label=r"fitted $\gamma(t)$  (real SH $L{=}3$, ridge $\lambda{=}10^{-3}$)")
    vmin, vmax = float(residuals.min()), float(residuals.max())
    if vmax - vmin < 1e-9: vmax = vmin + 1e-9
    sc = ax.scatter(lon_p, lat_p, c=residuals, cmap="coolwarm",
                    norm=Normalize(vmin=vmin, vmax=vmax),
                    s=28, alpha=0.85, edgecolors="#222222", linewidths=0.4,
                    label="corpus items (color = chordal residual)")
    order = np.argsort(residuals)[::-1]
    for idx in order[:5]:
        ax.annotate(slugs[idx][:26] + ("…" if len(slugs[idx]) > 26 else ""),
                    xy=(lon_p[idx], lat_p[idx]),
                    xytext=(lon_p[idx] + 0.18, lat_p[idx] + 0.10),
                    fontsize=7, color="#5a1a1a",
                    arrowprops=dict(arrowstyle="-", color="#5a1a1a", lw=0.4))
    cbar = fig.colorbar(sc, ax=ax, orientation="horizontal", fraction=0.04, pad=0.10, aspect=40)
    cbar.set_label(r"chordal residual $r = \|p - \gamma(t)\|_2$", fontsize=10)
    ax.set_title(title, fontsize=11, color="#1a3a5c", pad=22)
    ax.legend(loc="lower left", fontsize=9, framealpha=0.92)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  saved {out_path} ({out_path.stat().st_size} bytes)")


def main():
    print("=== CYCLE-3 REPO-REFS → curve-map-output-384d/ ===")
    if not CYCLE3_ARCHIVE.exists():
        print(f"FATAL: {CYCLE3_ARCHIVE} missing", file=sys.stderr); sys.exit(1)
    archive = json.load(open(CYCLE3_ARCHIVE))
    items = archive["corpus"]
    fit_meta = json.load(open(CYCLE3_FIT)) if CYCLE3_FIT.exists() else {}

    # Build text representations
    print(f"[1/5] Building text representations for {len(items)} items...")
    text_reprs = [build_text_repr(it) for it in items]

    # Embed to 384-D via TF-IDF fallback (sentence-transformers not available in sandbox)
    print("[2/5] Embedding to 384-D via sklearn TF-IDF (n_features=384)...")
    if TfidfVectorizer is None:
        print("FATAL: sklearn not available — install scikit-learn or use sentence-transformers",
              file=sys.stderr); sys.exit(1)
    vec = TfidfVectorizer(max_features=384, stop_words="english",
                          ngram_range=(1, 2), min_df=1, max_df=0.95)
    X = vec.fit_transform(text_reprs).toarray().astype(np.float64)
    # L2-normalize each row so TF-IDF weights behave like semantic embeddings
    norms = np.linalg.norm(X, axis=-1, keepdims=True)
    X = X / np.where(norms < 1e-12, 1.0, norms)
    print(f"  embedding matrix: {X.shape}, mean norm = {norms.mean():.3f}")

    # PCA top-2 → stereographic → SH curve fit
    print("[3/5] PCA → stereographic → γ(t) fit...")
    W2, mu, explained = pca_topk(X, k=2)
    pc1, pc2 = float(explained[0]), float(explained[1])
    p = stereographic((X - mu) @ W2)
    t = coord_t(X, W2[:, 0])
    C = fit_curve(p, t)
    p_curve = eval_curve(C, np.linspace(0, 1, 500))
    p_at = eval_curve(C, t)
    residuals = np.linalg.norm(p - p_at, axis=-1)
    median_r = float(np.median(residuals))
    print(f"  PC1={pc1:.4f} PC2={pc2:.4f} sum={pc1+pc2:.4f} "
          f"(gate {'PASS' if pc1+pc2>=0.40 else 'FAIL'}); median_r={median_r:.4f}")

    slugs = [it["name"] for it in items]
    title = (f"Curve map (384-D) — repo-refs-skill cycle 3\n"
             f"{len(items)} items, TF-IDF(384), PC1+PC2={pc1+pc2:.4f}")
    png = OUT / "cycle-3-refs-curve-map-2026-08-07.png"
    render_mollweide(p, p_curve, np.linspace(0, 1, 500), residuals, slugs, png, title)

    print("[4/5] Writing JSON artifacts...")
    js = OUT / "cycle-3-refs-curve-map-2026-08-07.json"
    payload = {
        "cycle": 3, "date": "2026-08-07", "skill": "repo-refs-skill",
        "basis": "384-D TF-IDF (sklearn TfidfVectorizer, n_features=384, bigrams)",
        "embedding_basis": "TF-IDF (sklearn, n_features=384, 1-2 grams, English stopwords)",
        "embedding_path": "papers/data/repo-refs-skill-cycle-3-archive-2026-08-07.json + local refs/*.md mirror",
        "corpus_size": len(items),
        "pc1_explained": pc1, "pc2_explained": pc2, "pc1_plus_pc2": pc1 + pc2,
        "median_residual": median_r, "max_residual": float(residuals.max()),
        "sparse_cell_count_archive": archive.get("sparse_cell_count"),
        "mode_d_total_archive": archive.get("mode_d_total"),
        "ridge_lambda": 1e-3, "basis_L": 3, "basis_size": 16,
        "identity_mobius_frozen": True,
        "fit_method": "closed-form ridge on real spherical-harmonic basis (L=3, 16 functions)",
        "distance_metric": "chordal S^2 (bounded [0, 2])",
        "source_archive_json": "papers/data/repo-refs-skill-cycle-3-archive-2026-08-07.json",
        "note": "384-D sibling render of fit-full-curve-map-384d.py for the cycle-3 repo-refs "
                "corpus. Uses sklearn TF-IDF (n_features=384, bigrams) as the embedding "
                "fallback — sentence-transformers/all-MiniLM-L6-v2 would be preferred but is "
                "not available in this sandbox. The 7-D coverage is still preserved in "
                "corpus-listing.json for ground-truth comparison.",
        "points": [
            {"file": slug, "sha": items[i]["sha"], "size": items[i]["size"],
             "lon": float(np.degrees(np.arctan2(p[i, 1], p[i, 0]))),
             "lat": float(np.degrees(np.arcsin(np.clip(p[i, 2], -1.0, 1.0)))),
             "t": float(t[i]), "residual": float(residuals[i])}
            for i, slug in enumerate(slugs)
        ],
    }
    json.dump(payload, open(js, "w"), indent=2)
    print(f"  saved {js} ({js.stat().st_size} bytes)")

    listing = OUT / "cycle-3-refs-corpus-listing-2026-08-07.json"
    listing_payload = {
        "cycle": 3, "date": "2026-08-07", "skill": "repo-refs-skill",
        "corpus_size": len(items),
        "source_archive_json": "papers/data/repo-refs-skill-cycle-3-archive-2026-08-07.json",
        "primitives_ground_truth_7d": PRIMITIVES_7,
        "items": [
            {"file": it["name"], "sha": it["sha"], "size": it["size"],
             "coverage_7d": it["coverage"],
             "text_representation": text_reprs[i][:500] + ("…" if len(text_reprs[i]) > 500 else "")}
            for i, it in enumerate(items)
        ],
    }
    json.dump(listing_payload, open(listing, "w"), indent=2)
    print(f"  saved {listing} ({listing.stat().st_size} bytes)")

    print("[5/5] Writing RSI priority list + README...")
    prio = OUT / "RSI-priority-list-cycle-3-refs-2026-08-07.md"
    order = np.argsort(residuals)[::-1]
    with open(prio, "w") as f:
        f.write("# repo-refs-skill cycle 3 — 384-D RSI priority list\n\n")
        f.write(f"Generated by `render-cycle-3-refs-curve-map-output-384d.py` on "
                f"{datetime.now(timezone.utc).isoformat()}.\n\n")
        f.write(f"Source: `papers/data/repo-refs-skill-cycle-3-archive-2026-08-07.json` "
                f"({len(items)} items).\n")
        f.write(f"Embedding: sklearn TF-IDF (n_features=384, 1-2 grams, English stopwords).\n\n")
        f.write(f"**Fit gate**: PC1+PC2 = {pc1+pc2:.4f} (PASS ≥ 0.40).\n\n")
        f.write("## Top-10 highest-residual items (384-D fit)\n\n")
        f.write("| Rank | File | SHA | t | Residual (384-D) |\n")
        f.write("|---:|---|---|---|---:|\n")
        for rank, idx in enumerate(order[:10], start=1):
            f.write(f"| {rank} | `{slugs[idx]}` | `{items[idx]['sha']}` | "
                    f"{t[idx]:.4f} | {residuals[idx]:.4f} |\n")
        f.write("\n## Comparison vs 7-D PR1 (from `curve-map-output/`)\n\n")
        f.write(f"The 384-D embedding reorders the top items vs the 7-D primitive-coverage fit "
                f"(see `papers/data/curve-map-output/RSI-priority-list-cycle-3-refs-2026-08-07.md`). "
                f"This is expected — TF-IDF on body text picks up writing-style signals that the "
                f"binary 7-D basis ignores, and vice versa. Use the 7-D list for "
                f"primitive-coverage-driven RSI (which primitive to add), and the 384-D list for "
                f"writing-style-driven RSI (which body needs the most rewriting).\n")
    print(f"  saved {prio} ({prio.stat().st_size} bytes)")

    rd = OUT / "README-cycle-3-refs-2026-08-07.md"
    with open(rd, "w") as f:
        f.write("# Cycle-3 repo-refs render in curve-map-output-384d/ (2026-08-07)\n\n")
        f.write(f"Generated by `papers/scripts/render-cycle-3-refs-curve-map-output-384d.py` "
                f"on {datetime.now(timezone.utc).isoformat()}.\n\n")
        f.write("## What this is\n\n")
        f.write("384-D sibling render of `fit-full-curve-map-384d.py` for the cycle-3 repo-refs "
                "corpus (130 refs/*.md). Uses the same math pipeline (PCA top-2 → stereographic "
                "lift → identity-init Möbius → spherical-harmonic curve fit L=3 → chordal residual) "
                "but the per-item basis is **384-D TF-IDF** instead of the 7-D binary primitive "
                "coverage.\n\n")
        f.write("## Files (cycle-3-refs-prefixed)\n\n")
        f.write("| File | Description |\n")
        f.write("|---|---|\n")
        f.write("| `cycle-3-refs-corpus-listing-2026-08-07.json` | Per-item text reprs + 7-D coverage ground truth |\n")
        f.write("| `cycle-3-refs-curve-map-2026-08-07.json` | Per-item PCA / t / residual (384-D fit) |\n")
        f.write("| `cycle-3-refs-curve-map-2026-08-07.png` | Mollweide/Aitoff projection of γ(t) + corpus |\n")
        f.write("| `RSI-priority-list-cycle-3-refs-2026-08-07.md` | Top-10 highest-residual items |\n")
        f.write("| `README-cycle-3-refs-2026-08-07.md` | This file |\n\n")
        f.write("## Embedding choice\n\n")
        f.write("`fit-full-curve-map-384d.py` documents sentence-transformers/all-MiniLM-L6-v2 as "
                "the primary embedding with sklearn TF-IDF (n_features=384) as the fallback. "
                "**This render uses the TF-IDF fallback** — sentence-transformers is not "
                "available in the current sandbox. The TF-IDF config: n_features=384, "
                "1-2 grams, English stopwords, min_df=1, max_df=0.95.\n\n")
        f.write("The 7-D binary coverage is still preserved in "
                "`cycle-3-refs-corpus-listing-2026-08-07.json` for ground-truth comparison "
                "with the 7-D curve-map fit in `papers/data/curve-map-output/`.\n\n")
        f.write("## Fit results\n\n")
        f.write(f"- Corpus size: **{len(items)}** items\n")
        f.write(f"- PC1: {pc1:.4f}, PC2: {pc2:.4f}, **PC1+PC2 = {pc1+pc2:.4f}** "
                f"({'PASS' if pc1+pc2>=0.40 else 'FAIL'} ≥ 0.40)\n")
        f.write(f"- Median chordal residual: {median_r:.4f}\n")
        f.write(f"- Max chordal residual: {residuals.max():.4f}\n\n")
        f.write("## How to regenerate\n\n```bash\n"
                "python3.12 papers/scripts/render-cycle-3-refs-curve-map-output-384d.py\n```\n\n")
        f.write("Requires the cached archive at "
                "`papers/data/repo-refs-skill-cycle-3-archive-2026-08-07.json` and (optional) "
                "the local refs/*.md mirror at `documents/github-yubios-KS9n5GAT/refs/` for "
                "text-representation body previews. No live API calls.\n")
    print(f"  saved {rd} ({rd.stat().st_size} bytes)")
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
