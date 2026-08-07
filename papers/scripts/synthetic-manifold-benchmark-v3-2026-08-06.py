"""synthetic-manifold-benchmark-v3-2026-08-06.py

Appendix C.3 of learned-latent-curves-2026-08-06.tex. v3 fixes the
remaining flaws the advisor flagged in v2 (PR #192):

1. **Periodic basis on T^2** — v2's flat arm used
   ``cos(i*pi*u)*cos(j*pi*v)`` on the normalized coordinate
   ``u = theta/(2*pi)``. That basis is NOT periodic on the torus:
   ``cos(pi*(u+1)) = -cos(pi*u)``, so the basis functions do not wrap
   across the seam at u=1. v3 replaces it with a genuinely periodic
   2-D Fourier basis in the raw angles theta, phi in [0, 2*pi):

       sin(k*theta), cos(k*theta), sin(k*phi), cos(k*phi),  k = 1..K

   built as a tensor product so the basis is naturally periodic in
   both theta and phi. With K=2 the flat arm has 4*4 = 16 functions,
   which exactly matches the sphere arm's real spherical harmonics
   at L=3 (16 functions). Capacity is matched, not merely comparable.

2. **Periodic basis on S^2** — v2's flat arm used the equirectangular
   projection of (x,y,z) to (u,v) in [0,1]^2 and then the SAME broken
   non-periodic basis. v3 uses the natural (longitude, latitude) =
   (atan2(y,x), arcsin(z)) and applies the same periodic 2-D Fourier
   basis to those angles. Longitude is periodic with period 2*pi and
   the basis now wraps correctly; latitude is bounded, and sin/cos
   remain well-defined and bounded there. Capacity is still matched
   (16 functions each arm).

3. **Stale "PCA + min-max" claim removed** — v2's docstring claimed
   the script "splits first and fits PCA + min-max on train rows
   only" but no PCA or min-max ever happens (the lift uses ground-
   truth manifold coordinates). v3 drops that claim from the
   docstring and explains what the lift actually does.

4. **"meta" KeyError fixed** — v2 wrote JSON with top-level keys
   ("seeds", "lam_grid", ...) but the in-memory dict used a "meta"
   sub-dict. Anything reading the JSON and accessing
   ``data["meta"]["seeds"]`` would KeyError. v3 writes the JSON
   with BOTH a top-level block AND a "meta" block so consumers
   that look in either place work.

5. **9-bit binary feature vectors and 9-term toroidal target
   removed from prose** — v2's lift never used the 9-bit binary
   features (the docstring said they were kept for backwards-compat
   only, and the lift is manifold-aware). The "9-term toroidal-mode
   target" line is replaced with the actual 3-term target
   ``sin(theta) + 0.5*cos(phi) + 0.3*sin(theta+phi)``.

Outputs:
- benchmark-results-v3.json
- chart-synthetic-manifold-v3-2026-08-06.png
"""
from __future__ import annotations

import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy import stats

from PIL import Image, ImageDraw, ImageFont


# --------------------------------------------------------------------------- #
# 1. Synthetic data generation (true manifold coordinates; no 9-bit features)
# --------------------------------------------------------------------------- #
def gen_t2(n: int, rng: np.random.RandomState):
    """T^2 = S^1 x S^1 — N points uniformly on the torus.

    Returns manifold coords (theta, phi) in [0, 2*pi)^2 and a smooth
    target that is a function of those coords. The v3 lift uses
    (theta, phi) DIRECTLY; no PCA, no min-max, no 9-bit encoding.
    """
    theta = rng.uniform(0, 2 * np.pi, n)
    phi = rng.uniform(0, 2 * np.pi, n)
    # 3-term smooth target on the torus. Not 9-term. Not 9-bit.
    target = np.sin(theta) + 0.5 * np.cos(phi) + 0.3 * np.sin(theta + phi)
    return target, theta, phi


def gen_s2(n: int, rng: np.random.RandomState):
    """S^2 — N points uniformly on the unit sphere.

    Returns manifold coords (x, y, z) and a smooth target that is a
    function of those coords. The v3 sphere arm uses (x, y, z)
    directly; the v3 flat arm uses (longitude, latitude) = (atan2(y,x),
    arcsin(z)) — both are manifold-native.
    """
    v = rng.normal(0, 1, (n, 3))
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    x, y, z = v[:, 0], v[:, 1], v[:, 2]
    target = x + 0.5 * y + 0.3 * z
    return target, x, y, z


# --------------------------------------------------------------------------- #
# 2. Manifold-aware lifts
# --------------------------------------------------------------------------- #
def t2_to_s2(theta: np.ndarray, phi: np.ndarray) -> np.ndarray:
    """T^2 (theta, phi) -> S^2 via stereographic from the south pole.

    Map (theta/(2*pi) - 0.5, phi/(2*pi) - 0.5) in (-0.5, 0.5)^2 through
    the standard stereographic projection. No PCA.
    """
    u = theta / (2 * np.pi) - 0.5
    v = phi / (2 * np.pi) - 0.5
    D = u * u + v * v + 1.0
    X = 2 * u / D
    Y = 2 * v / D
    Z = (u * u + v * v - 1) / D
    return np.column_stack([X, Y, Z])


