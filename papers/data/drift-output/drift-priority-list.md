# Drift priority list (PR4 cross-corpus drift detector, 4-corpus)

Generated: 2026-08-07
Corpora: self (111 items, anchor) → docs (37 items), refs (55 items), cycle4 (324 items).
3 Möbius φ_θ ∈ PSL(2,C) alignments, all anchored on `self` (identity-init, closed-form ridge + L-BFGS-B).
Strict-AND gate: warp ≥ pctl 80% AND nss_total ≥ pctl 80%.
Flagged regions (aggregated across 3 alignments): 30

## Top 10 flagged drift regions (ranked by drift_score, all 3 alignments)

### 1. alignment: `self-to-refs`, t_self = 0.3478, t_target = 0.6131, geodesic_d = 0.4710, drift_score = 10.5269

- **Nearest SELF item**: `self:2026-08-02 — v0.16 — First weekly Sunday cadence fire (12-ax` (file: SELF-CHANGELOG.md, section: 2026-08-02 — v0.16 — First weekly Sunday cadence fire (12-axis sweep + register drift signal))
- **Nearest target item**: `refs:RSI loop terminates at v3 (cycle 3 = cycle 3 of repo-history` (file: repo-history-skill-cycle-3-2026-08-07-changelog.md, section: RSI loop terminates at v3 (cycle 3 = cycle 3 of repo-history-skill, NOT to be confused with hyperspherical-harmonic-curve cycle 3 which is also at v5))
- **NSS axis hits (total 12)**: audience=1, inputs=0, outputs=0, mode=2, assumption_set=1, adjacent_problems=0, failure_modes=0, lifecycle=3, composition=0, knowledge_sources=0, calibration=1, recursion=4

- **Self-archaeology hook**: Read `SELF-CHANGELOG.md` section `2026-08-02 — v0.16 — First weekly Sunday cadence fire (12-axis sweep + register drift signal)` — the position on S^2 that `self-to-refs` says self has but refs lacks. Dispatch per the self-archaeology cadence (5 self-mode turns / per-directive / Sunday 9 AM Pacific).

### 2. alignment: `self-to-docs`, t_self = 0.3478, t_target = 0.5427, geodesic_d = 0.4679, drift_score = 6.7680

- **Nearest SELF item**: `self:2026-08-02 — v0.16 — First weekly Sunday cadence fire (12-ax` (file: SELF-CHANGELOG.md, section: 2026-08-02 — v0.16 — First weekly Sunday cadence fire (12-axis sweep + register drift signal))
- **Nearest target item**: `docs:Layer 5 — Documents (artifact_weights)` (file: weight-registry-2026-07-29.md, section: Layer 5 — Documents (artifact_weights))
- **NSS axis hits (total 10)**: audience=1, inputs=0, outputs=0, mode=2, assumption_set=1, adjacent_problems=0, failure_modes=0, lifecycle=3, composition=0, knowledge_sources=0, calibration=1, recursion=2

- **Self-archaeology hook**: Read `SELF-CHANGELOG.md` section `2026-08-02 — v0.16 — First weekly Sunday cadence fire (12-axis sweep + register drift signal)` — the position on S^2 that `self-to-docs` says self has but docs lacks. Dispatch per the self-archaeology cadence (5 self-mode turns / per-directive / Sunday 9 AM Pacific).

### 3. alignment: `self-to-docs`, t_self = 0.0870, t_target = 0.2613, geodesic_d = 0.5916, drift_score = 5.9901

- **Nearest SELF item**: `self:2026-08-06` (file: RECENT_ACTIVITY.md, section: 2026-08-06)
- **Nearest target item**: `docs:Layer 1 — System prompt (model_weights_analogue)` (file: weight-registry-2026-07-29.md, section: Layer 1 — System prompt (model_weights_analogue))
- **NSS axis hits (total 7)**: audience=0, inputs=0, outputs=1, mode=1, assumption_set=0, adjacent_problems=0, failure_modes=0, lifecycle=1, composition=0, knowledge_sources=2, calibration=0, recursion=2

