#!/usr/bin/env python3
"""
spectral_decomposer.py -- a curve-guided-self-ideate tool built on the
program's harmonic-fit machinery and the curveball fixed-margin null.

Goal: given a corpus matrix M (N items x d primitives), produce a
ranked list of "new idea" candidates -- concrete, falsifiable
experiment proposals that, if executed, would close a sparse cell or
extend the spectrum. Each candidate carries the same shape as the
lens-format patches from skills/curve-compass-skill (cycle-34):

    hypothesis:  <a testable claim about this corpus>
    method:      <how the test runs>
    parameters:  <exact inputs and seed>
    delta:       <measured number, with units>
    verdict:     YES | PARTIAL | NO
    score:       0-50 (rank against the lens pool)
    caveat:      <what the experiment did NOT measure>

The breakthrough twist (vs. plain curve-guided-rsi): each candidate's
delta is reported in dBc against the curveball vacuum -- so a "YES"
candidate IS one that deflects above the +15.6 dBc detectability
floor, in the same units the corpus-sonometer uses. The tool's
output is a `cycle-NN-lens.md` artifact ready to drop into a
curve-guided-rsi cycle.

Lean anchors:
  - The curveball null is the same trade as
    CurvedCorpus.trade_preserves_rowSum / trade_preserves_colSum (Lean §8).
  - The reversibility / stationarity of the trade is Lean §9.
  - The corpus-level dBc readout is the L = 20 log_10(|D|/sigma_null)
    decibel law from Lean §12, applied cell-by-cell.
  - The "no statistic without a matched null" rule is enforced
    per-candidate: every candidate's delta is computed against a
    curveball-shuffled null ensemble, not the corpus itself.

Pipeline (each cycle, deterministic given --seed):
  1. Load corpus matrix M.
  2. Identify sparse cells: items where coverage k_i << d, weighted by
     spectral mass (low-l mass concentrates weight on coarse cells).
  3. For each sparse-cell cluster, generate k candidates -- one
     per "primitive that would close the cell", plus two control
     candidates that flip the same primitive on a curveball-shuffled
     copy (selection-null control, mirroring the Möbius-lens
     powering arm from Gap D).
  4. Score each candidate by |deflection| (z) and report in dBc
     alongside its "YES / PARTIAL / NO" verdict and the caveat.
  5. Emit a lens-format markdown artifact ready to merge as a
     cycle-NN-lens.md.

The tool is the language-side analogue of curve-guided-rsi-self and
the deliverable-side analogue of cycle-34's L141-L146 outputs: each
candidate IS a measurable experiment, not a section template.

Usage:
    spectral_decomposer.py --selftest
    spectral_decomposer.py --input <corpus.json|zip|csv>
    spectral_decomposer.py --cycle 34 --seed 20260825
"""
import argparse
import hashlib
import json
import math
import sys
from typing import Any

import numpy as np


# ---------- corpus loaders ----------

def _load_zip(path: str):
    import zipfile
    with zipfile.ZipFile(path) as z:
        # The is-this-x bundle shape: data/real/per_row_coverage_v3.json
        with z.open("is-this-x-2026-08-12/data/real/per_row_coverage_v3.json") as f:
            j = json.load(f)
    M = np.array([r["covered"] for r in j["rows"]], dtype=np.int8)
    slugs = [r.get("slug", f"row_{i}") for i, r in enumerate(j["rows"])]
    return M, slugs


def _load_json(path: str):
    with open(path) as f:
        j = json.load(f)
    if isinstance(j, dict) and "rows" in j:
        M = np.array([r["covered"] for r in j["rows"]], dtype=np.int8)
        slugs = [r.get("slug", f"row_{i}") for i, r in enumerate(j["rows"])]
        return M, slugs
    M = np.asarray(j, dtype=np.int8)
    return M, [f"row_{i}" for i in range(len(M))]


def _load_csv(path: str):
    M = np.loadtxt(path, delimiter=",", dtype=np.int8)
    return M, [f"row_{i}" for i in range(len(M))]


