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

- Reading the file or running the script with no arguments shows the help text.
- For a guided tour of where this file fits in yubiOS, see `docs/ARCHITECTURE.md` and the cross-references in this directory.

## Guidelines

- Follow the conventions in `docs/STYLE.md` (or the most relevant style guide referenced from this directory).
- Match the existing structure of surrounding files: `## Examples`, `## Verification`, `## Changelog`, `## Anti-patterns`.

## Changelog

- 2026-08-12 — primitive-closure pass via `curve-compass-skill` + `curved-corpus-create` (this PR).

## Anti-patterns

- Don't claim structure without a null: V2 / PC1+PC2 without the curveball null is a number without a claim (per `curved-corpus-create` skill).
- Don't open a code-change PR for already-done work; if it's an audit-trail PR, name it that.
- Don't report `pi_T` statistics as properties of the historical corpus; the compass is on a *designed* dynamics, the historical log is the T->0 limit.

