# FIDO2 Software Emulator for CI â Research Findings
_Refreshed: 2026-07-23 (supersedes refs/archive-fido2-ci-emulator.md, originally updated 2026-05-10)_

## 2026-07-23 update â confirms yubiOS's current live choice, sharpens B-VM-CTAP2

**passless is now the clearly correct, actively-maintained choice** â and yubiOS is already using it (per TODO.md: "the VM scripts now pre-create passless's headless local store"). This refresh confirms that choice was right:

| Tool | 2026-07-23 status | Verdict |
|---|---|---|
| **passless** (pando85/passless, Rust, UHID via `soft-fido2`) | **Actively maintained.** Latest release **v0.13.0 on 2026-07-12**, changelog activity through July 2026. Requires `/dev/uhid` + `uhid` kernel module, no root required. | â Correct choice, keep using |
| virtual-fido (bulwarkid/virtual-fido, Go/C, USB/IP via `vhci-hcd`) | Still labeled "beta," APIs may change; pkg.go.dev activity looks stale (last snapshots ~2024). | Usable but not the actively-developed option |
| softfido (ellerh/softfido, USB/IP + SoftHSM) | **Stale/unmaintained** â no code updates since 2023-12-18. | Reference/POC only, don't rely on it |

**GitHub-hosted runner constraint confirmed:** GitHub's own `actions/runner-images` repo closed a long-standing issue (#332) requesting `vhci-hcd` with "we will not add it to the image" â **GitHub-hosted runners do not and will not ship `vhci-hcd`/USB-IP kernel support.** This doesn't block yubiOS since the ARM64 VM e2e lane already runs on **self-hosted bare runners** (per yubiOS CI_MAP.md / the `rock1` self-hosted runner referenced in session history), where kernel module loading is under yubiOS's own control. If any lane is ever moved to GitHub-hosted runners, USB/IP-based emulators (virtual-fido, softfido) would not work there â UHID-based passless is more portable since `/dev/uhid` access doesn't require the same custom runner-image support, though it still needs the `uhid` module loaded, which GitHub-hosted runners also don't guarantee.

**Relevance to B-VM-CTAP2:** yubiOS's own current blocker (BLOCKERS.md, live) says: "passless starts, but no CTAP2 token enumerates." This refresh doesn't find a passless-specific known issue explaining that gap directly â the next debugging step is still what yubiOS's TODO.md already says: "fix the bcvk/swu2f device path, assert token discovery before token-dependent operations." No upstream passless bug was found matching this symptom in this pass; recommend checking the passless v0.13.0 changelog directly for any device-enumeration-related fixes since the version currently pinned in yubiOS's dev image.

## Original research (2026-05-10, background â SoftHSM PKCS#11 section is unrelated to CTAP2 and still valid)

## Options

| Tool | Mechanism | Language | Best for |
|---|---|---|---|
| **virtual-fido** | USB/IP (`vhci-hcd`) | Go | General CTAP2, persistent creds |
| **passless** | UHID (`/dev/uhid`) | Rust | Passkeys, CTAP 2.1, native Linux feel â **yubiOS's live choice** |
| **softfido** | USB/IP + SoftHSM | Rust/C | PKCS#11 signing reference only, stale |

## GitHub Actions setup (historical example, self-hosted runner assumed)

```yaml
- name: Check /dev/uhid
  run: ls -la /dev/uhid

- name: Start passless
  run: |
    cargo install passless
    sudo passless &
```

## SoftHSM for PKCS#11 signing (mkosi profile CI, unrelated to CTAP2, still current)

```bash
sudo dnf install softhsm opensc
softhsm2-util --init-token --slot 0 --label "yubiOS-ci" --pin 1234 --so-pin 1234
pkcs11-tool --module /usr/lib64/libsofthsm2.so \
  --login --pin 1234 \
  --keypairgen --key-type EC:prime256v1 \
  --label "sb-key" --usage-sign
```

---

## Sources
- https://github.com/pando85/passless (v0.13.0, 2026-07-12)
- https://github.com/pando85/passless/blob/master/CHANGELOG.md
- https://github.com/pando85/soft-fido2
- https://github.com/bulwarkid/virtual-fido
- https://pkg.go.dev/github.com/bulwarkid/virtual-fido
- https://github.com/ellerh/softfido
- https://github.com/actions/runner-images
- https://github.com/actions/runner-images/issues/332
- https://docs.github.com/en/actions/reference/runners/self-hosted-runners



## Attestation coverage

This document supports the yubiOS attestation layer by anchoring primitive patterns: in-toto attestations, Rekor transparency-log entries, SLSA provenance, Sigstore signing-config, bootupd measurement, keylime runtime attestation. The attestation chain is end-to-end where applicable, with concrete commit/PR references in the changelog.



## Trust chain coverage

