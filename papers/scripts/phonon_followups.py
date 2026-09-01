#!/usr/bin/env python3
"""phonon_followups.py -- executes the five follow-ups of
refs/acoustic-optical-phonons-bridge-2026-09-01.md sec.5, in order.

Run from the repo root (CI: .github/workflows/phonon-followups.yml).

Stage 1  Pennes-omega identifiability audit (synthetic, deterministic).
Stage 2  FD-residual admission: corpus-side margin-determination check +
         compass-side linear-Phi residual (designed-chain descriptive).
Stage 3  Compass sweep-step <-> defocus time reconciliation + FCS gate.
Stage 4  Gaunt-coupled defocus on the real 2286x9 corpus vs curveball null,
         with matched selection pressure over the kappa grid, plus the
         transient-growth check.
Stage 5  Two-population (pattern-defined, k<9 rows) clustering statistic vs
         curveball null, with the margin-only-classifier leakage baseline.

Discipline: exclusion-only language in the emitted verdicts; every
corpus-facing statistic faces the curveball null; pi_T / T_x / tau_int
readouts are designed-chain (compass) properties. Scientific outcomes
(positive or negative) never fail the process; only internal sanity
assertions exit nonzero.

Output: one JSON document on stdout between PHONON_FOLLOWUPS_JSON_BEGIN/END
markers, plus human-readable stage lines.
"""

import importlib.util
import json
import math
import sys

import numpy as np

RESULTS = {}


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


defocus = _load("defocus", "tools/spectral-defocus/defocus.py")
collapse = _load("collapse", "tools/boltzmann-collapse/collapse.py")

TAU_INT_MEASURED = 5.486   # compass tau_int at T = 0.05, in sweeps (published)
T_REF = 0.05
D = 9


def curveball(M, n_trades, rng):
    """Fixed-margin curveball sampler (same move set as verify_claims.py /
    Lean sec.8 trades: row and column sums exactly preserved)."""
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


# ============================================================ Stage 1

def stage1_omega_audit():
    """Apply the uniform Pennes rescale E -> e^{-omega t} E to a synthetic
    spectrum and recompute each statistic. A statistic identifies omega iff
    its value changes."""
    rng = np.random.default_rng(11)
    c0 = rng.standard_normal(defocus.N_BASIS)
    E0 = defocus.energies_by_degree(c0)
    t, omega = 0.1, 3.0
    l = np.arange(defocus.MAX_L + 1)
    E_diag = E0 * np.exp(-2.0 * l * (l + 1.0) * t)
    E_omega = E_diag * math.exp(-omega * t)

    def share(E):
        return E / E.sum()

    stats = {}
    stats["parseval_share_per_degree"] = float(np.max(np.abs(share(E_diag) - share(E_omega))))
    stats["low_l_mass_rho(l<=2)"] = float(abs(share(E_diag)[:3].sum() - share(E_omega)[:3].sum()))
    stats["high_degree_mass(l=3)"] = float(abs(share(E_diag)[3] - share(E_omega)[3]))
    stats["gapD_J_L3_share"] = stats["high_degree_mass(l=3)"]  # same functional form
    # atomicity A_l(t) (defocus.py definition) -- NOT a cross-degree ratio
    A_diag = defocus.atomicity(E0, E_diag, t)
    A_omega = defocus.atomicity(E0, E_omega, t)
    stats["atomicity_A_l"] = float(np.max(np.abs(A_diag - A_omega)))
    stats["total_energy_E_tot"] = float(abs(E_diag.sum() - E_omega.sum()) / E_diag.sum())

    tol = 1e-12
    invariant = {k: v < tol for k, v in stats.items()}
    admitted_set = ["parseval_share_per_degree", "low_l_mass_rho(l<=2)",
                    "high_degree_mass(l=3)", "gapD_J_L3_share"]
    admitted_all_invariant = all(invariant[k] for k in admitted_set)
    sensitive = [k for k, inv in invariant.items() if not inv]
    verdict = ("omega VOID (unidentifiable): every admitted spectrum statistic is a "
               "ratio/share and invariant under E -> e^{-omega t}E. The only "
               "omega-sensitive observables are atomicity A_l (admission FAILED "
               "2026-08-22, z=+1.59 < 3) and unnormalized total energy (not admitted). "
               "Resurrecting omega requires first admitting an unnormalized observable "
               "behind its own curveball null." if admitted_all_invariant else
               "omega IDENTIFIABLE via an admitted statistic -- bridge doc ranking must be revised")
    RESULTS["stage1_omega_audit"] = {
        "max_change_under_omega_rescale": stats,
        "invariant": invariant,
        "admitted_set_all_invariant": bool(admitted_all_invariant),
        "omega_sensitive_observables": sensitive,
        "verdict": verdict,
    }
    assert stats["total_energy_E_tot"] > 0.1, "sanity: total energy must see omega"
    print("[stage1] admitted set invariant:", admitted_all_invariant,
          "| omega-sensitive:", sensitive)