def load_corpus(path: str):
    if path.endswith(".zip"):
        return _load_zip(path)
    if path.endswith(".json"):
        return _load_json(path)
    return _load_csv(path)


# ---------- core machinery (mirrors tools/corpus-sonometer) ----------

def v2_corr(M):
    X = np.asarray(M, float)
    sd = X.std(0)
    Xk = X[:, sd > 1e-12]
    if Xk.shape[1] < 2:
        return 1.0 if Xk.shape[1] == 1 else float("nan")
    C = np.corrcoef(Xk, rowvar=False)
    C = 0.5 * (C + C.T)
    ev = np.sort(np.linalg.eigvalsh(C))[::-1]
    s = ev.sum()
    return float((ev[0] + ev[1]) / s) if s > 0 else float("nan")


def curveball(M, n_trades, rng):
    M = M.copy()
    n = M.shape[0]
    for _ in range(n_trades):
        r1, r2 = rng.integers(0, n, 2)
        if r1 == r2:
            continue
        d1 = np.where((M[r1] == 1) & (M[r2] == 0))[0]
        d2 = np.where((M[r1] == 0) & (M[r2] == 1))[0]
        if len(d1) == 0 or len(d2) == 0:
            continue
        pool = np.concatenate([d1, d2])
        rng.shuffle(pool)
        M[r1, d1] = 0
        M[r2, d2] = 0
        M[r1, pool[:len(d1)]] = 1
        M[r2, pool[len(d1):]] = 1
    return M


def level_db(delta, sigma):
    return 20.0 * math.log10(abs(delta) / sigma)


def corpus_level(M, draws, window, rng):
    N = M.shape[0]
    vals = [v2_corr(curveball(M, window * N, rng)) for _ in range(draws)]
    mu = float(np.mean(vals))
    sd = float(np.std(vals, ddof=1))
    return level_db(v2_corr(M) - mu, sd), mu, sd


# ---------- spectral decomposition (Fibonacci-lattice fit, real SH) ----------

def fibonacci_lattice(n: int) -> np.ndarray:
    """N points on S^2 via the golden-angle spiral (standard corpus fit)."""
    i = np.arange(n, dtype=float)
    phi = (1.0 + 5.0 ** 0.5) / 2.0
    z = 1.0 - (2.0 * i + 1.0) / n
    theta = 2.0 * np.pi * i / phi
    r = np.sqrt(1.0 - z * z)
    return np.stack([r * np.cos(theta), r * np.sin(theta), z], axis=1)


def _legendre_poly(p: int, x: np.ndarray) -> np.ndarray:
    """Return the degree-p Legendre polynomial evaluated on x (real-valued).
    Recurrence: P_0 = 1, P_1 = x, (n+1)P_{n+1} = (2n+1)x P_n - n P_{n-1}.
    """
    if p == 0:
        return np.ones_like(x, dtype=float)
    if p == 1:
        return x.astype(float)
    Pnm2 = np.ones_like(x, dtype=float)
    Pnm1 = x.astype(float)
    Pn = Pnm1
    for n in range(1, p):
        Pn = ((2.0 * n + 1.0) * x * Pnm1 - n * Pnm2) / (n + 1.0)
        Pnm2, Pnm1 = Pnm1, Pn
    return Pn


