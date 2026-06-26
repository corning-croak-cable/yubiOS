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

**Signing toolchain:** Use `systemd-sbsign` (systemd v257+; yubiOS base is now pinned to v261+, see ADR-015 and ADR-016) via `--key pkcs11:…`.
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

**v261 (June 19, 2026):** No regressions for this ADR. `systemd-cryptenroll --fido2-device=auto` and `--fido2-with-client-pin=yes` are unchanged. New v261 features tracked in ADR-016 (`ConditionSecurity=measured-os`, `RestrictFileSystems=`, `systemd-tpm2-swtpm.service`) do not affect the disk-unlock path.

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

**Consequence:** Requires systemd >= 257. yubiOS base is now pinned to v261 (ADR-015/ADR-016); Debian Trixie ships systemd 257.x.

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
---

## ADR-014: Rootless Docker (Docker Buildx) over rootless Podman

**Status:** Accepted

**Context:** The build pipeline needs a rootless container build tool. Both Podman and
Docker Buildx can build OCI images without root. The project already depends on Docker Buildx
for Build Policies enforcement (`docker buildx build --policy ... --policy strict=true`)
per the OPA/Rego supply-chain strategy. Carrying two separate container runtimes — Podman
for builds, Docker Buildx for policy enforcement — adds redundant tooling and an extra
surface in the trust chain.

**Decision:** Use rootless Docker Buildx (`docker buildx build`) as the sole container build
runtime. Remove Podman from the build dependency chain.

**Rationale:**
- **One dependency, not two.** Every tool that processes the image before signing is an
  attack surface. Collapsing to a single runtime means a single audit target.
- **Build Policies require Buildx.** OPA/Rego Build Policies (`--policy`) are a
  Docker Buildx / BuildKit feature. Podman's Buildah backend has no equivalent; the
  policy gate would either be skipped or require a second tool. Using Buildx exclusively
  ensures `yubiOS.rego` runs on every `docker buildx build` without exception.
- **Native provenance and SBOM.** Buildx’s `--attest type=provenance,mode=max` and
  `--attest type=sbom` generate SLSA provenance at build time in one flag. Equivalent
  Podman/Buildah paths require separate cosign / syft invocations.
- **Uniform install path.** The runtime command for installing yubiOS to disk
  (`docker run --rm --privileged ... bootc install to-disk /dev/...`) is already
  Docker-CLI. Keeping build and run on the same tool eliminates `podman` as a distinct
  runtime requirement for end users.
- **daemonless trade-off accepted.** Docker requires a daemon (`dockerd`) or
  Docker-in-Docker in CI. The dhi.io CI base image ships Docker; on developer machines
  Docker Desktop or rootless `dockerd` provides the daemon. This overhead is accepted
  in exchange for the unified toolchain above.

**Migration:** Replace all `podman build` invocations with `docker buildx build` and
all `podman run` with `docker run`. The `Containerfile` syntax is identical; no
contents change beyond the build header comment.

**Source:** https://docs.docker.com/build/policies/intro/ (Build Policies, Buildx-only feature)
**Source:** https://docs.docker.com/build/attestations/ (provenance + SBOM attestations)

---

## ADR-015: fedora-bootc:45 as pinned-digest base image

**Status:** Accepted

**Context:** The Containerfile previously used `quay.io/fedora/fedora-bootc:latest` — a
mutable tag that silently pulls different content on each build. This creates two problems:
1. Non-reproducible builds: the base layer changes without any commit-level signal.
2. Policy violation: `yubiOS.rego` already requires `input.image.isCanonical` (digest-pinned
   refs) for all base images. Using `:latest` causes every `docker buildx build --policy`
   invocation to fail its own supply-chain gate.

**Decision:** Pin the base image to:

    FROM quay.io/fedora/fedora-bootc:45@sha256:b7b34d8720b2e0ccaba980fd92347e7820051496ca0e639704172c6f3fb8877d

**Rationale:**
- **Reproducibility.** A SHA256 digest is content-addressed and immutable; the same
  digest produces identical bits on every build, everywhere, forever.
- **Self-consistency.** Brings the Containerfile into compliance with `yubiOS.rego`,
  which rejects non-canonical refs. The image now passes its own policy gate.