# ============================================================ Stage 2

def stage2_fd_residual(M, rng):
    # corpus side: the k-histogram is margin-determined -> curveball deflection == 0
    k_real = M.sum(axis=1).astype(int)
    hist_real = np.bincount(k_real, minlength=D + 1)
    identical = True
    for _ in range(5):
        Mn = curveball(M, 20 * M.shape[0], rng)
        if not np.array_equal(np.bincount(Mn.sum(axis=1).astype(int), minlength=D + 1), hist_real):
            identical = False
    # compass side: measured Phi ladder vs its linear (FD/Binomial) reference
    phi, t_x_pub, note = collapse._load_measured_phi_ladder()
    k = np.arange(D + 1, dtype=float)
    # least-squares linear fit Phi(k) ~ eps*k + c (constant immaterial to pi_T)
    A = np.stack([k, np.ones_like(k)], axis=1)
    (eps, c0), *_ = np.linalg.lstsq(A, phi, rcond=None)
    phi_lin = eps * k + c0
    residual = (phi - phi_lin).tolist()
    tv = {}
    for T in (0.02, 0.0368, 0.038304, 0.041143, 0.05, 0.1):
        p_meas = collapse.pi_T(phi, D, T)
        p_lin = collapse.pi_T(phi_lin, D, T)
        p_fd = np.array([math.comb(D, i) for i in range(D + 1)], dtype=float)
        x = 1.0 / (1.0 + math.exp(eps / T))
        p_fd = p_fd * (x ** k) * ((1 - x) ** (D - k))
        assert np.max(np.abs(p_lin - p_fd)) < 1e-10, "FD/Binomial identity violated"
        tv[str(T)] = float(0.5 * np.abs(p_meas - p_lin).sum())
    RESULTS["stage2_fd_residual"] = {
        "corpus_side": {
            "k_histogram": hist_real.tolist(),
            "curveball_preserves_k_histogram_exactly": bool(identical),
            "verdict": ("FD-residual on the corpus k-histogram: EXCLUDED BY CONSTRUCTION "
                        "-- margin-determined, deflection == 0, dBc -> -inf. Recorded, "
                        "not fitted." if identical else "UNEXPECTED: histogram moved under curveball"),
        },
        "compass_side": {
            "phi_ladder_source": note[:120],
            "eps_linear_fit": float(eps),
            "phi_minus_linear_residual": residual,
            "tv_distance_piT_measured_vs_FD_binomial_by_T": tv,
            "verdict": ("designed-chain descriptive readout: the TV(T) profile measures "
                        "interaction beyond the ideal two-state (FD) gas on the compass. "
                        "No corpus claim; no admission possible (see corpus_side)."),
        },
    }
    assert identical, "curveball must preserve row sums exactly"
    print(f"[stage2] k-hist margin-determined: {identical} | eps={eps:.4f} | "
          f"TV at T=0.05: {tv['0.05']:.4f}")
    return phi


# ============================================================ Stage 3

