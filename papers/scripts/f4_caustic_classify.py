#!/usr/bin/env python3
"""F4 caustic classification via aberration / catastrophe theory (Zernike Slot 2).

Operationalizes the open Gap E of curved-corpus-unified-2026-08-22-v2:
"classification of these degeneracies (fold vs structural collapse) is
catastrophe-theoretic and left open".

Route: the 14 machine-precision V2=1.0000 rows are read from the RECORDED
dimension ladder (ladder_VD.json / ladder-VD.json) shipped inside
papers/is-this-x-2026-08-12-Final.zip, and each degenerate design is
reconstructed by importing the bundle's OWN pipeline code
(scripts/common.py, scripts/ladder_correlations.py) and re-running
build_ladder on the bundle's own corpora, with the recomputed V2 checked
against the recorded V2.

All classification fits are MEASUREMENTS, not theorems.

Seeded, numpy only.
"""
import argparse
import json
import math
import os
import sys
import tempfile
import zipfile

import numpy as np

BUNDLE = os.path.join('papers', 'is-this-x-2026-08-12-Final.zip')
ROOTNAME = 'is-this-x-2026-08-12'
SEED = 20260824
TOL_EXACT = 1e-9

Z_NAMES = {1: 'piston', 2: 'tilt_x', 3: 'tilt_y', 4: 'defocus', 5: 'astig_oblique',
           6: 'astig_vertical', 7: 'coma_y', 8: 'coma_x', 9: 'trefoil_y',
           10: 'trefoil_x', 11: 'spherical'}


def log(m):
    print(m, flush=True)


# ---------------------------------------------------------------- bundle io
def unpack():
    d = tempfile.mkdtemp()
    zipfile.ZipFile(BUNDLE).extractall(d)
    return os.path.join(d, ROOTNAME)


def read_recorded_ladder(root):
    cands = [os.path.join(root, 'results', 'ladder_VD.json'),
             os.path.join(root, 'timeseries', 'new-series', 'ladder-VD.json')]
    for p in cands:
        if not os.path.exists(p):
            continue
        obj = json.load(open(p))
        rows = obj.get('rows') or obj.get('records') or []
        norm = []
        for r in rows:
            if 'corpus' in r and 'dim_key' in r:
                corpus, dim_key = r['corpus'], r['dim_key']
            elif 'run_id' in r and '::' in r['run_id']:
                corpus, dim_key = r['run_id'].split('::', 1)
            elif 'params' in r:
                corpus, dim_key = r['params'].get('corpus'), r['params'].get('dim_key')
            else:
                continue
            norm.append(dict(corpus=corpus, dim_key=dim_key, V2=float(r['V2']),
                             D=int(r.get('D') or r.get('params', {}).get('D') or 0),
                             d_eff=int(r.get('d_eff') or r.get('params', {}).get('d_eff') or 0)))
        if norm:
            return os.path.relpath(p, root), norm
    return None, []


def load_pipeline(root):
    sys.path.insert(0, os.path.join(root, 'scripts'))
    import common as C
    import ladder_correlations as L
    real = os.path.join(root, 'data', 'real', 'per_row_coverage_v3.json')
    X, _, _ = C.load_real_matrix(real)
    ds = os.path.join(root, 'data', 'samples')
    zi = np.load(os.path.join(ds, 'family_i_latent_class.npz'))
    zii = np.load(os.path.join(ds, 'family_ii_curved.npz'))
    ziii = np.load(os.path.join(ds, 'family_iii_gwtc.npz'))
    corpora = {
        'real_yubios_2286x9': (X, 11),
        'gen_latent2class_2286x9': (zi['lc2_N2286_d9'].astype(float), 21),
        'gen_latent1class_2286x9': (zi['lc1_N2286_d9'].astype(float), 31),
        'gen_latent3class_2286x9': (zi['lc3_N2286_d9'].astype(float), 41),
        'gen_curved_s1_2048x9': (zii['cv_N2048_d9_s1.0_r0'].astype(float), 51),
        'gen_curved_s0_2048x9': (zii['cv_N2048_d9_s0.0_r0'].astype(float), 61),
        'gen_gwtc_1000x9': (ziii['gwtc_N1000'].astype(float), 71),
    }
    return C, L, corpora


# ------------------------------------------------------------ disk geometry
def disk_coords(P):
    den = 1.0 + P[:, 2]
    safe = np.where(np.abs(den) > 1e-12, den, 1e-12)
    u = P[:, 0] / safe
    v = P[:, 1] / safe
    bad = np.abs(den) <= 1e-12
    u[bad] = 0.0
    v[bad] = 0.0
    return u, v


