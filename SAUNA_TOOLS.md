---
contract: "Tools, software, services, and communication channels the user uses, and how they prefer to use them; plus what Sauna can do for them in the product (integrations, automations, connected surfaces). Route here when: the user describes how they use a tool, expresses a preference about it, reveals a workflow connecting tools, indicates which communication channels they use for which audiences, or clarifies Sauna capabilities (what to connect, what to automate, scope). A casual mention of a tool isn't enough — there needs to be context about how or why they use it. Editing: one line per tool or capability note. If an entry is already listed, tighten the existing line rather than adding a duplicate. Implementation details, API patterns, and automation recipes belong in Skills, not here. Account information belongs here."
short_description: "Tools and apps you use"
---

## Software & Apps

- GitHub: `corning-croak-cable` personal account; `yubi-OS` org (yubiOS, bootc, bcvk, mkosi, particleos, agent-skills, image-builder); **ARM64 fTPM forks added 2026-06-24:** `arm-trusted-firmware` ← ARM-software, `optee_os` + `optee_ftpm` ← OP-TEE, `u-boot` ← u-boot/u-boot, `ms-tpm-20-ref` ← microsoft, `edk2-rk3588` ← edk2-porting (ADR-018/019/020); API token lacks `workflow` scope — `.github/workflows/` files must be committed manually

- mkosi: OS image builder (systemd/mkosi fork) for yubiOS OCI images + UKI signing
- bcvk: bootc virtualization kit (Rust) for ephemeral VM testing and native flashing
- Docker/podman: container builds with Build Policies (OPA/Rego) for supply chain hardening
- systemd: core OS init; writing hardened service units for yubiOS

## Services & Accounts

- GitHub: `corning-croak-cable` personal account; `yubi-OS` org (yubiOS, bootc, bcvk, mkosi, particleos forks); API token lacks `workflow` scope — `.github/workflows/` files cannot be pushed via automation and must be committed manually
- dhi.io: container registry for pinned yubiOS base images; auth username `0mniteck42`, password via `${{ secrets.DOCKER }}`; pinned CI base image: `dhi.io/debian-base@sha256:9415967aa0ed8adea8b5c048994259d1982026dca143d0303c7bbe0e11ed67d3` (v2026.03.14 trixie-debian13-dev)
- Duck.com: privacy email alias in use

- GitHub SU: fine-grained PAT (`github_pat_...`) — connection `conn_fNLu9cx2iEZ2` — all scopes incl. `Workflows: Write`; use for workflow file edits, GitHub Projects GraphQL, and elevated operations

## Communication Channels

- [Channel]: [who/what it's used for]

- GitHub: code reviews, PR tracking, CI/CD via yubi-OS org
- Sauna: agent-assisted dev work, research, PR planning, document drafting

## Workflows

- [Trigger] → [Action]: [tools involved]

- PR draft ready → Sauna reviews and refines: Sauna + GitHub
- Build policy change → Sauna researches Docker Build Policies docs: Sauna + GitHub
- Session export → SESSION_*.zip → committed to `localize/yubiOS` branch of `agent-skills` → reimported at session start by unzipping into workspace; skills land in `skills/sauna/`, documents in `documents/`

## Sauna Capabilities

- When working with meeting notes, Sauna allows Granola access via MCP or (for enterprise customers only) supports the Granola API.
