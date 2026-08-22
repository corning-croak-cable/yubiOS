#!/usr/bin/env python3
"""
auditor.py -- self-contained numpy-only CLI that audits a binary coverage
matrix (rows x columns of 0/1) with the repo's null-standardized
"is-this-x" methodology: real V2 (top-2 eigenvalue share of the
correlation matrix) vs. a curveball (Strona trade) null, plus two
secondary nulls (column-permutation and iid Bernoulli) for context.

v2_corr and curveball are copied verbatim from papers/data/lean/verify_claims.py
to preserve fidelity with the repo's published methodology.
"""
import argparse
import json
import sys
import zipfile

import numpy as np

DEFAULT_SEED = 20260822


# ---------------------------------------------------------------------------
# Copied verbatim from papers/data/lean/verify_claims.py (do not modify: the
# published numbers this tool reproduces depend on these exact definitions).
# ---------------------------------------------------------------------------
def v2_corr(M):
    X = np.asarray(M, float)
    sd = X.std(0)
    Xk = X[:, sd > 1e-12]
    C = np.corrcoef(Xk, rowvar=False)
    C = 0.5 * (C + C.T)
    ev = np.sort(np.linalg.eigvalsh(C))[::-1]
    return float((ev[0] + ev[1]) / ev.sum())


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


# ---------------------------------------------------------------------------
# Secondary nulls (not in verify_claims.py, added here for context).
# ---------------------------------------------------------------------------
def column_permutation_null(M, rng):
    """Independently shuffle each column -- destroys all row structure and
    all column-column dependence while keeping each column's marginal
    (count of 1s) exactly fixed."""
    M = M.copy()
    for j in range(M.shape[1]):
        rng.shuffle(M[:, j])
    return M


def iid_bernoulli_null(M, rng):
    """Column-matched independent Bernoulli draws: each column's 1-rate is
    matched to the real data's column mean, but rows and columns are fully
    independent (no fixed margins at all)."""
    n = M.shape[0]
    p = M.mean(0)
    return (rng.random((n, M.shape[1])) < p).astype(np.int8)


# ---------------------------------------------------------------------------
# Input loading
# ---------------------------------------------------------------------------
def load_matrix_from_json(obj):
    if isinstance(obj, list):
        return np.array(obj, dtype=np.int8)
    if isinstance(obj, dict) and "rows" in obj:
        return np.array([r["covered"] for r in obj["rows"]], dtype=np.int8)
    raise ValueError(
        "Unrecognized JSON input: expected a plain 2D array, or an object "
        "with a 'rows' key whose entries have a 'covered' list."
    )


def load_matrix(path):
    if path.lower().endswith(".json"):
        with open(path) as f:
            obj = json.load(f)
        M = load_matrix_from_json(obj)
    elif path.lower().endswith(".csv"):
        M = np.loadtxt(path, delimiter=",", dtype=np.int8)
        if M.ndim == 1:
            M = M.reshape(1, -1)
    else:
        raise ValueError("Input file must end in .csv or .json")

    if M.ndim != 2:
        raise ValueError("Input matrix must be 2-dimensional (rows x columns)")
    if not np.isin(M, [0, 1]).all():
        raise ValueError("Input matrix must be binary (0/1 entries only)")
    return M


# ---------------------------------------------------------------------------
# Core audit
# ---------------------------------------------------------------------------
def run_audit(M, nsamp, trades_per_row, seed):
    n = M.shape[0]
    v2_real = v2_corr(M)

    rng = np.random.default_rng(seed)
    curveball_vals = [
        v2_corr(curveball(M, trades_per_row * n, rng)) for _ in range(nsamp)
    ]
    cb_mean = float(np.mean(curveball_vals))
    cb_sd = float(np.std(curveball_vals, ddof=1)) if nsamp > 1 else float("nan")

    dv2 = v2_real - cb_mean
    z = dv2 / cb_sd if cb_sd and cb_sd > 0 else float("nan")

    colperm_vals = [v2_corr(column_permutation_null(M, rng)) for _ in range(nsamp)]
    colperm_mean = float(np.mean(colperm_vals))

    iid_vals = [v2_corr(iid_bernoulli_null(M, rng)) for _ in range(nsamp)]
    iid_mean = float(np.mean(iid_vals))

    if abs(z) > 3:
        verdict = "SIGNAL"
    else:
        verdict = "NULL-COMPATIBLE"

    return {
        "n_rows": int(M.shape[0]),
        "n_cols": int(M.shape[1]),
        "v2_real": v2_real,
        "curveball_null_mean": cb_mean,
        "curveball_null_sd": cb_sd,
        "delta_v2": dv2,
        "z": z,
        "column_permutation_null_mean": colperm_mean,
        "iid_bernoulli_null_mean": iid_mean,
        "nsamp": nsamp,
        "trades_per_row": trades_per_row,
        "seed": seed,
        "verdict": verdict,
    }


