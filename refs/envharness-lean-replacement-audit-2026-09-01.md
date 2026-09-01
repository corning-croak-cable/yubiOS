# Can CurvedCorpus.lean take the place of envharness's inner workings? — audit, 2026-09-01

**Subject:** [google-research/envharness](https://github.com/google-research/envharness)
(arXiv:2608.19880), link #1 of the 22-link synthesis
([`refs/twenty-two-links-synthesis-and-photophysics-bridge-2026-08-25.md`](twenty-two-links-synthesis-and-photophysics-bridge-2026-08-25.md)).
Audited from source at HEAD (pushed 2026-08-21): `core/envharness.py`,
`core/actionable_env.py`, `harnesses/rules.py`, `harnesses/setup.py`,
`orchestration/objectives.py`, `orchestration/budget.py`, `core/code_loader.py`,
bridges and infra by tree inspection.

**Companion:** `CurvedCorpus.lean` §15 (harness algebra, shipped with this audit).

**Answer in one line:** the Lean proofs can take the place of envharness's
**contract layer** (the wrapper algebra and its safety invariants — now proved
in §15) and its **acceptance-statistics layer** (raw window means → curveball
null + dBc, already proved as §§8–12 and executed by `verify_claims.py`); they
cannot and should not take the place of the **execution layer** (environment
bridges, LLM calls, checkpoint IO, compiling model-written hook code).

---

## 1. What envharness's inner workings actually are

Three load-bearing pieces:

1. **A wrapper algebra.** `EnvHarness` IS-A `ActionableEnv` wrapping an inner
   `ActionableEnv`, default methods delegate inward, so harnesses stack
   arbitrarily (`Setup(Rules(Toy24Env()))`). Checkpointing walks the stack and
   saves each layer's own state.
2. **A mutation loop.** `HarnessAgent` (an LLM) emits Python source for a
   `_Rules(Rules)` subclass overriding up to three pure hooks —
   `filter_action` (A), `modify_transition` (T), `filter_observation` (O);
   `Setup` replays an action list as the S0 mechanism; `code_loader` compiles
   the emitted source; a `BudgetPolicy` decides when the search stops; a
   `MutationObjective` (DifficultyZone / RedTeam) scores recent traces and
   steers the next mutation.
3. **An implicit trust story.** "Harnesses stack arbitrarily", "a Blocked
   action leaves the env unchanged", "the loop terminates", "weights are
   normalized", "success rate in the target band" — all stated in docstrings
   or true-by-construction of one code path, none machine-checked.

## 2. Component-by-component verdicts

| envharness component | What it relies on | Lean-replaceable? | Where |
|---|---|---|---|
| `core/envharness.py` composition (stacking, delegation, identity defaults) | wrapper algebra: identity neutral, composition associative, Block short-circuits | **YES — proved** | §15 `hcomp_id_left/right_A/O`, `hcomp_assoc_A/O` |
| `harnesses/rules.py` Blocked branch ("a blocked action leaves the env unchanged", reward 0, not terminated) | a safety invariant true of one hand-written code path | **YES — proved as a theorem over every env transition** | §15 `blocked_is_noop`, `passthrough_step` |
| `orchestration/budget.py` (FixedBudget / CappedAdaptive / ObjectiveDriven) | loop termination at cap; ACCEPT halts | **YES — proved** | §15 `fixed_halts`, `capped_halts`, `capped_accept_halts`, `obj_halts` |
| `orchestration/objectives.py` DifficultyZone band test | band membership arithmetic under a float score formula | **YES (exact form) — proved**; the float `max(0, 1−\|sr−c\|/h)` stays measurement-side | §15 `dz_band_iff` |
| `orchestration/objectives.py` `_weights_from_failure_axes` | `round(v/s, 3)` weights implicitly assumed normalized | **YES — and the formalization finds a gap**: fixed-precision weights need not sum to unity (kernel-checked instance: counts (0,0,0,0,1) → per-mille floors sum to 999) | §15 `weights_round_gap`, `weights_exact_sum` |
| **Acceptance statistics** (DifficultyZone/RedTeam scores = raw success-rate window means; ACCEPT decisions ride on them) | between-arm comparison with **no matched null** — the 22-link finding, now confirmed in source | **YES — superseded outright**: curveball fixed-margin null (§8), reversibility + uniform stationarity (§9), uniqueness (§10), MP/Narayana target (§11), dBc level laws (§12), executed per-push by `verify_claims.py` CLAIMs 1–8 | already shipped |
| `harnesses/setup.py` S0 replay | replay determinism of the inner env | **PARTIAL**: the replay algebra (prefix composition) is provable; determinism of real envs (webarena, swebench) is an empirical property — measurement-side | not modeled; candidate §15 extension |
| `persistence/checkpoint.py` round-trip | `from_state(save_state) = id` per layer | **PARTIAL**: statable per-layer as an algebra law; the Rules layer's round-trip includes recompiling source — see next row | not modeled |
| `core/code_loader.py` (exec of LLM-written Python) | trust in model-emitted code | **NO — and should not be**: this is a supply-chain surface, not a theorem. The program's posture is to gate it (policy + sandbox, the yubiOS.rego pattern), never to prove it safe | out of scope by design |
| `bridges/*`, `infra/llm.py`, `agents/*`, orchestration runtime | real environments, subprocesses, model calls | **NO — execution-side** | out of scope by design |

## 3. The three-tier summary

- **Tier 1 — contracts (replaceable, now replaced):** every algebraic law the
  README and docstrings assert is now a kernel-checked theorem in §15. If
  envharness wanted its "harnesses stack arbitrarily" claim to be more than
  prose, this file is what that looks like.
- **Tier 2 — acceptance statistics (replaceable, strictly upgraded):** the
  inner loop's ACCEPT/REJECT rides on raw window means with no matched null.
  Swapping `ObjectiveSignal.score` for a curveball-deflection (dV2z / dBc)
  gives the loop a falsifier-bearing gate whose null is itself proved
  canonical (§§8–10). This is the highest-value replacement and requires no
  change to their execution machinery: traces → binary incidence
  (episode × skill/failure-axis) is exactly the corpus type the auditor
  ingests.
- **Tier 3 — execution (not replaceable):** Lean does not run webarena. The
  boundary is the same one the program already enforces between
  `CurvedCorpus.lean` and `verify_claims.py`: proofs on one side, seeded
  executable measurements on the other.

## 4. Findings of independent value

1. **The rounding-normalization gap** (§15 `weights_round_gap`): envharness's
   failure-axis weights are emitted at 3-decimal precision and need not sum
   to 1. Downstream consumers treating them as a distribution inherit a
   silent ≤ n·0.0005 leak. Exact-arithmetic weights (numerators over the
   common denominator) are exactly normalized; any fixed-precision emission
   needs a remainder-distribution rule.
2. **The Blocked contract generalizes.** rules.py guarantees the no-op by
   constructing one code path; the theorem holds for every transition
   function, which is the difference between "our code does this" and "any
   stack built from these pieces does this".
3. **The statistics finding of 2026-08-25 is now code-confirmed**: both
   built-in objectives are raw means over a trailing window (`sum(...) /
   len(recent)`); no randomization, no margin preservation, no deflection
   floor anywhere in the repo.

## 5. Open follow-ups

1. Model the Setup replay + checkpoint round-trip laws (per-layer
   `from_state ∘ save_state = id`) as a §15 extension — pure algebra, cheap.
2. Prototype the Tier-2 swap: an envharness `MutationObjective` whose score is
   a curveball dV2z on the episode × failure-axis incidence matrix, gated at
   the +15.6 dBc floor (a `corpus-auditor` adapter, ~50 lines).
3. Propose the weights fix upstream (largest-remainder allocation) with the
   §15 instance as the repro.