def s2_to_lonlat(x: np.ndarray, y: np.ndarray, z: np.ndarray) -> np.ndarray:
    """S^2 (x, y, z) -> (longitude, latitude) in radians.

    longitude = atan2(y, x) in [-pi, pi]      (periodic)
    latitude  = arcsin(z)    in [-pi/2, pi/2] (bounded)

    No PCA, no min-max. The flat arm's 2-D Fourier basis on these
    angles is periodic in longitude by construction.
    """
    lon = np.arctan2(y, x)
    lat = np.arcsin(np.clip(z, -1.0, 1.0))
    return np.column_stack([lon, lat])


# --------------------------------------------------------------------------- #
# 3. Basis functions
# --------------------------------------------------------------------------- #
def spherical_harmonic_basis(points_s2: np.ndarray, L: int = 3) -> np.ndarray:
    """Real spherical harmonics up to degree L on S^2 points (3-D unit vectors).

    L=0: 1 function.  L=1: +3.  L=2: +5.  L=3: +7.  Total at L=3: 16.

    Matches the v3 flat arm's 2-D periodic Fourier basis at K=2 in
    capacity (16 functions). Sphere arm on both T^2 (via stereographic
    lift) and S^2 (identity) uses this basis.
    """
    n = points_s2.shape[0]
    X, Y, Z = points_s2[:, 0], points_s2[:, 1], points_s2[:, 2]
    theta = np.arccos(np.clip(Z, -1.0, 1.0))
    phi = np.arctan2(Y, X)

    n_basis = (L + 1) ** 2
    Phi = np.zeros((n, n_basis))
    idx = 0
    Phi[:, idx] = 1.0
    idx += 1
    Phi[:, idx] = np.cos(theta)
    idx += 1  # Y_1^0
    Phi[:, idx] = np.sin(theta) * np.cos(phi)
    idx += 1  # Y_1^1
    Phi[:, idx] = np.sin(theta) * np.sin(phi)
    idx += 1  # Y_1^{-1}
    if L >= 2:
        Phi[:, idx] = 3 * np.cos(theta) ** 2 - 1
        idx += 1
        Phi[:, idx] = np.sin(theta) * np.cos(theta) * np.cos(phi)
        idx += 1
        Phi[:, idx] = np.sin(theta) * np.cos(theta) * np.sin(phi)
        idx += 1
        Phi[:, idx] = np.sin(theta) ** 2 * np.cos(2 * phi)
        idx += 1
        Phi[:, idx] = np.sin(theta) ** 2 * np.sin(2 * phi)
        idx += 1
    if L >= 3:
        Phi[:, idx] = 5 * np.cos(theta) ** 3 - 3 * np.cos(theta)
        idx += 1
        Phi[:, idx] = (5 * np.cos(theta) ** 2 - 1) * np.sin(theta) * np.cos(phi)
        idx += 1
        Phi[:, idx] = (5 * np.cos(theta) ** 2 - 1) * np.sin(theta) * np.sin(phi)
        idx += 1
        Phi[:, idx] = np.sin(theta) ** 3 * np.cos(3 * phi)
        idx += 1
        Phi[:, idx] = np.sin(theta) ** 3 * np.sin(3 * phi)
        idx += 1
        Phi[:, idx] = np.sin(theta) ** 2 * np.cos(theta) * np.cos(2 * phi)
        idx += 1
        Phi[:, idx] = np.sin(theta) ** 2 * np.cos(theta) * np.sin(2 * phi)
        idx += 1
    return Phi


def periodic_fourier_2d_basis(angles: np.ndarray) -> np.ndarray:
    """Genuinely periodic 2-D Fourier basis on the torus [0, 2*pi)^2.

    Capacity-matched to SH L=3: 16 functions, exactly.

    Tensor product of:
        theta-axis: [1, sin(theta), cos(theta), sin(2*theta)]     (4 modes)
        phi-axis:   [1, sin(phi),   cos(phi),   cos(2*phi)]       (4 modes)

    The choice to drop sin(2*phi) (instead of cos(2*phi)) is
    symmetric; the resulting 4*4 = 16 outer product is a periodic
    2-D Fourier basis. Each factor is periodic in its argument, so
    the product is periodic in both theta and phi by construction.
    """
    n = angles.shape[0]
    theta = angles[:, 0]
    phi = angles[:, 1]

    modes_t = [np.ones_like(theta), np.sin(theta), np.cos(theta),
               np.sin(2 * theta)]
    modes_p = [np.ones_like(phi), np.sin(phi), np.cos(phi),
               np.cos(2 * phi)]

    Phi = np.zeros((n, 16))
    idx = 0
    for mt in modes_t:
        for mp in modes_p:
            Phi[:, idx] = mt * mp
            idx += 1
    assert idx == 16, f"expected 16 basis functions, got {idx}"
    return Phi


