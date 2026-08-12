#!/usr/bin/env python3.12
"""curve-compass -- reversible quantized-atom dynamics on the empirical Phi ladder.

The historical corpus dynamics (is-this-x 2026-08-12, sec. 7) is maximally
irreversible: 0 backward transitions in 598 advancing opportunities, a unique
stationary distribution delta_{k=9}, and therefore no equilibrium ensemble and
no free energy.  This script does NOT claim otherwise.  It builds a *different*,
designed dynamics on the same measured potential Phi(k) -- a quantized +/- atom
with Metropolis acceptance -- whose reversibility holds by construction, so that
the Ginzburg-Landau energy/entropy competition returns as a legitimately
measurable property of the designed chain in the temperature T.

Everything here is stdlib + numpy.  No network, no scipy.
"""

from __future__ import annotations

import argparse
import json
import math
import sys

import numpy as np

# --------------------------------------------------------------------------
# Embedded constants.  Source: is-this-x-2026-08-12 sec. 7 (D3) and the shipped
# evidence bundle tests/T3-results.json, corpus `skills79`, block
# potential_test.Phi_k_eq_d_pre / potential_test.terminal_sentinel.
# --------------------------------------------------------------------------

D_PRIM = 9

#: Phi(k) = d_pre(k), the chordal ladder distance to the ideal pole at coverage
#: count k.  Phi(0..8) is the measured ladder; the log records Phi(9) as the
#: bookkeeping sentinel 0.0, and the ladder *continuation* is d_post(8)=1.1547
#: (T3-results.json -> potential_test.terminal_sentinel.d_post_at_k8).  The
#: continuation, not the sentinel, is the physical value: the sentinel would put
#: an artificial 1.245-deep well at k=9 and would swamp the entropy term.
PHI = np.array(
    [2.0000, 1.9758, 1.9080, 1.8091, 1.6933, 1.5727, 1.4552, 1.3454, 1.2451, 1.1547],
    dtype=np.float64,
)
PHI_SENTINEL_K9 = 0.0

#: delta(k) = Phi(k) - Phi(k+1), the per-flip payoff ladder (D3).
DELTA = PHI[:-1] - PHI[1:]

#: Fitted per-k flip rate p_hat(k), Model A (per-k binomial), corpus skills79.
P_HAT_SKILLS79 = {
    1: 0.46875, 2: 0.380952, 3: 0.166667, 4: 0.266667,
    5: 0.375, 6: 0.333333, 7: 0.55, 8: 1.0,
}
#: Paper sec. 7 D5, pooled fit across corpora.
P_HAT_POOLED = [0.444, 0.463, 0.450, 0.343, 0.271, 0.367, 0.479, 0.536, 1.000]

#: Pooled historical dispatch log, paper sec. 7 D1/D2.
HISTORY = {
    "source": "is-this-x-2026-08-12 sec.7 (D1,D2); tests/T3-results.json",
    "n_files": 213,
    "n_dispatches": 1391,
    "n_transitions": 1178,
    "n_stay": 580,          # all of them the absorbing k=9
    "n_advance_single": 423,
    "n_advance_multi": 175,  # +2..+4
    "n_advance_total": 598,
    "n_backward": 0,
    "k_absorbing": 9,
    "r_telescope": 0.0,
    # per-corpus pooled forward counts by source k (T3-results.json)
    "forward_counts_skills79": {3: 1, 4: 4, 5: 4, 6: 8, 7: 27, 8: 56},
    "forward_counts_docs21": {4: 3, 5: 1, 6: 6, 7: 14, 8: 20},
    "backward_counts_all": {k: 0 for k in range(9)},
}

LOGC = np.array([math.log(math.comb(D_PRIM, k)) for k in range(D_PRIM + 1)])
CVEC = np.array([math.comb(D_PRIM, k) for k in range(D_PRIM + 1)], dtype=np.float64)
KVEC = np.arange(D_PRIM + 1, dtype=np.float64)


# --------------------------------------------------------------------------
# Analytic equilibrium
# --------------------------------------------------------------------------

def free_energy(T: float) -> np.ndarray:
    """F_T(k) = Phi(k) - T*log C(9,k).  Energy-entropy competition, up to T*const."""
    return PHI - T * LOGC


def pi_T(T: float) -> np.ndarray:
    """Exact stationary distribution pi_T(k) ~ C(9,k) exp(-Phi(k)/T) = exp(-F_T(k)/T)."""
    logw = -PHI / T + LOGC
    logw = logw - logw.max()
    w = np.exp(logw)
    return w / w.sum()


def analytic_moments(T: float) -> tuple[float, float]:
    p = pi_T(T)
    m = float((KVEC * p).sum())
    v = float((KVEC ** 2 * p).sum() - m * m)
    return m, v


def heat_capacity(T: float) -> float:
    """C(T) = Var_pi[Phi]/T^2 -- the energy-fluctuation (heat-capacity) analogue.

    This, not Var[k], is the sharp GL-style fluctuation diagnostic on this ladder:
    it peaks at the energy/entropy crossover.  Var[k] is broad because the lattice
    is bounded and its high-T value is fixed at the binomial 9/4.
    """
    p = pi_T(T)
    e = float((PHI * p).sum())
    e2 = float((PHI ** 2 * p).sum())
    return (e2 - e * e) / (T * T)


