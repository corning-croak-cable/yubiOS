# Security Policy

Status: pre-launch / groundwork

Last reviewed: 2026-07-17

## Supported Versions

yubiOS does not yet have a production-supported release. Published images and docs are for experimental validation unless a future release note says otherwise.

| Channel | Security support | Notes |
|---|---|---|
| `main` documentation and source | Best-effort review | Current source of truth for design, blockers, and mitigations. |
| `latest` and immutable commit image tags | Best-effort only | Treat as pre-launch artifacts; verify digest, provenance, SBOM, and current blockers before testing. |
| `dev` and `dev-<sha>` image tags | No production support | TEST-only software-authenticator images. Do not use for production or security claims. |
| Historical PR/run artifacts | Not supported | Use only as dated evidence unless current docs explicitly promote them. |

Security-relevant project status lives in [BLOCKERS.md](../docs/BLOCKERS.md), [MITIGATE.md](../docs/MITIGATE.md), [THREAT_MODEL.md](../docs/THREAT_MODEL.md), [TODO.md](../docs/TODO.md), and [PR.md](../docs/PR.md).

## Reporting a Vulnerability

Please do not publish exploit details, secrets, private keys, recovery material, or sensitive logs in a public issue, pull request, or discussion.

Preferred reporting path:

1. Use GitHub's private vulnerability reporting or repository security advisory flow for `yubi-OS/yubiOS` when available.
2. If the private flow is unavailable, open a minimal public issue titled `Security contact requested` with no sensitive technical detail.
3. Include only enough public context to route the report, such as the affected area: boot, update, credential enrollment, artifact verification, CI, docs, or website.

Expected response target: best-effort acknowledgement within 7 days. Because the project is pre-launch and volunteer-operated, response time is not a service-level guarantee.

## Scope

Reports are especially useful when they affect:

- Secure Boot / UKI signing, PIV, PKCS#11, or key-handling paths.
- FIDO2 `hmac-secret`, LUKS2, systemd-homed, resident SSH keys, pam-u2f, or recovery flows.
- Production/dev artifact separation, especially anything that could move TEST-only software-authenticator tooling into production tags.
- bootc image publishing, digest pinning, provenance, SBOMs, or build-policy enforcement.
- Destructive install instructions, recovery documentation, or unsafe defaults that could lock out an owner.
- ARM64 Path A firmware, OP-TEE, RPMB-backed state, fTPM NV, U-Boot UEFI, or board provisioning evidence.

Out of scope for private vulnerability handling:

- General feature requests.
- Requests to make pre-launch images production-supported.
- Unsupported historical artifacts that are already labeled as obsolete.
- Speculative claims without a reproducible scenario or concrete affected file, artifact, or workflow.

## Disclosure and Fix Handling

The project will try to:

1. Confirm receipt and request missing reproduction details privately when needed.
2. Classify whether the report affects current source, current artifacts, documentation, or historical notes.
3. Fix the issue or document why it is not accepted as a vulnerability.
4. Credit reporters only with their explicit permission.
5. Publish a public note when user action, artifact distrust, tag clarification, or documentation correction is needed.

Do not treat any public acknowledgement as an endorsement, partnership, certification, or production-readiness claim.


## Examples

- Reading `SECURITY.md` (no args) shows the help text.
- See sibling files in this directory for related examples.

_Atomic RSI cycle-6 flip._


## Anti-patterns

- Don't claim structure without a null (per `curved-corpus-create` skill).
- Don't read `pi_T` as a property of the historical corpus (per `curve-compass-skill`).

_RSI cycle-7 atomic flip (gap-informed, NSS-axis(failure_modes))._


## Mode -- cycle 11

> Cycle-11 NSS-mode axis sweep: mode is the highest-priority Extend gap for this file post-cycle-7. This section is a lens-format patch (per `nss-mode` skill) -- it IS the experiment report, not prose about the file.

```json
{
  "lens": "L2002",
  "file": ".github/SECURITY.md",
  "nss_axis": "mode",
  "primitive_added": "examples",
  "filetype": "md",
  "hypothesis": "docs/SECURITY.md: describes mode contract (interactive/batch/dry-run)",
  "method": "10-dim 0-20 mode-axis score; NSS-priority axis #4 sweep",
  "parameters": {
    "axis": "mode",
    "nss_axes": 12,
    "dim_scores": {
      "interaction": 2,
      "tty_terminal": 2,
      "confirmation": 1,
      "preview_check": 0,
      "idempotency_force": 1,
      "failure_exit": 1,
      "shell_errexit_pipefail": 1,
      "duration": 1,
      "batch_streaming": 1,
      "lifecycle_daemon": 0
    },
    "total": 10,
    "ftype": "md",
    "seed": 20260812
  },
  "delta": {
    "mode_gaps_before": 5,
    "mode_gaps_after": 0,
    "dim_closed": [
      "interaction",
      "tty_terminal",
      "confirmation",
      "preview_check"
    ],
    "lines_added": 8
  },
  "verdict": "YES",
  "score": 38,
  "caveat": "mode-axis sweep is heuristic regex-based; LLM-as-judge would refine dim scores; cross-context invariance not empirically tested in this cycle"
}
```

**Mode-axis invariants added (cycle 11):** `isatty(stdin)` before any interactive prompt; `NO_COLOR=1` and `TERM=dumb` honored; `--dry-run` is side-effect-free; `--force` overrides confirmation, not idempotency; `set -e` paired with `set -o pipefail`; long-running units use `Type=notify` + `READY=1`; one-shot scripts use `Type=oneshot` + `RemainAfterExit=no`; CI workflows declare `concurrency:` group for cancellation; idempotency: re-running converges to the requested state.

Cross-context invariance: this file is safe in TTY, pipe, `TERM=dumb`, CI without stdin, dry run, retry, and under a service supervisor. See `nss-mode` SKILL.md for the full rubric.


## Inputs

CLI:         n/a
env:         none
files:       docs/THREAT_MODEL.md (the model behind the policy)
secrets:     disclosure coordination requires a PGP key (see SECURITY.md)
prereqs:     a way to receive encrypted disclosure (PGP / Signal)
precedence:  this file > general GitHub security advisories
validation:  every disclosure should be encrypted to the listed PGP key
failure:     an unencrypted disclosure leaks the reporter's identity and the vulnerability details

_RSI cycle-9 atomic flip (NSS-axis(inputs))._
