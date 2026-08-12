#!/usr/bin/env python3
"""create_corpus.py -- the standard-candle factory for the RSI curve regime.

Generates binary corpora with PRESCRIBED curved structure (planted real
spherical-harmonic signal on a Fibonacci golden-angle S^2 lattice), matched
null corpora (curveball / column-permutation / iid), a calibration pack
(signal-recovery curve, false-positive rate, detection threshold), and an
IS-THIS-X placement of any supplied N x d binary matrix against the
generated reference families.

Dependencies: Python stdlib + numpy. Nothing else.

Frozen math conventions (see SKILL.md 'Math conventions'):
  Fibonacci sampling   z_i = 1 - (2i+1)/N,  phi_i = 2*pi*i/PHI,  PHI=(1+sqrt5)/2
  Real SH basis        L = 3 -> 16 functions
  Ridge                C* = (Phi^T Phi + lam I)^-1 Phi^T Z, lam = 1e-3
  Residuals            chordal on S^2
  Gate                 PC1+PC2 >= 0.40  (REPORTED, NEVER TRUSTED ALONE)
  Primary statistic    dV2z = (V2 - E0[V2_curveball]) / SD0[V2_curveball]
  Y_3^3 constant       K = sqrt(70/(64 pi)) ~= 0.590044  (CORRECTED)
                       legacy K = sqrt(245/(64 pi)) ~= 1.103929 is WRONG
                       (ratio sqrt(7/2) ~= 1.8708); --legacy-k for compat only.

CLI:
  create_corpus.py generate  [...] --out corpus.json
  create_corpus.py measure   --matrix corpus.json [--reps R]
  create_corpus.py calibrate [...] --out calibration.json
  create_corpus.py place     --matrix any.json
  create_corpus.py --selftest
"""

import argparse
import binascii
import json
import math
import os
import sys

import numpy as np

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

PHI_GOLDEN = (1.0 + math.sqrt(5.0)) / 2.0
RIDGE_LAMBDA = 1e-3
SH_L = 3
SH_NFUNCS = 16
GATE_THRESHOLD = 0.40
DETECT_Z = 3.0
NULL_Z = 2.0

K_Y33 = math.sqrt(70.0 / (64.0 * math.pi))        # 0.5900435...  CORRECT
K_Y33_LEGACY = math.sqrt(245.0 / (64.0 * math.pi))  # 1.1039289...  WRONG

SCHEMA_VERSION = "curved-corpus-create/1.0.0"


# ----------------------------------------------------------------------------
# Geometry: Fibonacci golden-angle lattice on S^2  (i = t, no lookup tables)
# ----------------------------------------------------------------------------

def fibonacci_sphere(n):
    """Canonical Vogel lattice. Returns (xyz [n,3], theta [n], phi [n])."""
    i = np.arange(n, dtype=float)
    z = 1.0 - (2.0 * i + 1.0) / float(n)
    z = np.clip(z, -1.0, 1.0)
    phi = (2.0 * math.pi * i) / PHI_GOLDEN
    r = np.sqrt(np.maximum(0.0, 1.0 - z * z))
    xyz = np.stack([r * np.cos(phi), r * np.sin(phi), z], axis=1)
    theta = np.arccos(z)
    return xyz, theta, np.mod(phi, 2.0 * math.pi)


def real_sh_basis(xyz):
    """Real spherical harmonics, L=0..3 -> 16 columns, explicit Legendre form.

    Column order: (0,0) (1,-1)(1,0)(1,1) (2,-2)..(2,2) (3,-3)..(3,3).
    Column 15 is Y_3^3 = K sin^3(theta) cos(3 phi) with K = sqrt(70/(64 pi)).
    """
    x, y, z = xyz[:, 0], xyz[:, 1], xyz[:, 2]
    cols = [
        np.full_like(x, 0.5 * math.sqrt(1.0 / math.pi)),                # 0,0
        math.sqrt(3.0 / (4.0 * math.pi)) * y,                           # 1,-1
        math.sqrt(3.0 / (4.0 * math.pi)) * z,                           # 1,0
        math.sqrt(3.0 / (4.0 * math.pi)) * x,                           # 1,1
        0.5 * math.sqrt(15.0 / math.pi) * x * y,                        # 2,-2
        0.5 * math.sqrt(15.0 / math.pi) * y * z,                        # 2,-1
        0.25 * math.sqrt(5.0 / math.pi) * (3.0 * z * z - 1.0),          # 2,0
        0.5 * math.sqrt(15.0 / math.pi) * x * z,                        # 2,1
        0.25 * math.sqrt(15.0 / math.pi) * (x * x - y * y),             # 2,2
        0.25 * math.sqrt(35.0 / (2.0 * math.pi)) * y * (3 * x * x - y * y),   # 3,-3
        0.5 * math.sqrt(105.0 / math.pi) * x * y * z,                   # 3,-2
        0.25 * math.sqrt(21.0 / (2.0 * math.pi)) * y * (5 * z * z - 1.0),     # 3,-1
        0.25 * math.sqrt(7.0 / math.pi) * (5 * z ** 3 - 3 * z),         # 3,0
        0.25 * math.sqrt(21.0 / (2.0 * math.pi)) * x * (5 * z * z - 1.0),     # 3,1
        0.25 * math.sqrt(105.0 / math.pi) * (x * x - y * y) * z,        # 3,2
        0.25 * math.sqrt(35.0 / (2.0 * math.pi)) * x * (x * x - 3 * y * y),   # 3,3
    ]
    return np.stack(cols, axis=1)


