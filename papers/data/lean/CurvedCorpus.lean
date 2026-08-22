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
    8. trade_preserves_rowSum / trade_preserves_colSum -- curveball trades stay on the fixed-margin fibre
    9. trade_reversible / uniform_inflow_constant -- F3 null canonicity mechanics (reversibility, uniform stationarity)

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

  Resolution status: the identity-type core of the first item -- the
  curveball move set never leaves the fixed-margin fibre -- is proved in
  section 8 below. Every remaining measurement-side item is executed as a
  seeded PASS/FAIL check by verify_claims.py in this directory, which the
  same CI workflow runs beside this file: sampler uniformity on an
  exhaustively enumerated fibre (1), mixing convergence (2), the spherical
  heat-kernel semigroup identity (3), float-vs-exact-model checks of the
  theorems in this file (4), and reproduction of the corpus effect against
  its curveball null (5), and F3 null canonicity -- exhaustive fibre-graph
  irreducibility plus the constant-margin medium matched against
  destroyed-dependence baselines (6), completing sections 8-9.
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

/-! ### 8. Curveball trades stay on the fixed-margin fibre

Resolution boundary for the scope block above. The elementary move of the
curveball null sampler is a 2x2 checkerboard trade: rows i /= j and columns
a /= b, with the submatrix [[1,0],[0,1]] replaced by [[0,1],[1,0]] (or vice
versa; both directions are instances of the delta below). The claim that
the null ensemble is adequate splits into mechanics and statistics. The
mechanics -- the move set never leaves the fixed-margin fibre -- is
identity-type and proved here: a trade preserves every row sum and every
column sum. The statistics -- uniformity on the fibre, mixing, and every
other measurement-side item in the scope block -- are executed as seeded
PASS/FAIL checks by verify_claims.py beside this file, run by the same CI
workflow as this proof.

A matrix is Nat -> Nat -> Int; sums run over explicit index lists via
sumOver; countN counts occurrences. The preservation theorems hold for any
enumeration in which the two traded columns (resp. rows) occur equally
often -- in particular any duplicate-free enumeration containing both. -/

def countN (a : Nat) : List Nat → Int
  | [] => 0
  | x :: xs => (if x = a then 1 else 0) + countN a xs

def sumOver (f : Nat → Int) : List Nat → Int
  | [] => 0
  | x :: xs => f x + sumOver f xs

/-- The plus-minus-1 delta a trade applies at corners (i,a), (i,b), (j,a), (j,b). -/
def tradeDelta (i j a b r c : Nat) : Int :=
  (if r = i ∧ c = a then -1 else 0) + (if r = i ∧ c = b then 1 else 0)
    + (if r = j ∧ c = a then 1 else 0) + (if r = j ∧ c = b then -1 else 0)

/-- The traded matrix. -/
def trade (M : Nat → Nat → Int) (i j a b r c : Nat) : Int :=
  M r c + tradeDelta i j a b r c

theorem tradeDelta_row_other (i j a b r c : Nat) (h1 : r ≠ i) (h2 : r ≠ j) :
    tradeDelta i j a b r c = 0 := by
  have n1 : ¬(r = i ∧ c = a) := fun h => h1 h.1
  have n2 : ¬(r = i ∧ c = b) := fun h => h1 h.1
  have n3 : ¬(r = j ∧ c = a) := fun h => h2 h.1
  have n4 : ¬(r = j ∧ c = b) := fun h => h2 h.1
  simp [tradeDelta, n1, n2, n3, n4]

theorem tradeDelta_row_i (i j a b c : Nat) (hij : i ≠ j) :
    tradeDelta i j a b i c
      = (if c = a then (-1 : Int) else 0) + (if c = b then (1 : Int) else 0) := by
  have n3 : ¬(i = j ∧ c = a) := fun h => hij h.1
  have n4 : ¬(i = j ∧ c = b) := fun h => hij h.1
  simp [tradeDelta, n3, n4]

theorem tradeDelta_row_j (i j a b c : Nat) (hij : i ≠ j) :
    tradeDelta i j a b j c
      = (if c = a then (1 : Int) else 0) + (if c = b then (-1 : Int) else 0) := by
  have n1 : ¬(j = i ∧ c = a) := fun h => hij h.1.symm
  have n2 : ¬(j = i ∧ c = b) := fun h => hij h.1.symm
  simp [tradeDelta, n1, n2]

theorem trade_rowSum_other (M : Nat → Nat → Int) (i j a b r : Nat)
    (cols : List Nat) (h1 : r ≠ i) (h2 : r ≠ j) :
    sumOver (fun c => trade M i j a b r c) cols
      = sumOver (fun c => M r c) cols := by
  induction cols with
  | nil => rfl
  | cons x xs ih =>
      simp only [sumOver]
      rw [show trade M i j a b r x = M r x by
            unfold trade; rw [tradeDelta_row_other i j a b r x h1 h2]; omega]
      omega

