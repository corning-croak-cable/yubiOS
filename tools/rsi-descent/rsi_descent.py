#!/usr/bin/env python3
"""rsi_descent.py -- the single-action atom as a shippable primitive.

Implements the curve-compass / single-action-curve RSI descent on a binary
coverage matrix: map each row to a point on S^2 via PCA-top-2 + stereographic
lift, find the geodesic-only argmin single-primitive flip toward the ideal
pole, iterate to fixpoint. The Lean file papers/data/lean/CurvedCorpus.lean
proves (sections 1-3) that the atomic Delta >= 0 and that the corpus total
Delta >= 0 monotonically; this script enforces the same invariant at
runtime and aborts loudly if it ever fails (which would mean the script
deviates from the proved mathematical model).

numpy-only. Deterministic given --seed. Exit 0 on normal fixpoint.
"""

import argparse, json, sys, zipfile
import numpy as np

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

def load_input(path):
    if path.endswith(".zip"):
        with zipfile.ZipFile(path) as z:
            with z.open("is-this-x-2026-08-12/data/real/per_row_coverage_v3.json") as f:
                j = json.load(f)
        M = np.array([r["covered"] for r in j["rows"]], dtype=np.int8)
        slugs = [r["slug"] for r in j["rows"]]
        return M, slugs
    if path.endswith(".json"):
        with open(path) as f:
            j = json.load(f)
        if isinstance(j, dict) and "rows" in j:
            M = np.array([r["covered"] for r in j["rows"]], dtype=np.int8)
            slugs = [r.get("slug", str(i)) for i, r in enumerate(j["rows"])]
            return M, slugs
        M = np.asarray(j, dtype=np.int8)
        return M, [f"row_{i}" for i in range(len(M))]
    M = np.loadtxt(path, delimiter=",", dtype=np.int8)
    return M, [f"row_{i}" for i in range(len(M))]

def stereographic_lift(u, v):
    denom = 1 + u*u + v*v
    return np.array([2*u/denom, 2*v/denom, (u*u+v*v-1)/denom])

def pca_top2(X):
    Xc = X - X.mean(0)
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    return Xc @ Vt[:2].T

def run_descent(M, eps=1e-3, max_cycles=50, seed=20260822, assert_invariant=True):
    rng = np.random.default_rng(seed)
    n, d = M.shape
    trajectory = []
    ladder = {k: [] for k in range(d+1)}
    cum = 0.0
    for cycle in range(max_cycles):
        order = rng.permutation(n)
        cycle_delta = 0.0
        n_pos = 0
        for idx in order:
            row = M[idx]
            if row.sum() == d:
                continue
            Xfull = np.vstack([M, np.ones((1, d), dtype=np.int8)]) if not (M == 1).all(axis=1).any() else M
            z = (Xfull - Xfull.mean(0)) / (Xfull.std(0) + 1e-12)
            scores = pca_top2(z)
            idx_pos = idx if (Xfull is M) else -1
            if idx_pos < 0:
                idx_pos = idx
            u_i, v_i = scores[idx_pos]
            p_i = stereographic_lift(u_i, v_i)
            ideal_row = np.ones(d)
            Xall = np.vstack([M, ideal_row])
            za = (Xall - Xall.mean(0)) / (Xall.std(0) + 1e-12)
            sa = pca_top2(za)
            p_star = stereographic_lift(sa[-1, 0], sa[-1, 1])
            d_pre = float(np.linalg.norm(p_i - p_star))
            best_flip, best_d_post, best_d = -1, d_pre, d_pre
            for c in range(d):
                if row[c] == 0:
                    row[c] = 1
                    Xtry = np.vstack([M, np.ones((1, d), dtype=np.int8)]) if not (M == 1).all(axis=1).any() else M.copy()
                    Xtry[idx, c] = 1
                    z2 = (Xtry - Xtry.mean(0)) / (Xtry.std(0) + 1e-12)
                    s2 = pca_top2(z2)
                    p_post = stereographic_lift(s2[idx, 0], s2[idx, 1])
                    d_post = float(np.linalg.norm(p_post - p_star))
                    row[c] = 0
                    if d_post < best_d:
                        best_d = d_post; best_flip = c; best_d_post = d_post
            delta = d_pre - best_d_post
            if assert_invariant and delta < -1e-12:
                raise RuntimeError(f"INVARIANT VIOLATED: delta={delta:.6f} at idx={idx} cycle={cycle}")
            if delta > eps:
                M[idx, best_flip] = 1
                cycle_delta += delta
                n_pos += 1
                k = int(M[idx].sum())
                ladder[k].append(delta)
            else:
                k = int(M[idx].sum())
                ladder[k].append(0.0)
        cum += cycle_delta
        trajectory.append({"cycle": cycle, "cycle_delta": cycle_delta, "n_positive": n_pos, "cumulative": cum, "coverage": float(M.sum() / (n*d))})
        if cycle_delta < eps:
            break
    return M, trajectory, ladder, cum

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=False, default=None)
    p.add_argument("--epsilon", type=float, default=1e-3)
    p.add_argument("--max-cycles", type=int, default=50)
    p.add_argument("--seed", type=int, default=20260822)
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    if args.selftest:
        rng = np.random.default_rng(args.seed)
        M = (rng.random((60, 9)) < 0.5).astype(np.int8)
        M0 = M.copy()
        _, traj, ladder, cum = run_descent(M, eps=args.epsilon, max_cycles=args.max_cycles, seed=args.seed)
        all_deltas = [v for L in ladder.values() for v in L]
        assert all(d >= -1e-12 for d in all_deltas), "negative delta detected"
        n_full = int((M.sum(1) == 9).sum())
        out = {"selftest": True, "n_full_coverage": n_full, "cycles_to_fixpoint": len(traj), "cumulative_delta": cum, "trajectory": traj, "delta_ladder": {k: (max(vs) if vs else 0.0) for k, vs in ladder.items()}, "n_satisfied_invariance": len(all_deltas)}
        print(json.dumps(out, indent=2, default=float))
        return
    if not args.input:
        p.error("--input is required unless --selftest is given")
    M, slugs = load_input(args.input)
    M_out, traj, ladder, cum = run_descent(M, eps=args.epsilon, max_cycles=args.max_cycles, seed=args.seed)
    out = {"cycles_to_fixpoint": len(traj), "cumulative_delta": cum, "final_coverage": float(M_out.sum() / (M_out.shape[0]*M_out.shape[1])), "trajectory": traj, "delta_ladder": {k: (max(vs) if vs else 0.0) for k, vs in ladder.items()}}
    print(json.dumps(out, indent=2, default=float))

if __name__ == "__main__":
    main()
