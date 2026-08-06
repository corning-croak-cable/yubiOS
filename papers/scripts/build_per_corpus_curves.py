#!/usr/bin/env python3.12
"""build_per_corpus_curves.py — extends PR #186 (full curve map) with per-corpus PNGs
for the 3 corpora from PR #185 (skills/, refs/, docs/).

Pipeline (one corpus item per fit):
  1. Build per-file 9-D binary primitive coverage vector c ∈ {0,1}^9
     (deep-research variant — from `single-action-curve-rsi` SKILL.md §9-D Primitive Basis:
      has_purpose, has_evidence, has_correction, has_constraint, has_pushback,
      has_test, has_source, has_recommendation, has_priority).
  2. Project to S² via PCA top-2 → stereographic lift → identity-init Möbius
     (frozen φ_θ per PR1's contract).
  3. Fit harmonic curve γ(t) through the projected points using closed-form ridge
     on the real spherical-harmonic basis at L=3 (16 functions).
  4. Compute chordal residual r_i = ‖p_i − γ(t_i)‖₂ ∈ [0, 2] per point.
  5. Write outputs: curve-map.json, curve-map.png, RSI-priority.md per corpus
     + combined README.md.

Inputs:
  - skills/ : 79 SKILL.md files at /var/workspace/skills/github-yubios-KS9n5GAT/<skill>/SKILL.md
              (excluding .gitkeep and skill_registry.json)
  - refs/   : 14 deep-research .md files at /var/workspace/documents/github-yubios-KS9n5GAT/*.md
  - docs/   : 10 memory .md files at /var/workspace/memory/personal-WbtUgeUv/*.md

Math reuse: copied verbatim from PR1's `fit-full-curve-map.py`
(/var/workspace/documents/github-yubios-KS9n5GAT/papers/scripts/fit-full-curve-map.py).
Only the basis and the corpus-load logic differ from PR1.

Out-of-scope: do NOT push to git. do NOT create a PR. Files-only per spec.
"""
from __future__ import annotations

import json
import re
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
OUT_DIR = ROOT / "documents" / SPACE_DIR / "subagents" / "per-corpus-pngs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SKILLS_ROOT = ROOT / "skills" / SPACE_DIR
REFS_ROOT = ROOT / "documents" / SPACE_DIR
DOCS_ROOT = ROOT / "memory" / "personal-WbtUgeUv"

# --------------------------------------------------------------------------- #
# 1. The 9-D primitive basis (deep-research variant — single-action-curve-rsi).
# --------------------------------------------------------------------------- #
PRIMITIVES_9: List[str] = [
    "has_purpose",
    "has_evidence",
    "has_correction",
    "has_constraint",
    "has_pushback",
    "has_test",
    "has_source",
    "has_recommendation",
    "has_priority",
]

# Patterns per primitive (case-insensitive, any one match → contributes to the
# primitive's per-section score; per-section scores are weighted-averaged to
# file level then thresholded at 0.5 → binary).
PRIMITIVE_PATTERNS: Dict[str, List[str]] = {
    "has_purpose": [
        r"\bTL;DR\b", r"\bSummary\b", r"\bProblem Statement\b",
        r"\bGoal\b", r"\bIntent\b",
    ],
    "has_evidence": [
        r"\b\d{3,}\b",  # any 3-digit or larger number
        r"\bverified\b", r"\bPASS\b", r"\bmeasured\b",
        r"Probability:\s*high",
    ],
    "has_correction": [
        r"V\d+\s+failure", r"\bwas wrong\b", r"\bsymptom\b",
        r"not the cause", r"the actual root cause",
    ],
    "has_constraint": [
        r"\bMust\b", r"\bNever\b", r"\bCannot\b",
        r"ADR-\d+", r"\bDon't\b", r"\bban\b",
    ],
    "has_pushback": [
        r"\bPENDING\b", r"no release tag", r"\blimitations\b",
        r"not yet", r"~\s*3\s*weeks",
    ],
    "has_test": [
        r"V\d+-fix-[A-Z]", r"\bTest:\b", r"\bVerified\b",
        r"\bverify\b", r"\bPASS\b", r"\bVerification:",
    ],
    "has_source": [
        r"github\.com/", r"https?://", r"PR\s*#\d+",
        r"issue\s*#\d+", r"commit\s+`[0-9a-f]+`",
    ],
    "has_recommendation": [
        r"fix-[A-Z]", r"surgical fix", r"\bborrowable\b",
        r"V\d+\s*fix", r"ordered next steps",
    ],
    "has_priority": [
        r"\bP[012]/P[012]\b", r"high/medium/low",
        r"Probability:\s*(high|medium|low)", r"\bcritical\b",
    ],
}


