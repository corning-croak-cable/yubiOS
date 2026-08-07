# Drift priority list (PR4 cross-corpus drift detector, 4-corpus, repo-sourced)

Generated: 2026-08-07
Corpora: self (111 items, anchor, WORKSPACE-LOCAL EXCEPTION) → docs (284 items, yubi-OS/yubiOS/docs/), refs (1444 items, yubi-OS/yubiOS/refs/), cycle4 (324 items, yubi-OS/yubiOS/papers/data/repo-history-skill-cycle-4-archive-2026-08-07.json).
3 Möbius φ_θ ∈ PSL(2,C) alignments, all anchored on `self` (identity-init, closed-form ridge + L-BFGS-B).
Strict-AND gate: warp ≥ pctl 80% AND nss_total ≥ pctl 80%.
Flagged regions (aggregated): 30

## Sourcing rule (per operator standing instruction)

docs / refs / cycle4 are sourced directly from `yubi-OS/yubiOS` via
the GitHub Contents API + `raw.githubusercontent.com`. `self/` is the
ONE documented exception — no `self/` directory exists on any of the
user's repos (verified Contents API on yubi-OS/yubiOS + yubi-OS/agent-skills);
the 10 self/.md files are read from workspace `memory/personal-WbtUgeUv/`.
Resolution path: create a `yubi-OS/self` repo (or add a `self/` dir
under an existing repo), push the 10 files, update `REPO_SELF_PATH` in
this script, re-run.

## Top 10 flagged drift regions (ranked by drift_score, all 3 alignments)

### 1. alignment: `self-to-docs`, t_self = 0.0870, t_target = 0.3970, geodesic_d = 0.9483, drift_score = 10.0000

- **Nearest SELF item**: `self:2026-08-06` (file: RECENT_ACTIVITY.md, section: 2026-08-06)
- **Nearest target item**: `docs:Growth edges` (file: SELF.md, section: Growth edges)
- **NSS axis hits (total 10)**: audience=2, inputs=1, outputs=2, mode=2, assumption_set=0, adjacent_problems=0, failure_modes=0, lifecycle=0, composition=0, knowledge_sources=1, calibration=0, recursion=2

- **Self-archaeology hook**: Read `RECENT_ACTIVITY.md` section `2026-08-06` — the position on S^2 that `self-to-docs` says self has but docs lacks.

### 2. alignment: `self-to-docs`, t_self = 0.1739, t_target = 0.8040, geodesic_d = 0.9438, drift_score = 6.9665

- **Nearest SELF item**: `self:2026-08-07 — v0.27 — `repo-history-skill` shipped (hyper-sph` (file: SELF-CHANGELOG.md, section: 2026-08-07 — v0.27 — `repo-history-skill` shipped (hyper-sphere RSI archive of git + Linear history))
- **Nearest target item**: `docs:Continuous / adaptive coverage` (file: CITATION.md, section: Continuous / adaptive coverage)
- **NSS axis hits (total 7)**: audience=0, inputs=0, outputs=0, mode=0, assumption_set=0, adjacent_problems=0, failure_modes=0, lifecycle=0, composition=0, knowledge_sources=3, calibration=1, recursion=3

- **Self-archaeology hook**: Read `SELF-CHANGELOG.md` section `2026-08-07 — v0.27 — `repo-history-skill` shipped (hyper-sphere RSI archive of git + Linear history)` — the position on S^2 that `self-to-docs` says self has but docs lacks.

### 3. alignment: `self-to-docs`, t_self = 0.1304, t_target = 0.3920, geodesic_d = 0.9202, drift_score = 6.7924

- **Nearest SELF item**: `self:2026-07-31 — v0.8 — ci_test-vgpu-vm: extract-script + symlin` (file: SELF-CHANGELOG.md, section: 2026-07-31 — v0.8 — ci_test-vgpu-vm: extract-script + symlink fixes landed; composefs tamper amd64 reaches QEMU baseline (first time))
- **Nearest target item**: `docs:Threat Model Summary` (file: MITIGATE.md, section: Threat Model Summary)
- **NSS axis hits (total 7)**: audience=0, inputs=2, outputs=0, mode=1, assumption_set=1, adjacent_problems=0, failure_modes=1, lifecycle=0, composition=1, knowledge_sources=0, calibration=0, recursion=1

- **Self-archaeology hook**: Read `SELF-CHANGELOG.md` section `2026-07-31 — v0.8 — ci_test-vgpu-vm: extract-script + symlink fixes landed; composefs tamper amd64 reaches QEMU baseline (first time)` — the position on S^2 that `self-to-docs` says self has but docs lacks.

### 4. alignment: `self-to-refs`, t_self = 0.6522, t_target = 1.0000, geodesic_d = 0.9763, drift_score = 5.0000

- **Nearest SELF item**: `self:Differential-Aware Task Handling` (file: USER_PREFERENCES.md, section: Differential-Aware Task Handling)
- **Nearest target item**: `refs:Evidence requirement before OMN-53 moves to Done` (file: sealed-uki-vm-test-2026-07-30.md, section: Evidence requirement before OMN-53 moves to Done)
- **NSS axis hits (total 5)**: audience=0, inputs=1, outputs=0, mode=0, assumption_set=0, adjacent_problems=0, failure_modes=0, lifecycle=0, composition=1, knowledge_sources=1, calibration=0, recursion=2

- **Self-archaeology hook**: Read `USER_PREFERENCES.md` section `Differential-Aware Task Handling` — the position on S^2 that `self-to-refs` says self has but refs lacks.

