#!/usr/bin/env python3
"""gapD_loxodromic_navigation.py -- loxodromic navigation of the optimized lens.

The optimized real-corpus lens (data/gapD/lens-geometry-2026-08-22.json) is
loxodromic: its orbits are rhumb lines on S^2. Three pre-registered
experiments (2026-08-22, registered before execution):

(1) FLOW TRACE. M has canonical fractional powers M^t (principal branch of
    the eigenvalue log). Trace J(t) and the design condition number along
    t in [0, 1.5] (step 0.05), with the SAME real corpus + 20 curveball
    draws (seed 20260822) as the original run. Consistency: J(1) must
    reproduce the recorded +124.59 within 1.0.
    H1a: J(t) is monotone increasing on the admissible part of [0, 1]
         (Spearman rho >= 0.9).
    H1b: the last admissible grid point t_max has J(t_max) >= J(1), i.e.
         the discrete optimum sits on (not past) the boundary along its
         own flow.

(2) MERCATOR FLOW COORDINATES. Conjugate zeta = (w - z_att)/(w - z_rep)
    (attracting -> 0, repelling -> inf); the lens becomes zeta -> kappa*zeta.
    Flow coordinates per row: u = log|zeta| / log|kappa| (flow time),
    v = arg zeta (phase). Descriptive: percentiles of u, circular
    concentration of v, Spearman(u, row margin).

(3) ADMISSION NULL ON u. Per the membership condition, the flow coordinate
    must face the curveball null before admission. Statistic S = sd(u)
    (dispersion along the flow axis), computed identically on the real
    corpus and on each of 20 curveball draws mapped through the SAME
    frozen conjugation. Admit iff |z| >= 3 and the null is non-degenerate.
    Secondary (descriptive only): circular variance of v.

Dependencies: stdlib + numpy. Deterministic given --seed.
"""
import argparse
import json
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

GEO_PATH = os.path.join(ROOT, 'papers', 'data', 'gapD', 'lens-geometry-2026-08-22.json')


def load_M():
    geo = json.load(open(GEO_PATH))
    p = geo['normalized_params']
    a = complex(p['a'][0], p['a'][1]); b = complex(p['b'][0], p['b'][1])
    c = complex(p['c'][0], p['c'][1]); d = complex(p['d'][0], p['d'][1])
    return np.array([[a, b], [c, d]], dtype=complex)


def mobius_power(M, t):
    vals, vecs = np.linalg.eig(M)
    pw = np.exp(t * np.log(vals))
    Mt = vecs @ np.diag(pw) @ np.linalg.inv(vecs)
    det = Mt[0, 0] * Mt[1, 1] - Mt[0, 1] * Mt[1, 0]
    return Mt / np.sqrt(det)


def fixed_points(M):
    vals, vecs = np.linalg.eig(M)
    i_big = int(np.argmax(np.abs(vals)))
    fp = []
    for i in (0, 1):
        x, y = vecs[0, i], vecs[1, i]
        fp.append(x / y if abs(y) > 1e-14 else complex('inf'))
    # eigenvalue with |.|>1 corresponds to the REPELLING fixed point of w->Mw
    # (derivative at fixed point of eigenvector i is (val_j/val_i)... determine empirically below)
    return fp, vals


def shares_at(M2, datasets):
    a, b = M2[0, 0], M2[0, 1]
    c, d = M2[1, 0], M2[1, 1]
    shares = []
    worst_cond = 0.0
    for pts, tg in datasets:
        lensed = gap.apply_lens(pts, a, b, c, d)
        design = gap.real_sh_basis(lensed)
        ok, cond, num_rank = gap.guard_check(design)
        worst_cond = max(worst_cond, cond)
        if not ok:
            return None, worst_cond
        s, _, _ = gap.ridge_fit_energy_share(design, tg)
        shares.append(s)
    return shares, worst_cond


