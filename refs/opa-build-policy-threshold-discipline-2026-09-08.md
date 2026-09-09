# OPA/Rego Build Policy Threshold Discipline — Calibration Note

**Date:** 2026-09-08
**Scope:** How the docker buildx build policy (OPA/Rego) for yubiOS image builds decides "deny", and what evidence that decision must carry.

---

## TL;DR

The build policy's deny decisions are a detection system, and detection systems need calibration. This note records threshold-setting discipline for the yubiOS.rego policy: what counts as a violating input, what the false-positive expectation is, and how the decision is trusted.

## Thresholds

- The decision boundary is the Rego rule set itself: an input is either approved (approved registry, digest-pinned) or denied. No partial pass.
- Threshold changes (adding an approved registry, relaxing a provenance requirement) are manifest edits reviewed like code, never quiet policy loosening inside a build job.

## False-positive expectations

- A deny firing on a legitimate input is a policy calibration failure, fixed by amending the policy with review, never by bypassing the gate.
- Expected deny reasons (unapproved registry, unpinned digest, missing provenance) are enumerated so operators distinguish misconfiguration from new failure modes.

## Ground truth

- Ground truth is the input inventory itself: FROM image refs, digests, and provenance attestations as buildx presents them — not documentation about what should be pinned.

## Measurement uncertainty

- Evaluation is deterministic per input; uncertainty lives in whether the input inventory is complete. Missing inputs surface as explicit deny reasons, never silent allows.

## Sources

- docker-build-policy and docker-buildx-rootless skills; the yubiOS.rego pattern (default deny, decision + reason).

## Declarative policy coverage

The Rego file is the declarative policy; this note only records its calibration discipline.

## Continuous / adaptive coverage

Policy-denied builds are logged and reviewed; recurring deny reasons feed back into threshold review.