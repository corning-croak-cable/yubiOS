#!/usr/bin/env python3
"""gapD_lens_power.py -- Gap D: "power the lens" experiment.

Optimizes the previously-frozen Mobius chart phi_theta that reparameterizes
the S^2 domain (sphere -> stereographic C -> Mobius -> sphere) used ahead of
the 16-real-spherical-harmonic (L<=3) ridge fit on the Vogel/Fibonacci
golden-angle lattice. In every prior run in this repo's papers, phi_theta was
frozen at the identity Mobius map ("unpowered lens"). This script asks
whether *optimizing* phi_theta over its 6 real degrees of freedom can
concentrate a planted target family's spectral energy in the target (L=3)
harmonic block, relative to a matched pure-noise null evaluated under the
SAME phi_theta -- while an anti-caustic guard rejects any phi_theta that
makes the 16-column design matrix numerically singular or ill-conditioned.

Dependencies: Python stdlib + numpy ONLY (no scipy). Deterministic given a
seed (default 20260822).

Fidelity note on the planted-field generator
---------------------------------------------
This experiment fits a CONTINUOUS scalar field on the lattice (not the
binary standard-candle corpus of
papers/is-this-x-2026-08-12-Final.zip:.../curved-corpus-create/scripts/create_corpus.py),
because Gap D's objective needs a directly-fittable real-valued target for
the ridge regression. We reuse that script's frozen geometry EXACTLY
(Fibonacci golden-angle lattice fibonacci_sphere, and the real SH basis
real_sh_basis, both copied verbatim below with the same column order and
constants, including the corrected Y_3^3 constant K = sqrt(70/(64*pi))).
The planting itself is simplified relative to create_corpus.py's logistic
column-loading scheme: instead of a binary matrix with sigmoid-linked
columns, we plant a single continuous field

    y_i = s * combo(x_i) + noise_i,      noise_i ~ N(0, 1) iid,  s = 1

where combo(x_i) is a fixed, standardized combination of two L=3 real SH
probe channels (Y_3^3 and Y_3^{-3}, i.e. basis columns 15 and 9, the same
"channel 0 / channel 1" probes create_corpus.py uses for its planted
corpora), and the matched null replaces combo(x_i) with 0 (pure iid
N(0,1) noise, same lattice, no planted structure). This keeps the frozen
geometry and basis identical to the papers while giving Gap D a target
that is directly Parseval-decomposable against the L=3 harmonic block.

Usage:
    python3 gapD_lens_power.py --out gapD-results.json --seed 20260822
"""

import argparse
import json
import math
import time

import numpy as np

PHI_GOLDEN = (1.0 + math.sqrt(5.0)) / 2.0
RIDGE_LAMBDA = 1e-3
SH_L = 3
SH_NFUNCS = 16
L3_COLS = list(range(9, 16))
K_Y33 = math.sqrt(70.0 / (64.0 * math.pi))


def fibonacci_sphere(n):
    i = np.arange(n, dtype=float)
    z = 1.0 - (2.0 * i + 1.0) / float(n)
    z = np.clip(z, -1.0, 1.0)
    phi = (2.0 * math.pi * i) / PHI_GOLDEN
    r = np.sqrt(np.maximum(0.0, 1.0 - z * z))
    xyz = np.stack([r * np.cos(phi), r * np.sin(phi), z], axis=1)
    theta = np.arccos(z)
    return xyz, theta, np.mod(phi, 2.0 * math.pi)


