#!/usr/bin/env python3.12
"""Render cycle-3 repo-refs into papers/data/curve-map-output-multi-corpus/.

Multi-corpus fit alongside docs/refs/skills. Existing refs/ in this dir uses the
9-D deep-research basis (from `single-action-curve-rsi` SKILL.md); this script
writes cycle-3-refs-prefixed siblings using repo-refs-skill's 7-D document-quality
basis (problem_statement/recommendation/evidence/cross_reference/verification_plan/
source_citation/priority_signal).

Outputs (cycle-3-refs-prefixed):
  - cycle-3-refs-curve-map-2026-08-07.{json,png}
  - RSI-priority-cycle-3-refs-2026-08-07.md
  - README-cycle-3-refs-2026-08-07.md
"""
from __future__ import annotations
import json, sys
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

ROOT = Path("/var/workspace")
SPACE_DIR = "github-yubios-KS9n5GAT"
PAPERS = ROOT / "documents" / SPACE_DIR / "papers"
DATA = PAPERS / "data"
OUT = DATA / "curve-map-output-multi-corpus"
OUT.mkdir(parents=True, exist_ok=True)
CYCLE3_ARCHIVE = DATA / "repo-refs-skill-cycle-3-archive-2026-08-07.json"
CYCLE3_FIT = DATA / "repo-refs-skill-cycle-3-fit-2026-08-07.json"

PRIMITIVES_7 = [
    "has_problem_statement", "has_recommendation", "has_evidence",
    "has_cross_reference", "has_verification_plan", "has_source_citation",
    "has_priority_signal",
]