def lift_angles(u, v):
    r2 = u * u + v * v
    den = 1.0 + r2
    sx, sy, sz = 2 * u / den, 2 * v / den, (r2 - 1.0) / den
    theta = np.arccos(np.clip(sz, -1.0, 1.0))
    phi = np.arctan2(sy, sx)
    return theta, phi


def numerical_rank(M):
    s = np.linalg.svd(M, compute_uv=False)
    tol = max(M.shape) * np.finfo(float).eps * (s[0] if s.size else 0.0)
    return int((s > tol).sum()), s


# --------------------------------------------------------------- Zernike j<=11
def zernike11(x, y, rmax):
    r = np.sqrt(x * x + y * y) / rmax
    t = np.arctan2(y, x)
    s2, s3, s5, s6, s8 = math.sqrt(2.0), math.sqrt(3.0), math.sqrt(5.0), math.sqrt(6.0), math.sqrt(8.0)
    cols = [np.ones_like(r),
            2 * r * np.cos(t),
            2 * r * np.sin(t),
            s3 * (2 * r ** 2 - 1),
            s6 * r ** 2 * np.sin(2 * t),
            s6 * r ** 2 * np.cos(2 * t),
            s8 * (3 * r ** 3 - 2 * r) * np.sin(t),
            s8 * (3 * r ** 3 - 2 * r) * np.cos(t),
            s8 * r ** 3 * np.sin(3 * t),
            s8 * r ** 3 * np.cos(3 * t),
            s5 * (6 * r ** 4 - 6 * r ** 2 + 1)]
    del s2
    return np.column_stack(cols)


def lsq_fit(A, b):
    coef, *_ = np.linalg.lstsq(A, b, rcond=None)
    pred = A @ coef
    ss = float(((b - pred) ** 2).sum())
    tot = float(((b - b.mean()) ** 2).sum())
    r2 = 1.0 - ss / tot if tot > 0 else float('nan')
    return coef, r2


POLY = [(a, b) for a in range(5) for b in range(5) if a + b <= 4]


def poly_design(s, t):
    return np.column_stack([s ** a * t ** b for (a, b) in POLY])


def cubic_discriminant(c30, c21, c12, c03):
    return (18 * c30 * c21 * c12 * c03 - 4 * c21 ** 3 * c03 + c21 ** 2 * c12 ** 2
            - 4 * c30 * c12 ** 3 - 27 * c30 ** 2 * c03 ** 2)


# ------------------------------------------------------------------- ray map
def make_basis_fn(L, dim_key):
    if dim_key == '2_pca':
        def f(u, v):
            return np.column_stack([u, v])
        return f, 'identity_on_disk(D=2 PCA scores)'
    if dim_key.startswith('384_'):
        variant = dim_key[len('384_'):]

        def f(u, v):
            th, ph = lift_angles(u, v)
            return L.fib_lobe_basis(th, ph, variant)
        return f, 'stereographic_lift -> fib_lobe_basis(' + variant + ')'
    if dim_key == '16_sh_L3':
        def f(u, v):
            th, ph = lift_angles(u, v)
            import common as C
            return C.real_sh_L3(th, ph)
        return f, 'stereographic_lift -> real_sh_L3'
    raise ValueError(dim_key)


def jac_fd(phi_fn, u, v, h):
    a = phi_fn(u + h, v)
    b = phi_fn(u - h, v)
    c = phi_fn(u, v + h)
    d = phi_fn(u, v - h)
    du = (a - b) / (2 * h)
    dv = (c - d) / (2 * h)
    return du, dv


