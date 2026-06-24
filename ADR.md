# Architecture Decision Records — yubiOS

## ADR-001: YubiKey as TPM replacement

**Status:** Accepted

**Context:** Most secure-boot / disk-encryption stacks assume a TPM 2.0 chip.
TPMs are OEM-controlled, soldered to specific motherboards, and can be provisioned
with vendor keys the user never sees.

**Decision:** Use the YubiKey 5 series as the sole trust anchor.

**Rationale:**
- Hardware-bound key material that travels with the user, not the board
- Open specification (FIDO2/CTAP2, PIV/PKCS#11, OATH)
- Touch-required by default — no silent decryption
- User-generated keys: no OEM or manufacturer trust chain

**Trade-offs:**
- Lost YubiKey = locked out without recovery key; document recovery in ONBOARDING.md
- Single point of failure; recommend enrolling a backup YubiKey
- FIDO2 credentials are device-bound; cannot be backed up cryptographically

---

## ADR-002: Secure Boot signing via PIV (CCID), not FIDO2 (hidraw)

**Status:** Accepted

**Context:** The user wants YubiKey /dev/hidraw* interfaces throughout.
Secure Boot UKI signing requires an asymmetric signing operation with a
certificate that can be enrolled in the UEFI Secure Boot `db`.

**Decision:** Use YubiKey PIV slot 9c (Digital Signature) via PKCS#11 for
Secure Boot key material. Interface: CCID (USB smartcard), not hidraw.

**Signing toolchain:** Use `systemd-sbsign` (systemd v257+) via `--key pkcs11:…`.
This replaces legacy `sbsigntools` (`sbsign --engine pkcs11`). Both speak PKCS#11;
systemd-sbsign integrates tighter with the UKI pipeline and is now the upstream default.

**Why not FIDO2 for signing:**
- FIDO2 HMAC-secret CAN wrap a signing key (key encrypted on disk, FIDO2
  derives the AES key), but neither `sbsign` nor `systemd-sbsign` support this path natively.
- PIV/PKCS#11 is directly supported and battle-tested in all signing tools.
- Source: https://developers.yubico.com/yubico-piv-tool/

**Future:** A fully hidraw-only signing path (FIDO2 HMAC-secret wrapping a
Secure Boot key) is tracked in TODO.md. `age-plugin-fido2-hmac` is a candidate.

**Consequence:** Users need `pcscd` running for PIV ops. ykman must have CCID enabled.
    ykman config usb --enable FIDO --enable CCID

---

## ADR-003: LUKS2 + FIDO2 via systemd-cryptenroll (no TPM)

**Status:** Accepted

**Decision:** Disk encryption uses LUKS2 with `systemd-cryptenroll --fido2-device=auto`.
No TPM slot is enrolled.

**Rationale:**
- FIDO2 credential (HMAC-secret extension) stored in LUKS2 token header — no TPM needed
- Disk unlockable on any machine with the YubiKey (TPM-bound disks are board-locked)
- Touch required at every boot — prevents silent decryption
- FIDO2 enrollment does NOT bind to PCR hash values, so OS updates never require
  re-enrollment (unlike TPM2 PCR-hash policies which break on every kernel/initrd change)
- Source: https://www.freedesktop.org/software/systemd/man/latest/systemd-cryptenroll.html

**PIN policy:** `--fido2-with-client-pin=yes` is the default in yubiOS.
Requires FIDO2 PIN + touch at boot. Strongest available option without biometrics.

**Recovery key:** `systemd-cryptenroll --recovery-key` MUST be enrolled alongside
FIDO2. This is the only escape hatch if the YubiKey is lost or damaged.
Print the recovery key and store it physically offline.

**Boot phase binding:** The DEK is sealed to PCR 11 phase word `initrd-enter`.
Once the boot phase transitions (`initrd-leave` measured), the DEK can no longer be
unsealed from userspace — protects against post-boot extraction.

**Dracut:** The `fido2` dracut module must be enabled for FIDO2 unlock at boot.
This ships in `usr/lib/dracut.conf.d/50-yubiOS-fido2.conf`.

---

## ADR-004: ed25519-sk resident keys for SSH

**Status:** Accepted

**Decision:** SSH uses `ed25519-sk` with `-O resident` (discoverable credentials).

**Rationale:**
- Private key never leaves YubiKey; only a credential ID + public key stub on disk
- `-O resident` stores the key in YubiKey internal FIDO2 storage (limited slots)
- `ssh-keygen -K` can regenerate the stub on a new machine from the YubiKey alone
- `-O verify-required` forces FIDO2 PIN on every SSH use (stronger than touch-only)
- Source: https://www.openssh.com/txt/release-8.2 (OpenSSH 8.2 FIDO2 support)
- Source: libfido2 v1.16.0, hidraw communication verified

**Requires:** OpenSSH >= 8.2, libfido2 >= 1.10, YubiKey firmware >= 5.2.3 for ed25519-sk

---

## ADR-005: pam-u2f >= 1.3.1 required (CVE-2025-23013)

**Status:** Accepted

**Decision:** pam-u2f is used for sudo and login. Minimum version 1.3.1.

**Rationale:**
- CVE-2025-23013: partial authentication bypass in pam-u2f < 1.3.1
- Source: https://www.yubico.com/support/security-advisories/ysa-2025-01/
- `auth required pam_u2f.so` (not `sufficient`) — YubiKey touch always needed
- `authfile=/etc/yubico/u2f_keys` centralises enrolled keys for easier audit

**Recovery:** If YubiKey is lost, boot to emergency shell (add `rd.break` karg),
mount rootfs, comment out pam_u2f line in /etc/pam.d/sudo.

---

## ADR-006: Both mkosi and bootc build paths

**Status:** Accepted

**Decision:** Provide both `mkosi.conf` (particleos ethos) and `Containerfile` (bootc design).

**Rationale:**
- mkosi path: UKI with embedded verity, signed at build time, particleos-style offline build
- bootc path: OCI image, day-2 upgrades via `bootc upgrade`, registry-pull workflow
- Both consume the same `usr/` overlay tree; identical runtime behavior
- Maintainers can choose based on deployment model

**mkosi produces:** signed UKI `.efi`, dm-verity root, composefs image
**bootc produces:** OCI image deployable via `bootc install to-disk`

---

## ADR-007: composefs + dm-verity for immutable root

**Status:** Accepted

**Decision:** Use composefs over a dm-verity-checked erofs partition for the
read-only root filesystem, following the particleos pattern.

**Rationale:**
- composefs provides a cryptographically-verified directory tree via fs-verity
- erofs backing store is signed by systemd-repart's verity support
- Roothash is embedded in the UKI kernel cmdline at build time — tampering is
  detected before any userspace runs
- Fully compatible with bootc day-2 upgrades: each new OCI layer produces a
  new erofs+verity pair; old layers are garbage-collected

**Implementation:**
- dracut: `add_dracutmodules+=" composefs dm-verity"` in 51-yubiOS-composefs.conf
- repart: `Type=root` + `Verity=data` + matching `Type=root-verity` in 50-yubiOS-root.conf
- mkosi: `Verity=signed` already set in mkosi.conf

**Source:** https://github.com/containers/composefs

---

## ADR-008: systemd-sbsign over legacy sbsigntools

**Status:** Accepted

**Context:** Two tools can sign UEFI PE binaries (UKIs) via PKCS#11: legacy `sbsign`
(sbsigntools project) and `systemd-sbsign` added in systemd v257 (Dec 2024).

**Decision:** Use `systemd-sbsign` as the UKI signing tool going forward.

**Rationale:**
- `systemd-sbsign` is maintained inside the systemd tree — same release cycle, same
  PKCS#11 integration, co-developed with `ukify` and the unified kernel image pipeline
- Supports `--key pkcs11:slot=0;id=02` (YubiKey PIV slot 9c) natively
- Generates and verifies PCR 11 signatures in one step (`--pcr-private-key` /
  `--pcr-public-key`) alongside the SecureBoot signature — no separate invocations
- Upstream mkosi switched its signing backend to `systemd-sbsign` in v25+
- Source: https://www.freedesktop.org/software/systemd/man/latest/systemd-sbsign.html
- Source: https://0pointer.net/blog/announcing-systemd-v257.html

**Migration:** Replace any `sbsign --engine pkcs11 --key …` invocations in
FinalizeScripts and CI with `systemd-sbsign --key pkcs11:… --certificate cert.pem`.

**Consequence:** Requires systemd >= 257. Debian Trixie ships systemd 257.x.

---

## ADR-009: systemd-homed for per-user LUKS2+FIDO2 home directories

**Status:** Accepted

**Context:** Traditional Linux home directories rely on system-wide FDE for data protection.
This means all users share one encryption key; any system compromise exposes all user data,
and data is readable whenever the system is unlocked — including during suspend.

**Decision:** Use systemd-homed for all user home directories. Each home is an independent
LUKS2-encrypted volume unlocked by the user's own YubiKey FIDO2 credential.

**Rationale:**
- Per-user encryption: user data cryptographically inaccessible even when system is running
  but the user is not logged in
- Suspend security: homed locks (flushes LUKS2 keys) before system suspend; resumes only
  after YubiKey re-authentication — key never sits in RAM during suspend
- Portable homes: LUKS2 volume is a self-contained file; can migrate between machines with
  `homectl adopt` without re-encryption
- Dynamic UID assignment at login via uidmap mounts — no fixed UID conflicts across machines
- Source: https://0pointer.net/blog/authenticated-boot-and-disk-encryption-on-linux.html
  (section: How to Encrypt/Authenticate the User's Home Directory)

**Implementation:**
- `homectl create --fido2-device=auto <user>` at first boot (enrollment wizard step)
- Backup token: `homectl update --fido2-device=auto <user>` for second YubiKey
- Signing key management (v258+): `homectl add-signing-key <user>` for portable home
  migration between machines
- btrfs is required for the home volume filesystem (online resize support)

**v258 additions used:**
- `homectl add-signing-key` — enroll FIDO2 signing key for portable home across machines
- `homectl adopt` — import an existing home onto a new machine
- `homectl list-signing-keys` — audit enrolled keys

---

## ADR-010: Discoverable Partitions Specification (DPS) — no /etc/fstab

**Status:** Accepted

**Context:** Traditional Linux installations encode mount points in /etc/fstab, which lives
inside the root filesystem — creating a circular dependency (you need the root fs to know
where the root fs is). Boot loader configs duplicate this information, creating drift.

**Decision:** Partition all yubiOS disks using GPT partition type UUIDs from the
Discoverable Partitions Specification. Ship no /etc/fstab. Let systemd-gpt-auto-generator
handle all mount discovery at boot.

**Rationale:**
- DPS UUIDs are self-describing: partition type encodes role (/usr, root, home, swap,
  ESP, verity data, verity sig) and architecture — no external config needed
- Same disk image boots on bare metal, in a VM, and in a systemd-nspawn container with
  zero configuration changes — all three entry points understand DPS
- systemd-dissect, systemd-repart, systemd-nspawn, systemd-gpt-auto-generator all consume
  DPS natively; the same toolset handles image introspection, provisioning, and booting
- A/B versioning is encoded in GPT partition labels (`yubiOS_0.8`) — strverscmp() picks
  the newest automatically in every tool that dissects the image
- Source: https://systemd.io/DISCOVERABLE_PARTITIONS
- Source: https://0pointer.net/blog/the-wondrous-world-of-discoverable-gpt-disk-images.html

**Partition layout (shipped image):**

    (1) ESP              — systemd-boot + UKI
    (2) /usr A           — squashfs, immutable, Verity-protected, label: yubiOS_<ver>
    (3) /usr A verity    — Merkle tree data
    (4) /usr A sig       — PKCS#7 signature of Verity root hash

**Created on first boot by systemd-repart:**

    (5-7) /usr B + verity + sig  — initially _empty, filled on first update
    (8)   root fs                — LUKS2 btrfs, YubiKey FIDO2 enrolled
    (9)   home fs                — integrity-protected, systemd-homed per-user LUKS2
    (10)  swap                   — encrypted

---

## ADR-011: FIDO2 HMAC-secret enrollment survives OS updates (vs TPM2 PCR re-enrollment)

**Status:** Accepted

**Context:** When using TPM2 PCR-hash policies for LUKS2 unlock, every kernel, initrd, or
boot configuration change produces new PCR values — invalidating the existing enrollment.
Users must re-enroll the LUKS2 volume after every OS update, or pre-enroll future PCR
values using signed PCR policies (complex, distribution-dependent).

**Decision:** yubiOS uses FIDO2 HMAC-secret for all LUKS2 enrollments and does NOT bind
to TPM PCR hash values. Updates require zero re-enrollment.

**Rationale:**
- FIDO2 HMAC-secret produces a deterministic key from (credential_id, salt, PIN) —
  this key is independent of what OS or kernel version is running
- Updating the UKI, rebuilding the initrd, or changing kernel args has no effect on
  the LUKS2 token — it will still unlock on next boot with the same YubiKey + PIN
- Contrast with TPM2 PCR policies: PCR 11 changes on every UKI rebuild (different hash);
  the enrolled DEK is inaccessible unless the PCR policy is updated ahead of each update
- The signed PCR policy approach (Brave New Trusted Boot World, 2022) does solve the
  update problem for TPM2, but requires a distribution-maintained signing infrastructure;
  FIDO2 achieves the same update-survivability with hardware possession as the proof
- Source: https://0pointer.net/blog/unlocking-luks2-volumes-with-tpm2-fido2-pkcs11-security-hardware-on-systemd-248.html
  (Future section: notes TPM2 PCR re-enrollment complexity)
- Source: https://0pointer.net/blog/brave-new-trusted-boot-world.html
  (signed PCR policy design — this is what we avoid needing by using FIDO2)

**Trade-off:** FIDO2 does not verify *which OS* is running before releasing the key —
the disk will unlock if the correct YubiKey is present regardless of the boot environment.
This is a conscious trade-off: the YubiKey's physical possession requirement provides the
equivalent protection, and it avoids OEM/distribution trust dependencies.

---

## ADR-012: systemd-repart for first-boot partitioning (no traditional installer)

**Status:** Accepted

**Context:** Traditional OS installation involves running an installer that provisions
partitions, generates encryption keys, and configures the system — before the first real
boot. This means cryptographic keys are generated outside the target device, creating
opportunities for leakage during manufacturing or distribution.

**Decision:** yubiOS ships a minimal disk image (ESP + /usr A only). All remaining
partitions are created and encrypted by systemd-repart running from the initrd on first boot.
Cryptographic key material for the root filesystem is generated on the target device and
never leaves it.

**Rationale:**
- First-boot key generation: LUKS2 root fs key is created by systemd-repart on the target
  device; never exists on the build host or in transit
- Live image = installer image: `dd` the shipped image to a USB stick, it IS the installer;
  no separate installer artifact needed
- Adaptive sizing: systemd-repart reads the physical disk size and sizes the root fs
  partition to fill available space — no fixed-size pre-allocation
- Factory reset is the inverse: systemd-repart erases partitions 8-10 on next boot and
  recreates them with fresh keys (triggered via EFI variable or kernel argument)
- Source: https://0pointer.net/blog/fitting-everything-together.html
  (section: OS Installation vs. OS Instantiation)
- Source: https://www.freedesktop.org/software/systemd/man/latest/systemd-repart.html

**Implementation:**
- `usr/lib/repart/` directory contains partition definitions
- `bootc/install/` config passes `--repart-offline` to systemd-repart
- YubiKey FIDO2 enrollment runs from the `yubiOS-enroll.service` on first console login
  after repart creates the LUKS2 volume

---

## ADR-013: A/B updates via systemd-sysupdate + Boot Assessment counters

**Status:** Accepted

**Context:** OS updates are the most dangerous system operation: a failed update can render
a device unbootable. yubiOS needs atomic, rollback-capable updates that degrade gracefully
on failure without requiring user intervention.

**Decision:** Use systemd-sysupdate for A/B partition updates with Boot Assessment
counters embedded in UKI filenames.

**Mechanism:**
- Each update downloads 4 artifacts: new /usr partition, its Verity data partition,
  its PKCS#7 signature partition, and a new UKI into the ESP
- The new UKI filename includes a boot counter: `yubiOS_0.9+3`
- systemd-boot decrements the counter on each boot attempt. If the counter reaches zero,
  that UKI is excluded from the boot menu and the system falls back to the previous version
- On successful boot, userspace calls `bootctl set-boot-good` to strip the counter
  (marking the entry permanently good)
- Version selection is automatic: `strverscmp()` on partition labels and UKI filenames;
  newest version is always preferred without manual intervention

**Source:** https://systemd.io/AUTOMATIC_BOOT_ASSESSMENT
**Source:** https://0pointer.net/blog/fitting-everything-together.html (section: Updating Images)

**Consequence:**
- The `yubiOS-upgrade.service` unit must call `bootctl set-boot-good` after verifying
  a successful boot (network up, key services healthy)
- Rollback is automatic if the counter hits zero — but active monitoring should alert on
  rollback events so regressions are caught before affecting all deployed instances
