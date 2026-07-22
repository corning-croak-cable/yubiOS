# yubiOS Docker Build Policy
# Applied via: docker buildx build --policy reset=true,strict=true,filename=yubiOS.rego .
#
# Enforces supply chain rules on all build inputs before any layer executes.
# Violations fail the build immediately — nothing is pulled or built.
#
# Sources:
#   https://docs.docker.com/build/policies/
#   AGENTS.md — approved registries and build policy pattern

package docker

import future.keywords.if
import future.keywords.in

# ── Default deny ─────────────────────────────────────────────────────────────
default allow := false

# ── Approved base registries ──────────────────────────────────────────────────
# quay.io/fedora/      — official Fedora bootc images (yubiOS base)
# dhi.io/              — internal pinned build tooling (AGENTS.md default image)
# ghcr.io/actions/     — GitHub-hosted action containers (pages, attestations)
# ghcr.io/hadolint/    — Dockerfile/Containerfile linter
approved_registry(ref) if startswith(ref, "quay.io/fedora/")
approved_registry(ref) if startswith(ref, "dhi.io/")
approved_registry(ref) if startswith(ref, "ghcr.io/actions/")
approved_registry(ref) if startswith(ref, "ghcr.io/hadolint/")

# ── Rule 1: local context (no FROM pull) ─────────────────────────────────────
# Pure local builds (e.g. COPY-only layers) always pass.
allow if input.local

# ── Rule 2: approved + digest-pinned ─────────────────────────────────────────
# FROM must be from an approved registry AND pinned to an immutable digest.
# Mutable tags (:latest, :42) are rejected — tag reassignment is a supply chain
# attack vector. Pin to @sha256:... for repeatable input selection; two clean
# builds and payload comparison are still required to prove reproducibility.
#
# To pin quay.io/fedora/fedora-bootc:
#   skopeo inspect --format '{{.Digest}}' docker://quay.io/fedora/fedora-bootc:latest
#   → sha256:<hash>
#   Then in Containerfile: FROM quay.io/fedora/fedora-bootc@sha256:<hash>
allow if {
    approved_registry(input.image.ref)
    input.image.isCanonical
}

# ── Rule 3: provenance attestation (preferred, not yet required) ──────────────
# Uncomment to require SLSA provenance on all base images.
# Leave commented until quay.io/fedora/fedora-bootc ships provenance.
#
# allow if {
#     approved_registry(input.image.ref)
#     input.image.isCanonical
#     input.image.hasProvenance
# }

# ── Decision object (required by buildx policy evaluator) ────────────────────
decision := {
    "allow": allow,
    # Surface a human-readable reason on deny so the build log is actionable.
    "reason": reason,
}

# ── Default reason (keeps `decision` total so buildx's capability probe,
#    which evaluates with empty input, never gets a "zero result"). ──
default reason := "Build evaluated."

# ── Deny reasons ─────────────────────────────────────────────────────────────
reason := msg if {
    not input.local
    not approved_registry(input.image.ref)
    msg := sprintf(
        "Image '%v' is not from an approved registry. Allowed: quay.io/fedora/, dhi.io/, ghcr.io/actions/, ghcr.io/hadolint/",
        [input.image.ref],
    )
}

reason := msg if {
    not input.local
    approved_registry(input.image.ref)
    not input.image.isCanonical
    msg := sprintf(
        "Image '%v' uses a mutable tag. Pin to a digest: FROM %v@sha256:<hash>",
        [input.image.ref, input.image.ref],
    )
}

reason := "Build allowed." if allow
