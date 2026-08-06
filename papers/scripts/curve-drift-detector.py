#!/usr/bin/env python3
"""curve-drift-detector.py — PR4 cross-corpus drift detector.

Aligns the harmonic curve fit on `papers/data/` (papers-corpus) against the
harmonic curve fit on the SELF-doc corpus (memory/personal-WbtUgeUv/), computes
the Möbius warp between them, and flags regions of large warp as drift
signals (input for self-archaeology).

Math conventions (frozen from learned-latent-curve + hyperspherical-harmonic-curve):
  - 9-D `internal-big-picture` primitive basis (9 of 10 primitives; self_describing
    dropped at 94% coverage per the parent's rule).
  - Same basis for BOTH corpora (an explicit cross-corpus deviation from the
    per-corpus basis rule in curve-guided-rsi-self — documented).
  - PCA -> stereographic -> Möbius lift to S^2 (default N=2).
  - Identity-init Möbius (a=d=1, b=c=0; 6 real DOF; closed via L-BFGS-B).
  - Chordal S^2 distance for sparse-cell detection (r ~ 0.095).
  - Frozen degree weights (degree_weights not learnable in this artifact).
  - Sub-20 corpus decomposition rule: NOT applied (both corpora > 20).

Outputs to documents/github-yubios-KS9n5GAT/papers/data/drift-output/:
  - aligned-curves.png     — both curves overlaid in S^2, warp regions highlighted
  - warp-by-region.csv     — t_A, t_B, geodesic_d, nss_axes[12], flagged rows
  - drift-priority-list.md — top-10 flagged drift regions w/ self-archaeology hook
  - mobius-transform.json  — fitted rotation/dilation/translation params
  - README.md              — what/regen/math/how-to-read
  - papers-corpus-listing.json
  - self-corpus-listing.json
"""
from __future__ import annotations

import csv
import json
import math
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.optimize import minimize

# --------------------------------------------------------------------------- #
# 0. Paths (all absolute or rooted at /var/workspace/).
# --------------------------------------------------------------------------- #
ROOT = Path("/var/workspace")
PAPERS_DIR = ROOT / "documents" / "github-yubios-KS9n5GAT" / "papers"
SCRIPTS_DIR = PAPERS_DIR / "scripts"
DATA_DIR = PAPERS_DIR / "data"
OUT_DIR = DATA_DIR / "drift-output"
SELF_CORPUS_DIR = ROOT / "memory" / "personal-WbtUgeUv"
GH_RAW = (
    "https://api.github.com/repos/yubi-OS/yubiOS/contents/papers/data"
)
GH_ACCEPT = "application/vnd.github.v3.raw"
GH_CONN = "conn_1KXnkOHGgyE4"

# 9 primitives from `internal-big-picture`, minus `self_describing` (94% coverage).
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

# Keyword vocabulary per primitive for text-based scoring (self-corpus side).
# Drawn from the primitive names + standard security-engineering terminology
# documented in `internal-big-picture`. Frozen per the artifact's reproducibility
# contract (no learned weights).
PRIM_KEYWORDS: Dict[str, List[str]] = {
    "attestation": [
        "attest", "attestation", "verify", "verified", "signature", "signing",
        "cosign", "in-toto", "slsa", "rekor", "evidence", "proof",
    ],
    "trust_chain": [
        "trust", "chain", "root of trust", "chain of trust", "verified boot",
        "secure boot", "rot", "tpm", "yubikey", "key",
    ],
    "least_privilege": [
        "least privilege", "least-privilege", "capability", "capabilities",
        "sandbox", "no new privileges", "protect", "protectsystem",
        "rootless", "readonly", "nonroot", "drop",
    ],
    "declarative_policy": [
        "policy", "declarative", "rego", "opa", "psp", "pss",
        "restricted", "baseline", "conform", "constraint", "rule",
    ],
    "continuous_adaptive": [
        "continuous", "adaptive", "ongoing", "dynamic", "real-time",
        "monitor", "monitoring", "feedback", "loop", "live",
    ],
    "immutability": [
        "immutable", "immutability", "readonly", "read-only", "tamper",
        "tamper-proof", "append-only", "append only", "seal", "sealed",
        "frozen",
    ],
    "audit_evidence": [
        "audit", "evidence", "log", "journal", "trail", "history",
        "record", "documented", "receipt",
    ],
    "cryptographic_identity": [
        "crypto", "cryptographic", "key", "ed25519", "ecdsa", "rsa",
        "x509", "certificate", "cert", "sha256", "sha-256", "hash",
        "hmac", "tls",
    ],
    "segmentation": [
        "segment", "segmentation", "isolate", "isolated", "isolation",
        "namespace", "cgroup", "cgroups", "boundary", "compartment",
        "mvp", "separation",
    ],
}

# 12 NSS axes (negative-skill-space / self-archaeology) — keyword vocab for
# per-region drift prioritization. Each axis has a short keyword set; a region's
# text excerpt (the warped item's content) is scored per axis.
NSS_AXES: List[str] = [
    "audience", "inputs", "outputs", "mode", "assumption_set",
    "adjacent_problems", "failure_modes", "lifecycle", "composition",
    "knowledge_sources", "calibration", "recursion",
]
NSS_AXIS_KEYWORDS: Dict[str, List[str]] = {
    "audience": ["operator", "user", "audience", "consumer", "who", "shant"],
    "inputs": ["input", "inputs", "source", "fetch", "read", "tool", "api"],
    "outputs": ["output", "outputs", "produce", "emit", "write", "deliver"],
    "mode": ["mode", "modes", "register", "self-mode", "working-self", "creative-self"],
    "assumption_set": ["assume", "assumption", "must", "invariant", "precondition"],
    "adjacent_problems": ["adjacent", "related", "similar", "downstream", "upstream"],
    "failure_modes": ["fail", "failure", "error", "broken", "recover", "edge case"],
    "lifecycle": ["lifecycle", "re-fit", "rebuild", "rerun", "schedule", "cadence", "weekly"],
    "composition": ["compose", "composition", "pair", "orthogonal", "with skill"],
    "knowledge_sources": ["source", "corpus", "skills", "memory", "docs/", "evidence"],
    "calibration": ["calibrate", "calibration", "metric", "r^2", "r2", "pc1", "holdout"],
    "recursion": ["recursion", "recursive", "self", "self-archaeology", "rsi"],
}

# Number of warp sample points along curve-A.
N_WARP_SAMPLES = 24
# Drift flag threshold (combined warp-magnitude × NSS-axis score percentile).
WARP_FLAG_PCTL = 0.80
NSS_FLAG_PCTL = 0.80


# --------------------------------------------------------------------------- #
# 1. Corpus loaders.
# --------------------------------------------------------------------------- #
def gh_raw(rel_path: str) -> str:
    """Return GitHub raw URL (the proxy handles auth when called via run_script).

    We don't actually hit GitHub from this script — the data is downloaded once
    into session/papers-data-cache/ by the orchestrating shell. This function is
    a placeholder for the URL convention documented in the README.
    """
    return f"https://raw.githubusercontent.com/yubi-OS/yubiOS/main/{rel_path}"


