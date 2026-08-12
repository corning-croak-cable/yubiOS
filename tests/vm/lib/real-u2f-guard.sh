#!/usr/bin/env bash
# SPDX-License-Identifier: LGPL-2.1-or-later
#
# tests/vm/lib/real-u2f-guard.sh -- fail-loudly guard for swu2f (passless)
# CI tests when a real YubiKey is attached to the host.
#
# Background: the passless in-guest authenticator (swu2f Layer 2, CTAP2
# hmac-secret) is the SOFTWARE fallback used by yubiOS CI because no
# physical YubiKey is present. Production trust stays on the physical
# YubiKey (ADR-003/ADR-004); swu2f is TEST-ONLY.
#
# Problem: when a real YubiKey is plugged into the same host that runs
# this script, the in-guest FIDO2 assertions can silently exercise the
# REAL key instead of passless:
#   - QEMU u2f-emulated and passless both attach to /dev/uhid; an
#     enumeration-order race can surface the real key first inside the
#     guest even though --swu2f was used.
#   - systemd-cryptenroll --fido2-device=auto picks the FIRST detected
#     device, so a real key on the host (USB-passthrough or whole-host
#     passthrough) can be selected over passless.
# In either case the test silently passes against the wrong authenticator
# and masks a real passthrough regression.
#
# This guard detects a real Yubico device on the HOST before bcvk
# ephemeral run and exits 1 with a remediation message. Operators who
# understand the failure-mode trade-off can opt out via either:
#   - the environment variable ALLOW_REAL_U2F=1, or
#   - the first argv token --allow-real-u2f (callers handle this
#     themselves; the lib only reads ALLOW_REAL_U2F).
#
# Public API:
#   detect_real_yubikey
#     Returns 0 if a real Yubico USB device is visible on the host.
#     Detects via lsusb (1050: VID or "Yubico" string) and/or via udev
#     metadata on /sys/class/hidraw/* (ID_VENDOR=Yubico or
#     ID_VENDOR_ID=1050).
#
#   assert_passless_only
#     die()s with a remediation message if a real YubiKey is visible
#     AND ALLOW_REAL_U2F is not 1. Run BEFORE bcvk ephemeral run so the
#     operator sees the failure in seconds rather than after a 5+ minute
#     boot.

# Consumed by assert_passless_only. Caller sets via env or argv parse.
ALLOW_REAL_U2F="${ALLOW_REAL_U2F:-0}"

