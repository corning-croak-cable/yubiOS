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

## Milestone SecTime: Secure-World Time Evidence

Goal: verify whether RK3399/RK3588 yubiOS boards can make trustworthy time claims from the secure world before those claims are used for attestation, logs, replay windows, or freshness policy.

Research shape:

- Audit the TF-A, U-Boot, and OP-TEE board configuration for the secure time path, starting with `CFG_SECURE_TIME_SOURCE_CNTPCT`, OP-TEE AArch64 timer handling, and TF-A `SPD=opteed` integration.
- Distinguish an ARM generic timer counter read from secure world from a board-backed secure RTC, RPMB monotonic counter, or normal-world/REE time fallback.
- Define what "secure enough" means for yubiOS: monotonic within a boot, stable across suspend/resume, resistant to normal-world tampering, and explicit about power-loss and reboot limits.
- Add an OP-TEE smoke test or TA-level probe that records monotonic reads and failure behavior on RK3399 and RK3588 hardware.
- Keep policy claims out of [SPEC.md](SPEC.md) until the clock source, rollback behavior, and recovery path are source-backed and board-tested.

Evidence needed before promotion:

- Source-backed note under `refs/` identifying the active OP-TEE secure time configuration for RK3399 and RK3588.
- Hardware log showing secure-world monotonic reads across boot, suspend/resume, and expected failure cases.
- ADR coverage for which security decisions may rely on secure-world time and which must use a stronger counter, sealed state, or remote attestation freshness.
- Recovery guidance for boards with only REE-backed time or with ambiguous secure clock wiring.

## Milestone Frost: Firmware-Assisted GPU Resource Lockout

Goal: research a Panfrost-centered "Frost" path that can observe, limit, quarantine, or reset GPU resource abuse on RK3399/RK3588 without treating U-Boot as a runtime policy engine.

Research shape:

- Treat Linux DRM/Panfrost and cgroup v2 as the accounting and policy layer. Prefer the emerging DRM device-memory cgroup path when available; otherwise prototype minimal cgroup-aware Panfrost BO accounting.
- Hook BO allocation, PRIME import, BO destruction, and an optional submit guard rather than relying on userspace ioctl policy alone.
- Use U-Boot for early setup only: reserved memory, device-tree nodes, control mailbox metadata, and handoff to Linux plus secure monitor firmware.
- Define a secure monitor or firmware interface, such as SMC or a shared mailbox, for hard actions: context quarantine, IOMMU revocation, GPU reset, or power gating.
- Stage enforcement from observe, warn, and deny-allocation modes to cgroup/context quarantine, then full GPU reset or power-cycle only for repeated or unsafe violations.
- Separate device-memory limits from GPU time scheduling so the milestone is clear about what Frost protects and what remains future scheduler work.

Evidence needed before promotion:

- Source-backed map of current Panfrost/Rockchip kernel patch points for probe/init, BO create/free, PRIME import, and submit guarding.
- RK3399/RK3588 proof showing whether lockout can target an offending cgroup/context or must fall back to safe full-GPU reset behavior.
- Device-tree, reserved-memory, and control-mailbox sketch with recovery and failure behavior.
- Tests for false positives, graphics stack recovery, telemetry, logs, and owner notification.
- ADR coverage of the trust boundary between Linux policy, OP-TEE/TF-A hard cutoff, and user recovery.

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

Current fit analysis: [refs/endlessh-openwrt-fit-2026-07-17.md](refs/endlessh-openwrt-fit-2026-07-17.md).

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