def stage3_units(phi, share_real):
    """Collapsed single-flip Metropolis kernel on shells k=0..9; spectral gap
    -> relaxation time in sweeps; tie to defocus time by the ell*-matching
    convention; evaluate the FCS identifiability gate."""
    T = T_REF
    P = np.zeros((D + 1, D + 1))
    for k in range(D + 1):
        if k < D:
            a = min(1.0, math.exp(-(phi[k + 1] - phi[k]) / T))
            P[k, k + 1] = ((D - k) / D) * a
        if k > 0:
            a = min(1.0, math.exp(-(phi[k - 1] - phi[k]) / T))
            P[k, k - 1] = (k / D) * a
        P[k, k] = 1.0 - P[k].sum()
    pi = collapse.pi_T(phi, D, T)
    db_err = float(np.max(np.abs(pi[:, None] * P - (pi[:, None] * P).T)))
    ev = np.sort(np.abs(np.linalg.eigvals(P)))[::-1]
    gap_step = 1.0 - float(ev[1])
    tau_rel_steps = 1.0 / gap_step
    tau_rel_sweeps = tau_rel_steps / D
    # ell* = admitted-mass-carrying degree of the real corpus fit (l >= 1)
    l_star = int(np.argmax(share_real[1:]) + 1)
    tau_lstar = 1.0 / (2.0 * l_star * (l_star + 1.0))
    # convention: 1 sweep = c defocus-time units, c set by matching relaxations
    c = tau_lstar / tau_rel_sweeps
    tau_T_defocus = TAU_INT_MEASURED * c
    gate_ratio = tau_T_defocus / tau_lstar   # == tau_int / tau_rel_sweeps
    gate_pass = gate_ratio < 0.1
    RESULTS["stage3_units"] = {
        "T": T,
        "detailed_balance_max_flux_err": db_err,
        "kernel_spectral_gap_per_step": gap_step,
        "tau_rel_steps": tau_rel_steps,
        "tau_rel_sweeps": tau_rel_sweeps,
        "tau_int_published_sweeps": TAU_INT_MEASURED,
        "l_star": l_star,
        "tau_l_star_defocus_units": tau_lstar,
        "conversion_c_defocus_per_sweep_CONVENTION": c,
        "fcs_gate_ratio_tauT_over_tauD": gate_ratio,
        "fcs_gate_requires": "<< 1 (we use < 0.1)",
        "fcs_gate_pass": bool(gate_pass),
        "verdict": (("FCS gate PASSES under the ell*-matching convention" if gate_pass else
                     "FCS gate FAILS: the coverage-coordinate relaxation and the defocus "
                     "relaxation are the same order under the ell*-matching convention -- "
                     "the two-channel FCS factorization moves not-tested -> NOT-IDENTIFIABLE "
                     "at T=0.05")
                    + ". The tie is a stated convention (relaxation matching), not a theorem."),
    }
    assert db_err < 1e-12, "collapsed kernel must satisfy detailed balance"
    print(f"[stage3] gap/step={gap_step:.5f} tau_rel={tau_rel_sweeps:.3f} sweeps | "
          f"tau_int={TAU_INT_MEASURED} | gate ratio={gate_ratio:.3f} pass={gate_pass}")


# ============================================================ Stage 4 + 5 shared

def embed_and_fit(M):
    pts, tgt = defocus.matrix_to_sphere(M.astype(float))
    fit = defocus.fit_field(pts, tgt)
    return pts, tgt, fit


def gaunt_tensor(n_quad=8000):
    P = defocus.fibonacci_lattice(n_quad)
    Phi = defocus.design_matrix(P)             # (N,16)
    wq = 4.0 * math.pi / n_quad
    ortho = wq * (Phi.T @ Phi)
    ortho_err = float(np.max(np.abs(ortho - np.eye(defocus.N_BASIS))))
    G = wq * np.einsum("ni,nj,nk->ijk", Phi, Phi, Phi)
    # sparsity check against triangle+parity on degrees
    deg = defocus.DEGREES
    max_forbidden, max_allowed = 0.0, 0.0
    for i in range(16):
        for j in range(16):
            for k in range(16):
                l1, l2, l3 = deg[i], deg[j], deg[k]
                tri = l3 <= l1 + l2 and l1 <= l2 + l3 and l2 <= l1 + l3
                ok = tri and (l1 + l2 + l3) % 2 == 0
                v = abs(G[i, j, k])
                if ok:
                    max_allowed = max(max_allowed, v)
                else:
                    max_forbidden = max(max_forbidden, v)
    return G, ortho_err, max_forbidden, max_allowed


def evolve(c0, G, kappa, t_max=0.4, n_steps=200):
    """dc/dt = -Lambda c + kappa * B(c,c), B_i = sum_jk G_ijk c_j c_k. RK4.
    Returns per-degree energy trajectory (n_steps+1, 4) and times."""
    lam = defocus.DEGREES * (defocus.DEGREES + 1.0)

    def rhs(c):
        return -lam * c + kappa * np.einsum("ijk,j,k->i", G, c, c)

    dt = t_max / n_steps
    c = c0.copy()
    E = [defocus.energies_by_degree(c)]
    for _ in range(n_steps):
        k1 = rhs(c)
        k2 = rhs(c + 0.5 * dt * k1)
        k3 = rhs(c + 0.5 * dt * k2)
        k4 = rhs(c + dt * k3)
        c = c + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
        E.append(defocus.energies_by_degree(c))
    return np.array(E)