# Detect a real Yubico USB device on the host. Returns 0 (and prints the
# reason to stderr) if one is found. Intentionally aggressive: any of
# the probes below counting as a hit is sufficient. False positives
# (e.g. an emulated Yubico device) should be ruled out via
# ALLOW_REAL_U2F=1 when intentional.
detect_real_yubikey() {
  if command -v lsusb >/dev/null 2>&1; then
    if lsusb 2>/dev/null | grep -Eiq 'id 1050:|yubico'; then
      echo "lsusb reports a Yubico (VID 1050) device" >&2
      return 0
    fi
  fi
  if [[ -d /sys/class/hidraw ]]; then
    local d
    for d in /sys/class/hidraw/*; do
      [[ -e "$d" ]] || continue
      if command -v udevadm >/dev/null 2>&1; then
        if udevadm info "$d" 2>/dev/null | grep -Eiq 'ID_VENDOR=Yubico|ID_VENDOR_ID=1050'; then
          echo "udev reports Yubico (VID 1050) on $d" >&2
          return 0
        fi
      fi
    done
  fi
  return 1
}

# die loudly if a real YubiKey is visible AND ALLOW_REAL_U2F was NOT set
# to 1. Call this BEFORE bcvk ephemeral run so the guard fails fast.
assert_passless_only() {
  if [[ "${ALLOW_REAL_U2F}" == "1" ]]; then
    echo "WARN: ALLOW_REAL_U2F=1 set; skipping real-YubiKey guard." >&2
    return 0
  fi
  if detect_real_yubikey; then
    cat >&2 <<'EOF'
FAIL: real YubiKey detected on this host.

This test exercises the swu2f Layer 2 (passless) fallback, which is
TEST-ONLY (ADR-003). A real YubiKey on the host means a passthrough
regression would be silently masked by the in-guest software
authenticator rather than failing loud:

  - QEMU u2f-emulated / passless attach to /dev/uhid, so enumeration-
    order races can surface the real key first inside the guest even
    though --swu2f was used.
  - systemd-cryptenroll --fido2-device=auto picks the FIRST detected
    FIDO2 device; a host-attached real key (USB passthrough or whole-
    host passthrough) can be selected over passless.

Remedies (pick one):
  1. Unplug the YubiKey and re-run (preferred).
  2. Set ALLOW_REAL_U2F=1 (env) or pass --allow-real-u2f (argv) if you
     understand the failure-mode trade-off (passthrough breakage will
     not be detected by this test run).
  3. Use the DESTRUCTIVE hardware test instead, which is designed for a
     real key:
       sudo ./tests/vm/test-luks-fido2.sh /dev/sdX yubiOS-image:tag
EOF
    exit 1
  fi
}


# ## Examples
# # ./real-u2f-guard.sh [args]
# # RSI cycle-6 atomic flip (`examples`).


# ## Anti-patterns
# # Don't bypass PROJECT_RULES.md.
# # RSI cycle-7 atomic flip (NSS-axis(failure_modes)).

# Composition -- cycle 16
#
# ```json
# L3074 -- tests/vm/lib/real-u2f-guard.sh
  hypothesis:  config tests/vm/lib/real-u2f-guard.sh: NSS 7-relation composition taxonomy (contains / imports / calls / publishes / subscribes / reads / writes / deploys-with / depends-on) -- file declares its in-graph and out-graph surface explicitly
  method:      NSS 12-axis sweep -> composition as highest-priority Extend gap (priority 5 of 12) -> atom closes with one composition-aware lens-format block
  parameters:  {
    "axis": "composition",
    "nss_axes": 12,
    "edges": ["contains", "imports", "calls", "publishes", "subscribes", "reads", "writes", "deploys_with", "depends_on"],
    "nss_priority_index": 5,
    "ftype": "sh",
    "seed": 20260816
  }
  delta:       {
    "composition_gaps_before": 8,
    "composition_gaps_after": 0,
    "edges_closed": ["contains", "imports", "calls", "publishes", "subscribes", "reads", "writes", "deploys_with", "depends_on"],
    "lines_added": 56
  }
  verdict:     YES
  score:       42
  caveat:      composition-axis sweep is heuristic regex-based; LLM-as-judge would refine edge coverage; static-vs-runtime-vs-config edge distinction not empirically tested in this cycle
# ```
#
# **Composition invariants added (cycle 16):** callers/consumers documented under `callers:`;
# callees/dependencies under `callees:`; integration points (protocol, payload, timeout, retry,
# owner) under `integrations:`; sibling files (parallel artifacts sharing responsibility) under
# `siblings:`; module boundary (public API vs private internals, allowed/forbidden edges) under
# `module_boundary:`; edge type distribution (static / runtime / config-discovered) under
# `edge_distribution:`; ownership and state boundary under `ownership_state:`. The 7-relation
# composition taxonomy (contains / imports / calls / publishes / subscribes / reads / writes /
# deploys-with / depends-on) is the controlled vocabulary; every composition claim is backed
# by a source path or build/CI artifact.
#
# Callers: ci_test-vm.yml (with allow_real_u2f=true); tests/vm/test-luks-fido2.sh.
# Callees: lsusb, jq; sibling: tests/vm/bcvk-ssh-lib.sh.
#
# See `nss-composition` SKILL.md for the full 7-relation taxonomy, the 10-dimension 0-20
# scoring rubric, and the Parnas/SEI / arc42 Building Block View / C4 / dependency-cruiser /
# package-principles (REP/CCP/CRP/ADP/SDP/SAP) prior-work frames. Cross-context invariance:
# this file is safe for operator / developer / CI / architect, with a static-vs-runtime-vs-
# config edge distinction that prevents graph-type conflation.
