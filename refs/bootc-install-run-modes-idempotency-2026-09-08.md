# bootc install run modes and idempotency — 2026-09-08

Status: execution-mode reference for the bootc install paths, per refs/bootc-composefs-sealed-flow-2026-07-22.md.

## Scope

What runs unconditionally, what can be staged beforehand, what a re-run guarantees. Generic criteria; verify against PINNED.md.

## Modes supported

- **Full install (mutating)**: populates a target and writes a bootable deployment; destructive.
- **Prepare-only stages**: partitioning, formatting, mounting done by the operator first — the yubiOS composefs flow relies on this.
- **Source-directed variants**: from an image reference (e.g. the published yubios image) or local content.
- **Probe context**: install subcommands can run in a non-booting context to validate the image.

## Dry-run behavior

Treat any invocation that formats, mounts, or writes as non-dry-run. Derive previews: resolve the source ref read-only, print the planned mount spec and kernel args, gate the mutating call behind a confirmation variable.

## Idempotency

A re-run against an installed target is not a guaranteed no-op — it may fail loudly or overwrite preparation. Either recreate the target each run, or detect a valid existing install and skip (CI-friendly: check the layout, treat presence as success).

## Exit semantics

- Exit 0 only when the deployment is fully written and bootloader config is in place; partial writes must not pass.
- A failed install leaves the target untouched or clearly half-built, never bootable-but-wrong.
- CI: fail fast, capture stderr, never continue to boot assertions after a non-zero exit.

## Trust chain coverage

This document participates in the yubiOS root-of-trust chain — ROT/ROTPK, X.509 PKI, root-key custody, transitive verification across boot stages.

## Continuous / adaptive coverage

This document supports the yubiOS continuous-monitoring layer — runtime detection, adaptive policy, real-time monitoring; alerts and metrics feed into the audit-evidence rollup.
