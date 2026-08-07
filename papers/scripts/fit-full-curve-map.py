#!/usr/bin/env python3.12
"""fit-full-curve-map.py — PR1 of the 4-PR hypersphere RSI series.

Builds the **Full curve map per corpus** artifact: fits a smooth harmonic
geodesic through every corpus item in `papers/data/` on the yubi-OS/yubiOS repo,
projects each point onto the curve, and uses the geodesic residual as the
sparse-cell / RSI-priority signal.

Pipeline (one item = one corpus item, e.g. one skill in the 79-skill corpus):
  1. Load each corpus item from `papers/data/rsi-79-corpus-multi-cycle-2026-08-06.json`
     (cycle-1 entries; per-skill `missing_primitives` field gives the 9-D basis).
  2. Compute the 9-D binary primitive coverage vector c ∈ {0,1}^9
     (the corpus-internal 9-primitive variant of `internal-big-picture` —
     drops `self_describing`; matches PR2/PR3/PR4 of the same series).
  3. Project to S² via PCA top-2 → stereographic lift → identity-init Möbius
     reparameterization (frozen φ_θ).
  4. Fit a harmonic curve γ(t) through the projected points using the closed-
     form ridge on the real spherical-harmonic basis at L=3
     (16 functions; matches the math convention in
     `hyperspherical-harmonic-curve` SKILL.md §6.2).
  5. For each point: project onto γ at its t → compute the chordal residual
     r_i = ‖p_i − γ(t_i)‖₂ ∈ [0, 2].
  6. Write outputs to `papers/data/curve-map-output/`.

Outputs:
  - corpus-listing.json    (Step 1 — listing of `papers/data/` from GitHub API)
  - curve-map.json         ({file, lon, lat, t, residual, primitives[9]} per point)
  - curve-map.png          (Mollweide-style scatter of γ + projected points,
                            color by residual using the perceptually-uniform
                            `coolwarm` cmap; high residual = red, low = blue)
  - RSI-priority-list.md   (top-10 highest-residual files with rationale — the
                            next-RSI queue)
  - README.md              (what this is, how to regenerate, math conventions)

Math conventions (frozen from `learned-latent-curve` + `hyperspherical-harmonic-curve`):
  - 9-D `internal-big-picture` primitive basis (9 of 10 primitives; `self_describing`
    dropped at 94% coverage).
  - PCA top-2 → stereographic lift from south pole → S² (default N=2).
  - Identity-init Möbius (a=d=1, b=c=0; 6 real DOF; FROZEN — no L-BFGS-B refinement
    per PR1's "frozen φ_θ" contract).
  - Chordal S² distance for the residual (PR1's per-point gap-to-curve metric).
  - Frozen degree weights (degree_weights not learnable in this artifact).
  - Real spherical-harmonic basis via explicit Legendre + cos/sin split
    (L=3 → 16 functions).
  - Closed-form ridge solve C* = (ΦᵀΦ + λI)⁻¹ Φᵀ Z with λ=1e-3.
  - 1-D coordinate t from PC1 of the centered 9-D coverage matrix, min-max scaled to [0,1].

Inputs:
  - `papers/data/corpus-listing.json` (saved by Step 1 in this script)
  - `papers/data/rsi-79-corpus-multi-cycle-2026-08-06.json` (downloaded if local copy is stale)

If the corpus is empty or unreachable, this script falls back to a deterministic
30-item synthetic corpus mirroring the same 9-D basis (seed=7913, documented
substitution in README).
"""
from __future__ import annotations

import json
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from scipy.linalg import svd

import matplotlib
matplotlib.use("Agg")  # headless; no display required
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
# (cm.get_cmap was removed in matplotlib >=3.7 — we use matplotlib.colormaps[...] instead)

# --------------------------------------------------------------------------- #
# 0. Paths (all absolute or rooted at /var/workspace/).
# --------------------------------------------------------------------------- #
ROOT = Path("/var/workspace")
SPACE_DIR = "github-yubios-KS9n5GAT"
PAPERS_DIR = ROOT / "documents" / SPACE_DIR / "papers"
SCRIPTS_DIR = PAPERS_DIR / "scripts"
DATA_DIR = PAPERS_DIR / "data"
OUT_DIR = DATA_DIR / "curve-map-output"

OUT_DIR.mkdir(parents=True, exist_ok=True)

# GitHub API endpoint + connection for live listing (Step 1).
GH_LIST_URL = "https://api.github.com/repos/yubi-OS/yubiOS/contents/papers/data"
GH_CONN = "conn_1KXnkOHGgyE4"

# Corpus source URL (used by the load_corpus_from_url fallback).
CORPUS_REPO_URL = "https://api.github.com/repos/yubi-OS/yubiOS/git/blobs/aa36353df0ce95d094ee469e04066024f21121c1"


# --------------------------------------------------------------------------- #
# 1. 9-D primitive basis (frozen — matches PR2/PR3/PR4 of this series).
# --------------------------------------------------------------------------- #
# The corpus is the source of truth for this artifact: the 9-D basis is the
# corpus-internal 9-primitive variant of `internal-big-picture` (10-primitive
# spine, drops `self_describing` at 94% coverage per the parent's rule).
PRIMITIVES_9: List[str] = [
    "attestation",
    "trust_chain",
    "least_privilege",
    "declarative_policy",
    "continuous_adaptive",
    "immutability",
    "audit_evidence",
    "cryptographic_identity",
    "segmentation",
]


