#!/usr/bin/env bats

setup() {
    REPO_ROOT=$(cd -- "$BATS_TEST_DIRNAME/../.." && pwd -P)
    # shellcheck source=scripts/lib/reproducible-build.sh
    source "$REPO_ROOT/scripts/lib/reproducible-build.sh"
    unset SOURCE_DATE_EPOCH
}

@test "environment is derived from the selected commit" {
    configure_reproducible_build "$REPO_ROOT" HEAD amd64

    [ "$SOURCE_DATE_EPOCH" = "$(git -C "$REPO_ROOT" show -s --format=%ct HEAD)" ]
    [ "$SOURCE_DATE_ISO8601" = "$(date -u --date="@$SOURCE_DATE_EPOCH" '+%Y-%m-%dT%H:%M:%SZ')" ]
    [[ "$YUBIOS_MKOSI_SEED" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-5[0-9a-f]{3}-a[0-9a-f]{3}-[0-9a-f]{12}$ ]]
    [ "$TZ" = UTC ]
    [ "$PYTHONHASHSEED" = 0 ]
    [ "$KBUILD_BUILD_USER" = yubios ]
    [ "$KBUILD_BUILD_HOST" = reproducible ]
    [ "$TF_A_BUILD_TIMESTAMP" = "$KBUILD_BUILD_TIMESTAMP" ]
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

@test "every docker-container builder is digest pinned and payload manifests are stable" {
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
for path in files:
    text = path.read_text()
    for match in re.finditer(r"buildx create(?P<body>.{0,400}?)--use", text, re.S):
        body = match.group("body")
        if "--driver docker-container" in body and "--driver-opt" not in body:
            failures.append(f"{path.relative_to(root)} has an unpinned builder")

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
