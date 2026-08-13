#!/usr/bin/env python3
"""G1 — closed-form spherical defocus check.

Two legs:
  LEG 1 (semigroup identity): on a Fibonacci lattice, verify
      E[Y_lm(B_t^x)] = exp(-l(l+1)t) * Y_lm(x)
  by explicit Brownian simulation on S^2, per degree l, at several t.

  LEG 2 (real corpus): load the 2286x9 coverage matrix, reproduce the
  paper pipeline (z-score -> PCA top-2 -> RMS rescale -> stereographic
  lift), fit the 16 real SH (L=3) ridge, compute per-degree Parseval
  energies; diffuse the POINT POSITIONS by Brownian motion, refit, and
  compare measured per-degree energy decay against the closed form
  exp(-2*l(l+1)*t), which holds for the mean coefficients up to an
  incoherent-noise floor.

Seed 20260813. numpy only.
"""
import json, math, sys
import numpy as np

rng = np.random.default_rng(20260813)

# ---------- real spherical harmonics, L=3 (16 fns), orthonormal on S^2 ----------
def real_sh_16(xyz):
    x, y, z = xyz[:, 0], xyz[:, 1], xyz[:, 2]
    r2 = x*x + y*y + z*z
    # guard: inputs are unit vectors
    c = lambda v: v
    out = np.empty((xyz.shape[0], 16))
    ls = []
    # l=0
    out[:, 0] = 0.5 / math.sqrt(math.pi); ls.append(0)
    # l=1: Y_{1,-1}, Y_{1,0}, Y_{1,1}
    k1 = math.sqrt(3.0 / (4.0 * math.pi))
    out[:, 1] = k1 * y; out[:, 2] = k1 * z; out[:, 3] = k1 * x
    ls += [1, 1, 1]
    # l=2
    out[:, 4] = 0.5 * math.sqrt(15.0/math.pi) * x * y
    out[:, 5] = 0.5 * math.sqrt(15.0/math.pi) * y * z
    out[:, 6] = 0.25 * math.sqrt(5.0/math.pi) * (3.0*z*z - r2)
    out[:, 7] = 0.5 * math.sqrt(15.0/math.pi) * x * z
    out[:, 8] = 0.25 * math.sqrt(15.0/math.pi) * (x*x - y*y)
    ls += [2]*5
    # l=3
    out[:, 9]  = 0.25 * math.sqrt(35.0/(2.0*math.pi)) * y * (3.0*x*x - y*y)
    out[:, 10] = 0.5  * math.sqrt(105.0/math.pi) * x * y * z
    out[:, 11] = 0.25 * math.sqrt(21.0/(2.0*math.pi)) * y * (5.0*z*z - r2)
    out[:, 12] = 0.25 * math.sqrt(7.0/math.pi) * z * (5.0*z*z - 3.0*r2)
    out[:, 13] = 0.25 * math.sqrt(21.0/(2.0*math.pi)) * x * (5.0*z*z - r2)
    out[:, 14] = 0.25 * math.sqrt(105.0/math.pi) * (x*x - y*y) * z
    out[:, 15] = 0.25 * math.sqrt(35.0/(2.0*math.pi)) * x * (x*x - 3.0*y*y)
    ls += [3]*7
    return out, np.array(ls)

def fibonacci_lattice(N):
    i = np.arange(N)
    z = 1.0 - (2.0*i + 1.0)/N
    phi_g = (1.0 + math.sqrt(5.0))/2.0
    phi = 2.0*math.pi * i / phi_g
    s = np.sqrt(np.maximum(0.0, 1.0 - z*z))
    return np.stack([s*np.cos(phi), s*np.sin(phi), z], axis=1)

def brownian_step_batch(X, t_total, n_steps, rng):
    """Euler-Maruyama Brownian motion on S^2 (tangent noise + renormalize)."""
    dt = t_total / n_steps
    X = X.copy()
    for _ in range(n_steps):
        xi = rng.normal(size=X.shape)
        # project to tangent space
        xi -= (np.sum(xi*X, axis=1, keepdims=True)) * X
        X = X + math.sqrt(2.0*dt) * xi   # generator = Laplace-Beltrami (factor-2 convention: e^{t*Delta})
        X /= np.linalg.norm(X, axis=1, keepdims=True)
    return X

# NOTE on convention: with dX = sqrt(2) dB_tangent the generator is Delta (not Delta/2),
# so E[Y_lm(X_t)] = exp(-l(l+1) t) Y_lm(X_0). This matches the heat kernel e^{t Delta}.

