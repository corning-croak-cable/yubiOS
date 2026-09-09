# Deterministic-output contract of the reproducible-build pipeline

Date: 2026-09-08
Source: wayfinder ADD rung (Outputs-axis sector)

## Problem statement

How might we state, as a checkable contract, what the reproducible-build pipeline promises about output determinism?

## Output artifacts

- The OCI image and per-platform manifests — identified by digest.
- Attached provenance/SBOM attestations naming the build inputs.
- Build logs — diagnostics only, not a contract artifact.

## Determinism contract

- **Same inputs → same digest.** Same source revision, base digest, and build args yield identical digests, modulo documented non-determinism.
- **SOURCE_DATE_EPOCH discipline.** Timestamps come from a pinned source, not wall-clock.
- **Documented non-determinism.** Anything non-deterministic is listed here with its cause; unlisted divergence is a violation.
- **Verification is external.** Checked by rebuilding and comparing digests, not by trusting builder logs.

## Side effects

Permitted: pushing artifacts, attaching attestations, writing run summaries.

## Failure semantics

- A build that cannot meet the contract fails; no "best effort" artifact.
- Partial pushes fail; an artifact exists only when the build step completed.

## Verification plan

**Run cmd**: rebuild twice from the same pinned inputs; compare digests.
**Expected output**: identical digests; attestations attached.
**Pass criterion**: digest equality.

## Trust chain coverage

A deterministic digest is the anchor for cosign signatures and SLSA provenance.

## Least-privilege coverage

Builds run rootless (per rootless-container-builds); side effects bound to the list.

## Declarative policy coverage

Build Policies (Rego) vet build inputs; this contract governs what they may produce.

## Continuous / adaptive coverage

Every CI build run re-tests the determinism claim.

## Cryptographic identity coverage

Image digests are content-addressed identity; the cosign/SLSA chain signs that identity.
