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

@test "checkout preflight Git operations trust a different owner" {
    export GIT_TEST_ASSUME_DIFFERENT_OWNER=1

    run reproducible_git "$REPO_ROOT" rev-parse "HEAD^{commit}"
    [ "$status" -eq 0 ]
    [ "$output" = "$(git -c safe.directory="$REPO_ROOT" -C "$REPO_ROOT" rev-parse HEAD)" ]

    run reproducible_git "$REPO_ROOT" diff --quiet
    [ "$status" -eq 0 ]
    run reproducible_git "$REPO_ROOT" diff --cached --quiet
    [ "$status" -eq 0 ]
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

@test "EDK2 stack-cookie seeds are deterministic and identity scoped" {
    configure_reproducible_build "$REPO_ROOT" HEAD arm64
    first="$BATS_TEST_TMPDIR/first"
    second="$BATS_TEST_TMPDIR/second"
    different="$BATS_TEST_TMPDIR/different"

    write_reproducible_edk2_stack_cookies "$first" edk2-platform
    write_reproducible_edk2_stack_cookies "$second" edk2-platform
    write_reproducible_edk2_stack_cookies "$different" other-platform

    cmp "$first/StackCookieValues32.json" "$second/StackCookieValues32.json"
    cmp "$first/StackCookieValues64.json" "$second/StackCookieValues64.json"
    ! cmp -s "$first/StackCookieValues64.json" "$different/StackCookieValues64.json"
    [ "$(stat -c %Y "$first/StackCookieValues64.json")" = "$SOURCE_DATE_EPOCH" ]

    run python3 - "$first" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
for bits in (32, 64):
    values = json.loads((root / f"StackCookieValues{bits}.json").read_text())
    assert len(values) == 100
    assert all(0 < value < 2**bits for value in values)
PY
    [ "$status" -eq 0 ]
}

@test "firmware proof compares unsigned components and records the QEMU envelope" {
    configure_reproducible_build "$REPO_ROOT" HEAD arm64
    proof_root="$BATS_TEST_TMPDIR/proof"
    report="$BATS_TEST_TMPDIR/firmware-qemu-arm64.json"

    python3 - "$proof_root" "$GIT_SHA" "$SOURCE_DATE_EPOCH" <<'PY'
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
source = sys.argv[2]
epoch = sys.argv[3]
for variant in ("primary", "rebuild"):
    tree = root / variant
    files = {
        "stmm/BL32_AP_MM.fd": b"stmm",
        "firmware/BL32_AP_MM.fd": b"stmm",
        "firmware/u-boot/u-boot.bin": b"uboot",
        "firmware/optee_os/out/arm-plat-vexpress/core/tee-header_v2.bin": b"header",
        "firmware/optee_os/out/arm-plat-vexpress/core/tee-pager_v2.bin": b"pager",
        "firmware/optee_os/out/arm-plat-vexpress/core/tee-pageable_v2.bin": b"",
        "firmware/optee_os/out/arm-plat-vexpress/core/tee.bin": b"tee-bin",
        "firmware/optee_os/out/arm-plat-vexpress/core/tee.elf": b"tee-elf",
        "firmware/arm-trusted-firmware/build/qemu/debug/fip.bin": f"fip-{variant}".encode(),
        "firmware/arm-trusted-firmware/build/qemu/debug/bl1.bin": f"bl1-{variant}".encode(),
        "firmware/arm-trusted-firmware/build/qemu/debug/bl31/bl31.elf": f"bl31-{variant}".encode(),
        "firmware/fip-info.txt": f"certificate-{variant}".encode(),
    }
    manifest = "\n".join(
        (
            "yubiOS ARM64 firmware build artifact",
            "board=qemu-arm64",
            "arch=arm64",
            f"yubios_commit={source}",
            f"source_date_epoch={epoch}",
            "signature_envelope=TF-A CREATE_KEYS=1; excluded from byte-for-byte proof",
            "",
        )
    ).encode()
    files["firmware/firmware-manifest.txt"] = manifest
    for relative, content in files.items():
        path = tree / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
PY

    run "$REPO_ROOT/scripts/verify-reproducible-firmware.py" \
        qemu-arm64 "$proof_root/primary" "$proof_root/rebuild" "$report"
    [ "$status" -eq 0 ]
    run python3 - "$report" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1]))