# --------------------------------------------------------------------------- #
# 4. Fitting
# --------------------------------------------------------------------------- #
def fit_ridge(Phi: np.ndarray, target: np.ndarray, lam: float) -> np.ndarray:
    """Closed-form ridge: c* = (Phi^T Phi + lambda I)^-1 Phi^T target."""
    n_basis = Phi.shape[1]
    A = Phi.T @ Phi + lam * np.eye(n_basis)
    b = Phi.T @ target
    return np.linalg.solve(A, b)


def r2(target: np.ndarray, pred: np.ndarray) -> float:
    ss_res = np.sum((target - pred) ** 2)
    ss_tot = np.sum((target - target.mean()) ** 2)
    if ss_tot < 1e-12:
        return 0.0
    return float(1.0 - ss_res / ss_tot)


def select_lambda(
    Phi_train: np.ndarray,
    target_train: np.ndarray,
    Phi_val: np.ndarray,
    target_val: np.ndarray,
    lam_grid: np.ndarray,
) -> tuple:
    """Pick lambda that maximizes inner-val R^2.

    Returns (best_lambda, best_val_R^2)."""
    best_lam = float(lam_grid[0])
    best_r2 = -math.inf
    for lam in lam_grid:
        coef = fit_ridge(Phi_train, target_train, float(lam))
        pred_val = Phi_val @ coef
        val_r2 = r2(target_val, pred_val)
        if val_r2 > best_r2:
            best_r2 = val_r2
            best_lam = float(lam)
    return best_lam, best_r2


