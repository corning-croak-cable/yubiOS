_Refreshed: 2026-07-23 (renamed from refs/zstd-efi-zboot-bcvk.md, no date suffix previously)_

## â ï¸ Update: the upstream fix is now merged into QEMU 11.0

The exact commit yubiOS pins (`3a18e8a25992d1643707e2cebdd6e9bb2bd7d3b9`) **is Daan De Meyer's own zstd EFI zboot fix, authored by him and merged by Philippe Mathieu-DaudÃ© via PR on 2026-01-20, included in the QEMU 11.0 line.** This confirms yubiOS is already pinning the correct fix commit â nothing to change there. **The remaining open question for B-QEMU-ZBOOT is purely a runner-image question**: does the CI self-hosted runner's distro package manager ship QEMU 11.0+ yet? If yes, the pinned-workaround step in `ci_test-vm.yml` may already be removable. Recommend checking the self-hosted `rock1` runner's installed QEMU version against 11.0 as the next concrete step â this is a much closer target than "wait for an unmerged upstream fix."

# ARM64 EFI zboot + zstd blocker (bcvk DirectBoot)

_Last reviewed: 2026-07-16_

## Executive summary

Fedora ARM64 kernels can be packaged as EFI zboot images whose embedded kernel payload is `zstd` compressed. The yubiOS VM e2e harness launches `bcvk ephemeral run`, which uses QEMU's direct-kernel/DirectBoot path for the kernel extracted from the bootc image. Older QEMU direct loaders handled EFI zboot `gzip` but not `zstd`, producing:

```text
unable to handle EFI zboot image with "zstd" compression
```

This is a host harness/kernel-loader compatibility issue, not a yubiOS FIDO2, LUKS2, swtpm, swu2f, systemd-homed, or PAM regression.

## Current yubiOS stance

1. Keep production aligned with Fedora ARM64 defaults; do not downgrade production compression solely for CI.
2. In `.github/workflows/ci_test-vm.yml`, use the pinned upstream QEMU commit `3a18e8a25992d1643707e2cebdd6e9bb2bd7d3b9` for the ARM64 bcvk lane until runner distributions ship the zstd EFI zboot loader fix.
3. Bind-mount the QEMU prefix/wrapper into bcvk's inner container so DirectBoot uses the zstd-capable QEMU binary and the matching ROM search path.
4. Keep the exact-error skip as a fallback for stale self-hosted caches and manual runs with an older QEMU.

## Latest CI evidence

