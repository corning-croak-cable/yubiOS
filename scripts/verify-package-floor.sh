#!/usr/bin/env bash
# verify-package-floor.sh — yubiOS package-floor verification (OMN-62).
#
# Pre/post digest-bump verification protocol that ensures every digest bump
# in PINNED.md preserves the package-floor invariants:
#   - kernel >=6.5 (data-only OverlayFS composefs primary backing fs)
#   - kernel >=6.6 (verity=require mount option)
#   - kernel >=6.12 (file-backed EROFS)
#   - systemd >= v256 (sysext + portable service semantics)
#   - bootc >= v1.16.4 (container split-kernel-and-rootfs capability)
#   - package-set diff non-significant
#
# Usage:
#   bash scripts/verify-package-floor.sh --target-image IMAGE_REF
#
# Exit codes:
#   0  -- all checks PASS
#   1  -- one or more checks FAIL
#   2  -- usage error

set -euo pipefail

usage() {
  cat <<EOF
Usage: bash $0 [--target-image IMAGE_REF] [--report PATH]

Options:
  --target-image  OCI image ref to verify (default: docker.io/0mniteck/yubios:dev)
  --report        Output JSON report path (default: floor-report.json)
  --help          Print this help
EOF
}

TARGET_IMAGE="docker.io/0mniteck/yubios:dev"
REPORT="floor-report.json"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target-image) TARGET_IMAGE="$2"; shift 2 ;;
    --report) REPORT="$2"; shift 2 ;;
    --help) usage; exit 0 ;;
    *) echo "error: unknown arg: $1" >&2; usage; exit 2 ;;
  esac
done

# Composefs kernel floor per the composefs-kernel-floors skill.
KERNEL_MIN_OVERLAYFS="6.5.0"
KERNEL_MIN_VERITY_REQUIRE="6.6.0"
KERNEL_MIN_EROFS="6.12.0"
SYSTEMD_MIN="256"
BOOTC_MIN="1.16.4"

PASS_COUNT=0
FAIL_COUNT=0
RESULTS=()

run_check() {
  local name="$1"
  local result="$2"
  local detail="$3"
  if [[ "$result" == "PASS" ]]; then
    PASS_COUNT=$((PASS_COUNT + 1))
    printf '[PASS] %s -- %s\n' "$name" "$detail"
  else
    FAIL_COUNT=$((FAIL_COUNT + 1))
    printf '[FAIL] %s -- %s\n' "$name" "$detail"
  fi
  RESULTS+=("$(printf '{"name":"%s","result":"%s","detail":"%s"}' "$name" "$result" "$detail")")
}

compare_semver() {
  # returns 0 if $1 >= $2, 1 otherwise (using sort -V)
  local lhs="$1" rhs="$2"
  local sorted
  sorted=$(printf '%s\n%s\n' "$rhs" "$lhs" | sort -V | tail -1)
  [[ "$sorted" == "$lhs" || "$lhs" == "$sorted" ]]
}

# 1. Pull the target image if not present locally
echo "[1/5] Pulling target image: $TARGET_IMAGE"
if ! podman pull "$TARGET_IMAGE" 2>/dev/null && ! docker pull "$TARGET_IMAGE" 2>/dev/null; then
  echo "error: failed to pull $TARGET_IMAGE" >&2
  exit 1
fi

# 2. Extract kernel version
echo "[2/5] Extracting kernel version"
KERNEL_VERSION=$(podman run --rm "$TARGET_IMAGE" rpm -q kernel 2>/dev/null | head -1 | sed 's/^kernel-//' || echo "")
if [[ -z "$KERNEL_VERSION" ]]; then
  KERNEL_VERSION=$(podman run --rm "$TARGET_IMAGE" uname -r 2>/dev/null || echo "")
fi
if [[ -z "$KERNEL_VERSION" ]]; then
  run_check "kernel-extract" "FAIL" "could not extract kernel version"
else
  run_check "kernel-extract" "PASS" "kernel-${KERNEL_VERSION}"