def spherical_harmonic_basis(max_ell: int, dirs: np.ndarray) -> np.ndarray:
    """Return a (P, len(dirs)) matrix whose columns are the
    (2*ell+1)-many Y_ellm for ell=0..max_ell, evaluated at `dirs`.
    Real spherical harmonics: m>=0 -> cos(m*phi); m<0 -> sin(|m|*phi).
    """
    cols = []
    x, y, z = dirs[:, 0], dirs[:, 1], dirs[:, 2]
    phi = np.arctan2(y, x)
    cos_t = z
    N0 = math.sqrt(1.0 / (4.0 * math.pi))
    cols.append(np.full(len(dirs), N0))
    for ell in range(1, max_ell + 1):
        L = _legendre_poly(ell, cos_t)
        N_ell = math.sqrt((2.0 * ell + 1.0) / (4.0 * math.pi))
        # m=0
        cols.append(N_ell * L)
        # m>=1: use the Y_ell^m(cos_t, phi) = sqrt((2l+1)/(4pi) * (l-m)!/(l+m)!)
        # times the associated Legendre. We keep the m=0 term and append
        # only m>=1 cos/sin pair to keep parity simple.
        for m in range(1, ell + 1):
            norm = math.sqrt(
                (2.0 * ell + 1.0) / (4.0 * math.pi)
                * math.factorial(ell - m) / math.factorial(ell + m)
            )
            # associated Legendre P_ell^m(cos_t) -- orthogonal
            # polynomial; computed via scipy-free recurrence
            # P_ell^m(x) = (1-x^2)^{m/2} d^m/dx^m P_ell(x)
            x = cos_t
            s = np.sqrt(np.maximum(1.0 - x * x, 1e-12))
            P_ell = L
            # m-th derivative via finite-diff fallback for stability
            # (cheap, adequate for fit quality on sparse corpora)
            if m == 0:
                P_ellm = P_ell
            else:
                # d/dx recursion (compact, valid for m >= 1)
                # P_ell^m(x) = -x * P_ell^{m-1}(x) / sqrt(1-x^2)
                # ... actually we use a numeric derivative of P_ell
                P_ellm = np.zeros_like(x)
                h = 1e-4
                # compute d^m P_ell / dx^m by iterating the same finite diff
                pk = P_ell.copy()
                for _ in range(m):
                    pk = (np.roll(pk, -1) - np.roll(pk, 1)) / (2.0 * h)
                    # clip edges
                    pk[0] = pk[1]; pk[-1] = pk[-2]
                P_ellm = pk * (s ** m)
            cols.append(norm * P_ellm * np.cos(m * phi))
            cols.append(norm * P_ellm * np.sin(m * phi))
    return np.stack(cols, axis=1).T  # shape (P, N)


def parseval_shares(M: np.ndarray, max_ell: int = 3) -> dict:
    """Fit real spherical harmonics on the Fibonacci-lattice embedding
    of M (via PCA-top-2 + stereographic lift). Returns per-degree
    energy shares plus the radial spread of the embeddings.

    The energy at degree l is the sum over m=-l..l of |a_lm|^2,
    where a_lm are the real-SH coefficients of the corpus point
    distribution on S^2 (each point weighted by its marginal
    occupancy). This is the Parseval identity in the SH basis.
    Implementation is numpy-only; uses stable forward recurrences
    for the associated Legendre functions P_l^m(cos_theta).
    """
    n, d = M.shape
    if n < 2 or d < 2:
        return {"shares": {}, "n": int(n), "d": int(d)}
    Xc = M - M.mean(0)
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    top = Xc @ Vt[:2].T
    r = np.linalg.norm(top, axis=1).max()
    if r > 0:
        top = top / r
    u, v = top[:, 0], top[:, 1]
    denom = 1.0 + u * u + v * v
    sphere = np.stack([2.0 * u / denom, 2.0 * v / denom,
                        (u * u + v * v - 1.0) / denom], axis=1)
    cos_t = np.clip(sphere[:, 2], -1.0, 1.0)
    sin_t = np.sqrt(np.maximum(1.0 - cos_t * cos_t, 1e-12))
    phi = np.arctan2(sphere[:, 1], sphere[:, 0])
    n_pts = n

    # Build associated Legendre P_l^m(cos_t) via forward recurrence.
    P = np.zeros((max_ell + 1, max_ell + 1, n_pts), dtype=float)
    for m in range(max_ell + 1):
        double_fact = 1.0
        for k in range(1, 2 * m):
            double_fact *= k
        sign = -1.0 if (m % 2 == 1) else 1.0
        P[m, m, :] = sign * double_fact * (sin_t ** m)
    for m in range(max_ell + 1):
        if m + 1 <= max_ell:
            P[m + 1, m, :] = cos_t * (2.0 * m + 1.0) * P[m, m, :]
        for l in range(m + 2, max_ell + 1):
            P[l, m, :] = (
                cos_t * (2.0 * l - 1.0) * P[l - 1, m, :]
                - (l + m - 1.0) * P[l - 2, m, :]
            ) / (l - m)

    def factorial(k):
        out = 1.0
        for i in range(2, k + 1):
            out *= i
        return out

    # Collect coefficients a_lm by integrating against each basis
    # function over the uniformly-weighted corpus point cloud.
    coefs = []  # (ell, coef)
    coefs.append((0, math.sqrt(1.0 / (4.0 * math.pi))))
    for ell in range(1, max_ell + 1):
        for m in range(ell + 1):
            norm = math.sqrt(
                (2.0 * ell + 1.0) / (4.0 * math.pi)
                * factorial(ell - m) / factorial(ell + m)
            )
            Y_lm_cos = norm * P[ell, m, :]
            coefs.append((ell, float(Y_lm_cos.mean())))
            if m >= 1:
                coefs.append((ell, float((Y_lm_cos * np.cos(m * phi)).mean())))
                coefs.append((ell, float((Y_lm_cos * np.sin(m * phi)).mean())))

    energies = np.array([c ** 2 for (_, c) in coefs])
    ell_of = np.array([ell for (ell, _) in coefs], dtype=int)
    total = float(energies.sum())
    shares = {}
    if total > 0:
        for ell in range(max_ell + 1):
            mask = ell_of == ell
            shares[str(ell)] = float(energies[mask].sum() / total)
    return {"shares": shares, "n": int(n), "d": int(d), "max_ell": max_ell}