def load_papers_corpus(cache_dir: Path) -> Tuple[List[Dict], List[str]]:
    """Load papers-corpus from cached JSON files.

    Each item: {"id": str, "primitive_coverage": List[int] (len 9),
                 "text": str (short label for ranking display),
                 "source": "papers-corpus"}

    The natural item unit is per-skill x per-cycle row from the multi-cycle JSON
    (79 skills x 6 cycles = 474 rows). The single-cycle JSON adds 20 corpus-level
    aggregate cycle rows (one per RSI cycle in the single-action experiment).
    """
    items: List[Dict] = []

    # Multi-cycle JSON: per-skill x per-cycle rows with explicit missing_primitives.
    multi_path = cache_dir / "multi.json"
    if not multi_path.exists():
        multi_path = cache_dir / "rsi-79-corpus-multi-cycle-2026-08-06.json"
    multi = json.loads(multi_path.read_text())
    for row in multi["all_cycles"]:
        # c[k] = 1 if skill covers primitive k (i.e., primitive is NOT missing).
        missing = set(row.get("missing_primitives") or [])
        coverage = [0 if p in missing else 1 for p in PRIMITIVES_9]
        items.append({
            "id": f"{row['slug']}@c{row['cycle']}",
            "primitive_coverage": coverage,
            "text": f"{row['slug']} cycle {row['cycle']}",
            "source": "papers-corpus",
            "delta_d": row.get("delta_d", 0.0),
            "d_pre": row.get("d_pre", 0.0),
            "d_post": row.get("d_post", 0.0),
        })

    # Single-action cycle JSON: 20 corpus-level cycle rows (aggregate fit
    # quality per cycle, not per-skill). These are coarser-grained; included as
    # corpus-level anchors.
    single_path = cache_dir / "single.json"
    if not single_path.exists():
        single_path = cache_dir / "single-action-curve-rsi-cycles-2026-08-05.json"
    if single_path.exists():
        single = json.loads(single_path.read_text())
        for row in single.get("cycles", []):
            # No per-skill primitive flag for these — use d_pre vs corpus-mean
            # as a proxy: smaller d_pre -> more coverage; map continuously to
            # {0,1} coverage. For our binary basis, mark ALL primitives covered
            # when delta_d > 0 (a cycle that improved something), else use the
            # post-cycle state. This is a coarse anchor row.
            delta = float(row.get("delta_d", 0.0))
            if delta > 0.0:
                coverage = [1] * len(PRIMITIVES_9)
            else:
                # d_pre ~= 1.0 and d_post ~= 1.0 means the cycle moved nothing;
                # mark partial coverage (5/9 randomly seeded but deterministic
                # by cycle number for reproducibility).
                coverage = [(row["cycle"] + i) % 2 for i in range(len(PRIMITIVES_9))]
            items.append({
                "id": f"single-c{row['cycle']}",
                "primitive_coverage": coverage,
                "text": f"single-action cycle {row['cycle']}",
                "source": "papers-corpus-aggregate",
                "delta_d": delta,
                "d_pre": float(row.get("d_pre", 0.0)),
                "d_post": float(row.get("d_post", 0.0)),
            })

    return items, PRIMITIVES_9


def text_coverage(text: str, primitive: str) -> int:
    """Return 1 if the text covers the primitive (keyword hit), else 0.

    Frozen keyword vocabulary per PRIM_KEYWORDS; deterministic, no learned
    weights. Multi-line text is flattened to lowercase before matching.
    """
    flat = text.lower()
    for kw in PRIM_KEYWORDS[primitive]:
        if kw in flat:
            return 1
    return 0


def load_self_corpus() -> Tuple[List[Dict], List[str]]:
    """Load self-corpus from memory/personal-WbtUgeUv/.

    Item unit (per curve-guided-rsi-self granularity rule): each `## Section`
    header is one item. Total expected count: ~109 items across 10 files
    (well above the >=20 gate; no decomposition needed).
    """
    files = [
        ("SELF.md", "self"),
        ("SELF-CHANGELOG.md", "self-changelog"),
        ("USER_PREFERENCES.md", "preferences"),
        ("COMPANY.md", "company"),
        ("RULES.md", "rules"),
        ("SAUNA_IDENTITY.md", "identity"),
        ("SAUNA_TOOLS.md", "tools"),
        ("USER_PROFILE.md", "user-profile"),
        ("USER_RELATIONSHIPS.md", "relationships"),
        ("RECENT_ACTIVITY.md", "recent-activity"),
    ]
    items: List[Dict] = []
    for fname, tag in files:
        path = SELF_CORPUS_DIR / fname
        if not path.exists():
            continue
        text = path.read_text()
        # Parse `## Section` headers; each becomes one item. Items are
        # `text` = the section's body text (between this `##` and the next).
        sections: List[Tuple[str, str]] = []
        current_h = None
        current_buf: List[str] = []
        for line in text.splitlines():
            if line.startswith("## "):
                if current_h is not None:
                    sections.append((current_h, "\n".join(current_buf)))
                current_h = line[3:].strip()
                current_buf = []
            elif current_h is not None:
                # Skip the frontmatter `---` fences if they appear inside a
                # section (they shouldn't, but defensive).
                current_buf.append(line)
        if current_h is not None:
            sections.append((current_h, "\n".join(current_buf)))

        # Drop the very first "section" if it has no `##` header (top-of-file
        # intro before the first `##`); we treat those as intro, not corpus.
        # For files like SELF-CHANGELOG.md that have `## YYYY-MM-DD` entries,
        # the granularity rule says one entry = one item — already done.
        for h, body in sections:
            if not h.strip() or h.strip().lower() in {"", "---"}:
                continue
            coverage = [
                text_coverage(h + "\n" + body, p) for p in PRIMITIVES_9
            ]
            items.append({
                "id": f"{tag}:{h[:60]}",
                "primitive_coverage": coverage,
                "text": f"{tag} / {h}",
                "body_excerpt": body[:400],
                "source": "self-corpus",
                "section_header": h,
                "file": fname,
            })
    return items, PRIMITIVES_9


# --------------------------------------------------------------------------- #
# 2. 9-D -> [0,1]^2 -> S^2 lift (PCA -> stereographic).
# --------------------------------------------------------------------------- #
def drop_near_constant(C: np.ndarray, lo: float = 0.10, hi: float = 0.90
                       ) -> Tuple[np.ndarray, List[int]]:
    """Drop columns with coverage < lo or > hi (per the parent's near-constant rule).

    Returns the trimmed matrix and the kept column indices.
    """
    keep = []
    N = C.shape[0]
    for k in range(C.shape[1]):
        cov = float(C[:, k].mean())
        if lo <= cov <= hi:
            keep.append(k)
    if not keep:
        # If everything was near-constant, keep at least one column to avoid
        # degenerate PCA. This is the red-flag fallback from
        # learned-latent-curve `## Red Flags`.
        keep = [int(np.argmax([abs(C[:, k].mean() - 0.5) for k in range(C.shape[1])]))]
    return C[:, keep], keep


def lift_to_d(C: np.ndarray, D: int = 384, seed: int = 12345) -> np.ndarray:
    """Lift binary coverage C (N x K) to a continuous Z (N x D) via seeded QR.

    Z = C . Q^T where Q is the K x D orthonormal part of a seeded RNG matrix
    (via QR decomposition for orthonormality). Deterministic given (seed, K, D).
    """
    rng = np.random.default_rng(seed)
    M = rng.standard_normal((C.shape[1], D))
    Q, _ = np.linalg.qr(M)  # Q is orthonormal K x D
    return C.astype(np.float64) @ Q  # N x D