assert report["result"] == "match"
assert report["isolated_builds"] == 2
assert report["compared"]
assert report["excluded"]
assert any(not item["matched"] for item in report["excluded"])
PY
    [ "$status" -eq 0 ]

    printf drift > "$proof_root/rebuild/firmware/u-boot/u-boot.bin"
    run "$REPO_ROOT/scripts/verify-reproducible-firmware.py" \
        qemu-arm64 "$proof_root/primary" "$proof_root/rebuild" "$report"
    [ "$status" -ne 0 ]
    [[ "$output" == *"firmware/u-boot/u-boot.bin"* ]]
    run python3 - "$report" <<'PY'
import json
import sys

assert json.load(open(sys.argv[1]))["result"] == "mismatch"
PY
    [ "$status" -eq 0 ]
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
for relative in (
    "scripts/build-local-images.sh",
    "scripts/verify-reproducible-images.sh",
):
    if 'git -C "$repo_root"' in (root / relative).read_text():
        failures.append(f"{relative} bypasses command-scoped safe-directory trust")
bake = (root / "yubiOS-bake.hcl").read_text()
proof = (root / "scripts/verify-reproducible-images.sh").read_text()
firmware_proof = (root / "scripts/verify-reproducible-firmware.py").read_text()
diagnostic = root / "scripts/lib/diagnose-oci-layout.py"
containerfile = (root / "Containerfile").read_text()
passless = (root / "mkosi.conf.d/test/install-swu2f-authenticator.sh").read_text()
if '--allow "fs.write=$output"' not in proof:
    failures.append("OCI proof does not authorize its exact Bake output directory")
if "--setopt=history_record=false" not in containerfile:
    failures.append("production package install records nondeterministic DNF history")
if (
    "--no-compile" not in containerfile
    or "--invalidation-mode=checked-hash" not in containerfile
    or "compileall -f -q -j 1" not in containerfile
    or 'sysconfig.get_path("platlib")' not in containerfile
    or "/usr/local/lib/python*/site-packages/chipsec" in containerfile
    or "--quiet" in containerfile
):
    failures.append("CHIPSEC install does not regenerate deterministic Python bytecode")
if passless.count("--setopt=history_record=false") < 2:
    failures.append("passless build records nondeterministic DNF transactions")
for control in ("PASSLESS_BUILD_ROOT", "CARGO_INCREMENTAL=0", "--remap-path-prefix"):
    if control not in passless:
        failures.append(f"passless build lacks deterministic Rust control: {control}")
for state in (
    "/var/log/dnf*",
    "/var/cache/ldconfig/aux-cache",
    "/var/cache/libdnf5",
    "/var/lib/dnf/repos",
    "/usr/lib/sysimage/libdnf5/transaction_history.sqlite*",
):
    if state not in containerfile or state not in passless:
        failures.append(f"package-manager state is not removed from both image layers: {state}")
if not diagnostic.is_file() or "diagnose-oci-layout.py" not in proof:
    failures.append("OCI mismatch does not emit layer-level diagnostics")
if '--resolve "$WORK_ROOT/a"' not in proof:
    failures.append("OCI proof does not resolve BuildKit's nested image descriptor")
if "manifest_digest=$(jq -er '.manifests[0].digest'" in proof:
    failures.append("OCI proof still assumes the top-level descriptor is an image manifest")
if ".created == $expected)" in proof or "fromdateiso8601" not in proof:
    failures.append("OCI proof does not preserve valid inherited history timestamps")