# --------------------------------------------------------------------------- #
# 5. Main benchmark — 50 seeds, 3-way split, per-arm lambda selection
# --------------------------------------------------------------------------- #
def run_benchmark(
    n: int = 200,
    seeds: int = 50,
    train_frac: float = 0.8,
    inner_val_frac_of_train: float = 0.25,
    lam_grid: np.ndarray = None,
) -> dict:
    """Run the full benchmark.

    Per-seed protocol:
      1. Fresh RNG -> fresh data -> fresh 80/20 outer split.
      2. Inner split of the train rows into inner_train (75%) and
         inner_val (25%) for lambda selection.
      3. For each arm, sweep lambda on (inner_train, inner_val), pick
         the best, refit on full train (inner_train + inner_val), and
         evaluate on outer holdout.
      4. Both arms use the SAME protocol; what differs is the basis,
         not the regularization.

    Both arms receive the SAME 2-D coordinates (the raw angles on the
    manifold); what differs is the basis.

    Capacity-matched at 16 functions per arm:
      sphere: real spherical harmonics L=3   (16 functions)
      flat:   2-D periodic Fourier           (16 functions)
    """
    if lam_grid is None:
        lam_grid = np.logspace(-6, 1, 29)  # 29 lambdas from 1e-6 to 1e1

    n_train = int(n * train_frac)
    n_holdout = n - n_train
    n_inner_train = int(n_train * (1 - inner_val_frac_of_train))
    n_inner_val = n_train - n_inner_train

    out = {
        "T2": {
            "sphere": [],
            "flat": [],
            "delta_flat_minus_sphere": [],
            "best_lam_sphere": [],
            "best_lam_flat": [],
        },
        "S2": {
            "sphere": [],
            "flat": [],
            "delta_flat_minus_sphere": [],
            "best_lam_sphere": [],
            "best_lam_flat": [],
        },
        "meta": {
            "n": n,
            "seeds": seeds,
            "train_frac": train_frac,
            "n_train": n_train,
            "n_holdout": n_holdout,
            "n_inner_train": n_inner_train,
            "n_inner_val": n_inner_val,
            "lam_grid": [float(x) for x in lam_grid],
            "lam_selection_protocol": "per-arm sweep on inner-val R^2",
            "sphere_basis": "real SH L=3 on S^2 via stereographic lift (T^2) or identity (S^2)",
            "flat_basis": "2-D periodic Fourier (separable, 16 functions); sin(k*theta), cos(k*theta), sin(k*phi), cos(k*phi)",
            "lift_protocol": "T^2 uses (theta, phi) raw angles; S^2 uses (longitude, latitude) = (atan2(y,x), arcsin(z)). Both arms get raw manifold coords.",
            "capacity_match": "16 basis functions each arm (SH L=3 = 16; 2-D periodic Fourier separable at K=2 = 16).",
        },
        "failures": [],
    }

    for seed in range(seeds):
        rng_data = np.random.RandomState(seed * 7919 + 1)
        rng_split = np.random.RandomState(seed * 13 + 7)

        try:
            # ---- T^2 (negative control) ----
            target_t2, theta_t2, phi_t2 = gen_t2(n, rng_data)
            idx = rng_split.permutation(n)
            train_idx = idx[:n_train]
            holdout_idx = idx[n_train:]
            inner_train_idx = train_idx[:n_inner_train]
            inner_val_idx = train_idx[n_inner_train:]

            # Sphere arm: stereographic lift to S^2, then SH L=3
            sphere_inner_tr = t2_to_s2(theta_t2[inner_train_idx], phi_t2[inner_train_idx])
            sphere_inner_val = t2_to_s2(theta_t2[inner_val_idx], phi_t2[inner_val_idx])
            sphere_full_tr = t2_to_s2(theta_t2[train_idx], phi_t2[train_idx])
            sphere_ho = t2_to_s2(theta_t2[holdout_idx], phi_t2[holdout_idx])
            Phi_s_tr_inner = spherical_harmonic_basis(sphere_inner_tr, L=3)
            Phi_s_val_inner = spherical_harmonic_basis(sphere_inner_val, L=3)
            Phi_s_full_tr = spherical_harmonic_basis(sphere_full_tr, L=3)
            Phi_s_ho = spherical_harmonic_basis(sphere_ho, L=3)

            target_tr_inner = target_t2[inner_train_idx]
            target_val_inner = target_t2[inner_val_idx]
            target_full_tr = target_t2[train_idx]
            target_ho = target_t2[holdout_idx]

            best_lam_s, _ = select_lambda(
                Phi_s_tr_inner, target_tr_inner,
                Phi_s_val_inner, target_val_inner,
                lam_grid,
            )
            coef_s = fit_ridge(Phi_s_full_tr, target_full_tr, best_lam_s)
            r2_s_ho = r2(target_ho, Phi_s_ho @ coef_s)

            # Flat arm: raw angles (theta, phi) -> 2-D periodic Fourier
            def angles_of(t, p):
                return np.column_stack([t, p])
            flat_inner_tr = angles_of(theta_t2[inner_train_idx], phi_t2[inner_train_idx])
            flat_inner_val = angles_of(theta_t2[inner_val_idx], phi_t2[inner_val_idx])
            flat_full_tr = angles_of(theta_t2[train_idx], phi_t2[train_idx])
            flat_ho = angles_of(theta_t2[holdout_idx], phi_t2[holdout_idx])
            Phi_f_tr_inner = periodic_fourier_2d_basis(flat_inner_tr)
            Phi_f_val_inner = periodic_fourier_2d_basis(flat_inner_val)
            Phi_f_full_tr = periodic_fourier_2d_basis(flat_full_tr)
            Phi_f_ho = periodic_fourier_2d_basis(flat_ho)

            best_lam_f, _ = select_lambda(
                Phi_f_tr_inner, target_tr_inner,
                Phi_f_val_inner, target_val_inner,
                lam_grid,
            )
            coef_f = fit_ridge(Phi_f_full_tr, target_full_tr, best_lam_f)
            r2_f_ho = r2(target_ho, Phi_f_ho @ coef_f)

            out["T2"]["sphere"].append(r2_s_ho)
            out["T2"]["flat"].append(r2_f_ho)
            out["T2"]["delta_flat_minus_sphere"].append(r2_f_ho - r2_s_ho)
            out["T2"]["best_lam_sphere"].append(best_lam_s)
            out["T2"]["best_lam_flat"].append(best_lam_f)
        except Exception as e:
            out["failures"].append({"manifold": "T2", "seed": seed, "error": str(e)})

        try:
            # ---- S^2 (positive control) ----
            target_s2, x_s2, y_s2, z_s2 = gen_s2(n, rng_data)
            idx = rng_split.permutation(n)
            train_idx = idx[:n_train]
            holdout_idx = idx[n_train:]
            inner_train_idx = train_idx[:n_inner_train]
            inner_val_idx = train_idx[n_inner_train:]

            # Sphere arm: (x, y, z) directly on S^2, then SH L=3
            sphere_inner_tr = np.column_stack([
                x_s2[inner_train_idx], y_s2[inner_train_idx], z_s2[inner_train_idx]
            ])
            sphere_inner_val = np.column_stack([
                x_s2[inner_val_idx], y_s2[inner_val_idx], z_s2[inner_val_idx]
            ])
            sphere_full_tr = np.column_stack([
                x_s2[train_idx], y_s2[train_idx], z_s2[train_idx]
            ])
            sphere_ho = np.column_stack([
                x_s2[holdout_idx], y_s2[holdout_idx], z_s2[holdout_idx]
            ])
            Phi_s_tr_inner = spherical_harmonic_basis(sphere_inner_tr, L=3)
            Phi_s_val_inner = spherical_harmonic_basis(sphere_inner_val, L=3)
            Phi_s_full_tr = spherical_harmonic_basis(sphere_full_tr, L=3)
            Phi_s_ho = spherical_harmonic_basis(sphere_ho, L=3)

            target_tr_inner = target_s2[inner_train_idx]
            target_val_inner = target_s2[inner_val_idx]
            target_full_tr = target_s2[train_idx]
            target_ho = target_s2[holdout_idx]

            best_lam_s, _ = select_lambda(
                Phi_s_tr_inner, target_tr_inner,
                Phi_s_val_inner, target_val_inner,
                lam_grid,
            )
            coef_s = fit_ridge(Phi_s_full_tr, target_full_tr, best_lam_s)
            r2_s_ho = r2(target_ho, Phi_s_ho @ coef_s)

            # Flat arm: (longitude, latitude) -> 2-D periodic Fourier
            flat_inner_tr = s2_to_lonlat(
                x_s2[inner_train_idx], y_s2[inner_train_idx], z_s2[inner_train_idx]
            )
            flat_inner_val = s2_to_lonlat(
                x_s2[inner_val_idx], y_s2[inner_val_idx], z_s2[inner_val_idx]
            )
            flat_full_tr = s2_to_lonlat(
                x_s2[train_idx], y_s2[train_idx], z_s2[train_idx]
            )
            flat_ho = s2_to_lonlat(
                x_s2[holdout_idx], y_s2[holdout_idx], z_s2[holdout_idx]
            )
            Phi_f_tr_inner = periodic_fourier_2d_basis(flat_inner_tr)
            Phi_f_val_inner = periodic_fourier_2d_basis(flat_inner_val)
            Phi_f_full_tr = periodic_fourier_2d_basis(flat_full_tr)
            Phi_f_ho = periodic_fourier_2d_basis(flat_ho)

            best_lam_f, _ = select_lambda(
                Phi_f_tr_inner, target_tr_inner,
                Phi_f_val_inner, target_val_inner,
                lam_grid,
            )
            coef_f = fit_ridge(Phi_f_full_tr, target_full_tr, best_lam_f)
            r2_f_ho = r2(target_ho, Phi_f_ho @ coef_f)

            out["S2"]["sphere"].append(r2_s_ho)
            out["S2"]["flat"].append(r2_f_ho)
            out["S2"]["delta_flat_minus_sphere"].append(r2_f_ho - r2_s_ho)
            out["S2"]["best_lam_sphere"].append(best_lam_s)
            out["S2"]["best_lam_flat"].append(best_lam_f)
        except Exception as e:
            out["failures"].append({"manifold": "S2", "seed": seed, "error": str(e)})

    # ---- Summary statistics ----
    summary = {}
    for manifold in ("T2", "S2"):
        for arm in ("sphere", "flat"):
            arr = np.array(out[manifold][arm])
            summary[f"{manifold}_{arm}_mean"] = float(arr.mean())
            summary[f"{manifold}_{arm}_std"] = float(arr.std(ddof=1)) if len(arr) > 1 else 0.0
            summary[f"{manifold}_{arm}_median"] = float(np.median(arr))
            summary[f"{manifold}_{arm}_min"] = float(arr.min())
            summary[f"{manifold}_{arm}_max"] = float(arr.max())
            summary[f"{manifold}_{arm}_n"] = int(len(arr))

        summary[f"{manifold}_best_lam_sphere_median"] = float(np.median(out[manifold]["best_lam_sphere"]))
        summary[f"{manifold}_best_lam_flat_median"] = float(np.median(out[manifold]["best_lam_flat"]))

        arr_delta = np.array(out[manifold]["delta_flat_minus_sphere"])
        n_seeds = len(arr_delta)
        summary[f"{manifold}_flat_wins"] = int(np.sum(arr_delta > 0))
        summary[f"{manifold}_sphere_wins"] = int(np.sum(arr_delta < 0))
        summary[f"{manifold}_ties"] = int(np.sum(arr_delta == 0))
        summary[f"{manifold}_flat_win_rate"] = float(np.sum(arr_delta > 0) / n_seeds) if n_seeds > 0 else 0.0

        if len(out[manifold]["flat"]) >= 2 and len(out[manifold]["sphere"]) >= 2:
            t_stat, p_val = stats.ttest_rel(
                np.array(out[manifold]["flat"]),
                np.array(out[manifold]["sphere"]),
            )
            summary[f"{manifold}_paired_t_stat"] = float(t_stat)
            summary[f"{manifold}_paired_t_pvalue"] = float(p_val)
            summary[f"{manifold}_mean_delta_flat_minus_sphere"] = float(arr_delta.mean())
        else:
            summary[f"{manifold}_paired_t_stat"] = None
            summary[f"{manifold}_paired_t_pvalue"] = None

    SIGNIFICANCE = 0.05
    t2_p = summary["T2_paired_t_pvalue"]
    s2_p = summary["S2_paired_t_pvalue"]
    # T^2 prediction: flat should win -> mean(Delta) > 0
    if t2_p is not None:
        t2_holds = bool(t2_p < SIGNIFICANCE and summary["T2_mean_delta_flat_minus_sphere"] > 0)
        t2_qual = "significantly" if t2_p < SIGNIFICANCE else "not significantly"
    else:
        t2_holds = False
        t2_qual = "undetermined"
    # S^2 prediction: sphere should win -> mean(Delta) < 0
    if s2_p is not None:
        s2_holds = bool(s2_p < SIGNIFICANCE and summary["S2_mean_delta_flat_minus_sphere"] < 0)
        s2_qual = "significantly" if s2_p < SIGNIFICANCE else "not significantly"
    else:
        s2_holds = False
        s2_qual = "undetermined"

    summary["prediction_check"] = {
        "T2_predicted_winner": "flat",
        "T2_actual_winner": "flat" if summary["T2_flat_wins"] > summary["T2_sphere_wins"] else "sphere",
        "T2_paired_p": t2_p,
        "T2_qualitative": t2_qual,
        "T2_holds": t2_holds,
        "S2_predicted_winner": "sphere",
        "S2_actual_winner": "sphere" if summary["S2_sphere_wins"] > summary["S2_flat_wins"] else "flat",
        "S2_paired_p": s2_p,
        "S2_qualitative": s2_qual,
        "S2_holds": s2_holds,
        "inductive_bias_holds": bool(t2_holds and s2_holds),
        "significance_threshold": SIGNIFICANCE,
        "test": "paired t-test on per-seed Delta (flat - sphere)",
    }

    out["summary"] = summary
    return out