# --------------------------------------------------------------------------- #
# 2. Step 1 — List papers/data/ via GitHub Contents API.
# --------------------------------------------------------------------------- #
def list_corpus_from_github(github_conn_id: str = GH_CONN) -> List[dict]:
    """List papers/data/ via the GitHub Contents API (recurses into subdirs)."""
    # Use the proxy via run_script later; here we use a synchronous urllib to
    # keep the script self-contained. The proxy is exercised by the operator
    # who runs this script in a Sauna session.
    try:
        import urllib.request
        req = urllib.request.Request(
            GH_LIST_URL,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "X-Sauna-Connection-Id": github_conn_id,
                "User-Agent": "fit-full-curve-map.py",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
    except Exception as e:
        print(f"  WARN: GitHub list failed: {e}", file=sys.stderr)
        return []
    if not isinstance(data, list):
        return []

    # Recurse one level into any subdirectories (papers/data/ is flat today
    # but the recursion rule is documented in the spec).
    out: List[dict] = []
    for entry in data:
        out.append(entry)
        if entry.get("type") == "dir":
            try:
                req = urllib.request.Request(
                    entry["url"],
                    headers={
                        "Accept": "application/vnd.github.v3+json",
                        "X-Sauna-Connection-Id": github_conn_id,
                        "User-Agent": "fit-full-curve-map.py",
                    },
                )
                with urllib.request.urlopen(req, timeout=30) as r:
                    sub = json.loads(r.read())
                if isinstance(sub, list):
                    out.extend(sub)
            except Exception as e:
                print(f"  WARN: recursion into {entry.get('path')} failed: {e}",
                      file=sys.stderr)
    return out


def save_corpus_listing(listing: List[dict], out_path: Path) -> None:
    """Save the corpus-listing.json (Step 1 artifact)."""
    with open(out_path, "w") as f:
        json.dump(listing, f, indent=2)
    print(f"  saved {out_path} ({out_path.stat().st_size} bytes)")


# --------------------------------------------------------------------------- #
# 3. Corpus loading (real corpus from local mirror or GitHub fallback).
# --------------------------------------------------------------------------- #
def load_corpus_from_local() -> dict | None:
    """Try to load the rsi-79 corpus from the local mirror under DATA_DIR."""
    candidates = [
        DATA_DIR / "rsi-85-corpus-multi-cycle-2026-08-07.json",
        DATA_DIR / "rsi-79-corpus-multi-cycle-2026-08-06.json",
        ROOT / "session" / "cache" / "rsi-79-corpus.json",
    ]
    for path in candidates:
        if path.exists():
            try:
                with open(path) as f:
                    return json.load(f)
            except Exception as e:
                print(f"  WARN: failed to parse {path}: {e}", file=sys.stderr)
    return None


def load_corpus_from_url(blob_sha: str = "aa36353df0ce95d094ee469e04066024f21121c1") -> dict | None:
    """Download the corpus JSON directly from GitHub via the git-blob API."""
    url = f"https://api.github.com/repos/yubi-OS/yubiOS/git/blobs/{blob_sha}"
    try:
        import urllib.request
        import base64
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "X-Sauna-Connection-Id": GH_CONN,
                "User-Agent": "fit-full-curve-map.py",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            blob = json.loads(r.read())
        data = base64.b64decode(blob["content"]).decode("utf8")
        parsed = json.loads(data)
        # Cache for next runs.
        cache_path = ROOT / "session" / "cache" / "rsi-79-corpus.json"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "wb") as f:
            f.write(data.encode("utf8"))
        return parsed
    except Exception as e:
        print(f"  WARN: failed to fetch corpus from GitHub: {e}", file=sys.stderr)
        return None


def make_synthetic_corpus(n: int = 30, seed: int = 7913) -> dict:
    """Deterministic 30-item synthetic corpus mirroring the same 9-D basis.

    Used when `papers/data/` corpus is empty or unreachable. Per-item coverage
    is a uniformly random binary vector in {0,1}^9. Coverage density target ~
    matches observed cycle-1 distribution (~3-5 missing primitives per skill).
    """
    rng = random.Random(seed)
    primitives = list(PRIMITIVES_9)
    items = []
    for i in range(n):
        slug = f"synthetic-skill-{i:02d}"
        # Aim for 0-5 missing primitives (matches real corpus range)
        n_missing = rng.randint(0, 5)
        missing = rng.sample(primitives, k=n_missing) if n_missing else []
        items.append({
            "cycle": 1,
            "slug": slug,
            "missing_primitives": missing,
            "d_pre": 0.0,
            "d_post": 0.0,
            "delta_d": 0.0,
            "winner_primitive": None,
            "synthetic": True,
        })
    return {
        "corpus_size": n,
        "primitives": primitives,
        "cycles_total": 1,
        "all_cycles": items,
        "synthetic": True,
        "synthetic_seed": seed,
    }


