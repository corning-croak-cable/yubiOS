/-
  CurvedCorpus.lean
  Machine-checked invariants for the curved-corpus program.
  Companion to: "The Curved-Corpus Program, Unified" (Tchatalbachian, 2026-08-13).

  Core Lean 4 only: no mathlib, no external dependencies.
  Every `theorem` below is closed (no `sorry`).

  Contents (matching Section 6 of the paper):
    1. atom_delta_nonneg      -- Lemma 1: geodesic-only atom has Δ ≥ 0
    2. corpus_sum_nonneg      -- Theorem 1: linear composition preserves Δ ≥ 0
    3. cumulative_monotone    -- Corollary 1: running total is monotone
    4. gate_rank_identity     -- the V₂ gate is a rank test (0.40 threshold as 2/5)
    5. phi_ladder_telescope   -- fold-ladder potential drops telescope
    6. heat_exponent_monotone / heat_exponent_additive -- ℓ(ℓ+1) heat-kernel exponent facts
    7. mh_flux_symm           -- Metropolis flux min-symmetry (detailed balance kernel)

  Scope — what this file does NOT prove. The theorems below are
  identity-type statements over exact arithmetic (integers, fraction
  pairs). Machine-checking them certifies that the program's identities
  carry no empirical content — nothing more. In particular this file does
  not prove:
    • that the selected null ensemble (fixed-margin / curveball) is
      scientifically adequate for the corpus questions asked of it;
    • that any Monte Carlo calibration (null tables, mixing, power
      sweeps) has converged sufficiently;
    • that any numerical spherical heat-kernel implementation is
      error-free (G1's simulations are measurements, not theorems);
    • that floating-point execution of the shipped Python matches the
      real-number model formalized here;
    • or that any observed corpus-specific effect (e.g. ΔV₂ = +0.0144,
      z = +12.3) is genuine rather than an artifact.
  Those claims live on the measurement side of the identity/measurement
  boundary and are supported only by reproduction scripts and matched
  nulls, per the papers' own discipline.
-/

namespace CurvedCorpus

/-! ### 0. A hand-rolled integer min (no library dependence) -/

def imin (a b : Int) : Int := if a ≤ b then a else b

theorem imin_comm (a b : Int) : imin a b = imin b a := by
  unfold imin
  split <;> split <;> omega

theorem imin_le_left (a b : Int) : imin a b ≤ a := by
  unfold imin
  split <;> omega

theorem imin_le_right (a b : Int) : imin a b ≤ b := by
  unfold imin
  split <;> omega

/-! ### 1. The single-action atom (Lemma 1)

The atom evaluates a pre-action distance `dpre` and a finite nonempty list
of candidate post-action distances. The geodesic-only criterion selects the
minimum. We model "the atom only fires when some candidate does not increase
the distance" as the hypothesis `h : listMin dpre cands ≤ dpre` — which the
selection rule guarantees whenever the identity flip (distance `dpre` itself)
is among the candidates, and which the deployed atom enforces by construction
(it skips files where every flip increases distance).

Δ := dpre − (selected post distance) ≥ 0. -/

def listMin (d : Int) (cands : List Int) : Int :=
  cands.foldl imin d

theorem listMin_le_init (d : Int) (cands : List Int) :
    listMin d cands ≤ d := by
  unfold listMin
  induction cands generalizing d with
  | nil => exact Int.le_refl d
  | cons c cs ih =>
      have h1 : List.foldl imin (imin d c) cs ≤ imin d c := ih (imin d c)
      have h2 : imin d c ≤ d := imin_le_left d c
      exact Int.le_trans h1 h2

/-- Lemma 1 (atom invariant): when the atom selects the minimizing flip and
    the identity option is available, Δ = dpre − dpost ≥ 0. -/
theorem atom_delta_nonneg (dpre : Int) (cands : List Int) :
    0 ≤ dpre - listMin dpre cands := by
  have h := listMin_le_init dpre cands
  omega

/-! ### 2. Linear composition (Theorem 1) -/

def sumList : List Int → Int
  | [] => 0
  | x :: xs => x + sumList xs

/-- Theorem 1 (linear composition): if every atomic Δ ≥ 0 then the corpus
    total Δ ≥ 0. -/
theorem corpus_sum_nonneg (deltas : List Int)
    (h : ∀ d ∈ deltas, 0 ≤ d) : 0 ≤ sumList deltas := by
  induction deltas with
  | nil => exact Int.le_refl 0
  | cons d ds ih =>
      have hd : 0 ≤ d := h d ((by simp : d ∈ d :: ds))
      have hds : 0 ≤ sumList ds := ih (fun x hx => h x (List.mem_cons_of_mem d hx))
      show 0 ≤ d + sumList ds
      omega

/-! ### 3. Cumulative monotonicity (Corollary 1)

The running total over cycles is the prefix sum of per-cycle Δ's. -/

def prefixSum (deltas : List Int) : Nat → Int
  | 0 => 0
  | n + 1 =>
      match deltas with
      | [] => 0
      | d :: ds => d + prefixSum ds n

/-- Corollary 1 (cumulative monotonicity): with all per-cycle Δ ≥ 0,
    each prefix sum is ≤ the next. -/
theorem cumulative_monotone (deltas : List Int)
    (h : ∀ d ∈ deltas, 0 ≤ d) (n : Nat) :
    prefixSum deltas n ≤ prefixSum deltas (n + 1) := by
  induction n generalizing deltas with
  | zero =>
      cases deltas with
      | nil => simp [prefixSum]
      | cons d ds =>
          have hd : 0 ≤ d := h d ((by simp : d ∈ d :: ds))
          simp [prefixSum]
          omega
  | succ m ih =>
      cases deltas with
      | nil => simp [prefixSum]
      | cons d ds =>
          have hds : ∀ x ∈ ds, 0 ≤ x := fun x hx => h x (List.mem_cons_of_mem d hx)
          have := ih ds hds
          simp [prefixSum]
          omega

/-! ### 4. The gate is a rank test (C2)

V₂ = (λ₁+λ₂)/Σλ ≥ 0.40 with the threshold 0.40 = 2/5, and the shipped
estimator r̂ = 2/V₂ ≤ 5. With V₂ = p/q (p, q > 0), the gate is the fraction
comparison p/q ≥ 2/5 and the rank test is 2q/p ≤ 5. Fraction comparison
a/b ≥ c/d over positive denominators is encoded by cross-multiplication
(fracGe). The equivalence gate ↔ rank is an identity, but the two sides
cross-multiply over *different* denominators (q for the gate, p for the
rank proxy), so each direction genuinely consumes one positivity
hypothesis — that is the entire mathematical content: division by a
positive number preserves order. No empirical fact enters. -/

/-- a/b ≥ c/d over positive denominators, encoded by cross-multiplication. -/
def fracGe (a b c d : Int) : Prop := 0 < b ∧ 0 < d ∧ a * d ≥ c * b

/-- C2 (gate rank identity): with V₂ = p/q (p, q > 0),
    V₂ ≥ 2/5  ↔  r̂ = 2q/p ≤ 5 (stated as 5/1 ≥ 2q/p).
    Forward uses 0 < p, backward uses 0 < q. -/
theorem gate_rank_identity (p q : Int) (hp : 0 < p) (hq : 0 < q) :
    fracGe p q 2 5 ↔ fracGe 5 1 (2 * q) p := by
  constructor
  · intro h
    have h3 := h.2.2
    exact ⟨by omega, hp, by omega⟩
  · intro h
    have h3 := h.2.2
    exact ⟨hq, by omega, by omega⟩

/-! ### 5. The fold ladder telescopes (Section 4 of the 2026-08-12 paper)

Φ is the ladder potential after n folds; per-fold drops sum to the total
drop. Modeled with Φ : Nat → Int and drop k := Φ k − Φ (k+1). -/

def drops (Φ : Nat → Int) : Nat → Int
  | 0 => 0
  | n + 1 => drops Φ n + (Φ n - Φ (n + 1))

/-- The per-fold drops telescope: the sum of the first n drops equals
    Φ 0 − Φ n. Identity, not measurement. -/
theorem phi_ladder_telescope (Φ : Nat → Int) (n : Nat) :
    drops Φ n = Φ 0 - Φ n := by
  induction n with
  | zero => simp [drops]
  | succ m ih =>
      simp [drops, ih]
      omega

/-! ### 6. Heat-kernel exponent facts (Section 5, spherical defocus)

The forward defocus multiplies degree-ℓ energy by exp(−2ℓ(ℓ+1)t). The
exponent e(ℓ) = ℓ(ℓ+1) is strictly ordered in ℓ and additive over
concatenated diffusion times — the two facts G1's Leg-1 check rests on. -/

def heatExp (l : Nat) : Nat := l * (l + 1)

/-- Higher degrees defocus strictly faster: ℓ < ℓ' → e(ℓ) < e(ℓ'). -/
theorem heat_exponent_monotone (l l' : Nat) (h : l < l') :
    heatExp l < heatExp l' := by
  unfold heatExp
  have h1 : l + 1 ≤ l' := h
  have e1 : (l + 1) * (l + 1) = l * (l + 1) + (l + 1) := Nat.succ_mul l (l + 1)
  have e2 : (l + 1) * (l + 1) ≤ l' * (l' + 1) := Nat.mul_le_mul h1 (by omega)
  omega

/-- Semigroup additivity in the exponent: running time s then t multiplies
    energies by exp(−2e(ℓ)s)·exp(−2e(ℓ)t) = exp(−2e(ℓ)(s+t)); at the level
    of the integer-scaled exponent this is distributivity. -/
theorem heat_exponent_additive (l s t : Nat) :
    heatExp l * (s + t) = heatExp l * s + heatExp l * t := by
  exact Nat.mul_add (heatExp l) s t

/-! ### 7. Metropolis flux symmetry (curve-compass ± atom)

The compass atom's stationarity argument needs the detailed-balance kernel:
the flux between states a and b is proportional to min(w a, w b), which is
symmetric. With integer-scaled weights this is min-commutativity. -/

/-- Detailed-balance flux symmetry: min(wa, wb) = min(wb, wa). -/
theorem mh_flux_symm (wa wb : Int) : imin wa wb = imin wb wa :=
  imin_comm wa wb

end CurvedCorpus
