# Roadmap promotion gates: 2026-07-17

Status: accepted planning guardrail for moving FUTURE work into active implementation.

## Required fields before promotion

Every FUTURE item needs these fields before it moves into ADR, SPEC, CI, or implementation:

| Gate | Required answer |
|---|---|
| Owner/deployment target | Which board, VM, workflow, or deployment class is being changed? |
| Trust boundary | Which component decides, which component enforces, and which component can be compromised without breaking the claim? |
| Evidence target | What log, test, hardware run, packet capture, artifact, or attestation will prove the claim? |
| Recovery behavior | How does the owner recover from false positive, failed update, lockout, or broken boot? |
| Pins/upstream sources | Which upstream docs, commits, digests, or action SHAs are part of the claim? |
| Notification/retention | If owner notification or evidence is collected, what is stored, where, for how long, and what is explicitly excluded? |
| Prod/test separation | Does the work touch production artifacts, dev/test artifacts, installer artifacts, firmware artifacts, or lab-only outputs? |
| CI/hardware boundary | Can this be tested without main CI/hardware, or is it explicitly blocked on a named lane/board? |

## Current applications

- SecTime: promoted to research/design only; hardware proof is still required before production claims.
- Frost: promoted to research/design only; kernel prototype and RK hardware recovery evidence are still required.
- OpenWrt deception LAN: promoted to package/proof design only; VM/spare-router build and packet capture remain open.
- Firmware RK tags: promoted to CI workflow metadata/publish routing; real board-divergent payloads remain hardware-lane work.
- Post-launch hardware ideas: stay watch-listed until they name an owner, board/deployment target, evidence target, and recovery plan.

## Recovery baseline

Any feature that can lock an owner out must document a recovery path before it is enabled by default. For CI and docs, this means the TODO item may be marked "planned" or "designed" only; it should not move to "implemented" without the recovery evidence.