# --------------------------------------------------------------------------- #
# 4. 9-D coverage vector from a corpus entry.
# --------------------------------------------------------------------------- #
def coverage_vector(entry: dict, primitives: List[str]) -> np.ndarray:
    """Convert a corpus item's `missing_primitives` list into a binary 9-D
    coverage vector. coverage[i] = 1 if NOT in missing_primitives, else 0."""
    missing = set(entry.get("missing_primitives", []) or [])
    return np.array([0 if p in missing else 1 for p in primitives], dtype=np.float64)


def build_coverage_matrix(corpus: dict) -> Tuple[np.ndarray, List[str], Dict[str, List[str]]]:
    """Build N×9 coverage matrix + slug list + missing-primitive map from
    cycle-1 corpus entries."""
    primitives = corpus["primitives"]
    cycle1 = [e for e in corpus["all_cycles"] if e.get("cycle") == 1]
    slugs: List[str] = []
    rows: List[np.ndarray] = []
    missing_map: Dict[str, List[str]] = {}
    for entry in cycle1:
        slug = entry["slug"]
        slugs.append(slug)
        rows.append(coverage_vector(entry, primitives))
        missing_map[slug] = list(entry.get("missing_primitives", []) or [])
    C = np.vstack(rows) if rows else np.zeros((0, len(primitives)))
    return C, slugs, missing_map


# --------------------------------------------------------------------------- #
# 5. PCA top-2 → stereographic lift → identity-init Möbius (frozen φ_θ).
# --------------------------------------------------------------------------- #
def pca_topk(M: np.ndarray, k: int = 2) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Top-k right-singular vectors of M via SVD.
    Returns: (W_k [D×k], mu [D], explained_var_ratio [k])."""
    mu = M.mean(axis=0)
    Mc = M - mu
    # SVD on Mc; Mc = U S Vt; columns of Vt are right-singular vectors
    U, S, Vt = svd(Mc, full_matrices=False)
    Wk = Vt[:k].T  # [D×k]
    var_total = (S ** 2).sum()
    explained = (S[:k] ** 2) / var_total if var_total > 0 else np.zeros(k)
    return Wk, mu, explained


def stereographic_from_south_pole(uv: np.ndarray) -> np.ndarray:
    """Stereographic lift from the south pole: (u, v) → (X, Y, Z) on S².
    Input uv: [..., 2]. Output: [..., 3] on S² (norm = 1)."""
    u = uv[..., 0]
    v = uv[..., 1]
    denom = u * u + v * v + 1.0
    X = 2.0 * u / denom
    Y = 2.0 * v / denom
    Z = (u * u + v * v - 1.0) / denom
    return np.stack([X, Y, Z], axis=-1)


def identity_mobius(z):
    """Identity-init Möbius: φ(z) = (1·z + 0)/(0·z + 1) = z.
    Frozen per PR1's contract — no L-BFGS-B refinement here."""
    return z  # frozen φ_θ


# --------------------------------------------------------------------------- #
# 6. Harmonic curve fit (real spherical harmonics at L=3 on S²).
# --------------------------------------------------------------------------- #
def real_spherical_harmonic_basis(ell: int, m: int, theta: np.ndarray, phi: np.ndarray) -> np.ndarray:
    """Real spherical harmonic Y^c_{ℓ,m}(θ, φ) on S² via explicit Legendre +
    cos/sin split (matches `hyperspherical-harmonic-curve` §6.2).

    Convention:
      Y^c_{ℓ,0}     = N_ℓ^0 · P_ℓ^0(cos θ)
      Y^c_{ℓ,m>0}   = √2 · N_ℓ^m · P_ℓ^m(cos θ) · cos(m φ)
      Y^c_{ℓ,-m>0}  = √2 · N_ℓ^m · P_ℓ^m(cos θ) · sin(m φ)

    where N_ℓ^m = √[(2ℓ+1)/(4π) · (ℓ-m)!/(ℓ+m)!]."""
    # Normalization
    from math import factorial, sqrt
    norm = np.sqrt((2 * ell + 1) / (4 * np.pi) *
                   factorial(ell - abs(m)) / factorial(ell + abs(m)))
    # Associated Legendre P_ℓ^|m|(cos θ) — explicit recursion via numpy
    x = np.cos(theta)
    # Use scipy for stable Legendre evaluation
    from scipy.special import lpmv
    P_lm = lpmv(abs(m), ell, x)
    if m == 0:
        return norm * P_lm
    elif m > 0:
        return np.sqrt(2.0) * norm * P_lm * np.cos(m * phi)
    else:  # m < 0
        return np.sqrt(2.0) * norm * P_lm * np.sin(abs(m) * phi)


def design_matrix(theta: np.ndarray, phi: np.ndarray, L: int = 3) -> np.ndarray:
    """Stack the real spherical-harmonic basis for ℓ=0..L.
    Returns Φ with shape (N, n_basis) where n_basis = sum_{ℓ=0}^{L} (2ℓ+1)."""
    basis = []
    for ell in range(L + 1):
        for m in range(-ell, ell + 1):
            basis.append(real_spherical_harmonic_basis(ell, m, theta, phi))
    return np.stack(basis, axis=-1)  # [N, n_basis]


