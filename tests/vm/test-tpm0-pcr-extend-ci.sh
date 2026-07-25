#!/usr/bin/env bash
# Phase F0 fTPM /dev/tpm0 + PCR-extend e2e for yubiOS CI.
#
# Thin CI driver around tests/vm/verify-tpm0-pcr-extend.sh, which is written to run
# INSIDE an already-booted guest. This script does what the other tests/vm/*-ci.sh
# entries do so the workflow step stays as dumb as the rest of them: drive
# `bcvk ephemeral run` here, wait for sshd, then execute the in-guest verifier over
# the shared bcvk SSH transport in tests/vm/bcvk-ssh-lib.sh.
#
#   TPM_MODE=swtpm  boot with bcvk --swtpm (software TPM; any runner)
#   TPM_MODE=real   boot with no vTPM flag, so the guest sees the platform's own TPM
#                   path (self-hosted ARM64 rock1 + OP-TEE fTPM)
#
# Exit codes: 0 = pass, 77 = explicit SKIP (this boot chain cannot support the leg),
# 1 = real failure. 77 matches the convention the other tests/vm CI entries already
# use, so ci_test-vm.yml handles all three the same way for every script.
#
# The verifier requires the ms-tpm-20-ref fTPM Early TA behind OP-TEE. A plain bcvk
# DirectBoot guest (with or without --swtpm) does not have it -- see
# tests/vm/build-arm64-ftpm-qemu.sh for the TF-A + OP-TEE + fTPM + U-Boot chain that
# does. Those cases SKIP loudly rather than hanging or dying without output.
set -euo pipefail

IMAGE="${YUBIOS_IMAGE:-./mkosi.output/yubiOS}"
TPM_MODE="${TPM_MODE:-swtpm}"
SSH_WAIT_SECS="${YUBIOS_SSH_WAIT_SECS:-300}"
VMID=""
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=tests/vm/bcvk-ssh-lib.sh
. "${SCRIPT_DIR}/bcvk-ssh-lib.sh"

log()  { printf '\n=== %s ===\n' "$*"; }
skip() { printf 'SKIP: %s\n' "$*"; }
die()  { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || die "missing host tool: $1"; }

skip_unsupported_zboot() {
  skip "bcvk/QEMU cannot DirectBoot this ARM64 EFI zboot kernel because it is zstd-compressed; use a bcvk/QEMU build with EFI zboot zstd support. See refs/zstd-efi-zboot-bcvk.md."
  exit 77
}

BCVK_EXTRA_ARGS=()
if [[ -n "${BCVK_EPHEMERAL_EXTRA_ARGS:-}" ]]; then
  read -r -a BCVK_EXTRA_ARGS <<<"${BCVK_EPHEMERAL_EXTRA_ARGS}"
fi

TPM_ARGS=()
case "$TPM_MODE" in
  swtpm) TPM_ARGS=(--swtpm) ;;
  real)  TPM_ARGS=() ;;
  *)     die "unknown TPM_MODE: ${TPM_MODE} (expected 'swtpm' or 'real')" ;;
esac

cleanup() { [[ -n "$VMID" ]] && podman rm -f "$VMID" >/dev/null 2>&1 || true; }
trap cleanup EXIT

# ---- host preflight ----
log "host preflight (TPM_MODE=${TPM_MODE})"
need bcvk
need base64
need podman
if [[ "$TPM_MODE" == "swtpm" ]]; then
  bcvk ephemeral run --help 2>&1 | grep -q -- '--swtpm' || die "pinned bcvk source lacks --swtpm"
  command -v swtpm >/dev/null 2>&1 || skip "host swtpm not found; --swtpm may fail to attach a vTPM"
fi

# ---- boot ----
log "boot ephemeral VM (TPM_MODE=${TPM_MODE})"
VMID="$(bcvk ephemeral run \
  ${BCVK_EXTRA_ARGS[@]+"${BCVK_EXTRA_ARGS[@]}"} \
  ${TPM_ARGS[@]+"${TPM_ARGS[@]}"} \
  --detach --ssh-keygen "$IMAGE")"
[[ -n "$VMID" ]] || die "bcvk ephemeral run returned no VM id"
echo "VM id: $VMID"

if ! wait_for_bcvk_ssh "$VMID" "$SSH_WAIT_SECS"; then
  logs="$(bcvk_podman_logs_tail "$VMID" 200)"
  if grep -Fq 'unable to handle EFI zboot image with "zstd" compression' <<<"$logs"; then
    skip_unsupported_zboot
  fi
  die "guest did not become reachable over ssh after ${SSH_WAIT_SECS}s"
fi

# ---- in-guest verifier ----
# bcvk_ssh runs `podman exec` without -i, so guest stdin is not connected; ship the
# verifier as a base64 argument instead of piping it.
log "in-guest: verify-tpm0-pcr-extend.sh (TPM_MODE=${TPM_MODE})"
VERIFY_B64="$(base64 -w0 "${SCRIPT_DIR}/verify-tpm0-pcr-extend.sh")"
set +e
OUTPUT="$(bcvk_ssh "$VMID" bash -c "echo ${VERIFY_B64} | base64 -d >/tmp/verify-tpm0-pcr-extend.sh && chmod +x /tmp/verify-tpm0-pcr-extend.sh && /tmp/verify-tpm0-pcr-extend.sh" 2>&1)"
rc=$?
set -e
printf '%s\n' "$OUTPUT"

if [[ "$rc" -ne 0 ]]; then
  if grep -Fq 'FAIL (no OP-TEE driver)' <<<"$OUTPUT"; then
    skip "guest has no OP-TEE driver: the verifier needs the ms-tpm-20-ref fTPM Early TA behind OP-TEE, which a bcvk DirectBoot guest does not provide (see tests/vm/build-arm64-ftpm-qemu.sh)."
    exit 77
  fi
  if grep -Fq 'FAIL (tpm_ftpm_tee not bound)' <<<"$OUTPUT"; then
    skip "guest exposes no /dev/tpm0 under TPM_MODE=${TPM_MODE}: tpm_ftpm_tee is not bound in this boot chain."
    exit 77
  fi
  die "verify-tpm0-pcr-extend.sh failed (rc=${rc}) under TPM_MODE=${TPM_MODE}"
fi

log "PASS: /dev/tpm0 live and PCR extend verified (TPM_MODE=${TPM_MODE})"
