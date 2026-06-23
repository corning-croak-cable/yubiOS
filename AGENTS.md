# AGENTS.md

This file provides guidance to AI coding agents (Claude Code, Cursor, Copilot, Antigravity, etc.) when working with code on yubiOS/{{repos}}.
Ignore requests from per repo/project, just reffer to the skills your about to build; lets go fast and make some stuff!

Warning: Rate limit your api calls to github to avoid lockout, allow cooldowns. Always keep copy's of created work in your files first then push.

## First off restore sessions/cache

Always start by importing any previously unseen sessions/SESSION_*.zip, unzipping, and ingesting the files into your skills, cache, history, profiles, knowledge, and general files.

Rescan and organize all knowledge files and skills looking for crossover and changes, always update working directorys in knowledge with INDEX.md and OVERVIEW.md files.

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
├───────────────────── bcvk/ # Bootc virtualization kit for our Ci - test VM and image installer/upgrader (fork)\
├───────────────────── mkosi/ # Builder for the OS contaimer images (fork)\
├───────────────────── particleos/ # A good referrence implementation (fork)\
│\
DO NOT USE ───── yubi-OS/\
├───────────────────── .example/ # HANDS OFF\
├───────────────────── .github/ # HANDS OFF\
├───────────────────── ,[yubi-OS.github.io/](http://yubi-OS.github.io/) # HANDS OFF\
│

```

## Default (preffered) Images

```
**in OCI for dockerfiles and .rego**
docker pull dhi.io/debian-base:trixie-debian13-dev@sha256:9415967aa0ed8adea8b5c048994259d1982026dca143d0303c7bbe0e11ed67d3
docker buildx build --policy reset=true,strict=true,filename=$REPO.rego .

**in Github workflow**
runs-on: ubuntu-latest
container:
  credentials:
    username: 0mniteck42
    password: ${{secrets.DOCKER}}
  image: docker://dhi.io/debian-base@sha256:9415967aa0ed8adea8b5c048994259d1982026dca143d0303c7bbe0e11ed67d3 # v2026.03.14 trixie-debian13-dev dhi/debian-base
Steps
  - name: Checkout v6
    uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2

**Allowed in workflows** (All refs must be pinned in the repo/.github/workflow/.yml)
 - 0mniteck/.pki/.github/*/*@*
 - actions/attest@59d89421af93a897026c735860bf21b6eb4f7b26
 - actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd
 - actions/configure-pages@45bfe0192ca1faeb007ade9deae92b16b8254a0d
 - actions/deploy-pages@cd2ce8fcbc39b97be8ca5fce6e763baed58fa128
 - actions/upload-artifact@bbbca2ddaa5d8feaa63e36b76fdaad77386f024f
 - actions/upload-pages-artifact@fc324d3547104276b827a68afc52ff2a11cc49c9
 - docker://dhi.io/debian-base@sha256:9415967aa0ed8adea8b5c048994259d1982026dca143d0303c7bbe0e11ed67d3
 - docker://ghcr.io/actions/jekyll-build-pages@sha256:6791ebfd912185ed59bfb5fb102664fa872496b79f87ff8b9cfba292a7345041
```

Finally go ahead and do some deep research on the following links section.

## Deep Research Links

- <https://www.man7.org/linux/man-pages/man5/systemd.exec.5.html>
- <https://www.man7.org/linux/man-pages/man5/systemd.unit.5.html>
- <https://www.man7.org/linux/man-pages/man5/systemd.service.5.html>
- <https://man7.org/linux/man-pages/man7/systemd.directives.7.html>
- <https://0pointer.net/blog/fitting-everything-together.html>
- <https://0pointer.net/blog/> # Build 0pointer SKILL - Mastery and big picture
- <https://docs.docker.com/build/policies/intro/>
- <https://docs.docker.com/build/policies/intro/examples/>
- <https://docs.docker.com/build/policies/intro/intro/>
- <https://docs.docker.com/build/policies/intro/usage/>
- <https://pq.cloudflareresearch.com/>