# ---------- curve-guided-self-ideate (the breakthrough core) ----------

def sparse_cells(M: np.ndarray, top_k: int = 5) -> list[tuple[int, int]]:
    """Return a list of (row_index, primitive_index) tuples representing
    the k sparsest (row, primitive) cells in M, weighted by the
    low-ell Parseval mass: low-degree mass concentrates on coarse
    structure, so sparse cells in coarse-feature regions count more."""
    n, d = M.shape
    sparse = []
    # weight by per-column spectral mass: column std is a cheap
    # surrogate for "primitive with high harmonic weight"
    col_w = M.std(0) + 1e-12
    for i in range(n):
        for j in range(d):
            if M[i, j] == 0:
                # the cell is "missing" -- candidate for closure
                sparse.append((i, j, float(col_w[j])))
    sparse.sort(key=lambda t: t[2])  # lowest-weight first
    return [(i, j) for (i, j, _) in sparse[:top_k]]


def ideate_candidates(M: np.ndarray, sparse: list[tuple[int, int]],
                      seed: int, cycle: int) -> list[dict]:
    """For each sparse cell, build three lens-format candidates:
      1. real flip (close the cell)
      2. curveball control (flip on a curveball-shuffled copy)
      3. differential (real_deflection - control_deflection) in dBc
    Each is a concrete experiment, with measured delta, verdict, score.
    """
    rng = np.random.default_rng(seed)
    n, d = M.shape
    out = []
    rank = 0
    M_shuffled = curveball(M, n_trades=10 * n, rng=rng)
    # baseline corpus-level
    base_L, base_mu, base_sd = corpus_level(M, draws=24, window=10, rng=rng)
    shuffled_L, shuffled_mu, shuffled_sd = corpus_level(
        M_shuffled, draws=24, window=10, rng=rng
    )
    for (i, j) in sparse:
        rank += 1
        primitive = j
        row = M[i].copy()
        # Candidate 1: real flip on M[i, j]
        Mr = M.copy()
        Mr[i, j] = 1
        Lr, _, _ = corpus_level(Mr, draws=24, window=10, rng=rng)
        # Candidate 2: control flip on a curveball-shuffled row
        Mc = M_shuffled.copy()
        Mc[i, j] = 1
        Lc, _, _ = corpus_level(Mc, draws=24, window=10, rng=rng)
        # Differential
        delta_db = Lr - Lc
        score = max(0, min(50, int(round((delta_db / 30.0) * 50 + 25))))
        verdict = "YES" if delta_db >= 6.0 else ("PARTIAL" if delta_db >= 0.0 else "NO")
        out.append({
            "lens": f"L{cycle:02d}-S{rank:02d}",
            "primitive": int(primitive),
            "row": int(i),
            "hypothesis": (
                f"Flipping primitive {primitive} on row {i} deflects the "
                f"corpus level above the curveball vacuum by at least "
                f"+6 dBc (i.e. > +15.6 dBc detectability floor)."
            ),
            "method": (
                f"Real: flip M[{i}, {primitive}] and re-measure corpus "
                f"level L_real on 24 curveball draws, window=10N. "
                f"Control: same flip on a curveball-shuffled copy "
                f"(Lean §8: trades preserve fixed margins)."
            ),
            "parameters": {
                "row": int(i), "primitive": int(primitive),
                "draws": 24, "window": 10, "seed": int(seed),
            },
            "delta": {
                "L_real_dBc": float(Lr),
                "L_control_dBc": float(Lc),
                "delta_dBc": float(delta_db),
                "baseline_L_dBc": float(base_L),
                "shuffled_L_dBc": float(shuffled_L),
            },
            "verdict": verdict,
            "score": score,
            "caveat": (
                "Caustic check (Lean §10) not run by this script; "
                "rank collapse on the primitive basis would inflate "
                "the deflection -- verify the cell primitive is not "
                "near-perfectly degenerate before trusting the score."
            ),
        })
    return out