def spearman(x, y):
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    rx -= rx.mean(); ry -= ry.mean()
    den = np.sqrt((rx * rx).sum() * (ry * ry).sum())
    return float((rx * ry).sum() / den) if den > 0 else 0.0


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seed', type=int, default=20260822)
    p.add_argument('--n-null', type=int, default=20)
    p.add_argument('--trades-per-row', type=int, default=20)
    p.add_argument('--t-max', type=float, default=1.5)
    p.add_argument('--t-step', type=float, default=0.05)
    p.add_argument('--out', default=None)
    args = p.parse_args()

    t0 = time.time()
    rng = np.random.default_rng(args.seed)
    matrix = dfc.load_real_corpus_matrix(zip_path=os.path.join(ROOT, dfc.REAL_CORPUS_ZIP))
    n_rows = matrix.shape[0]
    datasets = [dfc.matrix_to_sphere(matrix)]
    for _ in range(args.n_null):
        Mn = dfc.curveball(matrix, args.trades_per_row * n_rows, rng)
        datasets.append(dfc.matrix_to_sphere(Mn))

    M = load_M()

    # ---- (1) flow trace ----
    ts = np.arange(0.0, args.t_max + 1e-9, args.t_step)
    trace = []
    for t in ts:
        Mt = mobius_power(M, float(t))
        shares, cond = shares_at(Mt, datasets)
        if shares is None:
            trace.append({'t': round(float(t), 4), 'admissible': False, 'worst_cond': cond})
            continue
        real = shares[0]; null = np.array(shares[1:])
        sd = null.std(ddof=1)
        J = float((real - null.mean()) / sd) if sd > 1e-12 else 0.0
        trace.append({'t': round(float(t), 4), 'admissible': True, 'J': J,
                      'real_share': float(real), 'null_mean': float(null.mean()),
                      'null_sd': float(sd), 'worst_cond': float(cond)})
    adm = [r for r in trace if r['admissible']]
    j1 = next((r['J'] for r in trace if abs(r['t'] - 1.0) < 1e-9 and r['admissible']), None)
    consistency_ok = bool(j1 is not None and abs(j1 - 124.5907) < 1.0)
    unit = [r for r in adm if r['t'] <= 1.0 + 1e-9]
    rho = spearman(np.array([r['t'] for r in unit]), np.array([r['J'] for r in unit]))
    t_last = adm[-1]['t'] if adm else None
    j_last = adm[-1]['J'] if adm else None
    first_inadm = next((r['t'] for r in trace if not r['admissible']), None)
    h1a = bool(rho >= 0.9)
    h1b = bool(j_last is not None and j1 is not None and j_last >= j1)

    # ---- (2) Mercator flow coordinates ----
    fps, vals = fixed_points(M)
    # classify: attracting fixed point has |derivative| < 1; derivative of Mobius at
    # fixed point z with matrix [[a,b],[c,d]], det 1: 1/(c*z+d)**2
    a_, b_ = M[0, 0], M[0, 1]; c_, d_ = M[1, 0], M[1, 1]
    der = [abs(1.0 / (c_ * z + d_) ** 2) for z in fps]
    z_att = fps[0] if der[0] < 1 else fps[1]
    z_rep = fps[1] if der[0] < 1 else fps[0]
    # multiplier kappa: apply M to a probe and measure in conjugated chart
    def conj(w):
        return (w - z_att) / (w - z_rep)
    probe = 0.3 + 0.2j
    Mp = (a_ * probe + b_) / (c_ * probe + d_)
    kappa = conj(Mp) / conj(probe)
    log_kappa = np.log(abs(kappa))

    def flow_coords(pts):
        w = gap.stereo_project(pts)
        zeta = (w - z_att) / (w - z_rep)
        u = np.log(np.abs(zeta)) / log_kappa
        v = np.angle(zeta)
        return u, v

    u_real, v_real = flow_coords(datasets[0][0])
    margins = matrix.sum(axis=1)
    circ_conc = float(abs(np.exp(1j * v_real).mean()))
    coords = {
        'kappa': [float(kappa.real), float(kappa.imag)], 'abs_kappa': float(abs(kappa)),
        'u_percentiles': {str(q): float(np.percentile(u_real, q)) for q in (1, 5, 25, 50, 75, 95, 99)},
        'u_sd': float(u_real.std(ddof=1)),
        'v_circular_concentration_R': circ_conc,
        'spearman_u_vs_row_margin': spearman(u_real, margins),
        'n_rows': int(n_rows),
    }

    # ---- (3) admission null on u ----
    S_real = float(u_real.std(ddof=1))
    S_null = []
    v_conc_null = []
    for pts, tg in datasets[1:]:
        un, vn = flow_coords(pts)
        S_null.append(float(un.std(ddof=1)))
        v_conc_null.append(float(abs(np.exp(1j * vn).mean())))
    S_null = np.array(S_null)
    mu0, sd0 = float(S_null.mean()), float(S_null.std(ddof=1))
    degenerate = bool(sd0 <= 1e-9)
    zS = float((S_real - mu0) / sd0) if not degenerate else float('nan')
    admitted = bool((not degenerate) and abs(zS) >= 3.0)

    result = {
        'experiment': 'gapD_loxodromic_navigation',
        'seed': args.seed,
        'flow_trace': {
            'consistency_J1': j1, 'consistency_ok': consistency_ok,
            'spearman_rho_on_unit': rho, 'H1a_monotone': h1a,
            't_last_admissible': t_last, 'J_at_t_last': j_last,
            'first_inadmissible_t': first_inadm, 'H1b_boundary_optimum': h1b,
            'trace': trace,
        },
        'flow_coordinates': coords,
        'u_admission': {
            'statistic': 'sd(u) across rows', 'S_real': S_real,
            'null_mean': mu0, 'null_sd': sd0, 'z': zS, 'degenerate': degenerate,
            'admitted': admitted,
            'secondary_v_concentration': {'real': circ_conc,
                'null_mean': float(np.mean(v_conc_null)), 'null_sd': float(np.std(v_conc_null, ddof=1))},
        },
        'wall_time_seconds': time.time() - t0,
    }
    txt = json.dumps(result, indent=2, default=str)
    if args.out:
        with open(args.out, 'w') as fh:
            fh.write(txt + chr(10))
        print('wrote %s' % args.out)
    else:
        print(txt)


if __name__ == '__main__':
    main()
