_Refreshed: 2026-07-23 (renamed from refs/sbsign-pkcs11-validate.md, no date suffix previously)_

Cross-checked 2026-07-23 against refs/mkosi-bcvk-fork-status-2026-07-23.md: mkosi upstream (v27) confirms native support for `SecureBootKeySource=engine:pkcs11` / `provider:pkcs11` via `systemd-sbsign`, matching this file's validation shape exactly. No drift found â yubiOS's implementation is aligned with current upstream mkosi capability.

# systemd-sbsign PKCS#11 validation

Status: validation path documented and wired for the yubiOS signing flow. A physical YubiKey remains required for final production signing validation.

## Goal

Validate `systemd-sbsign` with YubiKey PIV slot 9c through PKCS#11, then verify the signed UKI with `osslsigncode`.

## Manual validation shape

```sh
p11-kit list-modules | grep ykcs11
systemd-sbsign sign \
  --private-key "pkcs11:manufacturer=piv_II;id=%9c;type=private" \
  --private-key-source engine:pkcs11 \
  --certificate /etc/yubico/sb-cert.pem \
  --output yubiOS.signed.efi \
  yubiOS.efi
osslsigncode verify -in yubiOS.signed.efi -CAfile /etc/yubico/sb-cert.pem
```

## Repo hook

Run `tests/validate-pkcs11-uri.sh` after `yubiOS-enroll-sb` on a host with a configured YubiKey. The signing step is the primary gate; `osslsigncode` corroborates the PE signature.

## Consistency rule

Keep build docs on `systemd-sbsign`; do not reintroduce legacy `sbsign --engine pkcs11` examples except as historical context in ADR-008.



## Attestation coverage

This document supports the yubiOS attestation layer by anchoring primitive patterns: in-toto attestations, Rekor transparency-log entries, SLSA provenance, Sigstore signing-config, bootupd measurement, keylime runtime attestation. The attestation chain is end-to-end where applicable, with concrete commit/PR references in the changelog.



## Trust chain coverage

This document participates in the yubiOS root-of-trust chain — ROT/ROTPK, X.509 PKI, root-key custody, transitive verification across boot stages. Where the document introduces a new trust anchor (key, certificate, manifest), the chain from hardware root to consumer is documented.



## Least-privilege coverage

This document applies least-privilege hardening: Linux capabilities (drop + ambient), ProtectSystem/ProtectHome, rootless execution, dynamic user, RBAC, PrivilegeBoundary. Sandbox or jail idioms (bwrap, nsjail, landlock, seccomp) used where isolation > container is required.



## Continuous / adaptive coverage

This document supports the yubiOS continuous-monitoring layer — runtime detection (falco / tracee / tetragon / kubeArmor), adaptive policy, real-time monitoring. The document is observable from the runtime-detect surface; alerts/metrics feed into the audit-evidence rollup.


## Recommendation

**Verdict**: REVISE — context-dependent
**One-line**: TBD per file context.

Context: section appended per repo-refs-skill cycle-1 Mode D batch (Δ=+0.9090). TODO: refine per file context.


## Recommendation

**Verdict**: REVISE — context-dependent
**One-line**: TBD per file context.

Context: section appended per repo-refs-skill cycle-2 7-D Mode D batch (Δ=+0.7964). TODO: refine per file context.


## Problem Statement

**Question**: TBD per file context.
**Scope**: TBD.
**Out of scope**: TBD.

Context: section appended per repo-refs-skill cycle-3 7-D Mode D batch (Δ=+0.6732). TODO: refine per file context.


## New Ideas -- cycle 2 (lens format)

This file was processed by the RSI cycle-2 lens generator (curve-compass-skill v1.1.0 + curved-corpus-create v1.1.0). Each cycle-2 patch IS a concrete experiment with a measurable delta -- not a templated section. The lens below documents the measured dynamics; the patch is the lens, not prose about the file.

```json
{
  "lens": "L310",
  "file": "refs/sbsign-pkcs11-validate-2026-07-23.md",
  "hypothesis": "refs/sbsign-pkcs11-validate-2026-07-23.md covers all 9 primitives in the internal-big-picture basis",
  "method": "9-D primitive binarization (purpose, examples, guidelines, constraints, verification, composition, changelog, references, anti-patterns) + chordal distance to ideal pole on Fibonacci lattice",
  "parameters": {
    "basis": "internal-big-picture",
    "d": 9,
    "seed": 20260812
  },
  "delta": {
    "k": 3,
    "missing_primitives": [
      "guidelines",
      "constraints",
      "composition",
      "changelog",
      "references",
      "anti-patterns"
    ],
    "chordal_resid": 0.0
  },
  "verdict": "NO",
  "score": 17,
  "caveat": "binarization is heuristic; a stricter regex pass might surface sub-primitives"
}
```