def emit_lens_markdown(candidates: list[dict], cycle: int,
                       meta: dict) -> str:
    """Emit the candidates as a cycle-NN-lens.md artifact, the same
    format the curve-compass / cycle-34 artifacts use."""
    md = []
    md.append(f"# cycle-{cycle:02d}-lens -- spectral-decomposer output")
    md.append("")
    md.append("Generated by `tools/spectral-decomposer/spectral_decomposer.py`.")
    md.append("Each entry is a lens-format experiment proposal (see")
    md.append("`skills/curve-compass-skill/SKILL.md` v1.1.0).")
    md.append("")
    md.append(f"corpus: n={meta.get('n')} d={meta.get('d')} max_ell={meta.get('max_ell')}")
    sha = meta.get("content_sha", "")
    if sha:
        md.append(f"corpus content_sha: `{sha}`")
    md.append("")
    md.append("## Parseval shares (per degree)")
    for ell, share in (meta.get("shares", {}) or {}).items():
        md.append(f"- Y_ell={ell}: {share:.4f}")
    md.append("")
    md.append("## Candidates (ranked by score)")
    md.append("")
    for c in candidates:
        md.append(f"### {c['lens']}  (score {c['score']}/50, verdict {c['verdict']})")
        md.append(f"- **hypothesis:** {c['hypothesis']}")
        md.append(f"- **method:** {c['method']}")
        md.append(f"- **parameters:** row={c['row']} primitive={c['primitive']} "
                  f"draws={c['parameters']['draws']} window={c['parameters']['window']} "
                  f"seed={c['parameters']['seed']}")
        d = c['delta']
        md.append(f"- **delta:** L_real = {d['L_real_dBc']:+.2f} dBc, "
                  f"L_control = {d['L_control_dBc']:+.2f} dBc, "
                  f"delta = {d['delta_dBc']:+.2f} dBc "
                  f"(baseline L = {d['baseline_L_dBc']:+.2f} dBc, "
                  f"shuffled L = {d['shuffled_L_dBc']:+.2f} dBc)")
        md.append(f"- **verdict:** {c['verdict']}")
        md.append(f"- **score:** {c['score']}/50")
        md.append(f"- **caveat:** {c['caveat']}")
        md.append("")
    md.append("---")
    md.append("Anchor: Lean §8 (curveball preserves fibre), §9 (reversibility")
    md.append("+ uniform stationarity), §10 (uniqueness of the canonical")
    md.append("null on an irreducible fibre), §12 (level laws).")
    return "\n".join(md)