def real_sh_basis(xyz):
    x, y, z = xyz[:, 0], xyz[:, 1], xyz[:, 2]
    cols = [
        np.full_like(x, 0.5 * math.sqrt(1.0 / math.pi)),
        math.sqrt(3.0 / (4.0 * math.pi)) * y,
        math.sqrt(3.0 / (4.0 * math.pi)) * z,
        math.sqrt(3.0 / (4.0 * math.pi)) * x,
        0.5 * math.sqrt(15.0 / math.pi) * x * y,
        0.5 * math.sqrt(15.0 / math.pi) * y * z,
        0.25 * math.sqrt(5.0 / math.pi) * (3.0 * z * z - 1.0),
        0.5 * math.sqrt(15.0 / math.pi) * x * z,
        0.25 * math.sqrt(15.0 / math.pi) * (x * x - y * y),
        0.25 * math.sqrt(35.0 / (2.0 * math.pi)) * y * (3 * x * x - y * y),
        0.5 * math.sqrt(105.0 / math.pi) * x * y * z,
        0.25 * math.sqrt(21.0 / (2.0 * math.pi)) * y * (5 * z * z - 1.0),
        0.25 * math.sqrt(7.0 / math.pi) * (5 * z ** 3 - 3 * z),
        0.25 * math.sqrt(21.0 / (2.0 * math.pi)) * x * (5 * z * z - 1.0),
        0.25 * math.sqrt(105.0 / math.pi) * (x * x - y * y) * z,
        0.25 * math.sqrt(35.0 / (2.0 * math.pi)) * x * (x * x - 3 * y * y),
    ]
    return np.stack(cols, axis=1)


def _standardize(v):
    s = v.std()
    return (v - v.mean()) / s if s > 1e-12 else v - v.mean()


def stereo_project(xyz):
    x, y, z = xyz[:, 0], xyz[:, 1], xyz[:, 2]
    denom = np.clip(1.0 - z, 1e-12, None)
    return (x + 1j * y) / denom


def stereo_lift(w):
    a2 = np.abs(w) ** 2
    denom = 1.0 + a2
    x = 2.0 * w.real / denom
    y = 2.0 * w.imag / denom
    z = (a2 - 1.0) / denom
    return np.stack([x, y, z], axis=1)


def mobius_apply(w, a, b, c, d):
    return (a * w + b) / (c * w + d)


def apply_lens(xyz, a, b, c, d):
    w = stereo_project(xyz)
    w2 = mobius_apply(w, a, b, c, d)
    return stereo_lift(w2)


def params_from_delta(delta):
    a = 1.0 + delta[0] + 1j * delta[1]
    b = 0.0 + delta[2] + 1j * delta[3]
    c = 0.0 + delta[4] + 1j * delta[5]
    d = 1.0 + delta[6] + 1j * delta[7]
    det = a * d - b * c
    if abs(det) < 1e-14:
        return None
    s = 1.0 / np.sqrt(det)
    return a * s, b * s, c * s, d * s


RANK_MIN = SH_NFUNCS
COND_MAX = 1e3


def guard_check(design):
    sv = np.linalg.svd(design, compute_uv=False)
    cond = float(sv[0] / sv[-1]) if sv[-1] > 1e-300 else float("inf")
    num_rank = int((sv > sv[0] * 1e-10).sum())
    ok = (num_rank >= RANK_MIN) and (cond <= COND_MAX)
    return ok, cond, num_rank


def ridge_fit_energy_share(design, y, target_cols=L3_COLS, lam=RIDGE_LAMBDA):
    p = design.shape[1]
    gram = design.T @ design + lam * np.eye(p)
    rhs = design.T @ y
    c = np.linalg.solve(gram, rhs)
    total_energy = float(np.sum(c ** 2))
    target_energy = float(np.sum(c[target_cols] ** 2))
    share = target_energy / total_energy if total_energy > 1e-300 else 0.0
    resid = y - design @ c
    rss = float(np.sum(resid ** 2))
    return share, rss, c


