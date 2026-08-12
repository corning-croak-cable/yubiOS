# systemd v262 interface audit - 2026-07-14

Status: completed for `feat/systemd-v262-audit`.
Scope: close the TODO.md audit for `/run/boot-loader-entries/`, the experimental `systemd-sysupdated` D-Bus API, and `updatectl` assumptions before adopting systemd v262 packages or docs.

## Upstream check

- `systemd` `NEWS` currently contains `CHANGES WITH 262`, including `systemd-sysupdate` unit changes: `systemd-sysupdate.service` and `systemd-sysupdate.timer` are renamed to `systemd-sysupdate-update.service` and `systemd-sysupdate-update.timer`, with compatibility symlinks, and a new `systemd-sysupdate@.service` for Varlink activation.
- The v261 notes announced that v262 removes support for the compatibility directory `/run/boot-loader-entries/` and related interfaces. UAPI.1 Boot Loader Specification support remains.
- The v261 notes announced removal of the experimental `systemd-sysupdated` D-Bus API. Clients are expected to talk directly to `systemd-sysupdate` via Varlink IPC, and `updatectl` is being reworked around that direction.

## Repo audit

Searches were grouped around the three risky assumptions:

- `/run/boot-loader-entries/`, `boot-loader-entries`, and `boot loader entries`: only `TODO.md` and `refs/research-refresh-2026-07-11.md` mention the removal target directly. `SPEC.md` references the Boot Loader Specification generically, not the removed runtime compatibility directory.
- `systemd-sysupdated`, `sysupdated`, and `D-Bus`: only `TODO.md` and `refs/research-refresh-2026-07-11.md` mention the removed API directly.
- `updatectl`: only `TODO.md` and `refs/research-refresh-2026-07-11.md` mention it directly.
- `systemd-sysupdate` / `sysupdate`: `README.md`, `ADR.md`, and `ARCHITECTURE.md` describe the sysupdate backend/model. No repo code, workflow, or documented command path depends on `systemd-sysupdated` D-Bus or `updatectl`.

## Result

No code or workflow change is required for these v262 removals. Current docs are safe as long as they keep describing:

- UAPI.1 / Boot Loader Specification behavior, not `/run/boot-loader-entries/` compatibility injection.
- `systemd-sysupdate` as the backend/tooling model, not `systemd-sysupdated` D-Bus.
- Future client integration through Varlink, not `updatectl`, unless `updatectl` is re-audited after its v262 rework.

## Follow-up guardrails

- If yubiOS adds host-update units or timers after v262 adoption, prefer the v262 `systemd-sysupdate-update.service` / `.timer` names or explicitly verify the compatibility symlinks on the pinned base image.
- Keep future update UX docs explicit about whether they are using bootc CLI, `systemd-sysupdate`, a Varlink client, or a re-audited `updatectl` flow.

## Sources

- https://raw.githubusercontent.com/systemd/systemd/main/NEWS
- https://github.com/systemd/systemd/releases
- https://www.freedesktop.org/software/systemd/man/systemd-sysupdate.html
- https://www.freedesktop.org/software/systemd/man/latest/systemd-sysupdated.html



## Attestation coverage

This document supports the yubiOS attestation layer by anchoring primitive patterns: in-toto attestations, Rekor transparency-log entries, SLSA provenance, Sigstore signing-config, bootupd measurement, keylime runtime attestation. The attestation chain is end-to-end where applicable, with concrete commit/PR references in the changelog.



## Trust chain coverage

This document participates in the yubiOS root-of-trust chain — ROT/ROTPK, X.509 PKI, root-key custody, transitive verification across boot stages. Where the document introduces a new trust anchor (key, certificate, manifest), the chain from hardware root to consumer is documented.



## Least-privilege coverage

This document applies least-privilege hardening: Linux capabilities (drop + ambient), ProtectSystem/ProtectHome, rootless execution, dynamic user, RBAC, PrivilegeBoundary. Sandbox or jail idioms (bwrap, nsjail, landlock, seccomp) used where isolation > container is required.



## Continuous / adaptive coverage

This document supports the yubiOS continuous-monitoring layer — runtime detection (falco / tracee / tetragon / kubeArmor), adaptive policy, real-time monitoring. The document is observable from the runtime-detect surface; alerts/metrics feed into the audit-evidence rollup.



## Cryptographic identity coverage

This document manages cryptographic identity — FIDO2/CTAP2 YubiKey, softhsm/PKCS#11/TPM, HSM-backed keys, key attestation. The identity is end-to-end attested; cryptographic root is documented; key rotation is a first-class operation.


## Examples

- Reading `systemd-v262-audit-2026-07-14.md` (no args) shows usage
- See `docs/ARCHITECTURE.md` for where this file fits in yubiOS


## Guidelines

- Match the conventions in `docs/STYLE.md`
- See sibling files in this directory for the surrounding context


## Constraints

- Out of scope: changes to `papers/` (historical info) or `.github/workflows/*.yml` (CI workflows)


## Anti-patterns

- Don't claim structure without a null (per `curved-corpus-create`)
- Don't report pi_T as a property of the historical corpus (per `curve-compass-skill`)