# --------------------------------------------------------------- Gap E tests
def gap_e(C, M, dim_key, X, sc_full, rng):
    out = {}
    base_v2 = float(C.v2(M))
    N, D = M.shape

    def probe(M2):
        rk, s = numerical_rank(M2)
        return dict(rank=int(rk), V2=float(C.v2(M2)))

    if dim_key == '2_pca':
        add_col = sc_full[:, 2:3]
        add_label = 'PC3 (next column of the same PCA family)'
        rep = np.column_stack([M[:, 0], sc_full[:, 2]])
        rep_label = 'PC2 replaced by PC3 (in-family)'
    else:
        add_col = M[:, :1] * np.cos(0.5) - M[:, 1:2] * np.sin(0.5)
        add_label = 'one more phase-offset column of the same lobe family'
        rep = M.copy()
        rep[:, 0] = M[:, 0] * np.cos(0.7) - M[:, 1] * np.sin(0.7)
        rep_label = 'column 0 replaced by another phase offset (in-family)'

    out['in_family_add'] = probe(np.column_stack([M, add_col]))
    out['in_family_add']['what'] = add_label
    out['in_family_replace'] = probe(rep)
    out['in_family_replace']['what'] = rep_label

    g = rng.standard_normal((N, 1))
    out['generic_add'] = probe(np.column_stack([M, g]))
    out['generic_add']['what'] = 'append one generic seeded N(0,1) column'
    Mr = M.copy()
    Mr[:, -1] = g[:, 0]
    out['generic_replace'] = probe(Mr)
    out['generic_replace']['what'] = 'replace last column with a generic seeded N(0,1) column'

    sweep = []
    scale = float(np.linalg.norm(M[:, 0])) / max(1.0, math.sqrt(N))
    noise = rng.standard_normal(N)
    noise = noise / max(1e-30, float(np.linalg.norm(noise)) / math.sqrt(N))
    for e in [1e-8, 1e-6, 1e-4, 1e-3, 1e-2, 1e-1]:
        Me = M.copy()
        Me[:, 0] = Me[:, 0] + e * scale * noise
        rk, _ = numerical_rank(Me)
        sweep.append(dict(eps=e, rank=int(rk), V2=float(C.v2(Me))))
    out['eps_sweep'] = dict(what='one column additively perturbed by eps*scale*seeded noise',
                            rows=sweep)
    ok = [r for r in sweep if (1.0 - r['V2']) > 1e-12 and r['eps'] >= 1e-6]
    if len(ok) >= 3:
        lx = np.log10([r['eps'] for r in ok])
        ly = np.log10([1.0 - r['V2'] for r in ok])
        A = np.column_stack([np.ones_like(lx), lx])
        cf, r2 = lsq_fit(A, ly)
        out['eps_sweep']['loglog_exponent'] = float(cf[1])
        out['eps_sweep']['loglog_R2'] = float(r2)

    persists = (out['in_family_add']['rank'] == 2 and out['in_family_replace']['rank'] == 2
                and abs(out['in_family_add']['V2'] - 1.0) < 1e-9
                and abs(out['in_family_replace']['V2'] - 1.0) < 1e-9)
    out['base_V2'] = base_v2
    out['verdict'] = 'persists (structural collapse)' if persists else 'unfolds (fold-like)'
    return out