class Objective:
    def __init__(self, xyz, planted_field, null_fields, rng_guard_penalty=-1e6):
        self.xyz = xyz
        self.planted_field = planted_field
        self.null_fields = null_fields
        self.penalty = rng_guard_penalty
        self.n_evals = 0
        self.n_rejected = 0

    def evaluate(self, a, b, c, d):
        self.n_evals += 1
        lensed_xyz = apply_lens(self.xyz, a, b, c, d)
        design = real_sh_basis(lensed_xyz)
        ok, cond, num_rank = guard_check(design)
        if not ok:
            self.n_rejected += 1
            return self.penalty, {"guard_pass": False, "cond": cond, "num_rank": num_rank}
        planted_share, planted_rss, _ = ridge_fit_energy_share(design, self.planted_field)
        null_shares = np.empty(self.null_fields.shape[0])
        for r in range(self.null_fields.shape[0]):
            null_shares[r], _, _ = ridge_fit_energy_share(design, self.null_fields[r])
        mu0, sd0 = float(null_shares.mean()), float(null_shares.std(ddof=1))
        j = (planted_share - mu0) / sd0 if sd0 > 1e-12 else 0.0
        return j, {
            "guard_pass": True, "cond": cond, "num_rank": num_rank,
            "planted_share": planted_share, "null_mean": mu0, "null_sd": sd0,
            "planted_rss": planted_rss,
        }


def optimize(obj, rng, n_random=200, n_coord_rounds=25, init_step=0.35,
             coord_step0=0.15, shrink=0.85):
    best_delta = np.zeros(8)
    best_j = None
    best_info = None

    for _ in range(n_random):
        delta = rng.normal(0.0, init_step, size=8)
        params = params_from_delta(delta)
        if params is None:
            continue
        j, info = obj.evaluate(*params)
        if best_j is None or j > best_j:
            best_j, best_delta, best_info = j, delta, info

    identity_j, identity_info = obj.evaluate(1.0, 0.0, 0.0, 1.0)

    if best_j is None or identity_j > best_j:
        best_j, best_delta, best_info = identity_j, np.zeros(8), identity_info

    step = coord_step0
    for _round in range(n_coord_rounds):
        improved = False
        for k in range(8):
            for sign in (1.0, -1.0):
                trial = best_delta.copy()
                trial[k] += sign * step
                params = params_from_delta(trial)
                if params is None:
                    continue
                j, info = obj.evaluate(*params)
                if j > best_j:
                    best_j, best_delta, best_info = j, trial, info
                    improved = True
        step *= shrink
        if not improved and step < 1e-4:
            break

    return best_delta, best_j, best_info, identity_j, identity_info


def selfcheck_identity_baseline(xyz):
    design = real_sh_basis(xyz)
    ok, cond, num_rank = guard_check(design)
    return {"guard_pass": ok, "cond": cond, "num_rank": num_rank}


def selfcheck_cross_ratio(rng):
    w = rng.normal(size=(4, 2)) @ np.array([[1, 0], [0, 1]])
    w = w[:, 0] + 1j * w[:, 1]

    def cross_ratio(p):
        z1, z2, z3, z4 = p
        return ((z1 - z3) * (z2 - z4)) / ((z1 - z4) * (z2 - z3))

    delta = rng.normal(0.0, 0.5, size=8)
    params = params_from_delta(delta)
    a, b, c, d = params
    w2 = mobius_apply(w, a, b, c, d)
    cr1 = cross_ratio(w)
    cr2 = cross_ratio(w2)
    err = abs(cr1 - cr2)
    return {"cross_ratio_before": complex(cr1), "cross_ratio_after": complex(cr2),
            "abs_error": float(err), "pass": bool(err < 1e-9)}


def build_planted_field(xyz, theta, phi, rng, amplitude=1.0):
    basis = real_sh_basis(xyz)
    y33 = _standardize(basis[:, 15])
    y3m3 = _standardize(basis[:, 9])
    combo = _standardize(0.5 * y33 + 0.5 * y3m3)
    noise = rng.normal(0.0, 1.0, size=xyz.shape[0])
    return amplitude * combo + noise


def build_null_field(xyz, rng):
    return rng.normal(0.0, 1.0, size=xyz.shape[0])