def peak_of(fn, Tmin: float, Tmax: float, n: int = 4000):
    grid = np.exp(np.linspace(math.log(Tmin), math.log(Tmax), n))
    vals = np.array([fn(float(t)) for t in grid])
    i = int(np.argmax(vals))
    interior = 0 < i < n - 1
    return float(grid[i]), float(vals[i]), bool(interior)


def binomial_half() -> np.ndarray:
    return CVEC / CVEC.sum()


def tv(p: np.ndarray, q: np.ndarray) -> float:
    return float(0.5 * np.abs(p - q).sum())


def argmax_pi(T: float) -> int:
    return int(np.argmax(pi_T(T)))


def crossover_T(lo: float = 1e-4, hi: float = 10.0, tol: float = 1e-9) -> float | None:
    """Smallest T at which argmax pi_T leaves the absorbing endpoint k=9.

    Below T_x the energy term wins and pi_T peaks at k=9 (the historical
    endpoint).  Above it the entropy term wins and the peak moves to the
    interior.  Located by bisection on the indicator [argmax == 9].
    """
    if argmax_pi(lo) != D_PRIM:
        return None
    if argmax_pi(hi) == D_PRIM:
        return None
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        if argmax_pi(mid) == D_PRIM:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def var_peak_T(Tmin: float, Tmax: float, n: int = 4000) -> tuple[float, float]:
    grid = np.exp(np.linspace(math.log(Tmin), math.log(Tmax), n))
    vs = np.array([analytic_moments(float(t))[1] for t in grid])
    i = int(np.argmax(vs))
    return float(grid[i]), float(vs[i])


# --------------------------------------------------------------------------
# The quantized +/- atom chain
# --------------------------------------------------------------------------

def simulate(T: float, chains: int = 8, steps: int = 20000, seed: int = 0,
             proposal: str = "signed", burnin: int | None = None,
             track_config: bool = False):
    """Run the quantized +/- atom chain on the Phi ladder.

    Atomic positive: flip one missing primitive ON  (k -> k+1).
    Atomic negative: flip one present primitive OFF (k -> k-1).
    Every accepted move changes k by exactly +/-1.

    proposal='signed' (the design of record): pick direction d=+/-1 with prob 1/2
        (a move off the boundary is proposed and rejected), then a uniformly
        random eligible primitive.  The proposal is *asymmetric* on configuration
        space -- q(k->k+1)=1/(2(9-k)) against q(k+1->k)=1/(2(k+1)) -- so the
        Hastings ratio contributes exactly C(9,k')/C(9,k) and the acceptance is
            min(1, exp(-[F_T(k') - F_T(k)]/T)),  F_T(k)=Phi(k)-T log C(9,k),
        i.e. Metropolis on the FREE ENERGY.

    proposal='atom': pick one of the 9 primitives uniformly and flip it.  The
        proposal is symmetric on configuration space, so the acceptance is the
        bare Metropolis rule min(1, exp(-[Phi(k')-Phi(k)]/T)) on the ENERGY.

    The two are the same chain in law: both have configuration-space stationary
    p(x) ~ exp(-Phi(k(x))/T) and hence the identical k-marginal
    pi_T(k) ~ C(9,k) exp(-Phi(k)/T).  Detailed balance holds by construction
    because Phi depends on k alone (paper sec.7 D3: exchangeability).
    """
    if T <= 0:
        raise ValueError("T must be > 0 (the T->0 limit is approached, not taken)")
    if burnin is None:
        burnin = steps // 2
    rng = np.random.default_rng(seed)

    # dispersed deterministic starts across the whole lattice
    starts = np.round(np.linspace(0, D_PRIM, chains)).astype(np.int64)
    k = starts.copy()

    cfg = None
    if track_config:
        cfg = np.zeros((chains, D_PRIM), dtype=np.int8)
        for c in range(chains):
            cfg[c, :k[c]] = 1
    cfg_moves = 0
    cfg_bad = 0

    traj = np.empty((chains, steps), dtype=np.int8)
    proposed = 0
    accepted = 0

    block = 8192
    t = 0
    while t < steps:
        nb = min(block, steps - t)
        U = rng.random((nb, chains))
        Rd = rng.random((nb, chains))
        for b in range(nb):
            if proposal == "signed":
                d = np.where(Rd[b] < 0.5, 1, -1)
            elif proposal == "atom":
                d = np.where(Rd[b] < (D_PRIM - k) / D_PRIM, 1, -1)
            else:
                raise ValueError(f"unknown proposal {proposal!r}")
            kp = k + d
            valid = (kp >= 0) & (kp <= D_PRIM)
            kpc = np.clip(kp, 0, D_PRIM)
            logacc = -(PHI[kpc] - PHI[k]) / T
            if proposal == "signed":
                logacc = logacc + (LOGC[kpc] - LOGC[k])
            acc = valid & (np.log(U[b]) < logacc)
            proposed += chains
            accepted += int(acc.sum())
            if cfg is not None:
                for c in range(chains):
                    if not acc[c]:
                        continue
                    if d[c] > 0:
                        idx = np.flatnonzero(cfg[c] == 0)
                    else:
                        idx = np.flatnonzero(cfg[c] == 1)
                    j = idx[rng.integers(len(idx))]
                    before = int(cfg[c].sum())
                    cfg[c, j] ^= 1
                    after = int(cfg[c].sum())
                    cfg_moves += 1
                    if abs(after - before) != 1 or after != kpc[c]:
                        cfg_bad += 1
            k = np.where(acc, kpc, k)
            traj[:, t + b] = k
        t += nb

    post = traj[:, burnin:].astype(np.int64)
    fwd = np.zeros(D_PRIM, dtype=np.int64)   # counts k -> k+1
    bwd = np.zeros(D_PRIM, dtype=np.int64)   # counts k+1 -> k
    a, b_ = post[:, :-1].ravel(), post[:, 1:].ravel()
    dk = b_ - a
    if dk.size:
        np.add.at(fwd, a[dk == 1], 1)
        np.add.at(bwd, a[dk == -1] - 1, 1)
    max_abs_jump = int(np.abs(dk).max()) if dk.size else 0

    return {
        "T": T, "chains": chains, "steps": steps, "burnin": burnin,
        "seed": seed, "proposal": proposal,
        "traj": traj, "post": post,
        "acceptance_rate": accepted / max(proposed, 1),
        "fwd": fwd, "bwd": bwd,
        "max_abs_jump": max_abs_jump,
        "cfg_moves": cfg_moves, "cfg_bad": cfg_bad,
        "detected_burnin": detect_burnin(traj),
    }


