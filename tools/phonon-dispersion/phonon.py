#!/usr/bin/env python3
"""phonon-dispersion -- the acoustic/optical phonon reading of the curved-corpus
program, as a deterministic instrument. Pure stdlib (no numpy).

Companion to refs/acoustic-optical-phonons-bridge-2026-09-01.md and Lean
section 14 (papers/data/lean/CurvedCorpus.lean). Everything here is
identity-side: closed-form dispersion algebra, exact graph-Laplacian spectra,
Gaunt selection-rule combinatorics, and the Fermi-Dirac/Binomial identity for
the compass stationary law at linear Phi. Nothing here is a corpus statistic;
no curveball null is required because no corpus-specific claim is made.
Any future corpus-facing readout (e.g. the FD-residual "interaction beyond the
ideal two-state gas") must first pass its own curveball admission null.

Modes:
  --selftest            run all exact checks (CI gate; exits nonzero on any FAIL)
  --dispersion M1 M2    print the diatomic two-branch dispersion table
  --gaunt L             print Gaunt triangle+parity triad counts for l <= L
  --fd EPS T            compare pi_T(k) at linear Phi(k)=EPS*k with Binomial(9,p)

Verified sources for every closed form are cited in the refs/ bridge doc.
"""

import math
import sys
from functools import lru_cache

D_PRIMITIVES = 9  # the program's primitive count (coverage shells k = 0..9)


# ---------------------------------------------------------------- dispersion

def monatomic_omega(q, C=1.0, m=1.0, a=1.0):
    """1D monatomic chain: omega(q) = 2*sqrt(C/m)*|sin(q a / 2)|."""
    return 2.0 * math.sqrt(C / m) * abs(math.sin(q * a / 2.0))


def diatomic_omega2(q, m1, m2, C=1.0, a=1.0):
    """1D diatomic chain (cell period a, two masses): the two branches
    omega^2_{+,-}(q) = C(1/m1+1/m2) +/- C*sqrt((1/m1+1/m2)^2 - 4 sin^2(qa/2)/(m1 m2)).
    Returns (acoustic_sq, optical_sq)."""
    s = 1.0 / m1 + 1.0 / m2
    disc = s * s - 4.0 * (math.sin(q * a / 2.0) ** 2) / (m1 * m2)
    root = math.sqrt(max(disc, 0.0))
    return C * (s - root), C * (s + root)


def diatomic_gap(m1, m2, C=1.0):
    """Zone-boundary band gap: sqrt(2C/m_light) - sqrt(2C/m_heavy). 0 iff m1==m2."""
    ml, mh = min(m1, m2), max(m1, m2)
    return math.sqrt(2.0 * C / ml) - math.sqrt(2.0 * C / mh)


def klemens_allowed(m1, m2, C=1.0):
    """Klemens channel on the diatomic chain: zone-center optical ->
    two zone-boundary acoustic quanta is energetically allowed iff
    omega_opt(0) <= 2*omega_ac_max, i.e. iff m_heavy/m_light <= 3."""
    w_opt2 = 2.0 * C * (1.0 / m1 + 1.0 / m2)
    w_ac_max2 = 2.0 * C / max(m1, m2)
    return w_opt2 <= 4.0 * w_ac_max2 + 1e-12


# ---------------------------------------------------- Laplacian / Hamming

def binom(n, k):
    return math.comb(n, k)


def hamming_laplacian_check(d):
    """Exact integer check: on H(d,2) = Q_d, the combinatorial Laplacian
    L = D - A applied to the character chi_r(a) = (-1)^(r.a) gives
    2*wt(r) * chi_r. Verified for every r in {0,1}^d. Returns True/False."""
    n = 1 << d
    for r in range(n):
        wt = bin(r).count("1")
        for a in range(n):
            chi_a = -1 if bin(r & a).count("1") % 2 else 1
            # (L chi)(a) = d*chi(a) - sum over neighbors chi(a ^ 2^i)
            acc = d * chi_a
            for i in range(d):
                b = a ^ (1 << i)
                chi_b = -1 if bin(r & b).count("1") % 2 else 1
                acc -= chi_b
            if acc != 2 * wt * chi_a:
                return False
    return True


def sphere_eigen(l):
    """Laplace-Beltrami eigenvalue on S^2 and the program's energy decay rate."""
    return l * (l + 1), 2 * l * (l + 1)


# ------------------------------------------------------------------- Gaunt

def gaunt_allowed(l1, l2, l3):
    """Zonal (m=0) Gaunt selection rule: triangle + even parity."""
    tri = l3 <= l1 + l2 and l1 <= l2 + l3 and l2 <= l1 + l3
    return tri and (l1 + l2 + l3) % 2 == 0


def gaunt_counts(L):
    """(total, triangle_only, triangle_and_parity) triad counts for l_i <= L."""
    tot = tri = allowed = 0
    for l1 in range(L + 1):
        for l2 in range(L + 1):
            for l3 in range(L + 1):
                tot += 1
                t = l3 <= l1 + l2 and l1 <= l2 + l3 and l2 <= l1 + l3
                tri += t
                allowed += t and (l1 + l2 + l3) % 2 == 0
    return tot, tri, allowed