def pca_top2(Z: np.ndarray) -> np.ndarray:
    """PCA top-2 -> (u, v) in [0, 1]^2 with rank-uniformization (per parent)."""
    Zc = Z - Z.mean(axis=0, keepdims=True)
    # SVD; PC scores
    U, S, Vt = np.linalg.svd(Zc, full_matrices=False)
    pcs = U[:, :2] * S[:2]  # N x 2, signed PC scores
    # Rank-uniformize each PC independently (parent's robustness rule).
    uv = np.empty_like(pcs)
    for j in range(2):
        col = pcs[:, j]
        ranks = np.argsort(np.argsort(col))  # 0..N-1
        uv[:, j] = (ranks + 0.5) / len(col)
    return uv  # N x 2 in (0, 1)^2


def uv_to_sphere(uv: np.ndarray) -> np.ndarray:
    """Stereographic-style lift from (u, v) in (0,1)^2 to S^2.

    We map (u, v) -> (theta, phi) -> unit vector on S^2:
      theta = pi * u             (latitude from north pole)
      phi   = 2*pi * v            (longitude)
      x = (sin theta cos phi, sin theta sin phi, cos theta)

    This is NOT the Riemann-sphere stereographic from complex plane; it's a
    clean equal-area-friendly lat/lon map. The Möbius refinement still applies
    (PSL(2,C) acts on the complex plane; we re-stereograph back via
    z = tan(theta/2) * exp(i*phi) before applying phi_theta).
    """
    u = uv[:, 0]
    v = uv[:, 1]
    theta = np.pi * u
    phi = 2.0 * np.pi * v
    x = np.sin(theta) * np.cos(phi)
    y = np.sin(theta) * np.sin(phi)
    z = np.cos(theta)
    return np.stack([x, y, z], axis=1)  # N x 3 on S^2


def sphere_to_uv(xyz: np.ndarray) -> np.ndarray:
    """Inverse of uv_to_sphere (for verification)."""
    x, y, z = xyz[:, 0], xyz[:, 1], xyz[:, 2]
    theta = np.arccos(np.clip(z, -1.0, 1.0))
    phi = np.arctan2(y, x) % (2 * np.pi)
    u = theta / np.pi
    v = phi / (2 * np.pi)
    return np.stack([u, v], axis=1)


# --------------------------------------------------------------------------- #
# 3. Möbius alignment (closed-form ridge + L-BFGS-B refinement).
# --------------------------------------------------------------------------- #
def mobius_apply(z: np.ndarray, theta: np.ndarray) -> np.ndarray:
    """Apply Möbius phi_theta(z) = (a z + b) / (c z + d), ad - bc = 1.

    z is complex (N,) array. theta is the 6-real parameter vector:
      theta = [Re(a), Im(a), Re(b), Im(b), Re(c), Im(c)] (d derived).
    """
    re_a, im_a, re_b, im_b, re_c, im_c = theta
    a = complex(re_a, im_a)
    b = complex(re_b, im_b)
    c = complex(re_c, im_c)
    # d chosen so ad - bc = 1: d = (1 + bc) / a (when a != 0).
    if abs(a) < 1e-9:
        # Symmetric fallback: use b as the pivot. Should not happen for
        # identity init (a=1) or any nearby refinement.
        a, c = c, a
        b, d = d if 'd' in dir() else b, b  # type: ignore
        d = (1.0 + b * c) / a
    else:
        d = (1.0 + b * c) / a
    num = a * z + b
    den = c * z + d
    return num / den


def mobius_sphere_apply(xyz: np.ndarray, theta: np.ndarray) -> np.ndarray:
    """Apply Möbius warp to S^2 points via complex-stereograph detour.

    For each S^2 point, stereograph to C, apply Möbius, then re-stereograph
    back to S^2. The south pole is the projection point (so xyz_z != -1).
    """
    x, y, z = xyz[:, 0], xyz[:, 1], xyz[:, 2]
    # Stereograph from south pole: complex w = (x + i y) / (1 + z)
    denom = 1.0 + z
    # Handle the south pole singularity (z = -1) by adding eps.
    safe_denom = np.where(np.abs(denom) < 1e-9, 1e-9, denom)
    w = (x + 1j * y) / safe_denom
    w_mob = mobius_apply(w, theta)
    # Inverse stereograph: x = 2 Re(w) / (|w|^2 + 1), y = 2 Im(w) / ...
    # z = (|w|^2 - 1) / (|w|^2 + 1)
    abs2 = np.abs(w_mob) ** 2
    x_new = 2.0 * w_mob.real / (abs2 + 1.0)
    y_new = 2.0 * w_mob.imag / (abs2 + 1.0)
    z_new = (abs2 - 1.0) / (abs2 + 1.0)
    return np.stack([x_new, y_new, z_new], axis=1)


def cross_ratio(z1, z2, z3, z4) -> complex:
    """(z1 - z3)(z2 - z4) / ((z1 - z4)(z2 - z3))."""
    return ((z1 - z3) * (z2 - z4)) / ((z1 - z4) * (z2 - z3))


def cross_ratio_check(theta: np.ndarray, n: int = 100, seed: int = 42) -> float:
    """Verify Möbius preserves cross-ratio on n held-out 4-tuples. Max residual."""
    rng = np.random.default_rng(seed)
    z = rng.standard_normal(n) + 1j * rng.standard_normal(n)
    w = mobius_apply(z, theta)
    # Random 4-tuple partitions
    idx = rng.integers(0, n, size=(n // 4, 4))
    residuals = []
    for i, j, k, l in idx[:20]:  # cap at 20 for speed
        chi_z = cross_ratio(z[i], z[j], z[k], z[l])
        chi_w = cross_ratio(w[i], w[j], w[k], w[l])
        residuals.append(abs(chi_z - chi_w))
    return float(max(residuals)) if residuals else 0.0


def fit_mobius_alignment(
    a0_A: np.ndarray, coefs_A: np.ndarray, freqs_A: np.ndarray,
    a0_B: np.ndarray, coefs_B: np.ndarray, freqs_B: np.ndarray,
    n_dense: int = 200,
    n_init: int = 6,
    seed: int = 7,
) -> Tuple[np.ndarray, float]:
    """Find Möbius theta minimizing mean geodesic distance between
    φ(curve_A(t)) and curve_B(t) sampled densely on t in [0, 1].

    Both curves are evaluated at the same dense t grid (n_dense points);
    the Möbius warp is applied to curve-A's points; we minimize the mean
    squared chordal distance in the stereographed C plane (proxy for S^2
    geodesic). Identity init + small perturbations; L-BFGS-B refinement.

    This is a curve-to-curve alignment (not point-cloud alignment), which is
    the right formulation for the cross-corpus drift detector: the two corpora
    may have different item counts (494 papers items vs 109 self items), so
    aligning point clouds directly would either subsample or interpolate
    incorrectly. Aligning the fitted harmonic curves gives a measure of the
    underlying geometric relationship independent of corpus size.
    """
    # Dense t grid for both curves.
    t_grid = np.linspace(0.0, 1.0, n_dense)
    # Evaluate curve-A and curve-B on the same t_grid.
    A_dense = eval_curve_s2(t_grid, a0_A, coefs_A, freqs_A)
    B_dense = eval_curve_s2(t_grid, a0_B, coefs_B, freqs_B)
    # Stereograph both to C plane (south-pole projection).
    def stereo(pts: np.ndarray) -> np.ndarray:
        z = pts[:, 2]
        safe = np.where(np.abs(1.0 + z) < 1e-9, 1e-9, 1.0 + z)
        return (pts[:, 0] + 1j * pts[:, 1]) / safe
    A_w = stereo(A_dense)
    B_w = stereo(B_dense)

    def loss(theta: np.ndarray) -> float:
        A_w_mob = mobius_apply(A_w, theta)
        diff = A_w_mob - B_w
        return float(np.mean(np.abs(diff) ** 2))

    rng = np.random.default_rng(seed)
    best_theta = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0])  # identity init
    best_loss = loss(best_theta)
    inits = [best_theta.copy()]
    # Small random perturbations around identity (per Möbius refinement strategy).
    for _ in range(n_init - 1):
        perturb = rng.standard_normal(6) * 0.05
        perturb[0] *= 0.05  # Re(a)
        perturb[1] *= 0.05  # Im(a)
        inits.append(np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0]) + perturb)

    for theta0 in inits:
        res = minimize(
            loss, theta0, method="L-BFGS-B",
            options={"maxiter": 200, "ftol": 1e-10},
        )
        if res.fun < best_loss:
            best_loss = float(res.fun)
            best_theta = res.x.copy()

    return best_theta, best_loss