### 5. alignment: `self-to-docs`, t_self = 0.0435, t_target = 0.8141, geodesic_d = 0.7898, drift_score = 4.1641

- **Nearest SELF item**: `self:WeHo Auto (#weho-auto space)` (file: RECENT_ACTIVITY.md, section: WeHo Auto (#weho-auto space))
- **Nearest target item**: `docs:Continuous / adaptive coverage` (file: SELF.md, section: Continuous / adaptive coverage)
- **NSS axis hits (total 5)**: audience=0, inputs=1, outputs=0, mode=0, assumption_set=0, adjacent_problems=0, failure_modes=0, lifecycle=0, composition=0, knowledge_sources=2, calibration=1, recursion=1

- **Self-archaeology hook**: Read `RECENT_ACTIVITY.md` section `WeHo Auto (#weho-auto space)` — the position on S^2 that `self-to-docs` says self has but docs lacks.

### 6. alignment: `self-to-docs`, t_self = 0.0000, t_target = 0.4020, geodesic_d = 0.3517, drift_score = 3.7086

- **Nearest SELF item**: `self:2026-08-01 — v0.15 — `playbooks/` seeded from whole-self syn` (file: SELF-CHANGELOG.md, section: 2026-08-01 — v0.15 — `playbooks/` seeded from whole-self synthesis (PR #156, OMN-152, OMN-156..162))
- **Nearest target item**: `docs:8. PLAN.md â my stewardship` (file: SOUL.md, section: 8. PLAN.md â my stewardship)
- **NSS axis hits (total 10)**: audience=1, inputs=3, outputs=0, mode=2, assumption_set=0, adjacent_problems=0, failure_modes=1, lifecycle=0, composition=0, knowledge_sources=2, calibration=0, recursion=1

- **Self-archaeology hook**: Read `SELF-CHANGELOG.md` section `2026-08-01 — v0.15 — `playbooks/` seeded from whole-self synthesis (PR #156, OMN-152, OMN-156..162)` — the position on S^2 that `self-to-docs` says self has but docs lacks.

### 7. alignment: `self-to-cycle4`, t_self = 0.1739, t_target = 0.4874, geodesic_d = 0.6426, drift_score = 3.5552

- **Nearest SELF item**: `self:2026-08-07 — v0.27 — `repo-history-skill` shipped (hyper-sph` (file: SELF-CHANGELOG.md, section: 2026-08-07 — v0.27 — `repo-history-skill` shipped (hyper-sphere RSI archive of git + Linear history))
- **Nearest target item**: `c4-Commit-1bdcd74` (file: ?, section: c4-Commit-1bdcd74)
- **NSS axis hits (total 5)**: audience=0, inputs=0, outputs=0, mode=0, assumption_set=0, adjacent_problems=0, failure_modes=0, lifecycle=0, composition=0, knowledge_sources=2, calibration=0, recursion=3

- **Self-archaeology hook**: Read `SELF-CHANGELOG.md` section `2026-08-07 — v0.27 — `repo-history-skill` shipped (hyper-sphere RSI archive of git + Linear history)` — the position on S^2 that `self-to-cycle4` says self has but cycle4 lacks.

### 8. alignment: `self-to-cycle4`, t_self = 0.5217, t_target = 1.0000, geodesic_d = 0.4547, drift_score = 3.5217

- **Nearest SELF item**: `self:Source/evidence` (file: SELF.md, section: Source/evidence)
- **Nearest target item**: `c4-Linear-OMN-18` (file: ?, section: c4-Linear-OMN-18)
- **NSS axis hits (total 7)**: audience=1, inputs=2, outputs=0, mode=0, assumption_set=0, adjacent_problems=0, failure_modes=0, lifecycle=0, composition=0, knowledge_sources=3, calibration=0, recursion=1

- **Self-archaeology hook**: Read `SELF.md` section `Source/evidence` — the position on S^2 that `self-to-cycle4` says self has but cycle4 lacks.

### 9. alignment: `self-to-docs`, t_self = 0.5217, t_target = 0.4422, geodesic_d = 0.2567, drift_score = 3.5191

- **Nearest SELF item**: `self:Source/evidence` (file: SELF.md, section: Source/evidence)
- **Nearest target item**: `docs:Pushback: what the corpus doesn't show` (file: SOUL.md, section: Pushback: what the corpus doesn't show)
- **NSS axis hits (total 13)**: audience=2, inputs=3, outputs=3, mode=0, assumption_set=0, adjacent_problems=0, failure_modes=0, lifecycle=0, composition=0, knowledge_sources=4, calibration=0, recursion=1

- **Self-archaeology hook**: Read `SELF.md` section `Source/evidence` — the position on S^2 that `self-to-docs` says self has but docs lacks.

### 10. alignment: `self-to-docs`, t_self = 0.2609, t_target = 0.3819, geodesic_d = 0.6597, drift_score = 3.4783

- **Nearest SELF item**: `self:Anti-patterns I police in myself` (file: SELF.md, section: Anti-patterns I police in myself)
- **Nearest target item**: `docs:Strengths` (file: SELF.md, section: Strengths)
- **NSS axis hits (total 5)**: audience=0, inputs=1, outputs=0, mode=2, assumption_set=0, adjacent_problems=0, failure_modes=0, lifecycle=0, composition=0, knowledge_sources=0, calibration=0, recursion=2

- **Self-archaeology hook**: Read `SELF.md` section `Anti-patterns I police in myself` — the position on S^2 that `self-to-docs` says self has but docs lacks.
