<div align="center">

<img src="https://raw.githubusercontent.com/corning-croak-cable/yubiOS/main/assets/logo.png" alt="yubiOS logo" width="220" style="border-radius:16px;"/>

# yubiOS

**FIDO2-first immutable OS — YubiKey is the root of trust**

[![License: LGPL-2.1](https://img.shields.io/badge/license-LGPL--2.1-magenta?style=flat-square)](LICENSE)
[![Status: Groundwork](https://img.shields.io/badge/status-groundwork-blueviolet?style=flat-square)](TODO.md)
[![YubiKey 5](https://img.shields.io/badge/YubiKey-5%20series-ff1493?style=flat-square)](https://www.yubico.com)
[![FIDO2](https://img.shields.io/badge/FIDO2-hidraw-purple?style=flat-square)](https://fidoalliance.org)

*No TPM. No OEM. No trust anchors you don't control.*

</div>

---

## What it is

yubiOS fuses three lineages:

| Layer | Inspiration | What it gives us |
|---|---|---|
| **particleos ethos** | [systemd/particleos](https://github.com/systemd/particleos) | Immutable rootfs, UKI, dm-verity, composefs, systemd-boot |
| **bootc design** | [bootc-dev/bootc](https://github.com/bootc-dev/bootc) | OCI image as OS delivery unit, day-2 upgrades via registry pull |
| **YubiKey root of trust** | FIDO2 / PIV / OATH | Hardware-bound trust replacing TPM at every boundary |

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

> **ADR-002 note:** Secure Boot signing uses PIV/CCID, not hidraw.
> All other operations run on FIDO2 via `/dev/hidraw*`. Full rationale: [ADR.md](ADR.md)

## Quick start

```sh
# Build the OCI image
podman build -t yubiOS .

# Install to disk (disable Secure Boot in UEFI first)
podman run --rm --privileged --pid=host \
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
| systemd | 248 (systemd-cryptenroll FIDO2) |
| OpenSSH | 8.2 (FIDO2 key types) |
| pam-u2f | **1.3.1** (CVE-2025-23013 fix) |

## Design decisions

```
mkosi --profile yubios build
          ↓
    OCI image (yubios:latest)
          ↓
bcvk native-to-disk yubios:latest /dev/sdb
          ↓
    first boot → yubios-enroll.service → YubiKey tap
                                              │
                                              ▼ 
                                              ─────► YubiKey (PIV slot 9c)
                                                         │
                                                         ▼ sbsign via PKCS11
                                                    mkosi fork ──────────► OCI container image (yubiOS)
                                                         │                         │
                                                         │                         ▼ bootc install/upgrade
                                                         │                   bare metal / VM disk
                                                         │
                                                         └─────► bcvk fork ──────► ephemeral VM (test)
                                                                      │                  ▲
                                                                      └── USB passthrough YubiKey hidraw
```

All decisions are recorded in [ADR.md](ADR.md) with sources.
The short version: TPM replaced by YubiKey everywhere it can be.
Where FIDO2/hidraw can't reach (Secure Boot signing), PIV/CCID is used and documented honestly.
