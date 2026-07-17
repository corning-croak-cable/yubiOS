# Future Work

Last reviewed: 2026-07-17
Status: roadmap and research backlog

This file tracks future work that is not yet the normative baseline. Active requirements belong in [SPEC.md](SPEC.md); accepted decisions belong in [ADR.md](ADR.md); open blockers belong in [BLOCKERS.md](BLOCKERS.md).

## Near-Term Planning Cycle

The current planning cycle is [refs/planning-cycle-2026-07-11.md](refs/planning-cycle-2026-07-11.md). It completed a documentation and research refresh around systemd v261, PQ TLS defaults, bootc installation docs, QEMU zstd EFI zboot status, and stale wiki guidance.

## Milestone F: ARM64 Owner-Owned Root Of Trust

Goal: prove the production Path A story on real ARM64 hardware.

1. Select the first Path A board target, with RK3588 still the preferred flagship family.
2. Rehearse TF-A Trusted Board Boot and ROTPK provisioning on sacrificial hardware.
3. Bring up OP-TEE, StandaloneMM, RPMB-backed UEFI variables, and ms-tpm-20-ref fTPM.
4. Validate U-Boot UEFI Secure Boot and TCG2 measurement into the fTPM.
5. Boot the same signed yubiOS UKI used by x86-64 and prove `/usr` verification plus FIDO2 unlock.
6. Document exact board provisioning evidence before using production language.

Path B remains useful for measured/attested development and CI, but it must be described as evidence-and-sealing rather than boot-time rejection.

## Milestone CI: Keep The Test Lanes Honest

- Keep native ARM64 KVM evidence visible for the dev/swu2f VM leg.
- Keep the zstd EFI zboot workaround pinned until the runner QEMU version has the upstream fix.
- Keep PQ TLS verification in CI so future base-image bumps cannot silently lose ML-KEM hybrid defaults.
- Treat x86-64 VM issues as supported-platform compatibility work, not blockers for the ARM64 ownership thesis unless they affect shared artifacts.

## Milestone Docs: Prevent Snapshot Drift

- Add dated planning notes under `refs/` for each substantial research cycle.
- Avoid hardcoding run-specific image digests outside [PINNED.md](PINNED.md) unless the text clearly marks them as historical evidence.
- Keep `RestrictFileSystems=` and `RestrictFileSystemAccess=` distinct in all hardening docs.
- Prefer primary upstream sources in [CITATION.md](CITATION.md), then link repo-specific evidence from ADRs and refs.

## Milestone Net: OpenWrt WireGuard Deception LAN

Goal: research an OpenWrt project or package that turns a WireGuard-protected LAN into a deliberate "needle in the haystack" environment for SSH discovery attempts. The package should expose many low-risk decoy SSH endpoints, slow enumeration with tarpits where safe, and notify the owner when an agent or attacker probes for the real host.

Research shape:

- Package as an OpenWrt feed/package with UCI configuration, procd services, firewall/nftables integration, and optional LuCI only after the CLI path is stable.
- Bind to the WireGuard zone by default. Do not expose the deception surface on WAN unless an operator explicitly enables a lab mode.
- Support multi-host deception through loopback aliases, WireGuard-only decoy address pools, or nftables DNAT to lightweight responders.
- Evaluate an `endlessh`-style banner tarpit for delay, plus a higher-interaction honeypot mode only when storage, CPU, and legal/logging policy are explicit.
- Notify through syslog/ubus plus owner-selected channels such as ntfy, Gotify, Matrix, email, or a webhook, with rate limits and deduplication.
- Keep real host discovery dependent on known WireGuard peer identity, SSH host-key verification, and yubiOS/YubiKey controls. Deception is detection and delay, not primary authentication.

Safety constraints:

- Do not store attempted passwords, private keys, or sensitive payloads by default; hash or redact evidence when retention is needed.
- Keep strict CPU, memory, connection, and log-size ceilings so a tarpit cannot become a self-DoS.
- Separate protected-LAN mode from internet-facing lab mode in package defaults and documentation.
- Document privacy, legal, recovery, and false-positive handling before recommending deployment.

Evidence needed before promotion:

- OpenWrt VM or spare-router proof with a decoy address pool and owner notification path.
- Packet-level test evidence showing scans hit decoys before the real SSH endpoint is discoverable.
- Reproducible package build recipe, config lint, and firewall rule tests.
- ADR coverage for the trust boundary, notification model, evidence retention, and failure behavior.

## Post-Launch Hardware Work

| Work item | Status | Notes |
|---|---|---|
| RK3588 Path A production proof | Planned | Needs fuse/RPMB/OP-TEE validation on real boards |
| RK3399 stepping-stone proof | Planned | Useful for rehearsing TF-A and OP-TEE lineage |
| RPi 5 Path B documentation | Planned | Valuable dev target, not owner-owned Path A |
| Firmware OCI artifact hardening | Ongoing | Real hardware firmware tags should drop volatile CI flags |
| U-Boot FIDO2/U2F console gate | Idea-stage | Needs USB HID threat model and recovery design before implementation |
| Attestation service | Research | Must inherit PQ TLS requirements and fTPM evidence model |

## Deferred Ideas

- `systemd-sysinstall` as an optional guided installer path beyond current bootc and repart flows.
- LUO/KHO live-update research for appliance or server deployments where a short reboot is unacceptable.
- FIDO2-wrapped Secure Boot signing keys if upstream tools gain a clean hidraw path; PIV remains the current accepted route.
- ORAS artifact media types for non-OS OCI artifacts when registry UX is friendlier than `FROM scratch` carrier images.

## Exit Criteria For Moving Work Out Of FUTURE

Move an item into [ADR.md](ADR.md), [SPEC.md](SPEC.md), or implementation only when the following are true:

- The trust boundary is clear.
- Recovery and failure behavior are documented.
- CI or real-hardware evidence is defined.
- Required pins and upstream source references are recorded.
- Notification and evidence-retention policies are defined when detection or deception is involved.
- The change does not introduce a silent production/test artifact crossover.
