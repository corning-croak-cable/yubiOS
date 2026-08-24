#!/usr/bin/env python3
"""gapD_zernike_lens.py -- Zernike Slot 1: the ABERRATED lens extension of Gap D.

Extends the Gap D lens family from Mobius-only (6 real dof, conformal, hence
aberration-free in the papers' own optical dictionary) to

    Mobius  o  (low-order Zernike aberration displacement)

applied to the PRE-LIFT PCA disk coordinates, in the transverse-aberration
convention: displacement = grad W(rho, theta), with

    W = sum_j c_j Z_j,   j in Noll {4 defocus, 5/6 astigmatism, 7/8 coma, 11 spherical}

Z_j are Noll-normalized Zernike polynomials on the unit disk. Disk coordinates
are normalized to the unit disk by the max radius before the displacement is
applied, then rescaled back, so c = 0 reproduces the Mobius-only pipeline
EXACTLY (verified by a self-check against tools/spectral-defocus matrix_to_sphere).

Everything else is inherited verbatim from the existing Gap D machinery:
  - geometry / basis / guard / ridge from papers/scripts/gapD_lens_power.py
    (gap.real_sh_basis, gap.guard_check with RANK_MIN=16 and COND_MAX=1e3,
     gap.ridge_fit_energy_share with RIDGE_LAMBDA=1e-3 and L3_COLS=9..15,
     gap.params_from_delta, gap.mobius_apply, gap.stereo_lift)
  - the corpus pipeline from tools/spectral-defocus/defocus.py
    (z-score columns -> PCA top-2 -> RMS rescale -> stereographic lift;
     scalar field = z-scored PC3)
  - the objective J = (share_real - mean_null) / sd_null on the L=3 ridge
    energy share, and the selection-null control protocol (swap a null draw
    into the target slot) from papers/scripts/gapD_real_corpus_lens.py
  - curveball() copied verbatim from papers/data/lean/verify_claims.py

Measurement-type, not identity-type: every number below faces a seeded null
and none of it is a proof.

Dependencies: stdlib + numpy. Deterministic given --seed.
"""
import argparse
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'spectral-defocus'))
sys.path.insert(0, HERE)

import defocus as dfc
import gapD_lens_power as gap


# --------------------------------------------------------------------------
# curveball -- copied VERBATIM from papers/data/lean/verify_claims.py
# --------------------------------------------------------------------------
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


# --------------------------------------------------------------------------
# Pre-lift disk coordinates: defocus.matrix_to_sphere split before the lift
# --------------------------------------------------------------------------
def matrix_to_disk(matrix):
    mu = matrix.mean(axis=0)
    sigma = matrix.std(axis=0)
    sigma_safe = np.where(sigma > 1e-12, sigma, 1.0)
    z = (matrix - mu) / sigma_safe

    u_full, s_full, vt_full = np.linalg.svd(z, full_matrices=False)
    scores = u_full * s_full
    uv = scores[:, :2]
    pc3 = scores[:, 2] if scores.shape[1] > 2 else scores[:, -1]
    targets = (pc3 - pc3.mean()) / (pc3.std() if pc3.std() > 1e-12 else 1.0)

    rms = math.sqrt(np.mean(np.sum(uv ** 2, axis=1)))
    uv_scaled = uv / rms if rms > 1e-12 else uv
    rmax = float(np.max(np.sqrt(np.sum(uv_scaled ** 2, axis=1))))
    if rmax <= 1e-12:
        rmax = 1.0
    return uv_scaled, targets, rmax


# --------------------------------------------------------------------------
# Noll Zernike gradients on the unit disk (transverse-aberration convention)
# j = 4 defocus, 5/6 astigmatism, 7/8 coma, 11 spherical
# --------------------------------------------------------------------------
NOLL_INDICES = [4, 5, 6, 7, 8, 11]
NOLL_NAMES = ['Z4_defocus', 'Z5_astig_oblique', 'Z6_astig_vertical',
              'Z7_coma_y', 'Z8_coma_x', 'Z11_spherical']
N_ZERN = len(NOLL_INDICES)


