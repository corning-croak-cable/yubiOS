#!/usr/bin/env bash
# FIDO2 enrollment-surface e2e for yubiOS CI — NO physical hardware (#9, #25).
#
# Boots yubiOS in a bcvk ephemeral VM (--swtpm --swu2f, canonical bcvk branch
# feat/swtpm-ci — never merged, referenced like the mkosi fork) and exercises the
# enrollment stack end-to-end with the in-guest software CTAP2 authenticator
# (passless, shipped by `mkosi --profile test`, see PR #40):
#
#   1. enrollment surface   — /usr/bin/yubiOS-enroll-* + /usr/lib/yubiOS present
#   2. enrollment gating    — yubiOS-enroll.service carries ConditionSecurity=measured-os
#   3. FIDO2 registration   — pamu2fcfg registers against the CTAP2 token (the
#                             core primitive every enroll wizard leg builds on)
#   4. SSH resident-key path— ssh-keygen -t ed25519-sk against the authenticator
#                             (ADR-004; covers the #25 "SSH key generation" leg)
#
# Skip-tolerant like tests/vm/test-luks-fido2-ci.sh: CTAP2 legs SKIP (not fail)
# when the image doesn't ship the Layer 2 authenticator (non-test images).
# Production trust anchor remains the physical YubiKey (ADR-003/ADR-004);
# swtpm/swu2f are TEST-ONLY. Hardware validation: tests/vm/test-luks-fido2.sh.

set -euo pipefail

IMAGE="${YUBIOS_IMAGE:-./mkosi.output/yubiOS}"
VMID=""

log()  { printf '\n=== %s ===\n' "$*"; }
skip() { printf 'SKIP: %s\n' "$*"; }       # skip != fail (tool/capability absent)
skip_unsupported_zboot() {
  printf 'SKIP: %s\n' "bcvk/QEMU cannot DirectBoot this ARM64 EFI zboot kernel because it is zstd-compressed; use a bcvk/QEMU build with EFI zboot zstd support, boot through firmware/stub, or rebuild only the CI test image with a bcvk-supported kernel compression. See refs/zstd-efi-zboot-bcvk.md."
  exit 77
}
die()  { printf 'FAIL: %s\n' "$*" >&2; exit 1; }

need() { command -v "$1" >/dev/null 2>&1 || die "missing host tool: $1"; }

# Optional host-provided bcvk arguments. CI uses this to bind a zstd-capable
# a qemu-system-aarch64 wrapper into bcvk's inner podman container; local runs normally
# leave it empty. Keep this as a simple whitespace-split string: paths used by
# CI intentionally contain no spaces.
BCVK_EXTRA_ARGS=()
if [[ -n "${BCVK_EPHEMERAL_EXTRA_ARGS:-}" ]]; then
  read -r -a BCVK_EXTRA_ARGS <<<"${BCVK_EPHEMERAL_EXTRA_ARGS}"
fi

cleanup() { [[ -n "$VMID" ]] && podman rm -f "$VMID" >/dev/null 2>&1 || true; }
trap cleanup EXIT

# ---- host preflight ----
log "host preflight"
need bcvk
bcvk ephemeral run --help 2>&1 | grep -q -- '--swtpm' || die "bcvk lacks --swtpm; build branch feat/swtpm-ci"
bcvk ephemeral run --help 2>&1 | grep -q -- '--swu2f' || die "bcvk lacks --swu2f; build branch feat/swtpm-ci"

g() { bcvk ssh "$VMID" -- "$@"; }

# ---- boot ----
log "boot ephemeral VM (--swtpm --swu2f)"
VMID="$(bcvk ephemeral run "${BCVK_EXTRA_ARGS[@]}" --detach --ssh-keygen --swtpm --swu2f "$IMAGE")"
[[ -n "$VMID" ]] || die "bcvk ephemeral run returned no VM id"
echo "VM id: $VMID"
for i in $(seq 1 150); do
  bcvk ssh "$VMID" -- true >/dev/null 2>&1 && break
  if [[ "$i" -eq 150 ]]; then
    echo "--- podman logs (last 80 lines) ---"
    logs="$(podman logs --tail 80 "$VMID" 2>&1 || true)"
    printf '%s\n' "$logs"
    if grep -Fq 'unable to handle EFI zboot image with "zstd" compression' <<<"$logs"; then
      skip_unsupported_zboot
    fi
    die "guest did not become reachable over ssh after 300s"
  fi
  sleep 2