def coupling_stats(c0, G, kappa):
    """S = max_t gain in low-l (l<=2) share vs the diagonal flow;
    TG = max_t total-energy ratio vs diagonal (transient growth)."""
    c0 = c0 / math.sqrt(float(np.sum(c0 ** 2)))   # unit total amplitude energy
    Ek = evolve(c0, G, kappa)
    E0d = defocus.energies_by_degree(c0)
    l = np.arange(defocus.MAX_L + 1)
    ts = np.linspace(0.0, 0.4, Ek.shape[0])
    Ed = E0d[None, :] * np.exp(-2.0 * l * (l + 1.0) * ts[:, None])
    tot_k, tot_d = Ek.sum(axis=1), Ed.sum(axis=1)
    low_k = Ek[:, :3].sum(axis=1) / np.where(tot_k > 0, tot_k, 1.0)
    low_d = Ed[:, :3].sum(axis=1) / np.where(tot_d > 0, tot_d, 1.0)
    S = float(np.max(low_k - low_d))
    TG = float(np.max(tot_k / np.where(tot_d > 0, tot_d, 1.0)) - 1.0)
    mono = bool(np.all(np.diff(tot_k) <= 1e-12))
    return S, TG, mono


def stage4_gaunt(M, null_fits, fit_real, G, gq):
    ortho_err, max_forb, max_allow = gq
    kappas = [0.5, 1.0, 2.0]
    per_kappa = {}
    best_S, best_k, best_TG, best_mono = -1e9, None, None, None
    for kp in kappas:
        S, TG, mono = coupling_stats(fit_real.coeffs, G, kp)
        per_kappa[str(kp)] = {"S_low_share_gain": S, "TG_transient_growth": TG,
                              "E_tot_monotone": mono}
        if S > best_S:
            best_S, best_k, best_TG, best_mono = S, kp, TG, mono
    null_S = []
    for f in null_fits:
        s_best = max(coupling_stats(f.coeffs, G, kp)[0] for kp in kappas)  # matched selection
        null_S.append(s_best)
    null_S = np.array(null_S)
    mu, sd = float(null_S.mean()), float(null_S.std(ddof=1))
    z = (best_S - mu) / sd if sd > 0 else float("inf")
    dbc = 20.0 * math.log10(abs(best_S - mu) / sd) if sd > 0 and best_S != mu else None
    admitted = z > 6.0  # +15.6 dBc floor
    RESULTS["stage4_gaunt"] = {
        "gaunt_quadrature": {"n_quad": 8000, "orthonormality_max_err": ortho_err,
                             "max_|G|_forbidden_triads": max_forb,
                             "max_|G|_allowed_triads": max_allow},
        "kappa_grid": kappas,
        "per_kappa_real": per_kappa,
        "selected_kappa": best_k,
        "S_real_selected": best_S,
        "transient_growth_real_at_selected": best_TG,
        "E_tot_monotone_real": best_mono,
        "null_n": len(null_S),
        "null_S_mean": mu, "null_S_sd": sd,
        "z_matched_selection": float(z),
        "dBc": dbc,
        "detectability_floor_dBc": 15.6,
        "verdict": (("kappa deflects at z=%.2f (> 6): Gaunt-coupled low-share gain is "
                     "corpus-specific -- NOT-EXCLUDED, proceed to matched-parameter "
                     "ablation before shipping" % z) if admitted else
                    ("kappa does NOT clear the floor (z=%.2f <= 6): recorded NEGATIVE -- "
                     "the Gaunt-coupled low-share gain is not corpus-specific at L=3 with "
                     "this budget. The structural exclusion of the generic k_ISC matrix "
                     "in favour of Gaunt sparsity stands regardless (it is parsimony-side, "
                     "not data-side)." % z)),
    }
    assert ortho_err < 0.02, "quadrature orthonormality sanity"
    assert max_forb < 1e-6, "Gaunt sparsity: forbidden triads must vanish"
    print(f"[stage4] ortho_err={ortho_err:.2e} forbidden|G|max={max_forb:.2e} | "
          f"S_real={best_S:.4f}@k={best_k} TG={best_TG:.2e} | null {mu:.4f}+-{sd:.4f} z={z:.2f}")


def spherical_2means(pts, rng, iters=25, restarts=5):
    best_inertia, best_lab, best_cent = -1e18, None, None
    for _ in range(restarts):
        idx = rng.choice(len(pts), 2, replace=False)
        C = pts[idx].copy()
        lab = None
        for _ in range(iters):
            sim = pts @ C.T
            lab = np.argmax(sim, axis=1)
            for j in (0, 1):
                sel = pts[lab == j]
                if len(sel) == 0:
                    continue
                v = sel.sum(axis=0)
                n = np.linalg.norm(v)
                if n > 1e-12:
                    C[j] = v / n
        inertia = float(np.max(pts @ C.T, axis=1).sum())
        if inertia > best_inertia:
            best_inertia, best_lab, best_cent = inertia, lab, C
    return best_lab, best_cent


