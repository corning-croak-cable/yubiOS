#!/usr/bin/env python3
"""gapD_real_corpus_lens.py -- Gap D follow-up: the lens vs the REAL corpus.

Runs the Mobius-lens optimization of gapD_lens_power.py against the real
2286x9 corpus behind its matched curveball null, instead of a planted
synthetic field.

Design (pre-registered before execution, 2026-08-22):
- Real corpus: papers/is-this-x-2026-08-12-Final.zip per_row_coverage_v3.json,
  mapped to S^2 by the documented tools/spectral-defocus protocol (z-score
  columns -> PCA -> PC1/PC2 stereographic lift; scalar field = z-scored PC3).
- Matched null: --n-null curveball draws (Strona trades; BOTH margins exactly
  preserved, the Lean-proved fibre moves), each mapped through the SAME
  matrix->sphere pipeline, computed ONCE up front. Positions and field per
  draw are fixed; only the lens phi_theta varies during optimization.
- Objective J(phi) = (share_real(phi) - mean_null(phi)) / sd_null(phi), where
  share is the L=3 ridge energy share at the lensed points -- the identical
  estimator to gapD_lens_power.py (same basis, same ridge lambda, same guard).
- Anti-caustic guard must pass on the real design AND on every null design;
  otherwise the candidate phi is rejected with the standard penalty.
- H1 (same pre-registered bar): optimized J exceeds identity J by more than
  2 (J is already null-standardized). Both outcomes are publishable and
  recorded honestly.

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


class RealCorpusObjective:
    def __init__(self, datasets, penalty=-1e6):
        self.datasets = datasets  # [0] = real, rest = null draws
        self.penalty = penalty
        self.n_evals = 0
        self.n_rejected = 0

    def evaluate(self, a, b, c, d):
        self.n_evals += 1
        shares = []
        worst_cond = 0.0
        for pts, tg in self.datasets:
            lensed = gap.apply_lens(pts, a, b, c, d)
            design = gap.real_sh_basis(lensed)
            ok, cond, num_rank = gap.guard_check(design)
            worst_cond = max(worst_cond, cond)
            if not ok:
                self.n_rejected += 1
                return self.penalty, {'guard_pass': False, 'cond': cond, 'num_rank': num_rank}
            share, _, _ = gap.ridge_fit_energy_share(design, tg)
            shares.append(share)
        real_share = shares[0]
        null_shares = np.array(shares[1:])
        mu0 = float(null_shares.mean())
        sd0 = float(null_shares.std(ddof=1))
        j = (real_share - mu0) / sd0 if sd0 > 1e-12 else 0.0
        return j, {'guard_pass': True, 'worst_cond': worst_cond,
                   'real_share': real_share, 'null_mean': mu0, 'null_sd': sd0}


def main():
    p = argparse.ArgumentParser(description='Gap D real-corpus lens run')
    p.add_argument('--seed', type=int, default=20260822)
    p.add_argument('--n-null', type=int, default=20)
    p.add_argument('--trades-per-row', type=int, default=20)
    p.add_argument('--n-random', type=int, default=150)
    p.add_argument('--n-coord-rounds', type=int, default=20)
    p.add_argument('--zip-path', default=os.path.join(ROOT, dfc.REAL_CORPUS_ZIP))
    p.add_argument('--out', default=None)
    args = p.parse_args()

    t0 = time.time()
    rng = np.random.default_rng(args.seed)
    matrix = dfc.load_real_corpus_matrix(zip_path=args.zip_path)
    n_rows = matrix.shape[0]
    datasets = [dfc.matrix_to_sphere(matrix)]
    for _ in range(args.n_null):
        Mn = dfc.curveball(matrix, args.trades_per_row * n_rows, rng)
        datasets.append(dfc.matrix_to_sphere(Mn))

    obj = RealCorpusObjective(datasets)
    best_delta, best_j, best_info, identity_j, identity_info = gap.optimize(
        obj, rng, n_random=args.n_random, n_coord_rounds=args.n_coord_rounds)
    a, b, c, d = (complex(v) for v in gap.params_from_delta(best_delta))
    delta_sd = float(best_j - identity_j)
    h1 = bool(delta_sd > 2.0)

    result = {
        'experiment': 'gapD_real_corpus_lens',
        'status': 'executed',
        'seed': args.seed,
        'config': {
            'n_rows': int(n_rows), 'n_null_draws': args.n_null,
            'trades_per_row': args.trades_per_row,
            'n_random_draws': args.n_random, 'n_coord_rounds': args.n_coord_rounds,
            'ridge_lambda': gap.RIDGE_LAMBDA, 'target_degree_columns': gap.L3_COLS,
            'guard_rank_min': gap.RANK_MIN, 'guard_cond_max': gap.COND_MAX,
        },
        'pre_registration': {
            'H1': 'optimized J exceeds identity J by more than 2 (null-standardized): '
                  'a Mobius chart exists that concentrates the REAL corpus field '
                  'L=3 energy share beyond its fixed-margin null, more than the '
                  'identity chart does.',
            'H0': 'no such chart found at this budget; the lens adds nothing on the '
                  'real corpus.',
            'note': 'Both outcomes publishable; recorded honestly either way.',
        },
        'results': {
            'identity_J': identity_j,
            'identity_info': identity_info,
            'best_J': best_j,
            'best_info': best_info,
            'delta_J_sd': delta_sd,
            'H1_supported': h1,
            'best_theta': {
                'a': {'re': a.real, 'im': a.imag}, 'b': {'re': b.real, 'im': b.imag},
                'c': {'re': c.real, 'im': c.imag}, 'd': {'re': d.real, 'im': d.imag},
                'ad_minus_bc': complex(a * d - b * c).real,
            },
            'total_objective_evaluations': obj.n_evals,
            'guard_rejections': obj.n_rejected,
        },
        'wall_time_seconds': time.time() - t0,
        'limitations': [
            'PC3-as-field is the documented spectral-defocus convention, not '
            'dictated verbatim by the papers.',
            'Small optimizer budget; best_J is a lower bound.',
            'The corpus is atomic (176/2286 distinct rows); ridge shares on an '
            'atomic field inherit that structure.',
        ],
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