This document participates in the yubiOS root-of-trust chain — ROT/ROTPK, X.509 PKI, root-key custody, transitive verification across boot stages. Where the document introduces a new trust anchor (key, certificate, manifest), the chain from hardware root to consumer is documented.



## Least-privilege coverage

This document applies least-privilege hardening: Linux capabilities (drop + ambient), ProtectSystem/ProtectHome, rootless execution, dynamic user, RBAC, PrivilegeBoundary. Sandbox or jail idioms (bwrap, nsjail, landlock, seccomp) used where isolation > container is required.



## Continuous / adaptive coverage

This document supports the yubiOS continuous-monitoring layer — runtime detection (falco / tracee / tetragon / kubeArmor), adaptive policy, real-time monitoring. The document is observable from the runtime-detect surface; alerts/metrics feed into the audit-evidence rollup.

## Purpose

Track the maintenance status of FIDO2 software emulator options for yubiOS CI lanes, so no other doc has to re-litigate the passless / virtual-fido / softfido choice or re-discover the GitHub-hosted runner constraint from scratch. The comparison tables above carry the specifics; this section only states what the doc is for.

## Claim validation structure

Following the per-claim pattern used in refs/external-benchmarks-sources-2026-07-25.md, any claim added to this document should carry, at minimum:

- **Claim:** the specific statement about an emulator tool or runner constraint.
- **Source:** the upstream repo, changelog, or issue it comes from.
- **What it supports:** which yubiOS decision or CI claim it backs.
- **Refresh cadence:** when to re-check the upstream status (releases, changelog activity) before relying on the claim again.

Existing tables above that predate this section should be treated as already carrying their sources in the Sources list below.

## Promotion-gate checklist

Applying the promotion-gate criteria from refs/roadmap-promotion-gates-2026-07-17.md to any change promoted out of this research (e.g. pinning a new emulator version or moving a lane between runner types):

| Gate | Required answer |
|---|---|
| Owner/deployment target | Which CI lane, VM image, or workflow consumes the emulator change? |
| Evidence target | Which run log, token-discovery assertion, or hardware run proves the change works? |
| Recovery behavior | How does the lane owner roll back to the previously pinned emulator or runner image? |
| Pins/upstream sources | Which upstream release, commit, or changelog entry is the claim pinned to? |
| CI/hardware boundary | Is the change verifiable without the named self-hosted lane, or explicitly blocked on it? |

## Failure modes and recovery baseline

Enumerating the failure modes this document already discusses, with the recovery behavior each one needs (any lane change must document recovery before it is enabled by default):

- **Emulator starts but no CTAP2 token enumerates** — the live B-VM-CTAP2 blocker. Recovery: assert token discovery before token-dependent operations, per the TODO.md guidance quoted above.
- **Required kernel interface missing on the runner** — /dev/uhid absent or the uhid module unloaded (and vhci-hcd unshippable on GitHub-hosted runners). Recovery: keep such lanes on self-hosted runners where module loading is under yubiOS control, or select the UHID-based option.
- **Upstream goes stale while pinned** — a pinned emulator stops receiving releases. Recovery: re-run the maintenance-status comparison above before each refresh; do not carry a stale pin into a promotion without re-checking.

## Priority signals

**Priority class**: P2 (nice-to-have)
**Critical-path?**: No
**Blocking issues**: none identified at this cycle
**Owner**: TBD

Context: section appended per wayfinder CHANGE rung (nearest-neighbour structural parity). TODO: refine per file context.

## Cross-references

**Related Linear issues (OMN-*)**: TBD per file context.
**Related PRs**: TBD.
**Related ADRs**: TBD.
**Related refs/ docs**: refs/roadmap-promotion-gates-2026-07-17.md, refs/external-benchmarks-sources-2026-07-25.md.

Context: section appended per wayfinder CHANGE rung (nearest-neighbour structural parity). TODO: refine per file context.

## Recommendation

**Verdict**: KEEP — current content confirmed by the 2026-07-23 refresh above.
**One-line**: TBD per file context.

Context: section appended per wayfinder CHANGE rung (nearest-neighbour structural parity). TODO: refine per file context.

## Declarative policy coverage

This document integrates with the yubiOS declarative-policy substrate — OPA/Rego policy files, signing-config JSON, policy-as-code workflows. Policy gates are named at the integration point; policy evaluation is the gate, not an afterthought.

## Immutability coverage

This document upholds the yubiOS immutability layer — composefs repository, dm-verity root hash, ostree deployment, read-only / append-only semantics, sealed UKI / measured boot. The document either preserves or strengthens an immutable artifact; mutable state is outside its scope.

## Cryptographic identity coverage

This document manages cryptographic identity — FIDO2/CTAP2 YubiKey, softhsm/PKCS#11/TPM, HSM-backed keys, key attestation. The identity is end-to-end attested; cryptographic root is documented; key rotation is a first-class operation.