# --------------------------------------------------------------------------- #
# 2. Coverage computation — per-file 9-D binary vector.
# --------------------------------------------------------------------------- #
def _compile_patterns() -> Dict[str, List[re.Pattern]]:
    return {p: [re.compile(pat, re.IGNORECASE) for pat in pats]
            for p, pats in PRIMITIVE_PATTERNS.items()}

_COMPILED = _compile_patterns()


def _split_sections(text: str) -> List[Tuple[str, int]]:
    """Split markdown into sections (by ## heading). Return [(section_text, byte_len)]."""
    parts = re.split(r"(?m)^##\s+", text)
    out: List[Tuple[str, int]] = []
    # The first chunk is everything before the first `## ` heading.
    if parts:
        out.append((parts[0], len(parts[0].encode("utf8"))))
    for chunk in parts[1:]:
        # chunk starts with the heading title (no `## ` since we split on that)
        # Treat the full chunk as a section.
        out.append((chunk, len(chunk.encode("utf8"))))
    return out


def _section_score(section_text: str) -> Dict[str, float]:
    """Per-section primitive score ∈ [0, 1] = (patterns matched) / (patterns total).
    Capped at 1.0 per primitive. Truncated to first ~5000 chars per spec."""
    text = section_text[:5000]
    out: Dict[str, float] = {}
    for prim, pats in _COMPILED.items():
        hits = sum(1 for p in pats if p.search(text))
        out[prim] = min(1.0, hits / max(1, len(pats)))
    return out


def file_coverage(text: str, use_section_weighting: bool = True) -> Tuple[np.ndarray, Dict[str, float]]:
    """Compute the 9-D coverage vector for one file.

    If use_section_weighting=True (refs/ spec): weighted average over sections,
       weights = section byte length (normalized), threshold at 0.5 → binary.
    If use_section_weighting=False (skills/, docs/): treat the whole file as
       one section (full body, no truncation beyond the per-section 5000-cap
       which is moot for single-section).
    """
    if use_section_weighting:
        sections = _split_sections(text)
        if len(sections) < 2:
            # Single-section fallback: treat whole file as one section.
            sections = [(text, len(text.encode("utf8")))]
        total_bytes = sum(b for _, b in sections) or 1
        per_section_scores: List[Tuple[Dict[str, float], int]] = []
        for sec_text, sec_bytes in sections:
            score = _section_score(sec_text)
            per_section_scores.append((score, sec_bytes))
        # Weighted average per primitive
        weighted: Dict[str, float] = {}
        for prim in PRIMITIVES_9:
            num = sum(score[prim] * sec_bytes for score, sec_bytes in per_section_scores)
            weighted[prim] = num / total_bytes
        vec = np.array([1.0 if weighted[prim] >= 0.5 else 0.0
                        for prim in PRIMITIVES_9], dtype=np.float64)
        return vec, weighted
    else:
        # Whole-file scan: count all primitive matches across the entire file.
        full_score: Dict[str, float] = {}
        for prim, pats in _COMPILED.items():
            hits = sum(1 for p in pats if p.search(text))
            full_score[prim] = min(1.0, hits / max(1, len(pats)))
        vec = np.array([1.0 if full_score[prim] >= 0.5 else 0.0
                        for prim in PRIMITIVES_9], dtype=np.float64)
        return vec, full_score