def two_pop_stat(M, rng):
    pts, _, _ = (*embed_and_fit(M),)[0:3] if False else (None, None, None)
    # (explicit for clarity)
    pts, tgt = defocus.matrix_to_sphere(M.astype(float))
    k = M.sum(axis=1).astype(int)
    mask = k < D
    P = pts[mask]
    lab, C = spherical_2means(P, rng)
    r_all = float(np.linalg.norm(P.mean(axis=0)))
    parts = []
    for j in (0, 1):
        sel = P[lab == j]
        parts.append((len(sel) / len(P)) * float(np.linalg.norm(sel.mean(axis=0))))
    Gstat = sum(parts) - r_all
    return Gstat, lab, k[mask]


def stage5_two_pop(M, null_mats, rng):
    G_real, lab, kmask = two_pop_stat(M, rng)
    # margin-only classifier baseline: predict cluster from k alone
    acc = 0
    for kk in np.unique(kmask):
        sub = lab[kmask == kk]
        acc += max((sub == 0).sum(), (sub == 1).sum())
    acc_margin = float(acc / len(lab))
    balance = float((lab == 0).mean())
    null_G = np.array([two_pop_stat(Mn, rng)[0] for Mn in null_mats])
    mu, sd = float(null_G.mean()), float(null_G.std(ddof=1))
    z = (G_real - mu) / sd if sd > 0 else float("inf")
    dbc = 20.0 * math.log10(abs(G_real - mu) / sd) if sd > 0 and G_real != mu else None
    leaky = acc_margin > 0.85
    admitted = (z > 6.0) and not leaky
    RESULTS["stage5_two_pop"] = {
        "rows_k_lt_9": int(len(lab)),
        "cluster_balance": balance,
        "margin_only_classifier_accuracy": acc_margin,
        "margin_leakage_flag(acc>0.85)": bool(leaky),
        "G_real": G_real,
        "null_n": len(null_G), "null_G_mean": mu, "null_G_sd": sd,
        "z": float(z), "dBc": dbc,
        "verdict": (("two-population statistic deflects (z=%.2f) with acceptable margin "
                     "leakage (acc=%.2f): NOT-EXCLUDED -- the diatomic two-sublattice "
                     "extension earns a matched-parameter ablation" % (z, acc_margin))
                    if admitted else
                    ("recorded outcome: z=%.2f, margin-classifier acc=%.2f -- %s. The "
                     "two-population extension stays %s." %
                     (z, acc_margin,
                      "assignment leaks margin information" if leaky else "no deflection above the floor",
                      "not-tested pending a margin-clean assignment rule" if leaky else "excluded at this budget"))),
    }
    print(f"[stage5] G_real={G_real:.4f} | null {mu:.4f}+-{sd:.4f} z={z:.2f} | "
          f"margin acc={acc_margin:.3f} balance={balance:.2f}")


# ============================================================ main

def main():
    rng = np.random.default_rng(20260901)
    stage1_omega_audit()

    M = defocus.load_real_corpus_matrix().astype(np.int8)
    assert M.shape == (2286, 9)
    phi = stage2_fd_residual(M, rng)

    _, _, fit_real = embed_and_fit(M)
    stage3_units(phi, fit_real.share)

    print("[setup] sampling curveball nulls (40 draws, 20N trades)...")
    null_mats = [curveball(M, 20 * M.shape[0], rng) for _ in range(40)]
    null_fits = [embed_and_fit(Mn)[2] for Mn in null_mats]

    print("[setup] building Gaunt tensor (N=8000 quadrature)...")
    G, ortho_err, max_forb, max_allow = gaunt_tensor()
    stage4_gaunt(M, null_fits, fit_real, G, (ortho_err, max_forb, max_allow))

    stage5_two_pop(M, null_mats, rng)

    print("PHONON_FOLLOWUPS_JSON_BEGIN")
    print(json.dumps(RESULTS, indent=1, sort_keys=True))
    print("PHONON_FOLLOWUPS_JSON_END")
    print("RESULT: ALL FIVE FOLLOW-UPS EXECUTED (outcomes recorded, sanity assertions passed)")


if __name__ == "__main__":
    sys.exit(main())