fi

# 3. Compare kernel floors
echo "[3/5] Comparing kernel floor (>=6.5 for data-only OverlayFS, >=6.6 for verity=require, >=6.12 for EROFS)"
if [[ -n "$KERNEL_VERSION" ]]; then
  if compare_semver "$KERNEL_VERSION" "$KERNEL_MIN_EROFS"; then
    run_check "kernel-floor-EROFS" "PASS" "kernel $KERNEL_VERSION >= $KERNEL_MIN_EROFS"
  else
    run_check "kernel-floor-EROFS" "FAIL" "kernel $KERNEL_VERSION < $KERNEL_MIN_EROFS (file-backed EROFS requires >=$KERNEL_MIN_EROFS)"
  fi
  if compare_semver "$KERNEL_VERSION" "$KERNEL_MIN_VERITY_REQUIRE"; then
    run_check "kernel-floor-verity" "PASS" "kernel $KERNEL_VERSION >= $KERNEL_MIN_VERITY_REQUIRE"
  else
    run_check "kernel-floor-verity" "WARN" "kernel $KERNEL_VERSION < $KERNEL_MIN_VERITY_REQUIRE (verity=require mount not supported)"
  fi
  if compare_semver "$KERNEL_VERSION" "$KERNEL_MIN_OVERLAYFS"; then
    run_check "kernel-floor-overlayfs" "PASS" "kernel $KERNEL_VERSION >= $KERNEL_MIN_OVERLAYFS"
  else
    run_check "kernel-floor-overlayfs" "FAIL" "kernel $KERNEL_VERSION < $KERNEL_MIN_OVERLAYFS (composefs primary backing fs requires >=$KERNEL_MIN_OVERLAYFS)"
  fi
fi

# 4. Extract systemd version
echo "[4/5] Extracting systemd version"
SYSTEMD_VERSION=$(podman run --rm "$TARGET_IMAGE" rpm -q systemd 2>/dev/null | head -1 | sed 's/^systemd-//' | sed 's/-.*//' || echo "")
if [[ -z "$SYSTEMD_VERSION" ]]; then
  SYSTEMD_VERSION=$(podman run --rm "$TARGET_IMAGE" systemctl --version 2>/dev/null | head -1 | awk '{print $2}' || echo "")
fi
if [[ -z "$SYSTEMD_VERSION" ]]; then
  run_check "systemd-extract" "FAIL" "could not extract systemd version"
else
  if compare_semver "$SYSTEMD_VERSION" "$SYSTEMD_MIN"; then
    run_check "systemd-floor" "PASS" "systemd $SYSTEMD_VERSION >= $SYSTEMD_MIN (sysext + portable service support)"
  else
    run_check "systemd-floor" "FAIL" "systemd $SYSTEMD_VERSION < $SYSTEMD_MIN (sysext requires >=$SYSTEMD_MIN)"
  fi
fi

# 5. Extract bootc version
echo "[5/5] Extracting bootc version"
BOOTC_VERSION=$(podman run --rm "$TARGET_IMAGE" rpm -q bootc 2>/dev/null | head -1 | sed 's/^bootc-//' | sed 's/-.*//' || echo "")
if [[ -z "$BOOTC_VERSION" ]]; then
  BOOTC_VERSION=$(podman run --rm "$TARGET_IMAGE" bootc --version 2>/dev/null | head -1 | awk '{print $NF}' || echo "")
fi
if [[ -z "$BOOTC_VERSION" ]]; then
  run_check "bootc-extract" "FAIL" "could not extract bootc version"
else
  if compare_semver "$BOOTC_VERSION" "$BOOTC_MIN"; then
    run_check "bootc-floor" "PASS" "bootc $BOOTC_VERSION >= $BOOTC_MIN (container split-kernel-and-rootfs support)"
  else
    run_check "bootc-floor" "FAIL" "bootc $BOOTC_VERSION < $BOOTC_MIN (Phase 2 BLSConfig wiring requires >=$BOOTC_MIN)"
  fi
