# yubios

> An immutable, FIDO2-first OS image. YubiKey is the root of trust.
> No TPM. No OEM. No trust anchors you don't control.

## What it is

yubios combines:
- **particleos ethos** — immutable filesystem, UKI, dm-verity, systemd-boot, composefs
- **bootc design** — OCI container image as the OS delivery unit, day-2 upgrades via registry pull
- **YubiKey as root of trust** — FIDO2/U2F replaces the TPM for every security operation

The YubiKey is present at every trust boundary:

| Operation | Protocol | Interface |
|---|---|---|
| Secure Boot signing | PIV (PKCS#11) | CCID / USB |
| Disk encryption unlock | FIDO2 HMAC-secret | hidraw |
| SSH authentication | FIDO2 (ed25519-sk) | hidraw |
| sudo / login | FIDO2 U2F (pam-u2f) | hidraw |
| App-level 2FA | OATH TOTP (ykman) | OTP / CCID |

> **Design note:** Secure Boot signing uses the PIV/CCID interface, not hidraw.
> All other operations use FIDO2 via `/dev/hidraw*`. See [ADR.md](ADR.md) for why.

## Quick start

    # Build OCI image
    podman build -t yubios .

    # Install to disk (Secure Boot disabled first in UEFI)
    podman run --rm --privileged --pid=host \
      -v /dev:/dev -v /var/lib/containers:/var/lib/containers \
      yubios bootc install to-disk /dev/nvme0n1

    # On first boot: run the enrollment wizard
    yubios-enroll

## Onboarding

See [ONBOARDING.md](ONBOARDING.md) for the full guided walkthrough.

## Architecture

See [ADR.md](ADR.md) for all design decisions with sources.

## Status

Groundwork / early development. Enrollment scripts are functional.
mkosi build path and full verity integration are in progress.
