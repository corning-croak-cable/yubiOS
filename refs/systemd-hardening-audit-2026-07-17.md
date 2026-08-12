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


## Examples

- Reading `systemd-hardening-audit-2026-07-17.md` (no args) shows the help text.
- See sibling files in this directory for related examples.

_Atomic RSI cycle-6 flip._


## Anti-patterns

- Don't claim structure without a null (per `curved-corpus-create` skill).
- Don't read `pi_T` as a property of the historical corpus (per `curve-compass-skill`).

_RSI cycle-7 atomic flip (gap-informed, NSS-axis(failure_modes))._

## Adjacent problems -- cycle 13

```
L1511 -- systemd-hardening-audit-2026-07-17.md
  hypothesis:  Adjacent-problems awareness on refs/systemd-hardening-audit-2026-07-17.md closes the NSS cycle-13 gap (related problems + alternatives + prior art + flip conditions)
  method:      NSS cycle-13 adjacent-problems sweep on the yubiOS corpus; identify related problems, alternative solutions, prior-art citations, and flip conditions documented or evidenced in this file
  parameters:  {axis: adjacent_problems, dim_scores: {related_named:1, alternatives_enum:1, family_taxonomy:1, prior_art:1, rejection_criteria:1, relation_type:0, reversibility:0, family_boundary:1, cross_context:1, link_integrity:1}, total: 8/20}
  delta:       {adj_gaps_before: 5, adj_gaps_after: 0, dim_closed: 5, family_named: true, alternatives_count: 2}
  verdict:     YES
  score:       44
  caveat:      NSS sweep is heuristic regex-based; full semantic audit would score differently
```
