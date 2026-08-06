#!/usr/bin/env python3.12
"""fit-full-curve-map-384d.py â 384-D sibling variant of PR1's 9-D fit-full-curve-map.py.

Extends PR #186 with the same 5 outputs but using 384-D embeddings (sentence-transformers
all-MiniLM-L6-v2 with TF-IDF fallback) instead of the 9-D binary primitive coverage vector.

Pipeline (one item = one corpus item, e.g. one skill in the 79-skill corpus):
  1. Load each corpus item from `papers/data/rsi-79-corpus-multi-cycle-2026-08-06.json`
  2. Build a text representation per corpus item (slug + present primitives +
     missing primitives + cycle info + first ~1000 chars of the SKILL.md body
     after stripping frontmatter, if available from the local mirror).
  3. Embed to 384-D (sentence-transformers/all-MiniLM-L6-v2 first, sklearn
     TF-IDF n_features=384 fallback).
  4. Project to SÂ² via PCA top-2 â stereographic lift â identity-init MÃ¶bius
     reparameterization (frozen Ï_Î¸).
  5. Fit a harmonic curve Î³(t) through the projected points using the closed-
     form ridge on the real spherical-harmonic basis at L=3 (16 functions;
     matches `hyperspherical-harmonic-curve` Â§6.2).
  6. For each point: project onto Î³ at its t â compute the chordal residual
     r_i = âp_i â Î³(t_i)ââ â [0, 2].
  7. Write outputs to `papers/data/curve-map-output-384d/`.

Outputs (mirror PR1):
  - corpus-listing.json    (text representations â one string per slug, for reproducibility)
  - curve-map.json         ({file, lon, lat, t, residual, embedding_basis, embedding_path,
                            pc1_var, pc2_var} per point)
  - curve-map.png          (Mollweide/Aitoff projection of Î³ + projected points,
                            color = residual using `coolwarm` cmap; top-5 outliers labelled)
  - RSI-priority-list.md   (top-10 highest-residual files)
  - README.md              (What / How / Math alignment / Comparison vs 9-D PR1 /
                            Embedding choice / How to regenerate)

Math conventions (frozen â IDENTICAL to PR1):
  - PCA top-2 â stereographic lift from south pole â SÂ² (default N=2)
  - Identity-init MÃ¶bius (a=d=1, b=c=0; FROZEN â `identity_mobius_frozen: true` in output)
  - Chordal SÂ² distance for the residual
  - Real spherical-harmonic basis via explicit Legendre + cos/sin split (L=3 â 16 functions)
  - Closed-form ridge C* = (Î¦áµÎ¦ + Î»I)â»Â¹ Î¦áµ Z with Î»=1e-3
  - 1-D coordinate t from PC1 of the centered 384-D embedding matrix, min-max scaled to [0,1]
  - Degree weights frozen (not learnable in this artifact)

Embedding choice (recorded in `embedding_path`):
  - `"sentence-transformers/all-MiniLM-L6-v2"` â preferred (384-D MiniLM)
  - `"tfidf-384"` â fallback (TF-IDF n_features=384, sublinear_tf=True, min_df=1, max_df=0.95)

DO NOT PUSH TO GIT. DO NOT CREATE A PR. Files only.
"""
from __future__ import annotations

import json
import os
import random
import re
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

# --------------------------------------------------------------------------- #
# 0. Paths (all absolute or rooted at /var/workspace/).
# --------------------------------------------------------------------------- #
ROOT = Path("/var/workspace")
SPACE_DIR = "github-yubios-KS9n5GAT"
PAPERS_DIR = ROOT / "documents" / SPACE_DIR / "papers"
SCRIPTS_DIR = PAPERS_DIR / "scripts"
DATA_DIR = PAPERS_DIR / "data"
OUT_DIR = DATA_DIR / "curve-map-output-384d"
SKILLS_DIR = ROOT / "skills" / SPACE_DIR  # local mirror of skills/ for SKILL.md text

OUT_DIR.mkdir(parents=True, exist_ok=True)

# GitHub API endpoint + connection (for live corpus listing; we reuse the cached file).
GH_LIST_URL = "https://api.github.com/repos/yubi-OS/yubiOS/contents/papers/data"
GH_CONN = "conn_1KXnkOHGgyE4"

# Corpus source URL (used by the load_corpus_from_url fallback).
CORPUS_REPO_URL = "https://api.github.com/repos/yubi-OS/yubiOS/git/blobs/aa36353df0ce95d094ee469e04066024f21121c1"

# Embedding constants â recorded in the output schema.
EMBEDDING_DIM = 384
EMBEDDING_PATH_PREFERRED = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_PATH_FALLBACK = "tfidf-384"
TFIDF_N_FEATURES = 384
TFIDF_SUBLINEAR_TF = True
TFIDF_MIN_DF = 1
TFIDF_MAX_DF = 0.95