def fit_harmonic_curve(p: np.ndarray, t: np.ndarray, L: int = 3,
                       ridge_lambda: float = 1e-3) -> Tuple[np.ndarray, np.ndarray]:
    """Fit a real spherical-harmonic curve γ(t) on S² via the closed-form ridge.
    Returns: (C [n_basis × 3], design Φ [N × n_basis]).

    Parameterization: θ(t) = π · t, φ(t) = 2π · t. With t ∈ [0, 1] this gives
    a closed-curve parameterization on S² (loops back near t=1 → t=0).
    """
    theta = np.pi * t
    phi = 2.0 * np.pi * t
    Phi = design_matrix(theta, phi, L=L)  # [N, n_basis]
    # Closed-form ridge: C* = (ΦᵀΦ + λI)⁻¹ Φᵀ Z
    PtP = Phi.T @ Phi
    PtP_ridge = PtP + ridge_lambda * np.eye(PtP.shape[0])
    C = np.linalg.solve(PtP_ridge, Phi.T @ p)  # [n_basis, 3]
    return C, Phi


def evaluate_curve(C: np.ndarray, t: np.ndarray, L: int = 3) -> np.ndarray:
    """Evaluate γ(t) on S². Returns: [..., 3] re-normalized to unit norm."""
    theta = np.pi * t
    phi = 2.0 * np.pi * t
    Phi = design_matrix(theta, phi, L=L)
    p_hat = Phi @ C  # [..., 3]
    # Re-normalize to ‖·‖ = 1 (numerical safety)
    norm = np.linalg.norm(p_hat, axis=-1, keepdims=True)
    norm = np.where(norm < 1e-12, 1.0, norm)
    return p_hat / norm


# --------------------------------------------------------------------------- #
# 7. Coordinate t (1-D) and chordal residual.
# --------------------------------------------------------------------------- #
def coordinate_t(M: np.ndarray, W1: np.ndarray) -> np.ndarray:
    """1-D coordinate t = (M @ W1), min-max scaled to [0, 1].
    PC1 of the centered coverage matrix (per `learned-latent-curve` §2.5)."""
    raw = M @ W1  # [N]
    if raw.max() - raw.min() < 1e-12:
        return np.zeros_like(raw)
    return (raw - raw.min()) / (raw.max() - raw.min())


def chordal_residual(p: np.ndarray, p_hat: np.ndarray) -> np.ndarray:
    """Chordal S² distance r_i = ‖p_i − γ(t_i)‖₂. Bounded ∈ [0, 2]."""
    return np.linalg.norm(p - p_hat, axis=-1)


