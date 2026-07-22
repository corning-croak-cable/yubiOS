#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
readonly SCRIPT_DIR
# shellcheck source=scripts/lib/reproducible-build.sh
source "$SCRIPT_DIR/lib/reproducible-build.sh"

die() {
    printf 'error: %s\n' "$*" >&2
    exit 1
}

usage() {
    printf 'Usage: %s production|dev\n' "$0"
}

cleanup() {
    local status=$?
    local builder

    trap - EXIT
    for builder in "${BUILDERS[@]:-}"; do
        docker buildx rm --force "$builder" >/dev/null 2>&1 || true
    done
    if [[ -n "${WORK_ROOT:-}" ]] && { ((status == 0)) || [[ "${KEEP_REPRO_OUTPUT:-0}" != 1 ]]; }; then
        rm -rf -- "$WORK_ROOT"
    elif [[ -n "${WORK_ROOT:-}" ]]; then
        printf 'Reproduction outputs retained at %s\n' "$WORK_ROOT" >&2
    fi
    exit "$status"
}

case "${1:-}" in
    production) bake_target=yubios-repro ;;
    dev) bake_target=yubios-dev-repro ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; die 'select production or dev' ;;
esac

command -v docker >/dev/null 2>&1 || die 'docker is required'
command -v jq >/dev/null 2>&1 || die 'jq is required'
docker buildx version >/dev/null 2>&1 || die 'docker buildx is required'

repo_root=$(cd -- "$SCRIPT_DIR/.." && pwd -P)
revision=$(git -C "$repo_root" rev-parse HEAD)
if ! git -C "$repo_root" diff --quiet || ! git -C "$repo_root" diff --cached --quiet; then
    die 'tracked files are dirty; reproducibility proof requires a clean revision'
fi

case "$(uname -m)" in
    x86_64) architecture=amd64 ;;
    aarch64|arm64) architecture=arm64 ;;
    *) die "unsupported architecture: $(uname -m)" ;;
esac
platform="linux/${architecture}"
configure_reproducible_build "$repo_root" "$revision" "$architecture"

WORK_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/yubios-repro.XXXXXX")
BUILDERS=("yubios-repro-a-$$" "yubios-repro-b-$$")
trap cleanup EXIT
cd "$repo_root"

for index in 0 1; do
    builder=${BUILDERS[$index]}
    run=$([[ $index == 0 ]] && printf a || printf b)
    output="$WORK_ROOT/$run"
    mkdir -p "$output"

    docker buildx create \
        --name "$builder" \
        --driver docker-container \
        --driver-opt "image=${YUBIOS_BUILDKIT_IMAGE}" \
        --use || true
    docker buildx inspect "$builder" --bootstrap

    ARCH=$architecture \
    PLATFORM=$platform \
    GIT_SHA=$GIT_SHA \
    SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH \
    SOURCE_DATE_ISO8601=$SOURCE_DATE_ISO8601 \
    REPRO_DEST=$output \
    PUSH=false \
    BUILDX_NO_DEFAULT_ATTESTATIONS=1 \
        docker buildx bake \
            --builder "$builder" \
            --file "$repo_root/yubiOS-bake.hcl" \
            --no-cache \
            --pull \
            "$bake_target"
    docker buildx rm --force "$builder"
done

for run in a b; do
    (
        cd "$WORK_ROOT/$run"
        find . -type f -print0 | LC_ALL=C sort -z | xargs -0r sha256sum
    ) > "$WORK_ROOT/$run.sums"
done
diff -u "$WORK_ROOT/a.sums" "$WORK_ROOT/b.sums"
cmp "$WORK_ROOT/a/index.json" "$WORK_ROOT/b/index.json"

manifest_digest=$(jq -er '.manifests[0].digest' "$WORK_ROOT/a/index.json")
manifest="$WORK_ROOT/a/blobs/sha256/${manifest_digest#sha256:}"
config_digest=$(jq -er '.config.digest' "$manifest")
config="$WORK_ROOT/a/blobs/sha256/${config_digest#sha256:}"
jq -e --arg expected "$SOURCE_DATE_ISO8601" \
    '.created == $expected and all(.history[]?; .created == null or .created == $expected)' \
    "$config" >/dev/null

report=${REPRO_REPORT:-$repo_root/reproducibility.json}
mkdir -p "$(dirname -- "$report")"
jq -n \
    --arg source "$GIT_SHA" \
    --arg epoch "$SOURCE_DATE_EPOCH" \
    --arg created "$SOURCE_DATE_ISO8601" \
    --arg architecture "$architecture" \
    --arg target "$bake_target" \
    --arg buildkit "$YUBIOS_BUILDKIT_IMAGE" \
    --arg manifest "$manifest_digest" \
    --arg config "$config_digest" \
    '{schema: 1, source: $source, source_date_epoch: ($epoch | tonumber), created: $created,
      architecture: $architecture, target: $target, buildkit: $buildkit,
      subject: {manifest: $manifest, config: $config}, isolated_builds: 2,
      cache: "disabled", attestations: "compared separately"}' > "$report"

printf 'PASS: two isolated %s builds produced OCI manifest %s\nEvidence: %s\n' \
    "$bake_target" "$manifest_digest" "$report"
