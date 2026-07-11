---
contract: "Tools, software, services, and communication channels the user uses, and how they prefer to use them; plus what Sauna can do for them in the product. Route here when the user gives durable workflow/tooling preferences or account-level context. Do not store implementation recipes here; those belong in Skills or repo docs."
short_description: "Tools and apps you use"
---

## Software & Apps

- GitHub: `corning-croak-cable` personal account; `yubi-OS` org with active repos `yubiOS`, `bootc`, `bcvk`, `mkosi`, `particleos`, `agent-skills`, and ARM64 fTPM forks. Repos whose names contain a period are hands-off.
- mkosi: OS image builder fork for yubiOS OCI images, disk images, UKI signing, and installer artifacts.
- bcvk: bootc virtualization kit fork for ephemeral VM testing, VM install paths, and hardware/YubiKey passthrough experiments.
- Docker Buildx: preferred build runtime for yubiOS supply-chain policy enforcement and attestations.
- systemd: core OS init, measured-boot, homed, cryptenroll, sysupdate, service hardening, and v261 research surface.

## Services & Accounts

- GitHub app / workflow-capable path: current yubiOS guidance treats workflow-file writes as granted through the connected GitHub app or granted SU path. Historical notes saying workflow writes must be manual are stale unless a live write fails.
- Docker Hub: `0mniteck/yubios` is the primary yubiOS distribution repository for `latest`, per-commit, `dev`, `installer`, and `firmware` tag families.
- dhi.io: CI base-image registry. Username is `0mniteck42`; password comes from `${{ secrets.DOCKER }}`. The live digest belongs in `PINNED.md` only.
- Duck.com: privacy email alias in use for automation identity.

## Communication Channels

- GitHub: code reviews, PRs, issues, CI/CD, and repository status.
- Sauna / ChatGPT Agent: planning cycles, research, documentation drafting, CI/debug loops, and PR implementation assistance.

## Workflows

- Planning/research cycle -> read repo guidance, run source-backed research, update markdown/refs, flag inconsistencies, open PR, merge when appropriate.
- Workflow-file edit -> use the connected GitHub app / granted workflow-capable path, keep triggers narrow, and document CI status.
- Build-policy change -> research Docker Build Policies and yubiOS Rego policy before editing workflow or Containerfile references.
- Session export -> import provided `SESSION_*.zip` artifacts before relying on cached knowledge.

## Sauna Capabilities

- For substantial repo work, Sauna can coordinate GitHub reads/writes, documentation updates, research synthesis, PR creation, merge, and issue-based reporting.