def zernike_gradients(xn, yn):
    """Return (gx, gy), each (N, 6): partial derivatives of the Noll-normalized
    Zernike polynomials Z_4, Z_5, Z_6, Z_7, Z_8, Z_11 in Cartesian unit-disk
    coordinates.

    Z4  = sqrt(3) (2 r^2 - 1)
    Z5  = sqrt(6) (2 x y)
    Z6  = sqrt(6) (x^2 - y^2)
    Z7  = sqrt(8) (3 r^2 - 2) y
    Z8  = sqrt(8) (3 r^2 - 2) x
    Z11 = sqrt(5) (6 r^4 - 6 r^2 + 1)
    """
    r2 = xn * xn + yn * yn
    s3 = math.sqrt(3.0)
    s5 = math.sqrt(5.0)
    s6 = math.sqrt(6.0)
    s8 = math.sqrt(8.0)
    gx = np.stack([
        s3 * 4.0 * xn,
        s6 * 2.0 * yn,
        s6 * 2.0 * xn,
        s8 * 6.0 * xn * yn,
        s8 * (6.0 * xn * xn + 3.0 * r2 - 2.0),
        s5 * (24.0 * r2 * xn - 12.0 * xn),
    ], axis=1)
    gy = np.stack([
        s3 * 4.0 * yn,
        s6 * 2.0 * xn,
        -s6 * 2.0 * yn,
        s8 * (6.0 * yn * yn + 3.0 * r2 - 2.0),
        s8 * 6.0 * xn * yn,
        s5 * (24.0 * r2 * yn - 12.0 * yn),
    ], axis=1)
    return gx, gy


def make_dataset(matrix):
    uv, targets, rmax = matrix_to_disk(matrix)
    xn = uv[:, 0] / rmax
    yn = uv[:, 1] / rmax
    gx, gy = zernike_gradients(xn, yn)
    return {'xn': xn, 'yn': yn, 'rmax': rmax, 'gx': gx, 'gy': gy,
            'targets': targets}


def lens_points(ds, coeffs, ma, mb, mc, md):
    """Aberrated lens: unit-disk Zernike displacement, rescale, Mobius, lift."""
    if coeffs is None:
        xn, yn = ds['xn'], ds['yn']
    else:
        xn = ds['xn'] + ds['gx'] @ coeffs
        yn = ds['yn'] + ds['gy'] @ coeffs
    w = (xn * ds['rmax']) + 1j * (yn * ds['rmax'])
    w2 = gap.mobius_apply(w, ma, mb, mc, md)
    return gap.stereo_lift(w2)


ZERO_C = np.zeros(N_ZERN)


class AberratedObjective:
    """J = (share_target - mean_null) / sd_null on the L=3 ridge energy share,
    under the shared anti-caustic guard. datasets[0] is the target."""

    def __init__(self, datasets, penalty=-1e6):
        self.datasets = datasets
        self.penalty = penalty
        self.n_evals = 0
        self.n_rejected = 0

    def evaluate(self, delta, coeffs):
        self.n_evals += 1
        params = gap.params_from_delta(np.asarray(delta, dtype=float))
        if params is None:
            self.n_rejected += 1
            return self.penalty, {'guard_pass': False, 'reason': 'degenerate_mobius'}
        ma, mb, mc, md = params
        shares = []
        worst_cond = 0.0
        for ds in self.datasets:
            pts = lens_points(ds, coeffs, ma, mb, mc, md)
            if not np.all(np.isfinite(pts)):
                self.n_rejected += 1
                return self.penalty, {'guard_pass': False, 'reason': 'non_finite'}
            design = gap.real_sh_basis(pts)
            ok, cond, num_rank = gap.guard_check(design)
            worst_cond = max(worst_cond, cond)
            if not ok:
                self.n_rejected += 1
                return self.penalty, {'guard_pass': False, 'cond': cond,
                                      'num_rank': num_rank}
            share, _, _ = gap.ridge_fit_energy_share(design, ds['targets'])
            shares.append(share)
        target_share = shares[0]
        null_shares = np.array(shares[1:])
        mu0 = float(null_shares.mean())
        sd0 = float(null_shares.std(ddof=1))
        j = (target_share - mu0) / sd0 if sd0 > 1e-12 else 0.0
        return j, {'guard_pass': True, 'worst_cond': worst_cond,
                   'target_share': target_share, 'null_mean': mu0,
                   'null_sd': sd0}