def run(seed=20260822, n_lattice=512, n_null_reps=20, n_random=200,
        n_coord_rounds=25, amplitude=1.0):
    t0 = time.time()
    rng = np.random.default_rng(seed)
    xyz, theta, phi = fibonacci_sphere(n_lattice)

    baseline = selfcheck_identity_baseline(xyz)
    cross_ratio = selfcheck_cross_ratio(np.random.default_rng(seed + 1))

    planted_field = build_planted_field(xyz, theta, phi, rng, amplitude=amplitude)
    null_fields = np.stack([build_null_field(xyz, rng) for _ in range(n_null_reps)], axis=0)

    obj = Objective(xyz, planted_field, null_fields)
    best_delta, best_j, best_info, identity_j, identity_info = optimize(
        obj, rng, n_random=n_random, n_coord_rounds=n_coord_rounds)

    best_params = params_from_delta(best_delta)
    a, b, c, d = (complex(v) for v in best_params)
    wall_time = time.time() - t0

    delta_sd = float(best_j - identity_j) if (best_j is not None and identity_j is not None) else None
    h1_supported = bool(delta_sd is not None and delta_sd > 2.0)

    result = {
        "experiment": "gapD_lens_power",
        "status": "executed",
        "seed": seed,
        "config": {
            "n_lattice": n_lattice, "n_null_reps": n_null_reps,
            "n_random_draws": n_random, "n_coord_rounds": n_coord_rounds,
            "amplitude_s": amplitude, "ridge_lambda": RIDGE_LAMBDA,
            "target_degree_columns": L3_COLS, "guard_rank_min": RANK_MIN,
            "guard_cond_max": COND_MAX,
        },
        "pre_registration": {
            "H1": "optimized J exceeds identity J by more than 2 null standard "
                  "deviations (the lens materially concentrates the planted "
                  "family's L=3 spectral energy beyond a frozen identity chart).",
            "H0": "optimized J does not exceed identity J by more than 2 null "
                  "standard deviations (the lens adds nothing at s=1, N=512).",
            "note": "Both outcomes are treated as publishable; recorded honestly "
                     "below regardless of which held.",
        },
        "self_checks": {
            "identity_baseline": baseline,
            "cross_ratio_preservation": cross_ratio,
        },
        "results": {
            "identity_J": identity_j,
            "identity_info": identity_info,
            "best_J": best_j,
            "best_info": best_info,
            "delta_J_sd": delta_sd,
            "H1_supported": h1_supported,
            "best_theta": {
                "a": {"re": a.real, "im": a.imag},
                "b": {"re": b.real, "im": b.imag},
                "c": {"re": c.real, "im": c.imag},
                "d": {"re": d.real, "im": d.imag},
                "ad_minus_bc": complex(a * d - b * c).real,
            },
            "total_objective_evaluations": obj.n_evals,
            "guard_rejections": obj.n_rejected,
        },
        "wall_time_seconds": wall_time,
        "limitations": [
            "Single seed (20260822); no multi-seed replication in this run.",
            "Single amplitude s=1.0; no amplitude sweep.",
            "Small evaluation budget (~400-600 objective evaluations); optimizer "
            "is a simple random-search + coordinate-refinement scheme, not a "
            "proper gradient or global optimizer, so best_J is a lower bound on "
            "what a stronger optimizer could find.",
            "Planted field is a simplified continuous adaptation of the papers' "
            "binary standard-candle generator (see module docstring), not the "
            "exact create_corpus.py planting procedure.",
        ],
    }
    return result


def main():
    p = argparse.ArgumentParser(description="Gap D: power the lens experiment.")
    p.add_argument("--seed", type=int, default=20260822)
    p.add_argument("--n-lattice", type=int, default=512)
    p.add_argument("--n-null-reps", type=int, default=20)
    p.add_argument("--n-random", type=int, default=200)
    p.add_argument("--n-coord-rounds", type=int, default=25)
    p.add_argument("--amplitude", type=float, default=1.0)
    p.add_argument("--out", default=None)
    args = p.parse_args()

    result = run(seed=args.seed, n_lattice=args.n_lattice,
                 n_null_reps=args.n_null_reps, n_random=args.n_random,
                 n_coord_rounds=args.n_coord_rounds, amplitude=args.amplitude)

    txt = json.dumps(result, indent=2, sort_keys=False, default=str)
    if args.out:
        with open(args.out, "w") as fh:
            fh.write(txt + "\n")
        print("wrote %s" % args.out)
    else:
        print(txt)


if __name__ == "__main__":
    main()