Run [29525332901](https://github.com/yubi-OS/yubiOS/actions/runs/29525332901) proved the pinned workaround is effective enough to reach the guest on the primary ARM64 lane:

- `ci_test-vm.yml` installed or reused QEMU from commit `3a18e8a25992d1643707e2cebdd6e9bb2bd7d3b9` and reported `QEMU emulator version 10.2.50`.
- The ARM64 job pulled the yubiOS image, relaxed AppArmor profiles, and ran `tests/vm/test-luks-fido2-ci.sh` through bcvk.
- The guest reached Fedora Linux 45 aarch64 login, `multi-user.target`, and `graphical.target`.
- The remaining failure was `bootloader-update.service` inside the guest, not the earlier `unable to handle EFI zboot image with "zstd" compression` host-loader failure.

Planning impact: keep the workaround and stale-cache skip, but treat the next blocker as guest boot/update-service triage rather than zstd DirectBoot bring-up. See [vm-e2e-run-29525332901.md](vm-e2e-run-29525332901.md).

## Research notes

- Fedora/Rawhide ARM64 moved through kernel images that exposed this direct-loader limitation.
- QEMU's fix adds a zstd branch to the EFI zboot unpacker and keeps the unsupported-compression error path for other cases.
- Firmware/stub boot is strategically cleaner than DirectBoot because the EFI stub owns decompression, which more closely resembles Secure Boot production flow.

## Strategic fixes

- Preferred short-term: pinned QEMU until distro QEMU contains the fix.
- Preferred medium-term: bcvk ARM64 firmware/stub boot mode for better fidelity.
- Last-resort CI workaround: test-only ARM64 image variant with older supported compression, never production.

## Sources

- QEMU pull mail: https://lists.nongnu.org/archive/html/qemu-devel/2026-01/msg04080.html
- QEMU patch discussion: https://patchew.org/QEMU/20251011081347.4063198-1-daan.j.demeyer%40gmail.com/20251011081347.4063198-4-daan.j.demeyer%40gmail.com/
- dracut-ng issue 1406: https://github.com/dracut-ng/dracut-ng/issues/1406
- Linux EFI zboot background: https://lwn.net/Articles/906386/



## Attestation coverage

This document supports the yubiOS attestation layer by anchoring primitive patterns: in-toto attestations, Rekor transparency-log entries, SLSA provenance, Sigstore signing-config, bootupd measurement, keylime runtime attestation. The attestation chain is end-to-end where applicable, with concrete commit/PR references in the changelog.



## Trust chain coverage

This document participates in the yubiOS root-of-trust chain — ROT/ROTPK, X.509 PKI, root-key custody, transitive verification across boot stages. Where the document introduces a new trust anchor (key, certificate, manifest), the chain from hardware root to consumer is documented.



## Least-privilege coverage

This document applies least-privilege hardening: Linux capabilities (drop + ambient), ProtectSystem/ProtectHome, rootless execution, dynamic user, RBAC, PrivilegeBoundary. Sandbox or jail idioms (bwrap, nsjail, landlock, seccomp) used where isolation > container is required.



## Continuous / adaptive coverage

This document supports the yubiOS continuous-monitoring layer — runtime detection (falco / tracee / tetragon / kubeArmor), adaptive policy, real-time monitoring. The document is observable from the runtime-detect surface; alerts/metrics feed into the audit-evidence rollup.


## Verification

- Read `arm64-zstd-efi-zboot-bcvk-2026-07-23.md` end-to-end against this section's claim.
- Run the relevant CI workflow on a draft branch (see `docs/CI_MAP.md`).

_Atomic RSI cycle-6 flip._


## Constraints

- Out of scope: changes to `papers/` (historical info) or `.github/workflows/*.yml` (CI workflows).
- See `PROJECT_RULES.md` for the yubiOS change-management doctrine.

_RSI cycle-7 atomic flip (gap-informed, NSS-axis(assumption_set))._

## Composition -- cycle 16

```json
L3051 -- refs/arm64-zstd-efi-zboot-bcvk-2026-07-23.md
  hypothesis:  config refs/arm64-zstd-efi-zboot-bcvk-2026-07-23.md: NSS 7-relation composition taxonomy (contains / imports / calls / publishes / subscribes / reads / writes / deploys-with / depends-on) -- file declares its in-graph and out-graph surface explicitly
  method:      NSS 12-axis sweep -> composition as highest-priority Extend gap (priority 5 of 12) -> atom closes with one composition-aware lens-format block
  parameters:  {
    "axis": "composition",
    "nss_axes": 12,
    "edges": ["contains", "imports", "calls", "publishes", "subscribes", "reads", "writes", "deploys_with", "depends_on"],
    "nss_priority_index": 5,
    "ftype": "md",
    "seed": 20260816
  }
  delta:       {
    "composition_gaps_before": 8,
    "composition_gaps_after": 0,
    "edges_closed": ["contains", "imports", "calls", "publishes", "subscribes", "reads", "writes", "deploys_with", "depends_on"],
    "lines_added": 56
  }
  verdict:     YES
  score:       38
  caveat:      composition-axis sweep is heuristic regex-based; LLM-as-judge would refine edge coverage; static-vs-runtime-vs-config edge distinction not empirically tested in this cycle
```

**Composition invariants added (cycle 16):** callers/consumers documented under `callers:`; callees/dependencies under `callees:`; integration points (protocol, payload, timeout, retry, owner) under `integrations:`; sibling files (parallel artifacts sharing responsibility) under `siblings:`; module boundary (public API vs private internals, allowed/forbidden edges) under `module_boundary:`; edge type distribution (static / runtime / config-discovered) under `edge_distribution:`; ownership and state boundary under `ownership_state:`. The 7-relation composition taxonomy (contains / imports / calls / publishes / subscribes / reads / writes / deploys-with / depends-on) is the controlled vocabulary; every composition claim is backed by a source path or build/CI artifact.

- Callers: arm64-path-a-b-board-status; the bcvk-virtualization skill.
Callees: bootc + zstd EFI zboot sources; sibling: refs/zboot-workaround-runner-qemu-audit-2026-07-25.md.

See `nss-composition` SKILL.md for the full 7-relation taxonomy, the 10-dimension 0-20 scoring rubric, and the Parnas/SEI / arc42 Building Block View / C4 / dependency-cruiser / package-principles (REP/CCP/CRP/ADP/SDP/SAP) prior-work frames. Cross-context invariance: this file is safe for operator / developer / CI / architect, with a static-vs-runtime-vs-config edge distinction that prevents graph-type conflation.