# --------------------------------------------------------------------------
# Optimizers (same random-search + coordinate-refinement scheme as gap.optimize)
# --------------------------------------------------------------------------
def optimize_mobius(obj, rng, n_random, n_coord_rounds, init_step=0.35,
                    coord_step0=0.15, shrink=0.85):
    best_delta = np.zeros(8)
    best_j = None
    best_info = None
    for _ in range(n_random):
        delta = rng.normal(0.0, init_step, size=8)
        j, info = obj.evaluate(delta, ZERO_C)
        if best_j is None or j > best_j:
            best_j, best_delta, best_info = j, delta, info

    identity_j, identity_info = obj.evaluate(np.zeros(8), ZERO_C)
    if best_j is None or identity_j > best_j:
        best_j, best_delta, best_info = identity_j, np.zeros(8), identity_info

    step = coord_step0
    for _round in range(n_coord_rounds):
        improved = False
        for k in range(8):
            for sign in (1.0, -1.0):
                trial = best_delta.copy()
                trial[k] += sign * step
                j, info = obj.evaluate(trial, ZERO_C)
                if j > best_j:
                    best_j, best_delta, best_info = j, trial, info
                    improved = True
        step *= shrink
        if not improved and step < 1e-4:
            break
    return best_delta, best_j, best_info, identity_j, identity_info


def optimize_aberrated(obj, rng, delta0, j0, n_random, n_coord_rounds,
                       z_init_step=0.05, m_step0=0.12, z_step0=0.06,
                       shrink=0.85):
    """Mobius-first, then JOINT refinement over all 14 dof (8 Mobius deltas +
    6 Zernike coefficients). Seeded from the Mobius optimum with c = 0, so the
    aberrated optimum is guaranteed >= the Mobius optimum at this budget."""
    best_delta = np.asarray(delta0, dtype=float).copy()
    best_c = ZERO_C.copy()
    best_j = j0
    best_info = None

    for _ in range(n_random):
        c = rng.normal(0.0, z_init_step, size=N_ZERN)
        j, info = obj.evaluate(best_delta, c)
        if j > best_j:
            best_j, best_c, best_info = j, c, info

    m_step = m_step0
    z_step = z_step0
    for _round in range(n_coord_rounds):
        improved = False
        for k in range(8 + N_ZERN):
            for sign in (1.0, -1.0):
                td = best_delta.copy()
                tc = best_c.copy()
                if k < 8:
                    td[k] += sign * m_step
                else:
                    tc[k - 8] += sign * z_step
                j, info = obj.evaluate(td, tc)
                if j > best_j:
                    best_j, best_delta, best_c, best_info = j, td, tc, info
                    improved = True
        m_step *= shrink
        z_step *= shrink
        if not improved and z_step < 1e-5:
            break

    if best_info is None:
        best_j, best_info = obj.evaluate(best_delta, best_c)
    return best_delta, best_c, best_j, best_info


def run_one(datasets, seed, n_random, n_coord_rounds, n_random_z, n_coord_rounds_z):
    obj = AberratedObjective(datasets)
    rng = np.random.default_rng(seed)
    m_delta, m_j, m_info, id_j, id_info = optimize_mobius(
        obj, rng, n_random=n_random, n_coord_rounds=n_coord_rounds)
    a_delta, a_c, a_j, a_info = optimize_aberrated(
        obj, rng, m_delta, m_j, n_random=n_random_z,
        n_coord_rounds=n_coord_rounds_z)
    return {
        'identity_J': float(id_j),
        'identity_info': id_info,
        'mobius_J': float(m_j),
        'mobius_info': m_info,
        'mobius_delta': [float(v) for v in m_delta],
        'delta_J_mobius': float(m_j - id_j),
        'aberrated_J': float(a_j),
        'aberrated_info': a_info,
        'aberrated_delta': [float(v) for v in a_delta],
        'zernike_coeffs': {NOLL_NAMES[i]: float(a_c[i]) for i in range(N_ZERN)},
        'zernike_coeff_vector': [float(v) for v in a_c],
        'zernike_norm': float(np.linalg.norm(a_c)),
        'delta_J_aberrated': float(a_j - id_j),
        'aberration_gain': float(a_j - m_j),
        'objective_evaluations': obj.n_evals,
        'guard_rejections': obj.n_rejected,
    }


