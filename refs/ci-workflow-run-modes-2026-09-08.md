# yubiOS CI workflow run modes — 2026-09-08

Status: execution-mode reference for the yubiOS workflow families: triggers, locations, exit meaning.

## Scope

Classifies the .github/workflows/ families by execution mode. Generic criteria; check trigger blocks before dispatching.

## Modes supported

- **Event-driven (push/PR)**: build and smoke lanes that fire on code changes; red fails the PR check.
- **Dispatch-only (workflow_dispatch)**: the VM test lanes, with inputs (image, hw_device, allow_real_u2f) defaulting safe — the ALLOW_REAL_U2F guard relies on that.
- **Orchestrator groups**: ci.yml routes dispatches to inner workflows by a group input; outer success means only the dispatcher ran.
- **Recovery/self-service**: fetch-group workflows are re-run by the agent without human input when a digest expires.

## Dry-run behavior

No global dry-run. Substitutes: a lint/check-only input where declared; reading the dispatch plan (which jobs a group fans out to) first. Never probe by dispatching a mutating lane.

## Idempotency

Dispatching the same group twice is safe — runs are independent — but avoid double-dispatch in flight. Digest-bump and manifest-fetch workflows are deliberately re-runnable and converge at a later head.

## Exit semantics

- Green requires every required job on both matrix legs (amd64, arm64 self-hosted) to succeed; read per-job status, not the summary.
- Report a conclusion only with its workflow path and run id, per the PROJECT_RULES.md discipline.
- Inner-chain failures do not propagate as outer failures — read the inner runs' conclusions.

## Trust chain coverage

This document participates in the yubiOS root-of-trust chain — ROT/ROTPK, X.509 PKI, root-key custody, transitive verification across boot stages.

## Continuous / adaptive coverage

This document supports the yubiOS continuous-monitoring layer — runtime detection, adaptive policy, real-time monitoring; alerts and metrics feed into the audit-evidence rollup.