def wigner3j000(l1, l2, l3):
    """Wigner 3j symbol (l1 l2 l3; 0 0 0), exact closed form (Racah).
    Zero unless triangle holds and J = l1+l2+l3 is even."""
    J = l1 + l2 + l3
    if J % 2 == 1:
        return 0.0
    if not (l3 <= l1 + l2 and l1 <= l2 + l3 and l2 <= l1 + l3):
        return 0.0
    g = J // 2
    f = math.factorial
    delta = f(J - 2 * l1) * f(J - 2 * l2) * f(J - 2 * l3) / f(J + 1)
    val = ((-1) ** g) * math.sqrt(delta) * f(g) / (f(g - l1) * f(g - l2) * f(g - l3))
    return val


@lru_cache(maxsize=None)
def legendre(l, x):
    """P_l(x) by the Bonnet recurrence."""
    if l == 0:
        return 1.0
    if l == 1:
        return x
    return ((2 * l - 1) * x * legendre(l - 1, x) - (l - 1) * legendre(l - 2, x)) / l


def triple_legendre_integral(l1, l2, l3, n=4001):
    """Simpson integration of P_l1 P_l2 P_l3 over [-1, 1] (n odd)."""
    h = 2.0 / (n - 1)
    acc = 0.0
    for i in range(n):
        x = -1.0 + i * h
        w = 1.0 if i in (0, n - 1) else (4.0 if i % 2 == 1 else 2.0)
        acc += w * legendre(l1, x) * legendre(l2, x) * legendre(l3, x)
    return acc * h / 3.0


# --------------------------------------------- Fermi-Dirac / Binomial identity

def pi_T_linear_phi(eps, T, d=D_PRIMITIVES):
    """Compass stationary law pi_T(k) prop C(d,k) exp(-eps*k/T) at linear
    Phi(k) = eps*k, normalized."""
    w = [binom(d, k) * math.exp(-eps * k / T) for k in range(d + 1)]
    z = sum(w)
    return [x / z for x in w]


def binomial_fd(eps, T, d=D_PRIMITIVES):
    """Binomial(d, p) with the Fermi-Dirac per-primitive occupancy
    p = 1/(1 + exp(eps/T))."""
    p = 1.0 / (1.0 + math.exp(eps / T))
    return [binom(d, k) * (p ** k) * ((1.0 - p) ** (d - k)) for k in range(d + 1)]


# ---------------------------------------------------------------- selftest