# ---------------- LEG 1: semigroup identity ----------------
def leg1():
    N = 2048
    X0 = fibonacci_lattice(N)
    Y0, ls = real_sh_16(X0)
    ts = [0.01, 0.05, 0.1, 0.2]
    reps = 48
    rows = []
    for t in ts:
        acc = np.zeros_like(Y0)
        for r in range(reps):
            Xt = brownian_step_batch(X0, t, max(40, int(t*400)), rng)
            Yt, _ = real_sh_16(Xt)
            acc += Yt
        Ymean = acc / reps
        for l in [1, 2, 3]:
            sel = ls == l
            # regression slope of E[Y(X_t)] on Y(X_0), pooled over modes of degree l
            num = np.sum(Ymean[:, sel] * Y0[:, sel])
            den = np.sum(Y0[:, sel] * Y0[:, sel])
            measured = num / den
            predicted = math.exp(-l*(l+1)*t)
            rows.append((t, l, measured, predicted, measured/predicted))
    print("LEG1 semigroup identity  (measured decay vs exp(-l(l+1)t), pooled regression, reps=%d, N=%d)" % (reps, N))
    print("   t      l   measured   predicted   ratio")
    for t, l, m, p, q in rows:
        print(f"  {t:5.2f}  {l}   {m:8.5f}   {p:8.5f}   {q:6.3f}")
    return rows

# ---------------- LEG 2: real corpus ----------------
def paper_pipeline(M):
    # z-score columns (columns with zero variance -> drop from z-scoring, keep as 0)
    mu = M.mean(axis=0); sd = M.std(axis=0)
    sd[sd == 0] = 1.0
    Z = (M - mu) / sd
    # PCA top-2 via SVD
    U, S, Vt = np.linalg.svd(Z - Z.mean(axis=0), full_matrices=False)
    uv = U[:, :2] * S[:2]
    # RMS rescale
    rms = np.sqrt(np.mean(np.sum(uv**2, axis=1)))
    uv = uv / rms
    # stereographic lift
    u, v = uv[:, 0], uv[:, 1]
    d = 1.0 + u*u + v*v
    X = np.stack([2*u/d, 2*v/d, (u*u + v*v - 1.0)/d], axis=1)
    return Z, X

def parseval_energies(X, Z, lam=1e-3):
    B, ls = real_sh_16(X)
    G = B.T @ B + lam*np.eye(16)
    C = np.linalg.solve(G, B.T @ Z)
    Bn2 = np.sum(B*B, axis=0)          # ||B_(lm)||^2
    Cn2 = np.sum(C*C, axis=1)          # ||C_(lm)||^2
    E = Bn2 * Cn2
    El = np.array([E[ls == l].sum() for l in range(4)])
    return E, El, ls

def leg2(path):
    raw = json.load(open(path))
    rows = raw["rows"] if isinstance(raw, dict) else raw
    if isinstance(rows[0], dict):
        M = np.array([r["covered"] for r in rows], dtype=float)
    else:
        M = np.array(rows, dtype=float)
    print(f"\nLEG2 real corpus: matrix {M.shape}")
    Z, X0 = paper_pipeline(M)
    E0, El0, ls = parseval_energies(X0, Z)
    tot0 = El0.sum()
    print("  t=0 per-degree energy shares:", np.array2string(El0/tot0, precision=4))
    ts = [0.005, 0.02, 0.05, 0.1]
    reps = 12
    print("   t      l   measured E_l(t)/E_l(0)   closed form e^{-2l(l+1)t}")
    results = []
    for t in ts:
        ratios = np.zeros(4); 
        for r in range(reps):
            Xt = brownian_step_batch(X0, t, max(40, int(t*800)), rng)
            _, Elt, _ = parseval_energies(Xt, Z)
            ratios += Elt / np.maximum(El0, 1e-300)
        ratios /= reps
        for l in [1, 2, 3]:
            pred = math.exp(-2*l*(l+1)*t)
            results.append((t, l, ratios[l], pred))
            print(f"  {t:5.3f}  {l}   {ratios[l]:10.4f}               {pred:8.4f}")
    return El0/tot0, results

if __name__ == "__main__":
    leg1_rows = leg1()
    shares0, leg2_rows = leg2(sys.argv[1])
    out = {
        "seed": 20260813,
        "leg1": [{"t": t, "l": l, "measured": m, "predicted": p, "ratio": q} for t, l, m, p, q in leg1_rows],
        "leg2_shares_t0": shares0.tolist(),
        "leg2": [{"t": t, "l": l, "measured_ratio": m, "closed_form": p} for t, l, m, p in leg2_rows],
    }
    json.dump(out, open("session/g1/g1-results.json", "w"), indent=1)
    print("\nsaved session/g1/g1-results.json")
