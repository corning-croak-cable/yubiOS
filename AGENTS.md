# AGENTS.md

This file provides guidance to AI coding agents (Claude Code, Cursor, Copilot, Antigravity, etc.) when working with code on yubiOS/{{repos}}.
Prefer the skills and knowledge referenced from this file over ad-hoc per-repo instructions; let's go fast and make some stuff!

Warning: Rate limit your api calls to github to avoid lockout, allow cooldowns. Always keep copies of created work in your cache in the knowledge files first, then push.

## First off restore sessions/cache

Always start by importing any previously unseen sessions/SESSION_*.zip, unzipping, and ingesting the files into your skills, cache, history, profiles, knowledge, and general files.

Rescan and organize all knowledge files and skills looking for crossover and changes, always update working directories in knowledge with INDEX.md and OVERVIEW.md files.

Then incorporate the rest of the skills from this file, org, and repo; as well as absorb any references and docs. Look for and fill in knowledge gaps and any changes in repos and files and keep it in the top level INDEX.md knowledge file.

Consider this [AGENTS.md](https://github.com/yubi-OS/yubiOS/raw/refs/heads/main/AGENTS.md) as primary and to always combine together with the constantly updated skills/knowledge referenced from [AGENTS.md](https://github.com/yubi-OS/agent-skills/raw/refs/heads/main/AGENTS.md)

Always check for and update stale skills and knowledge that have upstream changes or during AGENTS.md ingestion; ie. a Refresh skills SKILL.

Finally reassess and update the TODO.md in this branch with relevant next steps.

## Repository Overview - https://github.com/yubi-OS/yubiOS

FIDO2-first immutable OS: YubiKey as root of trust for Secure Boot, disk encryption, SSH, and PAM — no TPM, no OEM dependency
This is the primary repo for the org at https://github.com/yubi-OS

## Hands-off .repos

Do NOT use or modify any repo that contains a decimal or period anywhere in the name. Does not restrict folders or files just the repo.

## Project Repository List
```

<https://github.com/>\
│ yubi-OS/ # Org-level\
├───────────────────── yubiOS/ # Main Project\
├───────────────────── bootc/ # Bootable OCI images (fork)\
├───────────────────── bcvk/ # Bootc virtualization kit — CI test VM + image installer/upgrader (fork)\
├───────────────────── mkosi/ # OS container image builder (fork)\
├───────────────────── particleos/ # Reference implementation (fork)\
│\
│ ARM64 fTPM stack (post-launch, ADR-018/019/020/021):\
├───────────────────── arm-trusted-firmware/ # TF-A BL31 — PLAT=rk3588, ROTPK, FIP, TBB (fork)\
├───────────────────── optee_os/ # BL32 secure-world OS — PLATFORM=rockchip, RPMB, Early TA (fork)\
├───────────────────── optee_ftpm/ # fTPM TA — ms-tpm-20-ref integration, UUID bc50d971 (fork)\
├───────────────────── u-boot/ # BL33 + UEFI — EFI_LOADER, TPM2_FTPM_TEE, measured boot (fork, ADR-021)\
├───────────────────── ms-tpm-20-ref/ # TPM 2.0 reference — pinned 98b60a44 (fork)\
├───────────────────── edk2/ # EDK2 StandaloneMM variable service for UEFI Secure Boot vars on RPMB (fork)\
├───────────────────── edk2-rk3588/ # EDK2 UEFI for RK3588 boards — reference only, not active path (fork, ADR-021)\
│\
DO NOT USE ───── yubi-OS/\
├───────────────────── .example/ # HANDS OFF\
├───────────────────── .github/ # HANDS OFF\
├───────────────────── ,[yubi-OS.github.io/](http://yubi-OS.github.io/) # HANDS OFF\
│

```

## Default (preferred) Images

**PINNED.md is the single source of truth for every approved digest and action SHA.**
Do not hardcode or duplicate digests here — look them up in
[PINNED.md](https://github.com/yubi-OS/yubiOS/raw/refs/heads/main/PINNED.md) and keep that
file current. The notes below show the shape; the authoritative values live in PINNED.md.

```
**in OCI for dockerfiles and .rego** (use the multi-arch INDEX digest from PINNED.md)
docker pull dhi.io/debian-base:trixie-debian13-dev@sha256:1cefd55d979ddbd9110cf73cf3de11798a7893a4598050ba57624bc754b244aa
docker buildx build --policy reset=true,strict=true,filename=$REPO.rego .

**in Github workflow** (INDEX digest auto-resolves per runner arch — required for amd64+arm64 matrices)
runs-on: ubuntu-24.04            # or ubuntu-24.04-arm for native arm64
container:
  credentials:
    username: 0mniteck42
    password: ${{secrets.DOCKER}}
  image: docker://dhi.io/debian-base@sha256:1cefd55d979ddbd9110cf73cf3de11798a7893a4598050ba57624bc754b244aa # trixie-debian13-dev INDEX (manifest list)
Steps
  - name: Checkout
    uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # see PINNED.md

**Multi-arch CI:** prefer a native matrix split (ubuntu-24.04 + ubuntu-24.04-arm, runs-on from
the matrix) over QEMU emulation — see yubiOS-ci.yml. arm64 hosted runners are free on public repos.

**Allowed actions + images:** see PINNED.md. Every `uses:` and image `FROM` must reference a SHA pinned there.
```

Finally go ahead and do some deep research on the following links section.

## Deep Research Links

- <https://www.man7.org/linux/man-pages/man5/systemd.exec.5.html>
- <https://www.man7.org/linux/man-pages/man5/systemd.unit.5.html>
- <https://www.man7.org/linux/man-pages/man5/systemd.service.5.html>
- <https://man7.org/linux/man-pages/man7/systemd.directives.7.html>
- <https://0pointer.net/blog/fitting-everything-together.html>
- <https://0pointer.net/blog/> # Build or update 0pointer SKILL - Mastery and big picture
- <https://docs.docker.com/>
- <https://docs.docker.com/build/policies/intro/>
- <https://docs.docker.com/build/policies/intro/examples/>
- <https://docs.docker.com/build/policies/intro/intro/>
- <https://docs.docker.com/build/policies/intro/usage/>
- <https://pq.cloudflareresearch.com/>
- <https://docs.github.com/en/actions>
- <https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions>
- <https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows>
- <https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication>
- <https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions>
- <https://docs.github.com/en/rest/actions>
- <https://docs.github.com/en/rest/actions/workflow-runs>
- <https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event>