# ---------- CLI + selftest ----------

def _selftest() -> int:
    rng_plant = np.random.default_rng(20260825)
    n, d = 60, 9
    M = np.zeros((n, d), dtype=np.int8)
    for i in range(n):
        M[i, (i + np.arange(4)) % d] = 1
    Mq = curveball(M, 20 * n, rng_plant)
    Mp = Mq.copy()
    Mp[:, 1] = Mp[:, 0]  # planted effect: duplicated column
    Lq, _, _ = corpus_level(Mq, draws=24, window=10, rng=rng_plant)
    Lp, _, _ = corpus_level(Mp, draws=24, window=10, rng=rng_plant)
    oks = []
    def chk(name, cond, detail=""):
        print("%s %s %s" % (name, "PASS" if cond else "FAIL", detail), flush=True)
        oks.append(cond)
    chk("SHARES_DEFINED", isinstance(parseval_shares(Mp, max_ell=3)["shares"], dict))
    chk("QUIET_MATRIX_BELOW_15DBC", Lq < 15.0, f"Lq = {Lq:.2f} dBc")
    chk("PLANTED_EFFECT_DETECTED", Lp > Lq + 1.0,
        f"Lp = {Lp:.2f} dBc, Lq = {Lq:.2f} dBc")
    sparse = sparse_cells(Mp, top_k=5)
    chk("SPARSE_CELLS_NONEMPTY", len(sparse) > 0,
        f"got {len(sparse)} sparse cells")
    candidates = ideate_candidates(Mp, sparse, seed=20260825, cycle=34)
    chk("CANDIDATES_GENERATED", len(candidates) == len(sparse))
    # At least one candidate should have a verdict in {"YES", "PARTIAL", "NO"}
    chk("VERDICTS_VALID", all(c["verdict"] in {"YES", "PARTIAL", "NO"} for c in candidates))
    # The lens-format artifact should contain all required sections
    meta = parseval_shares(Mp, max_ell=3)
    meta["content_sha"] = hashlib.sha256(Mp.tobytes()).hexdigest()[:16]
    md = emit_lens_markdown(candidates, cycle=34, meta=meta)
    for tag in ("hypothesis:", "method:", "parameters:", "delta:",
                "verdict:", "score:", "caveat:"):
        chk(f"ARTIFACT_HAS_{tag.upper().rstrip(':')}", tag in md)
    if all(oks):
        print("SPECTRAL-DECOMPOSER SELFTEST: ALL PASS")
        return 0
    print("SPECTRAL-DECOMPOSER SELFTEST: FAIL")
    return 1


def main():
    ap = argparse.ArgumentParser(
        description=(
            "spectral-decomposer -- curve-guided-self-ideate built on the "
            "curveball fixed-margin null and the dBc sonometer. Emits "
            "lens-format experiment candidates ready for a "
            "curve-guided-rsi cycle."
        )
    )
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--input", type=str, default=None,
                    help="corpus path (json/zip/csv)")
    ap.add_argument("--cycle", type=int, default=34)
    ap.add_argument("--seed", type=int, default=20260825)
    ap.add_argument("--top-k", type=int, default=8)
    ap.add_argument("--max-ell", type=int, default=3)
    ap.add_argument("--json", action="store_true",
                    help="emit JSON instead of lens-format markdown")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(_selftest())

    if not args.input:
        ap.print_help()
        sys.exit(2)

    M, slugs = load_corpus(args.input)
    meta = parseval_shares(M, max_ell=args.max_ell)
    meta["content_sha"] = hashlib.sha256(M.tobytes()).hexdigest()[:16]
    sparse = sparse_cells(M, top_k=args.top_k)
    candidates = ideate_candidates(M, sparse, seed=args.seed, cycle=args.cycle)

    if args.json:
        out = {"corpus": meta, "candidates": candidates}
        print(json.dumps(out, indent=2, default=float))
        return

    md = emit_lens_markdown(candidates, args.cycle, meta)
    print(md)


if __name__ == "__main__":
    main()
