# systemd hardening audit: 2026-07-17

Status: static audit complete; target-image runtime validation still required.

## Scope

Audited repo-owned yubiOS services found by source search:

- `usr/lib/systemd/system/yubiOS-enroll.service`
- `usr/lib/systemd/system/yubiOS-chipsec-firstboot.service`

The audit covers `ConditionSecurity=measured-os`, `RestrictFileSystems=`, and the newer v261 `RestrictFileSystemAccess=` distinction.

## Findings

| Unit | Finding | Status |
|---|---|---|
| `yubiOS-enroll.service` | Has `ConditionFirstBoot=yes`, `ConditionPathExists=!/var/lib/yubiOS/.enrolled`, and `ConditionSecurity=measured-os` in `[Unit]`. | Correct for first-boot enrollment gating. |
| `yubiOS-enroll.service` | Uses `RestrictFileSystems=~@network`, the deny-list form that blocks network filesystems without allow-listing away local filesystems needed for boot/enrollment. | Correct static shape. |
| `yubiOS-chipsec-firstboot.service` | Has `ConditionSecurity=measured-os`, `ConditionFirstBoot=yes`, and `Before=yubiOS-enroll.service`. | Correct for the first-boot firmware validation exception. |
| `yubiOS-chipsec-firstboot.service` | Intentionally omits `RestrictFileSystems=` and carries raw hardware capabilities for CHIPSEC. | Acceptable documented exception; keep one-shot/offline/narrow write paths. |
| Repo-wide | No repo-owned service currently uses `RestrictFileSystemAccess=`. | Do not add until target systemd and verity-backed execution assumptions are tested. |

## Existing tests

- `tests/unit/test-enroll-unit.bats` checks measured-boot gating, `[Unit]` placement, `RestrictFileSystems=~@network`, and `systemd-analyze verify` with staged Exec stubs.
- `tests/unit/test-chipsec-firstboot-unit.bats` checks measured/first boot gates, one-shot behavior, private network, narrow write paths, explicit capability exception, wrapper result semantics, and `systemd-analyze verify`.

## Remaining evidence gate

Run the Bats tests and `systemd-analyze verify` inside the target image/base after the next non-main-CI-safe opportunity. This pass did not boot the image or run main CI, so it closes the static TODO but not runtime evidence.

## Rule for future hardening

Keep `RestrictFileSystems=` and `RestrictFileSystemAccess=` separate:

- `RestrictFileSystems=` limits filesystem types and is already used for enrollment.
- `RestrictFileSystemAccess=` is a newer v261 control for verified filesystem access semantics and needs a separate design/test pass before use.



## Attestation coverage

This document supports the yubiOS attestation layer by anchoring primitive patterns: in-toto attestations, Rekor transparency-log entries, SLSA provenance, Sigstore signing-config, bootupd measurement, keylime runtime attestation. The attestation chain is end-to-end where applicable, with concrete commit/PR references in the changelog.



## Trust chain coverage

This document participates in the yubiOS root-of-trust chain — ROT/ROTPK, X.509 PKI, root-key custody, transitive verification across boot stages. Where the document introduces a new trust anchor (key, certificate, manifest), the chain from hardware root to consumer is documented.



## Continuous / adaptive coverage

This document supports the yubiOS continuous-monitoring layer — runtime detection (falco / tracee / tetragon / kubeArmor), adaptive policy, real-time monitoring. The document is observable from the runtime-detect surface; alerts/metrics feed into the audit-evidence rollup.



## Cryptographic identity coverage

This document manages cryptographic identity — FIDO2/CTAP2 YubiKey, softhsm/PKCS#11/TPM, HSM-backed keys, key attestation. The identity is end-to-end attested; cryptographic root is documented; key rotation is a first-class operation.



## Segmentation coverage

This document applies the yubiOS segmentation primitive — Linux namespaces, cgroups, sandbox, isolation boundary, trust boundary, jail idioms (nsjail, bwrap, firejail), landlock, seccomp. The boundary is named; the trust-domain transition is documented.


## Priority signals

**Priority class**: P2 (nice-to-have)
**Critical-path?**: No
**Blocking issues**: none identified at this cycle
**Owner**: TBD

Context: section appended per repo-refs-skill cycle-1 Mode D batch (Δ=+0.5896). TODO: refine per file context.


## Cross-references

**Related Linear issues (OMN-*)**: TBD per file context.
**Related PRs**: TBD.
**Related ADRs**: TBD.
**Related refs/ docs**: TBD.

Context: section appended per repo-refs-skill cycle-3 7-D Mode D batch (Δ=+0.5959). TODO: refine per file context.


## New Ideas -- cycle 2 (lens format)

This file was processed by the RSI cycle-2 lens generator (curve-compass-skill v1.1.0 + curved-corpus-create v1.1.0). Each cycle-2 patch IS a concrete experiment with a measurable delta -- not a templated section. The lens below documents the measured dynamics; the patch is the lens, not prose about the file.

```json
{
  "lens": "L316",
  "file": "refs/systemd-hardening-audit-2026-07-17.md",
  "hypothesis": "refs/systemd-hardening-audit-2026-07-17.md covers all 9 primitives in the internal-big-picture basis",
  "method": "9-D primitive binarization (purpose, examples, guidelines, constraints, verification, composition, changelog, references, anti-patterns) + chordal distance to ideal pole on Fibonacci lattice",
  "parameters": {
    "basis": "internal-big-picture",
    "d": 9,
    "seed": 20260812
  },
  "delta": {
    "k": 5,
    "missing_primitives": [
      "examples",
      "changelog",
      "references",
      "anti-patterns"
    ],
    "chordal_resid": 0.0
  },
  "verdict": "PARTIAL",
  "score": 28,
  "caveat": "binarization is heuristic; a stricter regex pass might surface sub-primitives"
}
```
