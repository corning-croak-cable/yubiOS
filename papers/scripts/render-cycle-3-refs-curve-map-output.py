#!/usr/bin/env python3.12
"""Render cycle-3 repo-refs-skill curve-map into papers/data/curve-map-output/.

Schema for the cycle-3 archive (papers/data/repo-refs-skill-cycle-3-archive-2026-08-07.json):
  top-level: corpus (list of 130), N_files, basis_dim=7, prim_survival (kept 7), PC1_PC2=0.4686
  each item: {name, sha, size, coverage: {7-primitive dict}}

Outputs (in papers/data/curve-map-output/, cycle-3-refs-prefixed):
  - cycle-3-refs-curve-map-2026-08-07.png  (Mollweide, chordal-residual colored)
  - cycle-3-refs-curve-map-2026-08-07.json (PCA + stereographic + per-item coords)
  - RSI-priority-list-cycle-3-refs-2026-08-07.md (top-10 highest-residual items)
  - README-cycle-3-refs-2026-08-07.md
"""
from __future__ import annotations

import json
import sys
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
PAPERS_DIR = ROOT / "documents" / SPACE_DIR / "papers"
DATA_DIR = PAPERS_DIR / "data"
OUT_DIR = DATA_DIR / "curve-map-output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CYCLE3_ARCHIVE_JSON = DATA_DIR / "repo-refs-skill-cycle-3-archive-2026-08-07.json"
CYCLE3_FIT_JSON = DATA_DIR / "repo-refs-skill-cycle-3-fit-2026-08-07.json"

PRIMITIVES_7 = [
    "has_problem_statement", "has_recommendation", "has_evidence",
    "has_cross_reference", "has_verification_plan", "has_source_citation",
    "has_priority_signal",
]


def pca_topk(M, k=2):
    mu = M.mean(axis=0)
    Mc = M - mu
    U, S, Vt = svd(Mc, full_matrices=False)
    Wk = Vt[:k].T
    var_total = (S ** 2).sum()
    explained = (S[:k] ** 2) / var_total if var_total > 0 else np.zeros(k)
    return Wk, mu, explained


def stereographic_from_south_pole(uv):
    u, v = uv[..., 0], uv[..., 1]
    denom = u * u + v * v + 1.0
    return np.stack([2.0 * u / denom, 2.0 * v / denom, (u * u + v * v - 1.0) / denom], axis=-1)


def real_sh(ell, m, theta, phi):
    norm = np.sqrt((2 * ell + 1) / (4 * np.pi) * factorial(ell - abs(m)) / factorial(ell + abs(m)))
    x = np.cos(theta)
    P_lm = lpmv(abs(m), ell, x)
    if m == 0:
        return norm * P_lm
    elif m > 0:
        return np.sqrt(2.0) * norm * P_lm * np.cos(m * phi)
    else:
        return np.sqrt(2.0) * norm * P_lm * np.sin(abs(m) * phi)


def design_matrix(theta, phi, L=3):
    basis = []
    for ell in range(L + 1):
        for m in range(-ell, ell + 1):
            basis.append(real_sh(ell, m, theta, phi))
    return np.stack(basis, axis=-1)


def fit_curve(p, t, L=3, ridge=1e-3):
    Phi = design_matrix(np.pi * t, 2 * np.pi * t, L=L)
    PtP_ridge = Phi.T @ Phi + ridge * np.eye(Phi.shape[1])
    return np.linalg.solve(PtP_ridge, Phi.T @ p), Phi


def evaluate_curve(C, t, L=3):
    Phi = design_matrix(np.pi * t, 2 * np.pi * t, L=L)
    p_hat = Phi @ C
    norm = np.linalg.norm(p_hat, axis=-1, keepdims=True)
    return p_hat / np.where(norm < 1e-12, 1.0, norm)


def coordinate_t(M, W1):
    raw = M @ W1
    if raw.max() - raw.min() < 1e-12:
        return np.zeros_like(raw)
    return (raw - raw.min()) / (raw.max() - raw.min())


