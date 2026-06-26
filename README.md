<div align="center">

<img src="https://raw.githubusercontent.com/corning-croak-cable/yubiOS/main/assets/logo.png" alt="yubiOS logo" width="220" style="border-radius:16px;"/>

# yubiOS

**FIDO2-first immutable OS — YubiKey is the root of trust**

### 🦴 🚧 Work In Progress 🚧 Work In Progress 🚧 Work In Progress 🚧

[![License: LGPL-2.1](https://img.shields.io/badge/license-LGPL--2.1-magenta?style=flat-square)](LICENSE)
[![Status: Groundwork](https://img.shields.io/badge/status-groundwork-blueviolet?style=flat-square)](TODO.md)
[![YubiKey 5](https://img.shields.io/badge/YubiKey-5%20series-ff1493?style=flat-square)](https://www.yubico.com)
[![FIDO2](https://img.shields.io/badge/FIDO2-hidraw-purple?style=flat-square)](https://fidoalliance.org)

*No TPM. No OEM. No trust anchors you don't control.*

</div>

---

## What it is

yubiOS fuses four lineages:

| Layer | Inspiration | What it gives us |
|---|---|---|
| **particleos ethos** | [systemd/particleos](https://github.com/systemd/particleos) | Immutable rootfs, UKI, dm-verity, composefs, systemd-boot |
| **bootc design** | [bootc-dev/bootc](https://github.com/bootc-dev/bootc) | OCI image as OS delivery unit, day-2 upgrades via registry pull |
| **Amutable vision** | [Lennart Poettering + systemd team](https://amutable.com) | "Integrity should be built into every critical infrastructure project" — image-based OS, verifiable integrity, determinism as a default |
| **YubiKey root of trust** | FIDO2 / PIV / OATH | Hardware-bound trust replacing TPM at every boundary |

### Ecosystem alignment

In January 2026 the core systemd team and the engineers behind, composefs, runc, Flatcar,
ParticleOS, and Ubuntu Core — founded [Amutable](https://amutable.com) with the mission:

> *“Deliver determinism and verifiable integrity to Linux workloads everywhere.”*

yubiOS is independently building toward the same architecture, with one additional constraint:
the YubiKey replaces the TPM as the hardware root of trust at every layer. The "Fitting Everything
Together" essay at [0pointer.net](https://0pointer.net/blog/fitting-everything-together.html) is the
primary design reference for yubiOS — hermetic /usr, DPS partitions, systemd-repart first-boot,
A/B sysupdate, systemd-homed per-user encryption, and UKI + dm-verity trust chain.

## Trust chain

```
┌───────────────────────────────────────────┐
│                 YubiKey 5                 │
├───────────────────────────────────────────┤
│ PIV slot 9c (CCID)   Secure Boot signing  │
│ FIDO2 HMAC-secret    Disk unlock (hidraw) │
│ FIDO2 ed25519-sk     SSH keys    (hidraw) │
│ FIDO2 U2F            sudo/login  (hidraw) │
│ OATH TOTP            App 2FA     (hidraw) │
└───────────────────────────────────────────┘
```

> **ADR-002 note:** Secure Boot signing uses PIV/CCID (via `systemd-sbsign` + PKCS#11),
> not hidraw. All other operations run on FIDO2 via `/dev/hidraw*`. Full rationale: [ADR.md](ADR.md)

## Get yubiOS

yubiOS ships as a **multi-arch [bootc](https://github.com/bootc-dev/bootc) OCI image on Docker Hub** — this is the primary download.

**Pull** (auto-selects `amd64` / `arm64`):
```sh
docker pull 0mniteck/yubios:latest
```

**Pin by digest** (reproducible — recommended for installs):
```sh
docker pull 0mniteck/yubios@sha256:c965a816b9173cf6f227e6b5b09e321e841ab5f8a49075c112657a0a40b5e761
```

**Install / upgrade with bootc:**
```sh
sudo bootc install to-disk --source-imgref docker://0mniteck/yubios:latest /dev/nvme0n1
sudo bootc switch 0mniteck/yubios:latest && sudo bootc upgrade
```

| | |
|---|---|
| Registry | `docker.io/0mniteck/yubios` |
| Tags | `:latest` + immutable `:<commit-sha>` per build |
| Platforms | `linux/amd64`, `linux/arm64` |
| Supply chain | SLSA build provenance + SBOM attestations attached |
| Published by | `yubiOS-ci.yml` `merge-manifest` job (current: run #113, `bfbc38f`) |

> Building from source instead? See **Quick start** below.

## Quick start

```sh
# Build the OCI image (per ADR-014: Docker Buildx, not Podman)
docker buildx build --policy reset=true,strict=true,filename=yubiOS.rego -t yubiOS .

# Install to disk (disable Secure Boot in UEFI first)
docker run --rm --privileged --pid=host \
  -v /dev:/dev -v /var/lib/containers:/var/lib/containers \
  yubiOS bootc install to-disk /dev/nvme0n1

# First boot: the enrollment wizard runs automatically
# Or launch it manually:
yubiOS-enroll
```

## Enrollment wizard

On first boot `yubiOS-enroll.service` fires on tty1 and walks through:

```
 ─── Step 1/4: Secure Boot Signing ───
 ─── Step 2/4: Disk Encryption (FIDO2 hidraw) ───
 ─── Step 3/4: SSH Key (ed25519-sk resident) ───
 ─── Step 4/4: sudo / Login Auth (U2F pam-u2f) ───
```

Each step is skippable. Each script is independently re-runnable. See [ONBOARDING.md](ONBOARDING.md).

## Repo layout

```
yubiOS/
├── Containerfile              # OCI image (bootc, Fedora base)
├── mkosi.conf                 # mkosi build (particleos-style UKI + verity)
├── assets/logo.png            # you're looking at it
├── usr/lib/
│   ├── bootc/install/           # bootc install config (systemd-boot, DPS)
│   ├── bootc/kargs.d/           # persistent kernel args
│   ├── dracut.conf.d/           # fido2 dracut module for boot-time disk unlock
│   ├── udev/rules.d/            # YubiKey hidraw + CCID uaccess rules
│   ├── pam.d/                   # PAM U2F sudo config template
│   ├── systemd/system/          # enrollment service + presets
│   └── yubiOS/                  # enrollment scripts
├── ADR.md                     # architecture decision records
├── ONBOARDING.md              # step-by-step onboarding guide
└── TODO.md                    # known gaps + future work
```

## Requirements

| | Minimum |
|---|---|
| YubiKey firmware | 5.2.3 (ed25519-sk) |
| systemd | **261** (systemd-sbsign, systemd-cryptenroll FIDO2; v261 adds `ConditionSecurity=measured-os`, `RestrictFileSystems=`) |
| OpenSSH | 8.2 (FIDO2 key types) |
| pam-u2f | **1.3.1** (CVE-2025-23013 fix) |
| Platform | **x86-64** (primary); **arm64/aarch64** (in development — see ADR-017) |

## Design decisions

```
  quay.io/fedora/fedora-bootc:45  @sha256 (pinned base — ADR-003)
                 |
        +--------+---------------------+
        v Containerfile                v mkosi --profile yubios
  rootless docker buildx          UKI + dm-verity, signed via
  --policy yubiOS.rego            YubiKey PIV slot 9c (PKCS#11)
  (supply-chain gate)                  |
        +--------+---------------------+
                 v   multi-arch OCI image  (linux/amd64 + linux/arm64)
        yubiOS-ci.yml . merge-manifest . SLSA provenance + SBOM attested
                 |  docker push
                 v
   +-------------------------------------------------+
   | docker.io/0mniteck/yubios:latest                |  <== PRIMARY DOWNLOAD
   | (+ immutable :<commit-sha> per build)           |
   +-------------------------------------------------+
                 |  pull
   +-------------+------------------+---------------------------------+
   v bootc install                  v bootc switch + upgrade          v bcvk
     to-disk (bare metal)             day-2 atomic update              ephemeral VM / native-to-disk
   |                                                                   (test loop, USB YubiKey passthrough)
   v  first boot -> yubiOS-enroll.service -> YubiKey tap
   +-------------+----------------------+------------------------------+
   v PIV slot 9c (CCID)                 v FIDO2 (hidraw)               v systemd-homed
  Secure Boot signing                 LUKS2 disk unlock              LUKS2 /home
  (systemd-sbsign / PKCS#11)          SSH ed25519-sk, pam-u2f         +- SLOT 0  FIDO2 unlock
                                                                      +- SLOT 1  recovery key
```


```
All decisions are recorded in [ADR.md](ADR.md) with sources.
The short version: TPM replaced by YubiKey everywhere it can be.
```
