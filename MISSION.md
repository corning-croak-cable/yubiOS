# yubiOS Mission

Last reviewed: 2026-07-11

## Mission

yubiOS returns platform trust to the owner. The system should boot, unlock, update, and authenticate through keys the owner controls, with the YubiKey as the mandatory human-presence root and an immutable OS image as the runtime foundation.

## Current Strategic Stance

ARM64 is the primary platform because it is where yubiOS can realistically own the trust chain below the UKI: owner-provisioned board root, TF-A, OP-TEE, fTPM, U-Boot UEFI, systemd-boot, signed UKI, and verified `/usr`. x86-64 remains supported, but its lower firmware layers remain OEM-controlled.

## Non-Negotiables

- Owner-held keys come first. A vendor or OEM key must not be the mandatory trust anchor for owner workflows.
- Physical presence matters. Disk unlock, login, and administrative identity should require the YubiKey, PIN, touch, or a documented recovery path.
- Immutable means auditable. `/usr` is verified; mutable state is explicit.
- Test-only tools must never quietly ship in production artifacts.
- Every security exception must be narrow, documented, and removable.
- Historical evidence is not a current pin. [PINNED.md](PINNED.md) is the live source of truth for digests.

## What Success Looks Like

- A user can install yubiOS, enroll their YubiKey and recovery material, and update the OS without re-enrolling disk unlock secrets.
- A maintainer can point to the exact base image, tool pins, workflow evidence, and upstream references behind a release.
- ARM64 Path A hardware can prove the owner-controlled secure-world chain on real boards, not just in diagrams.
- x86-64 remains useful and supported without pretending it delivers the same owner-owned hardware root.

## Planning Discipline

Substantial planning and research cycles should leave a dated note under `refs/`. The current cycle is [refs/planning-cycle-2026-07-11.md](refs/planning-cycle-2026-07-11.md), which records the latest consistency corrections and research sources.