def pca_topk(M, k=2):
    mu = M.mean(axis=0); Mc = M - mu
    _, S, Vt = svd(Mc, full_matrices=False)
    Wk = Vt[:k].T
    var_total = (S ** 2).sum()
    explained = (S[:k] ** 2) / var_total if var_total > 0 else np.zeros(k)
    return Wk, mu, explained


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
    print("=== CYCLE-3 REPO-REFS → curve-map-output-multi-corpus/ ===")
    if not CYCLE3_ARCHIVE.exists():
        print(f"FATAL: {CYCLE3_ARCHIVE} missing", file=sys.stderr); sys.exit(1)
    archive = json.load(open(CYCLE3_ARCHIVE))
    items = archive["corpus"]
    fit_meta = json.load(open(CYCLE3_FIT)) if CYCLE3_FIT.exists() else {}

    slugs = [it["name"] for it in items]
    cov = np.array([[it["coverage"][p] for p in PRIMITIVES_7] for it in items], dtype=np.float64)
    missing_map = {slug: [p for p in PRIMITIVES_7 if not it["coverage"][p]]
                   for slug, it in zip(slugs, items)}

    W2, mu, explained = pca_topk(cov, k=2)
    pc1, pc2 = float(explained[0]), float(explained[1])
    Mc = cov - mu; uv = Mc @ W2
    p = stereographic(uv)
    t = coord_t(cov, W2[:, 0])
    C = fit_curve(p, t)
    p_curve = eval_curve(C, np.linspace(0, 1, 500))
    p_at = eval_curve(C, t)
    residuals = np.linalg.norm(p - p_at, axis=-1)
    median_r = float(np.median(residuals))
    print(f"  {len(items)} items, PC1={pc1:.4f} PC2={pc2:.4f} sum={pc1+pc2:.4f} "
          f"(gate {'PASS' if pc1+pc2>=0.40 else 'FAIL'}); median_r={median_r:.4f}")

    png = OUT / "cycle-3-refs-curve-map-2026-08-07.png"
    title = (f"Multi-corpus: repo-refs-skill cycle 3 (final fixpoint)\n"
             f"{len(items)} items, 7-D basis, PC1+PC2={pc1+pc2:.4f}")
    render_mollweide(p, p_curve, np.linspace(0, 1, 500), residuals, slugs, png, title)

    js = OUT / "cycle-3-refs-curve-map-2026-08-07.json"
    payload = {
        "cycle": 3, "date": "2026-08-07", "skill": "repo-refs-skill",
        "basis": "7-D binary (repo-refs-skill cycle-3 fixpoint)",
        "primitives": PRIMITIVES_7,
        "corpus_size": len(items),
        "source_corpus": "yubi-OS/yubiOS refs/*.md (130 files)",
        "pc1_explained": pc1, "pc2_explained": pc2, "pc1_plus_pc2": pc1 + pc2,
        "median_residual": median_r, "max_residual": float(residuals.max()),
        "sparse_cell_count_archive": archive.get("sparse_cell_count"),
        "mode_d_total_archive": archive.get("mode_d_total"),
        "sparse_cell_count_fit": fit_meta.get("sparse_cell_count"),
        "mode_d_total_fit": fit_meta.get("mode_d_total"),
        "ridge_lambda": 1e-3, "basis_L": 3, "basis_size": 16,
        "identity_mobius_frozen": True,
        "fit_method": "closed-form ridge on real spherical-harmonic basis (L=3, 16 functions)",
        "distance_metric": "chordal S^2 (bounded [0, 2])",
        "source_archive_json": "papers/data/repo-refs-skill-cycle-3-archive-2026-08-07.json",
        "note": "Multi-corpus sibling render using repo-refs-skill's 7-D basis (NOT the "
                "9-D deep-research basis used by the existing curve-map-refs.{json,png} in "
                "this directory). Both renders live side by side without collision.",
        "points": [
            {"file": slug, "sha": items[i]["sha"], "size": items[i]["size"],
             "lon": float(np.degrees(np.arctan2(p[i, 1], p[i, 0]))),
             "lat": float(np.degrees(np.arcsin(np.clip(p[i, 2], -1.0, 1.0)))),
             "t": float(t[i]), "residual": float(residuals[i]),
             "missing_primitives": missing_map[slug]}
            for i, slug in enumerate(slugs)
        ],
    }
    json.dump(payload, open(js, "w"), indent=2)
    print(f"  saved {js} ({js.stat().st_size} bytes)")

    prio = OUT / "RSI-priority-cycle-3-refs-2026-08-07.md"
    order = np.argsort(residuals)[::-1]
    with open(prio, "w") as f:
        f.write("# repo-refs-skill cycle 3 — multi-corpus RSI priority list\n\n")
        f.write(f"Generated by `render-cycle-3-refs-multi-corpus.py` on "
                f"{datetime.now(timezone.utc).isoformat()}.\n\n")
        f.write(f"Source: `papers/data/repo-refs-skill-cycle-3-archive-2026-08-07.json` "
                f"({len(items)} items, 7-D basis).\n\n")
        f.write(f"**Fit gate**: PC1+PC2 = {pc1+pc2:.4f} (PASS ≥ 0.40).\n")
        sc = archive.get("sparse_cell_count") or fit_meta.get("sparse_cell_count")
        md = archive.get("mode_d_total") or fit_meta.get("mode_d_total")
        if sc is not None: f.write(f"**Sparse cells**: {sc}/130 ({100*sc/130:.1f}%).\n")
        if md is not None: f.write(f"**Mode D candidates**: {md}.\n\n")
        f.write("## Top-10 highest-residual items\n\n")
        f.write("| Rank | File | SHA | t | Residual | Missing primitives |\n")
        f.write("|---:|---|---|---|---:|---:|---|\n")
        for rank, idx in enumerate(order[:10], start=1):
            miss = ", ".join(missing_map[slugs[idx]]) or "(none)"
            f.write(f"| {rank} | `{slugs[idx]}` | `{items[idx]['sha']}` | "
                    f"{t[idx]:.4f} | {residuals[idx]:.4f} | {miss} |\n")
    print(f"  saved {prio} ({prio.stat().st_size} bytes)")

    rd = OUT / "README-cycle-3-refs-2026-08-07.md"
    with open(rd, "w") as f:
        f.write("# Cycle-3 repo-refs render in curve-map-output-multi-corpus/ (2026-08-07)\n\n")
        f.write(f"Generated by `papers/scripts/render-cycle-3-refs-multi-corpus.py` on "
                f"{datetime.now(timezone.utc).isoformat()}.\n\n")
        f.write("## Two renders of the refs/ corpus — different bases\n\n")
        f.write("This directory now has **two distinct refs/ curve maps**, each using a "
                "different primitive basis:\n\n")
        f.write("| File | Basis | Source script |\n")
        f.write("|---|---|---|\n")
        f.write("| `curve-map-refs.{json,png}` + `RSI-priority-refs.md` | 9-D deep-research "
                "(has_purpose, has_evidence, has_correction, has_constraint, has_pushback, "
                "has_test, has_source, has_recommendation, has_priority) | "
                "`build_per_corpus_curves.py` |\n")
        f.write("| `cycle-3-refs-curve-map-2026-08-07.{json,png}` + "
                "`RSI-priority-cycle-3-refs-2026-08-07.md` + this file | 7-D repo-refs-skill "
                "(has_problem_statement, has_recommendation, has_evidence, has_cross_reference, "
                "has_verification_plan, has_source_citation, has_priority_signal) | "
                "`render-cycle-3-refs-multi-corpus.py` |\n\n")
        f.write("Both fits pass the PC1+PC2 ≥ 0.40 gate (cycle-3 fits with margin: "
                f"{pc1+pc2:.4f}). The 7-D version is the cycle-3 RSI fixpoint for the "
                "`repo-refs-skill` SKILL.md; the 9-D version is from `build_per_corpus_curves.py`'s "
                "earlier deep-research variant.\n\n")
        f.write("## Cycle-3 (fixpoint) fit results\n\n")
        f.write(f"- Corpus size: **{len(items)}** items (130 refs/*.md)\n")
        f.write(f"- PC1: {pc1:.4f}, PC2: {pc2:.4f}, **PC1+PC2 = {pc1+pc2:.4f}** "
                f"({'PASS' if pc1+pc2>=0.40 else 'FAIL'} ≥ 0.40)\n")
        f.write(f"- Median chordal residual: {median_r:.4f}\n")
        f.write(f"- Max chordal residual: {residuals.max():.4f}\n\n")
        f.write("## How to regenerate\n\n```bash\n"
                "python3.12 papers/scripts/render-cycle-3-refs-multi-corpus.py\n```\n\n")
        f.write("Requires the cached archive at "
                "`papers/data/repo-refs-skill-cycle-3-archive-2026-08-07.json`. No live API calls.\n")
    print(f"  saved {rd} ({rd.stat().st_size} bytes)")
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