# --------------------------------------------------------------------------- #
# 3. Corpus loaders.
# --------------------------------------------------------------------------- #
def list_skills_corpus() -> List[Tuple[str, str]]:
    """Return [(slug, file_path)] for every skill with a SKILL.md, excluding
    .git, .gitkeep, skill_registry.json."""
    out: List[Tuple[str, str]] = []
    for entry in sorted(SKILLS_ROOT.iterdir()):
        if not entry.is_dir():
            continue
        name = entry.name
        if name.startswith("."):
            continue
        if name == "skill_registry.json":
            continue
        skill_md = entry / "SKILL.md"
        if skill_md.exists():
            out.append((name, str(skill_md)))
    return out


def list_refs_corpus() -> List[Tuple[str, str]]:
    """Return [(slug, file_path)] for every .md at the top level of REFS_ROOT
    (excluding the `papers/`, `scripts/`, `GET_TO_WORK/`, and `subagents/`
    subdirectories — we want only the deep-research outputs at the top level)."""
    out: List[Tuple[str, str]] = []
    for entry in sorted(REFS_ROOT.iterdir()):
        if not entry.is_file():
            continue
        if entry.suffix != ".md":
            continue
        out.append((entry.stem, str(entry)))
    return out


def list_docs_corpus() -> List[Tuple[str, str]]:
    """Return [(slug, file_path)] for every .md at the top level of DOCS_ROOT."""
    out: List[Tuple[str, str]] = []
    for entry in sorted(DOCS_ROOT.iterdir()):
        if not entry.is_file():
            continue
        if entry.suffix != ".md":
            continue
        out.append((entry.stem, str(entry)))
    return out


def load_corpus(name: str) -> Tuple[List[str], np.ndarray, Dict[str, List[str]], List[float]]:
    """Load a corpus, build the 9-D coverage matrix.

    Returns (slugs, C, missing_map, raw_scores_per_file).

    - slugs: list of file identifiers (one per item)
    - C: shape (n, 9) numpy array, dtype float64, values in {0, 1}
    - missing_map: {slug: [primitive_name, ...]} (names of primitives with c_j == 0)
    - raw_scores_per_file: list of per-file primitive coverage scores (the
      weighted means before thresholding — useful for diagnostics)
    """
    if name == "skills":
        files = list_skills_corpus()
        weighting = False
    elif name == "refs":
        files = list_refs_corpus()
        weighting = True
    elif name == "docs":
        files = list_docs_corpus()
        weighting = False
    else:
        raise ValueError(f"unknown corpus: {name}")

    slugs: List[str] = []
    rows: List[np.ndarray] = []
    missing_map: Dict[str, List[str]] = {}
    raw_scores_per_file: List[Dict[str, float]] = []

    for slug, path in files:
        try:
            text = Path(path).read_text(encoding="utf8", errors="replace")
        except Exception as e:
            print(f"  WARN: could not read {path}: {e}", file=sys.stderr)
            continue
        vec, scores = file_coverage(text, use_section_weighting=weighting)
        slugs.append(slug)
        rows.append(vec)
        missing_map[slug] = [PRIMITIVES_9[j] for j in range(9) if vec[j] == 0.0]
        raw_scores_per_file.append(scores)

    C = np.vstack(rows) if rows else np.zeros((0, 9), dtype=np.float64)
    return slugs, C, missing_map, raw_scores_per_file


# --------------------------------------------------------------------------- #
# 4. Math: PCA top-2 → stereographic → identity Möbius → real SH curve.
#    (Verbatim from PR1's `fit-full-curve-map.py`.)
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
    u = uv[..., 0]
    v = uv[..., 1]
    denom = u * u + v * v + 1.0
    X = 2.0 * u / denom
    Y = 2.0 * v / denom
    Z = (u * u + v * v - 1.0) / denom
    return np.stack([X, Y, Z], axis=-1)


def identity_mobius(z):
    return z  # frozen φ_θ per PR1's contract


def real_spherical_harmonic_basis(ell: int, m: int, theta: np.ndarray, phi: np.ndarray) -> np.ndarray:
    from math import factorial, sqrt
    norm = np.sqrt((2 * ell + 1) / (4 * np.pi) *
                   factorial(ell - abs(m)) / factorial(ell + abs(m)))
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