# ------------------------------------------------------------------- analyse
def analyse(C, L, name, seed, X, dim_key, recorded_V2, rng):
    rec = dict(corpus=name, dim_key=dim_key, seed=int(seed), recorded_V2=recorded_V2)
    sc_full = C.pca_scores(X, min(4, X.shape[1]))
    sc = C.pca_scores(X, 2)
    P = C.stereographic_lift(sc)
    u, v = disk_coords(P)
    rmax = float(np.max(np.sqrt(u * u + v * v)))

    basis_fn, ray_desc = make_basis_fn(L, dim_key)
    M = basis_fn(u, v)
    if dim_key == '2_pca':
        M = sc
    rk, sv = numerical_rank(M)
    v2 = float(C.v2(M))
    rec.update(D=int(M.shape[1]), N=int(M.shape[0]), recomputed_V2=v2,
               V2_match=bool(abs(v2 - recorded_V2) < 1e-9),
               numerical_rank=int(rk),
               singular_values_top5=[float(x) for x in sv[:5]],
               cond_top2=float(sv[0] / sv[1]) if sv.size > 1 and sv[1] > 0 else None,
               ray_map=ray_desc, disk_rmax=rmax)

    U, S, Vt = np.linalg.svd(M, full_matrices=False)
    W2 = Vt[:2].T

    def phi_fn(uu, vv):
        return basis_fn(uu, vv) @ W2

    Phi = phi_fn(u, v)

    Z = zernike11(u, v, rmax)
    zc = {}
    for comp in (0, 1):
        coef, r2 = lsq_fit(Z, Phi[:, comp])
        nrm = float(np.linalg.norm(coef)) or 1.0
        zc['component_' + str(comp + 1)] = dict(
            R2=float(r2),
            coefficients={Z_NAMES[j + 1]: float(coef[j] / nrm) for j in range(11)},
            dominant=sorted([(Z_NAMES[j + 1], abs(float(coef[j] / nrm))) for j in range(11)],
                            key=lambda kv: -kv[1])[:3])
    rec['zernike_fit_noll_le11'] = zc

    h = 1e-4 * max(rmax, 1.0)
    du, dv = jac_fd(phi_fn, u, v, h)
    det = du[:, 0] * dv[:, 1] - du[:, 1] * dv[:, 0]
    amp = np.linalg.norm(Phi, axis=1)
    lit = amp > (1e-3 * amp.max() if amp.max() > 0 else -1)
    rec['illuminated_points'] = int(lit.sum())
    rec['detJ_absmax'] = float(np.max(np.abs(det))) if det.size else 0.0

    if not lit.any() or rec['detJ_absmax'] == 0.0:
        rec['catastrophe'] = dict(type='undetermined', confidence='low',
                                  note='no illuminated sample points or identically vanishing Jacobian')
        return rec

    dl = det[lit]
    scale_det = float(np.max(np.abs(dl)))
    idx = np.where(lit)[0]
    ratio = float(np.min(np.abs(dl)) / scale_det)
    sign_change = bool(dl.min() < 0 < dl.max())
    rec['detJ_min_over_max_on_lit'] = ratio
    rec['detJ_sign_change_on_lit'] = sign_change

    if ratio > 0.05 and not sign_change:
        rec['catastrophe'] = dict(
            type='none (regular ray map)', confidence='high',
            note=('Jacobian determinant is bounded away from zero on every illuminated '
                  'sample point: the ray map has no singular locus. The V2=1.0000 is a '
                  'dimension identity of the basis (D=2), not a caustic of the map.'))
        return rec

    p = idx[int(np.argmin(np.abs(dl)))]
    u0, v0 = float(u[p]), float(v[p])
    J = np.array([[du[p, 0], dv[p, 0]], [du[p, 1], dv[p, 1]]])
    ju, js, jvt = np.linalg.svd(J)
    corank = int((js < 1e-8 * js[0]).sum()) if js[0] > 0 else 2
    if corank == 0 and js[1] < 1e-3 * js[0]:
        corank = 1
    kdir = jvt[-1]
    kperp = np.array([-kdir[1], kdir[0]])
    nvec = ju[:, -1]

    win = 0.02 * max(rmax, 1.0)
    gs = np.linspace(-win, win, 25)
    SS, TT = np.meshgrid(gs, gs, indexing='ij')
    gu = u0 + SS * kdir[0] + TT * kperp[0]
    gv = v0 + SS * kdir[1] + TT * kperp[1]
    G = phi_fn(gu.ravel(), gv.ravel())
    g = G @ nvec
    A = poly_design(SS.ravel() / win, TT.ravel() / win)
    coef, r2 = lsq_fit(A, g)
    cmap = {str(a) + str(b): float(coef[i]) for i, (a, b) in enumerate(POLY)}
    gm = float(np.max(np.abs(g))) or 1.0
    cnorm = {k: val / gm for k, val in cmap.items()}

    c20, c30, c40 = abs(cnorm['20']), abs(cnorm['30']), abs(cnorm['40'])
    disc = cubic_discriminant(cnorm['30'], cnorm['21'], cnorm['12'], cnorm['03'])
    tref = max(abs(zc['component_1']['coefficients']['trefoil_x']),
               abs(zc['component_1']['coefficients']['trefoil_y']),
               abs(zc['component_2']['coefficients']['trefoil_x']),
               abs(zc['component_2']['coefficients']['trefoil_y']))

    top = max(c20, c30, c40, 1e-30)
    if corank >= 2:
        ctype = 'hyperbolic umbilic (D4+)' if disc > 0 else 'elliptic umbilic (D4-)'
        conf = 'medium'
    elif c20 / top > 0.3:
        ctype = 'fold (A2)'
        conf = 'high' if (c20 > 3 * c30 and r2 > 0.99) else 'medium'
    elif c30 / top > 0.3:
        ctype = 'cusp (A3)'
        conf = 'medium'
    else:
        ctype = 'higher-order / undetermined'
        conf = 'low'

    rec['catastrophe'] = dict(
        type=ctype, confidence=conf, corank=corank,
        base_point_uv=[u0, v0], base_point_radius=float(math.hypot(u0, v0)),
        window=win,
        jacobian_singular_values=[float(x) for x in js],
        local_poly_R2=float(r2),
        normalized_local_coefficients=cnorm,
        key_terms=dict(s2=cnorm['20'], s3=cnorm['30'], s4=cnorm['40'],
                       t2=cnorm['02'], st=cnorm['11']),
        binary_cubic_discriminant=float(disc),
        azimuthal_trefoil_weight=float(tref),
        note=('degree-4 local normal form of the singular component of the ray map, '
              'in coordinates aligned with the Jacobian kernel; Whitney criterion: '
              'quadratic-in-kernel term dominant -> fold, vanishing quadratic with '
              'cubic dominant -> cusp; corank 2 -> umbilic by cubic discriminant sign.'))

    rec['gap_E'] = gap_e(C, M, dim_key, X, sc_full, rng)
    return rec


