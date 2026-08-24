#!/usr/bin/env python3
# corpus-sonometer -- a level meter for corpus effects, reported in dBc.
#
# Definition: the corpus level of an observed effect x against a null
# ensemble with mean mu and RMS fluctuation sigma is
#     L = 20 * log10(|x - mu| / sigma)   [dBc]
# referenced so 0 dBc == the vacuum's own RMS fluctuation -- the smallest
# detectable effect, the acoustician's 20 microPascal. The identity-side
# laws that make a level scale meaningful (levels add over cascaded
# gains, squaring doubles the level, readings are injective) are
# machine-checked in papers/data/lean/CurvedCorpus.lean section 12.
# This tool is the measurement instrument; verify_claims.py claim 8
# applies it to the real corpus matrix (published effect: z = +12.13,
# i.e. +21.68 dBc above the curveball vacuum).
#
# Usage: sonometer.py --selftest
import argparse, math, sys
import numpy as np


def level_db(delta, sigma):
    return 20.0 * math.log10(abs(delta) / sigma)


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


def corpus_level(M, draws, window, rng):
    N = M.shape[0]
    vals = [v2_corr(curveball(M, window * N, rng)) for _ in range(draws)]
    mu = float(np.mean(vals))
    sd = float(np.std(vals, ddof=1))
    return level_db(v2_corr(M) - mu, sd), mu, sd


def selftest():
    oks = []
    def chk(name, cond, detail=''):
        print('%s %s %s' % (name, 'PASS' if cond else 'FAIL', detail), flush=True)
        oks.append(cond)
    # identity-side spot checks (float shadows of Lean sec. 12)
    chk('LEVEL_10SIGMA_IS_20DB', abs(level_db(10.0, 1.0) - 20.0) < 1e-12)
    chk('LEVEL_DOUBLE_IS_6DB', abs(level_db(2.0, 1.0) - 6.020599913279624) < 1e-9)
    a, b = 3.7, 11.9
    chk('CASCADE_LEVELS_ADD', abs(level_db(a * b, 1.0) - (level_db(a, 1.0) + level_db(b, 1.0))) < 1e-9)
    chk('SQUARE_DOUBLES_LEVEL', abs(level_db(a * a, 1.0) - 2 * level_db(a, 1.0)) < 1e-9)
    # measurement-side: quiet matrix vs planted effect
    rng = np.random.default_rng(20260824)
    n, d, k = 400, 9, 4
    M = np.zeros((n, d), dtype=np.int8)
    for i in range(n):
        M[i, (i + np.arange(k)) % d] = 1
    Mq = curveball(M, 20 * n, rng)
    Mp = Mq.copy()
    Mp[:, 1] = Mp[:, 0]
    Lq, muq, sdq = corpus_level(Mq, 12, 10, rng)
    Lp, mup, sdp = corpus_level(Mp, 12, 10, rng)
    chk('QUIET_MATRIX_BELOW_14DBC', Lq < 14.0, 'L=%.2f dBc (typical fibre draw vs own null)' % Lq)
    chk('PLANTED_EFFECT_ABOVE_6DBC', Lp > 6.0, 'L=%.2f dBc (duplicated column)' % Lp)
    Mc = curveball(Mq, 500, rng)
    chk('MARGINS_PRESERVED', bool((Mc.sum(0) == Mq.sum(0)).all() and (Mc.sum(1) == Mq.sum(1)).all()))
    if all(oks):
        print('SONOMETER SELFTEST: ALL PASS')
        return 0
    print('SONOMETER SELFTEST: FAIL')
    return 1


def main():
    ap = argparse.ArgumentParser(description='corpus level meter (dBc)')
    ap.add_argument('--selftest', action='store_true')
    args = ap.parse_args()
    if args.selftest:
        sys.exit(selftest())
    ap.print_help()


if __name__ == '__main__':
    main()
