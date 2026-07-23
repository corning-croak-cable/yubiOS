> **Archived research snapshot** synced from the assistant knowledge base (`documents/github-yubios-KS9n5GAT/knowledge/`) on 2026-07-23. May predate current specs — treat `PINNED.md` and the dated `refs/*` notes as the live source of truth; this is background research context only.

---

# Docker Build Policies Reference
_Last verified: June 25, 2026 — Sources: docs.docker.com/build/policies_

## What it is

Docker Build Policies (Buildx ≥ 0.31.0) enforce supply-chain rules on build inputs using OPA Rego. They run before any layer executes, gating on attestations, allowed registries, signed Git tags, digests, etc.

Policy file is named after the Containerfile: `<repo>.rego`, placed alongside it. Or specify with `filename=<file>` in the `--policy` flag.\n\n**Key fact from June 2026 review:** `docker buildx policy eval` does NOT exist. Debug via `--progress=plain` and `log-level=debug` in the policy flag string. yubiOS invocation: `docker buildx build --policy reset=true,strict=true,filename=yubiOS.rego .`. Full policy + CLI reference in `docker-buildx-rootless` skill.

---

## Minimal Policy

```rego
package docker

default allow := false

# Allow local inputs
allow if input.local

# Allow images with provenance attestations
allow if {
    input.image.hasProvenance
}

decision := {"allow": allow}
```

If violated (e.g., FROM image lacks provenance), the build fails before any layer runs.

---

## CLI Usage

```bash
# Auto-loads Dockerfile.rego if present
docker buildx build .

# Specify policy file explicitly
docker buildx build --policy filename=strict.rego .

# reset=true: ignore auto-loaded policy, use only named one
docker buildx build --policy reset=true,filename=strict.rego .

# strict=true: fail if no policy loads or BuildKit lacks support
docker buildx build --policy strict=true .

# yubiOS usage (from AGENTS.md)
docker buildx build --policy reset=true,strict=true,filename=$REPO.rego .
```

---

## Common Policy Examples

```rego
# Only allow images from specific registry
allow if {
    startswith(input.image.ref, "dhi.io/")
}

# Require image to be referenced by digest (not mutable tag)
allow if {
    input.image.isCanonical
}

# Require Go 1.21+ in base image
allow if {
    semver.compare(input.image.metadata.go_version, "1.21.0") >= 0
}

# Require SBOM attestation
allow if {
    input.image.hasSBOM
}

# Require provenance from GitHub Actions
allow if {
    input.image.hasProvenance
    input.image.provenance.builder.id == "https://github.com/actions/runner"
}
```

---

## Debugging

```bash
# See full input JSON without building
docker buildx policy eval --print .

# Debug logging
docker buildx build --policy log-level=debug --progress=plain .
```

---

## yubiOS Context

The AGENTS.md pinned image:
```
docker pull dhi.io/debian-base:trixie-debian13-dev@sha256:9415967aa0ed8adea8b5c048994259d1982026dca143d0303c7bbe0e11ed67d3
docker buildx build --policy reset=true,strict=true,filename=$REPO.rego .
```

Policy should verify:
- Image comes from `dhi.io/` registry
- Image is referenced by digest (`isCanonical`)
- Provenance present (supply chain integrity)

---

## Integration Points

- **SLSA provenance**: `input.image.hasProvenance` + `input.image.provenance.*`
- **SBOM attestations**: `input.image.hasSBOM` (Syft/SPDX format)
- **Docker Scout**: post-build CVE monitoring complements policy-at-build-time
- **Compliance**: Policies satisfy SOC 2 / ISO 27001 supply chain requirements