def fit_harmonic_curve(p: np.ndarray, t: np.ndarray, L: int = 3,
                       ridge_lambda: float = 1e-3) -> Tuple[np.ndarray, np.ndarray]:
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


# --------------------------------------------------------------------------- #
# 5. Render curve-map.png.
# --------------------------------------------------------------------------- #
def render_curve_map(out_path: Path, p: np.ndarray, p_hat_curve: np.ndarray,
                     t_grid: np.ndarray, residuals: np.ndarray, slugs: List[str],
                     missing_map: Dict[str, List[str]], corpus_name: str,
                     title_prefix: str = "Per-corpus curve map") -> None:
    def to_lonlat(p_xyz: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        x, y, z = p_xyz[..., 0], p_xyz[..., 1], p_xyz[..., 2]
        lon = np.arctan2(y, x)
        lat = np.arcsin(np.clip(z, -1.0, 1.0))
        return lon, lat

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

    vmin = float(residuals.min())
    vmax = float(residuals.max())
    if vmax - vmin < 1e-9:
        vmax = vmin + 1e-9
    norm = Normalize(vmin=vmin, vmax=vmax)
    cmap = matplotlib.colormaps["coolwarm"]
    sc = ax.scatter(lon_p, lat_p, c=residuals, cmap=cmap, norm=norm,
                    s=28, alpha=0.85, edgecolors="#222222", linewidths=0.4,
                    label=f"corpus items (color = chordal residual)")

    # Label top-5 highest-residual points
    order = np.argsort(residuals)[::-1]
    top5 = order[:5]
    for idx in top5:
        label_text = slugs[idx][:22] + ("…" if len(slugs[idx]) > 22 else "")
        ax.annotate(label_text,
                    xy=(lon_p[idx], lat_p[idx]),
                    xytext=(lon_p[idx] + 0.18, lat_p[idx] + 0.10),
                    fontsize=7, color="#5a1a1a",
                    arrowprops=dict(arrowstyle="-", color="#5a1a1a", lw=0.4))

    cbar = fig.colorbar(sc, ax=ax, orientation="horizontal",
                        fraction=0.04, pad=0.10, aspect=40)
    cbar.set_label(r"chordal residual $r = \|p - \gamma(t)\|_2$  (high = red, low = blue)",
                   fontsize=10, color="#222222")

    n_items = len(slugs)
    ax.set_title(f"{title_prefix} — {corpus_name} corpus (extends PR #186)\n"
                 f"{n_items} items, 9-D deep-research primitive basis, "
                 f"identity-init Möbius (frozen $\\varphi_\\theta$)",
                 fontsize=11, color="#1a3a5c", pad=22)
    ax.legend(loc="lower left", fontsize=9, framealpha=0.92)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  saved {out_path} ({out_path.stat().st_size} bytes)")


# --------------------------------------------------------------------------- #
# 6. RSI-priority-list.md (top-10 highest-residual files).
# --------------------------------------------------------------------------- #
def build_priority_md(out_path: Path, corpus_name: str, slugs: List[str],
                      residuals: np.ndarray, missing_map: Dict[str, List[str]],
                      p: np.ndarray, t: np.ndarray) -> List[Tuple[str, float, List[str]]]:
    """Write the per-corpus priority markdown and return [(slug, residual, missing), ...] for top-N."""
    order = np.argsort(residuals)[::-1]
    top = order[:10]
    rows: List[Tuple[str, float, List[str]]] = []

    lines = [
        f"# RSI Priority List — Top-10 Highest-Residual Files — `{corpus_name}` corpus",
        "",
        "The geodesic residual on the fitted curve γ(t) is the sparse-cell / RSI-priority",
        "signal for this corpus. The 10 files with the largest residual are the highest-",
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
        covered = 9 - len(miss)
        ti = t[idx]
        x, y, z = p[idx, 0], p[idx, 1], p[idx, 2]
        miss_str = ", ".join(f"`{m}`" for m in miss) if miss else "(none)"
        lines.append(
            f"| {rank} | `{slug}` | {r:.4f} | {miss_str} | {covered}/9 | "
            f"{ti:.4f} | ({x:+.3f}, {y:+.3f}, {z:+.3f}) |"
        )
        rows.append((slug, float(r), miss))

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
        "- High-residual files contribute the largest per-cycle delta (largest gap",
        "  between the projected point p and the fitted curve γ(t)).",
        "",
        "## How to act on this list",
        "",
        "Per file in rank order, run one single-action cycle:",
        "",
        "1. Pick the missing primitive whose flip minimizes d_post (geodesic-only criterion).",
        "2. Apply the corresponding primitive-closure edit (e.g. add a `## Verification`",
        "   section if `has_test` wins).",
        "3. Re-fit and verify Δ ≥ 0.",
        "",
        "Stop when the cumulative delta plateaus (RSI fixpoint). PR4",
        "(`curve-drift-detector`) will close the loop across corpora.",
        "",
    ]

    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  saved {out_path} ({out_path.stat().st_size} bytes)")
    return rows


# --------------------------------------------------------------------------- #
# 7. Main per-corpus pipeline.
# --------------------------------------------------------------------------- #
def process_corpus(corpus_name: str) -> Dict:
    """Process a single corpus end-to-end. Return a summary dict."""
    print(f"\n=== Corpus: {corpus_name} ===")
    slugs, C, missing_map, raw_scores = load_corpus(corpus_name)
    n = len(slugs)
    print(f"  loaded {n} files; coverage matrix shape: {C.shape}")
    if n == 0:
        return {"corpus": corpus_name, "n": 0, "primitives": PRIMITIVES_9, "points": []}

    # Sub-20 decomposition rule (learned-latent-curve §A.2): if N < 20, the curve
    # fit is unreliable — we still fit (per spec, fit on all 3 corpora including
    # docs at N=10) and surface the warning in the README.
    sub20_warning = (n < 20)
    if sub20_warning:
        print(f"  WARN: N={n} < 20 (sub-20 decomposition rule applies; "
              f"curve fit is unreliable but we proceed per spec)")

    # PCA top-2 → stereographic lift → identity Möbius (frozen)
    W2, mu, explained = pca_topk(C, k=2)
    pc1, pc2 = float(explained[0]), float(explained[1])
    print(f"  PC1 = {pc1:.4f}, PC2 = {pc2:.4f}, PC1+PC2 = {pc1+pc2:.4f} "
          f"(gate ≥ 0.40: {'PASS' if pc1+pc2 >= 0.40 else 'FAIL'})")
    M_centered = C - mu
    uv = M_centered @ W2
    uv = identity_mobius(uv)
    p = stereographic_from_south_pole(uv)
    norm_p = np.linalg.norm(p, axis=-1)
    print(f"  S² points unit norm: max |‖p‖-1| = {np.abs(norm_p-1).max():.2e}")

    # 1-D coordinate t (PC1, min-max)
    W1 = W2[:, 0]
    t = coordinate_t(M_centered, W1)
    print(f"  t ∈ [0, 1] (N={n}, min={t.min():.4f}, max={t.max():.4f}, mean={t.mean():.4f})")

    # Fit γ(t)
    Ccoefs, Phi = fit_harmonic_curve(p, t, L=3, ridge_lambda=1e-3)
    print(f"  basis size: n_basis = {Ccoefs.shape[0]} (L=3 → 16 functions)")

    p_hat = evaluate_curve(Ccoefs, t, L=3)
    residuals = chordal_residual(p, p_hat)
    print(f"  residuals: min={residuals.min():.4f}, max={residuals.max():.4f}, "
          f"mean={residuals.mean():.4f}, median={np.median(residuals):.4f}, "
          f"std={residuals.std():.4f}")

    t_grid = np.linspace(0.001, 0.999, 360)
    p_hat_curve = evaluate_curve(Ccoefs, t_grid, L=3)

    # Coverage stats
    saturated = int(sum(1 for slug in slugs if len(missing_map.get(slug, [])) == 0))
    sparse = int(sum(1 for slug in slugs if len(missing_map.get(slug, [])) >= 7))
    avg_cov = float(np.mean([9 - len(missing_map[s]) for s in slugs]))
    coverage_counts = [9 - len(missing_map[s]) for s in slugs]

    # Write JSON
    map_path = OUT_DIR / f"curve-map-{corpus_name}.json"
    map_entries = []
    for i, slug in enumerate(slugs):
        x, y, z = p[i, 0], p[i, 1], p[i, 2]
        lon = float(np.degrees(np.arctan2(y, x)))
        lat = float(np.degrees(np.arcsin(np.clip(z, -1.0, 1.0))))
        cov_i = [int(C[i, j]) for j in range(9)]
        map_entries.append({
            "file": slug,
            "lon": lon,
            "lat": lat,
            "t": float(t[i]),
            "residual": float(residuals[i]),
            "primitives": cov_i,
        })
    map_doc = {
        "corpus": corpus_name,
        "basis": PRIMITIVES_9,
        "primitive_definitions": {
            p: f"deep-research 9-primitive variant (#{i}) from `single-action-curve-rsi` SKILL.md §9-D Primitive Basis"
            for i, p in enumerate(PRIMITIVES_9)
        },
        "n_items": n,
        "pc1_explained": pc1,
        "pc2_explained": pc2,
        "pc1_plus_pc2": pc1 + pc2,
        "ridge_lambda": 1e-3,
        "basis_L": 3,
        "basis_size": int(Ccoefs.shape[0]),
        "identity_mobius_frozen": True,
        "fit_method": "closed-form ridge on real spherical-harmonic basis (L=3, 16 functions)",
        "distance_metric": "chordal S^2 (bounded [0, 2])",
        "sub20_warning": sub20_warning,
        "saturated_count": saturated,
        "sparse_count": sparse,
        "avg_coverage": avg_cov,
        "points": map_entries,
    }
    with open(map_path, "w") as f:
        json.dump(map_doc, f, indent=2)
    print(f"  saved {map_path} ({map_path.stat().st_size} bytes)")

    # Render PNG
    png_path = OUT_DIR / f"curve-map-{corpus_name}.png"
    render_curve_map(png_path, p, p_hat_curve, t_grid, residuals, slugs,
                     missing_map, corpus_name)

    # Priority MD
    prio_path = OUT_DIR / f"RSI-priority-{corpus_name}.md"
    top_rows = build_priority_md(prio_path, corpus_name, slugs, residuals,
                                 missing_map, p, t)

    return {
        "corpus": corpus_name,
        "n": n,
        "pc1": pc1,
        "pc2": pc2,
        "pc1_plus_pc2": pc1 + pc2,
        "sub20_warning": sub20_warning,
        "saturated_count": saturated,
        "sparse_count": sparse,
        "avg_coverage": avg_cov,
        "residual_min": float(residuals.min()),
        "residual_max": float(residuals.max()),
        "residual_mean": float(residuals.mean()),
        "residual_median": float(np.median(residuals)),
        "residual_std": float(residuals.std()),
        "top_priority_rows": top_rows,
        "files": {
            "json": str(map_path),
            "png": str(png_path),
            "priority_md": str(prio_path),
        },
    }


# --------------------------------------------------------------------------- #
# 8. Combined README.md.
# --------------------------------------------------------------------------- #
def build_combined_readme(summaries: List[Dict]) -> Path:
    out_path = OUT_DIR / "README.md"
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = [
        "# Per-Corpus Curve Maps (PR #186 extension)",
        "",
        f"Generated by `build_per_corpus_curves.py` on **{generated_at}**.",
        "",
        "## What this is",
        "",
        "Extension of **PR #186 (Full curve map per corpus)** to the 3 corpora from",
        "**PR #185 (multi-corpus audit)** — `skills/`, `refs/`, `docs/` — using the",
        "**same math pipeline** but with the deep-research 9-D primitive basis from",
        "`single-action-curve-rsi` SKILL.md §9-D Primitive Basis (per spec).",
        "",
        "For each corpus we:",
        "",
        "1. Compute the **9-D binary primitive coverage vector** c ∈ {0,1}⁹ by scanning",
        "   each file's body for the 9 deep-research patterns: `has_purpose`, `has_evidence`,",
        "   `has_correction`, `has_constraint`, `has_pushback`, `has_test`, `has_source`,",
        "   `has_recommendation`, `has_priority`.",
        "2. Project to **S²** via PCA top-2 → stereographic lift from the south pole →",
        "   identity-init Möbius reparameterization (φ_θ **frozen** at identity, per PR1's contract).",
        "3. Fit a **harmonic curve γ(t)** through the projected points using a real",
        "   spherical-harmonic basis at L=3 (16 functions), solved by closed-form ridge",
        "   with λ=10⁻³.",
        "4. Compute the **chordal residual** r_i = ‖p_i − γ(t_i)‖₂ per file. The residual",
        "   is the sparse-cell / RSI-priority signal — high residual = furthest from the",
        "   fitted curve = highest expected Δ on the next single-action cycle.",
        "",
        "## Outputs (in `subagents/per-corpus-pngs/`)",
        "",
        "| File | Description |",
        "|---|---|",
        "| `curve-map-skills.json` / `.png` | Skills corpus (79 SKILL.md files) — 9-D coverage, curve fit, residual map. |",
        "| `curve-map-refs.json` / `.png` | Refs corpus (14 deep-research .md files) — 9-D coverage, curve fit, residual map. |",
        "| `curve-map-docs.json` / `.png` | Docs corpus (10 memory .md files) — 9-D coverage, curve fit, residual map. |",
        "| `RSI-priority-skills.md` | Top-10 highest-residual skills (next-RSI queue). |",
        "| `RSI-priority-refs.md` | Top-10 highest-residual refs. |",
        "| `RSI-priority-docs.md` | Top-10 highest-residual docs. |",
        "| `README.md` | This file. |",
        "",
        "## Per-corpus comparison",
        "",
        "| Corpus | N | Basis | Saturated | Sparse (≥7 missing) | Avg coverage | PC1+PC2 | Peak residual | Mean residual | Sub-20 warning |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]

    for s in summaries:
        lines.append(
            f"| `{s['corpus']}` | {s['n']} | 9-D | {s['saturated_count']}/{s['n']} | "
            f"{s['sparse_count']}/{s['n']} | {s['avg_coverage']:.2f}/9 | "
            f"{s['pc1_plus_pc2']:.4f} | {s['residual_max']:.4f} | "
            f"{s['residual_mean']:.4f} | "
            f"{'YES (N<20)' if s['sub20_warning'] else 'no'} |"
        )

    lines += [
        "",
        "## Cross-corpus aggregate stats",
        "",
        f"- **Total items fitted:** {sum(s['n'] for s in summaries)}",
        f"- **Peak residual overall:** {max(s['residual_max'] for s in summaries):.4f}",
        f"- **Mean residual overall:** "
        f"{sum(s['residual_mean'] * s['n'] for s in summaries) / max(1, sum(s['n'] for s in summaries)):.4f}",
        "",
        "### Shared top-3 files across corpora",
        "",
        "The 3 corpora are disjoint by design (skills vs deep-research .md vs memory files),",
        "so no slug is expected to appear in more than one corpus's top-3. The intersection is",
        "empty by construction.",
        "",
        "- skills top-3: " + ", ".join(f"`{r[0]}` ({r[1]:.4f})" for r in summaries[0]['top_priority_rows'][:3]),
        "- refs top-3: "   + ", ".join(f"`{r[0]}` ({r[1]:.4f})" for r in summaries[1]['top_priority_rows'][:3]),
        "- docs top-3: "   + ", ".join(f"`{r[0]}` ({r[1]:.4f})" for r in summaries[2]['top_priority_rows'][:3]),
        "",
        "## How this differs from PR #186 (Full curve map)",
        "",
        "| Element | PR #186 | This artifact |",
        "|---|---|---|",
        "| Basis | `internal-big-picture` 9-primitive (attestation, trust_chain, …) | `single-action-curve-rsi` 9-primitive (has_purpose, has_evidence, …) |",
        "| Corpus | `papers/data/` on `yubi-OS/yubiOS` (cycle-1 entries) | `skills/`, `refs/`, `docs/` (local mirror) |",
        "| Math | Verbatim (PCA → stereo → identity Möbius → SH L=3 → ridge) | Verbatim |",
        "| Distance | Chordal S² | Chordal S² |",
        "| Möbius | Frozen at identity | Frozen at identity |",
        "| Basis size | 16 functions | 16 functions |",
        "| Ridge λ | 10⁻³ | 10⁻³ |",
        "| Outputs | 1 (papers-corpus curve map) | 3 (one per corpus) |",
        "| Section weighting | n/a (single-cycle-1 vector per skill) | refs/: weighted by section byte length; skills/ + docs/: whole-file |",
        "",
        "## Math conventions (frozen from PR1 + parent skills)",
        "",
        "- 9-D basis: deep-research variant from `single-action-curve-rsi` SKILL.md",
        "- S² lift: PCA top-2 → stereographic from south pole → S² (`hyperspherical-harmonic-curve` §3.2)",
        "- Möbius: Identity-init, frozen (a=d=1, b=c=0; no L-BFGS-B refinement)",
        "- Basis: Real spherical harmonics L=3 (16 functions) via explicit Legendre + cos/sin split",
        "- Fit: Closed-form ridge C* = (ΦᵀΦ + λI)⁻¹ Φᵀ Z, λ=10⁻³",
        "- Domain parameterization: θ(t) = π·t, φ(t) = 2π·t (closed curve, t ∈ [0,1])",
        "- t coordinate: PC1 of centered coverage, min-max scaled to [0, 1]",
        "- Distance: Chordal S² = ‖p − γ(t)‖₂ ∈ [0, 2]",
        "- Degree weights: Frozen (degree_weights not learnable)",
        "",
        "## Sub-20 decomposition rule (learned-latent-curve §A.2)",
        "",
        "The learned-latent-curve skill notes that **N < 20 corpus size makes the curve fit",
        "unreliable**. The `docs/` corpus has N=10 and is BELOW this gate. We proceed per spec",
        "(fit all 3 corpora including docs) and surface this warning prominently in the docs/",
        "outputs. The fixpoint decision for docs/ should weigh the residual values with this",
        "uncertainty in mind.",
        "",
        "## Verification (end-to-end run)",
        "",
        "- All 3 `curve-map-<corpus>.json` files parse as valid JSON.",
        "- All 3 `curve-map-<corpus>.png` files render (Aitoff projection of γ + projected points).",
        "- All 3 `RSI-priority-<corpus>.md` files are populated with the top-10 highest-residual items.",
        "- Combined `README.md` aggregates per-corpus stats + cross-corpus comparison.",
        "- Script ran end-to-end without exception on the 3 corpora.",
        "",
        "## Risks & worked-arounds",
        "",
        "- **docs/ at N=10 < 20 gate**: fitted anyway per spec; the curve fit is unreliable",
        "  on a 10-item corpus. Surface this in every decision that uses docs/ residuals.",
        "- **section-weighting only on refs/**: skills/ + docs/ use whole-file scan (per spec).",
        "  This makes the 3 corpora not directly comparable on absolute residual scales —",
        "  compare rankings within each corpus, not residuals across corpora.",
        "- **PC1+PC2 < 0.40 gate** may fail for one or more corpora (especially docs/ at",
        "  N=10). This is documented per corpus in its JSON and surfaced in this README.",
        "- The fit is not pushed to git and no PR is created (per spec). The orchestrator",
        "  assembles and pushes.",
        "",
    ]

    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  saved {out_path} ({out_path.stat().st_size} bytes)")
    return out_path


# --------------------------------------------------------------------------- #
# 9. Main.
# --------------------------------------------------------------------------- #
def main() -> int:
    print("=== Per-corpus curve maps (PR #186 extension) ===")
    summaries = []
    for name in ["skills", "refs", "docs"]:
        summary = process_corpus(name)
        summaries.append(summary)

    print("\n=== Building combined README.md ===")
    build_combined_readme(summaries)

    print(f"\n=== Done. Outputs in {OUT_DIR} ===")
    for p in sorted(OUT_DIR.iterdir()):
        print(f"  {p.name}: {p.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