def y33_probe(theta, phi, legacy_k=False):
    """Y_3^3 angular probe, raw (unstandardized) values.

    K = sqrt(70/(64 pi)) by default. legacy_k=True restores the regime's
    historical sqrt(245/(64 pi)), which is larger by exactly sqrt(7/2) and
    MUST NOT be used for new work.
    """
    k = K_Y33_LEGACY if legacy_k else K_Y33
    return k * np.sin(theta) ** 3 * np.cos(3.0 * phi)


def stereographic_lift(uv):
    """Lift 2-D PCA scores to S^2 by stereographic projection from the south
    pole. Identity-init Mobius (a=d=1, b=c=0), FROZEN -- no refinement."""
    u, v = uv[:, 0], uv[:, 1]
    den = 1.0 + u * u + v * v
    return np.stack([2.0 * u / den, 2.0 * v / den, (-1.0 + u * u + v * v) / den],
                    axis=1)


# ----------------------------------------------------------------------------
# Generation
# ----------------------------------------------------------------------------

def _sigmoid(a):
    return 1.0 / (1.0 + np.exp(-a))


def _standardize(v):
    s = v.std()
    return (v - v.mean()) / s if s > 1e-12 else v - v.mean()


def generate(kind="planted", n=400, d=9, amplitude=1.0, modes=2, base_rate=0.5,
             seed=0, legacy_k=False, n_classes=2, class_sep=1.5,
             mixture_weight=0.5):
    """Build an N x d binary corpus with prescribed structure.

    kind:
      'planted'  planted S^2 spherical-harmonic curve. Logit of column j is
                 mu_j + amplitude * sum_k g_k(x_i) * w_kj, where g_k are the
                 first `modes` STANDARDIZED real-SH probe channels evaluated on
                 the Fibonacci lattice (channel 0 is always Y_3^3), and w_kj are
                 fixed deterministic column loadings. Standardizing g_k is what
                 makes V2 invariant to the Y_3^3 constant (see --legacy-k).
      'mixture'  latent-class mixture (the boring alternative, M4).
      'null'     iid Bernoulli with the same column marginals as the matched
                 planted corpus at amplitude 0.
    """
    rng = np.random.default_rng(seed)
    xyz, theta, phi = fibonacci_sphere(n)
    sh = real_sh_basis(xyz)

    # Probe channels. Channel 0 is Y_3^3 (column 15); then 3,-3; 2,2; 2,-2; 3,0.
    channel_cols = [15, 9, 8, 4, 12]
    modes = max(1, min(int(modes), len(channel_cols)))
    raw = np.stack([sh[:, c] for c in channel_cols[:modes]], axis=1)
    if legacy_k:
        raw = raw * (K_Y33_LEGACY / K_Y33)
    g = np.stack([_standardize(raw[:, k]) for k in range(modes)], axis=1)

    mu = math.log(base_rate / (1.0 - base_rate))

    if kind == "planted":
        # Deterministic column loadings: contiguous blocks of columns share a
        # channel with alternating sign, so distinct columns co-vary through
        # the planted curve and not merely through row mass.
        w = np.zeros((modes, d))
        for j in range(d):
            k = j % modes
            w[k, j] = 1.0 if (j // modes) % 2 == 0 else -1.0
        eta = mu + amplitude * (g @ w)
        p = _sigmoid(eta)
        x = (rng.random((n, d)) < p).astype(np.int8)
        meta = {"loadings": w.tolist()}
    elif kind == "mixture":
        k = max(2, int(n_classes))
        weights = np.full(k, 1.0 / k)
        if k == 2:
            weights = np.array([mixture_weight, 1.0 - mixture_weight])
        z = rng.choice(k, size=n, p=weights)
        centers = rng.normal(0.0, class_sep, size=(k, d)) + mu
        p = _sigmoid(centers[z])
        x = (rng.random((n, d)) < p).astype(np.int8)
        meta = {"class_assign": z.tolist()}
    elif kind == "null":
        base = generate("planted", n=n, d=d, amplitude=0.0, modes=modes,
                        base_rate=base_rate, seed=seed + 1, legacy_k=legacy_k)
        col = base["matrix"].mean(axis=0)
        x = (rng.random((n, d)) < col[None, :]).astype(np.int8)
        meta = {"col_marginals": col.tolist()}
    else:
        raise ValueError("unknown kind: %s" % kind)

    return {
        "schema": SCHEMA_VERSION,
        "matrix": x,
        "params": {"kind": kind, "N": n, "d": d, "amplitude": amplitude,
                   "modes": modes, "base_rate": base_rate, "seed": seed,
                   "legacy_k": bool(legacy_k), "n_classes": n_classes,
                   "class_sep": class_sep, "mixture_weight": mixture_weight,
                   "K_Y33": K_Y33_LEGACY if legacy_k else K_Y33},
        "meta": meta,
        "probe_raw_rms": float(np.sqrt(np.mean(raw[:, 0] ** 2))),
        "y33_raw_rms": float(np.sqrt(np.mean(y33_probe(theta, phi, legacy_k) ** 2))),
    }


# ----------------------------------------------------------------------------
# Null models
# ----------------------------------------------------------------------------

def null_iid(x, rng):
    """iid Bernoulli, column marginals matched. Row sums NOT preserved."""
    p = x.mean(axis=0)
    return (rng.random(x.shape) < p[None, :]).astype(np.int8)


def null_colperm(x, rng):
    """Independent permutation within each column. Column sums exactly kept."""
    y = np.empty_like(x)
    for j in range(x.shape[1]):
        y[:, j] = rng.permutation(x[:, j])
    return y


def null_curveball(x, rng, n_trades=None):
    """Curveball: uniform over binary matrices with the SAME row AND column
    sums (Strona et al. 2014). This is the regime's maximum-entropy null M0."""
    n, d = x.shape
    rows = [set(np.nonzero(x[i])[0].tolist()) for i in range(n)]
    if n_trades is None:
        n_trades = 5 * n
    for _ in range(int(n_trades)):
        a, b = rng.integers(0, n, size=2)
        if a == b:
            continue
        ra, rb = rows[a], rows[b]
        only_a = list(ra - rb)
        only_b = list(rb - ra)
        m = min(len(only_a), len(only_b))
        if m == 0:
            continue
        pool = only_a + only_b
        rng.shuffle(pool)
        new_a = set(pool[:len(only_a)])
        new_b = set(pool[len(only_a):])
        rows[a] = (ra & rb) | new_a
        rows[b] = (ra & rb) | new_b
    y = np.zeros_like(x)
    for i, s in enumerate(rows):
        if s:
            y[i, list(s)] = 1
    return y


NULLS = {"curveball": null_curveball, "colperm": null_colperm, "iid": null_iid}


# ----------------------------------------------------------------------------
# Measurement
# ----------------------------------------------------------------------------

def _corr_eigs(x):
    xf = x.astype(float)
    sd = xf.std(axis=0)
    keep = sd > 1e-12
    if keep.sum() < 2:
        return np.array([1.0]), int(keep.sum())
    xc = (xf[:, keep] - xf[:, keep].mean(axis=0)) / sd[keep]
    c = (xc.T @ xc) / max(1, xf.shape[0] - 1)
    ev = np.linalg.eigvalsh(c)
    return np.sort(np.maximum(ev, 0.0))[::-1], int(keep.sum())


def v2_of(x):
    ev, _ = _corr_eigs(x)
    tot = ev.sum()
    if tot <= 0:
        return 0.0
    return float(ev[:2].sum() / tot)


def participation_ratio(ev):
    s1 = ev.sum()
    s2 = (ev ** 2).sum()
    return float(s1 * s1 / s2) if s2 > 0 else 0.0


def shannon_effective_rank(ev):
    p = ev / ev.sum() if ev.sum() > 0 else ev
    p = p[p > 1e-15]
    return float(math.exp(-(p * np.log(p)).sum())) if p.size else 0.0


def otsu_bimodality(row_sums, d):
    """Otsu inter-class variance of the row-mass histogram, normalized by the
    total variance. 1.0 = perfectly two-point (all-off / all-on); ~0 =
    unimodal. This is the S2 'coverage bimodality' coordinate."""
    v = np.asarray(row_sums, dtype=float)
    tot = v.var()
    if tot <= 1e-15:
        return 0.0
    best = 0.0
    for thr in range(0, int(d)):
        lo = v[v <= thr]
        hi = v[v > thr]
        if lo.size == 0 or hi.size == 0:
            continue
        w0, w1 = lo.size / v.size, hi.size / v.size
        sb = w0 * w1 * (lo.mean() - hi.mean()) ** 2
        best = max(best, sb)
    return float(best / tot)


def sphere_fit(x):
    """PCA top-2 -> stereographic lift -> S^2; fit gamma(t) on the real SH
    basis (L=3, 16 fns) evaluated at the Fibonacci lattice with i = t (t is the
    PC1 rank); closed-form ridge; chordal residuals."""
    xf = x.astype(float)
    xc = xf - xf.mean(axis=0)
    n, d = xc.shape
    u, s, vt = np.linalg.svd(xc, full_matrices=False)
    scores = u[:, :2] * s[:2]
    tot = float((s ** 2).sum())
    pc12 = float((s[:2] ** 2).sum() / tot) if tot > 0 else 0.0
    # scale scores into a sane stereographic window
    rad = np.abs(scores).max()
    if rad > 1e-12:
        scores = scores / rad
    z = stereographic_lift(scores)

    t_raw = scores[:, 0]
    rank = np.argsort(np.argsort(t_raw))   # i = t : Fibonacci index IS the param
    xyz, theta, phi = fibonacci_sphere(n)
    basis = real_sh_basis(xyz)[rank]

    a = basis.T @ basis + RIDGE_LAMBDA * np.eye(SH_NFUNCS)
    c = np.linalg.solve(a, basis.T @ z)
    zhat = basis @ c
    nrm = np.linalg.norm(zhat, axis=1, keepdims=True)
    zhat = zhat / np.maximum(nrm, 1e-12)          # back onto S^2
    resid = np.linalg.norm(z - zhat, axis=1)       # chordal residual
    ss_res = float((resid ** 2).sum())
    zbar = z.mean(axis=0)
    ss_tot = float(((z - zbar) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    # numerical rank / conditioning of the design matrix -- the honest
    # replacement for the PC1+PC2 gate (see SKILL.md 'Gate failure mode').
    sv = np.linalg.svd(basis, compute_uv=False)
    cond = float(sv[0] / sv[-1]) if sv[-1] > 1e-300 else float("inf")
    num_rank = int((sv > sv[0] * 1e-10).sum())

    y33 = y33_probe(theta, phi)[rank]
    probe = float(np.abs(np.dot(_standardize(t_raw), _standardize(y33))) / n)

    return {"pc12": pc12, "gate_pass": bool(pc12 >= GATE_THRESHOLD),
            "sphere_r2": float(r2),
            "chordal_resid_mean": float(resid.mean()),
            "chordal_resid_p95": float(np.percentile(resid, 95)),
            "design_cond": cond, "design_numrank": num_rank,
            "y33_probe": probe}


def measure(x, reps=100, seed=0, nulls=("curveball", "colperm", "iid")):
    """Full measurement: V2, r_eff, sphere fit R^2, chordal residuals, plus the
    null-standardized dV2 for every requested null. dV2z(curveball) is THE
    detection statistic."""
    x = np.asarray(x, dtype=np.int8)
    rng = np.random.default_rng(seed)
    ev, d_eff = _corr_eigs(x)
    v2 = float(ev[:2].sum() / ev.sum()) if ev.sum() > 0 else 0.0
    rows = x.sum(axis=1)
    out = {
        "N": int(x.shape[0]), "d": int(x.shape[1]),
        "V2": v2,
        "eigenvalues": [float(e) for e in ev[:12]],
        "r_eff": participation_ratio(ev),
        "shannon_rank": shannon_effective_rank(ev),
        "mean_offdiag_corr": _mean_offdiag(x),
        "row_mass_mean": float(rows.mean()),
        "row_mass_sd": float(rows.std()),
        "otsu_bimodality": otsu_bimodality(rows, x.shape[1]),
        "col_marginals": [float(v) for v in x.mean(axis=0)],
        "nulls": {},
    }
    out.update(sphere_fit(x))
    for name in nulls:
        fn = NULLS[name]
        vals = np.array([v2_of(fn(x, rng)) for _ in range(int(reps))])
        mu, sd = float(vals.mean()), float(vals.std(ddof=1))
        out["nulls"][name] = {
            "reps": int(reps), "V2_mean": mu, "V2_sd": sd,
            "dV2": v2 - mu,
            "dV2z": float((v2 - mu) / sd) if sd > 1e-12 else 0.0,
        }
    cb = out["nulls"].get("curveball")
    out["dV2z"] = cb["dV2z"] if cb else None
    out["detected"] = bool(cb and abs(cb["dV2z"]) > DETECT_Z)
    return out


def _mean_offdiag(x):
    ev_free = x.astype(float)
    sd = ev_free.std(axis=0)
    keep = sd > 1e-12
    if keep.sum() < 2:
        return 0.0
    c = np.corrcoef(ev_free[:, keep], rowvar=False)
    iu = np.triu_indices(c.shape[0], 1)
    return float(c[iu].mean())


# ----------------------------------------------------------------------------
# Calibration
# ----------------------------------------------------------------------------

def calibrate(n=200, d=9, modes=2, amplitudes=(0.0, 0.25, 0.5, 1.0, 1.5, 2.0),
              trials=8, reps=60, seed=0, base_rate=0.5):
    """Signal-recovery sweep + false-positive rate + detection threshold."""
    curve = []
    for a in amplitudes:
        zs, v2s, r2s = [], [], []
        for t in range(int(trials)):
            c = generate("planted", n=n, d=d, amplitude=float(a), modes=modes,
                         base_rate=base_rate, seed=seed + 1000 * t + 7)
            m = measure(c["matrix"], reps=reps, seed=seed + t,
                        nulls=("curveball",))
            zs.append(m["dV2z"]); v2s.append(m["V2"]); r2s.append(m["sphere_r2"])
        zs = np.array(zs)
        curve.append({
            "amplitude": float(a), "trials": int(trials),
            "dV2z_mean": float(zs.mean()), "dV2z_sd": float(zs.std(ddof=1)),
            "V2_mean": float(np.mean(v2s)), "sphere_r2_mean": float(np.mean(r2s)),
            "power_at_z3": float((np.abs(zs) > DETECT_Z).mean()),
        })

    fp = []
    for t in range(int(trials)):
        c = generate("null", n=n, d=d, base_rate=base_rate,
                     seed=seed + 5000 * t + 13)
        m = measure(c["matrix"], reps=reps, seed=seed + 99 + t,
                    nulls=("curveball",))
        fp.append(m["dV2z"])
    fp = np.array(fp)

    thr = None
    for row in curve:
        if row["power_at_z3"] >= 0.8 and thr is None and row["amplitude"] > 0:
            thr = row["amplitude"]
    return {
        "schema": SCHEMA_VERSION,
        "design": {"N": n, "d": d, "modes": modes, "trials": trials,
                   "null_reps": reps, "base_rate": base_rate, "seed": seed},
        "recovery_curve": curve,
        "false_positive": {
            "trials": int(trials),
            "dV2z_mean": float(fp.mean()), "dV2z_sd": float(fp.std(ddof=1)),
            "dV2z_absmax": float(np.abs(fp).max()),
            "fpr_at_z3": float((np.abs(fp) > DETECT_Z).mean()),
            "fpr_at_z2": float((np.abs(fp) > NULL_Z).mean()),
        },
        "detection_threshold_amplitude": thr,
        "notes": "dV2z = (V2 - E0[V2_curveball]) / SD0[V2_curveball].",
    }


# ----------------------------------------------------------------------------
# IS-THIS-X placement
# ----------------------------------------------------------------------------

S_KEYS = ["V2", "dV2z", "r_eff", "otsu_bimodality", "col_marginal_mean",
          "col_marginal_sd"]

# Relative floor on a reference family's per-coordinate SD. With few trials the
# empirical SD is itself noisy and a too-narrow family excludes everything,
# including its own members. The floor makes exclusion conservative.
SD_FLOOR_REL = 0.05


def s_vector(m):
    cols = np.array(m["col_marginals"])
    return {
        "V2": m["V2"], "dV2z": m["dV2z"], "r_eff": m["r_eff"],
        "otsu_bimodality": m["otsu_bimodality"],
        "col_marginal_mean": float(cols.mean()),
        "col_marginal_sd": float(cols.std()),
    }


def _stable_tag(name):
    """Process-stable small integer from a family name. Python's builtin hash()
    is salted per process (PYTHONHASHSEED) and would make `place` irreproducible."""
    return int(binascii.crc32(name.encode("utf-8")) % 977)


def reference_families(n, d, base_rate, trials=6, reps=40, seed=0, modes=2):
    """Generate the reference families at matched (N, d, base rate)."""
    fams = {
        "M0_null":        dict(kind="null", amplitude=0.0),
        "M1_curve_weak":  dict(kind="planted", amplitude=0.5, modes=modes),
        "M1_curve_strong": dict(kind="planted", amplitude=1.5, modes=modes),
        "M4_mixture":     dict(kind="mixture", n_classes=2, class_sep=1.5),
    }
    out = {}
    for name, kw in fams.items():
        rows = []
        for t in range(int(trials)):
            c = generate(n=n, d=d, base_rate=base_rate,
                         seed=seed + 3000 * t + _stable_tag(name), **kw)
            m = measure(c["matrix"], reps=reps, seed=seed + t,
                        nulls=("curveball",))
            rows.append(s_vector(m))
        arr = {k: np.array([r[k] for r in rows]) for k in S_KEYS}
        out[name] = {
            "trials": int(trials),
            "mean": {k: float(arr[k].mean()) for k in S_KEYS},
            "sd": {k: float(arr[k].std(ddof=1)) for k in S_KEYS},
        }
    return out


def place(x, trials=6, reps=40, seed=0, modes=2):
    """Put an arbitrary N x d binary matrix in the IS-THIS-X question space.

    Verdicts are exclusion-style ONLY: excluded / not-excluded / not-tested.
    'PARTIAL' and 'compatible with' are not allowed outputs (D-memo Q3.1-3.3).
    """
    x = np.asarray(x, dtype=np.int8)
    n, d = x.shape
    m = measure(x, reps=max(reps, 60), seed=seed)
    s = s_vector(m)
    base_rate = float(np.clip(x.mean(), 0.05, 0.95))
    fams = reference_families(n, d, base_rate, trials=trials, reps=reps,
                              seed=seed + 1, modes=modes)

    rows = []
    for name, f in fams.items():
        zs, worst_key, worst = {}, None, 0.0
        tested = True
        for k in S_KEYS:
            sd = max(f["sd"][k], SD_FLOOR_REL * abs(f["mean"][k]))
            if sd < 1e-9:
                zs[k] = None
                tested = False
                continue
            zk = (s[k] - f["mean"][k]) / sd
            zs[k] = float(zk)
            if abs(zk) > abs(worst):
                worst, worst_key = zk, k
        if not tested and worst_key is None:
            verdict = "not-tested"
        elif abs(worst) > DETECT_Z:
            verdict = "excluded"
        else:
            verdict = "not-excluded"
        rows.append({"class": name, "verdict": verdict,
                     "max_abs_z": float(abs(worst)),
                     "driving_coordinate": worst_key, "z": zs,
                     "degenerate_coords": [k for k in S_KEYS if zs.get(k) is None]})

    not_ex = [r for r in rows if r["verdict"] == "not-excluded"]
    nearest = min(rows, key=lambda r: r["max_abs_z"])
    return {
        "schema": SCHEMA_VERSION,
        "input": {"N": int(n), "d": int(d), "density": float(x.mean())},
        "s_vector": s,
        "measurement": {k: m[k] for k in
                        ("V2", "dV2z", "r_eff", "shannon_rank", "sphere_r2",
                         "chordal_resid_mean", "pc12", "gate_pass",
                         "design_cond", "design_numrank", "y33_probe",
                         "mean_offdiag_corr", "otsu_bimodality")},
        "reference_families": fams,
        "exclusion_table": rows,
        "nearest_family": nearest["class"],
        "surviving_classes": [r["class"] for r in not_ex],
        "verdict_summary": ("all reference classes excluded -- corpus is off the "
                            "generated map; widen the family grid"
                            if not not_ex else
                            "nearest: %s (max|z| = %.2f)" %
                            (nearest["class"], nearest["max_abs_z"])),
    }


# ----------------------------------------------------------------------------
# I/O
# ----------------------------------------------------------------------------

def save_corpus(c, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    payload = {"schema": c["schema"], "params": c["params"],
               "probe_raw_rms": c.get("probe_raw_rms"),
               "y33_raw_rms": c.get("y33_raw_rms"),
               "matrix": c["matrix"].astype(int).tolist()}
    with open(path, "w") as fh:
        json.dump(payload, fh)
    return path


def load_matrix(path):
    with open(path) as fh:
        obj = json.load(fh)
    mat = obj["matrix"] if isinstance(obj, dict) else obj
    return np.asarray(mat, dtype=np.int8)


def emit(obj, path=None):
    txt = json.dumps(obj, indent=2, sort_keys=False)
    if path:
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        with open(path, "w") as fh:
            fh.write(txt + "\n")
        print("wrote %s" % path)
    else:
        print(txt)


# ----------------------------------------------------------------------------
# Selftest
# ----------------------------------------------------------------------------

def selftest():
    ok = True

    def chk(label, cond, detail=""):
        nonlocal ok
        ok = ok and bool(cond)
        print("  [%s] %s %s" % ("PASS" if cond else "FAIL", label, detail))

    print("curved-corpus-create selftest (%s)" % SCHEMA_VERSION)
    print("constants: K_Y33=%.6f  K_legacy=%.6f  ratio=%.6f (sqrt(7/2)=%.6f)"
          % (K_Y33, K_Y33_LEGACY, K_Y33_LEGACY / K_Y33, math.sqrt(3.5)))

    print("\n[1] geometry")
    xyz, th, ph = fibonacci_sphere(64)
    chk("Fibonacci points on unit sphere",
        np.allclose(np.linalg.norm(xyz, axis=1), 1.0, atol=1e-12))
    b = real_sh_basis(xyz)
    chk("real SH basis is L=3 -> 16 fns", b.shape == (64, SH_NFUNCS),
        str(b.shape))
    chk("basis col 15 == K sin^3 cos(3phi)",
        np.allclose(b[:, 15], y33_probe(th, ph), atol=1e-12))

    print("\n[2] planted s=2 corpus is DETECTED (z > 3)")
    cp = generate("planted", n=200, d=9, amplitude=1.5, modes=2, seed=11)
    mp = measure(cp["matrix"], reps=80, seed=3, nulls=("curveball",))
    chk("planted dV2z > 3", mp["dV2z"] > DETECT_Z, "z = %.3f" % mp["dV2z"])
    print("       V2=%.4f r_eff=%.3f sphereR2=%.4f resid=%.4f PC1+PC2=%.4f"
          % (mp["V2"], mp["r_eff"], mp["sphere_r2"],
             mp["chordal_resid_mean"], mp["pc12"]))

    print("\n[3] null corpus is NOT detected (|z| < 2)")
    cn = generate("null", n=200, d=9, seed=12)
    mn = measure(cn["matrix"], reps=80, seed=4, nulls=("curveball",))
    chk("null |dV2z| < 2", abs(mn["dV2z"]) < NULL_Z, "z = %.3f" % mn["dV2z"])
    print("       V2=%.4f r_eff=%.3f otsu=%.4f"
          % (mn["V2"], mn["r_eff"], mn["otsu_bimodality"]))

    print("\n[4] legacy-K flag changes SCALE ONLY, not V2")
    ca = generate("planted", n=200, d=9, amplitude=1.5, modes=2, seed=11,
                  legacy_k=False)
    cb = generate("planted", n=200, d=9, amplitude=1.5, modes=2, seed=11,
                  legacy_k=True)
    v2a, v2b = v2_of(ca["matrix"]), v2_of(cb["matrix"])
    chk("matrices identical under legacy-K",
        np.array_equal(ca["matrix"], cb["matrix"]))
    chk("V2 unchanged", abs(v2a - v2b) < 1e-12,
        "V2=%.6f vs %.6f" % (v2a, v2b))
    ratio = cb["y33_raw_rms"] / ca["y33_raw_rms"]
    chk("raw probe scale ratio == sqrt(7/2)", abs(ratio - math.sqrt(3.5)) < 1e-9,
        "ratio = %.6f" % ratio)

    print("\n[5] gate failure mode is reported, not trusted")
    chk("gate + rank both reported",
        all(k in mp for k in ("pc12", "gate_pass", "design_numrank",
                              "design_cond")),
        "PC1+PC2=%.4f rank=%d cond=%.3g"
        % (mp["pc12"], mp["design_numrank"], mp["design_cond"]))

    print("\n[6] calibration pack (miniature)")
    cal = calibrate(n=120, d=9, modes=2, amplitudes=(0.0, 0.75, 1.5),
                    trials=3, reps=40, seed=5)
    for r in cal["recovery_curve"]:
        print("       a=%.2f  dV2z=%+.2f +/- %.2f  V2=%.4f  R2=%.4f  power=%.2f"
              % (r["amplitude"], r["dV2z_mean"], r["dV2z_sd"], r["V2_mean"],
                 r["sphere_r2_mean"], r["power_at_z3"]))
    print("       FPR@|z|>3 = %.2f   FPR@|z|>2 = %.2f   thr_amp = %s"
          % (cal["false_positive"]["fpr_at_z3"],
             cal["false_positive"]["fpr_at_z2"],
             cal["detection_threshold_amplitude"]))
    chk("recovery is monotone in amplitude",
        cal["recovery_curve"][-1]["dV2z_mean"] >
        cal["recovery_curve"][0]["dV2z_mean"])
    chk("FPR at |z|>3 is 0", cal["false_positive"]["fpr_at_z3"] == 0.0)

    print("\n[7] IS-THIS-X placement round-trip")
    pl = place(cp["matrix"], trials=3, reps=40, seed=6)
    for r in pl["exclusion_table"]:
        print("       %-16s %-13s max|z|=%6.2f  (%s)"
              % (r["class"], r["verdict"], r["max_abs_z"],
                 r["driving_coordinate"]))
    chk("planted corpus excludes M0_null",
        any(r["class"] == "M0_null" and r["verdict"] == "excluded"
            for r in pl["exclusion_table"]))
    pl0 = place(cn["matrix"], trials=3, reps=40, seed=7)
    for r in pl0["exclusion_table"]:
        print("       %-16s %-13s max|z|=%6.2f  (%s)"
              % (r["class"], r["verdict"], r["max_abs_z"],
                 r["driving_coordinate"]))
    chk("null corpus does NOT exclude M0_null",
        any(r["class"] == "M0_null" and r["verdict"] == "not-excluded"
            for r in pl0["exclusion_table"]))

    print("\nSELFTEST %s" % ("GREEN" if ok else "RED"))
    return 0 if ok else 1


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(
        prog="create_corpus.py",
        description="Generate / measure / calibrate / place curved corpora.")
    p.add_argument("--selftest", action="store_true",
                   help="run the miniature end-to-end check and exit")
    sub = p.add_subparsers(dest="cmd")

    g = sub.add_parser("generate", help="emit a corpus with prescribed structure")
    g.add_argument("--kind", choices=["planted", "mixture", "null"],
                   default="planted")
    g.add_argument("-N", "--n", type=int, default=400)
    g.add_argument("-d", "--d", type=int, default=9)
    g.add_argument("--amplitude", type=float, default=1.0)
    g.add_argument("--modes", type=int, default=2,
                   help="number of planted SH channels (channel 0 = Y_3^3)")
    g.add_argument("--base-rate", type=float, default=0.5)
    g.add_argument("--n-classes", type=int, default=2)
    g.add_argument("--class-sep", type=float, default=1.5)
    g.add_argument("--mixture-weight", type=float, default=0.5)
    g.add_argument("--seed", type=int, default=0)
    g.add_argument("--legacy-k", action="store_true",
                   help="DEPRECATED compat: use K=sqrt(245/(64pi)). Do not use.")
    g.add_argument("--out", default=None)

    m = sub.add_parser("measure", help="V2, r_eff, sphere fit, null-standardized dV2")
    m.add_argument("--matrix", required=True)
    m.add_argument("--reps", type=int, default=100)
    m.add_argument("--seed", type=int, default=0)
    m.add_argument("--nulls", default="curveball,colperm,iid")
    m.add_argument("--out", default=None)

    c = sub.add_parser("calibrate", help="signal-recovery sweep + FPR")
    c.add_argument("-N", "--n", type=int, default=200)
    c.add_argument("-d", "--d", type=int, default=9)
    c.add_argument("--modes", type=int, default=2)
    c.add_argument("--amplitudes", default="0,0.25,0.5,1.0,1.5,2.0")
    c.add_argument("--trials", type=int, default=8)
    c.add_argument("--reps", type=int, default=60)
    c.add_argument("--base-rate", type=float, default=0.5)
    c.add_argument("--seed", type=int, default=0)
    c.add_argument("--out", default=None)

    q = sub.add_parser("place", help="IS-THIS-X placement of any binary matrix")
    q.add_argument("--matrix", required=True)
    q.add_argument("--trials", type=int, default=6)
    q.add_argument("--reps", type=int, default=40)
    q.add_argument("--modes", type=int, default=2)
    q.add_argument("--seed", type=int, default=0)
    q.add_argument("--out", default=None)
    return p


def main(argv=None):
    p = build_parser()
    a = p.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.cmd == "generate":
        c = generate(kind=a.kind, n=a.n, d=a.d, amplitude=a.amplitude,
                     modes=a.modes, base_rate=a.base_rate, seed=a.seed,
                     legacy_k=a.legacy_k, n_classes=a.n_classes,
                     class_sep=a.class_sep, mixture_weight=a.mixture_weight)
        if a.legacy_k:
            sys.stderr.write("WARNING: --legacy-k uses the WRONG Y_3^3 constant "
                             "sqrt(245/(64pi)); legacy compat only.\n")
        if a.out:
            save_corpus(c, a.out)
        else:
            emit({"schema": c["schema"], "params": c["params"],
                  "matrix": c["matrix"].astype(int).tolist()})
        return 0
    if a.cmd == "measure":
        x = load_matrix(a.matrix)
        emit(measure(x, reps=a.reps, seed=a.seed,
                     nulls=tuple(s.strip() for s in a.nulls.split(",") if s.strip())),
             a.out)
        return 0
    if a.cmd == "calibrate":
        amps = tuple(float(s) for s in a.amplitudes.split(","))
        emit(calibrate(n=a.n, d=a.d, modes=a.modes, amplitudes=amps,
                       trials=a.trials, reps=a.reps, seed=a.seed,
                       base_rate=a.base_rate), a.out)
        return 0
    if a.cmd == "place":
        x = load_matrix(a.matrix)
        emit(place(x, trials=a.trials, reps=a.reps, seed=a.seed,
                   modes=a.modes), a.out)
        return 0
    p.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())


# # ## Examples
# # python3 create_corpus.py --help
# # RSI cycle-6 atomic flip (`examples`).