theorem trade_rowSum_i (M : Nat → Nat → Int) (i j a b : Nat)
    (cols : List Nat) (hij : i ≠ j) :
    sumOver (fun c => trade M i j a b i c) cols
      = sumOver (fun c => M i c) cols + countN b cols - countN a cols := by
  induction cols with
  | nil => simp [sumOver, countN]
  | cons x xs ih =>
      simp only [sumOver, countN]
      rw [show trade M i j a b i x
            = M i x + ((if x = a then (-1 : Int) else 0)
                + (if x = b then (1 : Int) else 0)) by
            unfold trade; rw [tradeDelta_row_i i j a b x hij]]
      by_cases hxa : x = a <;> by_cases hxb : x = b <;> simp_all <;> omega

theorem trade_rowSum_j (M : Nat → Nat → Int) (i j a b : Nat)
    (cols : List Nat) (hij : i ≠ j) :
    sumOver (fun c => trade M i j a b j c) cols
      = sumOver (fun c => M j c) cols + countN a cols - countN b cols := by
  induction cols with
  | nil => simp [sumOver, countN]
  | cons x xs ih =>
      simp only [sumOver, countN]
      rw [show trade M i j a b j x
            = M j x + ((if x = a then (1 : Int) else 0)
                + (if x = b then (-1 : Int) else 0)) by
            unfold trade; rw [tradeDelta_row_j i j a b x hij]]
      by_cases hxa : x = a <;> by_cases hxb : x = b <;> simp_all <;> omega

theorem tradeDelta_col_other (i j a b r c : Nat) (h1 : c ≠ a) (h2 : c ≠ b) :
    tradeDelta i j a b r c = 0 := by
  have n1 : ¬(r = i ∧ c = a) := fun h => h1 h.2
  have n2 : ¬(r = i ∧ c = b) := fun h => h2 h.2
  have n3 : ¬(r = j ∧ c = a) := fun h => h1 h.2
  have n4 : ¬(r = j ∧ c = b) := fun h => h2 h.2
  simp [tradeDelta, n1, n2, n3, n4]

theorem tradeDelta_col_a (i j a b r : Nat) (hab : a ≠ b) :
    tradeDelta i j a b r a
      = (if r = i then (-1 : Int) else 0) + (if r = j then (1 : Int) else 0) := by
  have n2 : ¬(r = i ∧ a = b) := fun h => hab h.2
  have n4 : ¬(r = j ∧ a = b) := fun h => hab h.2
  simp [tradeDelta, n2, n4]

theorem tradeDelta_col_b (i j a b r : Nat) (hab : a ≠ b) :
    tradeDelta i j a b r b
      = (if r = i then (1 : Int) else 0) + (if r = j then (-1 : Int) else 0) := by
  have n1 : ¬(r = i ∧ b = a) := fun h => hab h.2.symm
  have n3 : ¬(r = j ∧ b = a) := fun h => hab h.2.symm
  simp [tradeDelta, n1, n3]

theorem trade_colSum_other (M : Nat → Nat → Int) (i j a b c : Nat)
    (rows : List Nat) (h1 : c ≠ a) (h2 : c ≠ b) :
    sumOver (fun r => trade M i j a b r c) rows
      = sumOver (fun r => M r c) rows := by
  induction rows with
  | nil => rfl
  | cons x xs ih =>
      simp only [sumOver]
      rw [show trade M i j a b x c = M x c by
            unfold trade; rw [tradeDelta_col_other i j a b x c h1 h2]; omega]
      omega

theorem trade_colSum_a (M : Nat → Nat → Int) (i j a b : Nat)
    (rows : List Nat) (hab : a ≠ b) :
    sumOver (fun r => trade M i j a b r a) rows
      = sumOver (fun r => M r a) rows + countN j rows - countN i rows := by
  induction rows with
  | nil => simp [sumOver, countN]
  | cons x xs ih =>
      simp only [sumOver, countN]
      rw [show trade M i j a b x a
            = M x a + ((if x = i then (-1 : Int) else 0)
                + (if x = j then (1 : Int) else 0)) by
            unfold trade; rw [tradeDelta_col_a i j a b x hab]]
      by_cases hxi : x = i <;> by_cases hxj : x = j <;> simp_all <;> omega

theorem trade_colSum_b (M : Nat → Nat → Int) (i j a b : Nat)
    (rows : List Nat) (hab : a ≠ b) :
    sumOver (fun r => trade M i j a b r b) rows
      = sumOver (fun r => M r b) rows + countN i rows - countN j rows := by
  induction rows with
  | nil => simp [sumOver, countN]
  | cons x xs ih =>
      simp only [sumOver, countN]
      rw [show trade M i j a b x b
            = M x b + ((if x = i then (1 : Int) else 0)
                + (if x = j then (-1 : Int) else 0)) by
            unfold trade; rw [tradeDelta_col_b i j a b x hab]]
      by_cases hxi : x = i <;> by_cases hxj : x = j <;> simp_all <;> omega

