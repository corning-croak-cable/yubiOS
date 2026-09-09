# bcvk ephemeral VM run modes — 2026-09-08

Status: execution-mode reference for bcvk's ephemeral VM surface as yubiOS CI uses it.

## Scope

How bcvk's ephemeral operations behave across execution modes. Generic criteria; verify flags against the bcvk pin.

## Modes supported

- **One-shot (ephemeral)**: the VM exists for one task's lifetime, then is discarded — the default yubiOS CI contract.
- **Detached**: the VM runs in the background; the script polls SSH readiness in a bounded loop.
- **Interactive**: console/shell attach for debugging.
- **Batch/scripted**: step-numbered script, tee'd logs, fail fast.

## Foreground vs background

Foreground runs block until the VM exits. Detached is the CI pattern: start, poll, never assume self-termination. Every detached VM needs a matching stop/rm in cleanup, or the runner leaks capacity.

## Dry-run behavior

No dedicated dry-run flag assumed. Substitutes: inspect existing VMs instead of creating; resolve image refs and ports read-only first; gate creation behind a check-only variable that prints the plan.

## Idempotency

Creation alone is not idempotent — re-running a boot step can double-create. Make scripts idempotent: deterministic VM names, tear down any same-named VM before boot, treat already-stopped/removed as success.

## Exit semantics

- Exit 0 only when every assertion passed and cleanup ran.
- Fail fast on the first failed assertion; tee or upload VM logs before exiting non-zero.
- Cleanup failures stay non-fatal (best-effort rm) so teardown never masks the result.

## Trust chain coverage

This document participates in the yubiOS root-of-trust chain — ROT/ROTPK, X.509 PKI, root-key custody, transitive verification across boot stages.

## Continuous / adaptive coverage

This document supports the yubiOS continuous-monitoring layer — runtime detection, adaptive policy, real-time monitoring; alerts and metrics feed into the audit-evidence rollup.