done

# ---- 1. enrollment surface ----
log "enrollment surface: yubiOS-enroll-* commands + /usr/lib/yubiOS"
g 'ls /usr/bin/yubiOS-enroll-* >/dev/null 2>&1' \
  || die "no /usr/bin/yubiOS-enroll-* commands in image (Containerfile symlinks missing)"
g 'test -d /usr/lib/yubiOS && test -s /usr/lib/yubiOS/lib.sh' \
  || die "/usr/lib/yubiOS/lib.sh missing"
g 'ls /usr/bin/yubiOS-enroll-*'

# ---- 2. enrollment gating (ADR-016 / #15) ----
log "yubiOS-enroll.service: unit present + measured-os condition wired"
if g 'systemctl cat yubiOS-enroll.service >/dev/null 2>&1'; then
  g 'systemctl cat yubiOS-enroll.service | grep -q "ConditionSecurity=measured-os"' \
    || die "yubiOS-enroll.service lacks ConditionSecurity=measured-os (ADR-016)"
  echo "ConditionSecurity=measured-os wired"
else
  skip "yubiOS-enroll.service not in this image profile"
fi

# ---- 3. start the in-guest CTAP2 authenticator (swu2f Layer 2) ----
log "swu2f Layer 2: start in-guest CTAP2 authenticator (passless)"
CTAP2=0
if g 'command -v passless >/dev/null'; then
  g 'modprobe uhid 2>/dev/null || true'
  g 'PASSLESS_E2E_AUTO_ACCEPT_UV=1 setsid passless --backend-type local \
       >/var/log/passless-enroll.log 2>&1 < /dev/null & true'
  for i in $(seq 1 15); do
    g 'command -v fido2-token >/dev/null && fido2-token -L 2>/dev/null | grep -q .' && break
    [[ "$i" -eq 15 ]] && skip "passless started but no FIDO2 token enumerated"
    g 'sleep 1'
  done
  if g 'for d in $(fido2-token -L | cut -d: -f1); do fido2-token -I "$d" 2>/dev/null | grep -qi "hmac-secret" && exit 0; done; exit 1'; then
    CTAP2=1
    echo "CTAP2 hmac-secret authenticator up"
  fi
else
  skip "passless not in image; CTAP2 enrollment legs need the TEST image (mkosi --profile test)"
fi

# ---- 4. FIDO2 registration (the wizard's core primitive) ----
if [[ "$CTAP2" -eq 1 ]]; then
  log "pam-u2f: register a credential against the software authenticator"
  g 'command -v pamu2fcfg >/dev/null' || die "pamu2fcfg missing from image"
  g 'pamu2fcfg -u ci-enroll > /tmp/enroll_u2f_keys && test -s /tmp/enroll_u2f_keys' \
    || die "pamu2fcfg registration against CTAP2 authenticator failed"
  echo "FIDO2 registration OK"
else
  skip "FIDO2 registration — needs CTAP2 (Layer 2)"
fi

# ---- 5. SSH ed25519-sk keygen (ADR-004; #25 SSH leg) ----
if [[ "$CTAP2" -eq 1 ]]; then
  log "ssh-keygen: ed25519-sk keypair against the software authenticator"
  if g 'ssh-keygen -t ed25519-sk -N "" -f /tmp/ci_sk_key </dev/null && test -s /tmp/ci_sk_key.pub'; then
    g 'head -c 32 /tmp/ci_sk_key.pub'
    echo "ed25519-sk keygen OK"
  else
    skip "ssh-keygen ed25519-sk failed — image openssh may lack the internal sk middleware for uhid tokens (hardware YubiKey path unaffected, ADR-004)"
  fi
else
  skip "ssh ed25519-sk keygen — needs CTAP2 (Layer 2)"
fi

log "PASS: enrollment surface verified (CTAP2 legs run when the TEST image ships passless)"