/-- A trade preserves every row sum, over any column enumeration counting
    the two traded columns equally often (any duplicate-free enumeration). -/
theorem trade_preserves_rowSum (M : Nat → Nat → Int) (i j a b r : Nat)
    (cols : List Nat) (hij : i ≠ j)
    (hbal : countN a cols = countN b cols) :
    sumOver (fun c => trade M i j a b r c) cols
      = sumOver (fun c => M r c) cols := by
  by_cases hri : r = i
  · have h := trade_rowSum_i M i j a b cols hij
    rw [hri]
    omega
  · by_cases hrj : r = j
    · have h := trade_rowSum_j M i j a b cols hij
      rw [hrj]
      omega
    · exact trade_rowSum_other M i j a b r cols hri hrj

/-- A trade preserves every column sum, over any row enumeration counting
    the two traded rows equally often (any duplicate-free enumeration). -/
theorem trade_preserves_colSum (M : Nat → Nat → Int) (i j a b c : Nat)
    (rows : List Nat) (hab : a ≠ b)
    (hbal : countN i rows = countN j rows) :
    sumOver (fun r => trade M i j a b r c) rows
      = sumOver (fun r => M r c) rows := by
  by_cases hca : c = a
  · have h := trade_colSum_a M i j a b rows hab
    rw [hca]
    omega
  · by_cases hcb : c = b
    · have h := trade_colSum_b M i j a b rows hab
      rw [hcb]
      omega
    · exact trade_colSum_other M i j a b c rows hca hcb

/-! ### 9. The F3 null is canonical: reversibility and uniform stationarity

README section F3 reads null standardization as deflection against an
unlensed background, with the fixed-margin ensemble as the medium. The
canonicity of that medium decomposes:
  (i)   the sampler's moves stay on the fixed-margin fibre (section 8);
  (ii)  every trade is reversible -- the column-swapped trade undoes it
        exactly -- so a uniform proposal has a symmetric kernel (here);
  (iii) a symmetric kernel makes the uniform distribution stationary:
        inflow to every state equals its constant outflow (here);
  (iv)  irreducibility of the trade graph on the fibre, and the
        constant-margin spectrum anchor (Lyu-Mukherjee / MP), are
        executed exhaustively by verify_claims.py claim 6.
With (i)-(iv) the unique stationary law of the curveball chain is uniform
on the fibre -- the maximum-entropy distribution given the margins, which
is what F3 requires of its vacuum. Outside machine reach and cited, not
proved: uniqueness-from-irreducibility in general (finite Markov chain
theory; checked exhaustively on the test instance) and the asymptotic
Lyu-Mukherjee spectrum theorem. -/

theorem sumOver_congr (f g : Nat → Int) (l : List Nat) (h : ∀ x, f x = g x) :
    sumOver f l = sumOver g l := by
  induction l with
  | nil => rfl
  | cons x xs ih => simp [sumOver, h x, ih]

/-- (ii) Every trade is undone exactly by the trade with columns swapped:
    the move set is reversible, so the uniform proposal kernel is
    symmetric. Pointwise identity, no hypotheses needed. -/
theorem trade_reversible (M : Nat → Nat → Int) (i j a b r c : Nat) :
    trade (trade M i j a b) i j b a r c = M r c := by
  unfold trade tradeDelta
  by_cases h1 : r = i <;> by_cases h2 : r = j <;>
    by_cases h3 : c = a <;> by_cases h4 : c = b <;>
      simp_all <;> omega

/-- (iii) Balance: for a symmetric kernel, total inflow to any state b
    equals total outflow from b, along any state enumeration. -/
theorem symm_kernel_balance (K : Nat → Nat → Int) (S : List Nat)
    (hsym : ∀ x y, K x y = K y x) (b : Nat) :
    sumOver (fun a => K a b) S = sumOver (fun a => K b a) S :=
  sumOver_congr _ _ S (fun a => hsym a b)

/-- (iii) Uniform stationarity: if a symmetric kernel has constant row
    sums R over the enumeration S, then the inflow to every state is
    that same R -- constant weights reproduce themselves, i.e. the
    uniform distribution is stationary for the chain. -/
theorem uniform_inflow_constant (K : Nat → Nat → Int) (S : List Nat) (R : Int)
    (hsym : ∀ x y, K x y = K y x)
    (hrow : ∀ a, sumOver (fun c => K a c) S = R) (b : Nat) :
    sumOver (fun a => K a b) S = R := by
  have h := symm_kernel_balance K S hsym b
  rw [h]
  exact hrow b

end CurvedCorpus