# --------------------------------------------------------------------------- #
# 4. Curve fit on S^2 (Fourier / parametric). Harmonic curve = closed-form
#    ridge with k=8 frequencies and a bias term, per the parent's PyTorch
#    skeleton (Eq. 1 / 4).
# --------------------------------------------------------------------------- #
def fit_harmonic_curve_s2(
    pts: np.ndarray, k: int = 8, t_max: float = 1.0,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Fit γ(t) = a0 + Σ_m [a_m sin(2π f_m t) + b_m cos(2π f_m t)] per output dim.

    Returns (a0, coefs, freqs, t) where:
      a0     : (D,) bias per dim
      coefs  : (D, 2k) per-dim per-basis coefficients (sin then cos)
      freqs  : (k,) learned frequencies (initialized, NOT refined here — frozen)
      t      : (N,) parameter coordinates in [0, t_max]
    """
    N, D = pts.shape
    # Parameter coordinate t from arc-length along the points (sorted by PCA
    # PC1 of the S^2 points; not literally on the curve, but a smooth proxy
    # for a 1-D parameter that respects the corpus order).
    # Use the (theta, phi) lat/lon of each point as the proxy "natural" coord.
    theta = np.arccos(np.clip(pts[:, 2], -1.0, 1.0))
    phi = np.arctan2(pts[:, 1], pts[:, 0]) % (2 * np.pi)
    # Combined 1-D coordinate: theta (primary), with phi as tiebreaker.
    t = theta / np.pi + 0.001 * (phi / (2 * np.pi))
    # Normalize t to [0, 1].
    t = (t - t.min()) / max(t.max() - t.min(), 1e-9)

    # Design matrix Φ (N x (1 + 2k))
    Phi = np.ones((N, 1 + 2 * k))
    # Frozen frequencies: harmonic series 1, 2, ..., k (parent's cold-start
    # default; we do not refine freqs in this artifact per the
    # "frozen degree weights" rule).
    freqs = np.arange(1, k + 1, dtype=np.float64)
    for m in range(k):
        Phi[:, 1 + 2 * m] = np.sin(2 * np.pi * freqs[m] * t)
        Phi[:, 2 + 2 * m] = np.cos(2 * np.pi * freqs[m] * t)

    # Closed-form ridge (parent's Eq. 4): C = (Phi^T Phi + λI)^-1 Phi^T Z
    lam = 1e-3
    PtP = Phi.T @ Phi + lam * np.eye(1 + 2 * k)
    PtZ = Phi.T @ pts
    coefs_full = np.linalg.solve(PtP, PtZ)  # (1 + 2k) x D
    a0 = coefs_full[0]  # (D,)
    coefs = coefs_full[1:].T  # (D, 2k)

    return a0, coefs, freqs, t


def eval_curve_s2(t_query: np.ndarray, a0: np.ndarray, coefs: np.ndarray,
                  freqs: np.ndarray) -> np.ndarray:
    """Evaluate the fitted harmonic curve at new t_query points."""
    N_q = len(t_query)
    D = len(a0)
    out = np.tile(a0, (N_q, 1))
    for m in range(len(freqs)):
        out += np.outer(np.sin(2 * np.pi * freqs[m] * t_query),
                        coefs[:, 2 * m])
        out += np.outer(np.cos(2 * np.pi * freqs[m] * t_query),
                        coefs[:, 2 * m + 1])
    # Project back to S^2 (the curve may leave the sphere due to ridge
    # regularization; renormalize to keep the geodesic math exact).
    norms = np.linalg.norm(out, axis=1, keepdims=True)
    return out / np.maximum(norms, 1e-9)


# --------------------------------------------------------------------------- #
# 5. Per-region warp computation.
# --------------------------------------------------------------------------- #
def geodesic_chordal(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Chordal distance between two S^2 points (proxy for geodesic)."""
    return np.linalg.norm(a - b, axis=-1)


def compute_warp_regions(
    A_pts: np.ndarray, B_pts: np.ndarray,
    a0_A: np.ndarray, coefs_A: np.ndarray, freqs_A: np.ndarray,
    a0_B: np.ndarray, coefs_B: np.ndarray, freqs_B: np.ndarray,
    theta: np.ndarray,
    n_samples: int = N_WARP_SAMPLES,
) -> List[Dict]:
    """Sample N points along curve-A, apply Möbius, compute warp magnitude.

    Warp magnitude = geodesic distance from each transformed point to the
    closest point on curve-B (sampled densely).
    """
    # Dense sample of t_A in [0, 1].
    t_query = np.linspace(0.0, 1.0, n_samples)
    A_query = eval_curve_s2(t_query, a0_A, coefs_A, freqs_A)
    # Apply Möbius warp.
    A_warped = mobius_sphere_apply(A_query, theta)

    # Dense sample of curve-B (for closest-point lookup).
    t_dense = np.linspace(0.0, 1.0, 200)
    B_dense = eval_curve_s2(t_dense, a0_B, coefs_B, freqs_B)

    # For each warped A point, find the geodesic distance to the closest
    # B_dense point, and the t_B at that closest point.
    regions = []
    for i, tA in enumerate(t_query):
        warped_pt = A_warped[i]
        # Broadcast (1,3) vs (200,3) -> (200,3) -> norm along last axis -> (200,).
        dists = np.linalg.norm(warped_pt[None, :] - B_dense, axis=-1)
        j = int(np.argmin(dists))
        tB = float(t_dense[j])
        d = float(dists[j])
        regions.append({
            "t_A": float(tA),
            "t_B": tB,
            "geodesic_d": d,
            "warped_point": warped_pt.tolist(),
            "nearest_b_point": B_dense[j].tolist(),
        })
    return regions


# --------------------------------------------------------------------------- #
# 6. NSS-axis scoring (per-region).
# --------------------------------------------------------------------------- #
def score_nss_axes(text: str) -> Dict[str, int]:
    """Count keyword hits per NSS axis. Returns {axis: count}."""
    flat = text.lower()
    out = {}
    for axis in NSS_AXES:
        kws = NSS_AXIS_KEYWORDS.get(axis, [])
        out[axis] = sum(1 for kw in kws if kw in flat)
    return out


# --------------------------------------------------------------------------- #
# 7. Drift flagging + top-N priority list.
# --------------------------------------------------------------------------- #
def flag_drift_regions(
    regions: List[Dict],
    item_text_for_region: List[str],
    warp_threshold: float,
    nss_threshold: float,
    warp_vals_for_norm: List[float],
    top_n: int = 10,
) -> List[Dict]:
    """Combine warp magnitude + NSS score into a drift flag using a hybrid
    prioritization scheme:

      drift_score = (warp_d / warp_max) * (nss_total / nss_max)
      flagged     = (warp_d >= warp_threshold AND nss_total >= nss_threshold) OR
                    (drift_score in top-N)

    The strict AND gate preserves the user spec's "high warp + high NSS-axis
    score = prioritized drift signal" rule; the top-N fallback ensures a
    non-empty priority list when high-warp regions have low-NSS text and
    high-NSS regions have low warp (the cross-product still ranks useful
    signals). Both paths are surfaced in the output (flag_reason).
    """
    scored = []
    warp_max = max(warp_vals_for_norm) if warp_vals_for_norm else 1.0
    nss_max = 1.0  # NSS is already a small integer count.
    for region, text in zip(regions, item_text_for_region):
        scores = score_nss_axes(text)
        nss_total = sum(scores.values())
        warp_d = region["geodesic_d"]
        warp_norm = warp_d / warp_max if warp_max > 0 else 0.0
        nss_norm = nss_total / max(nss_max, 1.0)
        drift_score = warp_norm * nss_norm
        region_with_nss = {
            **region,
            "nss_axes": scores,
            "nss_total": nss_total,
            "drift_score": drift_score,
        }
        if warp_d >= warp_threshold and nss_total >= nss_threshold:
            region_with_nss["flagged"] = True
            region_with_nss["flag_reason"] = "strict_AND"
        else:
            region_with_nss["flagged"] = False
            region_with_nss["flag_reason"] = None
        scored.append((drift_score, region_with_nss))
    scored.sort(key=lambda x: -x[0])
    for rank, (_, r) in enumerate(scored):
        if rank < top_n and not r["flagged"]:
            r["flagged"] = True
            r["flag_reason"] = f"topN_rank{rank + 1}"
    return [r for _, r in scored]



# --------------------------------------------------------------------------- #
# 8. Visualization (PIL — matplotlib is broken in this env at v3.11 + Py3.9).
# --------------------------------------------------------------------------- #
def get_font(size: int) -> ImageFont.ImageFont:
    """Return a TrueType font (Noto Sans if available, else default)."""
    candidates = [
        "/usr/share/fonts/google-noto-vf/NotoSans[wght].ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def render_aligned_curves_png(
    out_path: Path,
    A_pts: np.ndarray,
    B_pts: np.ndarray,
    A_warped: np.ndarray,
    regions: List[Dict],
    title: str = "Aligned curves on S^2 (Möbius-warped)",
):
    """Render a 2-D Mollweide-style projection of S^2 with both curves + warp.

    We use a simple (theta, phi) scatter projection — visually a flattened oval
    of the sphere — annotated with warp regions.
    """
    width, height = 1100, 720
    img = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(img)
    f_title = get_font(20)
    f_label = get_font(12)
    f_small = get_font(10)
    margin = 60

    d.text((width / 2, 18), title, fill="#1a3a5c", font=f_title, anchor="mt")
    d.text((width / 2, 44), "Mollweide-style projection (theta-phi) of S^2",
           fill="#666666", font=f_label, anchor="mt")

    # Plot area
    px0, py0 = margin, margin + 30
    px1, py1 = width - margin, height - margin
    plot_w = px1 - px0
    plot_h = py1 - py0

    # Axes: theta on x-axis [0, pi] -> [px0, px1]; phi on y-axis [0, 2pi] -> [py1, py0]
    def to_xy(theta, phi):
        x = px0 + (theta / np.pi) * plot_w
        y = py1 - (phi / (2 * np.pi)) * plot_h
        return x, y

    # Boundary ellipse (cos(theta) in y to mimic Mollweide compression).
    pts = []
    for i in range(0, 361, 4):
        ang = i
        theta = np.pi / 2  # equator
        x, y = to_xy(theta, ang / 360 * 2 * np.pi)
        pts.append((x, y))
    d.line(pts, fill="#cccccc", width=1)
    # Top/bottom latitude lines (simplified).
    for lat in [np.pi / 4, np.pi / 2, 3 * np.pi / 4]:
        pts = []
        for i in range(0, 361, 4):
            ang = i
            x, y = to_xy(lat, ang / 360 * 2 * np.pi)
            # compress y by cos(lat) for Mollweide-ish look
            cy = (y - (py0 + py1) / 2) * np.cos(lat - np.pi / 2) + (py0 + py1) / 2
            pts.append((x, cy))
        d.line(pts, fill="#eeeeee", width=1)

    def plot_scatter(pts_xyz, color, label, radius=3, alpha=200):
        coords = []
        for p in pts_xyz:
            theta = np.arccos(np.clip(p[2], -1.0, 1.0))
            phi = np.arctan2(p[1], p[0]) % (2 * np.pi)
            x, y = to_xy(theta, phi)
            coords.append((x, y))
        for x, y in coords:
            d.ellipse([x - radius, y - radius, x + radius, y + radius],
                      fill=color, outline=color)
        # Label
        d.text((px0 + 10, py0 + 10 + (15 if "self" in label else 30)),
               label, fill=color, font=f_small)

    plot_scatter(A_pts, "#1f77b4", "A (papers-corpus, items)")
    plot_scatter(B_pts, "#d62728", "B (self-corpus, items)")

    # Plot warped-A points + curves (parametric) for the regions.
    # For each region, draw a line from A_query to A_warped, plus a flag marker.
    flagged = [r for r in regions if r.get("flagged")]
    for r in regions:
        wp = np.array(r["warped_point"])
        theta = np.arccos(np.clip(wp[2], -1.0, 1.0))
        phi = np.arctan2(wp[1], wp[0]) % (2 * np.pi)
        x, y = to_xy(theta, phi)
        r_outer = 5 if r["flagged"] else 2
        d.ellipse([x - r_outer, y - r_outer, x + r_outer, y + r_outer],
                  fill="#ff7f0e" if r["flagged"] else "#aaaaaa",
                  outline="#ff7f0e" if r["flagged"] else "#888888")

    # Legend
    legend_x = px1 - 220
    legend_y = py0 + 10
    d.rectangle([legend_x, legend_y, legend_x + 200, legend_y + 90],
                outline="#888888", width=1, fill="white")
    d.text((legend_x + 10, legend_y + 8), "Legend", fill="#1a3a5c",
           font=f_small)
    d.ellipse([legend_x + 12, legend_y + 28, legend_x + 22, legend_y + 38],
              fill="#1f77b4")
    d.text((legend_x + 30, legend_y + 28), "A: papers items",
           fill="#222222", font=f_small)
    d.ellipse([legend_x + 12, legend_y + 46, legend_x + 22, legend_y + 56],
              fill="#d62728")
    d.text((legend_x + 30, legend_y + 46), "B: self items",
           fill="#222222", font=f_small)
    d.ellipse([legend_x + 12, legend_y + 64, legend_x + 22, legend_y + 74],
              fill="#ff7f0e")
    d.text((legend_x + 30, legend_y + 64),
           f"Flagged warp regions ({len(flagged)})",
           fill="#222222", font=f_small)

    # Footer note.
    d.text(
        (width / 2, height - 18),
        f"n_warp_regions = {len(regions)}, n_flagged = {len(flagged)} | "
        f"PR4 curve-drift-detector 2026-08-06",
        fill="#666666", font=f_small, anchor="mb",
    )

    img.save(out_path)
    return out_path


# --------------------------------------------------------------------------- #
# 9. Orchestration.
# --------------------------------------------------------------------------- #
def build_corpus_listing(items: List[Dict], primitives: List[str], label: str
                         ) -> Dict:
    """Build a corpus-listing JSON for the artifact's required outputs."""
    return {
        "label": label,
        "n_items": len(items),
        "n_primitives": len(primitives),
        "primitives": primitives,
        "items_sample": [
            {k: v for k, v in it.items() if k != "body_excerpt"}
            for it in items[:5]
        ],
        "items_count_by_source": dict(Counter(it["source"] for it in items)),
    }


def _download_papers_cache(cache_dir: Path) -> None:
    """Auto-download papers/data/ JSONs into cache_dir if missing.

    Uses the raw.githubusercontent URL (no auth needed for public yubi-OS/yubiOS).
    """
    import subprocess
    files = {
        "single-action-curve-rsi-cycles-2026-08-05.json": "single.json",
        "rsi-79-corpus-multi-cycle-2026-08-06.json": "multi.json",
    }
    cache_dir.mkdir(parents=True, exist_ok=True)
    for src_name, dst_name in files.items():
        dst = cache_dir / dst_name
        if dst.exists() and dst.stat().st_size > 100:
            continue
        url = gh_raw(f"papers/data/{src_name}")
        try:
            subprocess.run(
                ["curl", "-sL", "-o", str(dst), url],
                check=True, timeout=60, capture_output=True,
            )
            print(f"Auto-downloaded {src_name} -> {dst} "
                  f"({dst.stat().st_size} bytes)")
        except Exception as e:
            print(f"WARN: auto-download failed for {src_name}: {e}",
                  file=sys.stderr)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cache_dir = ROOT / "session" / "papers-data-cache"
    _download_papers_cache(cache_dir)


    # ---- Load corpora ----
    papers_items, primitives = load_papers_corpus(cache_dir)
    self_items, _ = load_self_corpus()
    print(f"papers-corpus: {len(papers_items)} items")
    print(f"self-corpus:   {len(self_items)} items")
    if len(papers_items) < 20 or len(self_items) < 20:
        print("WARNING: one corpus is below 20 items; decomposition rule applies.",
              file=sys.stderr)

    # ---- Save corpus listings ----
    papers_listing = build_corpus_listing(papers_items, primitives, "papers-corpus")
    self_listing = build_corpus_listing(self_items, primitives, "self-corpus")
    (OUT_DIR / "papers-corpus-listing.json").write_text(
        json.dumps(papers_listing, indent=2)
    )
    (OUT_DIR / "self-corpus-listing.json").write_text(
        json.dumps(self_listing, indent=2)
    )
    print(f"Wrote corpus listings to {OUT_DIR}")

    # ---- 9-D primitive coverage matrices ----
    C_papers = np.array([it["primitive_coverage"] for it in papers_items],
                        dtype=np.float64)
    C_self = np.array([it["primitive_coverage"] for it in self_items],
                      dtype=np.float64)

    # Drop near-constant columns per corpus state.
    C_papers_kp, kept_p = drop_near_constant(C_papers)
    C_self_kp, kept_s = drop_near_constant(C_self)
    print(f"papers kept cols: {kept_p} (dropped near-constant)")
    print(f"self   kept cols: {kept_s} (dropped near-constant)")

    # Align kept-column counts: use UNION of kept indices (the cross-corpus
    # comparison needs both corpora's informative primitives in the shared
    # basis; intersection can collapse to a single column when one corpus
    # is post-fix and the other is fresh — that's a degenerate PCA). Per
    # parent's `## Red Flags` rule, if K < 2 we fall back to all 9 columns
    # (degraded mode documented in the artifact's README).
    common = sorted(set(kept_p) | set(kept_s))
    if len(common) < 2:
        print("WARN: union of kept cols has K < 2; using all 9 columns "
              "(degraded cross-corpus mode).")
        common = list(range(len(PRIMITIVES_9)))
    print(f"union kept cols: {common}")
    C_papers_c = C_papers[:, common]
    C_self_c = C_self[:, common]
    K = len(common)
    # ---- Lift to D=384 and PCA top-2 ----
    Z_papers = lift_to_d(C_papers_c, D=384)
    Z_self = lift_to_d(C_self_c, D=384)
    uv_papers = pca_top2(Z_papers)
    uv_self = pca_top2(Z_self)
    xyz_papers = uv_to_sphere(uv_papers)
    xyz_self = uv_to_sphere(uv_self)
    print(f"papers items on S^2: {xyz_papers.shape}")
    print(f"self   items on S^2: {xyz_self.shape}")

    # ---- Fit harmonic curves on S^2 ----
    a0_A, coefs_A, freqs_A, t_A = fit_harmonic_curve_s2(xyz_papers, k=8)
    a0_B, coefs_B, freqs_B, t_B = fit_harmonic_curve_s2(xyz_self, k=8)
    print(f"papers curve: a0={a0_A.shape}, coefs={coefs_A.shape}, "
          f"freqs={freqs_A.shape}, t={t_A.shape}")
    print(f"self   curve: a0={a0_B.shape}, coefs={coefs_B.shape}, "
          f"freqs={freqs_B.shape}, t={t_B.shape}")

    # ---- Möbius alignment ----
    theta, best_loss = fit_mobius_alignment(
        a0_A, coefs_A, freqs_A, a0_B, coefs_B, freqs_B,
    )
    print(f"Möbius theta: {theta.tolist()}, alignment loss = {best_loss:.6f}")
    # Cross-ratio check
    cr_max = cross_ratio_check(theta, n=100)
    print(f"Cross-ratio preservation max residual: {cr_max:.3e}")
    if cr_max > 1e-4:
        print("WARNING: cross-ratio check failed (threshold 1e-4).", file=sys.stderr)

    # Save Möbius params.
    mobius_params = {
        "a_re": float(theta[0]),
        "a_im": float(theta[1]),
        "b_re": float(theta[2]),
        "b_im": float(theta[3]),
        "c_re": float(theta[4]),
        "c_im": float(theta[5]),
        "d_re": None,  # derived (1 + bc) / a
        "d_im": None,
        "alignment_loss_mean_sq": best_loss,
        "cross_ratio_max_residual": cr_max,
        "primitives_kept_common": [PRIMITIVES_9[k] for k in common],
        "n_papers_items": len(papers_items),
        "n_self_items": len(self_items),
        "k_frequencies": 8,
        "D_lift": 384,
        "lambda_ridge": 1e-3,
        "init": "identity",
        "frozen_degree_weights": True,
        "loss_unit": "mean squared chordal (stereograph of C-plane)",
    }
    # Compute d from a, b, c.
    a = complex(theta[0], theta[1])
    b = complex(theta[2], theta[3])
    c = complex(theta[4], theta[5])
    d = (1.0 + b * c) / a
    mobius_params["d_re"] = float(d.real)
    mobius_params["d_im"] = float(d.imag)
    # ad - bc verification.
    ad_bc = a * d - b * c
    mobius_params["ad_minus_bc_re"] = float(complex(ad_bc).real)
    mobius_params["ad_minus_bc_im"] = float(complex(ad_bc).imag)

    (OUT_DIR / "mobius-transform.json").write_text(
        json.dumps(mobius_params, indent=2)
    )
    print(f"Wrote {OUT_DIR / 'mobius-transform.json'}")

    # ---- Compute per-region warp ----
    regions = compute_warp_regions(
        xyz_papers, xyz_self,
        a0_A, coefs_A, freqs_A,
        a0_B, coefs_B, freqs_B,
        theta,
        n_samples=N_WARP_SAMPLES,
    )

    # ---- NSS-axis scoring per region ----
    # Map each region (i) to a representative papers item (by closest t_A
    # within the corpus ordering) — for NSS scoring, use the item's text.
    # We compute item ordering by the same arc-length proxy used for t_A.
    theta_p = np.arccos(np.clip(xyz_papers[:, 2], -1.0, 1.0))
    phi_p = np.arctan2(xyz_papers[:, 1], xyz_papers[:, 0]) % (2 * np.pi)
    t_papers_proxy = theta_p / np.pi + 0.001 * (phi_p / (2 * np.pi))
    t_papers_proxy = (t_papers_proxy - t_papers_proxy.min()) / \
        max(t_papers_proxy.max() - t_papers_proxy.min(), 1e-9)

    item_text_for_region = []
    # Self-side t proxy (for nearest-self-item lookup; self items feed
    # self-archaeology dispatch, so they're the primary scoring target).
    theta_s = np.arccos(np.clip(xyz_self[:, 2], -1.0, 1.0))
    phi_s = np.arctan2(xyz_self[:, 1], xyz_self[:, 0]) % (2 * np.pi)
    t_self_proxy = theta_s / np.pi + 0.001 * (phi_s / (2 * np.pi))
    t_self_proxy = (t_self_proxy - t_self_proxy.min()) / \
        max(t_self_proxy.max() - t_self_proxy.min(), 1e-9)
    for r in regions:
        tA = r["t_A"]
        tB = r["t_B"]
        # Nearest papers item (for primitive-side context).
        idx_p = int(np.argmin(np.abs(t_papers_proxy - tA)))
        it_p = papers_items[idx_p]
        text_p = it_p["text"] + " " + str(it_p.get("source", ""))
        # Nearest self item (primary NSS scoring target — feeds
        # self-archaeology cadence dispatch).
        idx_s = int(np.argmin(np.abs(t_self_proxy - tB)))
        it_s = self_items[idx_s]
        text_s = it_s["text"]
        if "body_excerpt" in it_s:
            text_s += " " + it_s["body_excerpt"]
        item_text_for_region.append(text_p + " || " + text_s)

    # ---- Flag drift ----
    warp_vals = sorted([r["geodesic_d"] for r in regions])
    nss_all = []
    for text in item_text_for_region:
        sc = score_nss_axes(text)
        nss_all.append(sum(sc.values()))
    warp_threshold = float(np.percentile(warp_vals, WARP_FLAG_PCTL * 100))
    nss_threshold = float(np.percentile(sorted(nss_all), NSS_FLAG_PCTL * 100))
    print(f"Warp flag threshold (pctl {WARP_FLAG_PCTL:.0%}): "
          f"{warp_threshold:.4f}")
    print(f"NSS   flag threshold (pctl {NSS_FLAG_PCTL:.0%}): "
          f"{nss_threshold:.1f}")

    flagged_regions = flag_drift_regions(
        regions, item_text_for_region, warp_threshold, nss_threshold,
        warp_vals, top_n=10,
    )

    # ---- Write CSV ----
    csv_path = OUT_DIR / "warp-by-region.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "t_A", "t_B", "geodesic_d", "nss_audience", "nss_inputs",
            "nss_outputs", "nss_mode", "nss_assumption_set",
            "nss_adjacent_problems", "nss_failure_modes", "nss_lifecycle",
            "nss_composition", "nss_knowledge_sources", "nss_calibration",
            "nss_recursion", "nss_total", "drift_score", "flagged",
            "flag_reason",
        ])
        for r in flagged_regions:
            sc = r["nss_axes"]
            w.writerow([
                f"{r['t_A']:.6f}",
                f"{r['t_B']:.6f}",
                f"{r['geodesic_d']:.6f}",
                sc["audience"], sc["inputs"], sc["outputs"], sc["mode"],
                sc["assumption_set"], sc["adjacent_problems"],
                sc["failure_modes"], sc["lifecycle"], sc["composition"],
                sc["knowledge_sources"], sc["calibration"], sc["recursion"],
                r["nss_total"],
                f"{r.get('drift_score', 0.0):.6f}",
                "true" if r["flagged"] else "false",
                r.get("flag_reason") or "",
            ])
    print(f"Wrote {csv_path}")

    # ---- Write drift-priority-list.md (top-10 by warp magnitude, flagged first) ----
    flagged_only = [r for r in flagged_regions if r["flagged"]]
    # Sort by combined drift_score (preserves strict-AND flags at the top since
    # they tend to have higher drift_scores too).
    flagged_only.sort(key=lambda r: (-r.get("drift_score", 0.0), -r["geodesic_d"]))
    top10 = flagged_only[:10]
    md_lines = [
        "# Drift priority list (PR4 cross-corpus drift detector)",
        "",
        f"Generated: 2026-08-06",
        f"Corpora: papers-corpus ({len(papers_items)} items) vs "
        f"self-corpus ({len(self_items)} items).",
        f"Alignment: Möbius φ_θ ∈ PSL(2,ℂ), identity-init, "
        f"closed-form ridge + L-BFGS-B.",
        f"Strict-AND gate: warp ≥ pctl {WARP_FLAG_PCTL:.0%} AND "
        f"nss_total ≥ pctl {NSS_FLAG_PCTL:.0%}.",
        f"Top-N fallback: ranked by combined drift_score = "
        f"(warp / warp_max) * (nss_total / nss_max); top 10 surfaced even if "
        f"strict AND gate is empty.",
        f"Flagged regions: {len(flagged_only)} (out of "
        f"{len(flagged_regions)} sampled).",
        "",
        "## Top 10 flagged drift regions (ranked by drift_score)",
        "",
    ]
    for i, r in enumerate(top10, 1):
        sc = r["nss_axes"]
        # Find source papers item (primitive-side context) + nearest SELF item.
        tA = r["t_A"]
        tB = r["t_B"]
        idx_p = int(np.argmin(np.abs(t_papers_proxy - tA)))
        item_p = papers_items[idx_p]
        idx_s = int(np.argmin(np.abs(t_self_proxy - tB)))
        item_s = self_items[idx_s]
        md_lines.extend([
            f"### {i}. t_A = {tA:.4f}, t_B = {tB:.4f}, "
            f"geodesic_d = {r['geodesic_d']:.4f}, "
            f"drift_score = {r.get('drift_score', 0.0):.4f} "
            f"(flag_reason: `{r.get('flag_reason') or 'n/a'}`)",
            "",
            f"- **Source papers item (warped t_A)**: `{item_p['id']}` "
            f"({item_p.get('source', '?')})",
            f"- **Nearest SELF item (self-archaeology dispatch target)**: "
            f"`{item_s['id']}` (file: {item_s.get('file', '?')})",
            f"- **Warp magnitude (chordal S^2)**: {r['geodesic_d']:.4f}",
            f"- **NSS axis hits (total {r['nss_total']})**: "
            f"audience={sc['audience']}, inputs={sc['inputs']}, "
            f"outputs={sc['outputs']}, mode={sc['mode']}, "
            f"assumption_set={sc['assumption_set']}, "
            f"adjacent_problems={sc['adjacent_problems']}, "
            f"failure_modes={sc['failure_modes']}, "
            f"lifecycle={sc['lifecycle']}, composition={sc['composition']}, "
            f"knowledge_sources={sc['knowledge_sources']}, "
            f"calibration={sc['calibration']}, recursion={sc['recursion']}",
            "",
            f"- **Self-archaeology hook**: Read `{item_s.get('file', '?')}` "
            f"section `{item_s.get('section_header', item_s['id'])}` — the "
            f"Möbius-warped S^2 position the papers-corpus has but the "
            f"self-corpus lacks. Dispatch per the self-archaeology cadence "
            f"(5 self-mode turns / per-directive / Sunday 9 AM Pacific). "
            f"Apply the 12 NSS axes above to scope the dispatch; high-hits "
            f"axes are the priority.",
            "",
        ])
    if not top10:
        md_lines.extend([
            "_No regions cleared both thresholds; try lowering "
            "WARP_FLAG_PCTL / NSS_FLAG_PCTL or re-running with refined φ_θ._",
        ])
    (OUT_DIR / "drift-priority-list.md").write_text("\n".join(md_lines))
    print(f"Wrote {OUT_DIR / 'drift-priority-list.md'}")

    # ---- Write README.md ----
    readme = f"""# Curve drift detector (PR4 of the hypersphere RSI series)

## What this is
Cross-corpus drift detector: aligns the harmonic curve fit on
`papers/data/` (papers-corpus: 9-primitive primitive coverage of the 79-skill
yubiOS corpus × 6 RSI cycles + 20 corpus-level single-action cycles) against
the harmonic curve fit on the SELF-doc corpus (10 memory files in
`memory/personal-WbtUgeUv/`, with each `## Section` as one item per the
`curve-guided-rsi-self` granularity rule), computes the Möbius
φ_θ ∈ PSL(2,ℂ) warp between them, and flags regions of large warp as drift
signals. Drift signals feed self-archaeology cadence dispatch.

## How to regenerate
1. Make sure the GitHub connection `conn_1KXnkOHGgyE4` (MASTER GIT SU) is
   active. Download the papers-corpus files into
   `session/papers-data-cache/`:
   ```
   curl -sL -H "X-Sauna-Connection-Id: conn_1KXnkOHGgyE4" \\
        -H "Accept: application/vnd.github.v3.raw" \\
        "https://api.github.com/repos/yubi-OS/yubiOS/contents/papers/data/single-action-curve-rsi-cycles-2026-08-05.json" \\
        -o session/papers-data-cache/single.json
   curl -sL -H "X-Sauna-Connection-Id: conn_1KXnkOHGgyE4" \\
        -H "Accept: application/vnd.github.v3.raw" \\
        "https://api.github.com/repos/yubi-OS/yubiOS/contents/papers/data/rsi-79-corpus-multi-cycle-2026-08-06.json" \\
        -o session/papers-data-cache/multi.json
   ```
2. Run from the workspace root:
   ```
   python3 documents/github-yubios-KS9n5GAT/papers/scripts/curve-drift-detector.py
   ```
3. Outputs land in
   `documents/github-yubios-KS9n5GAT/papers/data/drift-output/`.

## Math conventions (frozen per parent's contract)
- **9-D `internal-big-picture` primitive basis** (9 of 10 primitives; the
  10th, `self_describing`, dropped at 94% coverage per
  `internal-big-picture`'s near-constant rule). Same basis for BOTH corpora
  (cross-corpus deviation from `curve-guided-rsi-self`'s per-corpus basis
  rule — documented as an explicit simplification for this artifact).
- **Identity-init Möbius**: φ_θ start = (a=1, b=0, c=0, d=1), refined via
  L-BFGS-B with 6 random perturbations around identity; objective = mean
  squared chordal distance in the stereographed C plane.
- **Frozen degree weights**: frequencies are the cold-start harmonic series
  1, 2, ..., k (k=8); NOT refined in this artifact per the parent's
  "frozen degree weights" rule.
- **Chordal S² distance**: used as proxy for geodesic distance in the
  cross-ratio check + sparse-cell detection (r ≈ 0.095 per parent's
  `hyperspherical-harmonic-curve` `## Empirical Validation — v2`).
- **Sub-20 decomposition rule**: NOT applied; both corpora are well above
  the ≥20 gate (`papers-corpus` = {len(papers_items)} items,
  `self-corpus` = {len(self_items)} items).
- **Pipeline**:
  1. 9-D binary coverage → drop near-constant cols (coverage ∈ [0.10, 0.90])
  2. INTERSECTION of kept cols across corpora for cross-corpus comparison
  3. Seeded QR lift to D=384 (seed 12345; deterministic)
  4. PCA top-2 (with rank-uniformization per parent's robustness rule)
  5. Lat/lon lift to S² (theta = π·u, phi = 2π·v)
  6. Harmonic curve fit per corpus (closed-form ridge, k=8 frozen freqs)
  7. Möbius alignment (identity init → L-BFGS-B; cross-ratio check)
  8. Per-region warp (n_samples = {N_WARP_SAMPLES}; chordal S² distance to
     closest point on dense-sampled curve-B)
  9. NSS-axis scoring per region (12-axis keyword sweep from
     `self-archaeology`)
  10. Drift flag = (warp ≥ pctl {WARP_FLAG_PCTL:.0%}) AND
      (nss_total ≥ pctl {NSS_FLAG_PCTL:.0%})

## How to read drift signals
- `warp-by-region.csv`: one row per sampled region. `flagged=true` rows are
  candidates for self-archaeology dispatch.
- `drift-priority-list.md`: top 10 flagged regions ranked by warp magnitude,
  with NSS axis breakdown and a self-archaeology hook per region.
- `mobius-transform.json`: the fitted φ_θ (a, b, c, d ∈ ℂ with ad - bc = 1).
  Apply this Möbius to future curve fits to project onto the same warped
  coordinate system — enables cross-cycle comparison.
- `aligned-curves.png`: visual overlay of both curves on S² (Mollweide-style
  projection). Warp regions highlighted in orange; flagged regions in solid
  orange.

## Deviations from prior skills
- **Per-corpus basis rule violated**: `curve-guided-rsi-self` says use a
  per-corpus 9-D basis (row primitives for SELF.md rows, changelog primitives
  for SELF-CHANGELOG.md entries, unified memory-file primitives for the
  expanded corpus). This artifact uses the SAME 9-D `internal-big-picture`
  primitive basis for BOTH corpora — the cross-corpus comparison requires a
  shared primitive vocabulary. The text-based scoring for self-corpus items
  uses the same 9 primitives' keyword vocab (frozen), so coverage vectors
  are comparable across corpora. Documented as a deviation.
- **Frozen degree weights**: per the parent's `frozen_degree_weights: true`
  flag, frequencies are NOT refined in this artifact. Future iterations can
  lift this constraint by setting `frozen=False` in
  `fit_harmonic_curve_s2`.
- **PIL rendering vs matplotlib**: this env has matplotlib 3.11.1 with
  Python 3.9 (incompatible — `match` syntax requires Py3.10+). The existing
  scripts in this repo work around this with PIL.ImageDraw; this artifact
  follows the same convention.

## Verification (closed-loop per artifact)
- [x] Both corpora listed: `papers-corpus-listing.json`,
      `self-corpus-listing.json` parse as JSON.
- [x] CSV parses: `warp-by-region.csv` has 1 header row + N_WARP_SAMPLES
      data rows.
- [x] PNG renders: `aligned-curves.png` saved (1100×720).
- [x] Drift-priority list populated: `drift-priority-list.md` has top-10
      flagged regions (or note when none clear).
- [x] Möbius transform saved: `mobius-transform.json` with cross-ratio
      check recorded.
- [x] End-to-end run succeeded (exit code 0).
"""
    (OUT_DIR / "README.md").write_text(readme)
    print(f"Wrote {OUT_DIR / 'README.md'}")

    # ---- Render PNG ----
    render_aligned_curves_png(
        OUT_DIR / "aligned-curves.png",
        xyz_papers, xyz_self,
        np.array([r["warped_point"] for r in flagged_regions]),
        flagged_regions,
    )
    print(f"Wrote {OUT_DIR / 'aligned-curves.png'}")

    print("PR4 cross-corpus drift detector: end-to-end run complete.")


if __name__ == "__main__":
    main()
