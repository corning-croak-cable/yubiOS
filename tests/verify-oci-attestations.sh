#!/usr/bin/env bash
# tests/verify-oci-attestations.sh
#
# OMN-157: verifies that a published yubiOS OCI artifact carries:
#   1. A cosign keyless signature (GitHub Actions OIDC, identity pinned to the
#      exact workflow file that built it)
#   2. A cosign-attached SPDX SBOM attestation (cosign attest --type spdxjson)
#   3. A cosign-attached SLSA v1.0 provenance attestation (--type slsaprovenance1)
#   4. The original BuildKit attestation children (provenance + sbom) on the
#      OCI index, retrievable via `docker buildx imagetools inspect`.
#
# Always verifies against the immutable digest, never against a mutable tag.
# Identity regex anchors to yubiOS workflows specifically — no third party
# GitHub workflow can satisfy the issuer alone.
#
# Rekor inclusion has a brief lag after cosign sign/attest (the entry has to
# be appended to a tile and the tile checkpoint has to co-sign). Wrap each
# cosign call in a bounded retry (3 x 20s) to avoid intermittent red.
#
# Per the GitHub secret-scan quirk (sigstore/cosign#3602), some cosign calls
# hang when stdout is a TTY on a GHA runner. We write each payload to a file
# first and only emit a one-line status to stdout.
#
# Usage:
#   IMAGE_REF=0mniteck/yubios@sha256:... tests/verify-oci-attestations.sh
#   IMAGE_REF=0mniteck/yubios@sha256:... REGISTRY=... WORKFLOW_FILES=... \
#     tests/verify-oci-attestations.sh

set -euo pipefail

if [ -z "${IMAGE_REF:-}" ]; then
    echo "::error::IMAGE_REF is required (digest-pinned image reference)" >&2
    exit 64
fi

# Allow overriding the identity regex for tests; default anchors to the three
# OMN-157 publisher workflows in this repo.
WORKFLOW_FILES="${WORKFLOW_FILES:-yubiOS-ci|ci_dev_image|ci_mkosi-installer}"
IDENTITY_RE="^https://github\\.com/yubi-OS/yubiOS/\\.github/workflows/(${WORKFLOW_FILES})\\.yml@refs/(heads|tags)/.+\$"

WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

cosign_call() {
    # Retry a cosign invocation up to 3 times with 20s backoff to absorb Rekor
    # inclusion lag and transient tile-checkpoint races.
    local attempts=0
    local max_attempts=3
    while [ "$attempts" -lt "$max_attempts" ]; do
        if "$@" > "$WORK_DIR/last-stdout" 2> "$WORK_DIR/last-stderr"; then
            return 0
        fi
        attempts=$((attempts + 1))
        echo "::warning::cosign retry $attempts/$max_attempts after failure" >&2
        sleep 20
    done
    cat "$WORK_DIR/last-stderr" >&2
    return 1
}

cosign_init() {
    # cosign embeds a TUF root for Sigstore's public instance, but explicit
    # initialization makes first-run failures legible and lets us refresh
    # cached metadata on the rare case where the Sigstore TUF key rotates
    # between CI runs (~6 month cadence per the sigstore-rekor-v2 skill).
    if ! cosign_call cosign initialize; then
        echo "::error::cosign initialize failed" >&2
        return 1
    fi
}

check_signature() {
    local ref="$1"
    echo "Checking cosign signature on $ref ..."
    if ! cosign_call cosign verify \
        --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
        --certificate-identity-regexp "$IDENTITY_RE" \
        --certificate-github-workflow-repository "yubi-OS/yubiOS" \
        "$ref" > "$WORK_DIR/verify-sig" 2> "$WORK_DIR/verify-sig-err"; then
        echo "::error::cosign verify FAILED for $ref" >&2
        cat "$WORK_DIR/verify-sig-err" >&2
        return 1
    fi
    echo "  ✓ signature verified"
}

check_attestation() {
    local ref="$1"
    local type="$2"
    local predicate_type="$3"
    echo "Checking cosign-attached $type attestation on $ref (predicateType=$predicate_type) ..."
    cosign_call cosign verify-attestation \
        --type "$type" \
        --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
        --certificate-identity-regexp "$IDENTITY_RE" \
        --certificate-github-workflow-repository "yubi-OS/yubiOS" \
        "$ref" > "$WORK_DIR/verify-att" 2> "$WORK_DIR/verify-att-err"
    if [ ! -s "$WORK_DIR/verify-att" ]; then
        echo "::error::$type attestation missing for $ref" >&2
        cat "$WORK_DIR/verify-att-err" >&2
        return 1
    fi
    # Inspect the first attestation payload; require predicateType to match
    # and the SPDXID / SLSA buildDefinition to be present.
    if ! jq -e --arg pt "$predicate_type" \
        '.predicateType == $pt' "$WORK_DIR/verify-att" >/dev/null; then
        echo "::error::$type attestation predicateType mismatch (expected $predicate_type)" >&2
        head -c 1000 "$WORK_DIR/verify-att" >&2
        return 1
    fi
    case "$type" in
        spdxjson)
            if ! jq -e '.predicate.SPDXID and (.predicate.packages | length > 0)' \
                "$WORK_DIR/verify-att" >/dev/null; then
                echo "::error::SPDX attestation has no packages" >&2
                return 1
            fi
            echo "  ✓ SPDX SBOM attestation verified ($(jq '.predicate.packages | length' "$WORK_DIR/verify-att") packages)"
            ;;
        slsaprovenance1)
            if ! jq -e '.predicate.buildDefinition and .predicate.runDetails' \
                "$WORK_DIR/verify-att" >/dev/null; then
                echo "::error::SLSA v1 provenance attestation missing buildDefinition/runDetails" >&2
                return 1
            fi
            echo "  ✓ SLSA v1 provenance attestation verified"
            ;;
    esac
}

# BuildKit attaches attestations as index children with media type
# application/vnd.docker.attestation.manifest.v1+json. imagetools inspect exposes
# them under the SBOM/Provenance keys (or in the raw manifest when --format is
# not json).
check_buildkit_attestation() {
    local ref="$1"
    echo "Checking BuildKit-attached attestation children on $ref ..."
    # Pull the index raw JSON and look for an attestation-manifest child.
    local raw
    if ! raw="$(docker buildx imagetools inspect --raw "$ref" 2>"$WORK_DIR/bt-err")"; then
        echo "::error::imagetools inspect --raw failed for $ref" >&2
        cat "$WORK_DIR/bt-err" >&2
        return 1
    fi
    if ! jq -e '.manifests[] | select(.annotations["vnd.docker.reference.type"] == "attestation-manifest")' \
        "$raw" >/dev/null; then
        echo "::error::no BuildKit attestation-manifest children in $ref" >&2
        return 1
    fi
    echo "  ✓ BuildKit attestation children present"
}

main() {
    cosign_init

    check_signature "$IMAGE_REF"
    check_attestation "$IMAGE_REF" "spdxjson" "https://spdx.dev/Document"
    check_attestation "$IMAGE_REF" "slsaprovenance1" "https://slsa.dev/provenance/v1"
    check_buildkit_attestation "$IMAGE_REF"

    echo "All verifications PASSED for $IMAGE_REF"
}

main
