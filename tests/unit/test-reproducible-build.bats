#!/usr/bin/env bats

setup() {
    REPO_ROOT=$(cd -- "$BATS_TEST_DIRNAME/../.." && pwd -P)
    # shellcheck source=scripts/lib/reproducible-build.sh
    source "$REPO_ROOT/scripts/lib/reproducible-build.sh"
    unset SOURCE_DATE_EPOCH
}

@test "environment is derived from the selected commit" {
    configure_reproducible_build "$REPO_ROOT" HEAD amd64

    [ "$SOURCE_DATE_EPOCH" = "$(git -c safe.directory="$REPO_ROOT" -C "$REPO_ROOT" show -s --format=%ct HEAD)" ]
    [ "$SOURCE_DATE_ISO8601" = "$(date -u --date="@$SOURCE_DATE_EPOCH" '+%Y-%m-%dT%H:%M:%SZ')" ]
    [[ "$YUBIOS_MKOSI_SEED" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-5[0-9a-f]{3}-a[0-9a-f]{3}-[0-9a-f]{12}$ ]]
    [ "$TZ" = UTC ]
    [ "$PYTHONHASHSEED" = 0 ]
    [ "$KBUILD_BUILD_USER" = yubios ]
    [ "$KBUILD_BUILD_HOST" = reproducible ]
    [ "$TF_A_BUILD_TIMESTAMP" = "$KBUILD_BUILD_TIMESTAMP" ]
}

@test "commit metadata resolves from an Actions checkout with different ownership" {
    export GIT_TEST_ASSUME_DIFFERENT_OWNER=1

    configure_reproducible_build "$REPO_ROOT" HEAD arm64

    [ "$GIT_SHA" = "$(git -c safe.directory="$REPO_ROOT" -C "$REPO_ROOT" rev-parse HEAD)" ]
    [[ "$SOURCE_DATE_EPOCH" =~ ^[0-9]+$ ]]
}

@test "a conflicting caller epoch is rejected" {
    SOURCE_DATE_EPOCH=1
    run configure_reproducible_build "$REPO_ROOT" HEAD amd64

    [ "$status" -ne 0 ]
    [[ "$output" == *"does not match"* ]]
}

@test "mkosi seed is architecture scoped" {
    configure_reproducible_build "$REPO_ROOT" HEAD amd64
    amd64_seed=$YUBIOS_MKOSI_SEED
    unset SOURCE_DATE_EPOCH
    configure_reproducible_build "$REPO_ROOT" HEAD arm64

    [ "$amd64_seed" != "$YUBIOS_MKOSI_SEED" ]
}

@test "payload normalization fixes modes and mtimes" {
    configure_reproducible_build "$REPO_ROOT" HEAD amd64
    root="$BATS_TEST_TMPDIR/payload"
    mkdir -p "$root/sub"
    printf data > "$root/sub/file"
    chmod 0700 "$root/sub/file"

    normalize_reproducible_tree "$root"

    [ "$(stat -c %a "$root/sub")" = 755 ]
    [ "$(stat -c %a "$root/sub/file")" = 644 ]
    [ "$(stat -c %Y "$root/sub/file")" = "$SOURCE_DATE_EPOCH" ]
}

