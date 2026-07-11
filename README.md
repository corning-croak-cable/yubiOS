<div align="center">

<img src="https://raw.githubusercontent.com/yubi-OS/yubiOS/main/assets/logo.png" alt="yubiOS logo" width="220" style="border-radius:16px;"/>

# yubiOS

**FIDO2-first immutable OS - YubiKey is the root of trust**

[![License: LGPL-2.1](https://img.shields.io/badge/license-LGPL--2.1-magenta?style=flat-square)](LICENSE)
[![Status: Groundwork](https://img.shields.io/badge/status-groundwork-blueviolet?style=flat-square)](TODO.md)
[![YubiKey 5](https://img.shields.io/badge/YubiKey-5%20series-ff1493?style=flat-square)](https://www.yubico.com)
[![FIDO2](https://img.shields.io/badge/FIDO2-hidraw-purple?style=flat-square)](https://fidoalliance.org)

*No TPM. No OEM. No trust anchors you don't control.*

</div>

---

## What it is

yubiOS is an immutable, bootc-delivered Linux OS that treats the owner's YubiKey as the user-facing root of trust. It combines:

| Layer | Inspiration | What it gives us |
|---|---|---|
| particleos ethos | [systemd/particleos](https://github.com/systemd/particleos) | Immutable `/usr`, UKIs, dm-verity, composefs, systemd-boot |
| bootc design | [bootc-dev/bootc](https://github.com/bootc-dev/bootc) | OCI image as OS delivery unit, day-2 upgrades via registry pull |
| systemd image model | [Fitting Everything Together](https://0pointer.net/blog/fitting-everything-together.html) | DPS partitions, systemd-repart first boot, A/B sysupdate, systemd-homed |
| YubiKey root of trust | FIDO2 / PIV / OATH | Owner-held trust for signing, unlock, SSH, PAM, and app 2FA |

ARM64 is the primary target platform because it is where yubiOS can own the firmware stack below the UKI through TF-A, OP-TEE, fTPM, and U-Boot. x86-64 remains fully supported above the UKI, but its firmware and optional TPM are platform/OEM trust anchors.

## Trust chain

```text
YubiKey 5
- PIV slot 9c via CCID: Secure Boot / UKI signing with systemd-sbsign + PKCS#11
- FIDO2 hmac-secret via hidraw: LUKS2 root and systemd-homed unlock
- FIDO2 ed25519-sk via hidraw: SSH resident keys
- FIDO2 U2F via hidraw: sudo/login with pam-u2f
- OATH via hidraw: application 2FA
```

Secure Boot signing uses PIV/CCID, not hidraw. Full rationale: [ADR-002](ADR.md#adr-002-secure-boot-signing-via-piv-ccid-not-fido2-hidraw).

## Get yubiOS

yubiOS ships as a multi-arch [bootc](https://github.com/bootc-dev/bootc) OCI image on Docker Hub:

```sh
docker pull 0mniteck/yubios:latest
```

For reproducible installs, pin the image by the digest produced by the latest green `yubiOS-ci.yml` publish for the intended release. Do not treat a run-specific digest in an old PR or research note as evergreen.

Install or upgrade with bootc:

```sh
sudo bootc install to-disk --source-imgref docker://0mniteck/yubios:latest /dev/nvme0n1
sudo bootc switch 0mniteck/yubios:latest
sudo bootc upgrade
```

| | |
|---|---|
| Registry | `docker.io/0mniteck/yubios` |
| Production tags | `latest` plus immutable commit tags |
| Test tags | `dev`, `dev-<sha>` for swu2f TEST-only images |
| Artifact tags | `installer`, `firmware` and per-commit variants |
| Platforms | `linux/amd64`, `linux/arm64` |
| Supply chain | SLSA build provenance + SBOM attestations |

## Build from source

```sh
docker buildx build --policy reset=true,strict=true,filename=yubiOS.rego -t yubiOS .

docker run --rm --privileged --pid=host \
  -v /dev:/dev -v /var/lib/containers:/var/lib/containers \
  yubiOS bootc install to-disk /dev/nvme0n1
```

Every approved base image and GitHub Action SHA lives in [PINNED.md](PINNED.md). That file is the single source of truth for pins.

## Enrollment wizard

On first boot `yubiOS-enroll.service` runs on tty1 and walks through:

1. Secure Boot signing through PIV slot 9c.
2. Disk encryption through FIDO2 hmac-secret.
3. SSH resident key generation through `ed25519-sk`.
4. sudo/login registration through pam-u2f.

Each step is skippable and independently re-runnable. See [ONBOARDING.md](ONBOARDING.md).

## Repo layout

```text
yubiOS/
├── .github/workflows/              # CI, manifest refresh, publish, VM/e2e, integration lanes
├── assets/                         # logo and CI assets
├── mkosi.conf                      # mkosi build path
├── mkosi.conf.d/                   # desktop, minimal, surface, chipsec, and test profiles
├── Containerfile                   # production bootc image
├── Containerfile.dev               # TEST-only swu2f dev image
├── yubiOS.rego                     # OPA/Rego Build Policy
├── renovate.json                   # digest-tracking automation
├── refs/                           # research notes, planning cycles, per-issue implementation specs
├── tests/                          # unit, VM, PKCS#11, and UKI verification tests
├── usr/lib/                        # shipped OS overlay: bootc, dracut, PAM, repart, systemd, yubiOS scripts
├── ADR.md                          # architecture decision records
├── ARCHITECTURE.md                 # trust chain + build pipeline diagrams
├── SPEC.md                         # normative project specification
├── MISSION.md                      # project mission
├── MITIGATE.md                     # threat model and control mapping
├── FUTURE.md                       # post-launch ARM64-owned root-of-trust plan
├── ONBOARDING.md                   # operator enrollment guide
├── PINNED.md                       # approved refs and digests
├── BLOCKERS.md                     # dependency and blocker map
└── TODO.md                         # active planning surface
```

## Requirements

| Component | Minimum |
|---|---|
| YubiKey firmware | 5.2.3 for ed25519-sk |
| systemd | 261 for current measured-boot gates and v261 research targets |
| OpenSSH | 8.2 for FIDO2 key types |
| pam-u2f | 1.3.1 for CVE-2025-23013 fix |
| Platform | arm64/aarch64 primary; x86-64 secondary but fully supported |

## Current research notes

- Latest docs/research planning pass: [refs/planning-cycle-2026-07-11.md](refs/planning-cycle-2026-07-11.md)
- ARM64 zstd EFI zboot / bcvk DirectBoot: [refs/zstd-efi-zboot-bcvk.md](refs/zstd-efi-zboot-bcvk.md)
- LUKS2 FIDO2 e2e coverage: [refs/luks-fido2-e2e-test.md](refs/luks-fido2-e2e-test.md)
- ARM64 fTPM Phase F0: [refs/arm64-ftpm-phase-f0.md](refs/arm64-ftpm-phase-f0.md)
- systemd v261 base-image history: [refs/v261-base-image.md](refs/v261-base-image.md)

All decisions are recorded in [ADR.md](ADR.md), with source-backed research in [refs/](refs/).