def format_human(result):
    lines = []
    lines.append("Corpus Auditor -- null-standardized coverage-matrix report")
    lines.append("=" * 60)
    lines.append(f"matrix:              {result['n_rows']} rows x {result['n_cols']} cols")
    lines.append(f"real V2:             {result['v2_real']:.10f}")
    if result["v2_real"] >= 1.0 - 1e-9:
        lines.append(
            "  ** WARNING: V2 is exactly 1.0000 -- this usually indicates rank "
            "degeneracy (e.g. too few independent columns, or near-duplicate "
            "columns), not a genuine strong effect. Investigate before trusting "
            "the verdict below. **"
        )
    lines.append(
        f"curveball null:      {result['curveball_null_mean']:.6f} "
        f"+/- {result['curveball_null_sd']:.6f}  "
        f"(nsamp={result['nsamp']}, trades_per_row={result['trades_per_row']})"
    )
    lines.append(f"delta V2:            {result['delta_v2']:+.6f}")
    lines.append(f"z:                   {result['z']:+.2f}")
    lines.append(f"column-perm null:    {result['column_permutation_null_mean']:.6f}  (per-column independent shuffles)")
    lines.append(f"iid Bernoulli null:  {result['iid_bernoulli_null_mean']:.6f}  (column-matched independent draws)")
    lines.append("-" * 60)
    lines.append(f"VERDICT: {result['verdict']}")
    if result["verdict"] == "SIGNAL":
        lines.append(
            "  |z| > 3: the real matrix's V2 is not compatible with the "
            "curveball (fixed-margin) null at this threshold."
        )
    else:
        lines.append(
            "  |z| <= 3: not distinguishable from the curveball null at this "
            "threshold."
        )
    lines.append(
        "NOTE: z from a finite Monte Carlo null is over-dispersed relative to "
        "a naive normal reference (see the repo's papers/ for discussion). "
        "Treat 2 < |z| < 4 as inconclusive, not decisive, in either direction."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def selftest():
    ZIP_PATH = "papers/is-this-x-2026-08-12-Final.zip"
    MEMBER = "is-this-x-2026-08-12/data/real/per_row_coverage_v3.json"
    try:
        with zipfile.ZipFile(ZIP_PATH) as z:
            with z.open(MEMBER) as f:
                obj = json.load(f)
    except FileNotFoundError:
        print(
            f"SELFTEST FAIL: could not find {ZIP_PATH} -- run this from the "
            "repo root.",
            file=sys.stderr,
        )
        return 1

    M = load_matrix_from_json(obj)
    assert M.shape == (2286, 9), f"unexpected shape {M.shape}"

    v2_real = v2_corr(M)
    ok1 = abs(v2_real - 0.7235293730732693) < 1e-9

    rng = np.random.default_rng(DEFAULT_SEED)
    n = M.shape[0]
    vals = [v2_corr(curveball(M, 20 * n, rng)) for _ in range(40)]
    mu = float(np.mean(vals))
    sd = float(np.std(vals, ddof=1))
    dv2 = v2_real - mu
    z = dv2 / sd

    ok2 = z > 6
    ok3 = 0.005 < dv2 < 0.025

    print(f"real V2 = {v2_real!r} (expected 0.7235293730732693, match={ok1})")
    print(f"curveball null = {mu:.6f} +/- {sd:.6f}, dV2 = {dv2:+.4f}, z = {z:+.2f}")
    print(f"(published: null 0.709180 +/- 0.001183, z=+12.13)")
    print(f"z > 6: {ok2}; 0.005 < dV2 < 0.025: {ok3}")

    if ok1 and ok2 and ok3:
        print("SELFTEST: PASS")
        return 0
    print("SELFTEST: FAIL")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser():
    p = argparse.ArgumentParser(
        prog="auditor.py",
        description=(
            "Audit a binary coverage matrix against a curveball (fixed-margin) "
            "null using the repo's V2 (top-2 correlation-eigenvalue share) "
            "methodology."
        ),
    )
    p.add_argument("--input", help="CSV (0/1 rows x columns) or JSON input file")
    p.add_argument("--nsamp", type=int, default=50, help="null samples to draw (default 50)")
    p.add_argument("--trades-per-row", type=int, default=20, help="curveball trades per row per null sample (default 20)")
    p.add_argument("--seed", type=int, default=DEFAULT_SEED, help="RNG seed (default 20260822)")
    p.add_argument("--json", action="store_true", help="emit machine-readable JSON instead of the human report")
    p.add_argument("--selftest", action="store_true", help="run the built-in reproduction check against the published corpus and exit")
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.selftest:
        sys.exit(selftest())

    if not args.input:
        parser.error("--input is required (unless --selftest is given)")

    try:
        M = load_matrix(args.input)
    except (ValueError, OSError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)

    result = run_audit(M, args.nsamp, args.trades_per_row, args.seed)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_human(result))

    sys.exit(0)


if __name__ == "__main__":
    main()