- **Self-archaeology hook**: Read `RECENT_ACTIVITY.md` section `2026-08-06` — the position on S^2 that `self-to-docs` says self has but docs lacks. Dispatch per the self-archaeology cadence (5 self-mode turns / per-directive / Sunday 9 AM Pacific).

### 4. alignment: `self-to-docs`, t_self = 0.1304, t_target = 0.2613, geodesic_d = 0.6187, drift_score = 5.3689

- **Nearest SELF item**: `self:2026-07-31 — v0.8 — ci_test-vgpu-vm: extract-script + symlin` (file: SELF-CHANGELOG.md, section: 2026-07-31 — v0.8 — ci_test-vgpu-vm: extract-script + symlink fixes landed; composefs tamper amd64 reaches QEMU baseline (first time))
- **Nearest target item**: `docs:Layer 1 — System prompt (model_weights_analogue)` (file: weight-registry-2026-07-29.md, section: Layer 1 — System prompt (model_weights_analogue))
- **NSS axis hits (total 6)**: audience=0, inputs=0, outputs=1, mode=1, assumption_set=0, adjacent_problems=0, failure_modes=0, lifecycle=1, composition=1, knowledge_sources=1, calibration=0, recursion=1

- **Self-archaeology hook**: Read `SELF-CHANGELOG.md` section `2026-07-31 — v0.8 — ci_test-vgpu-vm: extract-script + symlink fixes landed; composefs tamper amd64 reaches QEMU baseline (first time)` — the position on S^2 that `self-to-docs` says self has but docs lacks. Dispatch per the self-archaeology cadence (5 self-mode turns / per-directive / Sunday 9 AM Pacific).

### 5. alignment: `self-to-docs`, t_self = 0.1739, t_target = 0.0000, geodesic_d = 0.6053, drift_score = 5.2528

- **Nearest SELF item**: `self:2026-08-07 — v0.27 — `repo-history-skill` shipped (hyper-sph` (file: SELF-CHANGELOG.md, section: 2026-08-07 — v0.27 — `repo-history-skill` shipped (hyper-sphere RSI archive of git + Linear history))
- **Nearest target item**: `docs:Note on <primitive> coverage (curve-guided-rsi v1 gap-fix)` (file: curve-guided-rsi-run-2026-08-03.md, section: Note on <primitive> coverage (curve-guided-rsi v1 gap-fix))
- **NSS axis hits (total 6)**: audience=0, inputs=1, outputs=0, mode=0, assumption_set=0, adjacent_problems=0, failure_modes=0, lifecycle=0, composition=0, knowledge_sources=2, calibration=0, recursion=3

- **Self-archaeology hook**: Read `SELF-CHANGELOG.md` section `2026-08-07 — v0.27 — `repo-history-skill` shipped (hyper-sphere RSI archive of git + Linear history)` — the position on S^2 that `self-to-docs` says self has but docs lacks. Dispatch per the self-archaeology cadence (5 self-mode turns / per-directive / Sunday 9 AM Pacific).

### 6. alignment: `self-to-docs`, t_self = 0.0435, t_target = 0.0000, geodesic_d = 0.6914, drift_score = 5.0000