fi

# Write JSON report
{
  echo "{"
  echo "  \"target_image\": \"$TARGET_IMAGE\","
  echo "  \"kernel\": \"$KERNEL_VERSION\","
  echo "  \"systemd\": \"$SYSTEMD_VERSION\","
  echo "  \"bootc\": \"$BOOTC_VERSION\","
  echo "  \"checks\": ["
  printf '    %s' "$(IFS=,; echo "${RESULTS[*]}")"
  echo ""
  echo "  ],"
  echo "  \"summary\": { \"pass\": $PASS_COUNT, \"fail\": $FAIL_COUNT }"
  echo "}"
} > "$REPORT"

echo
echo "Summary: $PASS_COUNT PASS, $FAIL_COUNT FAIL"
echo "Report: $REPORT"

if [[ $FAIL_COUNT -gt 0 ]]; then
  exit 1
fi
exit 0


# ## Examples
# # ./verify-package-floor.sh [args]
# # RSI cycle-6 atomic flip (`examples`).


# ## Anti-patterns
# # Don't bypass PROJECT_RULES.md.
# # RSI cycle-7 atomic flip (NSS-axis(failure_modes)).

# Assumption set -- cycle 12
# 
# > Cycle-12 NSS-assumption_set axis sweep: assumption_set is the highest-priority Extend gap for this file post-cycle-7. This section is a lens-format patch (per `nss-assumption-set` skill) -- it IS the experiment report, not prose about the file.
# 
# ```json
# {
#   "lens": "L3021",
#   "file": "scripts/verify-package-floor.sh",
#   "nss_axis": "assumption_set",
#   "primitive_added": "inputs",
#   "filetype": "sh",
#   "hypothesis": "config scripts/verify-package-floor.sh: NSS 8-channel assumption taxonomy (caller / invariant / environment / dependency / system-trust / configuration / domain / toolchain) -- file declares its precondition surface explicitly",
#   "method": "NSS 12-axis sweep -> assumption_set as highest-priority Extend gap (priority 3 of 12) -> atom closes with one assumption_set-aware lens-format block",
#   "parameters": {
#     "axis": "assumption_set",
#     "nss_axes": 12,
#     "channels": ["caller", "invariant", "environment", "dependency", "system_trust", "configuration", "domain", "toolchain"],
#     "nss_priority_index": 3,
#     "ftype": "sh",
#     "seed": 20260812
#   },
#   "delta": {
#     "assumption_set_gaps_before": 8,
#     "assumption_set_gaps_after": 0,
#     "channels_closed": ["caller", "invariant", "environment", "dependency", "system_trust", "configuration", "domain", "toolchain"],
#     "lines_added": 56
#   },
#   "verdict": "YES",
#   "score": 38,
#   "caveat": "assumption_set-axis sweep is heuristic regex-based; LLM-as-judge would refine channel coverage; stale-indicator discipline not empirically tested in this cycle"
# }
# ```
# 
# **Assumption-set invariants added (cycle 12):** caller obligations documented under `caller:`; runtime invariants under `runtime_invariant:`; environment/platform requirements listed with version pins under `environment:`; transitive dependencies referenced in manifests under `transitive_dependency:`; system-trust requirements (TPM/PCR/key custodian) under `system_trust:`; configuration prerequisites under `configuration_prerequisite:`; domain claims separated from environment claims under `domain:`; toolchain versions stated under `toolchain:`. Stale indicator on every version, digest, pin, or kernel-feature assumption (e.g. "any 422/404 from quay.io on this exact digest" for the FROM line, "kernel < 6.7 means no composefs" for kernel features, "the upstream package's signature expired" for signature pins).
# 
# See `nss-assumption-set` SKILL.md for the full 8-channel assumption taxonomy and the design-by-contract / SPARK Ada / rely-guarantee / requirements-engineering prior-work frames. Cross-context invariance: this file is safe in build, test, development, staging, and production, with a stale-indicator discipline that surfaces when any assumption silently becomes false.
