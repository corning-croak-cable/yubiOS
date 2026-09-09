# Attestation-artifact output shape of the cosign/SLSA pipeline

Date: 2026-09-08
Source: wayfinder ADD rung (Outputs-axis sector)

## Problem statement

How might we pin down what the cosign/SLSA pipeline emits for a bootc image, so consumers know what to expect and what "verified" means?

## Output artifacts

- **Signature layer**: a cosign signature over the image digest.
- **Attestation layer**: cosign attestations with in-toto predicates — SLSA provenance, SBOM.
- **Bound subject**: artifacts bind to the image *digest*, never a mutable tag.

## Output contract

- **Shape stability**: predicate types and field names are contract; changes need a versioned predicate type.
- **Idempotency**: re-signing an attested digest yields no duplicates; the set converges.
- **Determinism of binding**: same image → same subject binding; only signer timestamps differ.
- **Transparency**: a consumer re-derives the verdict from the artifact, not pipeline logs.

## Side effects

Permitted: pushing signatures/attestations to the registry, writing a run summary.

## Failure semantics

- A signing step that cannot bind a resolvable digest fails — no orphaned attestations.
- Verification failure is a finding to the consumer, never a silent pass.

## Verification plan

**Run cmd**: cosign verify / verify-attestation against the registry for a signed digest.
**Expected output**: signature and each declared attestation type resolve.
**Pass criterion**: independent verification succeeds.

## Trust chain coverage

These artifacts link build to boot-time policy; malformation breaks the chain.

## Least-privilege coverage

Signing credentials are scoped to producing these artifacts only.

## Declarative policy coverage

Policy gates (Build Policies, admission checks) consume this shape.

## Continuous / adaptive coverage

Every CI signing run re-emits these artifacts.

## Cryptographic identity coverage

Signing identity, key refs, and transparency-log anchoring are first-class fields.