- **Nearest SELF item**: `self:WeHo Auto (#weho-auto space)` (file: RECENT_ACTIVITY.md, section: WeHo Auto (#weho-auto space))
- **Nearest target item**: `docs:Note on <primitive> coverage (curve-guided-rsi v1 gap-fix)` (file: curve-guided-rsi-run-2026-08-03.md, section: Note on <primitive> coverage (curve-guided-rsi v1 gap-fix))
- **NSS axis hits (total 5)**: audience=0, inputs=2, outputs=0, mode=0, assumption_set=0, adjacent_problems=0, failure_modes=0, lifecycle=0, composition=0, knowledge_sources=1, calibration=0, recursion=2

- **Self-archaeology hook**: Read `RECENT_ACTIVITY.md` section `WeHo Auto (#weho-auto space)` — the position on S^2 that `self-to-docs` says self has but docs lacks. Dispatch per the self-archaeology cadence (5 self-mode turns / per-directive / Sunday 9 AM Pacific).

### 7. alignment: `self-to-docs`, t_self = 0.2609, t_target = 0.0000, geodesic_d = 0.5023, drift_score = 4.3594

- **Nearest SELF item**: `self:Anti-patterns I police in myself` (file: SELF.md, section: Anti-patterns I police in myself)
- **Nearest target item**: `docs:Note on <primitive> coverage (curve-guided-rsi v1 gap-fix)` (file: curve-guided-rsi-run-2026-08-03.md, section: Note on <primitive> coverage (curve-guided-rsi v1 gap-fix))
- **NSS axis hits (total 6)**: audience=0, inputs=2, outputs=0, mode=2, assumption_set=0, adjacent_problems=0, failure_modes=0, lifecycle=0, composition=0, knowledge_sources=0, calibration=0, recursion=2

- **Self-archaeology hook**: Read `SELF.md` section `Anti-patterns I police in myself` — the position on S^2 that `self-to-docs` says self has but docs lacks. Dispatch per the self-archaeology cadence (5 self-mode turns / per-directive / Sunday 9 AM Pacific).

### 8. alignment: `self-to-docs`, t_self = 0.7391, t_target = 0.4221, geodesic_d = 0.4301, drift_score = 4.3541

- **Nearest SELF item**: `self:Key Quotes` (file: USER_PROFILE.md, section: Key Quotes)
- **Nearest target item**: `docs:Stage 5: Re-fit + verification (CLOSED LOOP)` (file: curve-guided-rsi-run-2026-08-03.md, section: Stage 5: Re-fit + verification (CLOSED LOOP))
- **NSS axis hits (total 7)**: audience=0, inputs=0, outputs=0, mode=0, assumption_set=0, adjacent_problems=0, failure_modes=0, lifecycle=1, composition=0, knowledge_sources=1, calibration=3, recursion=2

- **Self-archaeology hook**: Read `USER_PROFILE.md` section `Key Quotes` — the position on S^2 that `self-to-docs` says self has but docs lacks. Dispatch per the self-archaeology cadence (5 self-mode turns / per-directive / Sunday 9 AM Pacific).

### 9. alignment: `self-to-refs`, t_self = 0.7826, t_target = 0.4221, geodesic_d = 0.4489, drift_score = 4.1805

- **Nearest SELF item**: `self:Differential Awareness` (file: SAUNA_IDENTITY.md, section: Differential Awareness)
- **Nearest target item**: `refs:7. Recommended next steps` (file: refederated-identity-oidc-sigstore-privacy-2026-08-07.md, section: 7. Recommended next steps)
- **NSS axis hits (total 5)**: audience=0, inputs=1, outputs=0, mode=0, assumption_set=1, adjacent_problems=0, failure_modes=0, lifecycle=0, composition=1, knowledge_sources=1, calibration=0, recursion=1

- **Self-archaeology hook**: Read `SAUNA_IDENTITY.md` section `Differential Awareness` — the position on S^2 that `self-to-refs` says self has but refs lacks. Dispatch per the self-archaeology cadence (5 self-mode turns / per-directive / Sunday 9 AM Pacific).

### 10. alignment: `self-to-refs`, t_self = 0.7391, t_target = 0.0000, geodesic_d = 0.4145, drift_score = 3.8602

- **Nearest SELF item**: `self:Key Quotes` (file: USER_PROFILE.md, section: Key Quotes)
- **Nearest target item**: `refs:Result (live fit on 2026-08-07 11:32 UTC)` (file: repo-history-skill-cycle-3-2026-08-07-changelog.md, section: Result (live fit on 2026-08-07 11:32 UTC))
- **NSS axis hits (total 5)**: audience=0, inputs=1, outputs=0, mode=1, assumption_set=0, adjacent_problems=0, failure_modes=0, lifecycle=0, composition=0, knowledge_sources=2, calibration=0, recursion=1

- **Self-archaeology hook**: Read `USER_PROFILE.md` section `Key Quotes` — the position on S^2 that `self-to-refs` says self has but refs lacks. Dispatch per the self-archaeology cadence (5 self-mode turns / per-directive / Sunday 9 AM Pacific).