- **Systemd version guarantee.** Fedora 45 ships systemd ≥ 257, satisfying ADR-008’s
  requirement for `systemd-sbsign` (the UKI signing tool). A mutable `:latest` tag
  could regress this at any point.
- **fedora-bootc is the right base.** Unlike `quay.io/fedora/fedora`, `fedora-bootc`
  is purpose-built for bootc deployments: /usr-merged, composefs pre-configured,
  systemd-boot-ready, correct /etc layout for hermetic first-boot via systemd-repart,
  no legacy sysvinit, no dnf or package-manager cruft in the deployed image.
- **Source:** https://quay.io/repository/fedora/fedora-bootc
- **Source:** https://github.com/containers/bootc (fedora-bootc upstream)

**Digest update policy:**
- Digest MUST be updated via tooling (Renovate, Dependabot, or `bootc-base-imagectl`)
  when a new Fedora 45 point release is published. Manual bumps are acceptable but
  must include a commit message that states the new digest and the Fedora 45.x version.
- Before bumping: verify the new digest still ships systemd ≥ 257 and pam-u2f ≥ 1.3.1.
- Never revert to a mutable tag (`:latest`, `:45`) without a digest suffix.
- When Fedora 46 is released and stable, open a separate ADR amendment to bump the major version.

**Trade-off:** Digest pinning means security patches in the base image require an
explicit digest bump (a commit). This is intentional — every base change is auditable,
and automated tooling handles the operational overhead.

---

## ADR-016: systemd v261 adoption and yubiOS impact

**Status:** Accepted

**Context:** systemd v261 shipped June 19–21, 2026. Several features directly affect
yubiOS architecture: a new software TPM service (bcvk CI), a new security condition
for measured-boot units, a new filesystem restriction primitive, a new native OS
installer, and live-update/kexec state handover.

**Decision:** Track and adopt the following v261 features for yubiOS. Each item below
is either an immediate action or a tracked future item.

---

### v261 Feature 1: `systemd-tpm2-swtpm.service` — software TPM for VMs

**What it is:** A new service that starts IBM’s `swtpm` (software TPM 2.0 emulator)
and exposes it to the system. Enables TPM2-based measured-boot features on VMs and
hardware lacking a physical TPM chip.

**yubiOS action (CI):**
- Enable `systemd-tpm2-swtpm.service` in bcvk ephemeral VMs to exercise the TPM2 code
  paths in systemd (PCR measurements, LUKS PCR binding) during CI without physical hardware.
- yubiOS itself still uses YubiKey FIDO2 for secrets (ADR-003 unchanged) — swtpm is
  for test coverage only, not the production trust anchor.
- Add `swtpm` package to bcvk test image; configure `ci/vm-swtpm.conf` drop-in.

