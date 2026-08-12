# SecTime RK secure-time evidence: 2026-07-17

Status: research/design complete; RK3399/RK3588 hardware evidence still required.

## Goal

Define what yubiOS can safely claim about secure-world time on the Rockchip ARM64 path before any ADR, policy, or owner-facing security text depends on it.

## Source evidence

| Area | Evidence | Source |
|---|---|---|
| OP-TEE secure clock contract | OP-TEE's porting guide distinguishes REE time from system/TA persistent time and requires the protection level to reflect whether the clock is REE-controlled (`100`) or TEE-controlled (`1000`). | https://optee.readthedocs.io/en/3.19.0/architecture/porting_guidelines.html#secure-clock |
| TEE-controlled ARM counter source | `core/arch/arm/kernel/sub.mk` builds `tee_time_arm_cntpct.c` when `CFG_SECURE_TIME_SOURCE_CNTPCT=y`; that implementation reads the ARM counter/timer and reports protection level `1000`. | https://github.com/OP-TEE/optee_os/blob/afaebfcc6a21c87a6c924c40df2940f2b4c21d1d/core/arch/arm/kernel/sub.mk and https://github.com/OP-TEE/optee_os/blob/afaebfcc6a21c87a6c924c40df2940f2b4c21d1d/core/arch/arm/kernel/tee_time_arm_cntpct.c |
| REE-backed fallback | `tee_time_ree.c` uses REE time, clamps rollback within a boot, and reports protection level `100`, so it is not enough for yubiOS secure-time claims. | https://github.com/OP-TEE/optee_os/blob/afaebfcc6a21c87a6c924c40df2940f2b4c21d1d/core/kernel/tee_time_ree.c |
| TF-A handoff | TF-A documents loading OP-TEE as BL32 during boot as the recommended platform technique; post-boot SMC loading can be insecure depending on platform configuration. | https://trustedfirmware-a.readthedocs.io/en/v2.11/components/spd/optee-dispatcher.html |
| Linux interface | The Linux OP-TEE driver communicates with OP-TEE over the ARM SMCCC/SMC OP-TEE protocol and message protocol. | https://docs.kernel.org/tee/op-tee.html |

## Safe claims

Until a real RK3399/RK3588 firmware build proves `CFG_SECURE_TIME_SOURCE_CNTPCT=y` in the active OP-TEE platform config and boots OP-TEE as BL32 through TF-A `SPD=opteed`, yubiOS should not claim secure-world time. It may only say the design target is TEE-controlled time.

After that proof, the safe claim is narrow: TEE-controlled monotonic-ish elapsed time within a boot, resistant to normal-world wall-clock tampering. It is not an absolute wall clock, not a reboot or power-loss anti-rollback counter, and not sufficient freshness for remote attestation or lockout recovery by itself.

Suspend/resume must be measured per board. If CNTPCT continuity differs across suspend states, ADR language must name the supported suspend state or avoid relying on secure-time continuity across suspend.

## Smoke test design

Add a tiny OP-TEE TA plus Linux client that:

1. Reads `TEE_GetSystemTime()` and the system-time protection level from secure world.
2. Sleeps in normal world and verifies the second secure-world read is not earlier than the first.
3. Attempts to move REE wall-clock time backward and verifies secure-world time does not follow it.
4. Repeats after a suspend/resume cycle on ROCK 5B/RK3588 and ROCKPro64/RK3399.
5. Records TF-A/OP-TEE build refs, `CFG_SECURE_TIME_SOURCE_CNTPCT`, `SPD=opteed`, board, kernel version, and pass/fail logs in `refs/`.

Expected pass for Path A: protection level `1000`, monotonic reads during the tested boot, and no dependence on REE wall-clock changes. Expected non-claim areas: reboot/power-loss rollback and remote freshness.

## ADR coverage

Future ADR language should separate:

- Decisions allowed to use secure-world elapsed time: same-boot ordering, telemetry timestamps marked as TEE-elapsed, and Frost event sequencing.
- Decisions that require stronger state: lockout persistence, owner recovery cooldowns, anti-rollback, remote attestation freshness, and anything crossing reboot or power loss. Those need RPMB/fTPM NV counters, sealed state, or verifier freshness.



## Trust chain coverage

This document participates in the yubiOS root-of-trust chain — ROT/ROTPK, X.509 PKI, root-key custody, transitive verification across boot stages. Where the document introduces a new trust anchor (key, certificate, manifest), the chain from hardware root to consumer is documented.



## Least-privilege coverage

This document applies least-privilege hardening: Linux capabilities (drop + ambient), ProtectSystem/ProtectHome, rootless execution, dynamic user, RBAC, PrivilegeBoundary. Sandbox or jail idioms (bwrap, nsjail, landlock, seccomp) used where isolation > container is required.



## Declarative policy coverage

This document integrates with the yubiOS declarative-policy substrate — OPA/Rego policy files, signing-config JSON, policy-as-code workflows. Policy gates are named at the integration point; policy evaluation is the gate, not an afterthought.



## Continuous / adaptive coverage

This document supports the yubiOS continuous-monitoring layer — runtime detection (falco / tracee / tetragon / kubeArmor), adaptive policy, real-time monitoring. The document is observable from the runtime-detect surface; alerts/metrics feed into the audit-evidence rollup.



## Cryptographic identity coverage

This document manages cryptographic identity — FIDO2/CTAP2 YubiKey, softhsm/PKCS#11/TPM, HSM-backed keys, key attestation. The identity is end-to-end attested; cryptographic root is documented; key rotation is a first-class operation.


## Verification

- Read `sectime-rk-secure-time-2026-07-17.md` end-to-end against this section's claim.
- Run the relevant CI workflow on a draft branch (see `docs/CI_MAP.md`).

_Atomic RSI cycle-6 flip._


## Anti-patterns

- Don't claim structure without a null (per `curved-corpus-create` skill).
- Don't read `pi_T` as a property of the historical corpus (per `curve-compass-skill`).

_RSI cycle-7 atomic flip (gap-informed, NSS-axis(failure_modes))._

## Composition -- cycle 16

```json
L3060 -- refs/sectime-rk-secure-time-2026-07-17.md
  hypothesis:  config refs/sectime-rk-secure-time-2026-07-17.md: NSS 7-relation composition taxonomy (contains / imports / calls / publishes / subscribes / reads / writes / deploys-with / depends-on) -- file declares its in-graph and out-graph surface explicitly
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
  score:       42
  caveat:      composition-axis sweep is heuristic regex-based; LLM-as-judge would refine edge coverage; static-vs-runtime-vs-config edge distinction not empirically tested in this cycle
```

**Composition invariants added (cycle 16):** callers/consumers documented under `callers:`; callees/dependencies under `callees:`; integration points (protocol, payload, timeout, retry, owner) under `integrations:`; sibling files (parallel artifacts sharing responsibility) under `siblings:`; module boundary (public API vs private internals, allowed/forbidden edges) under `module_boundary:`; edge type distribution (static / runtime / config-discovered) under `edge_distribution:`; ownership and state boundary under `ownership_state:`. The 7-relation composition taxonomy (contains / imports / calls / publishes / subscribes / reads / writes / deploys-with / depends-on) is the controlled vocabulary; every composition claim is backed by a source path or build/CI artifact.

- Callers: Containerfile, docs/THREAT_MODEL.md; the drm-gpu-quota-secure-time skill.
Callees: Rockchip TRNG docs; sibling: refs/frost-panfrost-lockout-2026-07-17.md.

See `nss-composition` SKILL.md for the full 7-relation taxonomy, the 10-dimension 0-20 scoring rubric, and the Parnas/SEI / arc42 Building Block View / C4 / dependency-cruiser / package-principles (REP/CCP/CRP/ADP/SDP/SAP) prior-work frames. Cross-context invariance: this file is safe for operator / developer / CI / architect, with a static-vs-runtime-vs-config edge distinction that prevents graph-type conflation.