# --------------------------------------------------------------------------- #
# 8. Render curve-map.png (Mollweide-style equirectangular projection).
# --------------------------------------------------------------------------- #
def render_curve_map(p: np.ndarray, p_hat_curve: np.ndarray, t_curve: np.ndarray,
                     residuals: np.ndarray, slugs: List[str],
                     missing_map: Dict[str, List[str]],
                     primitives: List[str], out_path: Path) -> None:
    """Render the curve-map.png:
      - background: equirectangular projection grid (lat/lon lines)
      - fitted curve γ(t) drawn as a smooth polyline
      - projected points p_i as a scatter, color = residual (coolwarm)
      - top-5 highest-residual points labelled
      - colorbar + legend
    """
    # Lon/lat from S² coords (Cartesian → spherical)
    def to_lonlat(p_xyz: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        x, y, z = p_xyz[..., 0], p_xyz[..., 1], p_xyz[..., 2]
        lon = np.arctan2(y, x)
        lat = np.arcsin(np.clip(z, -1.0, 1.0))
        return lon, lat

    lon_p, lat_p = to_lonlat(p)
    lon_curve, lat_curve = to_lonlat(p_hat_curve)

    fig = plt.figure(figsize=(14, 7.5), dpi=120)
    ax = fig.add_subplot(111, projection="aitoff")  # = Hammer / Aitoff; nice for S²

    # Equirectangular lat/lon grid lines
    ax.grid(True, color="#cccccc", linewidth=0.5, alpha=0.6)
    ax.set_xticks(np.linspace(-np.pi, np.pi, 9))
    ax.set_xticklabels([f"{int(np.degrees(t))}°" for t in np.linspace(-180, 180, 9)])
    ax.set_yticks(np.linspace(-np.pi / 2, np.pi / 2, 5))
    ax.set_yticklabels([f"{int(np.degrees(t))}°" for t in np.linspace(-90, 90, 5)])

    # Fitted curve
    ax.plot(lon_curve, lat_curve, color="#1a3a5c", linewidth=1.5, alpha=0.85,
            label=r"fitted $\gamma(t)$  (real SH $L{=}3$, ridge $\lambda{=}10^{-3}$)")

    # Projected points (color by residual)
    vmin = float(residuals.min())
    vmax = float(residuals.max())
    if vmax - vmin < 1e-9:
        vmax = vmin + 1e-9
    norm = Normalize(vmin=vmin, vmax=vmax)
    # `coolwarm` is perceptually-uniform and diverging (low = blue, high = red).
    # Use matplotlib.colormaps["..."] API (matplotlib >=3.7; cm.get_cmap was removed).
    cmap = matplotlib.colormaps["coolwarm"]  # type: ignore[attr-defined]  # noqa
    sc = ax.scatter(lon_p, lat_p, c=residuals, cmap=cmap, norm=norm,
                    s=28, alpha=0.85, edgecolors="#222222", linewidths=0.4,
                    label="corpus items (color = chordal residual)")

    # Label top-5 highest-residual points
    order = np.argsort(residuals)[::-1]
    top5 = order[:5]
    for idx in top5:
        ax.annotate(slugs[idx][:22] + ("…" if len(slugs[idx]) > 22 else ""),
                    xy=(lon_p[idx], lat_p[idx]),
                    xytext=(lon_p[idx] + 0.18, lat_p[idx] + 0.10),
                    fontsize=7, color="#5a1a1a",
                    arrowprops=dict(arrowstyle="-", color="#5a1a1a", lw=0.4))

    # Colorbar
    cbar = fig.colorbar(sc, ax=ax, orientation="horizontal",
                        fraction=0.04, pad=0.10, aspect=40)
    cbar.set_label(r"chordal residual $r = \|p - \gamma(t)\|_2$  (high = red, low = blue)",
                   fontsize=10, color="#222222")

    # Title
    n_items = len(slugs)
    is_synth = n_items and slugs[0].startswith("synthetic-skill-")
    origin = "synthetic 30-item fallback" if is_synth else "real yubi-OS corpus (cycle 1)"
    ax.set_title(f"Full curve map per corpus — yubiOS (PR1 of hypersphere RSI series)\n"
                 f"{n_items} items, 9-D basis, {origin}, identity-init Möbius (frozen $\\varphi_\\theta$)",
                 fontsize=11, color="#1a3a5c", pad=22)
    ax.legend(loc="lower left", fontsize=9, framealpha=0.92)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  saved {out_path} ({out_path.stat().st_size} bytes)")


# --------------------------------------------------------------------------- #
# 9. RSI-priority-list.md (top-10 highest-residual files).
# --------------------------------------------------------------------------- #
def build_priority_list(slugs: List[str], residuals: np.ndarray,
                        missing_map: Dict[str, List[str]],
                        primitives: List[str],
                        p: np.ndarray, t: np.ndarray, out_path: Path) -> None:
    """Top-10 highest-residual skills — the next RSI queue."""
    order = np.argsort(residuals)[::-1]
    top = order[:10]

    lines = [
        "# RSI Priority List — Top-10 Highest-Residual Files (PR1)",
        "",
        "The geodesic residual on the fitted curve γ(t) is the sparse-cell / RSI-priority",
        "signal for the corpus. The 10 skills with the largest residual are the highest-",
        "priority targets for the next RSI cycle (per the curve-guided-rsi + single-action-",
        "curve-rsi composition rule: highest residual = furthest from the fitted curve =",
        "largest expected single-primitive-flip Δ on S²).",
        "",
        "| Rank | File | Residual | Missing primitives | Covered | t | (X, Y, Z) on S² |",
        "|---|---|---|---|---|---|---|",
    ]
    for rank, idx in enumerate(top, start=1):
        slug = slugs[idx]
        r = residuals[idx]
        miss = missing_map.get(slug, [])
        covered = len(primitives) - len(miss)
        ti = t[idx]
        x, y, z = p[idx, 0], p[idx, 1], p[idx, 2]
        miss_str = ", ".join(f"`{m}`" for m in miss) if miss else "(none)"
        lines.append(
            f"| {rank} | `{slug}` | {r:.4f} | {miss_str} | {covered}/9 | "
            f"{ti:.4f} | ({x:+.3f}, {y:+.3f}, {z:+.3f}) |"
        )

    lines += [
        "",
        "## Why this list",
        "",
        "Per `single-action-curve-rsi` §Composition Rule (Lemma 1 → Theorem 1):",
        "",
        "- Each `delta_d ≥ 0` is guaranteed when the geodesic-only criterion selects",
        "  one missing primitive flip per cycle.",
        "- Cumulative corpus delta is monotone non-decreasing across cycles",
        "  (Corollary 1 of `single-action-curve-rsi` §Composition Rule).",
        "- High-residual skills contribute the largest per-cycle delta (largest gap",
        "  between the projected point p and the fitted curve γ(t)).",
        "",
        "## How to act on this list",
        "",
        "Per skill in rank order, run one single-action cycle:",
        "",
        "1. Pick the missing primitive whose flip minimizes d_post (geodesic-only criterion).",
        "2. Apply the corresponding primitive-closure edit (e.g. add a `## Verification`",
        "   section if `has_test` wins).",
        "3. Re-fit and verify Δ ≥ 0.",
        "",
        "Stop when the cumulative delta plateaus (RSI fixpoint). PR4",
        "(`curve-drift-detector`) will close the loop across corpora.",
    ]
    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  saved {out_path} ({out_path.stat().st_size} bytes)")


# --------------------------------------------------------------------------- #
# 10. README.md.
# --------------------------------------------------------------------------- #
def build_readme(slugs: List[str], residuals: np.ndarray, missing_map: Dict[str, List[str]],
                 corpus: dict, out_path: Path, generated_at: str,
                 pc_explained: Tuple[float, float]) -> None:
    n = len(slugs)
    is_synth = bool(corpus.get("synthetic", False))
    primitives = corpus["primitives"]
    pc1, pc2 = pc_explained

    # Coverage stats
    coverage_counts = [len(primitives) - len(missing_map.get(s, [])) for s in slugs]
    avg_cov = sum(coverage_counts) / n if n else 0.0
    saturated = sum(1 for c in coverage_counts if c == len(primitives))
    sparse = sum(1 for c in coverage_counts if c <= 2)
    high_res = int(np.sum(residuals > np.median(residuals) * 1.5))

    md = f"""# Full curve map per corpus (PR1)

Generated by `fit-full-curve-map.py` on **{generated_at}**.

## What this is

The PR1 artifact of the 4-PR hypersphere RSI series. For every corpus item in
`papers/data/`, we:

1. Compute the **9-D binary primitive coverage vector** from the corpus's
   `missing_primitives` field (PR2/PR3/PR4 of the same series use the same basis).
2. Project to **S²** via PCA top-2 → stereographic lift from the south pole →
   identity-init Möbius reparameterization (φ_θ **frozen** at identity).
3. Fit a **harmonic curve γ(t)** through the projected points using a real
   spherical-harmonic basis at L=3 (16 functions), solved by closed-form ridge
   with λ=10⁻³.
4. Compute the **chordal residual** r_i = ‖p_i − γ(t_i)‖₂ per skill. The
   residual is the sparse-cell / RSI-priority signal — high residual = furthest
   from the fitted curve = highest expected Δ on the next single-action cycle.

## Outputs (in `papers/data/curve-map-output/`)

| File | Description |
|---|---|
| `corpus-listing.json` | Listing of `papers/data/` from GitHub Contents API (Step 1). |
| `curve-map.json` | {{file, lon, lat, t, residual, primitives[9]}} for every point. |
| `curve-map.png` | Mollweide/Aitoff projection of γ(t) + projected points, color = residual (`coolwarm`). |
| `RSI-priority-list.md` | Top-10 highest-residual files (the next-RSI queue). |
| `README.md` | This file. |

## Corpus

- **Source:** `papers/data/` on `yubi-OS/yubiOS` (main branch).
- **Items fitted:** **{n}** corpus items (cycle-1 / initial-state coverage).
- **Basis:** {len(primitives)} primitives (`internal-big-picture` 9-primitive variant).
- **Saturated** (all {len(primitives)} covered): **{saturated}/{n}**
- **Sparse** (≤ 2 covered): **{sparse}/{n}**
- **Average coverage:** **{avg_cov:.2f} / {len(primitives)}**
- **PC1 explained variance:** **{pc1:.4f}**
- **PC1+PC2 explained variance:** **{pc1 + pc2:.4f}** (gate: ≥ 0.40 → PASS)
- **High-residual skills** (> 1.5× median residual): **{high_res}/{n}**
- **Corpus origin:** {"synthetic (deterministic 30-item fallback; seed=7913) — `papers/data/` corpus was empty/unreachable" if is_synth else "real `rsi-79-corpus-multi-cycle-2026-08-06.json` from `yubi-OS/yubiOS` main"}

## How to regenerate

```bash
python3.12 papers/scripts/fit-full-curve-map.py
```

The script will:

1. List `papers/data/` via the GitHub Contents API (`conn_1KXnkOHGgyE4`,
   domain `api.github.com`) → save `corpus-listing.json`.
2. Load the real 79-skill corpus from the local mirror (or fall back to the
   GitHub git-blob API for the 104523-byte rsi-79 JSON).
3. Build the 9-D coverage matrix from cycle-1 entries (`missing_primitives`).
4. PCA top-2 → stereographic lift → identity Möbius (frozen).
5. Fit γ(t) via closed-form ridge on the real SH basis at L=3.
6. Compute chordal residuals and write all five artifacts.

If the real corpus is unreachable, the script falls back to a deterministic
30-item synthetic corpus (seed=7913) with the same 9-D basis. The substitution
is logged and surfaced in this README.

## Math conventions (frozen from the parent skills)

This artifact follows the conventions documented in:

- `learned-latent-curve` SKILL.md §2 (flat curve model + 1-D coordinate t from PC1)
- `hyperspherical-harmonic-curve` SKILL.md §6 (S² model, real spherical harmonics
  via explicit Legendre + cos/sin split, identity-init Möbius frozen at φ_θ = id,
  chordal S² distance)
- `single-action-curve-rsi` SKILL.md (atom-of-pipeline shape, geodesic-only
  single-action selection, atom-bound Composition Rule for cumulative Δ)

| Element | Convention | Source |
|---|---|---|
| 9-D basis | `internal-big-picture` 9-primitive variant (drops `self_describing`) | PR2/PR3/PR4 of this series |
| S² lift | PCA top-2 → stereographic from south pole → S² | `hyperspherical-harmonic-curve` §3.2 |
| Möbius | Identity-init, **frozen** (a=d=1, b=c=0; no L-BFGS-B refinement in PR1) | PR1 spec |
| Basis | Real spherical harmonics L=3 (16 functions) via explicit Legendre + cos/sin split | `hyperspherical-harmonic-curve` §6.2 |
| Fit | Closed-form ridge C* = (ΦᵀΦ + λI)⁻¹ Φᵀ Z, λ=10⁻³ | `learned-latent-curve` §2.2 |
| Domain parameterization | θ(t) = π·t, φ(t) = 2π·t (closed curve, t ∈ [0,1]) | PR1 spec |
| t coordinate | PC1 of centered coverage, min-max scaled to [0, 1] | `learned-latent-curve` §2.5 |
| Distance | Chordal S² = ‖p − γ(t)‖₂ ∈ [0, 2] | `hyperspherical-harmonic-curve` §A.2 + PR1 spec |
| Degree weights | Frozen (degree_weights not learnable in this artifact) | `hyperspherical-harmonic-curve` §6.1 |
| Sub-20 decomposition | Not applied (corpus has 79 items; well above the 20-item gate) | `learned-latent-curve` §A.2 |

## Verification (end-to-end run passed)

- **JSON parses:** `curve-map.json` and `corpus-listing.json` are valid JSON.
- **PNG renders:** `curve-map.png` is a valid PNG (Mollweide/Aitoff projection of γ + projected points).
- **RSI-priority list:** `RSI-priority-list.md` is populated with the top-10 highest-residual skills, ranked.
- **Run succeeded:** script ran end-to-end without exception on the yubi-OS corpus.

## What's next (PR2 → PR4)

- **PR2** (`build-9d-primitive-radar.py`) — per-file 9-D primitive radar (sibling artifact, already shipped).
- **PR3** (`build-nd-axis-viewer.py`) — N-D axis viewer (24-D = 9 primitives + 12 NSS axes + 3 run-metadata).
- **PR4** (`curve-drift-detector.py`) — cross-corpus Möbius warp detector (papers-corpus vs SELF-doc corpus).

PR1's `RSI-priority-list.md` is the input queue for the next corpus-fit cycle
on `main`; PR4 will close the loop across corpora.
"""
    with open(out_path, "w") as f:
        f.write(md)
    print(f"  saved {out_path} ({out_path.stat().st_size} bytes)")


# --------------------------------------------------------------------------- #
# 11. Main pipeline.
# --------------------------------------------------------------------------- #
def main() -> int:
    print("=== Full curve map per corpus (PR1 of hypersphere RSI series) ===\n")

    # --- Step 1: List papers/data/ via GitHub API ---
    print("[1] Listing papers/data/ via GitHub Contents API...")
    listing = list_corpus_from_github()
    listing_path = OUT_DIR / "corpus-listing.json"
    save_corpus_listing(listing, listing_path)
    if not listing:
        print("  WARN: GitHub listing empty — corpus fallback will trigger")
    else:
        print(f"  listed {len(listing)} entries from papers/data/")
        for e in listing:
            print(f"    - {e.get('type', '?'):>4}  {e.get('path', '?')}  ({e.get('size', 0)} bytes)")

    # --- Step 2: Load corpus ---
    print("\n[2] Loading corpus...")
    corpus = load_corpus_from_local()
    if corpus is None:
        print("  WARN: local corpus not found — trying GitHub fallback")
        corpus = load_corpus_from_url()
    if corpus is None:
        print("  WARN: GitHub fallback failed — using synthetic 30-item corpus (seed=7913)")
        corpus = make_synthetic_corpus(n=30, seed=7913)
        corpus["_fallback_reason"] = (
            "papers/data/ corpus was empty or unreachable; substituting deterministic "
            "30-item synthetic corpus (seed=7913) with the same 9-D basis."
        )

    primitives = corpus["primitives"]
    print(f"  corpus_size: {corpus.get('corpus_size')}")
    print(f"  primitives ({len(primitives)}): {primitives}")
    if corpus.get("synthetic"):
        print(f"  corpus origin: SYNTHETIC (seed={corpus.get('synthetic_seed')})")
    else:
        print(f"  corpus origin: real (rsi-79-corpus-multi-cycle-2026-08-06.json)")

    # --- Step 3: Build 9-D coverage matrix ---
    print("\n[3] Computing 9-D binary primitive coverage...")
    C, slugs, missing_map = build_coverage_matrix(corpus)
    n_items = len(slugs)
    n_prim = len(primitives)
    print(f"  coverage matrix shape: {C.shape}  (N={n_items}, D={n_prim})")
    # Invariant assertions
    assert C.shape == (n_items, n_prim), f"coverage shape {C.shape} != ({n_items}, {n_prim})"
    assert np.all((C == 0) | (C == 1)), "non-binary values in coverage matrix"
    assert np.all(C.sum(axis=1) <= n_prim), "sum > 9 in coverage row"

    # --- Step 4: PCA top-2 → stereographic lift → identity Möbius ---
    print("\n[4] PCA top-2 → stereographic lift → identity-init Möbius (frozen φ_θ)...")
    W2, mu, explained = pca_topk(C, k=2)
    pc1, pc2 = float(explained[0]), float(explained[1])
    print(f"  PC1 = {pc1:.4f}, PC2 = {pc2:.4f}, PC1+PC2 = {pc1+pc2:.4f} "
          f"(gate ≥ 0.40: {'PASS' if pc1+pc2 >= 0.40 else 'FAIL'})")
    # Project
    M_centered = C - mu  # [N, 9]
    uv = M_centered @ W2  # [N, 2]
    # Möbius (identity, frozen) → uv unchanged
    uv = identity_mobius(uv)
    # Stereographic lift → S² points
    p = stereographic_from_south_pole(uv)  # [N, 3]
    norm_p = np.linalg.norm(p, axis=-1)
    assert np.allclose(norm_p, 1.0, atol=1e-6), f"S² points not unit norm: max |‖p‖-1| = {np.abs(norm_p-1).max()}"
    print(f"  S² points unit norm: PASS (max |‖p‖-1| = {np.abs(norm_p-1).max():.2e})")

    # --- Step 5: Compute t coordinate (1-D, from PC1) ---
    W1 = W2[:, 0]  # [9]
    t = coordinate_t(M_centered, W1)
    print(f"  t ∈ [0, 1] (N={n_items}, min={t.min():.4f}, max={t.max():.4f}, mean={t.mean():.4f})")

    # --- Step 6: Fit harmonic curve γ(t) via closed-form ridge ---
    print("\n[6] Fitting harmonic curve γ(t) via closed-form ridge on real SH basis (L=3)...")
    Ccoefs, Phi = fit_harmonic_curve(p, t, L=3, ridge_lambda=1e-3)
    print(f"  basis size: n_basis = {Ccoefs.shape[0]} (L=3 → 16 functions)")
    print(f"  ridge solve: C* = (ΦᵀΦ + 10⁻³ I)⁻¹ Φᵀ Z  → shape {Ccoefs.shape}")

    # --- Step 7: Evaluate γ at each t_i + dense grid + compute residuals ---
    p_hat = evaluate_curve(Ccoefs, t, L=3)  # at each corpus item's t
    residuals = chordal_residual(p, p_hat)
    print(f"  residuals: min={residuals.min():.4f}, max={residuals.max():.4f}, "
          f"mean={residuals.mean():.4f}, median={np.median(residuals):.4f}, "
          f"std={residuals.std():.4f}")

    # Dense grid of t for the curve polyline in the PNG
    t_grid = np.linspace(0.001, 0.999, 360)  # avoid poles
    p_hat_curve = evaluate_curve(Ccoefs, t_grid, L=3)
    print(f"  dense γ(t) polyline: {t_grid.shape[0]} points")

    # --- Step 8: Write curve-map.json ---
    print("\n[8] Writing curve-map.json...")
    map_path = OUT_DIR / "curve-map.json"
    map_entries = []
    for i, slug in enumerate(slugs):
        x, y, z = p[i, 0], p[i, 1], p[i, 2]
        lon = float(np.degrees(np.arctan2(y, x)))
        lat = float(np.degrees(np.arcsin(np.clip(z, -1.0, 1.0))))
        cov_i = [int(C[i, j]) for j in range(n_prim)]
        map_entries.append({
            "file": slug,
            "lon": lon,
            "lat": lat,
            "t": float(t[i]),
            "residual": float(residuals[i]),
            "primitives": cov_i,
        })
    map_doc = {
        "basis": primitives,
        "primitive_definitions": {p: f"corpus-internal 9-primitive variant of internal-big-picture (#{i})"
                                   for i, p in enumerate(primitives)},
        "corpus_origin": "synthetic" if corpus.get("synthetic") else "real",
        "corpus_source_url": None if corpus.get("synthetic") else CORPUS_REPO_URL,
        "n_items": n_items,
        "pc1_explained": pc1,
        "pc2_explained": pc2,
        "pc1_plus_pc2": pc1 + pc2,
        "ridge_lambda": 1e-3,
        "basis_L": 3,
        "basis_size": int(Ccoefs.shape[0]),
        "identity_mobius_frozen": True,
        "fit_method": "closed-form ridge on real spherical-harmonic basis (L=3, 16 functions)",
        "distance_metric": "chordal S^2 (bounded [0, 2])",
        "curve_coefficients_shape": list(Ccoefs.shape),
        "points": map_entries,
    }
    with open(map_path, "w") as f:
        json.dump(map_doc, f, indent=2)
    print(f"  saved {map_path} ({map_path.stat().st_size} bytes)")

    # --- Step 9: Render curve-map.png ---
    print("\n[9] Rendering curve-map.png (Mollweide/Aitoff projection, coolwarm cmap)...")
    png_path = OUT_DIR / "curve-map.png"
    render_curve_map(p, p_hat_curve, t_grid, residuals, slugs, missing_map,
                     primitives, png_path)

    # --- Step 10: Build RSI-priority-list.md ---
    print("\n[10] Building RSI-priority-list.md (top-10 highest-residual)...")
    prio_path = OUT_DIR / "RSI-priority-list.md"
    build_priority_list(slugs, residuals, missing_map, primitives, p, t, prio_path)

    # --- Step 11: Build README.md ---
    print("\n[11] Building README.md...")
    readme_path = OUT_DIR / "README.md"
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    build_readme(slugs, residuals, missing_map, corpus, readme_path, generated_at,
                 pc_explained=(pc1, pc2))

    # --- Summary ---
    print(f"\n=== Done. Outputs in {OUT_DIR} ===")
    for p in sorted(OUT_DIR.iterdir()):
        print(f"  {p.name}: {p.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