**Implementation note (2026-06-26, bcvk #3):** bcvk uses *DirectBoot* (extracts kernel+initrd from the UKI, bypassing `systemd-stub` and the ESP), so `systemd-tpm2-swtpm.service` cannot bring up `/dev/tpm0` inside the guest. The shipped route is a **host-side QEMU vTPM emulator device** instead: `swtpm` runs on the host and is attached via `-tpmdev emulator` + arch-aware `-device tpm-tis`/`tpm-crb`, exposed through `bcvk ephemeral run --swtpm`; the guest kernel's `tpm_tis`/`tpm_crb` driver then creates `/dev/tpm0` automatically (no in-guest service). Lands on bcvk branch `feat/swtpm-ci` (referenced directly, never merged).

**Source:** https://github.com/systemd/systemd/releases/tag/v261

---

### v261 Feature 2: `ConditionSecurity=measured-os`

**What it is:** A new unit condition that is true only when the running OS has full
measured-boot semantics — i.e., every component from firmware to userspace is
cryptographically measured and the system passes attestation checks.

**yubiOS action (high value):**
- Add `ConditionSecurity=measured-os` to the `yubiOS-enroll.service` unit and any
  security-critical service that should refuse to run on a system whose trust chain
  is incomplete (e.g., SecureBoot disabled, initrd unsigned).
- This closes a gap where the enrollment wizard could fire on a non-measured boot
  and silently enroll a YubiKey into an untrustworthy chain.
- Implementation: add to `usr/lib/systemd/system/yubiOS-enroll.service`

```ini
[Unit]
ConditionSecurity=measured-os
```

**Source:** https://github.com/systemd/systemd/releases/tag/v261

---

### v261 Feature 3: `RestrictFileSystems=` (BPF LSM)

**What it is:** A new `systemd.exec(5)` sandboxing directive that uses BPF LSM to
restrict which filesystems a service may access by type. Complements existing
`ProtectSystem=`, `PrivateDevices=`, and `RestrictNamespaces=`.

**yubiOS action:**
- Evaluate adding `RestrictFileSystems=` to the enrollment scripts and
  YubiKey auth services to limit filesystem surface. Candidate:
  `RestrictFileSystems=tmpfs proc sysfs devtmpfs`
- Requires systemd >= 261 and a kernel with BPF LSM enabled (`CONFIG_BPF_LSM=y`).
  Verify this is set in the fedora-bootc:45 kernel config before deploying.
- Add to next `systemd-hardening` skill audit cycle.

**Source:** https://github.com/systemd/systemd/releases/tag/v261

---

### v261 Feature 4: `systemd-sysinstall` — native text-based OS installer

**What it is:** A new native installer that orchestrates `systemd-repart`,
`bootctl`, and `systemd-creds` via Varlink. Replaces distribution-specific
installation scripts with a standardized, composable installation path.

**yubiOS context (ADR-012 alignment):**
- ADR-012 uses `systemd-repart` for first-boot partitioning (no traditional installer).
  `systemd-sysinstall` is upstream’s answer to the same problem, and confirms that
  design choice.
- yubiOS does NOT need to adopt `systemd-sysinstall` directly — the first-boot
  systemd-repart path is already in place and is simpler for the single-image model.
- Track for future use: `systemd-sysinstall` may become the right path for
  multi-boot installs or guided first-boot UX beyond what `yubiOS-enroll` provides.

---

### v261 Feature 5: Live Update / Kexec Handover (LUO/KHO)

**What it is:** PID1 supports Linux’s Live Update Orchestration (LUO) and Kexec
Handover (KHO). The system can carry FD store state, service state, and credentials
across a `kexec` reboot — enabling kernel updates with near-zero downtime.

**yubiOS context (ADR-013 alignment):**
- yubiOS uses A/B partition updates via `systemd-sysupdate` + Boot Assessment (ADR-013).
  LUO/KHO is a complementary path for latency-sensitive environments where even a
  short reboot is unacceptable.
- For the current yubiOS use case (desktop/laptop), the A/B reboot model is correct.
  Kexec handover is worth tracking for server/appliance deployments.
- `FileDescriptorStorePreserve=yes` — new unit option — can preserve open FIDO2
  credential handles across kexec if implemented. Track but do not act yet.

---

**Minimum systemd version for v261 features:**

| Feature | Min version |
|---|---|
| `systemd-tpm2-swtpm.service` | 261 |
| `ConditionSecurity=measured-os` | 261 |
| `RestrictFileSystems=` | 261 |
| `systemd-sysinstall` | 261 |
| `FileDescriptorStorePreserve=yes` | 261 |

Fedora 45 ships systemd 261 (confirmed via `rpm -q systemd` in fedora-bootc:45 after June 2026
point release). The pinned digest in ADR-015 predates v261; bump to a post-June-19 Fedora 45
digest to get these features in the base image.

**Immediate action:** Bump `fedora-bootc:45` digest to a post-June-19 point release and
verify `systemd --version` returns 261. Then add `ConditionSecurity=measured-os` to
`yubiOS-enroll.service` (highest-value, lowest-risk change).

**Source:** https://github.com/systemd/systemd/releases/tag/v261

---

## ADR-017: ARM64 Multi-Architecture Profile

**Date:** 2026-06-24  
**Status:** Accepted  
**Context:** yubiOS is designed around FIDO2 hardware trust, immutable /usr, and UKI-based boot — none of which are x86-64-specific. ARM64/aarch64 is the dominant architecture in embedded, server, and mobile-adjacent hardware, and is a natural second target.

**Decision:** Ship yubiOS as a multi-arch project: x86-64 as the primary, supported production platform; arm64/aarch64 as a secondary, in-development platform. The trust chain (YubiKey FIDO2, systemd-sbsign PIV, UKI + dm-verity) is architecturally identical on both platforms.

**Build changes:**
- docker buildx build --platform linux/amd64,linux/arm64 via QEMU emulation on amd64 runners (docker/setup-qemu-action in CI).
- The fedora-bootc:45 base image is multi-arch. The existing Containerfile requires no platform-specific changes beyond the --platform flag.
- bcvk native-to-disk works on ARM64 target hardware without modification (Rust cross-compilation via --target aarch64-unknown-linux-gnu).

**ARM64-specific mitigations (see MITIGATE.md for full analysis):**

| Attack | ARM64 mitigation |
|---|---|
| CNTVOFF_EL2 virtual timer offset | Kernel arch_timer erratum workarounds applied at boot. UKI/PCR trust chain unchanged. |
| ARM CoreSight debug/trace exfiltration | Kernel lockdown (SecureBoot active) disables CoreSight trace interfaces via CONFIG_LOCK_DOWN_KERNEL_FORCE_CONFIDENTIALITY. |
| qcom,dload Qualcomm firmware sideload | dm-verity blocks library substitution regardless of sideload path. Preferred hardware: non-Qualcomm ARM64 (Ampere, RPi 5, ARM Juno). |

**Preferred ARM64 hardware targets (for qcom,dload attack surface — ADR-017 scope):**
- Raspberry Pi 5 (BCM2712, no Qualcomm sideload) — **Path B only for yubiOS-owned RoT** (VideoCore VII firmware runs before ARM cores; Broadcom key permanently in chain; see ADR-019)
- **RK3588** (Rockchip — no vendor key in chain, FIREWALL_DDR hardware TrustZone isolation; **primary Path A target**; boards: Orange Pi 5, Rock 5B, NanoPC-T6)
- **RK3399** (Rockchip — same TF-A/OP-TEE lineage, blobless DDR init, dry-run testable; **Path A stepping stone**; boards: RockPro64, Pinebook Pro)
- Ampere Altra / AmpereOne (server, documented fuse provisioning)

**Consequences:**
- CI must add docker/setup-qemu-action for cross-platform builds.
- ARM64 hardware testing is separate from x86-64 VM CI (bcvk native-to-disk to physical ARM64 hardware).
- MITIGATE.md updated: CNTVOFF_EL2, CoreSight, and qcom,dload entries revised from "N/A (x86-64 only)" to active mitigations.
- ARCHITECTURE.md and README.md updated to document the multi-arch profile.

**Source:** ADR-008 (systemd-sbsign is PIV-based, not arch-specific), ADR-014 (Docker Buildx multi-platform), ADR-015 (fedora-bootc:45 is multi-arch), [MITIGATE.md](MITIGATE.md)

---

## ADR-018: yubiOS-Owned ARM64 Secure-World Stack (TF-A + OP-TEE + fTPM)

**Date:** 2026-06-24  
**Status:** Proposed — post-launch (see [FUTURE.md](FUTURE.md))  
**Context:** On most ARM64 hardware there is no discrete TPM and no firmware TPM we control — the SoC vendor owns the secure world (their TF-A, their TrustZone payload, their boot ROM key, their fTPM if any). Measured boot still needs a TPM-shaped thing to hold PCRs and seal secrets. Inheriting the vendor's secure world reintroduces exactly the OEM/vendor supply-chain trust anchor yubiOS exists to remove (see [MITIGATE.md](MITIGATE.md)).

**Decision:** Post-launch, build the whole ARM64 secure-world stack ourselves: **ARM Trusted Firmware (TF-A)** as our EL3 monitor and Trusted Board Boot chain; **OP-TEE** as BL32, our secure-world OS; the **Microsoft `ms-tpm-20-ref` fTPM** run as an OP-TEE Trusted Application so the PCRs and sealing root are ours; **U-Boot** as BL33. Pin `OP-TEE/optee_ftpm` + `microsoft/ms-tpm-20-ref@98b60a44aba79b15fcce1c0d1e46cf5918400f6a`; fTPM TA UUID `bc50d971-d4c9-42c4-82cb-343fb7f37896`; build as an Early TA (`CFG_EARLY_TA=y`) with NV in RPMB (`CFG_RPMB_FS=y`).

**fTPM vs YubiKey — complementary, not redundant:** the fTPM is the *platform-integrity* root (PCR measurement, attestation, optional seal); the YubiKey stays the *user-identity* root and the primary disk-unlock path (FIDO2 hmac-secret, ADR-003). The fTPM must never become the sole disk-unlock gate — doing so would re-create an on-device, vendor-shaped trust anchor. It is where `ConditionSecurity=measured-os` (ADR-016) binds on hardware with no real TPM.

**Alternatives considered:**
- *Vendor fTPM / TrustZone as-is* — rejected: trust anchor we did not choose; defeats the thesis.
- *No TPM on ARM64, YubiKey only* — rejected: leaves no PCR set or local attestation root for measured boot.
- *Discrete TPM chip* — rejected: most target ARM64 boards have no TPM header; adds a part we don't control.

**Consequences:** Per-SoC TF-A bring-up is significant; pick one board and go deep first. The fTPM is software (an `ms-tpm-20-ref`/OP-TEE bug is a TPM bug) — track CVEs, pin commits, fold into Renovate (ADR-015). Highest risk: the Early-TA RPMB bootstrap before `tee-supplicant` (OP-TEE issue #5766) — prove on QEMU `virt` first.

**Source:** [FUTURE.md](FUTURE.md), `knowledge/arm64-ftpm-stack.md`, skills `arm-trusted-firmware-optee` + `ftpm-optee-tpm`, ADR-016 (measured-os), ADR-017 (ARM64).

---

## ADR-019: Dual Root-of-Trust Provisioning Paths (Fuse-Enforcing vs Measured/Attested)

**Date:** 2026-06-24  
**Status:** Proposed — post-launch (see [FUTURE.md](FUTURE.md))  
**Context:** TF-A Trusted Board Boot anchors the chain in a ROTPK hash burned into SoC OTP/eFuse. Burning fuses is irreversible and can brick boards; some SoCs lock or hide the fuses; dev boards often can't or shouldn't be burned. We need a coherent stance for boards where we cannot (or choose not to) anchor a hardware root of trust.

**Decision:** Support two provisioning paths. The five TF-A stages are identical on both; only the *root* differs.
- **Path A — fuses burnable (enforcing):** ROTPK hash in OTP/eFuse, full TBB, BL1 rejects any image that doesn't chain to it. Bad code never executes. The production path. Targets: **RK3588** (primary — no vendor key in chain, FIREWALL_DDR hardware TrustZone isolation, RSA/ECDSA OTP, SRK revocation table, dry-run testable; boards: Orange Pi 5, Rock 5B, NanoPC-T6), **RK3399** (stepping stone — same TF-A/OP-TEE lineage, blobless DDR init, dry-run via `rkdeveloptool db`; boards: RockPro64, Pinebook Pro), Ampere with documented fuse provisioning. **RPi 5 is Path B only** — see note below.
- **Path B — no/locked/unburned fuses (measured + attested):** no hardware-enforced rejection. Software root of trust via U-Boot FIT verified boot (public key in the U-Boot control DTB) plus measured boot into the fTPM; trust is decided *after* boot by local/remote attestation and fTPM/YubiKey secret release. For dev boards and early bring-up.

> **RPi 5 (BCM2712) Path B classification:** The Broadcom VideoCore VII closed-source firmware executes before the ARM cores start and holds a Broadcom key permanently in the boot chain. Counter-signing the EEPROM with a customer key adds an OTP-burned layer, but cannot remove the Broadcom key or replace the closed VideoCore stage. This violates the yubiOS requirement that every trust anchor be owner-controlled and auditable. RPi 5 is valuable for toolchain validation (Pi 4 dry-run; Pi 5 requires OTP burn first), Qualcomm-attack-surface analysis (no qcom,dload), and measured/attested deployments (Path B), but cannot serve as a production Path A target for a yubiOS-owned root of trust.

**Honest framing:** Path B records what ran and can withhold secrets when measurements are wrong, but a compromised stage still executes long enough to measure itself. It is evidence-and-sealing, not boot-time rejection, and its anchor lives in writable firmware (only as strong as the storage holding U-Boot and its key). Path A is strictly stronger; Path B is a deliberate, documented fallback, not a substitute.

**Consequences:** Each supported board is tagged Path A or Path B and documented. Path A provisioning (ROTPK burn) is treated like a production-secret operation, rehearsed on a sacrificial board. The RPMB key write (`CFG_RPMB_WRITE_KEY=y`) for the variable store / fTPM NV is another effectively-irreversible per-device step folded into provisioning.

**Source:** [FUTURE.md](FUTURE.md) (two-path trust chain), `knowledge/rockchip-otp-secure-boot.md`, `knowledge/rpi5-otp-secure-boot.md`, TF-A TBB docs, U-Boot `FIT_SIGNATURE` verified boot.

---

## ADR-020: U-Boot as the ARM64 UEFI Firmware + Authenticated Variable Store (OP-TEE StandaloneMM)

**Date:** 2026-06-24  
**Status:** Proposed — post-launch (see [FUTURE.md](FUTURE.md))  
**Context:** yubiOS's x86-64 boot chain is systemd-boot + UKI + UEFI Secure Boot. We do not want a divergent, bespoke ARM64 boot path. U-Boot's `EFI_LOADER` subsystem is a real UEFI environment (boot + runtime services, system table, `Boot####`/`BootOrder`, PE/COFF loading), so the same signed artifacts can run on ARM64 with U-Boot speaking UEFI in place of vendor EDK2.

**Decision:** On ARM64, U-Boot (BL33) provides the UEFI environment and chainloads the **same systemd-boot + UKI** that x86-64 uses, unmodified. Enable `CONFIG_EFI_LOADER`, `CONFIG_EFI_SECURE_BOOT` (PK/KEK/db/dbx authentication of PE/COFF binaries, incl. UKIs), and `CONFIG_EFI_TCG2_PROTOCOL` (UKI-stage measurement into the fTPM, per ADR-018). Store the Secure Boot variables (PK/KEK/db/dbx) in **EDK2 StandaloneMM** run as an **OP-TEE** module, backed by **RPMB** (`CFG_STMM_PATH=`, `CONFIG_EFI_MM_COMM_TEE=y`, `CONFIG_CMD_OPTEE_RPMB=y`), so they are tamper-resistant rather than living in writable normal-world flash. Use `CONFIG_EFI_CAPSULE_*` (capsule-on-disk, FMP) for U-Boot/FIP/OP-TEE firmware updates.

**Consequences:** ARM64 stops being a special boot path — one UKI signing flow, one set of Secure Boot keys, one systemd-boot, across both architectures. The variable store shares the same RPMB that backs the fTPM. Capsule-on-disk folds firmware updates into the A/B + Renovate story (ADR-013/015). U-Boot's UEFI is a subset of the spec; verify each needed protocol on the target board during bring-up.

**Alternatives considered:**
- *Vendor EDK2 / TianoCore firmware* — rejected: vendor-owned trust anchor; same objection as ADR-018.
- *Boot the kernel directly from U-Boot (no UEFI)* — rejected: diverges from the x86-64 UKI/systemd-boot chain and loses UEFI Secure Boot semantics.
- *Variables in normal-world flash* — rejected: writable by a compromised normal world; defeats Secure Boot.

**Source:** [FUTURE.md](FUTURE.md) (components 4–5), U-Boot UEFI + measured-boot docs (v2026.01), EDK2 StandaloneMM on OP-TEE, ADR-018, ADR-002 (UKI/SecureBoot lineage).

---

## ADR-021: U-Boot as the Sole ARM64 Bootloader and UEFI Firmware Provider

**Date:** 2026-06-24  
**Status:** Accepted — post-launch (see [FUTURE.md](FUTURE.md))  
**Supersedes:** The alternative-UEFI option mentioned in ADR-020 (edk2-rk3588 as a parallel UEFI path is rejected here).

**Context:** The ARM64 secure-world stack (ADR-018/019/020) needs a BL33 stage that both completes the TF-A boot chain and provides the UEFI environment yubiOS's existing systemd-boot + UKI toolchain requires. Two candidates exist:

- **U-Boot** (`yubi-OS/u-boot` fork of `u-boot/u-boot`): the non-secure BL33 bootloader. Provides a real UEFI environment via its `EFI_LOADER` subsystem. Mainline defconfigs exist for all three primary target boards.
- **edk2-rk3588** (`edk2-porting/edk2-rk3588`): a community EDK2 port for RK3588 that replaces U-Boot as BL33 with a full TianoCore firmware stack. Designed primarily for running Windows and standard ACPI-first OSes.

**Decision:** U-Boot is the sole UEFI firmware provider on ARM64. edk2-rk3588 as a BL33 replacement is rejected.

**Why U-Boot wins:**

1. **All three target boards have mainline U-Boot defconfigs** (confirmed in `yubi-OS/u-boot` fork):
   - Orange Pi 5 (RK3588S): `orangepi-5-rk3588s_defconfig`
   - Rock 5B (RK3588): `rock5b-rk3588_defconfig`
   - NanoPC-T6 (RK3588): `nanopc-t6-rk3588_defconfig`

2. **U-Boot EFI_LOADER is a real UEFI environment.** Boot services, runtime services, the UEFI system table, `Boot####`/`BootOrder` variables, and PE/COFF loading (`CONFIG_EFI_LOADER=y`). systemd-boot + UKI + UEFI Secure Boot run unmodified, identical to x86-64 (ADR-020).

3. **Direct integration with TF-A + OP-TEE.** U-Boot slots cleanly into the TF-A BL33 position. edk2-rk3588 bundles its own TF-A integration, which we cannot audit or override without forking the entire firmware stack.

4. **Full fTPM integration.** U-Boot has first-class `CONFIG_TPM2_FTPM_TEE=y` (talking to the ms-tpm-20-ref fTPM via the OP-TEE TEE driver), `CONFIG_MEASURED_BOOT=y`, and `CONFIG_EFI_TCG2_PROTOCOL=y` in the same binary. edk2-rk3588 would require separate TPM integration work.

5. **StandaloneMM is independent.** The EDK2 StandaloneMM UEFI variable service (needed for tamper-resistant PK/KEK/db/dbx storage on RPMB, per ADR-020) is built from upstream `tianocore/edk2` as a standalone OP-TEE module (`BL32_AP_MM.fd`, `CFG_STMM_PATH=`). It does not require edk2-rk3588 and works identically with U-Boot as the UEFI consumer.

6. **Scope alignment.** edk2-rk3588 targets Windows 11 / ACPI-first workflows on RK3588. yubiOS is a security-hardened Linux OS. Device Tree mode (Linux-first) is fully supported by U-Boot EFI_LOADER and is the correct boot path for our stack.

**Disposition of `yubi-OS/edk2-rk3588` fork:**  
Retained in the org for reference (community UEFI firmware art for RK3588 boards) but **not an active build dependency**. The StandaloneMM variable service is sourced from `tianocore/edk2` directly, not from this fork. If StandaloneMM build tooling needs an EDK2 fork in the future, fork `tianocore/edk2` at that point.

**U-Boot kconfig for ARM64 (target config per board + yubiOS overlays):**
```
CONFIG_TEE=y
CONFIG_OPTEE=y
CONFIG_TPM=y
CONFIG_TPM_V2=y
CONFIG_TPM2_FTPM_TEE=y        # fTPM via OP-TEE TEE driver (ADR-018)
CONFIG_MEASURED_BOOT=y
CONFIG_TPM2_EVENT_LOG_SIZE=0x10000
CONFIG_EFI_LOADER=y
CONFIG_EFI_SECURE_BOOT=y       # PK/KEK/db/dbx PE/COFF authentication (ADR-020)
CONFIG_EFI_TCG2_PROTOCOL=y     # TCG2 measured boot to fTPM
CONFIG_EFI_MM_COMM_TEE=y       # StandaloneMM variable service via OP-TEE (ADR-020)
CONFIG_CMD_OPTEE_RPMB=y
CONFIG_EFI_CAPSULE_AUTHENTICATE=y  # Firmware update authentication
```

**Alternatives considered:**
- *edk2-rk3588 as BL33 UEFI firmware* — rejected: bundled TF-A integration bypasses our chain; ACPI-first design diverges from yubiOS Linux/Device-Tree stack; no first-class fTPM/OP-TEE integration; adds a separate, opaque build dependency for a capability U-Boot already provides.
- *Direct kernel boot from U-Boot (no UEFI)* — rejected (same as ADR-020): loses UEFI Secure Boot semantics and diverges from the x86-64 UKI/systemd-boot chain.

**Source:** `yubi-OS/u-boot` defconfig inventory (2026-06-24), U-Boot EFI docs (v2026.01), ADR-018 (secure-world stack), ADR-019 (RK3588 as primary Path A target), ADR-020 (UEFI + StandaloneMM), [FUTURE.md](FUTURE.md).