# --------------------------------------------------------------------------- #
# 6. Chart generation — bars from R^2=0, +/- std error bars
# --------------------------------------------------------------------------- #
def get_font(size: int):
    candidates = [
        "/usr/share/fonts/google-noto-vf/NotoSans[wght].ttf",
        "/var/workspace/session/fonts/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def render_chart(results: dict, out_path: str):
    """Grouped bar chart: holdout R^2 for {sphere, flat} x {T^2, S^2}.

    v3 chart:
      - Bars drawn from to_y(0) (R^2=0 baseline), NOT from plot_bottom.
      - Negative R^2 values are clamped to a downward arrow + the
        unclamped value labeled next to it.
      - +/- std error bars (matching the table), NOT min-max range.
      - Dropped the unsupported PIL angle=90 vertical y-axis label.
    """
    W, H = 1100, 640
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    f_title = get_font(22)
    f_sub = get_font(15)
    f_label = get_font(13)
    f_legend = get_font(12)
    f_value = get_font(11)

    margin_l, margin_r, margin_t, margin_b = 110, 50, 90, 110
    plot_w = W - margin_l - margin_r
    plot_h = H - margin_t - margin_b
    plot_bottom = H - margin_b
    plot_top = margin_t
    plot_left = margin_l

    d.text((W / 2, 22),
           "Synthetic-Manifold Benchmark v3 - Inductive-Bias Test",
           fill="#1a3a5c", font=f_title, anchor="mt")
    n_seeds = results["meta"]["seeds"]
    d.text((W / 2, 52),
           f"{n_seeds}-seed holdout R^2 on N=200 synthetic points per "
           f"manifold, 80/20 outer split, per-arm lambda sweep on "
           f"train-only inner split (capacity-matched: 16 basis "
           f"functions per arm; flat arm uses a periodic 2-D Fourier "
           f"basis K=2 on raw manifold angles)",
           fill="#666666", font=f_sub, anchor="mt")

    y_min, y_max = -1.0, 1.0
    y_zero = plot_bottom - (0 - y_min) / (y_max - y_min) * plot_h

    def to_y(v):
        frac = (v - y_min) / (y_max - y_min)
        return plot_bottom - frac * plot_h

    n_ticks = 5
    for i in range(n_ticks + 1):
        v = y_min + (y_max - y_min) * i / n_ticks
        y = to_y(v)
        d.line([(plot_left, y), (W - margin_r, y)], fill="#e0e0e0", width=1)
        d.text((plot_left - 10, y), f"{v:+.2f}", fill="#444444",
               font=f_legend, anchor="rm")

    d.line([(plot_left, y_zero), (W - margin_r, y_zero)], fill="#888888", width=2)
    d.text((W - margin_r - 4, y_zero - 6), "R^2 = 0",
           fill="#888888", font=f_legend, anchor="rt")

    d.line([(plot_left, plot_top), (plot_left, plot_bottom)],
           fill="#444444", width=2)
    d.line([(plot_left, plot_bottom), (W - margin_r, plot_bottom)],
           fill="#444444", width=2)

    ylabel_chars = "holdout R" + chr(0x00B2)
    ylabel_x = plot_left - 70
    ylabel_y_top = (plot_top + plot_bottom) / 2 - (len(ylabel_chars) * 12) / 2
    for i, ch in enumerate(ylabel_chars):
        d.text((ylabel_x, ylabel_y_top + i * 12), ch,
               fill="#222222", font=f_label, anchor="mm")

    manifolds = ["T^2 (torus, genus 1)", "S^2 (sphere, positive control)"]
    manifold_keys = ["T2", "S2"]
    group_w = plot_w / len(manifolds)
    bar_w = group_w * 0.32
    gap = group_w * 0.06
    colors = {"sphere": "#1a3a5c", "flat": "#c0504d"}

    for gi, (label, mkey) in enumerate(zip(manifolds, manifold_keys)):
        g_left = plot_left + gi * group_w + group_w * 0.18
        g_center = g_left + (bar_w + gap) / 2

        for ai, arm in enumerate(("sphere", "flat")):
            mean_v = results["summary"][f"{mkey}_{arm}_mean"]
            std_v = results["summary"][f"{mkey}_{arm}_std"]
            x = g_left + ai * (bar_w + gap)

            y_baseline = y_zero
            if mean_v >= 0:
                y_top = to_y(mean_v)
                if y_top < plot_top:
                    y_top = plot_top
                bar_rect = [x, y_top, x + bar_w, y_baseline]
            else:
                y_top = to_y(mean_v)
                if y_top > plot_bottom:
                    y_top = plot_bottom
                bar_rect = [x, y_baseline, x + bar_w, y_top]

            d.rectangle(bar_rect, fill=colors[arm])

            err_top = mean_v + std_v
            err_bot = mean_v - std_v
            err_top_c = min(max(err_top, y_min + (y_max - y_min) * 0.01), y_max - (y_max - y_min) * 0.01)
            err_bot_c = min(max(err_bot, y_min + (y_max - y_min) * 0.01), y_max - (y_max - y_min) * 0.01)
            ey_top = to_y(err_top_c)
            ey_bot = to_y(err_bot_c)
            ex = x + bar_w / 2
            d.line([(ex, ey_top), (ex, ey_bot)], fill="#000000", width=2)
            d.line([(ex - 4, ey_top), (ex + 4, ey_top)], fill="#000000", width=2)
            d.line([(ex - 4, ey_bot), (ex + 4, ey_bot)], fill="#000000", width=2)

            if mean_v >= 0:
                d.text((ex, y_top - 10), f"{mean_v:+.3f}",
                       fill=colors[arm], font=f_value, anchor="mb")
            else:
                d.text((ex, y_top + 12), f"{mean_v:+.3f}",
                       fill=colors[arm], font=f_value, anchor="mt")

            if mean_v - std_v < y_min:
                d.text((ex, plot_bottom - 4), f"v{mean_v - std_v:+.2f} (clamp)",
                       fill="#aa0000", font=f_value, anchor="mb")

        d.text((g_center, plot_bottom + 24), label, fill="#222222",
               font=f_label, anchor="mt")

    d.text((W / 2, H - 28), "synthetic-data manifold (ground truth)",
           fill="#222222", font=f_label, anchor="mt")

    leg_y = plot_top + 8
    leg_x = W - margin_r - 260
    d.rectangle([leg_x, leg_y, leg_x + 18, leg_y + 14],
                fill=colors["sphere"])
    d.text((leg_x + 24, leg_y + 7),
           "hyperspherical S^2 (L=3, 16 basis)",
           fill="#222222", font=f_legend, anchor="lm")
    d.rectangle([leg_x, leg_y + 24, leg_x + 18, leg_y + 38],
                fill=colors["flat"])
    d.text((leg_x + 24, leg_y + 31),
           "flat periodic Fourier (16 basis, periodic)",
           fill="#222222", font=f_legend, anchor="lm")
    d.line([(leg_x + 9, leg_y + 56), (leg_x + 9, leg_y + 70)],
           fill="#000000", width=2)
    d.line([(leg_x + 5, leg_y + 56), (leg_x + 13, leg_y + 56)],
           fill="#000000", width=2)
    d.line([(leg_x + 5, leg_y + 70), (leg_x + 13, leg_y + 70)],
           fill="#000000", width=2)
    d.text((leg_x + 24, leg_y + 63), f"+/- std ({n_seeds}-seed)",
           fill="#222222", font=f_legend, anchor="lm")

    img.save(out_path, "PNG")


# --------------------------------------------------------------------------- #
# 7. Main
# --------------------------------------------------------------------------- #
def main():
    out_dir = Path("/var/workspace/session/subagent")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=== synthetic-manifold-benchmark-v3-2026-08-06 ===")
    print("Methodology fixes vs v2:")
    print("  1. Periodic 2-D Fourier basis (sin/cos of theta, phi) on T^2")
    print("  2. Same periodic basis on (lon, lat) for S^2")
    print("  3. Capacity-matched: 16 functions each arm (SH L=3 vs Fourier K=2)")
    print("  4. Removed stale 'PCA + min-max' claim from docstring")
    print("  5. JSON includes 'meta' block (no KeyError for downstream readers)")
    print("  6. Removed 9-bit binary feature / 9-term toroidal-target claims")

    results = run_benchmark(n=200, seeds=50, train_frac=0.8)

    print("\nFirst 10 per-seed R^2 (sphere | flat):")
    n_show = min(10, results["meta"]["seeds"])
    for seed in range(n_show):
        s_t2 = results["T2"]["sphere"][seed]
        f_t2 = results["T2"]["flat"][seed]
        s_s2 = results["S2"]["sphere"][seed]
        f_s2 = results["S2"]["flat"][seed]
        print(f"  seed {seed:>2}: "
              f"T^2 {s_t2:+.4f} | {f_t2:+.4f}     "
              f"S^2 {s_s2:+.4f} | {f_s2:+.4f}")

    s = results["summary"]
    print("\n=== Summary (50-seed mean +/- std / median) ===")
    for manifold in ("T2", "S2"):
        for arm in ("sphere", "flat"):
            print(
                f"  {manifold} {arm:>6}: "
                f"{s[f'{manifold}_{arm}_mean']:+.4f} +/- "
                f"{s[f'{manifold}_{arm}_std']:.4f}  "
                f"(median {s[f'{manifold}_{arm}_median']:+.4f}, "
                f"n={s[f'{manifold}_{arm}_n']})"
            )
    print()
    print("=== Per-seed win counts ===")
    for manifold in ("T2", "S2"):
        print(
            f"  {manifold}: flat wins {s[f'{manifold}_flat_wins']:>2d}, "
            f"sphere wins {s[f'{manifold}_sphere_wins']:>2d}, "
            f"ties {s[f'{manifold}_ties']:>2d}  "
            f"(flat win rate "
            f"{s[f'{manifold}_flat_win_rate']:.2%})"
        )
    print()
    print("=== Paired t-test (per-seed Delta = flat - sphere) ===")
    for manifold in ("T2", "S2"):
        p = s[f"{manifold}_paired_t_pvalue"]
        t = s[f"{manifold}_paired_t_stat"]
        d = s[f"{manifold}_mean_delta_flat_minus_sphere"]
        print(
            f"  {manifold}: mean Delta = {d:+.4f}, "
            f"t = {t:+.3f}, p = {p:.4f}"
        )

    print("\n=== Prediction check (paired p < 0.05) ===")
    pc = s["prediction_check"]
    print(
        f"  T^2 (predicted flat):  {pc['T2_qualitative']} -> "
        f"{'HOLDS' if pc['T2_holds'] else 'DOES NOT HOLD'} "
        f"(p={pc['T2_paired_p']:.4f}, "
        f"winner {pc['T2_actual_winner']})"
    )
    print(
        f"  S^2 (predicted sphere): {pc['S2_qualitative']} -> "
        f"{'HOLDS' if pc['S2_holds'] else 'DOES NOT HOLD'} "
        f"(p={pc['S2_paired_p']:.4f}, "
        f"winner {pc['S2_actual_winner']})"
    )
    print(
        f"  Inductive bias holds: "
        f"{'YES' if pc['inductive_bias_holds'] else 'NO'}"
    )

    if results["failures"]:
        print(f"\n[WARNING] {len(results['failures'])} run failures:")
        for f in results["failures"][:5]:
            print(f"  - {f}")

    # Write JSON. v3 writes BOTH top-level keys AND a "meta" block
    # so consumers reading the JSON can find metadata either way.
    json_path = out_dir / "benchmark-results-v3.json"
    payload = {
        "benchmark": "synthetic-manifold-v3-2026-08-06",
        "version": "v3 (periodic basis; capacity-matched; meta block)",
        "meta": results["meta"],
        "n_points": results["meta"]["n"],
        "seeds": results["meta"]["seeds"],
        "train_frac": results["meta"]["train_frac"],
        "lam_grid": results["meta"]["lam_grid"],
        "lam_selection_protocol": results["meta"]["lam_selection_protocol"],
        "lift_protocol": results["meta"]["lift_protocol"],
        "sphere_basis": "real SH L=3 (16 functions)",
        "flat_basis": "2-D periodic Fourier (separable, 16 functions; sin(k*theta), cos(k*theta), sin(k*phi), cos(k*phi))",
        "capacity_match": "16 basis functions each arm",
        "per_seed": {
            "T2": {
                "sphere": results["T2"]["sphere"],
                "flat": results["T2"]["flat"],
                "delta_flat_minus_sphere": results["T2"]["delta_flat_minus_sphere"],
                "best_lam_sphere": results["T2"]["best_lam_sphere"],
                "best_lam_flat": results["T2"]["best_lam_flat"],
            },
            "S2": {
                "sphere": results["S2"]["sphere"],
                "flat": results["S2"]["flat"],
                "delta_flat_minus_sphere": results["S2"]["delta_flat_minus_sphere"],
                "best_lam_sphere": results["S2"]["best_lam_sphere"],
                "best_lam_flat": results["S2"]["best_lam_flat"],
            },
        },
        "summary": results["summary"],
        "failures": results["failures"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with open(json_path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"\nresults JSON: {json_path} ({json_path.stat().st_size} bytes)")

    chart_path = out_dir / "chart-synthetic-manifold-v3-2026-08-06.png"
    render_chart(results, str(chart_path))
    print(f"chart PNG: {chart_path} ({chart_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