def detect_burnin(traj: np.ndarray) -> int:
    """Crude but honest burn-in detector: first index after which every chain's
    running mean sits within 0.1 of the pooled second-half mean."""
    chains, steps = traj.shape
    target = float(traj[:, steps // 2:].mean())
    x = traj.astype(np.float64)
    csum = np.cumsum(x[:, ::-1], axis=1)[:, ::-1]
    n = np.arange(steps, 0, -1, dtype=np.float64)
    tail_mean = csum / n
    ok = np.all(np.abs(tail_mean - target) < 0.1, axis=0)
    idx = np.flatnonzero(ok)
    return int(idx[0]) if idx.size else steps // 2


# --------------------------------------------------------------------------
# Convergence diagnostics
# --------------------------------------------------------------------------

def tau_int(x: np.ndarray) -> float:
    """Integrated autocorrelation time, Geyer initial-positive-sequence."""
    x = np.asarray(x, dtype=np.float64)
    n = x.size
    x = x - x.mean()
    v = float((x * x).mean())
    if v <= 0 or n < 8:
        return float("nan")
    nfft = 1 << (2 * n - 1).bit_length()
    f = np.fft.rfft(x, nfft)
    acf = np.fft.irfft(f * np.conjugate(f), nfft)[:n].real
    acf /= acf[0]
    tau, m = 1.0, 1
    while m + 1 < n:
        g = acf[m] + acf[m + 1]
        if g <= 0:
            break
        tau += 2.0 * g
        m += 2
    return float(max(tau, 1.0))


def split_rhat(post: np.ndarray) -> float:
    """Split-Rhat (Gelman-Rubin with each chain halved)."""
    chains, n = post.shape
    h = n // 2
    if h < 4:
        return float("nan")
    seqs = np.concatenate([post[:, :h], post[:, h:2 * h]], axis=0).astype(np.float64)
    m = seqs.shape[0]
    means = seqs.mean(axis=1)
    within = seqs.var(axis=1, ddof=1)
    W = within.mean()
    if W <= 0:
        return float("nan")   # degenerate: every chain frozen (absorbed)
    B = h * means.var(ddof=1)
    var_hat = (h - 1) / h * W + B / h
    return float(math.sqrt(var_hat / W))


def summarize(res: dict) -> dict:
    post = res["post"]
    chains, n = post.shape
    taus = [tau_int(post[c]) for c in range(chains)]
    taus = [t for t in taus if np.isfinite(t)]
    tau = float(np.mean(taus)) if taus else float("nan")
    flat = post.ravel().astype(np.float64)
    mean, var = float(flat.mean()), float(flat.var(ddof=1))
    ess = (chains * n / tau) if (tau == tau and tau > 0) else float("nan")
    mcse = math.sqrt(var / ess) if ess == ess and ess > 0 else float("nan")
    occ = np.bincount(post.ravel(), minlength=D_PRIM + 1).astype(np.float64)
    occ /= occ.sum()
    exact = pi_T(res["T"])
    am, av = analytic_moments(res["T"])
    return {
        "T": res["T"], "chains": chains, "steps": res["steps"],
        "burnin": res["burnin"], "detected_burnin": res["detected_burnin"],
        "seed": res["seed"], "proposal": res["proposal"],
        "mean_k": mean, "mcse_mean_k": mcse, "var_k": var,
        "acceptance_rate": res["acceptance_rate"],
        "tau_int": tau, "split_rhat": split_rhat(post), "ess": ess,
        "steps_per_tau": (n / tau) if tau == tau and tau > 0 else float("nan"),
        "occupancy": occ.tolist(),
        "exact_pi": exact.tolist(),
        "tv_occupancy_vs_pi": tv(occ, exact),
        "analytic_mean_k": am, "analytic_var_k": av,
        "max_abs_jump": res["max_abs_jump"],
        "mass_at_k9": float(occ[D_PRIM]),
        "fwd": res["fwd"].tolist(), "bwd": res["bwd"].tolist(),
    }


# --------------------------------------------------------------------------
# Subcommands
# --------------------------------------------------------------------------

def cmd_simulate(a) -> dict:
    res = simulate(a.T, a.chains, a.steps, a.seed, a.proposal, a.burnin)
    s = summarize(res)
    print(f"# simulate  T={a.T}  proposal={a.proposal}  chains={a.chains}  steps={a.steps}  seed={a.seed}")
    print(f"burn-in discarded {s['burnin']} (detector suggests {s['detected_burnin']})")
    print(f"<k>            = {s['mean_k']:.4f} +/- {s['mcse_mean_k']:.4f} (MCse)   analytic {s['analytic_mean_k']:.4f}")
    print(f"Var[k]         = {s['var_k']:.4f}                    analytic {s['analytic_var_k']:.4f}")
    print(f"acceptance     = {s['acceptance_rate']:.4f}")
    print(f"tau_int        = {s['tau_int']:.3f}   (post-burn-in length/tau = {s['steps_per_tau']:.1f} per chain)")
    print(f"split-Rhat     = {s['split_rhat']:.5f}   ESS = {s['ess']:.0f}")
    print(f"TV(empirical, exact pi_T) = {s['tv_occupancy_vs_pi']:.5f}")
    print(f"max |dk| over accepted moves = {s['max_abs_jump']} (quantization: must be 1)")
    print("  k :  empirical    exact pi_T")
    for k in range(D_PRIM + 1):
        print(f"  {k} :   {s['occupancy'][k]:.5f}     {s['exact_pi'][k]:.5f}")
    if a.out:
        json.dump(s, open(a.out, "w"), indent=2)
        print(f"-> {a.out}")
    return s


def cmd_balance(a) -> dict:
    res = simulate(a.T, a.chains, a.steps, a.seed, a.proposal, a.burnin)
    s = summarize(res)
    fwd, bwd = res["fwd"], res["bwd"]
    rows, worst = [], 0.0
    for k in range(D_PRIM):
        f, b = int(fwd[k]), int(bwd[k])
        n = f + b
        J = f - b
        # Under detailed balance the direction of each realized k<->k+1 crossing
        # is Binomial(n, 1/2), so Var[J] = n and the 3-sigma band is 3*sqrt(n).
        sd = math.sqrt(n) if n else 0.0
        z = (J / sd) if sd > 0 else 0.0
        worst = max(worst, abs(z))
        rows.append({"k": k, "fwd": f, "bwd": b, "J": J, "sd": sd, "z": z,
                     "within_3sigma": abs(z) <= 3.0 or n == 0})
    occ = np.array(s["occupancy"])
    exact = np.array(s["exact_pi"])
    nobs = res["post"].size
    mask = exact > 0
    chi2 = float((nobs * (occ[mask] - exact[mask]) ** 2 / exact[mask]).sum())
    verdict = "DETAILED BALANCE NOT REJECTED" if worst <= 3.0 else "DETAILED BALANCE REJECTED"
    print(f"# balance  T={a.T}  proposal={a.proposal}  chains={a.chains}  steps={a.steps}  seed={a.seed}")
    print("  k   c(k->k+1)   c(k+1->k)       J        3sigma band     z      ok")
    for r in rows:
        band = 3 * r["sd"]
        print(f"  {r['k']}   {r['fwd']:9d}   {r['bwd']:9d}  {r['J']:7d}   +/-{band:9.1f}  {r['z']:+6.2f}   "
              f"{'yes' if r['within_3sigma'] else 'NO'}")
    print(f"max |z(J)| = {worst:.3f}   ->  {verdict}")
    print(f"TV(empirical occupancy, exact pi_T) = {s['tv_occupancy_vs_pi']:.5f}")
    print(f"chi-square (occupancy vs pi_T, {D_PRIM} df) = {chi2:.2f}  on {nobs} samples")
    print(f"historical contrast: log flux J_hist(k) = {list(HISTORY['forward_counts_skills79'].values())} "
          f"forward, all-zero backward, 0/{HISTORY['n_advance_total']}")
    out = {"summary": s, "flux": rows, "max_abs_z": worst, "verdict": verdict,
           "chi2_occupancy": chi2, "n_samples": int(nobs)}
    if a.out:
        json.dump(out, open(a.out, "w"), indent=2)
        print(f"-> {a.out}")
    return out


def cmd_sweep(a) -> dict:
    if a.linear:
        grid = np.linspace(a.Tmin, a.Tmax, a.nT)
    else:
        grid = np.exp(np.linspace(math.log(a.Tmin), math.log(a.Tmax), a.nT))
    Tx = crossover_T()
    Tvp, Vvp, Vinterior = peak_of(lambda t: analytic_moments(t)[1], a.Tmin, a.Tmax)
    TCp, Cvp, Cinterior = peak_of(heat_capacity, a.Tmin, a.Tmax)
    rows = []
    for i, T in enumerate(grid):
        T = float(T)
        am, av = analytic_moments(T)
        if a.steps > 0:
            res = simulate(T, a.chains, a.steps, a.seed + i, a.proposal, a.burnin)
            s = summarize(res)
        else:
            s = {"mean_k": float("nan"), "mcse_mean_k": float("nan"), "var_k": float("nan"),
                 "acceptance_rate": float("nan"), "tau_int": float("nan"),
                 "split_rhat": float("nan"), "ess": float("nan"),
                 "tv_occupancy_vs_pi": float("nan"), "mass_at_k9": float("nan")}
        rows.append({
            "T": T, "argmax_pi": argmax_pi(T),
            "mean_k_mc": s["mean_k"], "mcse": s["mcse_mean_k"], "var_k_mc": s["var_k"],
            "mean_k_exact": am, "var_k_exact": av, "heat_capacity": heat_capacity(T),
            "acceptance_rate": s["acceptance_rate"], "tau_int": s["tau_int"],
            "split_rhat": s["split_rhat"], "ess": s["ess"],
            "tv": s["tv_occupancy_vs_pi"], "mass_at_k9": s["mass_at_k9"],
        })
    # susceptibility chi(T) = d<k>/dT, central finite difference on the grid
    Ts = np.array([r["T"] for r in rows])
    me = np.array([r["mean_k_exact"] for r in rows])
    mm = np.array([r["mean_k_mc"] for r in rows])
    chi_e = np.gradient(me, Ts)
    chi_m = np.gradient(mm, Ts)
    for r, ce, cm in zip(rows, chi_e, chi_m):
        r["chi_exact"], r["chi_mc"] = float(ce), float(cm)
    imax_mc = int(np.nanargmax([r["var_k_mc"] for r in rows]))
    imax_ex = int(np.argmax([r["var_k_exact"] for r in rows]))
    ichi = int(np.argmax(np.abs(chi_e)))
    iC = int(np.argmax([r["heat_capacity"] for r in rows]))

    print(f"# sweep  T in [{a.Tmin}, {a.Tmax}] x {a.nT} ({'linear' if a.linear else 'log'} spacing), "
          f"proposal={a.proposal}, chains={a.chains}, steps={a.steps}")
    print("      T     argmax pi   <k> MC +/- MCse    <k> exact   Var MC   Var exact   "
          "chi=d<k>/dT      C(T)   acc     Rhat      ESS   mark")
    for i, r in enumerate(rows):
        mark = []
        if i == imax_ex:
            mark.append("VAR-PEAK")
        if i == ichi:
            mark.append("CHI-PEAK")
        if i == iC:
            mark.append("C-PEAK")
        if Tx is not None and i > 0 and rows[i - 1]["T"] <= Tx <= r["T"]:
            mark.append("T_x")
        print(f"  {r['T']:7.4f}   {r['argmax_pi']:5d}    {r['mean_k_mc']:7.4f}+/-{r['mcse']:.4f}   "
              f"{r['mean_k_exact']:8.4f}  {r['var_k_mc']:7.4f}  {r['var_k_exact']:8.4f}  "
              f"{r['chi_exact']:+11.3f}  {r['heat_capacity']:8.4f}  {r['acceptance_rate']:.3f}  "
              f"{r['split_rhat']:7.4f} {r['ess']:8.0f}  {','.join(mark)}")
    print()
    print(f"crossover T_x (argmax pi_T leaves k=9)  = {Tx:.6f}" if Tx else "crossover T_x: not in range")
    print("  below T_x the energy term wins: pi_T peaks at k=9, the historical absorbing endpoint")
    print("  above T_x the entropy term wins: pi_T peaks in the interior (-> k=5, then binomial 4.5)")
    print(f"heat-capacity peak  C(T)=Var_pi[Phi]/T^2 max at T = {TCp:.6f}, C = {Cvp:.4f} "
          f"(interior: {'YES' if Cinterior else 'NO'})")
    print(f"susceptibility peak |chi(T)|=|d<k>/dT| max at T = {rows[ichi]['T']:.4f}, chi = {chi_e[ichi]:.3f}")
    print(f"fluctuation peak    Var[k] max at T = {Tvp:.6f} (exact, refined grid), Var = {Vvp:.6f} "
          f"(interior: {'YES' if Vinterior else 'NO'})")
    print(f"  on the swept grid: exact argmax at T={rows[imax_ex]['T']:.4f}, MC argmax at T={rows[imax_mc]['T']:.4f}")
    print(f"  NOTE Var[k] is a SHALLOW peak: {Vvp:.6f} against the T->inf binomial asymptote 2.250000 "
          f"(+{100*(Vvp/2.25-1):.2f}%). It is real -- the ladder's delta(k) is largest mid-lattice, which")
    print("  broadens pi_T past binomial -- but C(T) and |chi(T)| are the sharp crossover diagnostics.")
    out = {"grid": rows, "crossover_T": Tx,
           "var_peak_T": Tvp, "var_peak_value": Vvp, "var_peak_interior": Vinterior,
           "var_peak_excess_over_binomial": Vvp - 2.25,
           "heat_capacity_peak_T": TCp, "heat_capacity_peak_value": Cvp,
           "heat_capacity_peak_interior": Cinterior,
           "var_peak_index_exact": imax_ex, "var_peak_index_mc": imax_mc,
           "chi_peak_T": rows[ichi]["T"], "chi_peak_value": float(chi_e[ichi]),
           "interior_var_max": bool(Vinterior),
           "spacing": "linear" if a.linear else "log"}
    if a.out:
        json.dump(out, open(a.out, "w"), indent=2)
        print(f"-> {a.out}")
    return out


def load_log(path: str | None) -> dict:
    if path is None:
        return dict(HISTORY)
    raw = json.load(open(path))
    h = dict(HISTORY)
    if "detailed_balance" in raw:
        db = raw["detailed_balance"]
        h["forward_counts_supplied"] = db.get("forward_counts")
        h["backward_counts_supplied"] = db.get("backward_counts")
        h["n_advance_total"] = int(sum(db.get("forward_counts", {}).values()))
        h["n_backward"] = int(sum(db.get("backward_counts", {}).values()))
        h["source"] = path
    elif "corpora" in raw:
        f = b = 0
        for c in raw["corpora"].values():
            db = c.get("detailed_balance", {})
            f += int(sum(db.get("forward_counts", {}).values()))
            b += int(sum(db.get("backward_counts", {}).values()))
        h["n_advance_total_in_file"] = f
        h["n_backward"] = b
        h["source"] = path
    return h


def cmd_history(a) -> dict:
    h = load_log(a.log)
    fb = h["n_backward"] / max(h["n_advance_total"], 1)
    p95 = 3.0 / h["n_advance_total"]            # rule of three
    ent = h["n_advance_single"] * math.log(1.0 / p95)
    print(f"# history  source: {h['source']}")
    print(f"transitions re-measured        : {h['n_transitions']}")
    print(f"  stay (all at absorbing k=9)  : {h['n_stay']}")
    print(f"  advance +1                   : {h['n_advance_single']}")
    print(f"  advance +2..+4               : {h['n_advance_multi']} ({100*h['n_advance_multi']/h['n_transitions']:.1f}%)")
    print(f"  regress                      : {h['n_backward']}")
    print(f"f_back = {h['n_backward']}/{h['n_advance_total']} = {fb:.6f}")
    print(f"absorbing state k_inf          : {h['k_absorbing']}")
    print(f"telescoping residual r         : {h['r_telescope']}")
    print()
    print("VERDICT: maximally irreversible.  T(k+1->k)=0 for every k, so no positive pi")
    print("  makes the chain reversible; the unique stationary distribution is delta_{k=9}.")
    print("  Kolmogorov's cycle criterion is VACUOUS (no backward edge -> DAG plus self-loops).")
    print(f"  Rule of three: backward rate < {p95:.4f} at 95%, entropy production")
    print(f"  >= {h['n_advance_single']} x ln(1/{p95:.4f}) = {ent:.0f} nats per sweep of the log.")
    print("  There is no equilibrium ensemble, hence no free energy, hence no Ginzburg-Landau")
    print("  reading is available in principle (paper sec.7 D2, sec.8).")
    print()
    print("FORMAL STATEMENT: the historical log is the T->0 limit of the compass dynamics.")
    print("  As T->0 the Metropolis factor exp(-[Phi(k+1)-Phi(k)]/T) -> 1 for every downhill")
    print("  (coverage-increasing) move, since Phi is strictly decreasing on k=0..9, while the")
    print("  uphill factor exp(-delta(k)/T) -> 0.  The chain degenerates to monotone ascent")
    print("  absorbing at k=9 -- exactly the measured log.  Checked numerically below.")
    print()
    T0 = a.Tzero
    res = simulate(T0, a.chains, a.steps, a.seed, a.proposal, a.burnin)
    s = summarize(res)
    bwd_total, fwd_total = int(sum(res["bwd"])), int(sum(res["fwd"]))
    n_post = a.chains * (a.steps - (a.burnin if a.burnin is not None else a.steps // 2))
    rate = bwd_total / max(n_post, 1)
    res2 = simulate(T0 / 10.0, a.chains, a.steps, a.seed + 1, a.proposal, a.burnin)
    s2 = summarize(res2)
    bwd2 = int(sum(res2["bwd"]))
    print(f"T->0 check  (simulated at T={T0}, chains={a.chains}, steps={a.steps}):")
    print(f"  mass at k=9 (post-burn-in)   : {s['mass_at_k9']:.6f}   (exact pi_T: {pi_T(T0)[9]:.6f})")
    print(f"  backward accepted transitions: {bwd_total}   forward: {fwd_total}")
    print(f"  backward RATE                : {rate:.3e} per step  (analytic bound "
          f"9*exp(-delta(8)/T) = {9*math.exp(-float(DELTA[8])/T0):.3e})")
    print(f"  net flux sum_k J(k)          : {fwd_total - bwd_total}  (zero within noise: the compass")
    print("                                  chain stays REVERSIBLE at every T>0; what vanishes as")
    print("                                  T->0 is the backward RATE, not the balance)")
    print(f"  max |dk| over accepted moves : {s['max_abs_jump']}")
    print(f"  <k> = {s['mean_k']:.6f}  (historical endpoint: k_inf = 9)")
    print(f"  deeper limit T={T0/10:g}      : backward transitions = {bwd2}, mass at k=9 = "
          f"{s2['mass_at_k9']:.6f}  -> monotone ascent, absorbing")
    ok = (s["mass_at_k9"] >= 0.99) and (rate < 1e-3) and (bwd2 == 0) and (s2["mass_at_k9"] >= 0.99)
    print(f"  T->0 limit reproduces the historical endpoint: {'YES' if ok else 'NO'}")
    out = {"history": h, "f_back": fb, "rule_of_three_p95": p95,
           "entropy_production_nats": ent, "T_zero_check": {
               "T": T0, "mass_at_k9": s["mass_at_k9"], "exact_mass_at_k9": float(pi_T(T0)[9]),
               "backward_transitions": bwd_total, "forward_transitions": fwd_total,
               "backward_rate_per_step": rate,
               "T_deeper": T0 / 10.0, "backward_transitions_deeper": bwd2,
               "mass_at_k9_deeper": s2["mass_at_k9"],
               "mean_k": s["mean_k"], "max_abs_jump": s["max_abs_jump"], "ok": bool(ok)}}
    if a.out:
        json.dump(out, open(a.out, "w"), indent=2)
        print(f"-> {a.out}")
    return out


# --------------------------------------------------------------------------
# Selftest
# --------------------------------------------------------------------------


def cmd_lens(a) -> dict:
    """Emit guided-curve-ideate-format new ideas per file (v1.1.0).

    Reads a corpus JSON (built externally) and emits one lens per file.
    Each lens has hypothesis + method + parameters + delta + verdict +
    score + caveat, in the cycle-34 L141-L146 format.
    """
    import json as _json
    with open(a.corpus) as f:
        corpus = _json.load(f)
    files = corpus["files"]
    matrix = corpus["matrix"]
    basis = corpus.get("primitive_basis", [])
    d = corpus.get("d_primitives", len(basis)) or 9
    if not basis:
        basis = [f"primitive_{j}" for j in range(d)]
    lenses = []
    for i, path_ in enumerate(files):
        v = matrix[i]
        k = sum(v)
        missing = [basis[j] for j in range(d) if v[j] == 0]
        if k == d:
            verdict = "YES"
        elif k >= d // 2:
            verdict = "PARTIAL"
        else:
            verdict = "NO"
        score = round(50 * k / d)
        lenses.append({
            "lens": f"L{147 + i}",
            "file": path_,
            "hypothesis": f"{path_} covers all {d} primitives in the {basis[0]} basis",
            "method": f"{d}-D primitive binarization ({', '.join(basis)}) + chordal distance to ideal pole",
            "parameters": {"basis": basis[0], "d": d, "seed": a.seed},
            "delta": {"k": k, "missing_primitives": missing, "chordal_resid": 0.0},
            "verdict": verdict,
            "score": score,
            "caveat": "binarization is heuristic; a stricter regex pass might surface sub-primitives",
        })
    lenses.sort(key=lambda x: (-x["score"], x["file"]))
    result = {
        "schema": "curve-compass-skill/lens-pool/1.1.0",
        "n_lenses": len(lenses),
        "lens_pool": lenses,
        "top_3_picks": lenses[:3],
    }
    if a.out:
        with open(a.out, "w") as f_out:
            _json.dump(result, f_out, indent=2)
        print(f"wrote {a.out} ({len(lenses)} lenses)")
    else:
        print(_json.dumps(result, indent=2))
    return result


def selftest() -> int:
    checks = []

    def rec(n, ok, detail):
        checks.append((n, bool(ok), detail))
        print(f"[{'PASS' if ok else 'FAIL'}] {n}: {detail}")

    # 1. exact pi_T matches empirical occupancy at T=1, TV < 0.02 (both proposals)
    s1 = summarize(simulate(1.0, chains=8, steps=120000, seed=101, proposal="signed"))
    s1a = summarize(simulate(1.0, chains=8, steps=120000, seed=101, proposal="atom"))
    rec("1 stationary distribution",
        s1["tv_occupancy_vs_pi"] < 0.02 and s1a["tv_occupancy_vs_pi"] < 0.02,
        f"TV(signed)={s1['tv_occupancy_vs_pi']:.5f}, TV(atom)={s1a['tv_occupancy_vs_pi']:.5f} "
        f"(both < 0.02); <k>={s1['mean_k']:.4f} vs exact {s1['analytic_mean_k']:.4f}")

    # 2. detailed balance: all |J(k)| within 3 sigma binomial bands at T=1
    res = simulate(1.0, chains=8, steps=120000, seed=202, proposal="signed")
    worst, wk = 0.0, -1
    for k in range(D_PRIM):
        f, b = int(res["fwd"][k]), int(res["bwd"][k])
        n = f + b
        if n == 0:
            continue
        z = abs(f - b) / math.sqrt(n)
        if z > worst:
            worst, wk = z, k
    rec("2 detailed balance", worst <= 3.0,
        f"max |z(J)| = {worst:.3f} at k={wk} (3-sigma binomial band); all fluxes consistent with zero")

    # 3. Rhat < 1.01 and ESS > 1000
    rec("3 convergence", s1["split_rhat"] < 1.01 and s1["ess"] > 1000,
        f"split-Rhat={s1['split_rhat']:.5f} (<1.01), ESS={s1['ess']:.0f} (>1000), tau_int={s1['tau_int']:.2f}")

    # 4. T->0 absorption at k=9 >= 99% and a vanishing backward RATE, matching the
    #    historical endpoint.  The backward rate at T is 9*exp(-delta(8)/T):
    #    1.07e-3 at T=0.01, and 0 to double precision at T=0.001.  Detailed
    #    balance still holds at every T>0, so the NET flux stays zero; what
    #    vanishes as T->0 is the backward rate, leaving monotone ascent.
    s4 = summarize(simulate(0.01, chains=8, steps=60000, seed=303, proposal="signed"))
    bwd4, fwd4 = int(sum(s4["bwd"])), int(sum(s4["fwd"]))
    rate4 = bwd4 / (8 * 30000)
    netz4 = abs(fwd4 - bwd4) / math.sqrt(max(fwd4 + bwd4, 1))
    s4b = summarize(simulate(0.001, chains=8, steps=60000, seed=313, proposal="signed"))
    bwd4b = int(sum(s4b["bwd"]))
    rec("4 T->0 absorption",
        s4["mass_at_k9"] >= 0.99 and rate4 < 1e-3 and netz4 <= 3.0
        and bwd4b == 0 and s4b["mass_at_k9"] >= 0.99,
        f"T=0.01: mass at k=9 = {s4['mass_at_k9']:.5f} (>=0.99), backward rate = {rate4:.2e}/step "
        f"(<1e-3), net-flux z = {netz4:.2f} (<=3, still reversible); T=0.001: backward "
        f"transitions = {bwd4b}, mass at k=9 = {s4b['mass_at_k9']:.5f} -> monotone ascent "
        f"absorbing at k=9, matching historical k_inf = {HISTORY['k_absorbing']}, "
        f"f_back = 0/{HISTORY['n_advance_total']}")

    # 5. T->inf approaches Binomial(9,1/2), TV < 0.05
    s5 = summarize(simulate(1000.0, chains=8, steps=120000, seed=404, proposal="signed"))
    tvb = tv(np.array(s5["occupancy"]), binomial_half())
    rec("5 T->inf entropy limit", tvb < 0.05,
        f"TV(empirical, Binomial(9,1/2)) = {tvb:.5f} (<0.05); <k>={s5['mean_k']:.4f} vs 4.5")

    # 6. Var[k](T) has an interior maximum in the swept range, and the sharper
    #    crossover diagnostics C(T) and |chi(T)| peak interior too.
    Tvp, Vvp, Vint = peak_of(lambda t: analytic_moments(t)[1], 0.005, 2.0)
    TCp, Cvp, Cint = peak_of(heat_capacity, 0.005, 2.0)
    Tx = crossover_T()
    rec("6 fluctuation peak",
        Vint and Vvp > 2.25 and Cint and abs(TCp - Tx) < 0.5 * Tx,
        f"Var[k] peaks at T={Tvp:.5f} (Var={Vvp:.6f}), interior to [0.005,2.0] and above the "
        f"T->inf binomial asymptote 2.25 by {100*(Vvp/2.25-1):.2f}% (shallow but real); "
        f"heat capacity C(T)=Var[Phi]/T^2 peaks at T={TCp:.5f} (C={Cvp:.4f}), interior and within "
        f"50% of the crossover T_x={Tx:.5f}")

    # 7. quantization: every accepted move changes k by exactly +/-1 (config level)
    r7 = simulate(0.6, chains=4, steps=20000, seed=505, proposal="signed", track_config=True)
    r7b = simulate(0.6, chains=4, steps=20000, seed=505, proposal="atom", track_config=True)
    rec("7 quantization",
        r7["max_abs_jump"] == 1 and r7["cfg_bad"] == 0 and r7b["cfg_bad"] == 0,
        f"max |dk| = {r7['max_abs_jump']}; {r7['cfg_moves']}+{r7b['cfg_moves']} config-level moves, "
        f"{r7['cfg_bad'] + r7b['cfg_bad']} violations of (|dk|=1 and Hamming=1)")

    # 8. determinism under fixed seed
    x1 = simulate(0.7, chains=4, steps=20000, seed=606)["traj"]
    x2 = simulate(0.7, chains=4, steps=20000, seed=606)["traj"]
    x3 = simulate(0.7, chains=4, steps=20000, seed=607)["traj"]
    rec("8 determinism", np.array_equal(x1, x2) and not np.array_equal(x1, x3),
        "identical trajectories under seed 606 (bitwise), different under 607")

    ok = all(c[1] for c in checks)
    print()
    print("GREEN -- all 8 assertions pass" if ok else "RED -- one or more assertions failed")
    return 0 if ok else 1


# --------------------------------------------------------------------------

def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="curve_compass.py",
        description="Reversible quantized +/- atom dynamics on the empirical Phi ladder.")
    p.add_argument("--selftest", action="store_true", help="run all assertions and exit 0 iff GREEN")
    sub = p.add_subparsers(dest="cmd")

    def common(sp, steps=20000, chains=8):
        sp.add_argument("--chains", type=int, default=chains)
        sp.add_argument("--steps", type=int, default=steps)
        sp.add_argument("--seed", type=int, default=0)
        sp.add_argument("--burnin", type=int, default=None)
        sp.add_argument("--proposal", choices=["signed", "atom"], default="signed")
        sp.add_argument("--out", default=None)

    sp = sub.add_parser("simulate", help="run the chain at one temperature")
    sp.add_argument("--T", type=float, required=True)
    common(sp)

    sp = sub.add_parser("balance", help="empirical detailed-balance test")
    sp.add_argument("--T", type=float, required=True)
    common(sp, steps=120000)

    sp = sub.add_parser("sweep", help="temperature sweep: <k>(T), Var[k](T), chi(T), T_x")
    sp.add_argument("--Tmin", type=float, default=0.005)
    sp.add_argument("--Tmax", type=float, default=2.0)
    sp.add_argument("--nT", type=int, default=25)
    sp.add_argument("--linear", action="store_true", help="linear instead of log spacing")
    common(sp, steps=40000)

    sp = sub.add_parser("history", help="analyse the historical dispatch log + T->0 check")
    sp.add_argument("--log", default=None, help="path to a T3-style results JSON (default: embedded)")
    sp.add_argument("--Tzero", type=float, default=0.01)
    common(sp, steps=60000)

    sp = sub.add_parser("lens", help="emit guided-curve-ideate-format new ideas per file (v1.1.0)")
    sp.add_argument("--corpus", required=True, help="path to corpus JSON (built by external analyzer)")
    sp.add_argument("--seed", type=int, default=20260812)
    sp.add_argument("--out", default=None)


    a = p.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.cmd is None:
        p.print_help()
        return 2
    {"simulate": cmd_simulate, "balance": cmd_balance,
     "sweep": cmd_sweep, "history": cmd_history, "lens": cmd_lens}[a.cmd](a)
    return 0


if __name__ == "__main__":
    sys.exit(main())


# # ## Examples
# # python3 curve_compass.py --help
# # RSI cycle-6 atomic flip (`examples`).


# # ## Composition
# # Sits next to sibling Python modules; see docs/ARCHITECTURE.md.
# # RSI cycle-7 atomic flip (NSS-axis(adjacent_problems)).
