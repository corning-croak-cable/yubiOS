---
name: slsa-provenance
description: 'Implements SLSA supply chain security levels 3 and 4. Use when adding provenance attestations to build artifacts, setting up GitHub Actions SLSA workflows, verifying attestations with slsa-verifier or cosign, or auditing a build pipeline for supply chain compliance. Triggers on: SLSA, provenance, attestation, supply chain, sigstore, cosign, rekor.'
---

# SLSA Provenance

## Overview

SLSA (Supply-chain Levels for Software Artifacts) makes the build process tamper-evident. Level 3 is the practical target for yubiOS; Level 4 requires fully hermetic builds and two-party review.

## Level Requirements

| Level | Source | Build | Provenance |
|---|---|---|---|
| L1 | any | scripted | generated |
| L2 | versioned | CI service | authenticated |
| **L3** | automated | isolated/ephemeral | non-falsifiable (service-signed) |
| L4 | 2-party reviewed | hermetic + reproducible | complete deps |

**L3 does not require hermetic builds.** Network access is allowed; isolation is the key property.

**L4 on GitHub Actions is hard** — hermetic builds require declaring all deps and blocking network. Aim for L3, document gaps toward L4.

---

## GitHub Actions: SLSA L3 Provenance

Use `slsa-framework/slsa-github-generator` reusable workflows. They run in isolated GitHub-hosted runners (the isolation is what makes it L3).

### Container image provenance

```yaml
# .github/workflows/release.yml
jobs:
  build:
    permissions:
      id-token: write
      contents: read
      packages: write
    uses: slsa-framework/slsa-github-generator/.github/workflows/generator_container_slsa3.yml@v2.1.0
    with:
      image: ghcr.io/yubi-OS/yubiOS
      digest: ${{ needs.build.outputs.digest }}
    secrets:
      registry-username: ${{ github.actor }}
      registry-password: ${{ secrets.GITHUB_TOKEN }}
```

### Generic binary provenance (OCI artifacts, UKIs)

```yaml
jobs:
  provenance:
    needs: [build]
    permissions:
      id-token: write
      contents: read
    uses: slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@v2.1.0
    with:
      base64-subjects: ${{ needs.build.outputs.hashes }}
```

Generate `hashes` in your build job:
```bash
sha256sum artifact.uki artifact.img | base64 -w0
```

---

## Provenance Format

SLSA provenance is an **in-toto v1.0 Statement** in a **DSSE envelope**, signed by the build service's OIDC identity and logged in **Rekor** (Sigstore transparency log).

```json
{
  "_type": "https://in-toto.io/Statement/v0.1",
  "predicateType": "https://slsa.dev/provenance/v0.2",
  "subject": [{ "name": "artifact.uki", "digest": { "sha256": "abc123..." } }],
  "predicate": {
    "builder": { "id": "https://github.com/slsa-framework/slsa-github-generator/...@refs/tags/v2.1.0" },
    "buildType": "...",
    "invocation": {
      "configSource": {
        "uri": "git+https://github.com/yubi-OS/yubiOS",
        "entryPoint": ".github/workflows/release.yml"
      }
    },
    "materials": [{ "uri": "git+...", "digest": { "sha1": "..." } }]
  }
}
```

---

## Verification

```bash
# Verify SLSA provenance for a binary
slsa-verifier verify-artifact artifact.uki \
  --provenance-path artifact.uki.intoto.jsonl \
  --source-uri github.com/yubi-OS/yubiOS \
  --builder-id https://github.com/slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@v2.1.0

# Verify container image attestation with cosign
cosign verify-attestation \
  --type slsaprovenance \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  --certificate-identity-regexp 'https://github.com/slsa-framework/slsa-github-generator' \
  ghcr.io/yubi-OS/yubiOS@sha256:...

# Inspect Rekor entry
rekor-cli get --uuid <uuid> --format json | jq .
```

---

## Cosign: Signing and Attesting

```bash
# Keyless signing (GitHub Actions — uses OIDC identity)
cosign sign ghcr.io/yubi-OS/yubiOS@sha256:...

# Attach an SBOM attestation
cosign attest \
  --type spdxjson \
  --predicate sbom.spdx.json \
  ghcr.io/yubi-OS/yubiOS@sha256:...

# Verify signature keylessly
cosign verify \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  --certificate-identity https://github.com/yubi-OS/yubiOS/.github/workflows/release.yml@refs/heads/main \
  ghcr.io/yubi-OS/yubiOS@sha256:...
```

---

## Docker Build Policy Integration

Enforce provenance at build time with a Rego policy:

```rego
package docker

default allow := false

# Require all FROM images to have SLSA provenance
allow if {
    input.image.hasProvenance
}

# Require canonical digest (no mutable tags)
allow if {
    input.image.isCanonical
}

decision := {"allow": allow}
```

```bash
docker buildx build --policy reset=true,strict=true,filename=$REPO.rego .
```

---

## yubiOS Checklist

- [ ] OCI image gets SLSA L3 provenance via `generator_container_slsa3.yml`
- [ ] UKI binary gets generic L3 provenance via `generator_generic_slsa3.yml`
- [ ] All `FROM` base images pinned to digests (`dhi.io/debian-base@sha256:...`)
- [ ] `Dockerfile.rego` enforces `isCanonical` + `hasProvenance` on inputs
- [ ] SBOM (SPDX via Syft) attached as cosign attestation
- [ ] `slsa-verifier` runs in post-deploy CI as gate

---

## Rekor v2 Notes (GA Oct 2025)

Rekor v2 uses tile-based logs. Clients auto-migrate. Use `rekor-cli` >= v2 or Cosign >= v2.4 for compatibility.

---

## References

- https://slsa.dev/spec/v1.0/levels
- https://github.com/slsa-framework/slsa-github-generator
- https://docs.sigstore.dev/cosign/verifying/attestation/
- https://github.com/sigstore/rekor
