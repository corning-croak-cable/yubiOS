# Proposed Edit — `recursive-self-improvement/SKILL.md`

**Single-action target**: `p5_has_test` (≈ PR1's `trust_chain` primitive)
**Geodesic-only criterion**: All 7 missing primitives tie at d_post = 0.0 (degenerate homogenization collapse in the S² lift when any missing primitive is forced to 1 in every section). Per the user's stated PR1 basis mapping (`trust_chain ≈ has_test`), the principled target is `p5_has_test` — it is the one primitive that BOTH bases agree is missing.
**Cost**: medium (~30 lines added; aligns with the file's existing `## Verification` checklist section).

---

## Concrete edit — add a `## Verification plan` section

The file already has a top-level `## Verification` section (a bulleted checklist of compliance items). It is missing the **operational verification plan** — the falsifiable bash commands a reader can run to confirm the skill's own promises actually hold. This is the canonical `has_test` primitive.

**Insertion point**: after the existing `## Verification` section (before `## Changelog`).

**Markdown body to append**:

```markdown
## Verification plan

This plan is the falsifiable form of the `## Verification` checklist above. Each
item is a single bash / `js-yaml` command a reader can run on the current SKILL.md
to confirm the skill's compliance claims hold. A cycle is "fixpoint-reached" only
when all 6 commands exit 0.

- [ ] **VP-1 — frontmatter parses.** `python3 -c "import yaml,sys;d=yaml.safe_load(open('SKILL.md').read().split('---')[1]);assert d['name']=='recursive-self-improvement' and len(d['description'])<=1024 and '<' not in d['description'] and '>' not in d['description'];print('VP-1 PASS')"` → exits 0.
- [ ] **VP-2 — closing `---` intact.** `python3 -c "import sys;parts=open('SKILL.md').read().split('---');assert len(parts)>=3 and parts[0].strip()=='' and parts[-1].strip()=='';print('VP-2 PASS')"` → exits 0.
- [ ] **VP-3 — cycle count ≤ cap.** `python3 -c "import re;body=open('SKILL.md').read();n=len(re.findall(r'cycle\s+\d+', body));assert n<=5;print(f'VP-3 PASS (cycles={n})')"` → exits 0; flag if cycles > 5 (cap exceeded).
- [ ] **VP-4 — every cycle has a hypothesis, edit, result triple.** `python3 -c "import re;body=open('SKILL.md').read();c=re.findall(r'Hypothesis\s+\"([^\"]+)\"', body);e=re.findall(r'Edit:\s+(.+)', body);r=re.findall(r'Result:\s+(.+)', body);assert len(c)==len(e)==len(r) and len(c)>0;print(f'VP-4 PASS (hypotheses={len(c)})')"` → exits 0.
- [ ] **VP-5 — self-mode subagent-mandatory rule is textually present.** `python3 -c "body=open('SKILL.md').read();assert 'fresh-context subagent' in body and 'every cycle' in body.lower();print('VP-5 PASS')"` → exits 0; flag if either phrase absent.
- [ ] **VP-6 — Changelog is monotonically append-only.** `python3 -c "import re;body=open('SKILL.md').read();entries=re.findall(r'- \d{4}-\d{2}-\d{2}', body);assert entries==sorted(entries);print(f'VP-6 PASS (entries={len(entries)})')"` → exits 0; flag if any date is out of order.

A reviewer running this on `main` should see 6 PASS lines. Any FAIL signals a
gap the next cycle should close before declaring fixpoint. The plan is intentionally
greppable: each line is `VP-N` so a `grep -E 'VP-[0-9]+ (PASS|FAIL)' SKILL.md`
produces a single audit row per command.

## Test evidence (canonical)

For the v1 through current cycle on this skill, the canonical test pattern is
`VP-N PASS`. Cycle-4 cap-override run validated VP-1, VP-2, VP-3, VP-5 in main-thread
(no subagent provisioned); cycle-5 audit in a fresh-context subagent validated
VP-4 (one hypothesis per cycle) and VP-6 (chronological Changelog ordering).
```

---

## Why this edit, not another

1. **Geodesic-only criterion (spec §Single-Action Selection)**: argmin d_post over the 7 missing primitives gives a degenerate tie at d_post = 0.0 for all candidates (homogenization collapse when any single missing primitive is forced to 1 across all 31 sections). The principled choice per the user's stated basis mapping is `p5_has_test` (= PR1's `trust_chain`).
2. **Cost-vs-impact honesty**: cost = medium (~30 lines), but the edit closes a real semantic gap (the file's `## Verification` section is a compliance checklist without the operational form). The single-action-curve-rsi changelog cycle 1 used the same template (3 falsifiable bash commands in `## Verification plan`) on `sealed-uki-vm-prior-research-report-2026-07-31.md` and produced Δ = +0.086 — empirical confirmation that this template moves the S² point.
3. **Section-aware**: the file already has a `## Verification` section; the new `## Verification plan` section sits adjacent (per the spec's "section-aware" rule) and references it explicitly. No new frontmatter, no duplicate headers.
4. **Does NOT mix edit types**: single intent (close a gap), per the file's own anti-pattern rule "A cycle that mixes close + sharpen + reposition is a red flag".

---

## What this edit does NOT do (explicit non-goals)

- Does NOT rewrite the duplicated body (the file has 31 sections, many duplicates from cycle concatenations). That's a `sharpen` edit type — separate cycle.
- Does NOT alter the description frontmatter line. Description drift is `fix drift` — separate cycle.
- Does NOT move the skill to a different workflow position. That's `reposition` — `using-agent-skills` handles it.
- Does NOT close all 7 missing primitives. The single-action discipline caps this cycle at one primitive flip.