def selfcheck_baseline(matrix):
    """c = 0 with the identity Mobius must reproduce defocus.matrix_to_sphere."""
    pts_ref, tgt_ref = dfc.matrix_to_sphere(matrix)
    ds = make_dataset(matrix)
    pts_mine = lens_points(ds, ZERO_C, 1.0, 0.0, 0.0, 1.0)
    dp = float(np.max(np.abs(pts_mine - pts_ref)))
    dt = float(np.max(np.abs(ds['targets'] - tgt_ref)))
    return {'max_abs_point_diff': dp, 'max_abs_target_diff': dt,
            'pass': bool(dp < 1e-10 and dt < 1e-10)}


def frozen_share(ds, coeffs, delta):
    params = gap.params_from_delta(np.asarray(delta, dtype=float))
    if params is None:
        return None, None
    ma, mb, mc, md = params
    pts = lens_points(ds, coeffs, ma, mb, mc, md)
    if not np.all(np.isfinite(pts)):
        return None, None
    design = gap.real_sh_basis(pts)
    ok, cond, num_rank = gap.guard_check(design)
    share, _, _ = gap.ridge_fit_energy_share(design, ds['targets'])
    return float(share), bool(ok)


def zscore(real_value, null_values):
    arr = np.asarray(null_values, dtype=float)
    mu = float(arr.mean())
    sd = float(arr.std(ddof=1))
    z = (real_value - mu) / sd if sd > 1e-12 else 0.0
    return {'real': float(real_value), 'null_mean': mu, 'null_sd': sd,
            'null_min': float(arr.min()), 'null_max': float(arr.max()),
            'n_draws': int(arr.size), 'z': float(z), 'PASS': bool(z > 3.0)}