@test "builder setup is pinned and reusable, ARM64 proof is enforced, and manifests are stable" {
    run python3 - "$REPO_ROOT" <<'PY'
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
files = [
    *sorted((root / ".github/workflows").glob("*.yml")),
    root / "scripts/build-local-images.sh",
    root / "scripts/verify-reproducible-images.sh",
]
failures = []
bake = (root / "yubiOS-bake.hcl").read_text()
if not re.search(
    r'target "_image-export"\s*\{.*?type\s*=\s*"provenance".*?disabled\s*=\s*!PUSH',
    bake,
    re.S,
):
    failures.append("Docker exports do not disable provenance while registry exports retain it")
if not re.search(
    r'target "_image-export"\s*\{.*?BUILDKIT_MULTI_PLATFORM\s*=\s*PUSH\s*\?\s*"1"\s*:\s*"0"',
    bake,
    re.S,
):
    failures.append("Docker exports do not disable BuildKit manifest-list output")
if not re.search(
    r'target "_repro-export"\s*\{.*?BUILDKIT_MULTI_PLATFORM\s*=\s*"1"',
    bake,
    re.S,
):
    failures.append("OCI reproducibility exports do not retain deterministic multi-platform mode")
for path in files:
    text = path.read_text()
    for match in re.finditer(r"buildx create(?P<body>.{0,400}?)--use", text, re.S):
        body = match.group("body")
        if "--driver docker-container" in body and "--driver-opt" not in body:
            failures.append(f"{path.relative_to(root)} has an unpinned builder")
        line = text[match.end():].splitlines()[0]
        if "|| true" not in line:
            failures.append(f"{path.relative_to(root)} has a non-idempotent builder create")

for relative, report in (
    (".github/workflows/yubiOS-ci.yml", "production-arm64.json"),
    (".github/workflows/ci_dev_image.yml", "dev-arm64.json"),
):
    text = (root / relative).read_text()
    if "if: matrix.arch == 'arm64'" not in text or report not in text:
        failures.append(f"{relative} does not gate reproducibility evidence on ARM64")
    if "if: matrix.arch == 'amd64'" in text or report.replace("arm64", "amd64") in text:
        failures.append(f"{relative} still gates reproducibility evidence on amd64")

for relative in (
    ".github/workflows/ci_firmware-rk.yml",
    ".github/workflows/ci_mkosi-installer.yml",
    "scripts/lib/local-build-firmware.sh",
    "scripts/lib/local-build-installer.sh",
):
    if "workflow_run=" in (root / relative).read_text():
        failures.append(f"{relative} embeds workflow identity in a payload")

if failures:
    print("\n".join(failures), file=sys.stderr)
    raise SystemExit(1)
PY

    [ "$status" -eq 0 ]
}

@test "workflow jobs install git before checkout and reproducibility resolution" {
    run python3 - "$REPO_ROOT" <<'PY'
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
workflow_paths = (
    ".github/workflows/yubiOS-ci.yml",
    ".github/workflows/ci_dev_image.yml",
    ".github/workflows/ci_test_pq_tls_verify.yml",
    ".github/workflows/ci_mkosi-installer.yml",
    ".github/workflows/ci_firmware-rk.yml",
)
install = "apt-get install -y -qq --no-install-recommends git"
resolver = 'run: scripts/lib/reproducible-build.sh . "$GITHUB_SHA" "$ARCH" "$GITHUB_ENV"'
failures = []
resolver_jobs = 0

for relative in workflow_paths:
    text = (root / relative).read_text()
    jobs = text.split("jobs:\n", 1)[1]
    for match in re.finditer(r"(?ms)^  ([A-Za-z0-9_-]+):\n(.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)", jobs):
        job_name, body = match.groups()
        if resolver not in body:
            continue
        resolver_jobs += 1
        positions = (body.find(install), body.find("uses: actions/checkout@"), body.find(resolver))
        if not positions[0] < positions[1] < positions[2] or positions[0] < 0:
            failures.append(f"{relative}:{job_name} must install git before checkout and resolution")

unit_body = next(
    match.group(2)
    for match in re.finditer(
        r"(?ms)^  ([A-Za-z0-9_-]+):\n(.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)",
        (root / workflow_paths[0]).read_text().split("jobs:\n", 1)[1],
    )
    if match.group(1) == "unit-tests"
)
unit_positions = (unit_body.find(install), unit_body.find("uses: actions/checkout@"))
if not unit_positions[0] < unit_positions[1] or unit_positions[0] < 0:
    failures.append(f"{workflow_paths[0]}:unit-tests must install git before checkout")
if resolver_jobs != 9:
    failures.append(f"expected 9 resolver jobs, found {resolver_jobs}")

if failures:
    print("\n".join(failures), file=sys.stderr)
    raise SystemExit(1)
PY

    [ "$status" -eq 0 ]
}