def classify():
    root = unpack()
    src, ladder = read_recorded_ladder(root)
    C, L, corpora = load_pipeline(root)
    rng = np.random.default_rng(SEED)

    deg = [r for r in ladder if abs(r['V2'] - 1.0) <= TOL_EXACT]
    log('recorded ladder source: ' + str(src) + '  rows=' + str(len(ladder)) +
        '  exact-1.0000 rows=' + str(len(deg)))

    results = []
    for r in deg:
        name, dk = r['corpus'], r['dim_key']
        if name not in corpora:
            results.append(dict(corpus=name, dim_key=dk, error='corpus not reconstructible'))
            continue
        X, seed = corpora[name]
        log('--- ' + name + ' :: ' + dk)
        rec = analyse(C, L, name, seed, X, dk, r['V2'], rng)
        log('    rank=' + str(rec['numerical_rank']) + ' V2rec=' + str(rec['recomputed_V2'])
            + ' match=' + str(rec['V2_match']) + ' type=' + str(rec.get('catastrophe', {}).get('type'))
            + ' gapE=' + str(rec.get('gap_E', {}).get('verdict')))
        results.append(rec)

    out = dict(
        schema='f4-caustic-classification-v1',
        created='2026-08-24',
        seed=SEED,
        provenance=dict(
            route='recorded',
            ladder_source='papers/is-this-x-2026-08-12-Final.zip::' + str(src),
            ladder_rows=len(ladder),
            degenerate_rows=len(deg),
            designs='reconstructed by importing the bundle scripts/common.py and '
                    'scripts/ladder_correlations.py and re-running their own basis builders '
                    'on the bundle corpora; recomputed V2 checked against recorded V2',
            synthetic=False),
        disclaimer=('Classification fits are MEASUREMENTS, not theorems. The catastrophe '
                    'labels are read off least-squares local normal forms of a finite '
                    'sampled ray map and are contingent on the fit window, the Noll j<=11 '
                    'truncation and the numerical-rank tolerance. Nothing here is elevated '
                    'to an identity-type claim.'),
        method=dict(
            ray_map='disk (u,v) -> stereographic lift -> basis evaluation -> projection on '
                    'the top-2 right singular subspace of the sampled design',
            zernike='Noll j<=11 least squares on the sampled disk points, coefficients '
                    'normalized to unit 2-norm per component',
            normal_form='degree<=4 bivariate polynomial fit of the singular component in '
                        'Jacobian-kernel-aligned local coordinates on a 25x25 grid',
            gap_E='one-column perturbations: in-family add, in-family replace, generic add, '
                  'generic replace, plus an eps sweep of one additively perturbed column'),
        results=results)
    txt = json.dumps(out, separators=(',', ':'), sort_keys=False)
    log('RESULT_BYTES ' + str(len(txt)))
    n = 40000
    if len(txt) <= n:
        print('RESULT_JSON ' + txt, flush=True)
    else:
        parts = [txt[i:i + n] for i in range(0, len(txt), n)]
        for i, pt in enumerate(parts):
            print('RESULT_CHUNK ' + str(i) + '/' + str(len(parts)) + ' ' + pt, flush=True)


def recon():
    out = dict(stage='recon', bundle=BUNDLE, bundle_exists=os.path.exists(BUNDLE))
    if not out['bundle_exists']:
        print('RESULT_JSON ' + json.dumps(out))
        return
    zf = zipfile.ZipFile(BUNDLE)
    for n in zf.namelist():
        print('ENTRY ' + n)
    print('RESULT_JSON ' + json.dumps(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', default='classify')
    a = ap.parse_args()
    if a.mode == 'recon':
        recon()
    else:
        classify()


if __name__ == '__main__':
    main()