def main():
    p = argparse.ArgumentParser(description='Zernike Slot 1: aberrated Gap D lens')
    p.add_argument('--seed', type=int, default=20260824)
    p.add_argument('--n-null', type=int, default=20)
    p.add_argument('--trades-per-row', type=int, default=20)
    p.add_argument('--n-random', type=int, default=150)
    p.add_argument('--n-coord-rounds', type=int, default=20)
    p.add_argument('--n-random-z', type=int, default=120)
    p.add_argument('--n-coord-rounds-z', type=int, default=14)
    p.add_argument('--n-controls', type=int, default=5)
    p.add_argument('--n-admit', type=int, default=32)
    p.add_argument('--zip-path', default=os.path.join(ROOT, dfc.REAL_CORPUS_ZIP))
    p.add_argument('--out', default=None)
    args = p.parse_args()

    t0 = time.time()
    matrix = dfc.load_real_corpus_matrix(zip_path=args.zip_path)
    n_rows, n_cols = matrix.shape
    print('corpus %dx%d' % (n_rows, n_cols))

    sc = selfcheck_baseline(matrix)
    print('selfcheck_baseline %s' % json.dumps(sc))

    null_rng = np.random.default_rng(args.seed)
    datasets = [make_dataset(matrix)]
    for i in range(args.n_null):
        Mn = curveball(matrix, args.trades_per_row * n_rows, null_rng)
        datasets.append(make_dataset(Mn))
        print('null draw %d/%d built  t=%.1fs' % (i + 1, args.n_null, time.time() - t0))

    real = run_one(datasets, args.seed, args.n_random, args.n_coord_rounds,
                   args.n_random_z, args.n_coord_rounds_z)
    print('REAL identity_J=%.4f mobius_J=%.4f dJ_mob=%.4f aberrated_J=%.4f dJ_ab=%.4f gain=%.4f  t=%.1fs'
          % (real['identity_J'], real['mobius_J'], real['delta_J_mobius'],
             real['aberrated_J'], real['delta_J_aberrated'],
             real['aberration_gain'], time.time() - t0))

    controls = []
    n_ctrl = min(args.n_controls, args.n_null)
    for k in range(n_ctrl):
        swapped = list(datasets)
        swapped[0], swapped[k + 1] = swapped[k + 1], swapped[0]
        res = run_one(swapped, args.seed, args.n_random, args.n_coord_rounds,
                      args.n_random_z, args.n_coord_rounds_z)
        res['control_index'] = k
        controls.append(res)
        print('CONTROL %d dJ_mob=%.4f dJ_ab=%.4f gain=%.4f ||c||=%.4f  t=%.1fs'
              % (k, res['delta_J_mobius'], res['delta_J_aberrated'],
                 res['aberration_gain'], res['zernike_norm'], time.time() - t0))

    ctrl_dj_mob = [c['delta_J_mobius'] for c in controls]
    ctrl_dj_ab = [c['delta_J_aberrated'] for c in controls]
    ctrl_gain = [c['aberration_gain'] for c in controls]
    ctrl_cnorm = [c['zernike_norm'] for c in controls]

    # ---- Admission: membership condition on the induced scalar coordinates ----
    win_c = np.array(real['zernike_coeff_vector'], dtype=float)
    win_delta = np.array(real['aberrated_delta'], dtype=float)
    mob_delta = np.array(real['mobius_delta'], dtype=float)

    ds_real = datasets[0]
    s_ab_real, ok_ab_real = frozen_share(ds_real, win_c, win_delta)
    s_mob_real, ok_mob_real = frozen_share(ds_real, ZERO_C, mob_delta)
    d_ab_real = s_ab_real - s_mob_real

    admit_rng = np.random.default_rng(args.seed + 777)
    s_ab_null, s_mob_null, d_ab_null = [], [], []
    guard_fail = 0
    for i in range(args.n_admit):
        Mn = curveball(matrix, args.trades_per_row * n_rows, admit_rng)
        dsn = make_dataset(Mn)
        sa, oka = frozen_share(dsn, win_c, win_delta)
        sm, okm = frozen_share(dsn, ZERO_C, mob_delta)
        if sa is None or sm is None:
            guard_fail += 1
            continue
        if not (oka and okm):
            guard_fail += 1
        s_ab_null.append(sa)
        s_mob_null.append(sm)
        d_ab_null.append(sa - sm)
        print('admit draw %d/%d s_ab=%.6f s_mob=%.6f  t=%.1fs'
              % (i + 1, args.n_admit, sa, sm, time.time() - t0))

    admission = {
        'protocol': 'winning aberrated lens FROZEN; each curveball draw pushed '
                    'through the identical lens; coordinate compared to the real '
                    'corpus value. Bar: z > 3.',
        'n_draws': len(s_ab_null),
        'guard_flags': guard_fail,
        'L3_share_aberrated': zscore(s_ab_real, s_ab_null),
        'L3_share_mobius': zscore(s_mob_real, s_mob_null),
        'aberration_induced_share_gain': zscore(d_ab_real, d_ab_null),
    }

    result = {
        'experiment': 'gapD_zernike_lens',
        'slot': 'Zernike Slot 1 -- aberrated lens extension of Gap D',
        'status': 'executed',
        'seed': args.seed,
        'config': {
            'n_rows': int(n_rows), 'n_cols': int(n_cols),
            'n_null_draws': args.n_null, 'trades_per_row': args.trades_per_row,
            'n_random_draws': args.n_random, 'n_coord_rounds': args.n_coord_rounds,
            'n_random_z': args.n_random_z, 'n_coord_rounds_z': args.n_coord_rounds_z,
            'n_controls': n_ctrl, 'n_admission_draws': args.n_admit,
            'ridge_lambda': gap.RIDGE_LAMBDA,
            'target_degree_columns': gap.L3_COLS,
            'guard_rank_min': gap.RANK_MIN, 'guard_cond_max': gap.COND_MAX,
            'noll_indices': NOLL_INDICES, 'noll_names': NOLL_NAMES,
            'aberration_convention': 'displacement = grad W on unit-disk-normalized '
                                     'pre-lift PCA coords; W = sum c_j Z_j (Noll '
                                     'normalized); epsilon absorbed into c_j',
            'optimizer': 'Mobius-first (random search + coordinate refinement, '
                         'gap.optimize scheme), then JOINT 14-dof refinement '
                         'seeded at (mobius optimum, c=0)',
        },
        'pre_registration': {
            'question': 'Does Delta-J(Mobius+Zernike) exceed Delta-J(Mobius) by more '
                        'than the selection-null control gap? If yes, the corpus '
                        'signal is non-conformal.',
            'H1': 'aberration_gain on the real corpus exceeds the control '
                  'aberration_gain distribution.',
            'H0': 'the aberration gain is indistinguishable from what pure '
                  'margin-noise achieves under identical selection pressure.',
            'admission': 'any induced scalar coordinate must clear z > 3 against '
                         '>= 30 curveball draws to be admissible.',
            'note': 'Both outcomes publishable; negatives recorded prominently.',
        },
        'self_checks': {'mobius_baseline_matches_defocus_pipeline': sc},
        'results': {
            'real': real,
            'controls': controls,
            'control_distribution': {
                'delta_J_mobius': {'values': ctrl_dj_mob,
                                   'mean': float(np.mean(ctrl_dj_mob)),
                                   'sd': float(np.std(ctrl_dj_mob, ddof=1)),
                                   'min': float(np.min(ctrl_dj_mob)),
                                   'max': float(np.max(ctrl_dj_mob))},
                'delta_J_aberrated': {'values': ctrl_dj_ab,
                                      'mean': float(np.mean(ctrl_dj_ab)),
                                      'sd': float(np.std(ctrl_dj_ab, ddof=1)),
                                      'min': float(np.min(ctrl_dj_ab)),
                                      'max': float(np.max(ctrl_dj_ab))},
                'aberration_gain': {'values': ctrl_gain,
                                    'mean': float(np.mean(ctrl_gain)),
                                    'sd': float(np.std(ctrl_gain, ddof=1)),
                                    'min': float(np.min(ctrl_gain)),
                                    'max': float(np.max(ctrl_gain))},
                'zernike_norm': {'values': ctrl_cnorm,
                                 'mean': float(np.mean(ctrl_cnorm)),
                                 'sd': float(np.std(ctrl_cnorm, ddof=1))},
            },
            'real_vs_control': {
                'delta_J_mobius_z_vs_controls': float(
                    (real['delta_J_mobius'] - np.mean(ctrl_dj_mob)) /
                    (np.std(ctrl_dj_mob, ddof=1) if np.std(ctrl_dj_mob, ddof=1) > 1e-12 else 1.0)),
                'delta_J_aberrated_z_vs_controls': float(
                    (real['delta_J_aberrated'] - np.mean(ctrl_dj_ab)) /
                    (np.std(ctrl_dj_ab, ddof=1) if np.std(ctrl_dj_ab, ddof=1) > 1e-12 else 1.0)),
                'aberration_gain_z_vs_controls': float(
                    (real['aberration_gain'] - np.mean(ctrl_gain)) /
                    (np.std(ctrl_gain, ddof=1) if np.std(ctrl_gain, ddof=1) > 1e-12 else 1.0)),
                'real_gain_exceeds_all_controls': bool(
                    real['aberration_gain'] > max(ctrl_gain)),
            },
            'admission': admission,
        },
        'wall_time_seconds': time.time() - t0,
        'limitations': [
            'Measurement-type result. Nothing here is a proof; no claim is elevated '
            'to a theorem.',
            'Small optimizer budget; every reported J is a LOWER bound on what a '
            'stronger optimizer would find, for the real corpus and the controls alike.',
            'The aberrated optimum is seeded at (Mobius optimum, c=0), so '
            'aberration_gain >= 0 by construction. The scientific content is '
            'therefore entirely in the comparison of the REAL gain against the '
            'CONTROL gain distribution, not in the gain being positive.',
            'The membership condition is applied to the induced FROZEN-lens '
            'coordinates (L=3 share under the winning aberrated lens, and the '
            'aberration-induced share gain). A >= 30-draw null on ||c|| itself '
            'would require >= 30 full re-optimizations and is out of the runner '
            'budget; only the 5 selection-null control optimizations sample it.',
            'PC3-as-field is the documented spectral-defocus convention, not '
            'dictated verbatim by the papers.',
            'The corpus is atomic (176/2286 distinct rows); ridge shares on an '
            'atomic field inherit that structure.',
            "Naming collision flagged per Slot 4: Zernike Z_4 'defocus' is a "
            'deterministic quadratic rephasing and is NOT the spherical heat-flow '
            'defocus in t used elsewhere in this program.',
        ],
    }

    print('RESULT_JSON ' + json.dumps(result, default=str))
    txt = json.dumps(result, indent=2, default=str)
    if args.out:
        with open(args.out, 'w') as fh:
            fh.write(txt + chr(10))
        print('wrote %s' % args.out)


if __name__ == '__main__':
    main()