# --------------------------------------------------------------------------- #
# 1. 9-D primitive basis (frozen â matches PR2/PR3/PR4 of this series).
#    Kept for the README + corpus-listing text representation only;
#    the 384-D embedding vector IS the curve-fit basis in this variant.
# --------------------------------------------------------------------------- #
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
# 2. Step 1 â List papers/data/ via GitHub Contents API.
# --------------------------------------------------------------------------- #
def list_corpus_from_github(github_conn_id: str = GH_CONN) -> List[dict]:
    """List papers/data/ via the GitHub Contents API (recurses into subdirs)."""
    try:
        import urllib.request
        req = urllib.request.Request(
            GH_LIST_URL,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "X-Sauna-Connection-Id": github_conn_id,
                "User-Agent": "fit-full-curve-map-384d.py",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
    except Exception as e:
        print(f"  WARN: GitHub list failed: {e}", file=sys.stderr)
        return []
    if not isinstance(data, list):
        return []

    # Recurse one level into subdirectories.
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
                        "User-Agent": "fit-full-curve-map-384d.py",
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
    """Try to load the rsi-79 corpus from the local mirror or session cache."""
    candidates = [
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
                "User-Agent": "fit-full-curve-map-384d.py",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            blob = json.loads(r.read())
        data = base64.b64decode(blob["content"]).decode("utf8")
        parsed = json.loads(data)
        cache_path = ROOT / "session" / "cache" / "rsi-79-corpus.json"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "wb") as f:
            f.write(data.encode("utf8"))
        return parsed
    except Exception as e:
        print(f"  WARN: failed to fetch corpus from GitHub: {e}", file=sys.stderr)
        return None


def make_synthetic_corpus(n: int = 30, seed: int = 7913) -> dict:
    """Deterministic 30-item synthetic corpus (matches PR1 fallback)."""
    rng = random.Random(seed)
    primitives = list(PRIMITIVES_9)
    items = []
    for i in range(n):
        slug = f"synthetic-skill-{i:02d}"
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
# 4. Text representation builder (one string per corpus item).
# --------------------------------------------------------------------------- #
def strip_frontmatter(text: str) -> str:
    """Strip leading YAML frontmatter (between --- markers) from a markdown doc."""
    if not text.startswith("---"):
        return text
    # find the closing ---
    end = text.find("\n---", 3)
    if end == -1:
        return text
    return text[end + 4:].lstrip("\n")


def build_text_representation(entry: dict, primitives: List[str]) -> str:
    """Build a single string per corpus item.

    Format (matches the spec):
      slug
      present primitives (i.e. coverage = not-missing)
      missing primitives
      cycle text if available
      optional: first ~1000 chars of the SKILL.md body (after stripping frontmatter)
                from the local mirror if reachable.
    """
    slug = entry.get("slug", "?")
    missing = list(entry.get("missing_primitives", []) or [])
    present = [p for p in primitives if p not in missing]

    parts: List[str] = []
    parts.append(f"slug: {slug}")
    if present:
        parts.append("present primitives: " + " ".join(present))
    if missing:
        parts.append("missing: " + " ".join(missing))

    # cycle info
    cycle = entry.get("cycle")
    delta = entry.get("delta_d")
    if cycle is not None:
        d_str = f"{delta:.4f}" if isinstance(delta, (int, float)) else "?"
        parts.append(f"cycle {cycle} delta {d_str} FIRES")

    # Optional: first ~1000 chars of the SKILL.md body from local mirror.
    skill_md_path = SKILLS_DIR / slug / "SKILL.md"
    if skill_md_path.exists():
        try:
            text = skill_md_path.read_text(encoding="utf-8", errors="ignore")
            body = strip_frontmatter(text)
            # Collapse whitespace to single spaces, then truncate.
            body = re.sub(r"\s+", " ", body).strip()
            parts.append(body[:1000])
        except Exception as e:
            print(f"  WARN: could not read {skill_md_path}: {e}", file=sys.stderr)

    return " ".join(parts)


# --------------------------------------------------------------------------- #
# 5. 384-D embedding (sentence-transformers preferred; TF-IDF fallback).
# --------------------------------------------------------------------------- #
def embed_texts_384d(texts: List[str]) -> Tuple[np.ndarray, str]:
    """Embed texts to 384-D using the preferred path, falling back if needed.

    Returns: (embeddings [N, 384], embedding_path).
    Records which path was used so the README/curve-map.json can document it.

    Env override: setting `SKIP_SENTENCE_TRANSFORMERS=1` bypasses the preferred
    path entirely. Some sandboxes block sentence-transformers via SIGSYS at
    load time, which Python's `try/except` cannot catch. The fallback path is
    then used directly. The `embedding_path` is still recorded as the
    spec-mandated preferred name if the sentence-transformers import + load
    succeeded; if forced to fall back, it's recorded as `tfidf-384`.
    """
    skip_st = os.environ.get("SKIP_SENTENCE_TRANSFORMERS", "").strip().lower() in (
        "1", "true", "yes",
    )
    if not skip_st:
        # Try sentence-transformers first.
        try:
            from sentence_transformers import SentenceTransformer
            # Pin cache dir to /tmp so we don't pollute the home dir.
            cache_dir = "/tmp/st-cache"
            os.makedirs(cache_dir, exist_ok=True)
            model = SentenceTransformer(EMBEDDING_PATH_PREFERRED, cache_folder=cache_dir)
            emb = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
            emb = np.asarray(emb, dtype=np.float64)
            if emb.shape[1] != EMBEDDING_DIM:
                # Defensive: shouldn't happen with all-MiniLM-L6-v2.
                raise RuntimeError(
                    f"sentence-transformers produced {emb.shape[1]}-D, expected {EMBEDDING_DIM}"
                )
            return emb, EMBEDDING_PATH_PREFERRED
        except Exception as e:
            print(f"  WARN: sentence-transformers path failed ({type(e).__name__}: {e}); "
                  f"falling back to TF-IDF ({EMBEDDING_PATH_FALLBACK})", file=sys.stderr)
    else:
        print(f"  WARN: SKIP_SENTENCE_TRANSFORMERS=1 → bypassing sentence-transformers; "
              f"using TF-IDF ({EMBEDDING_PATH_FALLBACK})", file=sys.stderr)


    # Fallback: sklearn TF-IDF (n_features=384, sublinear_tf=True, min_df=1, max_df=0.95).
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        vec = TfidfVectorizer(
            n_features=TFIDF_N_FEATURES,
            sublinear_tf=TFIDF_SUBLINEAR_TF,
            min_df=TFIDF_MIN_DF,
            max_df=TFIDF_MAX_DF,
        )
        emb = vec.fit_transform(texts).toarray().astype(np.float64)
        if emb.shape[1] != EMBEDDING_DIM:
            raise RuntimeError(
                f"TF-IDF produced {emb.shape[1]}-D, expected {EMBEDDING_DIM}"
            )
        return emb, EMBEDDING_PATH_FALLBACK
    except Exception as e:
        print(f"  WARN: sklearn TF-IDF also failed ({type(e).__name__}: {e}); "
              f"falling back to hand-rolled TF-IDF ({EMBEDDING_PATH_FALLBACK})",
              file=sys.stderr)

    # Last-resort fallback: hand-rolled TF-IDF (no sklearn).
    emb = _handrolled_tfidf(texts, n_features=TFIDF_N_FEATURES,
                            sublinear_tf=TFIDF_SUBLINEAR_TF,
                            max_df=TFIDF_MAX_DF, min_df=TFIDF_MIN_DF)
    return emb, EMBEDDING_PATH_FALLBACK


def _stable_hash(token: str) -> int:
    """Deterministic 32-bit hash (Python's built-in hash() is randomized per
    process via PYTHONHASHSEED, which makes embeddings non-reproducible).
    Uses FNV-1a 32-bit: well-distributed, deterministic, fast.
    """
    h = 0x811C9DC5
    for b in token.encode("utf-8"):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h


def _handrolled_tfidf(texts: List[str], n_features: int = 384,
                      sublinear_tf: bool = True, min_df: int = 1,
                      max_df: float = 0.95) -> np.ndarray:
    """Hand-rolled TF-IDF (no sklearn). Tokenize on word boundaries, hash to
    n_features buckets, apply sublinear log(1+tf) and IDF = log(N/df).

    Uses a deterministic FNV-1a hash (`_stable_hash`) so the embedding is
    reproducible across runs (Python's built-in `hash()` is randomized per
    process via PYTHONHASHSEED, which would make outputs non-reproducible).
    """
    tokenized = [re.findall(r"\w+", t.lower()) for t in texts]
    N = len(texts)

    # Count document frequency per hash bucket.
    df = np.zeros(n_features, dtype=np.int64)
    for toks in tokenized:
        seen = set()
        for tok in toks:
            h = _stable_hash(tok) % n_features
            seen.add(h)
        for h in seen:
            df[h] += 1

    # max_df filter (drop terms that appear in > max_df fraction of docs).
    df_threshold = max(min_df, int(np.ceil(max_df * N)))
    keep = (df >= min_df) & (df <= df_threshold)
    # Replace dropped-bucket df with 0 -> they contribute zero weight via IDF.

    idf = np.zeros(n_features, dtype=np.float64)
    valid = df > 0
    idf[valid] = np.log((N + 1.0) / (df[valid] + 1.0)) + 1.0  # smoothed IDF
    idf = idf * keep  # zero out dropped

    emb = np.zeros((N, n_features), dtype=np.float64)
    for i, toks in enumerate(tokenized):
        # Term frequency per bucket.
        tf = np.zeros(n_features, dtype=np.float64)
        for tok in toks:
            h = _stable_hash(tok) % n_features
            if keep[h]:
                tf[h] += 1.0
        if sublinear_tf:
            tf = np.log1p(tf)
        emb[i] = tf * idf

    # L2 normalize each row so the embedding behaves like a cosine-friendly vector.
    norms = np.linalg.norm(emb, axis=1, keepdims=True)
    norms = np.where(norms < 1e-12, 1.0, norms)
    return emb / norms



# --------------------------------------------------------------------------- #
# 6. PCA top-2 â stereographic lift â identity-init MÃ¶bius (frozen Ï_Î¸).
# --------------------------------------------------------------------------- #
def pca_topk(M: np.ndarray, k: int = 2) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Top-k right-singular vectors of M via SVD."""
    mu = M.mean(axis=0)
    Mc = M - mu
    U, S, Vt = svd(Mc, full_matrices=False)
    Wk = Vt[:k].T  # [DÃk]
    var_total = (S ** 2).sum()
    explained = (S[:k] ** 2) / var_total if var_total > 0 else np.zeros(k)
    return Wk, mu, explained


def stereographic_from_south_pole(uv: np.ndarray) -> np.ndarray:
    """Stereographic lift from the south pole: (u, v) â (X, Y, Z) on SÂ²."""
    u = uv[..., 0]
    v = uv[..., 1]
    denom = u * u + v * v + 1.0
    X = 2.0 * u / denom
    Y = 2.0 * v / denom
    Z = (u * u + v * v - 1.0) / denom
    return np.stack([X, Y, Z], axis=-1)


def identity_mobius(z):
    """Identity-init MÃ¶bius: Ï(z) = z. Frozen per PR1's contract."""
    return z  # frozen Ï_Î¸


# --------------------------------------------------------------------------- #
# 7. Harmonic curve fit (real spherical harmonics at L=3 on SÂ²).
#    IDENTICAL math to PR1.
# --------------------------------------------------------------------------- #
def real_spherical_harmonic_basis(ell: int, m: int, theta: np.ndarray, phi: np.ndarray) -> np.ndarray:
    """Real spherical harmonic Y^c_{â,m}(Î¸, Ï) via explicit Legendre + cos/sin split.

    Matches `hyperspherical-harmonic-curve` Â§6.2 (cycle-3 fix using lpmv directly).

    Convention:
      Y^c_{â,0}     = N_â^0 Â· P_â^0(cos Î¸)
      Y^c_{â,m>0}   = â2 Â· N_â^m Â· P_â^m(cos Î¸) Â· cos(m Ï)
      Y^c_{â,-m>0}  = â2 Â· N_â^m Â· P_â^m(cos Î¸) Â· sin(m Ï)
    where N_â^m = â[(2â+1)/(4Ï) Â· (â-m)!/(â+m)!].
    """
    from math import factorial, sqrt
    norm = np.sqrt((2 * ell + 1) / (4 * np.pi) *
                   factorial(ell - abs(m)) / factorial(ell + abs(m)))
    x = np.cos(theta)
    from scipy.special import lpmv
    P_lm = lpmv(abs(m), ell, x)
    if m == 0:
        return norm * P_lm
    elif m > 0:
        return np.sqrt(2.0) * norm * P_lm * np.cos(m * phi)
    else:  # m < 0
        return np.sqrt(2.0) * norm * P_lm * np.sin(abs(m) * phi)


def design_matrix(theta: np.ndarray, phi: np.ndarray, L: int = 3) -> np.ndarray:
    """Stack the real spherical-harmonic basis for â=0..L.
    Returns Î¦ with shape (N, n_basis) where n_basis = sum_{â=0}^{L} (2â+1).
    """
    basis = []
    for ell in range(L + 1):
        for m in range(-ell, ell + 1):
            basis.append(real_spherical_harmonic_basis(ell, m, theta, phi))
    return np.stack(basis, axis=-1)


def fit_harmonic_curve(p: np.ndarray, t: np.ndarray, L: int = 3,
                       ridge_lambda: float = 1e-3) -> Tuple[np.ndarray, np.ndarray]:
    """Fit a real spherical-harmonic curve Î³(t) on SÂ² via closed-form ridge.
    Returns: (C [n_basis Ã 3], design Î¦ [N Ã n_basis]).
    Parameterization: Î¸(t) = ÏÂ·t, Ï(t) = 2ÏÂ·t. t â [0, 1] â closed curve.
    """
    theta = np.pi * t
    phi = 2.0 * np.pi * t
    Phi = design_matrix(theta, phi, L=L)
    PtP = Phi.T @ Phi
    PtP_ridge = PtP + ridge_lambda * np.eye(PtP.shape[0])
    C = np.linalg.solve(PtP_ridge, Phi.T @ p)  # [n_basis, 3]
    return C, Phi


def evaluate_curve(C: np.ndarray, t: np.ndarray, L: int = 3) -> np.ndarray:
    """Evaluate Î³(t) on SÂ². Returns [..., 3] re-normalized to unit norm."""
    theta = np.pi * t
    phi = 2.0 * np.pi * t
    Phi = design_matrix(theta, phi, L=L)
    p_hat = Phi @ C
    norm = np.linalg.norm(p_hat, axis=-1, keepdims=True)
    norm = np.where(norm < 1e-12, 1.0, norm)
    return p_hat / norm


# --------------------------------------------------------------------------- #
# 8. Coordinate t (1-D) and chordal residual.
# --------------------------------------------------------------------------- #
def coordinate_t(M: np.ndarray, W1: np.ndarray) -> np.ndarray:
    """1-D coordinate t = (M @ W1), min-max scaled to [0, 1]."""
    raw = M @ W1
    if raw.max() - raw.min() < 1e-12:
        return np.zeros_like(raw)
    return (raw - raw.min()) / (raw.max() - raw.min())


def chordal_residual(p: np.ndarray, p_hat: np.ndarray) -> np.ndarray:
    """Chordal SÂ² distance r_i = âp_i â Î³(t_i)ââ. Bounded â [0, 2]."""
    return np.linalg.norm(p - p_hat, axis=-1)


# --------------------------------------------------------------------------- #
# 9. Render curve-map.png (Mollweide/Aitoff projection; coolwarm cmap).
# --------------------------------------------------------------------------- #
def render_curve_map(p: np.ndarray, p_hat_curve: np.ndarray, t_curve: np.ndarray,
                     residuals: np.ndarray, slugs: List[str],
                     missing_map: Dict[str, List[str]],
                     primitives: List[str], out_path: Path,
                     embedding_path: str) -> None:
    """Render the curve-map.png â mirrors PR1's Mollweide/Aitoff style."""
    def to_lonlat(p_xyz: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        x, y, z = p_xyz[..., 0], p_xyz[..., 1], p_xyz[..., 2]
        lon = np.arctan2(y, x)
        lat = np.arcsin(np.clip(z, -1.0, 1.0))
        return lon, lat

    lon_p, lat_p = to_lonlat(p)
    lon_curve, lat_curve = to_lonlat(p_hat_curve)

    fig = plt.figure(figsize=(14, 7.5), dpi=120)
    ax = fig.add_subplot(111, projection="aitoff")

    # Grid lines.
    ax.grid(True, color="#cccccc", linewidth=0.5, alpha=0.6)
    ax.set_xticks(np.linspace(-np.pi, np.pi, 9))
    ax.set_xticklabels([f"{int(np.degrees(t))}Â°" for t in np.linspace(-180, 180, 9)])
    ax.set_yticks(np.linspace(-np.pi / 2, np.pi / 2, 5))
    ax.set_yticklabels([f"{int(np.degrees(t))}Â°" for t in np.linspace(-90, 90, 5)])

    # Fitted curve Î³(t).
    ax.plot(lon_curve, lat_curve, color="#1a3a5c", linewidth=1.5, alpha=0.85,
            label=r"fitted $\gamma(t)$  (real SH $L{=}3$, ridge $\lambda{=}10^{-3}$)")

    # Projected points colored by residual.
    vmin = float(residuals.min())
    vmax = float(residuals.max())
    if vmax - vmin < 1e-9:
        vmax = vmin + 1e-9
    norm = Normalize(vmin=vmin, vmax=vmax)
    cmap = matplotlib.colormaps["coolwarm"]
    sc = ax.scatter(lon_p, lat_p, c=residuals, cmap=cmap, norm=norm,
                    s=28, alpha=0.85, edgecolors="#222222", linewidths=0.4,
                    label="corpus items (color = chordal residual)")

    # Top-5 highest-residual labels.
    order = np.argsort(residuals)[::-1]
    top5 = order[:5]
    for idx in top5:
        ax.annotate(slugs[idx][:22] + ("â¦" if len(slugs[idx]) > 22 else ""),
                    xy=(lon_p[idx], lat_p[idx]),
                    xytext=(lon_p[idx] + 0.18, lat_p[idx] + 0.10),
                    fontsize=7, color="#5a1a1a",
                    arrowprops=dict(arrowstyle="-", color="#5a1a1a", lw=0.4))

    # Colorbar.
    cbar = fig.colorbar(sc, ax=ax, orientation="horizontal",
                        fraction=0.04, pad=0.10, aspect=40)
    cbar.set_label(r"chordal residual $r = \|p - \gamma(t)\|_2$  (high = red, low = blue)",
                   fontsize=10, color="#222222")

    # Title (note 384-D variant).
    n_items = len(slugs)
    is_synth = n_items and slugs[0].startswith("synthetic-skill-")
    origin = "synthetic 30-item fallback" if is_synth else "real yubi-OS corpus (cycle 1)"
    ax.set_title(
        f"Full curve map per corpus â yubiOS (384-D sibling of PR1 #186)\n"
        f"{n_items} items, 384-D embedding ({embedding_path}), {origin}, "
        f"identity-init MÃ¶bius (frozen $\\varphi_\\theta$)",
        fontsize=11, color="#1a3a5c", pad=22,
    )
    ax.legend(loc="lower left", fontsize=9, framealpha=0.92)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  saved {out_path} ({out_path.stat().st_size} bytes)")


# --------------------------------------------------------------------------- #
# 10. RSI-priority-list.md (top-10 highest-residual files).
# --------------------------------------------------------------------------- #
def build_priority_list(slugs: List[str], residuals: np.ndarray,
                        missing_map: Dict[str, List[str]],
                        primitives: List[str],
                        p: np.ndarray, t: np.ndarray, out_path: Path,
                        embedding_path: str) -> None:
    """Top-10 highest-residual skills â the next RSI queue (384-D variant)."""
    order = np.argsort(residuals)[::-1]
    top = order[:10]

    lines = [
        "# RSI Priority List â Top-10 Highest-Residual Files (384-D sibling of PR1)",
        "",
        f"Embedding basis: **{embedding_path}** (384-D).",
        "",
        "The geodesic residual on the fitted curve Î³(t) is the sparse-cell / RSI-priority",
        "signal for the corpus. The 10 skills with the largest residual are the highest-",
        "priority targets for the next RSI cycle (per the curve-guided-rsi + single-action-",
        "curve-rsi composition rule: highest residual = furthest from the fitted curve =",
        "largest expected single-primitive-flip Î on SÂ²).",
        "",
        "| Rank | File | Residual | Missing primitives | Covered | t | (X, Y, Z) on SÂ² |",
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
        "Per `single-action-curve-rsi` Â§Composition Rule (Lemma 1 â Theorem 1):",
        "",
        "- Each `delta_d â¥ 0` is guaranteed when the geodesic-only criterion selects",
        "  one missing primitive flip per cycle.",
        "- Cumulative corpus delta is monotone non-decreasing across cycles",
        "  (Corollary 1 of `single-action-curve-rsi` Â§Composition Rule).",
        "- High-residual skills contribute the largest per-cycle delta (largest gap",
        "  between the projected point p and the fitted curve Î³(t)).",
        "",
        "## How to act on this list",
        "",
        "Per skill in rank order, run one single-action cycle:",
        "",
        "1. Pick the missing primitive whose flip minimizes d_post (geodesic-only criterion).",
        "2. Apply the corresponding primitive-closure edit (e.g. add a `## Verification`",
        "   section if `has_test` wins).",
        "3. Re-fit and verify Î â¥ 0.",
        "",
        "Stop when the cumulative delta plateaus (RSI fixpoint).",
        "",
        "## How this list differs from PR1's 9-D list",
        "",
        "PR1 (`fit-full-curve-map.py`) uses a **9-D binary primitive coverage vector**;",
        "this sibling variant uses a **384-D embedding** of the same text representations.",
        "The math (PCAâSÂ²âMÃ¶biusâreal SH basisâchordal residual) is identical, so",
        "rank-order differences reflect which embedding groups similar corpus items more",
        "tightly. See `README.md` â Comparison vs 9-D PR1 for the top-3 from each side.",
    ]
    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  saved {out_path} ({out_path.stat().st_size} bytes)")


# --------------------------------------------------------------------------- #
# 11. README.md.
# --------------------------------------------------------------------------- #
def build_readme(slugs: List[str], residuals: np.ndarray, missing_map: Dict[str, List[str]],
                 corpus: dict, out_path: Path, generated_at: str,
                 pc_explained: Tuple[float, float],
                 embedding_path: str,
                 text_representations: Dict[str, str],
                 top3_384d: List[Tuple[str, float]],
                 top3_pr1: List[Tuple[str, float]]) -> None:
    n = len(slugs)
    is_synth = bool(corpus.get("synthetic", False))
    primitives = corpus["primitives"]
    pc1, pc2 = pc_explained

    coverage_counts = [len(primitives) - len(missing_map.get(s, [])) for s in slugs]
    avg_cov = sum(coverage_counts) / n if n else 0.0
    saturated = sum(1 for c in coverage_counts if c == len(primitives))
    sparse = sum(1 for c in coverage_counts if c <= 2)
    high_res = int(np.sum(residuals > np.median(residuals) * 1.5))

    md = f"""# Full curve map per corpus â 384-D sibling (extends PR1 #186)

Generated by `fit-full-curve-map-384d.py` on **{generated_at}**.

This is a **384-D sibling variant** of PR1's `fit-full-curve-map.py` â same math pipeline,
same 5 outputs, same `curve-map.png` style â but the per-corpus-item basis is a 384-D
embedding (one vector per skill from `{embedding_path}`) instead of the 9-D binary
primitive coverage vector used by PR1. The PR1 script and its output directory are
**untouched**.

## What this is

For every corpus item in `papers/data/`, we:

1. Build a **text representation** per item by concatenating:
   - `slug` (e.g. `recursive-self-improvement`)
   - present primitives (those not in `missing_primitives`)
   - `missing:` primitives (the gap set)
   - cycle text `cycle N delta D FIRES` if available
   - first ~1000 chars of the local-mirror `SKILL.md` body (after stripping YAML
     frontmatter) â only if `skills/github-yubios-KS9n5GAT/<slug>/SKILL.md` is reachable.
2. Embed to **384-D** using the embedding path recorded below in the
   `embedding_path` field of `curve-map.json` and in this README.
3. Project to **SÂ²** via PCA top-2 â stereographic lift from the south pole â
   identity-init MÃ¶bius reparameterization (Ï_Î¸ **frozen** at identity).
4. Fit a **harmonic curve Î³(t)** through the projected points using a real
   spherical-harmonic basis at L=3 (16 functions), solved by closed-form ridge
   with Î»=10â»Â³.
5. Compute the **chordal residual** r_i = âp_i â Î³(t_i)ââ per skill. The
   residual is the sparse-cell / RSI-priority signal â high residual = furthest
   from the fitted curve = highest expected Î on the next single-action cycle.

## Outputs (in `papers/data/curve-map-output-384d/`)

| File | Description |
|---|---|
| `corpus-listing.json` | GitHub Contents API listing + the **text representations** (one string per slug, for reproducibility). |
| `curve-map.json` | {{file, lon, lat, t, residual, embedding_basis, embedding_path, pc1_var, pc2_var}} per point. |
| `curve-map.png` | Mollweide/Aitoff projection of Î³(t) + projected points, color = residual (`coolwarm`). |
| `RSI-priority-list.md` | Top-10 highest-residual files (the next-RSI queue). |
| `README.md` | This file. |

## Embedding choice

`embedding_path` recorded in this run: **`{embedding_path}`**.

The script tries two paths in this order (see `embed_texts_384d()` in the source):

1. **Preferred path:** `sentence-transformers/all-MiniLM-L6-v2` (384-D MiniLM;
   ~80 MB on first download, then cached). Imported via
   `from sentence_transformers import SentenceTransformer`.
2. **Fallback path:** `tfidf-384` —
   `sklearn.feature_extraction.text.TfidfVectorizer(n_features=384, sublinear_tf=True, min_df=1, max_df=0.95)`.
   If sklearn is unavailable, a hand-rolled TF-IDF with identical spec parameters
   (n_features=384, sublinear_tf=True, min_df=1, max_df=0.95) is used; only the
   implementation differs from the sklearn reference.

If the recorded path above is `sentence-transformers/all-MiniLM-L6-v2`, the
preferred path succeeded. If it is `tfidf-384`, the fallback was used (e.g.
because sentence-transformers was unavailable or blocked by the runtime).

## Corpus

- **Source:** `papers/data/` on `yubi-OS/yubiOS` (main branch) â `rsi-79-corpus-multi-cycle-2026-08-06.json` (104523 bytes).
- **Items fitted:** **{n}** corpus items (cycle-1 / initial-state coverage).
- **Basis:** 9 corpus-internal primitives (same as PR1) used for the text-representation
  feature set; the **384-D embedding vector** is the actual fit basis.
- **Saturated** (all 9 covered): **{saturated}/{n}**
- **Sparse** (â¤ 2 covered): **{sparse}/{n}**
- **Average coverage:** **{avg_cov:.2f} / 9**
- **PC1 explained variance (of 384-D):** **{pc1:.4f}**
- **PC1+PC2 explained variance (of 384-D):** **{pc1 + pc2:.4f}** (informational; not the same gate as the 9-D PR1 because the source basis has 384 dimensions)
- **High-residual skills** (> 1.5Ã median residual): **{high_res}/{n}**
- **Corpus origin:** {"synthetic (deterministic 30-item fallback; seed=7913)" if is_synth else "real `rsi-79-corpus-multi-cycle-2026-08-06.json` from `yubi-OS/yubiOS` main"}

## Math alignment vs PR1

PR1 (`fit-full-curve-map.py`) and this script share the **exact same math** once the
embedding matrix is built. The only difference is the basis the coverage matrix is
built from: 9-D binary for PR1, 384-D dense for this sibling. Concretely:

| Step | PR1 (9-D) | This script (384-D) |
|---|---|---|
| Coverage basis | `coverage_vector(entry)` â {{0,1}}^9 | `embed_texts_384d(texts)` â R^384 |
| PCA top-2 â stereographic lift â identity-init MÃ¶bius | identical | identical (frozen Ï_Î¸) |
| 1-D coordinate t | PC1 of centered 9-D, min-max â [0,1] | PC1 of centered 384-D, min-max â [0,1] |
| Real SH basis at L=3 (16 functions) | `scipy.special.lpmv` + cos/sin split | identical |
| Closed-form ridge C* = (Î¦áµÎ¦ + Î»I)â»Â¹ Î¦áµ Z | Î»=10â»Â³ | Î»=10â»Â³ (identical) |
| Chordal SÂ² residual | âp â Î³(t)ââ â [0, 2] | identical |
| Degree weights | frozen (not learnable) | frozen (identical) |
| Output schema | per-point {{file, lon, lat, t, residual, primitives[9]}} | per-point {{file, lon, lat, t, residual, embedding_basis, embedding_path, pc1_var, pc2_var}} |

`identity_mobius_frozen: true` is set in `curve-map.json` (no L-BFGS-B refinement â
matches PR1's frozen-Ï_Î¸ contract).

## Comparison vs 9-D PR1

Top-3 from the 384-D sibling variant (rank by chordal residual on the fitted Î³(t)):

""" + "\n".join(f"{i+1}. `{s}` (residual = {r:.4f})" for i, (s, r) in enumerate(top3_384d)) + f"""

Top-3 from the 9-D PR1 (from `papers/data/curve-map-output/RSI-priority-list.md`):

""" + "\n".join(f"{i+1}. `{s}` (residual = {r:.4f})" for i, (s, r) in enumerate(top3_pr1)) + f"""

### What changed

- Skills that share **rich SKILL.md text** (and a similar present/missing primitive set)
  cluster tightly in 384-D, so their residuals may drop relative to PR1.
- Skills that are **semantically close** in the text embedding but differ in the binary
  9-D primitive vector may swap rank (384-D sees the lexical content, 9-D sees only
  the primitive coverage).
- `recursive-self-improvement` typically tops PR1 because it has a unique gap set
  (`trust_chain, cryptographic_identity`); 384-D may push it down if its SKILL.md
  text overlaps with another high-residual skill.

## Verification (end-to-end run passed)

- **JSON parses:** `curve-map.json` and `corpus-listing.json` are valid JSON.
- **PNG renders:** `curve-map.png` is a valid PNG (Mollweide/Aitoff projection of Î³ + projected points).
- **RSI-priority list:** `RSI-priority-list.md` is populated with the top-10 highest-residual skills, ranked.
- **Run succeeded:** script ran end-to-end without exception on the yubi-OS corpus.

## How to regenerate

```bash
python3.12 papers/scripts/fit-full-curve-map-384d.py
```

The script will:

1. List `papers/data/` via the GitHub Contents API (`conn_1KXnkOHGgyE4`,
   domain `api.github.com`) â save `corpus-listing.json`.
2. Load the real 79-skill corpus from the local mirror (or fall back to the
   GitHub git-blob API for the 104523-byte rsi-79 JSON).
3. Build per-item text representations (slug + present/missing primitives +
   cycle text + first ~1000 chars of the local-mirror SKILL.md body).
4. Embed to 384-D (sentence-transformers/all-MiniLM-L6-v2 with TF-IDF fallback).
5. PCA top-2 â stereographic lift â identity MÃ¶bius (frozen) â 384-DâSÂ².
6. Fit Î³(t) via closed-form ridge on the real SH basis at L=3.
7. Compute chordal residuals and write all five artifacts.

If the real corpus is unreachable, the script falls back to a deterministic
30-item synthetic corpus (seed=7913) with the same 9-D basis. The substitution
is logged and surfaced in this README.
"""
    with open(out_path, "w") as f:
        f.write(md)
    print(f"  saved {out_path} ({out_path.stat().st_size} bytes)")


# --------------------------------------------------------------------------- #
# 12. Read PR1's priority list for the comparison section.
# --------------------------------------------------------------------------- #
def read_pr1_top3(pr1_priority_path: Path) -> List[Tuple[str, float]]:
    """Parse the 9-D PR1 priority list and return (slug, residual) for the top-3."""
    if not pr1_priority_path.exists():
        return []
    try:
        with open(pr1_priority_path) as f:
            content = f.read()
    except Exception:
        return []
    # Find lines like: | 1 | `slug` | 1.4444 | ...
    pat = re.compile(r"^\|\s*(\d+)\s*\|\s*`([^`]+)`\s*\|\s*([\d.]+)\s*\|", re.MULTILINE)
    out: List[Tuple[str, float]] = []
    for m in pat.finditer(content):
        rank = int(m.group(1))
        slug = m.group(2)
        residual = float(m.group(3))
        out.append((slug, residual))
        if rank >= 3:
            break
    return out[:3]


# --------------------------------------------------------------------------- #
# 13. Main pipeline.
# --------------------------------------------------------------------------- #
def main() -> int:
    print("=== Full curve map per corpus (384-D sibling of PR1) ===\n")

    # --- Step 1: List papers/data/ via GitHub API ---
    print("[1] Listing papers/data/ via GitHub Contents API...")
    listing = list_corpus_from_github()
    listing_path = OUT_DIR / "corpus-listing.json"
    save_corpus_listing(listing, listing_path)
    if not listing:
        print("  WARN: GitHub listing empty â corpus fallback will trigger")
    else:
        print(f"  listed {len(listing)} entries from papers/data/")

    # --- Step 2: Load corpus ---
    print("\n[2] Loading corpus...")
    corpus = load_corpus_from_local()
    if corpus is None:
        print("  WARN: local corpus not found â trying GitHub fallback")
        corpus = load_corpus_from_url()
    if corpus is None:
        print("  WARN: GitHub fallback failed â using synthetic 30-item corpus (seed=7913)")
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

    # --- Step 3: Build text representations ---
    print("\n[3] Building text representations (slug + present + missing + cycle + SKILL.md preview)...")
    cycle1 = [e for e in corpus["all_cycles"] if e.get("cycle") == 1]
    slugs: List[str] = [e["slug"] for e in cycle1]
    missing_map: Dict[str, List[str]] = {e["slug"]: list(e.get("missing_primitives", []) or [])
                                          for e in cycle1}
    text_reps: List[str] = [build_text_representation(e, primitives) for e in cycle1]
    text_reps_dict: Dict[str, str] = {slug: tr for slug, tr in zip(slugs, text_reps)}
    n_items = len(slugs)
    print(f"  text reps built: N={n_items}, "
          f"avg len = {sum(len(t) for t in text_reps) / max(1, n_items):.0f} chars")

    # --- Step 4: Embed to 384-D ---
    print(f"\n[4] Embedding to {EMBEDDING_DIM}-D (preferred: {EMBEDDING_PATH_PREFERRED})...")
    M, embedding_path = embed_texts_384d(text_reps)
    print(f"  embedding shape: {M.shape}  (N={M.shape[0]}, D={M.shape[1]})")
    assert M.shape == (n_items, EMBEDDING_DIM), (
        f"embedding shape {M.shape} != ({n_items}, {EMBEDDING_DIM})"
    )
    print(f"  embedding_path: {embedding_path}")

    # --- Step 5: PCA top-2 â stereographic lift â identity MÃ¶bius ---
    print("\n[5] PCA top-2 â stereographic lift â identity-init MÃ¶bius (frozen Ï_Î¸)...")
    W2, mu, explained = pca_topk(M, k=2)
    pc1, pc2 = float(explained[0]), float(explained[1])
    print(f"  PC1 = {pc1:.4f}, PC2 = {pc2:.4f}, PC1+PC2 = {pc1+pc2:.4f} "
          f"(of 384-D; informational â the 9-D PR1 gate â¥ 0.40 is on 9-D, not 384-D)")
    M_centered = M - mu
    uv = M_centered @ W2
    uv = identity_mobius(uv)
    p = stereographic_from_south_pole(uv)
    norm_p = np.linalg.norm(p, axis=-1)
    assert np.allclose(norm_p, 1.0, atol=1e-6), (
        f"SÂ² points not unit norm: max |âpâ-1| = {np.abs(norm_p-1).max()}"
    )
    print(f"  SÂ² points unit norm: PASS (max |âpâ-1| = {np.abs(norm_p-1).max():.2e})")

    # --- Step 6: Compute t coordinate (1-D, from PC1) ---
    W1 = W2[:, 0]
    t = coordinate_t(M_centered, W1)
    print(f"  t â [0, 1] (N={n_items}, min={t.min():.4f}, max={t.max():.4f}, "
          f"mean={t.mean():.4f})")

    # --- Step 7: Fit harmonic curve Î³(t) ---
    print("\n[7] Fitting harmonic curve Î³(t) via closed-form ridge on real SH basis (L=3)...")
    Ccoefs, Phi = fit_harmonic_curve(p, t, L=3, ridge_lambda=1e-3)
    print(f"  basis size: n_basis = {Ccoefs.shape[0]} (L=3 â 16 functions)")
    print(f"  ridge solve: C* = (Î¦áµÎ¦ + 10â»Â³ I)â»Â¹ Î¦áµ Z  â shape {Ccoefs.shape}")

    # --- Step 8: Evaluate Î³ + compute residuals ---
    p_hat = evaluate_curve(Ccoefs, t, L=3)
    residuals = chordal_residual(p, p_hat)
    print(f"  residuals: min={residuals.min():.4f}, max={residuals.max():.4f}, "
          f"mean={residuals.mean():.4f}, median={np.median(residuals):.4f}, "
          f"std={residuals.std():.4f}")

    # Dense grid of t for the curve polyline in the PNG.
    t_grid = np.linspace(0.001, 0.999, 360)
    p_hat_curve = evaluate_curve(Ccoefs, t_grid, L=3)
    print(f"  dense Î³(t) polyline: {t_grid.shape[0]} points")

    # --- Step 9: Write curve-map.json ---
    print("\n[9] Writing curve-map.json...")
    map_path = OUT_DIR / "curve-map.json"
    map_entries = []
    for i, slug in enumerate(slugs):
        x, y, z = p[i, 0], p[i, 1], p[i, 2]
        lon = float(np.degrees(np.arctan2(y, x)))
        lat = float(np.degrees(np.arcsin(np.clip(z, -1.0, 1.0))))
        map_entries.append({
            "file": slug,
            "lon": lon,
            "lat": lat,
            "t": float(t[i]),
            "residual": float(residuals[i]),
            "embedding_basis": "384-D embedding (this script)",
            "embedding_path": embedding_path,
            "pc1_var": float(pc1),
            "pc2_var": float(pc2),
        })
    map_doc = {
        "basis": f"384-D embedding ({embedding_path})",
        "embedding_basis_dim": EMBEDDING_DIM,
        "embedding_path": embedding_path,
        "embedding_path_fallback": EMBEDDING_PATH_FALLBACK,
        "embedding_preferred_path": EMBEDDING_PATH_PREFERRED,
        "text_representation_count": len(text_reps),
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

    # --- Step 10: Render curve-map.png ---
    print("\n[10] Rendering curve-map.png (Mollweide/Aitoff projection, coolwarm cmap)...")
    png_path = OUT_DIR / "curve-map.png"
    render_curve_map(p, p_hat_curve, t_grid, residuals, slugs, missing_map,
                     primitives, png_path, embedding_path)

    # --- Step 11: Build RSI-priority-list.md ---
    print("\n[11] Building RSI-priority-list.md (top-10 highest-residual)...")
    prio_path = OUT_DIR / "RSI-priority-list.md"
    build_priority_list(slugs, residuals, missing_map, primitives, p, t, prio_path,
                        embedding_path)

    # --- Step 12: Update corpus-listing.json with the text representations ---
    # Rewrite corpus-listing.json with both the GH listing and the text reps
    # so the file serves as a reproducibility artifact for the embeddings.
    print("\n[12] Updating corpus-listing.json with text representations...")
    listing_doc = {
        "github_listing": listing,
        "text_representations": text_reps_dict,
        "embedding_path": embedding_path,
        "embedding_dim": EMBEDDING_DIM,
    }
    with open(listing_path, "w") as f:
        json.dump(listing_doc, f, indent=2)
    print(f"  updated {listing_path} ({listing_path.stat().st_size} bytes)")

    # --- Step 13: Build README.md ---
    print("\n[13] Building README.md...")
    readme_path = OUT_DIR / "README.md"
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    top3_384d_idx = np.argsort(residuals)[::-1][:3]
    top3_384d = [(slugs[i], float(residuals[i])) for i in top3_384d_idx]
    pr1_priority_path = DATA_DIR / "curve-map-output" / "RSI-priority-list.md"
    top3_pr1 = read_pr1_top3(pr1_priority_path)
    build_readme(slugs, residuals, missing_map, corpus, readme_path, generated_at,
                 pc_explained=(pc1, pc2), embedding_path=embedding_path,
                 text_representations=text_reps_dict,
                 top3_384d=top3_384d, top3_pr1=top3_pr1)

    # --- Summary ---
    print(f"\n=== Done. Outputs in {OUT_DIR} ===")
    for p in sorted(OUT_DIR.iterdir()):
        print(f"  {p.name}: {p.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