def render_mollweide(p, p_hat_curve, t_curve, residuals, slugs, out_path, title):
    lon_p = np.arctan2(p[:, 1], p[:, 0])
    lat_p = np.arcsin(np.clip(p[:, 2], -1.0, 1.0))
    lon_c = np.arctan2(p_hat_curve[:, 1], p_hat_curve[:, 0])
    lat_c = np.arcsin(np.clip(p_hat_curve[:, 2], -1.0, 1.0))

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
    if vmax - vmin < 1e-9:
        vmax = vmin + 1e-9
    norm = Normalize(vmin=vmin, vmax=vmax)
    sc = ax.scatter(lon_p, lat_p, c=residuals, cmap="coolwarm", norm=norm,
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
    cbar.set_label(r"chordal residual $r = \|p - \gamma(t)\|_2$", fontsize=10, color="#222222")
    ax.set_title(title, fontsize=11, color="#1a3a5c", pad=22)
    ax.legend(loc="lower left", fontsize=9, framealpha=0.92)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  saved {out_path} ({out_path.stat().st_size} bytes)")


def main():
    print("=== CYCLE-3 REPO-REFS RENDER → curve-map-output/ ===")
    print(f"Date: {datetime.now(timezone.utc).isoformat()}")
    if not CYCLE3_ARCHIVE_JSON.exists():
        print(f"FATAL: {CYCLE3_ARCHIVE_JSON} not found", file=sys.stderr)
        sys.exit(1)

    with open(CYCLE3_ARCHIVE_JSON) as f:
        archive = json.load(f)
    items = archive["corpus"]
    sparse_cells = archive.get("sparse_cell_count")
    mode_d_total = archive.get("mode_d_total")
    if sparse_cells is None or mode_d_total is None:
        try:
            with open(CYCLE3_FIT_JSON) as f:
                fit = json.load(f)
            sparse_cells = sparse_cells or fit.get("sparse_cell_count")
            mode_d_total = mode_d_total or fit.get("mode_d_total")
        except Exception:
            pass
    print(f"[1/4] Loaded {len(items)} items, basis_dim={archive.get('basis_dim')}, "
          f"sparse_cells={sparse_cells}, mode_d={mode_d_total})")

    slugs = [it["name"] for it in items]
    coverage_rows = np.array([[it["coverage"][p] for p in PRIMITIVES_7] for it in items],
                             dtype=np.float64)
    missing_map = {slug: [p for p in PRIMITIVES_7 if not it["coverage"][p]]
                   for slug, it in zip(slugs, items)}
    print(f"  coverage shape {coverage_rows.shape}, primitives={PRIMITIVES_7}")

    W2, mu, explained = pca_topk(coverage_rows, k=2)
    pc1, pc2 = float(explained[0]), float(explained[1])
    print(f"[2/4] PCA: PC1={pc1:.4f} PC2={pc2:.4f} sum={pc1+pc2:.4f} "
          f"(gate ≥ 0.40: {'PASS' if pc1+pc2 >= 0.40 else 'FAIL'})")

    Mc = coverage_rows - mu
    uv = Mc @ W2
    p = stereographic_from_south_pole(uv)
    t = coordinate_t(coverage_rows, W2[:, 0])

    C_curve, _ = fit_curve(p, t, L=3, ridge=1e-3)
    t_curve = np.linspace(0, 1, 500)
    p_hat_curve = evaluate_curve(C_curve, t_curve, L=3)
    p_at_t = evaluate_curve(C_curve, t, L=3)
    residuals = np.linalg.norm(p - p_at_t, axis=-1)
    median_res = float(np.median(residuals))
    print(f"[3/4] γ(t) fit: min={residuals.min():.4f} median={median_res:.4f} max={residuals.max():.4f}")

    title = (f"Curve map — repo-refs-skill cycle 3 (final fixpoint fit)\n"
             f"{len(items)} items, 7-D basis, PC1+PC2={pc1+pc2:.4f}, "
             f"identity-init Möbius (frozen $\\varphi_\\theta$)")
    png_path = OUT_DIR / "cycle-3-refs-curve-map-2026-08-07.png"
    render_mollweide(p, p_hat_curve, t_curve, residuals, slugs, png_path, title)

    print("[4/4] Writing JSON + priority list + README")
    json_path = OUT_DIR / "cycle-3-refs-curve-map-2026-08-07.json"
    payload = {
        "cycle": 3, "date": "2026-08-07", "skill": "repo-refs-skill",
        "basis": "7-D binary (repo-refs-skill cycle-3 fixpoint)",
        "primitives": PRIMITIVES_7,
        "corpus_size": len(items),
        "source_corpus": "yubi-OS/yubiOS refs/*.md (130 files)",
        "pc1_explained": pc1, "pc2_explained": pc2, "pc1_plus_pc2": pc1 + pc2,
        "sparse_cell_count_archive": sparse_cells,
        "mode_d_total_archive": mode_d_total,
        "ridge_lambda": 1e-3, "basis_L": 3, "basis_size": 16,
        "identity_mobius_frozen": True,
        "fit_method": "closed-form ridge on real spherical-harmonic basis (L=3, 16 functions)",
        "distance_metric": "chordal S^2 (bounded [0, 2])",
        "source_archive_json": "papers/data/repo-refs-skill-cycle-3-archive-2026-08-07.json",
        "note": "Sibling render of fit-full-curve-map.py for the 130-file refs/ corpus, "
                "using repo-refs-skill's own 7-D primitive basis (not the 79-skill internal-big-picture basis).",
        "points": [
            {"file": slug, "sha": items[i]["sha"], "size": items[i]["size"],
             "lon": float(np.degrees(np.arctan2(p[i, 1], p[i, 0]))),
             "lat": float(np.degrees(np.arcsin(np.clip(p[i, 2], -1.0, 1.0)))),
             "t": float(t[i]), "residual": float(residuals[i]),
             "missing_primitives": missing_map[slug]}
            for i, slug in enumerate(slugs)
        ],
    }
    with open(json_path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"  saved {json_path} ({json_path.stat().st_size} bytes)")

    order = np.argsort(residuals)[::-1]
    priority_md = OUT_DIR / "RSI-priority-list-cycle-3-refs-2026-08-07.md"
    with open(priority_md, "w") as f:
        f.write("# repo-refs-skill — cycle-3 RSI priority list (final fixpoint fit)\n\n")
        f.write(f"Generated by `render-cycle-3-refs-curve-map-output.py` on "
                f"{datetime.now(timezone.utc).isoformat()}.\n\n")
        f.write(f"Source: `papers/data/repo-refs-skill-cycle-3-archive-2026-08-07.json` "
                f"({len(items)} items, 7-D basis).\n\n")
        f.write(f"**Fit gate**: PC1+PC2 = {pc1+pc2:.4f} (PASS ≥ 0.40).\n")
        if sparse_cells is not None:
            f.write(f"**Sparse cells**: {sparse_cells}/130 ({100*sparse_cells/130:.1f}%).\n")
        if mode_d_total is not None:
            f.write(f"**Mode D candidates**: {mode_d_total}.\n\n")
        f.write("## Top-10 highest-residual items\n\n")
        f.write("| Rank | File | SHA | t | Residual | Missing primitives |\n")
        f.write("|---:|---|---|---|---:|---:|---|\n")
        for rank, idx in enumerate(order[:10], start=1):
            missing = ", ".join(missing_map[slugs[idx]]) or "(none)"
            f.write(f"| {rank} | `{slugs[idx]}` | `{items[idx]['sha']}` | "
                    f"{t[idx]:.4f} | {residuals[idx]:.4f} | {missing} |\n")
    print(f"  saved {priority_md} ({priority_md.stat().st_size} bytes)")

    readme_path = OUT_DIR / "README-cycle-3-refs-2026-08-07.md"
    with open(readme_path, "w") as f:
        f.write("# Cycle-3 repo-refs render, in curve-map-output/ (2026-08-07)\n\n")
        f.write(f"Generated by `papers/scripts/render-cycle-3-refs-curve-map-output.py` on "
                f"{datetime.now(timezone.utc).isoformat()}.\n\n")
        f.write("## Why this file exists here\n\n")
        f.write("`curve-map-output/` is normally owned by `fit-full-curve-map.py`, which fits the "
                "**79-skill corpus** on the `internal-big-picture` 7-D primitive basis (attestation, "
                "trust_chain, least_privilege, ...). This directory adds a sibling render for the "
                "**130-file `refs/` corpus** evaluated against `repo-refs-skill`'s own 7-D primitive basis "
                "(document-quality: problem_statement, recommendation, evidence, cross_reference, "
                "verification_plan, source_citation, priority_signal). Two different corpora, two "
                "different 7-D bases — both fits live side by side without collision:\n\n")
        f.write("| File | Owner | Corpus | Basis |\n")
        f.write("|---|---|---|---|\n")
        f.write("| `curve-map.png` / `curve-map.json` / `RSI-priority-list.md` / `corpus-listing.json` / `README.md` | "
                "`fit-full-curve-map.py` | 79 skills | internal-big-picture (7-D) |\n")
        f.write("| `cycle-3-refs-curve-map-2026-08-07.{png,json}`, "
                "`RSI-priority-list-cycle-3-refs-2026-08-07.md`, this file | "
                "`render-cycle-3-refs-curve-map-output.py` | 130 refs/*.md | repo-refs-skill (7-D) |\n\n")
        f.write("## Cycle-3 (fixpoint) fit results\n\n")
        f.write(f"- Corpus size: **{len(items)}** items (130 refs/*.md)\n")
        f.write(f"- PC1 explained variance: {pc1:.4f}\n")
        f.write(f"- PC2 explained variance: {pc2:.4f}\n")
        f.write(f"- **PC1+PC2 = {pc1+pc2:.4f}** (gate ≥ 0.40, "
                f"{'PASS' if pc1+pc2 >= 0.40 else 'FAIL'})\n")
        f.write(f"- Median chordal residual: {median_res:.4f}\n")
        f.write(f"- Max chordal residual: {residuals.max():.4f}\n")
        if sparse_cells is not None:
            f.write(f"- Sparse cells: {sparse_cells}/130 ({100*sparse_cells/130:.1f}%)\n")
        f.write(f"- Mode D candidates (from archive): {archive.get('mode_d_total')}\n\n")
        f.write("## How to regenerate\n\n```bash\n"
                "python3.12 papers/scripts/render-cycle-3-refs-curve-map-output.py\n```\n\n")
        f.write("Requires the cached archive at "
                "`papers/data/repo-refs-skill-cycle-3-archive-2026-08-07.json` "
                "(produced upstream in the cycle-3 RSI fixpoint run). No live API calls — pure re-render.\n")
    print(f"  saved {readme_path} ({readme_path.stat().st_size} bytes)")
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
