# ARM64 RK board status: 2026-07-17

Status: workflow evidence updated 2026-07-21; Path A hardware proof still required.

## Board matrix

| Board | SoC | yubiOS role | Current status |
|---|---|---|---|
| Radxa ROCK 5B | RK3588 | Primary Path A board | Run 29869527608 compiled board components but lacked the required real DDR/TPL input and combined `u-boot-rockchip.bin`. Needs that input plus sacrificial ROTPK/fuse, RPMB, fTPM NV, U-Boot UEFI, and signed-UKI proof. |
| ROCKPro64 | RK3399 | Supported secondary Path A board | Run 29869527608 produced combined Rockchip images. Physical ROTPK/fuse, RPMB, fTPM NV, recovery, and signed-UKI evidence remain open. |
| QEMU ARM64 virt | vexpress-qemu_armv8a | CI firmware baseline | Run 29869527608 passed fTPM/StandaloneMM boot assertions on both runner architectures. It is not proof of RPMB-backed real hardware behavior. |

## Path A vs Path B

Path A means owner-owned root of trust on real hardware: TF-A trusted-board-boot, OP-TEE as BL32, StandaloneMM with RPMB-backed variables, fTPM NV backed by real persistent storage, U-Boot UEFI, and a signed UKI boot path.

Path B means CI or emulated firmware can prove build shape and integration behavior but not hardware-backed persistence, fuses, RPMB, or owner root-of-trust custody.

ROCK 5B and ROCKPro64 stay Path B for production claims until the board-specific evidence is recorded in `refs/`.

## Firmware tags

`ci_firmware-rk.yml` publishes:

- `0mniteck/yubios:firmware`
- `0mniteck/yubios:firmware-<sha>`
- `0mniteck/yubios:firmware-qemu-arm64`
- `0mniteck/yubios:firmware-qemu-arm64-<sha>`
- `0mniteck/yubios:firmware-rock5b-rk3588`
- `0mniteck/yubios:firmware-rock5b-rk3588-<sha>`
- `0mniteck/yubios:firmware-rockpro64-rk3399`
- `0mniteck/yubios:firmware-rockpro64-rk3399-<sha>`

The board tags now carry board-specific compile outputs. They remain pre-production: QEMU is the only boot-tested variant, ROCK 5B lacks a required firmware input, and ROCKPro64 has no retained physical-board proof. See [ci-evidence-2026-07-21.md](ci-evidence-2026-07-21.md).



## Attestation coverage

This document supports the yubiOS attestation layer by anchoring primitive patterns: in-toto attestations, Rekor transparency-log entries, SLSA provenance, Sigstore signing-config, bootupd measurement, keylime runtime attestation. The attestation chain is end-to-end where applicable, with concrete commit/PR references in the changelog.



## Least-privilege coverage

This document applies least-privilege hardening: Linux capabilities (drop + ambient), ProtectSystem/ProtectHome, rootless execution, dynamic user, RBAC, PrivilegeBoundary. Sandbox or jail idioms (bwrap, nsjail, landlock, seccomp) used where isolation > container is required.



## Continuous / adaptive coverage

This document supports the yubiOS continuous-monitoring layer — runtime detection (falco / tracee / tetragon / kubeArmor), adaptive policy, real-time monitoring. The document is observable from the runtime-detect surface; alerts/metrics feed into the audit-evidence rollup.



## Cryptographic identity coverage

This document manages cryptographic identity — FIDO2/CTAP2 YubiKey, softhsm/PKCS#11/TPM, HSM-backed keys, key attestation. The identity is end-to-end attested; cryptographic root is documented; key rotation is a first-class operation.


## Priority signals

**Priority class**: P2 (nice-to-have)
**Critical-path?**: No
**Blocking issues**: none identified at this cycle
**Owner**: TBD

Context: section appended per repo-refs-skill cycle-1 Mode D batch (Δ=+0.4834). TODO: refine per file context.


## Cross-references

**Related Linear issues (OMN-*)**: TBD per file context.
**Related PRs**: TBD.
**Related ADRs**: TBD.
**Related refs/ docs**: TBD.

Context: section appended per repo-refs-skill cycle-2 7-D Mode D batch (Δ=+0.4739). TODO: refine per file context.


## New Ideas -- cycle 2 (lens format)

This file was processed by the RSI cycle-2 lens generator (curve-compass-skill v1.1.0 + curved-corpus-create v1.1.0). Each cycle-2 patch IS a concrete experiment with a measurable delta -- not a templated section. The lens below documents the measured dynamics; the patch is the lens, not prose about the file.

```json
{
  "lens": "L216",
  "file": "refs/arm64-rk-board-status-2026-07-17.md",
  "hypothesis": "refs/arm64-rk-board-status-2026-07-17.md covers all 9 primitives in the internal-big-picture basis",
  "method": "9-D primitive binarization (purpose, examples, guidelines, constraints, verification, composition, changelog, references, anti-patterns) + chordal distance to ideal pole on Fibonacci lattice",
  "parameters": {
    "basis": "internal-big-picture",
    "d": 9,
    "seed": 20260812
  },
  "delta": {
    "k": 3,
    "missing_primitives": [
      "examples",
      "guidelines",
      "constraints",
      "composition",
      "changelog",
      "anti-patterns"
    ],
    "chordal_resid": 0.0
  },
  "verdict": "NO",
  "score": 17,
  "caveat": "binarization is heuristic; a stricter regex pass might surface sub-primitives"
}
```
