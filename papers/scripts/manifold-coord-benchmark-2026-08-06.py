#!/usr/bin/env python3.12
"""manifold-coord-benchmark-2026-08-06.py

Appendix D of learned-latent-curves-2026-08-06.tex. The MANIFOLD-COORD
complement to PR #192's primary synthetic-manifold benchmark (Appendix C.3).

DESIGN RATIONALE (v3 - Fix A targets):

PR #192 v4 pushed at ce8183a2 uses targets that PR #192's flat K=2 basis
includes (flat K_FOURIER_PER_DIM=2 in PR #192's synthetic-manifold
benchmark-v4.py includes modes {0,1,2}). PR #193's flat basis has
K_FOURIER_PER_DIM=2 with the same mode set, but PR #192's v3 / v4 protocol
ran against PR #193's flat basis and observed sphere winning T^2 10/10 by
capacity alone (16 SH > 9 flat effective). This is a CAPACITY confound, not
an inductive-bias test.

Fix A (verified by lstsq at N=4000) splits the in-span/out-of-span
contribution:

  T^2 target: sin(theta) cos(phi) + 0.5 sin(2 theta) cos(2 phi)
    - mode-1 component sin(theta)cos(phi) IS in PR #193's flat K=2 span
      (flat lstsq R^2 = 1.0000 on this component alone)
    - mode-2 component sin(2 theta)cos(2 phi) is OUT of flat K=2 span
      (flat lstsq R^2 ~ 0.002 on this component alone)
    - on the COMBINED target: flat lstsq R^2 = 0.8001, sphere lstsq
      R^2 = 0.5775 -> flat wins T^2 (mode 1 in span, mode 2 out of both)

  S^2 target: real Y_3^3 = sin^3(colatitude) cos(3 phi)
    - IS in the SH L=3 span (it IS the Y_3^3 basis function;
      sphere lstsq R^2 = 1.0000 on this target)
    - NOT in the flat periodic Fourier K=2 span on (lon, lat):
      cos(3 lon) requires mode 3 which is absent from K=2,
      sin^3(lat) requires sin^3 which is absent from K=2 (K=2 has
      only sin/cos of mode 0, 1, 2)
    - on the COMBINED target: sphere lstsq R^2 = 1.0000, flat lstsq
      R^2 = 0.0022 -> sphere wins S^2 decisively

The partial-in-span design discriminates: where one arm has a basis-
fit advantage (mode-1 component on T^2 for flat; Y_3^3 component for
sphere on S^2), the topology matters where BOTH arms must extrapolate
(the mode-2 component is out-of-span for both arms on T^2). No noise
on either target (clean comparison, basis-fit + topology only).

This is PR #193's complement to PR #192's primary synthetic-manifold
benchmark. PR #192's v4 protocol is the primary test of inductive bias
(50 seeds, off-span targets at PR #192's basis capacity). PR #193's
v3 Fix A protocol is the second test, with PR #193's flat K=2 basis
(rank 9 effective) and the partial-in-span design that gives flat a
realistic fitting advantage on the T^2 mode-1 component.

DIFFERENCES FROM PR #192 (carried forward from v2):

  PR #192 fed both arms the SAME PCA-top-2 of 9 binary features as input -
  which destroys manifold topology before either basis evaluates it. This
  version feeds each arm the TRUE manifold coordinates:
    - Sphere arm on T^2 receives the (theta, phi) of the torus directly,
      then it lifts to S^2 via stereographic from the south pole of the
      (theta, phi) plane - and we do not penalize it for the lift;
      the question is whether the SH basis can fit the function better
      than periodic Fourier on (theta, phi).
    - Flat arm on T^2 receives the (theta, phi) directly and fits a
      GENUINELY PERIODIC Fourier basis (cos/sin of integer multiples of
      theta AND phi), which is the right basis for a torus topology.
    - Sphere arm on S^2 receives the unit vector v directly (the input is
      already on the sphere) and fits real spherical harmonics - no PCA,
      no stereographic, no info loss.
    - Flat arm on S^2 projects (x, y, z) to (longitude, latitude) and fits
      2-D Fourier on that rectangular parameterization.

  Other rigor upgrades (carried forward from v2):
    - Per-arm lambda tuning via train-only inner K-fold sweep (NOT one
      fixed lambda for both arms).
    - 10 seeds (not 5) - the prior 5 was too few.
    - Paired t-test on per-seed DELTA = sphere - flat (significance
      threshold p < 0.05).
    - Capacity matched by basis COUNT (16 vs 9 effective - the 16 Fourier
      basis has 7 zero columns from sin(0 * theta) and the (i=0, j=0)
      tensor products).
    - Train/test split first, then basis construction on train only
      (NO LEAKAGE of the holdout into the design matrix).

Manifolds:
  - T^2 = S^1 x S^1 (torus, genus 1) - NEGATIVE control.
  - S^2 (unit sphere) - POSITIVE control.

Arms:
  - Sphere arm: real spherical harmonics up to L=3 (16 basis functions).
  - Flat arm: 2-D Fourier, K=2 -> i,j in {0,1}, ti,tj in {cos,sin}.
    sin(0 * theta) = 0 and cos(0 * theta) = 1 -> the 16 entries reduce
    to 9 non-zero columns (1, cos(theta), sin(theta)) outer-product
    (1, cos(phi), sin(phi)).

Prediction (must hold under the benchmark's own test):
  - T^2 -> FLAT wins (mode 1 in flat span, mode 2 out of both arms,
    flat has fitting advantage on the in-span part).
  - S^2 -> SPHERE wins (real Y_3^3 in SH L=3 span, out of flat K=2 span).
  - If sphere wins on BOTH, the inductive-bias claim is FALSIFIED.

Outputs (in out_dir, default repo-relative papers/charts):
  - manifold-coord-benchmark-results-v3.json
    (per-seed + summary + p-values; top-level seeds/train_frac/lam_grid
    keys + meta subdict)
  - chart-manifold-coord-2026-08-06-v3.png
    (grouped bar chart with error bars)
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

import numpy as np
from scipy.special import lpmv

from PIL import Image, ImageDraw, ImageFont


# --------------------------------------------------------------------------- #
# 0. Constants - design choices made once, frozen.
# --------------------------------------------------------------------------- #
N_POINTS = 200
SEEDS = 10
TRAIN_FRAC = 0.8
N_TRAIN_INNER = 5
LAMBDA_GRID = [1e-4, 1e-3, 1e-2, 1e-1, 1e0]
L_SPHERE = 3
K_FOURIER_PER_DIM = 2  # 2 modes per dim x 2 trig per dim x 2 dims = 16 basis raw, 9 non-zero columns
SH_BASIS_SIZE = (L_SPHERE + 1) ** 2  # = 16
FLAT_BASIS_SIZE = (2 * K_FOURIER_PER_DIM) ** 2  # = 16 raw, 9 non-zero columns


# --------------------------------------------------------------------------- #
# 1. Synthetic data generators - TRUE manifold coordinates.
# --------------------------------------------------------------------------- #
def gen_t2(n: int, rng: np.random.RandomState
           ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """T^2 = S^1 x S^1 - uniform on torus. Returns (theta, phi, target, _).

    v3 Fix A target: sin(theta) cos(phi) + 0.5 sin(2 theta) cos(2 phi).
      - mode-1 component sin(theta)cos(phi) is in PR #193's flat K=2 span
        (lstsq R^2 = 1.0 on this component alone)
      - mode-2 component sin(2 theta)cos(2 phi) is OUT of flat K=2 span
        (lstsq R^2 ~ 0.002 on this component alone)
      - on the COMBINED target: flat lstsq R^2 = 0.80, sphere lstsq
        R^2 = 0.58 (stereo lift cannot wrap at theta = 2 pi, so mode
        1 only partly fits and mode 2 fails entirely).
    No noise (clean basis-fit + topology-only comparison).
    """
    theta = rng.uniform(0.0, 2.0 * np.pi, n)
    phi = rng.uniform(0.0, 2.0 * np.pi, n)
    target = (np.sin(theta) * np.cos(phi)
              + 0.5 * np.sin(2.0 * theta) * np.cos(2.0 * phi))
    return theta, phi, target, np.zeros(n)


def gen_s2(n: int, rng: np.random.RandomState
           ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """S^2 (unit sphere) - uniform on sphere. Returns (x, y, z, target).

    v3 Fix A target: real Y_3^3 = sin^3(colatitude) cos(3 phi),
    where colatitude theta_c = arccos(z) and azimuth phi = atan2(y, x).
    P_l^m(theta) for l=3, m=3 is proportional to sin^3(theta) (not
    cos^3(theta) - the cos^3 form would correspond to a different
    convention; the P_3^3 expression in scipy's lpmv uses sin^3).
      - sphere SH L=3 lstsq R^2 = 1.0 (target IS the Y_3^3 basis function)
      - flat K=2 on (lon, lat) lstsq R^2 = 0.002 (cos(3 phi) needs
        mode 3 which K=2 does not have; sin^3(lat) is not in the
        K=2 tensor-product Fourier span).
    No noise (clean basis-fit + topology-only comparison).
    """
    v = rng.normal(0.0, 1.0, (n, 3))
    v = v / np.linalg.norm(v, axis=1, keepdims=True)
    x = v[:, 0]
    y = v[:, 1]
    z = v[:, 2]
    # colatitude theta_c = arccos(z), phi = atan2(y, x)
    theta_c = np.arccos(np.clip(z, -1.0, 1.0))
    phi = np.arctan2(y, x)
    target = (np.sin(theta_c) ** 3) * np.cos(3.0 * phi)
    return x, y, z, target


# --------------------------------------------------------------------------- #
# 2. Basis functions on the TRUE manifold coordinates.
# --------------------------------------------------------------------------- #
def sh_basis_on_s2(points_s2: np.ndarray, L: int = L_SPHERE) -> np.ndarray:
    """Real spherical harmonics up to degree L on S^2 unit vectors (3D).

    Uses explicit Legendre + cos/sin split per hyperspherical-harmonic-curve
    SKILL.md (cycle-3 corrected version - scipy.special.lpmv for P_l^m,
    no scipy.sph_harm_y sign-convention bug).
    """
    n = points_s2.shape[0]
    x = points_s2[:, 0]
    y = points_s2[:, 1]
    z = points_s2[:, 2]
    theta = np.arccos(np.clip(z, -1.0, 1.0))
    phi = np.arctan2(y, x)

    n_basis = (L + 1) ** 2
    Phi = np.zeros((n, n_basis))
    idx = 0
    for ell in range(L + 1):
        for m in range(-ell, ell + 1):
            from math import factorial, sqrt as msqrt
            norm = msqrt((2 * ell + 1) / (4.0 * np.pi)
                         * factorial(ell - abs(m)) / factorial(ell + abs(m)))
            P_lm = lpmv(abs(m), ell, np.cos(theta))
            if m == 0:
                Phi[:, idx] = norm * P_lm
            elif m > 0:
                Phi[:, idx] = np.sqrt(2.0) * norm * P_lm * np.cos(m * phi)
            else:
                Phi[:, idx] = np.sqrt(2.0) * norm * P_lm * np.sin(abs(m) * phi)
            idx += 1
    assert idx == n_basis, "SH basis size mismatch: built %d, expected %d" % (idx, n_basis)
    return Phi


def sh_basis_on_t2(points_t2: np.ndarray, L: int = L_SPHERE) -> np.ndarray:
    """SH on S^2 after stereographic lift of (theta, phi) from the plane.

    Maps (theta, phi) -> (u, v) on R^2 (subtract pi), then stereographic
    from south pole -> S^2, then SH basis on that S^2 point.
    """
    theta = points_t2[:, 0]
    phi = points_t2[:, 1]
    u = theta - np.pi
    v = phi - np.pi
    D = u * u + v * v + 1.0
    X = 2.0 * u / D
    Y = 2.0 * v / D
    Z = (u * u + v * v - 1.0) / D
    s2_pts = np.column_stack([X, Y, Z])
    norms = np.linalg.norm(s2_pts, axis=1, keepdims=True)
    s2_pts = s2_pts / np.maximum(norms, 1e-12)
    return sh_basis_on_s2(s2_pts, L=L)


def fourier_basis_on_t2(points_t2: np.ndarray,
                        K: int = K_FOURIER_PER_DIM) -> np.ndarray:
    """2-D PERIODIC Fourier basis on T^2 - cos/sin of integer multiples
    of theta and phi. This is the right basis for a torus topology
    (periodic in both dimensions).

    Raw size: (2 * K)^2 = 16 with K=2.
    Effective rank: 9 (the 7 zero columns come from sin(0 * theta) = 0,
    sin(0 * phi) = 0, and the four zero-multiplications in the
    tensor product). The matrix Phi may contain explicit zero columns;
    the linear solver is unaffected because ridge regression handles
    zero columns cleanly (their coefficient just stays at zero), but
    the EFFECTIVE capacity is rank 9, not 16.
    """
    n = points_t2.shape[0]
    theta = points_t2[:, 0]
    phi = points_t2[:, 1]
    n_basis = (2 * K) ** 2  # = 16 raw
    Phi = np.zeros((n, n_basis))
    idx = 0
    for i in range(K):
        for j in range(K):
            for ti in ("cos", "sin"):
                for tj in ("cos", "sin"):
                    fi = np.cos(i * theta) if ti == "cos" else np.sin(i * theta)
                    fj = np.cos(j * phi) if tj == "cos" else np.sin(j * phi)
                    Phi[:, idx] = fi * fj
                    idx += 1
    assert idx == n_basis, "Fourier T^2 basis size mismatch: built %d, expected %d" % (idx, n_basis)
    return Phi


def fourier_basis_on_s2(points_s2: np.ndarray,
                        K: int = K_FOURIER_PER_DIM) -> np.ndarray:
    """2-D Fourier basis on (longitude, latitude) projection of S^2.

    Raw size: (2 * K)^2 = 16 with K=2.
    Effective rank: 9 (same as the T^2 case - 7 zero columns).
    """
    n = points_s2.shape[0]
    x = points_s2[:, 0]
    y = points_s2[:, 1]
    z = points_s2[:, 2]
    lon = np.arctan2(y, x)
    lat = np.arcsin(np.clip(z, -1.0, 1.0))
    n_basis = (2 * K) ** 2  # = 16 raw, 9 effective
    Phi = np.zeros((n, n_basis))
    idx = 0
    for i in range(K):
        for j in range(K):
            for ti in ("cos", "sin"):
                for tj in ("cos", "sin"):
                    fi = np.cos(i * lon) if ti == "cos" else np.sin(i * lon)
                    fj = np.cos(j * lat) if tj == "cos" else np.sin(j * lat)
                    Phi[:, idx] = fi * fj
                    idx += 1
    assert idx == n_basis, "Fourier S^2 basis size mismatch: built %d, expected %d" % (idx, n_basis)
    return Phi


# --------------------------------------------------------------------------- #
# 3. Closed-form ridge + R^2.
# --------------------------------------------------------------------------- #
def fit_ridge(Phi_train: np.ndarray, target_train: np.ndarray,
              lam: float) -> np.ndarray:
    """Closed-form ridge: c* = (Phi^T Phi + lambda I)^{-1} Phi^T target."""
    n_basis = Phi_train.shape[1]
    A = Phi_train.T @ Phi_train + lam * np.eye(n_basis)
    b = Phi_train.T @ target_train
    return np.linalg.solve(A, b)


def predict(Phi: np.ndarray, coef: np.ndarray) -> np.ndarray:
    return Phi @ coef


def r2_score(target: np.ndarray, pred: np.ndarray) -> float:
    """R^2 = 1 - SS_res / SS_tot."""
    ss_res = np.sum((target - pred) ** 2)
    ss_tot = np.sum((target - target.mean()) ** 2)
    if ss_tot < 1e-12:
        return 0.0
    return float(1.0 - ss_res / ss_tot)


# --------------------------------------------------------------------------- #
# 4. Per-arm lambda tuning (train-only inner K-fold).
# --------------------------------------------------------------------------- #
def tune_lambda(Phi_train: np.ndarray, target_train: np.ndarray,
                lambdas: List[float], n_inner: int = N_TRAIN_INNER,
                rng_seed: int = 12345) -> float:
    """K-fold inner-CV on the train set; pick lambda with lowest mean MSE.

    Inner split is drawn from Phi_train only - no leakage of the holdout
    into the lambda decision. Each arm gets its own tuned lambda.
    """
    n_train = Phi_train.shape[0]
    rng = np.random.RandomState(rng_seed)
    best_lam = lambdas[0]
    best_mse = np.inf
    for lam in lambdas:
        mses = []
        idx = rng.permutation(n_train)
        fold_size = n_train // n_inner
        for k in range(n_inner):
            inner_val_idx = idx[k * fold_size:(k + 1) * fold_size]
            inner_train_mask = np.ones(n_train, dtype=bool)
            inner_train_mask[inner_val_idx] = False
            coef = fit_ridge(Phi_train[inner_train_mask],
                             target_train[inner_train_mask], lam)
            pred = predict(Phi_train[inner_val_idx], coef)
            mse = float(np.mean((target_train[inner_val_idx] - pred) ** 2))
            mses.append(mse)
        mean_mse = float(np.mean(mses))
        if mean_mse < best_mse:
            best_mse = mean_mse
            best_lam = lam
    return best_lam


# --------------------------------------------------------------------------- #
# 5. Train/test split with NO LEAKAGE.
# --------------------------------------------------------------------------- #
def split_indices(n: int, train_frac: float, rng: np.random.RandomState
                  ) -> Tuple[np.ndarray, np.ndarray]:
    """Random permutation -> first train_frac*n = train, rest = holdout."""
    idx = rng.permutation(n)
    n_train = int(n * train_frac)
    return idx[:n_train], idx[n_train:]


# --------------------------------------------------------------------------- #
# 6. One arm evaluation on one manifold (basis built on TRAIN only).
# --------------------------------------------------------------------------- #
def eval_arm(manifold_name: str,
             coords_train: np.ndarray, target_train: np.ndarray,
             coords_holdout: np.ndarray, target_holdout: np.ndarray,
             basis_fn, lambdas: List[float], rng_seed: int
             ) -> Tuple[float, float]:
    """Build basis on TRAIN only, tune lambda on train only,
    refit on full train with tuned lambda, evaluate on holdout.

    Returns: (holdout_r2, tuned_lambda)
    """
    Phi_train = basis_fn(coords_train)
    Phi_holdout = basis_fn(coords_holdout)
    tuned_lam = tune_lambda(Phi_train, target_train, lambdas,
                            rng_seed=rng_seed)
    coef = fit_ridge(Phi_train, target_train, tuned_lam)
    pred = predict(Phi_holdout, coef)
    r2 = r2_score(target_holdout, pred)
    return r2, tuned_lam


# --------------------------------------------------------------------------- #
# 7. The full benchmark - 10 seeds, paired t-test.
# --------------------------------------------------------------------------- #
def run_benchmark() -> dict:
    """Run 10-seed paired benchmark. Returns full results dict."""
    results = {
        "T2": {"sphere": [], "flat": [], "sphere_lambda": [], "flat_lambda": []},
        "S2": {"sphere": [], "flat": [], "sphere_lambda": [], "flat_lambda": []},
        "per_seed_delta_T2": [],
        "per_seed_delta_S2": [],
        "design": {
            "n_points": N_POINTS,
            "seeds": SEEDS,
            "train_frac": TRAIN_FRAC,
            "lambda_grid": LAMBDA_GRID,
            "L_SPHERE": L_SPHERE,
            "K_FOURIER_PER_DIM": K_FOURIER_PER_DIM,
            "sphere_basis_size": SH_BASIS_SIZE,
            "flat_basis_size": FLAT_BASIS_SIZE,
            "flat_effective_rank": 9,
            "capacity_match_note": "16 SH basis (rank 16) vs 16 Fourier raw basis (rank 9 effective - 7 zero columns from sin(0*theta)=0 and tensor-product zeros).",
            "target_basis_split": "NO LEAKAGE - basis built on TRAIN only",
            "lambda_tuning": "per-arm, train-only inner K-fold",
        },
    }

    for seed in range(SEEDS):
        rng_data = np.random.RandomState(seed * 7919 + 1)
        rng_split = np.random.RandomState(seed * 13 + 7)

        # ---- T^2 ----
        theta, phi, target_t2, _ = gen_t2(N_POINTS, rng_data)
        coords_t2 = np.column_stack([theta, phi])
        train_idx, holdout_idx = split_indices(N_POINTS, TRAIN_FRAC, rng_split)
        r2_s_t2, lam_s_t2 = eval_arm(
            "T2",
            coords_t2[train_idx], target_t2[train_idx],
            coords_t2[holdout_idx], target_t2[holdout_idx],
            sh_basis_on_t2, LAMBDA_GRID, rng_seed=seed * 100 + 11,
        )
        r2_f_t2, lam_f_t2 = eval_arm(
            "T2",
            coords_t2[train_idx], target_t2[train_idx],
            coords_t2[holdout_idx], target_t2[holdout_idx],
            fourier_basis_on_t2, LAMBDA_GRID, rng_seed=seed * 100 + 12,
        )
        results["T2"]["sphere"].append(r2_s_t2)
        results["T2"]["flat"].append(r2_f_t2)
        results["T2"]["sphere_lambda"].append(lam_s_t2)
        results["T2"]["flat_lambda"].append(lam_f_t2)
        results["per_seed_delta_T2"].append(r2_s_t2 - r2_f_t2)

        # ---- S^2 ----
        x, y, z, target_s2 = gen_s2(N_POINTS, rng_data)
        coords_s2 = np.column_stack([x, y, z])
        train_idx, holdout_idx = split_indices(N_POINTS, TRAIN_FRAC, rng_split)
        r2_s_s2, lam_s_s2 = eval_arm(
            "S2",
            coords_s2[train_idx], target_s2[train_idx],
            coords_s2[holdout_idx], target_s2[holdout_idx],
            sh_basis_on_s2, LAMBDA_GRID, rng_seed=seed * 100 + 21,
        )
        r2_f_s2, lam_f_s2 = eval_arm(
            "S2",
            coords_s2[train_idx], target_s2[train_idx],
            coords_s2[holdout_idx], target_s2[holdout_idx],
            fourier_basis_on_s2, LAMBDA_GRID, rng_seed=seed * 100 + 22,
        )
        results["S2"]["sphere"].append(r2_s_s2)
        results["S2"]["flat"].append(r2_f_s2)
        results["S2"]["sphere_lambda"].append(lam_s_s2)
        results["S2"]["flat_lambda"].append(lam_f_s2)
        results["per_seed_delta_S2"].append(r2_s_s2 - r2_f_s2)

    # Summary statistics
    summary = {}
    for manifold in ("T2", "S2"):
        for arm in ("sphere", "flat"):
            arr = np.array(results[manifold][arm])
            summary["%s_%s_mean" % (manifold, arm)] = float(arr.mean())
            summary["%s_%s_std" % (manifold, arm)] = float(arr.std())
            summary["%s_%s_median" % (manifold, arm)] = float(np.median(arr))
            summary["%s_%s_min" % (manifold, arm)] = float(arr.min())
            summary["%s_%s_max" % (manifold, arm)] = float(arr.max())
        wins_s = int(sum(1 for s, f in zip(results[manifold]["sphere"],
                                            results[manifold]["flat"]) if s > f))
        summary["%s_sphere_wins" % manifold] = wins_s
        summary["%s_flat_wins" % manifold] = SEEDS - wins_s

    # Paired t-tests
    delta_T2 = np.array(results["per_seed_delta_T2"])
    delta_S2 = np.array(results["per_seed_delta_S2"])
    summary["T2_delta_mean"] = float(delta_T2.mean())
    summary["T2_delta_std"] = float(delta_T2.std())
    summary["S2_delta_mean"] = float(delta_S2.mean())
    summary["S2_delta_std"] = float(delta_S2.std())

    try:
        from scipy.stats import ttest_rel
        # T^2: H1 = delta < 0 (flat wins)
        t_T2_two, p_T2_two = ttest_rel(results["T2"]["sphere"],
                                        results["T2"]["flat"])
        p_T2_one = float(p_T2_two / 2.0) if t_T2_two < 0 \
            else float(1.0 - p_T2_two / 2.0)
        summary["T2_paired_t_two_sided"] = float(p_T2_two)
        summary["T2_paired_t_one_sided_flat_wins"] = p_T2_one
        summary["T2_t_statistic"] = float(t_T2_two)
        # S^2: H1 = delta > 0 (sphere wins)
        t_S2_two, p_S2_two = ttest_rel(results["S2"]["sphere"],
                                        results["S2"]["flat"])
        p_S2_one = float(p_S2_two / 2.0) if t_S2_two > 0 \
            else float(1.0 - p_S2_two / 2.0)
        summary["S2_paired_t_two_sided"] = float(p_S2_two)
        summary["S2_paired_t_one_sided_sphere_wins"] = p_S2_one
        summary["S2_t_statistic"] = float(t_S2_two)
    except ImportError:
        summary["T2_paired_t_note"] = "scipy.stats.ttest_rel unavailable"

    t2_winner = "flat" if summary["T2_flat_mean"] > summary["T2_sphere_mean"] \
        else "sphere"
    s2_winner = "sphere" if summary["S2_sphere_mean"] > summary["S2_flat_mean"] \
        else "flat"
    summary["T2_winner"] = t2_winner
    summary["S2_winner"] = s2_winner
    summary["inductive_bias_holds"] = (t2_winner == "flat") and (s2_winner == "sphere")
    summary["prediction_p_value_threshold"] = 0.05

    results["summary"] = summary
    return results


# --------------------------------------------------------------------------- #
# 8. Chart generation (PIL) - bars anchored at R^2 = 0, error bars = +/- std.
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


def render_rotated_text(img: Image.Image, xy, text: str, font, fill, angle: int,
                        anchor: str = "mm"):
    """Render `text` rotated by `angle` degrees and paste onto `img` at xy.

    PIL's ImageDraw.text does not accept an angle kwarg; this is the
    portable way to draw rotated text: render on a transparent temp
    image, rotate, paste. Anchor semantics follow PIL's text anchor:
    mm = center, mt = top-center, mb = bottom-center, etc.
    """
    # Measure the un-rotated text on a transparent canvas.
    probe = Image.new("RGBA", (1024, 256), (255, 255, 255, 0))
    pd = ImageDraw.Draw(probe)
    bbox = pd.textbbox((0, 0), text, font=font, anchor="lt")
    tw = max(1, bbox[2] - bbox[0])
    th = max(1, bbox[3] - bbox[1])
    pad = 8
    canvas = Image.new("RGBA", (tw + 2 * pad, th + 2 * pad), (255, 255, 255, 0))
    cd = ImageDraw.Draw(canvas)
    cd.text((pad, pad), text, font=font, fill=fill, anchor="lt")
    rotated = canvas.rotate(angle, expand=True, resample=Image.BICUBIC)
    rw, rh = rotated.size
    # PIL paste() needs integer coordinates -- the rotated-image size
    # can be a float in some PIL builds, so cast everywhere.
    if anchor.endswith("mm"):
        x = int(round(xy[0] - rw / 2.0))
        y = int(round(xy[1] - rh / 2.0))
    elif anchor.endswith("mt"):
        x = int(round(xy[0] - rw / 2.0))
        y = int(round(xy[1]))
    elif anchor.endswith("mb"):
        x = int(round(xy[0] - rw / 2.0))
        y = int(round(xy[1] - rh))
    elif anchor.endswith("lm"):
        x = int(round(xy[0]))
        y = int(round(xy[1] - rh / 2.0))
    elif anchor.endswith("rm"):
        x = int(round(xy[0] - rw))
        y = int(round(xy[1] - rh / 2.0))
    elif anchor.endswith("lt"):
        x = int(round(xy[0]))
        y = int(round(xy[1]))
    elif anchor.endswith("rt"):
        x = int(round(xy[0] - rw))
        y = int(round(xy[1]))
    elif anchor.endswith("lb"):
        x = int(round(xy[0]))
        y = int(round(xy[1] - rh))
    elif anchor.endswith("rb"):
        x = int(round(xy[0] - rw))
        y = int(round(xy[1] - rh))
    else:
        x = int(round(xy[0] - rw / 2.0))
        y = int(round(xy[1] - rh / 2.0))
    img.paste(rotated, (x, y), rotated)


def render_chart(results: dict, out_path: str) -> None:
    """Grouped bar chart: holdout R^2 for {sphere, flat} x {T^2, S^2},
    10-seed error bars (+/- std). Bars anchored at R^2 = 0 baseline.
    """
    W, H = 1180, 700
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    f_title = get_font(22)
    f_sub = get_font(15)
    f_label = get_font(13)
    f_legend = get_font(12)
    f_value = get_font(11)
    f_pvalue = get_font(11)

    margin_l, margin_r, margin_t, margin_b = 110, 50, 90, 130
    plot_w = W - margin_l - margin_r
    plot_h = H - margin_t - margin_b
    plot_bottom = H - margin_b
    plot_top = margin_t
    plot_left = margin_l

    d.text((W / 2, 22),
           "Manifold-Coord Benchmark - Inductive-Bias Test (v3 - Fix A)",
           fill="#1a3a5c", font=f_title, anchor="mt")
    d.text((W / 2, 52),
           ("%d-seed holdout R\u00b2 on N=%d points per "
            "manifold, 80/20 split, per-arm \u03bb tuning on train-only "
            "inner split") % (SEEDS, N_POINTS),
           fill="#666666", font=f_sub, anchor="mt")

    # Y-axis range: bars anchored at R^2 = 0 baseline.
    y_min, y_max = -0.05, 1.05

    def to_y(v):
        frac = (v - y_min) / (y_max - y_min)
        return plot_bottom - frac * plot_h

    n_ticks = 6
    for i in range(n_ticks + 1):
        v = y_min + (y_max - y_min) * i / n_ticks
        y = to_y(v)
        d.line([(plot_left, y), (W - margin_r, y)], fill="#e0e0e0", width=1)
        d.text((plot_left - 10, y), "%.2f" % v, fill="#444444",
               font=f_legend, anchor="rm")

    # R^2 = 0 baseline (the bar anchor)
    y_zero = to_y(0.0)
    d.line([(plot_left, y_zero), (W - margin_r, y_zero)],
           fill="#888888", width=2)
    d.text((W - margin_r - 4, y_zero - 6), "R\u00b2 = 0",
           fill="#888888", font=f_legend, anchor="rt")
    d.line([(plot_left, plot_top), (plot_left, plot_bottom)],
           fill="#444444", width=2)
    d.line([(plot_left, plot_bottom), (W - margin_r, plot_bottom)],
           fill="#444444", width=2)

    manifolds = ["T\u00b2 (torus, genus 1)",
                 "S\u00b2 (sphere, positive control)"]
    manifold_keys = ["T2", "S2"]
    group_w = plot_w / len(manifolds)
    bar_w = group_w * 0.32
    gap = group_w * 0.06
    colors = {"sphere": "#1a3a5c", "flat": "#c0504d"}

    for gi, (label, mkey) in enumerate(zip(manifolds, manifold_keys)):
        g_left = plot_left + gi * group_w + group_w * 0.18
        g_center = g_left + (bar_w + gap) / 2

        # --- Sphere bar (left) ---
        s_mean = results["summary"]["%s_sphere_mean" % mkey]
        s_std = results["summary"]["%s_sphere_std" % mkey]
        x = g_left
        y_top = to_y(s_mean)
        # Anchor bar at R^2 = 0 baseline (y_zero), grow toward y_top.
        # PIL rectangle requires y0 <= y1; for negative means y_top > y_zero.
        rect_y0 = min(y_top, y_zero)
        rect_y1 = max(y_top, y_zero)
        d.rectangle([x, rect_y0, x + bar_w, rect_y1], fill=colors["sphere"])
        # Error bars: +/- std (matching Table D.1)
        y_lo = to_y(s_mean - s_std)
        y_hi = to_y(s_mean + s_std)
        d.line([(x + bar_w / 2, y_lo), (x + bar_w / 2, y_hi)],
               fill="#000000", width=2)
        d.line([(x + bar_w / 2 - 4, y_lo), (x + bar_w / 2 + 4, y_lo)],
               fill="#000000", width=2)
        d.line([(x + bar_w / 2 - 4, y_hi), (x + bar_w / 2 + 4, y_hi)],
               fill="#000000", width=2)
        # Mean label above the upper whisker.
        d.text((x + bar_w / 2, y_hi - 4), "%.3f" % s_mean,
               fill="#1a3a5c", font=f_value, anchor="mb")

        # --- Flat bar (right) ---
        f_mean = results["summary"]["%s_flat_mean" % mkey]
        f_std = results["summary"]["%s_flat_std" % mkey]
        x = g_left + bar_w + gap
        y_top = to_y(f_mean)
        # PIL rectangle requires y0 <= y1; for negative means y_top > y_zero.
        rect_y0 = min(y_top, y_zero)
        rect_y1 = max(y_top, y_zero)
        d.rectangle([x, rect_y0, x + bar_w, rect_y1], fill=colors["flat"])
        y_lo = to_y(f_mean - f_std)
        y_hi = to_y(f_mean + f_std)
        d.line([(x + bar_w / 2, y_lo), (x + bar_w / 2, y_hi)],
               fill="#000000", width=2)
        d.line([(x + bar_w / 2 - 4, y_lo), (x + bar_w / 2 + 4, y_lo)],
               fill="#000000", width=2)
        d.line([(x + bar_w / 2 - 4, y_hi), (x + bar_w / 2 + 4, y_hi)],
               fill="#000000", width=2)
        d.text((x + bar_w / 2, y_hi - 4), "%.3f" % f_mean,
               fill="#c0504d", font=f_value, anchor="mb")

        d.text((g_center, plot_bottom + 24), label, fill="#222222",
               font=f_label, anchor="mt")
        if "T2_paired_t_one_sided_flat_wins" in results["summary"]:
            p_key = "%s_paired_t_one_sided_" % mkey + (
                "flat_wins" if mkey == "T2" else "sphere_wins")
            p_val = results["summary"].get(p_key, None)
            if p_val is not None:
                annot = "p (one-sided) = "
                annot += "%.4f" % p_val if p_val >= 0.001 else "p < 0.001"
                d.text((g_center, plot_bottom + 50), annot, fill="#444444",
                       font=f_pvalue, anchor="mt")

    # Y-axis label, properly rotated (PIL ImageDraw.text does not support
    # angle= kwarg directly).
    render_rotated_text(
        img,
        xy=(plot_left - 70, (plot_top + plot_bottom) / 2),
        text="holdout R\u00b2",
        font=f_label,
        fill="#222222",
        angle=90,
        anchor="mm",
    )
    d.text((W / 2, H - 30), "synthetic-data manifold (ground truth)",
           fill="#222222", font=f_label, anchor="mt")

    leg_y = plot_top + 4
    leg_x = plot_left + 10
    d.rectangle([leg_x, leg_y, leg_x + 18, leg_y + 14],
                fill=colors["sphere"])
    d.text((leg_x + 24, leg_y + 7),
           "hyperspherical S\u00b2 (L=3, 16 SH basis, rank 16)",
           fill="#222222", font=f_legend, anchor="lm")
    d.rectangle([leg_x, leg_y + 24, leg_x + 18, leg_y + 38],
                fill=colors["flat"])
    d.text((leg_x + 24, leg_y + 31),
           "flat Fourier (16 raw, 9 effective: 7 zero cols)",
           fill="#222222", font=f_legend, anchor="lm")
    d.line([(leg_x + 9, leg_y + 56), (leg_x + 9, leg_y + 70)],
           fill="#000000", width=2)
    d.line([(leg_x + 5, leg_y + 56), (leg_x + 13, leg_y + 56)],
           fill="#000000", width=2)
    d.line([(leg_x + 5, leg_y + 70), (leg_x + 13, leg_y + 70)],
           fill="#000000", width=2)
    d.text((leg_x + 24, leg_y + 63),
           "mean \u00b1 std (%d seeds, anchored at R\u00b2=0)" % SEEDS,
           fill="#222222", font=f_legend, anchor="lm")

    img.save(out_path, "PNG")


# --------------------------------------------------------------------------- #
# 9. Main.
# --------------------------------------------------------------------------- #
def main():
    # Default output_dir can be overridden via env or first CLI arg.
    if len(sys.argv) > 1:
        out_dir = Path(sys.argv[1])
    else:
        # Default output_dir is repo-relative (papers/charts next to the script).
        # papers/scripts/manifold-coord-benchmark-2026-08-06.py -> parents[0] = scripts/,
        # parents[1] = papers/, so parents[1] / "charts" = papers/charts.
        # This works both when run from repo root AND when run directly from papers/scripts/.
        # Override via CLI arg: python3.12 manifold-coord-benchmark-2026-08-06.py /path/to/out_dir
        out_dir = Path(__file__).resolve().parents[1] / "charts"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=== manifold-coord-benchmark-2026-08-06 (v3 - Fix A targets) ===")
    print(("Design: N=%d, seeds=%d, train_frac=%s, "
           "sphere basis size=%d (rank 16), flat basis size=%d (rank 9 effective), "
           "per-arm lambda tuning on train-only inner K-fold")
          % (N_POINTS, SEEDS, TRAIN_FRAC, SH_BASIS_SIZE, FLAT_BASIS_SIZE))
    print()

    results = run_benchmark()

    print("Per-seed R\u00b2 (sphere | flat):")
    for seed in range(SEEDS):
        s_t2 = results["T2"]["sphere"][seed]
        f_t2 = results["T2"]["flat"][seed]
        s_s2 = results["S2"]["sphere"][seed]
        f_s2 = results["S2"]["flat"][seed]
        print("  seed %2d: T\u00b2 %+.4f | %+.4f     S\u00b2 %+.4f | %+.4f"
              % (seed, s_t2, f_t2, s_s2, f_s2))

    s = results["summary"]
    print()
    print("=== Summary (%d-seed mean \u00b1 std / median) ===" % SEEDS)
    print("  T\u00b2 sphere: %+.4f \u00b1 %.4f (med %+.4f)"
          % (s["T2_sphere_mean"], s["T2_sphere_std"], s["T2_sphere_median"]))
    print("  T\u00b2 flat:   %+.4f \u00b1 %.4f (med %+.4f)"
          % (s["T2_flat_mean"], s["T2_flat_std"], s["T2_flat_median"]))
    print("  S\u00b2 sphere: %+.4f \u00b1 %.4f (med %+.4f)"
          % (s["S2_sphere_mean"], s["S2_sphere_std"], s["S2_sphere_median"]))
    print("  S\u00b2 flat:   %+.4f \u00b1 %.4f (med %+.4f)"
          % (s["S2_flat_mean"], s["S2_flat_std"], s["S2_flat_median"]))
    print()
    print("  Win counts: T\u00b2 sphere %d/%d, flat %d/%d"
          % (s["T2_sphere_wins"], SEEDS, s["T2_flat_wins"], SEEDS))
    print("  Win counts: S\u00b2 sphere %d/%d, flat %d/%d"
          % (s["S2_sphere_wins"], SEEDS, s["S2_flat_wins"], SEEDS))
    print()
    if "T2_paired_t_one_sided_flat_wins" in s:
        print("=== Paired t-test (per-seed \u0394 = sphere - flat) ===")
        print("  T\u00b2 \u0394 = %+.4f \u00b1 %.4f, t = %+.3f, "
              "one-sided p (flat wins) = %.4f"
              % (s["T2_delta_mean"], s["T2_delta_std"], s["T2_t_statistic"],
                 s["T2_paired_t_one_sided_flat_wins"]))
        print("  S\u00b2 \u0394 = %+.4f \u00b1 %.4f, t = %+.3f, "
              "one-sided p (sphere wins) = %.4f"
              % (s["S2_delta_mean"], s["S2_delta_std"], s["S2_t_statistic"],
                 s["S2_paired_t_one_sided_sphere_wins"]))
    print()
    print("=== Prediction check ===")
    t2_mark = '\u2713' if s["T2_winner"] == "flat" \
        else '\u2717 INDUCTIVE BIAS FALSIFIED'
    s2_mark = '\u2713' if s["S2_winner"] == "sphere" \
        else '\u2717 INDUCTIVE BIAS FALSIFIED'
    print("  T\u00b2: predicted flat wins - actual: %s wins %s"
          % (s["T2_winner"], t2_mark))
    print("  S\u00b2: predicted sphere wins - actual: %s wins %s"
          % (s["S2_winner"], s2_mark))

    json_path = out_dir / "manifold-coord-benchmark-results-v3.json"
    payload = {
        "benchmark": "manifold-coord-benchmark-2026-08-06",
        "version": "v3 - Fix A targets (mode-1 in span, mode-2 out); PR #193 complement to PR #192 v4",
        "seeds": SEEDS,
        "train_frac": TRAIN_FRAC,
        "lam_grid": LAMBDA_GRID,
        "meta": {
            "n_points": N_POINTS,
            "seeds": SEEDS,
            "train_frac": TRAIN_FRAC,
            "lam_grid": LAMBDA_GRID,
            "L_SPHERE": L_SPHERE,
            "K_FOURIER_PER_DIM": K_FOURIER_PER_DIM,
            "sphere_basis_size": SH_BASIS_SIZE,
            "flat_basis_size": FLAT_BASIS_SIZE,
            "flat_effective_rank": 9,
            "T2_target_formula": "sin(theta)*cos(phi) + 0.5*sin(2*theta)*cos(2*phi)",
            "S2_target_formula": "sin(arccos(z))^3 * cos(3*atan2(y,x))  [real Y_3^3]",
            "lstsq_at_N4000": {
                "T2_flat_R2": 0.8001,
                "T2_sphere_R2": 0.5775,
                "S2_sphere_R2": 1.0000,
                "S2_flat_R2": 0.0022,
            },
            "fix_design": "Fix A - mode-1 in flat K=2 span, mode-2 out of both arms (topology matters where both must extrapolate); S^2 target IS the Y_3^3 basis function (in SH L=3 span, not in flat K=2 span on (lon, lat))",
            "no_noise": True,
        },
        "design": results["design"],
        "per_seed": {
            "T2": {"sphere": results["T2"]["sphere"],
                   "flat": results["T2"]["flat"]},
            "S2": {"sphere": results["S2"]["sphere"],
                   "flat": results["S2"]["flat"]},
        },
        "per_seed_lambda": {
            "T2": {"sphere": results["T2"]["sphere_lambda"],
                   "flat": results["T2"]["flat_lambda"]},
            "S2": {"sphere": results["S2"]["sphere_lambda"],
                   "flat": results["S2"]["flat_lambda"]},
        },
        "per_seed_delta": {
            "T2_sphere_minus_flat": results["per_seed_delta_T2"],
            "S2_sphere_minus_flat": results["per_seed_delta_S2"],
        },
        "summary": results["summary"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with open(json_path, "w") as f:
        json.dump(payload, f, indent=2)
    print()
    print("results JSON: %s (%d bytes)" % (json_path, json_path.stat().st_size))

    chart_path = out_dir / "chart-manifold-coord-2026-08-06-v3.png"
    render_chart(results, str(chart_path))
    print("chart PNG: %s (%d bytes)" % (chart_path, chart_path.stat().st_size))


if __name__ == "__main__":
    main()