if 'org.opencontainers.image.created"] == $expected' not in proof:
    failures.append("OCI proof does not verify its canonical creation annotation")
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
    if not re.search(
        r"Install docker CLI \+ buildx.*?apt-get install.*?python3.*?wcurl",
        text,
        re.S,
    ):
        failures.append(f"{relative} does not install the OCI diagnostic runtime")
    if "if: matrix.arch == 'amd64'" in text or report.replace("arm64", "amd64") in text:
        failures.append(f"{relative} still gates reproducibility evidence on amd64")

firmware_workflow = (root / ".github/workflows/ci_firmware-rk.yml").read_text()
if firmware_workflow.count("artifact_suffix: arm64-repro") != 4:
    failures.append("firmware workflow does not rebuild StandaloneMM and all three boards on ARM64")
if "write_reproducible_edk2_stack_cookies" not in firmware_workflow:
    failures.append("firmware workflow does not preseed deterministic EDK2 stack cookies")
if "write_reproducible_edk2_stack_cookies" not in (root / "scripts/lib/local-build-firmware.sh").read_text():
    failures.append("local firmware path does not share deterministic EDK2 stack cookies")
if "firmware-reproducibility:" not in firmware_workflow:
    failures.append("firmware workflow has no blocking component comparison job")
if "needs: [optee_fip, firmware-reproducibility]" not in firmware_workflow:
    failures.append("QEMU verification is not blocked on firmware reproducibility")
if 'repro-evidence/firmware-${{ matrix.board }}-arm64.json' not in firmware_workflow:
    failures.append("firmware workflow retains no board-scoped ARM64 evidence")
for board in ("qemu-arm64", "rockpro64-rk3399", "rock5b-rk3588"):
    if board not in firmware_workflow:
        failures.append(f"firmware proof matrix omits {board}")
if "CREATE_KEYS=1" not in firmware_proof or "SIGNED_QEMU_REASON" not in firmware_proof:
    failures.append("firmware proof does not preserve the QEMU signing boundary")

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
if resolver_jobs != 10:
    failures.append(f"expected 10 resolver jobs, found {resolver_jobs}")

if failures:
    print("\n".join(failures), file=sys.stderr)
    raise SystemExit(1)
PY

    [ "$status" -eq 0 ]
}

@test "OCI diagnostics resolve BuildKit's nested platform index" {
    run python3 - "$REPO_ROOT" "$BATS_TEST_TMPDIR" <<'PY'
import hashlib
import json
import pathlib
import runpy
import subprocess
import sys

root = pathlib.Path(sys.argv[1])
layout = pathlib.Path(sys.argv[2]) / "oci"
blobs = layout / "blobs" / "sha256"
blobs.mkdir(parents=True)

def put(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(encoded).hexdigest()
    (blobs / digest).write_bytes(encoded)
    return {"digest": f"sha256:{digest}", "size": len(encoded)}

config = {"architecture": "arm64", "os": "linux"}
config_descriptor = put(config)
manifest = {
    "schemaVersion": 2,
    "config": config_descriptor,
    "layers": [],
}
manifest_descriptor = put(manifest)
platform_index = {"schemaVersion": 2, "manifests": [manifest_descriptor]}
platform_descriptor = put(platform_index)
(layout / "index.json").write_text(
    json.dumps({"schemaVersion": 2, "manifests": [platform_descriptor]})
)

namespace = runpy.run_path(str(root / "scripts/lib/diagnose-oci-layout.py"))
_, resolved_manifest, resolved_config = namespace["resolve_image"](layout)
assert resolved_manifest == manifest
assert resolved_config == config
resolved = subprocess.run(
    [
        sys.executable,
        str(root / "scripts/lib/diagnose-oci-layout.py"),
        "--resolve",
        str(layout),
    ],
    check=True,
    text=True,
    stdout=subprocess.PIPE,
).stdout.strip()
assert resolved == f"{manifest_descriptor['digest']}\t{config_descriptor['digest']}"
PY

    [ "$status" -eq 0 ]
}
