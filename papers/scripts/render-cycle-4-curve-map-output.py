#!/usr/bin/env python3.12
"""render-cycle-4-curve-map-output.py — Cycle-4 repo-history render into
`papers/data/curve-map-output/` (the PLAIN directory, not the -384d one).

This is the sibling of `render-cycle-4-fit.py` (which writes into
`curve-map-output-384d/`). User asked to add the cycle-4 repo-history render
to "the other renders that use the curve PCA" — i.e. the plain
`curve-map-output/` directory that `fit-full-curve-map.py` normally owns.

`fit-full-curve-map.py`'s own corpus (`rsi-79-corpus-multi-cycle-2026-08-06.json`,
9-D internal-big-picture basis) is a DIFFERENT primitive space from the
repo-history-skill's 9-D basis (has_purpose, has_sha, has_pr_ref, ...). Rather
than conflate the two, this script writes cycle-4-prefixed sibling files
into the SAME directory so both corpora's fits live side by side without
clobbering `curve-map.png` / `curve-map.json` / `RSI-priority-list.md` /
`corpus-listing.json` / `README.md` (the fit-full-curve-map.py outputs).

Reuses the cached 324-item archive
(`papers/data/repo-history-skill-cycle-4-archive-2026-08-07.json`) — no live
API calls needed; the corpus was already fetched for the -384d render.

Pipeline (identical math to `render-cycle-4-fit.py` / `fit-full-curve-map.py`):
  1. Load 9-D binary coverage matrix from the cached archive.
  2. PCA top-2 → stereographic lift from south pole → S².
  3. Identity-init Möbius (frozen φ_θ).
  4. 1-D coordinate t = PC1 of centered coverage, min-max scaled to [0,1].
  5. Fit γ(t) on real SH basis (L=3, 16 functions) via closed-form ridge (λ=1e-3).
  6. Chordal residual r_i = ‖p_i − γ(t_i)‖₂ ∈ [0, 2].
  7. Render Mollweide/Aitoff PNG (coolwarm cmap), JSON, priority list, README.

Outputs (in `papers/data/curve-map-output/`, cycle-4-prefixed):
  - cycle-4-repo-history-curve-map-2026-08-07.png
  - cycle-4-repo-history-curve-map-2026-08-07.json
  - RSI-priority-list-cycle-4-repo-history-2026-08-07.md
  - README-cycle-4-repo-history-2026-08-07.md
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from scipy.linalg import svd
from scipy.special import lpmv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

# --------------------------------------------------------------------------- #
# 0. Paths.
# --------------------------------------------------------------------------- #
ROOT = Path("/var/workspace")
SPACE_DIR = "github-yubios-KS9n5GAT"
PAPERS_DIR = ROOT / "documents" / SPACE_DIR / "papers"
DATA_DIR = PAPERS_DIR / "data"
OUT_DIR = DATA_DIR / "curve-map-output"  # the PLAIN directory (sibling to -384d)
OUT_DIR.mkdir(parents=True, exist_ok=True)

CYCLE4_ARCHIVE_JSON = DATA_DIR / "repo-history-skill-cycle-4-archive-2026-08-07.json"

PRIMITIVES_9: List[str] = [
    "has_purpose", "has_sha", "has_pr_ref", "has_linear_ref",
    "has_state_progression", "has_author", "has_cross_corpus_link",
    "has_evidence", "has_temporal_anchor",
]


# --------------------------------------------------------------------------- #
# 1. Math pipeline (identical to render-cycle-4-fit.py).
# --------------------------------------------------------------------------- #
def pca_topk(M: np.ndarray, k: int = 2) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    mu = M.mean(axis=0)
    Mc = M - mu
    U, S, Vt = svd(Mc, full_matrices=False)
    Wk = Vt[:k].T
    var_total = (S ** 2).sum()
    explained = (S[:k] ** 2) / var_total if var_total > 0 else np.zeros(k)
    return Wk, mu, explained


def stereographic_from_south_pole(uv: np.ndarray) -> np.ndarray:
    u, v = uv[..., 0], uv[..., 1]
    denom = u * u + v * v + 1.0
    X = 2.0 * u / denom
    Y = 2.0 * v / denom
    Z = (u * u + v * v - 1.0) / denom
    return np.stack([X, Y, Z], axis=-1)


def real_spherical_harmonic_basis(ell: int, m: int, theta: np.ndarray, phi: np.ndarray) -> np.ndarray:
    from math import factorial
    norm = np.sqrt((2 * ell + 1) / (4 * np.pi) * factorial(ell - abs(m)) / factorial(ell + abs(m)))
    x = np.cos(theta)
    P_lm = lpmv(abs(m), ell, x)
    if m == 0:
        return norm * P_lm
    elif m > 0:
        return np.sqrt(2.0) * norm * P_lm * np.cos(m * phi)
    else:
        return np.sqrt(2.0) * norm * P_lm * np.sin(abs(m) * phi)


def design_matrix(theta: np.ndarray, phi: np.ndarray, L: int = 3) -> np.ndarray:
    basis = []
    for ell in range(L + 1):
        for m in range(-ell, ell + 1):
            basis.append(real_spherical_harmonic_basis(ell, m, theta, phi))
    return np.stack(basis, axis=-1)


def fit_harmonic_curve(p: np.ndarray, t: np.ndarray, L: int = 3, ridge_lambda: float = 1e-3):
    theta = np.pi * t
    phi = 2.0 * np.pi * t
    Phi = design_matrix(theta, phi, L=L)
    PtP = Phi.T @ Phi
    PtP_ridge = PtP + ridge_lambda * np.eye(PtP.shape[0])
    C = np.linalg.solve(PtP_ridge, Phi.T @ p)
    return C, Phi


def evaluate_curve(C: np.ndarray, t: np.ndarray, L: int = 3) -> np.ndarray:
    theta = np.pi * t
    phi = 2.0 * np.pi * t
    Phi = design_matrix(theta, phi, L=L)
    p_hat = Phi @ C
    norm = np.linalg.norm(p_hat, axis=-1, keepdims=True)
    norm = np.where(norm < 1e-12, 1.0, norm)
    return p_hat / norm


def coordinate_t(M: np.ndarray, W1: np.ndarray) -> np.ndarray:
    raw = M @ W1
    if raw.max() - raw.min() < 1e-12:
        return np.zeros_like(raw)
    return (raw - raw.min()) / (raw.max() - raw.min())


def chordal_residual(p: np.ndarray, p_hat: np.ndarray) -> np.ndarray:
    return np.linalg.norm(p - p_hat, axis=-1)


def render_curve_map(p, p_hat_curve, t_curve, residuals, slugs, primitives, out_path, title):
    def to_lonlat(p_xyz):
        x, y, z = p_xyz[..., 0], p_xyz[..., 1], p_xyz[..., 2]
        return np.arctan2(y, x), np.arcsin(np.clip(z, -1.0, 1.0))

    lon_p, lat_p = to_lonlat(p)
    lon_curve, lat_curve = to_lonlat(p_hat_curve)

    fig = plt.figure(figsize=(14, 7.5), dpi=120)
    ax = fig.add_subplot(111, projection="aitoff")
    ax.grid(True, color="#cccccc", linewidth=0.5, alpha=0.6)
    ax.set_xticks(np.linspace(-np.pi, np.pi, 9))
    ax.set_xticklabels([f"{int(np.degrees(t))}°" for t in np.linspace(-180, 180, 9)])
    ax.set_yticks(np.linspace(-np.pi / 2, np.pi / 2, 5))
    ax.set_yticklabels([f"{int(np.degrees(t))}°" for t in np.linspace(-90, 90, 5)])

    ax.plot(lon_curve, lat_curve, color="#1a3a5c", linewidth=1.5, alpha=0.85,
            label=r"fitted $\gamma(t)$  (real SH $L{=}3$, ridge $\lambda{=}10^{-3}$)")

    vmin, vmax = float(residuals.min()), float(residuals.max())
    if vmax - vmin < 1e-9:
        vmax = vmin + 1e-9
    norm = Normalize(vmin=vmin, vmax=vmax)
    cmap = matplotlib.colormaps["coolwarm"]
    sc = ax.scatter(lon_p, lat_p, c=residuals, cmap=cmap, norm=norm,
                    s=28, alpha=0.85, edgecolors="#222222", linewidths=0.4,
                    label="corpus items (color = chordal residual)")

    order = np.argsort(residuals)[::-1]
    for idx in order[:5]:
        ax.annotate(slugs[idx][:22] + ("…" if len(slugs[idx]) > 22 else ""),
                    xy=(lon_p[idx], lat_p[idx]),
                    xytext=(lon_p[idx] + 0.18, lat_p[idx] + 0.10),
                    fontsize=7, color="#5a1a1a",
                    arrowprops=dict(arrowstyle="-", color="#5a1a1a", lw=0.4))

    cbar = fig.colorbar(sc, ax=ax, orientation="horizontal", fraction=0.04, pad=0.10, aspect=40)
    cbar.set_label(r"chordal residual $r = \|p - \gamma(t)\|_2$  (high = red, low = blue)",
                   fontsize=10, color="#222222")
    ax.set_title(title, fontsize=11, color="#1a3a5c", pad=22)
    ax.legend(loc="lower left", fontsize=9, framealpha=0.92)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  saved {out_path} ({out_path.stat().st_size} bytes)")


def main() -> None:
    print("=== CYCLE 4 REPO-HISTORY RENDER → curve-map-output/ (plain dir) ===")
    print(f"Date: {datetime.now(timezone.utc).isoformat()}")
    print(f"Output: {OUT_DIR}\n")

    if not CYCLE4_ARCHIVE_JSON.exists():
        print(f"FATAL: {CYCLE4_ARCHIVE_JSON} not found — run render-cycle-4-fit.py first "
              f"to fetch + cache the 324-item archive.", file=sys.stderr)
        sys.exit(1)

    print(f"[1/4] Loading cached archive from {CYCLE4_ARCHIVE_JSON}")
    with open(CYCLE4_ARCHIVE_JSON) as f:
        archive = json.load(f)
    items_meta = archive["items"]
    slugs = [f"{it['kind']}-{it['label']}" for it in items_meta]
    coverage_rows = np.array([it["coverage"] for it in items_meta], dtype=np.float64)
    missing_map = {slug: it["missing"] for slug, it in zip(slugs, items_meta)}
    print(f"  loaded {len(items_meta)} items, coverage shape {coverage_rows.shape}")

    print(f"\n[2/4] PCA top-2 → stereographic → identity Möbius (frozen φ_θ)")
    W2, mu, explained = pca_topk(coverage_rows, k=2)
    pc1, pc2 = float(explained[0]), float(explained[1])
    print(f"  PC1={pc1:.4f}, PC2={pc2:.4f}, sum={pc1+pc2:.4f} (gate ≥ 0.40: "
          f"{'PASS' if pc1+pc2 >= 0.40 else 'FAIL'})")

    Mc = coverage_rows - mu
    uv = Mc @ W2
    p = stereographic_from_south_pole(uv)
    W1 = W2[:, 0]
    t = coordinate_t(coverage_rows, W1)

    print(f"\n[3/4] Fitting γ(t) on real SH basis (L=3) via closed-form ridge")
    C_curve, _ = fit_harmonic_curve(p, t, L=3, ridge_lambda=1e-3)
    t_curve = np.linspace(0, 1, 500)
    p_hat_curve = evaluate_curve(C_curve, t_curve, L=3)
    p_at_t = evaluate_curve(C_curve, t, L=3)
    residuals = chordal_residual(p, p_at_t)
    median_res = float(np.median(residuals))
    print(f"  residuals: min={residuals.min():.4f}, median={median_res:.4f}, max={residuals.max():.4f}")

    title = (
        f"Curve map — repo-history-skill cycle 4, rendered into curve-map-output/\n"
        f"{len(items_meta)} items, 9-D basis, PC1+PC2={pc1+pc2:.4f}, "
        f"identity-init Möbius (frozen $\\varphi_\\theta$)"
    )
    png_path = OUT_DIR / "cycle-4-repo-history-curve-map-2026-08-07.png"
    render_curve_map(p, p_hat_curve, t_curve, residuals, slugs, PRIMITIVES_9, png_path, title)

    print(f"\n[4/4] Writing JSON + priority list + README")
    json_path = OUT_DIR / "cycle-4-repo-history-curve-map-2026-08-07.json"
    curve_map = {
        "cycle": 4, "date": "2026-08-07",
        "basis": "9-D binary (repo-history-skill)",
        "primitives": PRIMITIVES_9,
        "corpus_size": len(items_meta),
        "corpus_breakdown": archive["corpus_breakdown"],
        "pc1_explained": pc1, "pc2_explained": pc2, "pc1_plus_pc2": pc1 + pc2,
        "ridge_lambda": 1e-3, "basis_L": 3, "basis_size": 16,
        "identity_mobius_frozen": True,
        "fit_method": "closed-form ridge on real spherical-harmonic basis (L=3, 16 functions)",
        "distance_metric": "chordal S^2 (bounded [0, 2])",
        "source_archive_json": str(CYCLE4_ARCHIVE_JSON.relative_to(ROOT)),
        "note": "Sibling render of render-cycle-4-fit.py, written into the PLAIN "
                "curve-map-output/ directory (not -384d) alongside the unrelated "
                "79-skill/internal-big-picture fit owned by fit-full-curve-map.py. "
                "Different corpus, different 9-D primitive basis — files are "
                "cycle-4-repo-history-prefixed to avoid collision.",
        "points": [
            {
                "file": slug,
                "lon": float(np.degrees(np.arctan2(p[i, 1], p[i, 0]))),
                "lat": float(np.degrees(np.arcsin(np.clip(p[i, 2], -1.0, 1.0)))),
                "t": float(t[i]), "residual": float(residuals[i]),
                "missing_primitives": missing_map[slug],
            }
            for i, slug in enumerate(slugs)
        ],
    }
    with open(json_path, "w") as f:
        json.dump(curve_map, f, indent=2)
    print(f"  saved {json_path} ({json_path.stat().st_size} bytes)")

    order = np.argsort(residuals)[::-1]
    top10 = order[:10]
    priority_md = OUT_DIR / "RSI-priority-list-cycle-4-repo-history-2026-08-07.md"
    with open(priority_md, "w") as f:
        f.write("# repo-history-skill — cycle-4 RSI priority list (rendered into curve-map-output/)\n\n")
        f.write(f"Generated by `render-cycle-4-curve-map-output.py` on {datetime.now(timezone.utc).isoformat()}.\n\n")
        f.write(f"Source: `{CYCLE4_ARCHIVE_JSON.relative_to(ROOT)}` ({len(items_meta)} items).\n\n")
        f.write(f"**Fit gate**: PC1+PC2 = {pc1+pc2:.4f} (PASS ≥ 0.40).\n\n")
        f.write("## Top-10 highest-residual items\n\n")
        f.write("| Rank | File | Kind | Label | t | Residual | Missing primitives |\n")
        f.write("|---:|---|---|---|---:|---:|---|\n")
        for rank, idx in enumerate(top10, start=1):
            f.write(f"| {rank} | `{slugs[idx]}` | {items_meta[idx]['kind']} | {items_meta[idx]['label']} | "
                    f"{t[idx]:.4f} | {residuals[idx]:.4f} | {', '.join(missing_map[slugs[idx]]) or '(none)'} |\n")
    print(f"  saved {priority_md} ({priority_md.stat().st_size} bytes)")

    readme_path = OUT_DIR / "README-cycle-4-repo-history-2026-08-07.md"
    with open(readme_path, "w") as f:
        f.write("# Cycle-4 repo-history render, in curve-map-output/ (2026-08-07)\n\n")
        f.write(f"Generated by `papers/scripts/render-cycle-4-curve-map-output.py` on "
                f"{datetime.now(timezone.utc).isoformat()}.\n\n")
        f.write("## Why this file exists here\n\n")
        f.write("`curve-map-output/` is normally owned by `fit-full-curve-map.py`, which fits the "
                "**79-skill corpus** on the `internal-big-picture` 9-D primitive basis (attestation, "
                "trust_chain, least_privilege, ...). That is a DIFFERENT corpus and a DIFFERENT 9-D "
                "primitive space from the `repo-history-skill` corpus (has_purpose, has_sha, has_pr_ref, "
                "...). Rather than merge two unrelated primitive bases into one fit, this script writes "
                "a **cycle-4-repo-history-prefixed sibling render** into the same directory so both "
                "corpora's fits are discoverable side by side without collision:\n\n")
        f.write("| File | Owner | Corpus | Basis |\n")
        f.write("|---|---|---|---|\n")
        f.write("| `curve-map.png` / `curve-map.json` / `RSI-priority-list.md` / `corpus-listing.json` / `README.md` | "
                "`fit-full-curve-map.py` | 79 skills | internal-big-picture (9-D) |\n")
        f.write("| `cycle-4-repo-history-curve-map-2026-08-07.{png,json}`, `RSI-priority-list-cycle-4-repo-history-2026-08-07.md`, "
                "this file | `render-cycle-4-curve-map-output.py` | 324 repo-history events (PRs/Issues/Commits/"
                "Releases/Linear OMN) | repo-history-skill (9-D) |\n\n")
        f.write("## Cycle-4 fit results\n\n")
        f.write(f"- Corpus size: **{len(items_meta)}** items ({archive['corpus_breakdown']})\n")
        f.write(f"- PC1 explained variance: {pc1:.4f}\n")
        f.write(f"- PC2 explained variance: {pc2:.4f}\n")
        f.write(f"- **PC1+PC2 = {pc1+pc2:.4f}** (gate ≥ 0.40, "
                f"{'PASS' if pc1+pc2 >= 0.40 else 'FAIL'})\n")
        f.write(f"- Median chordal residual: {median_res:.4f}\n")
        f.write(f"- Max chordal residual: {residuals.max():.4f}\n\n")
        f.write("## How to regenerate\n\n```bash\npython3.12 papers/scripts/render-cycle-4-curve-map-output.py\n```\n\n")
        f.write("Requires the cached archive at "
                f"`{CYCLE4_ARCHIVE_JSON.relative_to(ROOT)}` (produced by `render-cycle-4-fit.py`'s "
                "corpus fetch step). No live API calls in this script — it's a pure re-render of "
                "already-fetched data into a different output directory.\n")
    print(f"  saved {readme_path} ({readme_path.stat().st_size} bytes)")

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
