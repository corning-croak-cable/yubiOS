# Exit-code vocabulary for the yubiOS CI test-script family

Date: 2026-09-08
Source: wayfinder ADD rung (Outputs-axis sector)
Scope: a shared vocabulary over existing CI test scripts

## Problem statement

How might we give every yubiOS CI test script one shared exit-code vocabulary, so a caller can distinguish "the check failed" from "the harness could not run" without parsing stderr?

## Output contract

- **Exit 0** — passed; stdout carries the PASS summary.
- **Exit 1** — check failed: a *finding*, not a harness fault; stderr names the failed check.
- **Exit 2** — usage error; no check ran.
- **64–78 (sysexits.h)** — environment failures (unreachable prerequisite, bad config); retryable by class. A finding is not.
- **≥ 128** — killed by signal; no verdict.

## Rules

- Never swallow an error and exit 0.
- stderr is diagnostics and findings; stdout is the machine-readable summary only.
- Exit codes are a closed set: a new code updates this document, not just the script.
- Callers branch on class (0 / 1 / 2 / 64-78 / ≥128) without knowing the script.

## Verification plan

**Run cmd**: run any family script with a broken prerequisite and a failing check.
**Expected output**: distinct exit codes; finding on stderr, summary on stdout.
**Pass criterion**: callers distinguish harness fault from finding by exit code alone.

## Trust chain coverage

A script that cannot report its verdict cannot anchor the chain from artifact to attested image.

## Least-privilege coverage

Test scripts run with minimal token scopes; the environment-failure class avoids leaking config into stdout.

## Declarative policy coverage

The contract is a policy-as-code gate: CI steps branch on exit codes; weakening it is a policy regression.

## Continuous / adaptive coverage

CI runs are the continuous surface; exit-code classes feed the run-status rollup.

## Cryptographic identity coverage

Cosign steps report signature failure as a finding (exit 1), never a retryable environment fault.