def selftest():
    ok_all = True

    def check(name, ok, detail=""):
        nonlocal ok_all
        ok_all &= ok
        print(("PASS" if ok else "FAIL") + f" {name}" + (f" -- {detail}" if detail else ""))

    # 1. Diatomic branch anatomy (m1=1, m2=3, C=1).
    m1, m2, C = 1.0, 3.0, 1.0
    s = 1.0 / m1 + 1.0 / m2
    ac0, op0 = diatomic_omega2(0.0, m1, m2, C)
    check("acoustic_gapless_at_zone_center", abs(ac0) < 1e-12, f"omega2_-(0)={ac0:.2e}")
    check("optical_zone_center", abs(op0 - 2 * C * s) < 1e-12,
          f"omega2_+(0)={op0:.6f} vs 2C(1/m1+1/m2)={2*C*s:.6f}")
    acb, opb = diatomic_omega2(math.pi, m1, m2, C)  # zone boundary of the cell BZ
    check("zone_boundary_heavy", abs(acb - 2 * C / m2) < 1e-12, f"{acb:.6f} vs {2*C/m2:.6f}")
    check("zone_boundary_light", abs(opb - 2 * C / m1) < 1e-12, f"{opb:.6f} vs {2*C/m1:.6f}")
    check("gap_positive_unequal_masses", diatomic_gap(m1, m2) > 0,
          f"gap={diatomic_gap(m1, m2):.6f}")
    check("gap_closes_equal_masses", abs(diatomic_gap(2.0, 2.0)) < 1e-15)
    # acoustic branch monotone on [0, pi]
    qs = [math.pi * i / 200 for i in range(201)]
    mono = all(diatomic_omega2(qs[i], m1, m2)[0] <= diatomic_omega2(qs[i + 1], m1, m2)[0] + 1e-12
               for i in range(200))
    check("acoustic_branch_monotone", mono)
    # monatomic consistency: diatomic (cell period a=1, atom spacing a/2)
    # with m1=m2 collapses onto the monatomic chain at spacing 1/2
    w2eq, _ = diatomic_omega2(1.1, 1.7, 1.7)
    check("equal_mass_collapse_is_monatomic",
          abs(math.sqrt(w2eq) - monatomic_omega(1.1, 1.0, 1.7, 0.5)) < 1e-12)

    # 2. Klemens energy condition: allowed iff m_heavy/m_light <= 3.
    check("klemens_allowed_ratio2", klemens_allowed(1.0, 2.0))
    check("klemens_boundary_ratio3", klemens_allowed(1.0, 3.0))
    check("klemens_forbidden_ratio4", not klemens_allowed(1.0, 4.0))

    # 3. Acoustic sum rule / zero mode: Hamming Laplacian on characters, exact.
    check("hamming_laplacian_spectrum_d4", hamming_laplacian_check(4),
          "L chi_r = 2*wt(r) chi_r for all 16 characters of Q_4")
    check("hamming_zero_mode", hamming_laplacian_check(1), "j=0 all-ones annihilated")

    # 4. S^2 spectrum vs Hamming: quadratic vs linear level penalty.
    tbl_ok = all(sphere_eigen(l) == (l * (l + 1), 2 * l * (l + 1)) for l in range(9))
    dom_ok = all(2 * l * (l + 1) > 2 * l for l in range(1, 9))
    check("sphere_eigenvalues", tbl_ok, "lambda(l)=l(l+1), rate 2l(l+1), l=0..8")
    check("quadratic_dominates_hamming", dom_ok, "2l(l+1) > 2l for l>=1; equal at l=0")

    # 5. Gaunt selection rules: counts + two-route verification.
    tot, tri, allowed = gaunt_counts(3)
    check("gaunt_counts_L3", (tot, tri, allowed) == (64, 34, 23),
          f"total={tot} triangle={tri} triangle+parity={allowed} forbidden={tot-allowed}")
    # two-route check: rule vs exact Wigner 3j(0,0,0) zero-pattern, l <= 5
    ok3j = all((abs(wigner3j000(a, b, c)) > 1e-15) == gaunt_allowed(a, b, c)
               for a in range(6) for b in range(6) for c in range(6))
    check("gaunt_rule_matches_wigner3j", ok3j, "zero pattern identical for all l<=5")
    # three-route check: Simpson triple-Legendre integral, l <= 4
    okint = True
    for a in range(5):
        for b in range(5):
            for c in range(5):
                z = abs(triple_legendre_integral(a, b, c)) < 1e-6
                if z == gaunt_allowed(a, b, c):
                    okint = False
    check("gaunt_rule_matches_integral", okint,
          "vanishing pattern of int P_a P_b P_c identical for all l<=4")

    # 6. Fermi-Dirac / Binomial identity at linear Phi (0 new parameters).
    okfd = True
    worst = 0.0
    for eps, T in ((0.5, 0.05), (1.0, 0.3), (-0.2, 0.1), (0.05, 0.041143)):
        a = pi_T_linear_phi(eps, T)
        b = binomial_fd(eps, T)
        worst = max(worst, max(abs(x - y) for x, y in zip(a, b)))
        okfd &= all(abs(x - y) < 1e-12 for x, y in zip(a, b))
    check("fermi_dirac_binomial_identity", okfd,
          f"pi_T(k) == Binomial(9, 1/(1+e^(eps/T))) at linear Phi; worst |diff|={worst:.2e}")

    print("SELFTEST: " + ("ALL PASS" if ok_all else "FAILURES PRESENT"))
    return 0 if ok_all else 1


# --------------------------------------------------------------------- CLI

def main(argv):
    if "--selftest" in argv:
        return selftest()
    if "--dispersion" in argv:
        i = argv.index("--dispersion")
        m1, m2 = float(argv[i + 1]), float(argv[i + 2])
        print("q/pi   omega_acoustic   omega_optical   (C=1, cell period a=1)")
        for j in range(11):
            q = math.pi * j / 10
            a2, o2 = diatomic_omega2(q, m1, m2)
            print(f"{j/10:4.1f}   {math.sqrt(max(a2,0)):14.6f}   {math.sqrt(o2):13.6f}")
        print(f"zone-center optical: {math.sqrt(2*(1/m1+1/m2)):.6f}   "
              f"band gap: {diatomic_gap(m1, m2):.6f}   "
              f"Klemens allowed: {klemens_allowed(m1, m2)}")
        return 0
    if "--gaunt" in argv:
        L = int(argv[argv.index("--gaunt") + 1])
        tot, tri, allowed = gaunt_counts(L)
        print(f"L={L}: triads={tot} triangle={tri} triangle+parity(allowed)={allowed} "
              f"forbidden={tot-allowed} forbidden_frac={(tot-allowed)/tot:.4f}")
        return 0
    if "--fd" in argv:
        i = argv.index("--fd")
        eps, T = float(argv[i + 1]), float(argv[i + 2])
        a = pi_T_linear_phi(eps, T)
        b = binomial_fd(eps, T)
        p = 1.0 / (1.0 + math.exp(eps / T))
        print(f"linear Phi(k)={eps}*k at T={T}: FD occupancy p = {p:.6f}")
        print(" k   pi_T(k)        Binomial(9,p)  |diff|")
        for k in range(D_PRIMITIVES + 1):
            print(f"{k:2d}   {a[k]:.10f}   {b[k]:.10f}  {abs(a[k]-b[k]):.2e}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
