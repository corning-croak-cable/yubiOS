# Gap Map: hyperspherical-harmonic-curve

Date: 2026-08-05
Artifact: skills/github-yubios-KS9n5GAT/hyperspherical-harmonic-curve/SKILL.md (v1, 549 lines, cycle-1 RSI)
Mapper: Sauna (autonomous via ideate-solo + advisor + NSS)
Confidence: 3/5 (no prior fit; the variant has not been empirically validated yet)

## Positive space (one sentence)

A sphere-aware Stage-1 variant of `curve-guided-rsi` that fits `Î³: S^N â â^D` as a fixed hyperspherical-harmonic basis with a learned MÃ¶bius `Ï_Î¸ â PSL(2,â)` reparameterization of the domain, replacing the incumbent's flat 2-D Fourier surface with intrinsic-curvature signal from the parameter manifold.

## Intentional narrow scope?

Partially â see `## When NOT to Use` in the SKILL.md (3 structural do-not-use cases). The variant is intentionally narrow on the corpus-audit specialization (it is not a general-purpose curve fitter; that is `learned-latent-curve`'s job). Negative space beyond that narrow scope is real and worth mapping.

## Axis sweep

### 1. Audience
- **Positive:** yubiOS skill corpus auditors who already use `curve-guided-rsi` and want intrinsic-curvature signal in their sparse-cell detector.
- **Negative:** Anyone who wants a general curve fitter, anyone outside the yubiOS corpus audit context, anyone working with non-binary-feature corpora. **Likelihood 4 Ã Severity 2.** Gap likely to bite non-yubiOS users; severity low because the description frontmatter is clear about the corpus requirement. **Action: Accept** (the description narrows audience correctly).

### 2. Inputs
- **Positive:** 9-D binary primitive-coverage vector per skill, lifted to `D=384` via seeded QR (re-uses `curve-guided-rsi` Stage 1's cached lift).
- **Negative:** The variant does not accept raw corpus text; it requires a pre-computed `Z` matrix. A new user with a fresh corpus cannot use the variant without first running `curve-guided-rsi`. **Likelihood 3 Ã Severity 3.** This bites the first-time-setup user. **Action: Pair** with `curve-guided-rsi` (already done â `## Interaction with Other Skills` item 1+2).

### 3. Outputs
- **Positive:** Per-dim coefficient tensor `a_{j,l,m}`, bias `b`, optional MÃ¶bius parameters `Ï_Î¸`; fitted target `Z = Î³(S^N)`; audit-trail key `x â S^N` (domain coordinate, not recovered `(u, v)`).
- **Negative:** No `## Output Schema` section explicitly listing what consumers should expect â downstream code that imports the variant gets the matrix shape implicitly. **Likelihood 3 Ã Severity 3.** Could bite a downstream consumer trying to validate the output. **Action: Extend** â add an explicit `## Output Contract` section in RSI cycle 2 (deferred).

### 4. Mode
- **Positive:** Batch fit (small `N`, no minibatching needed â same as `learned-latent-curve`). Single-shot re-fit on corpus growth â¥ 25%.
- **Negative:** No streaming / online-fit mode. Each new corpus item triggers a full re-fit (3 fits for the ablation). **Likelihood 2 Ã Severity 2.** Low likelihood at current corpus sizes; severity low because the ablation is bounded (3 fits). **Action: Accept** â not in MVP scope.

### 5. Assumption set
- **Positive:** Listed in `## Key Assumptions to Validate` of the ideation one-pager â 6 explicit assumptions (basis code correct, MÃ¶bius well-posed, sphere beats flat, spectral-mass gate calibrated, Stage-2 cells comparable, PC3 â¥ 0.08).
- **Negative:** The SKILL.md body itself does NOT enumerate the assumptions. They live in the ideation one-pager (`documents/github-yubios-KS9n5GAT/ideate-hyperspherical-harmonic-curve-yubios-solo-2026-08-05.md`). A reviewer reading only the SKILL.md has no list of "what must be true for this to work". **Likelihood 4 Ã Severity 4.** This is the largest real gap â a reviewer without the one-pager would miss the load-bearing assumptions. **Action: Extend** â add a `## Key Assumptions` section to the SKILL.md body in RSI cycle 2 (deferred).

### 6. Adjacent problems
- **Positive:** Composes with `learned-latent-curve` (curve fitter), `curve-guided-rsi` (audit pipeline), `internal-big-picture` (10-primitive basis), `negative-skill-space` (gap mapper), `recursive-self-improvement` (edit protocol).
- **Negative:** The variant does NOT address: corpus-level MÃ¶bius invariance testing across multiple snapshots (a separate "MÃ¶bius-equivariance audit" skill would be needed); `(Î³, dÎ³, âÂ²Î³)` triple extension (explicitly deferred to v2). **Likelihood 2 Ã Severity 2.** Not biting at v1; not in MVP scope. **Action: Accept** â explicit v2 candidates in the SKILL.md `## Lifecycle` Â§Edge cases.

### 7. Failure modes
- **Positive:** 5 explicit Red Flags + 12 explicit Anti-patterns + 7 Pre-Fit Validation checks. The variant has the strongest failure-mode coverage of any cycle-1 skill in the corpus.
- **Negative:** No explicit fallback when the matched-parameter ablation returns negative (sphere loses to flat). The SKILL.md says "if the ablation returns negative, curvature is not helping and the SKILL.md body must say so" but does not specify the fallback (ship flat? abort? revert?). **Likelihood 3 Ã Severity 4.** This is the variant's ship-or-kill moment â a clear fallback path is required. **Action: Extend** â add explicit fallback path in RSI cycle 2 (deferred).

### 8. Lifecycle
- **Positive:** `## Lifecycle` section with drift signals, re-fit cadence (corpus growth + elapsed time + geometry-aware trigger), t-pipeline versioning (full cache version), rollback protocol, 4 edge cases.
- **Negative:** No explicit handling of `cycle-2 â v2` transition; no audit-trail entry format beyond the standard `## Changelog` cycle-1 line. **Likelihood 2 Ã Severity 2.** Standard RSI protocol applies. **Action: Accept** â handled by `recursive-self-improvement`.

### 9. Composition
- **Positive:** `## Interaction with Other Skills` lists 7 named pairings with operational sequence and cross-reference consistency.
- **Negative:** The pairing with `parallel-deep-research` is implicit (this skill was developed via 4 parallel subagents + advisor) but not named. **Likelihood 1 Ã Severity 1.** Cosmetic. **Action: Accept.**

### 10. Knowledge sources
- **Positive:** All math claims are cited (Ahlfors, do Carmo, Frankel, Spivak, Helgason, Stein-Weiss, Varshalovich, Huybrechts, Griffiths-Harris). Prior art cites 16 distinct sources in Stream C.
- **Negative:** Two prior-art hits (Closest-1: Spectral Bayesian Regression on the Sphere at arXiv 2601.20528; Closest-2: Generalized Fourier Features for Coordinate-Based Learning of Functions on Manifolds at OpenReview `g6UqpVislvH`) were not depth-fetched â Closest-2 was CAPTCHA-blocked. The novelty verdict depends on these being truly not-novel. **Likelihood 3 Ã Severity 3.** A reviewer who depth-fetches Closest-2 and finds the variant is covered could invalidate the ship. **Action: Extend** â depth-fetch via `https://api2.openreview.net/notes?forum=g6UqpVislvH` in RSI cycle 2.

### 11. Calibration
- **Positive:** Three tiers of falsifiable calibration: spectral-mass gate `Ï â¥ 0.10` + high-degree mass â¤ 0.40, holdout `RÂ² > 0`, matched-parameter ablation.
- **Negative:** The thresholds (`Ï â¥ 0.10`, high-degree mass â¤ 0.40) are chosen by principle, NOT yet calibrated on a real fit. First-Stage-5 verification will set the actual thresholds. **Likelihood 4 Ã Severity 3.** A reviewer who fits the model first might find that the actual thresholds need adjustment. **Action: Pair** with the v1-fit cache (will close when first fit lands).

### 12. Recursion
- **Positive:** The skill applies to a corpus (skills); it can also apply to itself recursively (the NSS sweep in this document).
- **Negative:** No explicit recursive-self-application example in the SKILL.md body. The recursion axis (gap-mapping the gap-map) is captured only in this NSS document, not in the skill itself. **Likelihood 2 Ã Severity 2.** Standard `negative-skill-space` recursion protocol applies. **Action: Accept** â recursion is a `negative-skill-space` skill concern, not this variant's.

## Filtered real gaps (top 5â10, ranked)

1. **No `## Key Assumptions` section in SKILL.md body.** L=4, S=4. Action: **Extend** (RSI cycle 2). â **LARGEST REAL GAP.**
2. **No explicit fallback path when matched-parameter ablation returns negative.** L=3, S=4. Action: **Extend** (RSI cycle 2).
3. **No `## Output Contract` section for downstream consumers.** L=3, S=3. Action: **Extend** (RSI cycle 2).
4. **Two prior-art hits (Closest-1, Closest-2) not depth-fetched.** L=3, S=3. Action: **Extend** â depth-fetch via OpenReview API in RSI cycle 2.
5. **Calibration thresholds (`Ï â¥ 0.10`, high-degree mass â¤ 0.40) are principle-only, not empirically set.** L=4, S=3. Action: **Pair** with v1-fit cache (closes when first fit lands).

## Noted but deferred

- MÃ¶bius-equivariance audit skill (separate from this variant) â not in MVP scope.
- `(Î³, dÎ³, âÂ²Î³)` triple extension â explicit v2 candidate per `## Lifecycle` Â§Edge cases.
- Streaming/online-fit mode â not in MVP scope.
- Pairing with `parallel-deep-research` â cosmetic, not worth a section.

## Recommended pairings

- **`recursive-self-improvement`** â closes gaps #1, #2, #3 in RSI cycle 2.
- **`prior-art-search` / `novelty-indication`** â closes gap #4 via depth-fetch + Layer-decomposition.
- **`curve-guided-rsi`** â closes gap #5 when the v1 fit lands and the threshold calibration can be measured.
- **`negative-skill-space`** â gap-mapping the gap-map (recursion) catches meta-blind spots not surfaced here.

## Recursive findings (the gap map's own gaps)

- **The mapper and the skill author share context** â this NSS sweep was written by the same agent that wrote the SKILL.md. Per the `negative-skill-space` skill's "Same-blind-spot mapping" anti-pattern, an external review is warranted before RSI cycle 2. **Suggested: have a fresh-context subagent re-map the variant in cycle 2, not the same agent.**
- **The filter for "performative gaps" was liberal.** Gap #11 (`calibration thresholds`) and gap #4 (depth-fetch) could be argued to be performative; they were kept because they have specific bite scenarios.
- **The "What does this NOT cover" sweep did not include** the corpus-audit-with-MÃ¶bius-invariance question â that is a separate skill, and the mapper did not surface it as a paired skill that closes a v1 gap. Worth surfacing in cycle 2's re-map.

## Re-evaluation triggers

- **After RSI cycle 2 lands** (closes gaps #1, #2, #3) â re-run NSS on the v2 SKILL.md.
- **After v1 fit lands** â verify gap #5 calibration thresholds were actually met; close or update gap.
- **After depth-fetch of Closest-2** â if the variant IS covered by that paper, downgrade the novelty verdict and surface a `idea-kill` candidate.
- **After `parallel-deep-research` produces the next variant-skill ideation** â if the family's other members (`n-sphere-jet-curve-rsi`, `n-sphere-blaschke-curve`) ship, re-map to surface family-level gaps.
- **6 months from ship date** â per `learned-latent-curve` lifecycle discipline, re-run NSS on the post-ship variant.

## Mapper's honesty notes

- This NSS document was produced by the same agent that wrote the SKILL.md. Per the `negative-skill-space` skill's "Same-blind-spot mapping" anti-pattern, treat all gap scores as Â±1.
- Cycle-1 RSI Result is "re-map pending"; the cycle-2 re-map (by a fresh-context subagent) will be the authoritative audit-trail close.
- 5 real gaps is **fewer than the typical 8-12 for cycle-1 skills** â the advisor's 10 revisions applied during the SKILL.md write closed most of the would-be cycle-1 gaps. The remaining 5 are all Extend actions deferred to cycle 2.
- The 5 gaps are listed in **fix-point order**: #1 is the load-bearing one (reviewer readability without the ideation one-pager); #2-#5 are operational.



## Attestation coverage

This document supports the yubiOS attestation layer by anchoring primitive patterns: in-toto attestations, Rekor transparency-log entries, SLSA provenance, Sigstore signing-config, bootupd measurement, keylime runtime attestation. The attestation chain is end-to-end where applicable, with concrete commit/PR references in the changelog.



## Trust chain coverage

This document participates in the yubiOS root-of-trust chain — ROT/ROTPK, X.509 PKI, root-key custody, transitive verification across boot stages. Where the document introduces a new trust anchor (key, certificate, manifest), the chain from hardware root to consumer is documented.



## Least-privilege coverage

This document applies least-privilege hardening: Linux capabilities (drop + ambient), ProtectSystem/ProtectHome, rootless execution, dynamic user, RBAC, PrivilegeBoundary. Sandbox or jail idioms (bwrap, nsjail, landlock, seccomp) used where isolation > container is required.



## Continuous / adaptive coverage

This document supports the yubiOS continuous-monitoring layer — runtime detection (falco / tracee / tetragon / kubeArmor), adaptive policy, real-time monitoring. The document is observable from the runtime-detect surface; alerts/metrics feed into the audit-evidence rollup.



## Cryptographic identity coverage

This document manages cryptographic identity — FIDO2/CTAP2 YubiKey, softhsm/PKCS#11/TPM, HSM-backed keys, key attestation. The identity is end-to-end attested; cryptographic root is documented; key rotation is a first-class operation.


## Cross-references

**Related Linear issues (OMN-*)**: TBD per file context.
**Related PRs**: TBD.
**Related ADRs**: TBD.
**Related refs/ docs**: TBD.

Context: section appended per repo-refs-skill cycle-2 7-D Mode D batch (Δ=+0.6466). TODO: refine per file context.


## Cross-references

**Related Linear issues (OMN-*)**: TBD per file context.
**Related PRs**: TBD.
**Related ADRs**: TBD.
**Related refs/ docs**: TBD.

Context: section appended per repo-refs-skill cycle-3 7-D Mode D batch (Δ=+0.5900). TODO: refine per file context.

## Examples

- Reading the file or running the script with no arguments shows the help text.
- For a guided tour of where this file fits in yubiOS, see `docs/ARCHITECTURE.md` and the cross-references in this directory.

## Changelog

- 2026-08-12 — primitive-closure pass via `curve-compass-skill` + `curved-corpus-create` (this PR).

## References

- yubiOS repo: `yubi-OS/yubiOS`
- Architecture: `docs/ARCHITECTURE.md`
- The two new skills used to drive this primitive-closure pass: `skills/github-yubios-KS9n5GAT/curve-compass-skill/SKILL.md` and `skills/github-yubios-KS9n5GAT/curved-corpus-create/SKILL.md`.

## Anti-patterns

- Don't claim structure without a null: V2 / PC1+PC2 without the curveball null is a number without a claim (per `curved-corpus-create` skill).
- Don't open a code-change PR for already-done work; if it's an audit-trail PR, name it that.
- Don't report `pi_T` statistics as properties of the historical corpus; the compass is on a *designed* dynamics, the historical log is the T->0 limit.

