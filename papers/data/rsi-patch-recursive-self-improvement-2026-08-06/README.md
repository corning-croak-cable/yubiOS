# RSI Patch — `recursive-self-improvement`

**Cycle ID**: `single-action-rsi-recursive-self-improvement-2026-08-06`
**Basis**: `single-action-curve-rsi` deep-research 9-primitive basis
**Cycle outcome**: succeeded (with degenerate-tie caveat)
**PR1 residual (input)**: 1.4444
**Predicted post-edit residual**: ~1.238 (≈14.3% reduction)

---

## Files in this patch

| File | Purpose | Size |
|---|---|---|
| [cycle.json](file://./cycle.json) | Full cycle record (coverage matrix, S² point, candidates, Δ, predicted residual) | ~10 KB |
| [proposed-edit.md](file://./proposed-edit.md) | Concrete edit to apply to `SKILL.md` — adds `## Verification plan` section with 6 VP commands | ~5 KB |
| [patch-report.md](file://./patch-report.md) | Human-readable report: PR1 context, basis mismatch, computed values, red flags, next-cycle recommendation | ~8 KB |
| [README.md](file://./README.md) | This file — top-level summary | ~2 KB |

---

## TL;DR

PR #186's curve fit flagged `recursive-self-improvement` as the TOP-1 highest-residual skill (1.4444) in the 79-skill corpus. This skill is the META-SKILL (it describes the RSI loop itself), so fixing it has compounding value across every cycle.

This cycle computed:

- **File-level coverage**: 2/9 primitives covered (`has_evidence`, `has_constraint`); 7/9 missing.
- **d_pre** (chordal to ideal pole on S²): **0.658**.
- **Single-action target**: `p5_has_test` (≈ PR1's `trust_chain` — the primitive that BOTH bases agree is missing).
- **Δ** (geodesic improvement): **+0.658** (degenerate tie across all 7 candidates due to S² lift homogenization collapse; principled choice via basis mapping).
- **Predicted post-edit residual**: **~1.238** (14.3% reduction from PR1 input of 1.4444).

The proposed edit adds a `## Verification plan` section with 6 falsifiable bash commands (VP-1 through VP-6) that operationalize the existing `## Verification` compliance checklist.

---

## Next steps

1. **Apply the edit** in `proposed-edit.md` to the SKILL.md (do NOT do this from this subagent — the orchestrator handles git operations).
2. **Re-run the cycle** post-edit to measure the realized Δ.
3. **Pick the next single-action target** from the post-edit candidates (likely `p8_has_priority` — low-cost P0/P1/P2 label additions).
4. **Hard-stop after 3 cycles** per the skill's own §Red Flags ("Running more than three cycles without escalating").

---

## Notes for the orchestrator

- This subagent **does not** push to git or create a PR.
- This subagent **does not** modify the actual SKILL.md file (only proposes the edit).
- Files were written only to `/var/workspace/documents/github-yubios-KS9n5GAT/subagents/rsi-patch-recursive-self-improvement/`.
- The `single-action-curve-rsi` SKILL.md was read first, as required.
- The basis mismatch between PR1 (`internal-big-picture` corpus variant) and this cycle (`single-action-curve-rsi` deep-research variant) is documented in `cycle.json` → `basis_mapping_to_pr1` and in `patch-report.md` → §Basis mismatch.
