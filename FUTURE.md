# FUTURE.md — Post-Launch: A yubiOS-Owned Root of Trust on ARM64 (Primary Platform)

> *No TPM. No OEM. No trust anchors you don't control.*
>
> Status: **Planning** — post-launch (after Phase 0 ships). Nothing here blocks launch.
> Scope: ARM64 only — yubiOS's primary target platform (ADR-017, ADR-023). x86-64 remains a
> fully supported secondary platform and keeps its existing UKI + SecureBoot + dm-verity chain.

---

## Why this exists

yubiOS replaces the TPM with a YubiKey for **secrets and signing**. But measured boot still needs
a TPM-shaped thing to hold PCRs and an event log. On x86-64 that is the platform TPM (or, in our
design, the YubiKey for unlock plus firmware PCRs for attestation). On most ARM64 hardware there is
**no discrete TPM and no firmware TPM we control** — the SoC vendor owns the secure world.

That is the exact dependency yubiOS exists to kill. The OEM/vendor supply chain is the root of the
Faux Phy attack chain (see [MITIGATE.md](MITIGATE.md)). On ARM64 the vendor's TrustZone payload,
their TF-A, their boot ROM key, and their fTPM (if any) are all trust anchors we did not choose.

This project builds the whole ARM64 secure-world stack ourselves:

- **ARM Trusted Firmware (TF-A)** — our EL3 monitor and Trusted Board Boot chain, our ROTPK.
- **OP-TEE** — our secure-world OS as BL32, replacing the vendor TEE.
- **Microsoft `ms-tpm-20-ref` fTPM** — a TPM 2.0 we run as an OP-TEE Trusted Application, so the
  PCRs and the sealing root are ours, not a vendor's.
- **U-Boot** — our BL33 bootloader, which also *provides the UEFI environment* so the same
  systemd-boot + UKI chain runs on ARM64, measures the OS, and talks to our fTPM.

End state: an ARM64 board where every layer from the boot ROM key onward is signed by keys we hold,
the TPM is software we audit, and the YubiKey stays the user-facing root of trust. The fTPM guards
the *device fabric*; the YubiKey guards the *user identity*. They are complementary, not redundant.

---

## The trust chain — two provisioning paths

The chain is the same five TF-A stages on both paths. What differs is the **root**: whether we can
burn our ROTPK hash into the SoC's one-time-programmable fuses. That single fact decides whether the
chain *enforces* (refuses bad code before it runs) or only *measures* (records it for attestation).

### Path A — fuses available and burnable (enforcing)

Full hardware-anchored Trusted Board Boot. Our ROTPK hash is burned into SoC OTP/eFuse; BL1 refuses
any image that doesn't chain to it. This is the strong path: bad code never executes.

```
ROTPK hash  ──burned──►  SoC OTP / eFuse   (immutable, one-time)
   │
  BL1  verifies BL2 vs ROTPK ......................... reject on mismatch
  BL2  verifies BL31/BL32/BL33 vs FIP certs (TBB) .... reject on mismatch
   ├─► BL31  EL3 Secure Monitor (PSCI, SMC routing)
   ├─► BL32  OP-TEE OS ──► fTPM TA (ms-tpm-20-ref)
   └─► BL33  U-Boot  ── provides UEFI (see below) ──► systemd-boot → UKI
        every stage measured into PCRs (enforced AND attested)
```

Targets: **RK3588** (primary Path A — no vendor key in chain, FIREWALL_DDR hardware TrustZone isolation, RSA/ECDSA OTP, SRK revocation; boards: Orange Pi 5, Rock 5B, NanoPC-T6), **RK3399** (stepping stone — same TF-A/OP-TEE lineage, blobless DDR init, dry-run testable; boards: RockPro64, Pinebook Pro),
Ampere with documented fuse provisioning. **RPi 5 is Path B only** (see below).

### Path B — no fuses, vendor-locked, deliberately not burned, or closed-source vendor stage (measured + attested)

When OTP is unavailable, vendor-locked, or we choose not to take the irreversible/bricking risk
(dev boards, early bring-up), there is **no hardware-enforced rejection**. We layer two softer
anchors instead:

Note: **RPi 5 (BCM2712) is Path B**, not Path A. The Broadcom VideoCore VII firmware
runs before ARM cores execute, holds a Broadcom key permanently in the chain, and is
closed-source. Customer OTP adds a second signature layer but cannot remove the Broadcom
key. RPi 5 is excellent for toolchain validation and Qualcomm-attack-surface testing, but
the yubiOS requirement that every trust anchor be owner-controlled rules it out for Path A.
Use Pi 4 (dry-run before OTP burn) to validate the signing toolchain, then move to RK3588.

```
(no immutable hardware key)
   │
  Vendor/board firmware loads our U-Boot   (trust starts in writable firmware)
   │
  U-Boot FIT verified boot ── public key in U-Boot control DTB ──► verify next images
   │   (software RoT: only as trustworthy as the firmware holding the key)
   └─► BL33 U-Boot ── UEFI ──► systemd-boot → UKI
        every stage MEASURED into fTPM PCRs + TCG2 event log
        ▼
   Local/remote ATTESTATION decides trust AFTER boot:
   fTPM unseals secrets / YubiKey gates access only if PCRs match a golden value
```

The honest framing: Path B records what ran and lets the fTPM + YubiKey withhold secrets when the
measurements are wrong, but a compromised stage still *executes* long enough to measure itself. It
is evidence-and-sealing, not boot-time rejection. Good for attestation, fleet identity, and
key-sealing; not a substitute for Path A's enforcement.

**At BL33, U-Boot provides the UEFI environment** (its `EFI_LOADER` subsystem): boot + runtime
services, the UEFI system table, `Boot####`/`BootOrder` variables, and PE/COFF loading. So
**yubiOS's existing x86-64 boot chain — systemd-boot + UKI + UEFI Secure Boot — runs unmodified on
ARM64**, with U-Boot speaking UEFI in place of vendor EDK2. Detail in component 4.

### Two roots of trust, two jobs (both paths)

| | fTPM (in OP-TEE) | YubiKey 5 |
|---|---|---|
| **Role** | Platform integrity, PCR measurement, attestation, optional seal | User identity, secret unlock, signing |
| **Lives in** | Secure world (Secure-EL1/EL0), on-device | External hardware, off-device |
| **Answers** | "Is this exact firmware + OS stack what we signed?" | "Is the authorized human present?" |
| **Survives OS reinstall** | NV state in RPMB (device-bound) | Yes — token is independent of the machine |
| **yubiOS stance** | We **own** it (our OP-TEE build, our keys) | Primary RoT, unchanged from x86-64 design |

The YubiKey still unlocks the disk (FIDO2 hmac-secret, ADR-003). The fTPM does **not** replace that.
On Path A it gives enforced measured-boot PCRs; on Path B those same PCRs are the attestation anchor.
Either way it is where `ConditionSecurity=measured-os` (ADR-016) binds on hardware with no real TPM.

---

## Component breakdown

### 1. ARM Trusted Firmware (TF-A)

- Stages: **BL1** (boot ROM), **BL2** (Trusted Boot, loads + authenticates everything else),
  **BL31** (EL3 runtime / Secure Monitor — PSCI, SMC routing between worlds),
  **BL32** (= OP-TEE), **BL33** (= U-Boot).
- **Trusted Board Boot (TBB):** X.509 cert chain rooted in the **ROTPK**, whose SHA-256 hash is
  burned into SoC OTP/fuses. BL2 verifies each image hash against signed content certs before exec.
- **FIP** (Firmware Image Package) bundles BL31/BL32/BL33 + certs; built with `fiptool`.
- **Measured boot:** BL1/BL2 measure each stage into a TCG2 event log carried in memory. Modern
  TF-A/OP-TEE/U-Boot pass it via the **Firmware Handoff** spec (Transfer Lists, `BLOBLISTT_TPM_EVLOG`).
- yubiOS owns the ROTPK. This is the ARM64 analogue of `bootctl enroll-keys` on x86-64.

### 2. OP-TEE (BL32, secure-world OS)

- Secure-EL1 kernel + Secure-EL0 Trusted Apps. Normal world (U-Boot, Linux) calls in via **SMC**,
  trapped to EL3 (BL31) and routed to OP-TEE.
- Linux side: `optee.ko` exposes `/dev/tee0` + `/dev/teepriv0`; **`tee-supplicant`** services RPC
  for storage (OP-TEE has no block driver of its own).
- **RPMB** (Replay Protected Memory Block on eMMC/UFS) is the rollback-proof NV store. Build with
  `CFG_RPMB_FS=y`. This is where the fTPM's seeds, counters, and NV indices live.

### 3. fTPM Trusted Application (`ms-tpm-20-ref` via `OP-TEE/optee_ftpm`)

- Canonical repo: **`github.com/OP-TEE/optee_ftpm`** (split out of ms-tpm-20-ref's
  `Historical_Samples/Samples/ARM32-FirmwareTPM` in Oct 2024; the active integration home).
- Pins **`microsoft/ms-tpm-20-ref` commit `98b60a44aba79b15fcce1c0d1e46cf5918400f6a`**.
- **UUID:** `bc50d971-d4c9-42c4-82cb-343fb7f37896`.
- Build flags: `CFG_MS_TPM_20_REF=<path>`, `CFG_TA_MEASURED_BOOT=y`, `CFG_TA_EVENT_LOG_SIZE=<bytes>`;
  requires OP-TEE PTA `PTA_SYSTEM_GET_TPM_EVENT_LOG`.
- **Build as an Early TA** (`CFG_EARLY_TA=y`, `EARLY_TA_PATHS=.../bc50d971-...stripped.elf`) so it is
  compiled into the OP-TEE binary (`.rodata.early_ta`) and is alive before any rootfs or
  `tee-supplicant`. U-Boot and Linux IMA both need the TPM before userspace exists.
- **Known bootstrap hazard:** an Early TA that must write NV before `tee-supplicant` is up will panic
  on RPMB access (OP-TEE issue #5766). Mitigation: run `tee-supplicant` from initramfs and/or defer
  persistent writes. This is the single biggest integration risk; prototype it first.

### 4. U-Boot (BL33) — bootloader AND UEFI firmware

Two roles. **As the fTPM client:**
- Kconfig: `CONFIG_TEE=y`, `CONFIG_OPTEE=y`, `CONFIG_TPM=y`, `CONFIG_TPM_V2=y`,
  `CONFIG_TPM2_FTPM_TEE=y` (driver `tpm2_ftpm_tee.c`), `CONFIG_MEASURED_BOOT=y`,
  `CONFIG_TPM2_EVENT_LOG_SIZE=0x10000`.
- Device tree node: `tpm { compatible = "microsoft,ftpm"; };`
- `tpm2` command suite drives the fTPM; U-Boot replays the firmware event log into PCRs, measures
  kernel/DTB/initramfs, then hands the log to Linux via `linux,sml-base` / `linux,sml-size` in the
  kernel `/chosen` DTB node.

**As the UEFI firmware (`EFI_LOADER`) — the architectural unlock:**
- `CONFIG_EFI_LOADER=y` + `CONFIG_CMD_BOOTEFI=y` give a real UEFI environment: boot services,
  runtime services, the UEFI system table, `Boot####`/`BootOrder`, and PE/COFF EFI binary loading.
  **systemd-boot, a UKI, shim, or GRUB load unmodified** — the same artifacts yubiOS already signs
  for x86-64 UEFI Secure Boot. ARM64 stops being a special boot path.
- `CONFIG_EFI_TCG2_PROTOCOL=y` (with `TPM_V2`) exposes the TCG2 protocol, so the UEFI/UKI stage
  measures into the fTPM exactly as it would on a physical-TPM box; the OS verifies PCRs against the
  final event log.
- `CONFIG_EFI_CAPSULE_*` — capsule-on-disk firmware updates (Firmware Management Protocol) for
  U-Boot, FIP, and OP-TEE images. Fold into the A/B + Renovate update story (ADR-013/015) post-bring-up.

### 5. UEFI Secure Boot + protected variable store (OP-TEE StandaloneMM)

Real UEFI Secure Boot needs PK/KEK/db/dbx to be persistent **and** protected from the normal world.
The upstream pattern: run EDK2's **StandaloneMM** variable service as an **OP-TEE** module, backing
the variables in **RPMB**.

- U-Boot: `CONFIG_EFI_SECURE_BOOT=y` (needs `EFI_LOADER` + `FIT_SIGNATURE`),
  `CONFIG_EFI_MM_COMM_TEE=y`, `CONFIG_OPTEE=y`, `CONFIG_CMD_OPTEE_RPMB=y`. U-Boot authenticates
  PE/COFF EFI binaries (UKIs included) against db/dbx and talks to the secure-world variable service
  over the MM communication protocol.
- OP-TEE: build EDK2 `StandAloneMM` (`BL32_AP_MM.fd`) and point OP-TEE at it with `CFG_STMM_PATH=`,
  plus `CFG_RPMB_FS=y`, `CFG_RPMB_WRITE_KEY=y`, `CFG_CORE_DYN_SHM=y`.
- Result: tamper-resistant PK/KEK/db/dbx on RPMB instead of writable normal-world flash — the ARM64
  equivalent of Secure Boot variables in protected NVRAM, sharing the same RPMB that backs the fTPM.

### 6. Linux (normal-world consumer)

- Kconfig: `CONFIG_TCG_TPM=y`, `CONFIG_TCG_FTPM_TEE=m`, `CONFIG_TEE=y`, `CONFIG_OPTEE=y`.
- `tpm_ftpm_tee.ko` reads `linux,sml-base`/`-size`, exposes `/dev/tpm0` + `/dev/tpmrm0`.
- IMA consumes the fTPM for runtime measurement. Probe-ordering matters: the fTPM must be ready
  before IMA, so `tee-supplicant` belongs in the initramfs.

---

## Phased roadmap

> Each phase is a gate. Don't start the next until the prior one boots and measures cleanly.

**Phase F0 — Reference bring-up (emulated).**
Build TF-A + OP-TEE + fTPM Early TA + U-Boot + Linux for QEMU `virt` (ARM64). Get `/dev/tpm0` live
with PCRs extending. No yubiOS specifics yet. Proves the toolchain and the Early-TA/RPMB bootstrap.

**Phase F1 — Own the keys.**
Replace all default/test keys: our ROTPK, our FIP signing keys, our OP-TEE TA signing key. Document
the key hierarchy and where each private key lives (offline? PIV slot on a YubiKey?).

**Phase F2 — Real hardware.**
Bring up on a non-Qualcomm ARM64 target (RPi 5, Ampere, or ARM Juno per ADR-017). Provision RPMB,
burn ROTPK to fuses on a sacrificial board first. This is the irreversible step — treat fuse burns
like production secrets.

**Phase F3 — Measured boot end to end.**
Firmware Handoff event log from BL1 → U-Boot → Linux. Verify PCR values are reproducible across
reboots and match a known-good golden value.

**Phase F4 — Bind to yubiOS policy.**
Wire `ConditionSecurity=measured-os` (ADR-016) to the fTPM PCR state. Decide the fTPM-vs-YubiKey
split for LUKS: YubiKey FIDO2 stays the unlock path; fTPM optionally seals a fallback/attestation
secret to PCR 0/1/7. Keep YubiKey as the primary; fTPM seal is additive, never the sole gate.

**Phase F5 — Reproducible + signed builds.**
Fold the secure-world build into the existing Docker Buildx + OPA/Rego pipeline (ADR-014/015).
Pin TF-A, OP-TEE, optee_ftpm, ms-tpm-20-ref commits. Add to Renovate digest tracking.

---

## Open questions / risks

- **Early-TA RPMB bootstrap** (OP-TEE #5766) — highest risk; resolve in F0.
- **Per-SoC TF-A platform ports** — TF-A is platform-specific. Each board is its own BL1/BL2/BL31
  bring-up. RPi 5, Ampere, and Juno are very different efforts. Pick one and go deep first.
- **Fuse burning is irreversible** — ROTPK to OTP locks the board to our keys. Need a documented,
  rehearsed provisioning flow before touching production hardware.
- **fTPM is software** — a bug in `ms-tpm-20-ref` or OP-TEE is a TPM bug. We inherit Microsoft's
  reference code; we must track its CVEs and pinned commit, not fork-and-forget.
- **Does the fTPM weaken the FIDO2-first thesis?** No, if scoped correctly: the fTPM measures and
  attests; the YubiKey still authorizes. The fTPM must never become the sole unlock path, or we have
  reintroduced exactly the on-device, vendor-shaped trust anchor yubiOS set out to remove.
- **Apple Silicon (Asahi)** — interesting but no TF-A/OP-TEE path; out of scope for now.
- **Path A vs Path B is a per-board decision** — enforcement vs attestation depends on the target.
  RPi 5 forces an OTP burn before secure boot works at all; dev boards stay on Path B. Document which
  path each supported board is on.
- **Path B firmware is writable** — U-Boot FIT verified boot is only as trustworthy as the storage
  holding U-Boot and its embedded key. Without an upstream immutable stage, an attacker who can
  rewrite firmware swaps verifier and key together. Path B is attestation, not a hardware RoT.
- **UEFI variable store provisioning** — StandaloneMM + RPMB needs the RPMB key written
  (`CFG_RPMB_WRITE_KEY=y`) once per device; another irreversible-ish step to fold into provisioning.

---

## Repos & references

| Component | Repo / source |
|---|---|
| TF-A | `github.com/ARM-software/arm-trusted-firmware` |
| OP-TEE OS | `github.com/OP-TEE/optee_os` |
| fTPM TA integration | `github.com/OP-TEE/optee_ftpm` |
| MS TPM 2.0 reference | `github.com/microsoft/ms-tpm-20-ref` @ `98b60a44` |
| U-Boot | `source.denx.de/u-boot/u-boot` |
| Linux fTPM driver | `drivers/char/tpm/tpm_ftpm_tee.c` |
| fTPM over OP-TEE (worked example) | NVIDIA BlueField DPU BSP docs |
| U-Boot SPL measured boot | Raymond Mao, "TPM 2.0 Event Log for U-Boot SPL on ARMv8" |
| U-Boot UEFI (`EFI_LOADER`) + Secure Boot + measured boot | `docs.u-boot.org` — uefi.html, measured_boot.rst, EFI variables via OP-TEE |
| EDK2 StandaloneMM variable service | OP-TEE `CFG_STMM_PATH` + U-Boot `CONFIG_EFI_MM_COMM_TEE` (StandAloneMM on RPMB) |
| RPi secure boot / OTP | Raspberry Pi `usbboot` secure-boot docs (Pi 4 testable; Pi 5 OTP-first) |

Internal: [ARCHITECTURE.md](ARCHITECTURE.md) · [ADR.md](ADR.md) (ADR-016 v261, ADR-017 ARM64) ·
[MITIGATE.md](MITIGATE.md) (vendor supply-chain attack surface this project closes).

Skills: `arm-trusted-firmware-optee`, `ftpm-optee-tpm` (github-yubios space).

---

## Idea (unscoped) — U-Boot console/shell authentication gate (FIDO2/U2F)

> Status: **Idea — scoped by ADR-027, not yet implemented or phased**. See ADR-027 for the
> resolved design decisions (scope, protocol, hook point, storage, recovery). Not yet in the
> phased roadmap above.
> Source: raw idea submitted via chat attachment; the submitted sketch used invented APIs
> (a fictional `<u2f.h>`/`u2f_authenticate()`, `libu2f-server` — which is a *relying-party
> server* verification library, not an embedded/authenticator-side client — a `do_shell`
> command that doesn't exist, and pre-Kconfig U-Boot Makefile style). What follows is the
> corrected shape of the idea, not the submitted sketch.

### The gap this closes

Everything else in this document hardens the boot chain *up to and through* U-Boot (TF-A
TBB, OP-TEE, the fTPM). None of it gates **U-Boot's own interactive console**. On real
hardware, U-Boot's `abortboot()` path (`common/autoboot.c`) lets anyone with UART/serial
access interrupt autoboot (Ctrl-C, or a configured keypress) and drop into the U-Boot
shell — from which they can dump memory, alter `bootargs`, reflash environment variables,
or otherwise interfere with the chain below Linux. U-Boot already ships a mitigation for
this — `CONFIG_AUTOBOOT_KEYED` + `CONFIG_AUTOBOOT_ENCRYPTION` (SHA256-hashed shared
password gating the break-in prompt) — but a shared password is exactly the class of
secret the FIDO2-first thesis exists to avoid: copyable, phishable, and not bound to
possession of hardware. Gating the U-Boot console behind a YubiKey touch instead would be
consistent with the rest of yubiOS's stance and would close a real gap in the ARM64 (and,
in principle, x86-64) boot chain.

### Corrected technical shape

- **Real hook point:** `abortboot()` / the autoboot key-sequence check in
  `common/autoboot.c`, not a `do_shell` command — there is no such command in mainline
  U-Boot. This is the same place `CONFIG_AUTOBOOT_ENCRYPTION` already hooks; a U2F gate
  is an alternative (or additional) factor at that same choke point.
- **No existing U-Boot FIDO2/U2F client stack.** `libfido2` and `libu2f-server` are
  host-side (glibc, USB via libusb) — neither runs inside U-Boot's freestanding runtime.
  This would need a from-scratch minimal CTAP1/U2F **HID client** on top of U-Boot's own
  USB host stack (`drivers/usb/host/`), reusing U-Boot's existing HID transport code
  (`common/usb_kbd.c` is the closest existing analog: USB HID class driver polled from the
  console layer) rather than trying to port a full authenticator library.
- **Prefer CTAP1/U2F over CTAP2** for a first pass — U2F's raw HID framing and
  challenge/register/authenticate flow is dramatically simpler to reimplement bare-metal
  than CTAP2/CBOR. This also matches what the file was actually named after.
- **Signature verification is not new work.** U-Boot already carries ECDSA verification
  for FIT image signing (`lib/ecdsa/`, optionally via mbedTLS) — the same primitive
  verifies a U2F assertion signature; no new crypto library needed, only a new caller.
- **Enrollment/key storage question (needs an ADR):** the U2F public key + key handle
  registered for console access has to live somewhere U-Boot can read before Linux boots
  — U-Boot's environment (if in a protected partition), a dedicated DPS partition, or (if
  Phase F for the fTPM has landed on that board) RPMB via OP-TEE. Decide this alongside
  ADR-018/019/020, not independently — it's the same "where do ARM64 secure secrets live"
  question the fTPM work already answers.
- **Fail-open vs fail-closed matters more here than elsewhere.** Losing the enrolled
  YubiKey should not brick the board. Needs an explicit recovery path (e.g. a backup
  YubiKey slot, mirroring the existing backup-key enrollment pattern already shipped for
  disk unlock, PR #3) decided in the ADR, not improvised at implementation time.

### Relationship to existing work

Distinct from and complementary to everything else in this file: the fTPM/TF-A/OP-TEE
work protects the **measured/enforced chain**; this protects the **interactive escape
hatch** into U-Boot that exists independently of that chain. Also distinct from the
already-shipped host-side FIDO2 work (LUKS2 unlock ADR-003, pam-u2f, SSH auth,
systemd-homed) — those all run after Linux is up; this runs inside U-Boot, before Linux
exists, with no libc, no filesystem beyond what U-Boot's own drivers provide, and no
existing embedded U2F client to build on.

### Scoping resolved — see ADR-027

The open questions this section used to list are now resolved in **ADR-027**
(U-Boot Console/Shell Authentication Gate): ARM64-only scope, CTAP1/U2F (not
CTAP2), hook at `abortboot()` alongside `CONFIG_AUTOBOOT_ENCRYPTION`, storage
piggybacked on whatever ADR-018/019/020 already decided per-board, and a
mandatory backup-key recovery path before this ever ships. Still **Proposed**,
not scheduled into a Phase F sub-phase — implementation waits on Phase F0–F3
landing far enough to know each board's Path A/B storage answer, plus a
standalone QEMU USB-HID-passthrough spike of the U2F client, kept deliberately
decoupled from the fTPM roadmap.

---

## Easter Egg — "The Konami Tap" (cosmetic, zero trust impact)

> Status: **Planning / fun**. Post-launch, low priority. Strictly cosmetic + diagnostic.
> Hard rule: this MUST NOT touch, weaken, or branch any trust boundary. It runs only
> after the user is already authenticated inside `yubiOS-enroll`, changes no keys, no
> signatures, no LUKS slots, no PAM policy. If it ever needs a security exception, it
> gets cut.

### Concept

yubiOS asks for a YubiKey touch at every boundary. So the egg speaks the only language
the hardware already has: **touch**. During the enrollment wizard, if the operator taps
the key in the classic Konami rhythm, yubiOS winks back.

The YubiKey only emits "user-presence" events (one tap = one event), so we encode the
code as a **timed tap sequence** read from `/dev/hidraw*` presence events, decoded like
Morse: long-hold = "direction change", short-tap = "press". Canonical sequence:

```
↑ ↑ ↓ ↓ ← → ← → B A
hold hold tap tap hold-L hold-R hold-L hold-R tap tap   (10 presence events, < 6s window)
```

### What it unlocks (all harmless)

1. **A boot splash** — a one-time plymouth/ASCII splash on the next boot: the yubiOS
   trust-chain diagram rendered in magenta (`#ff1493`, the YubiKey pink) with the koan
   *"No TPM. No OEM. No trust anchors you don't control."*
2. **Audit Mode (genuinely useful)** — enables one extra-verbose run of the measured-boot
   event log + `systemd-analyze security` for every yubiOS unit, dumped to the journal
   under a `yubiOS-audit` tag. Read-only; it reports, it does not change.
3. A `/etc/yubiOS/.konami` breadcrumb (mode 0644) so `yubiOS-enroll` can show a tiny
   "🕹 unlocked" line on later runs. No secret, no capability.

### Implementation sketch (post-launch)

- `usr/lib/yubiOS/konami.sh`: decode presence-event timings from libfido2's
  `fido_dev_get_touch_status()` polling loop already used by the enroll scripts; match
  against the sequence with a tolerance window.
- Splash: a `plymouth` theme drop-in shipped as a sysext (per the modularity ladder),
  so the egg is an *optional overlay*, never in the signed base `/usr`.
- Audit Mode: a `yubiOS-audit.service` `Type=oneshot` unit, `ConditionPathExists=/etc/yubiOS/.konami`,
  hardened like every other unit (it only reads).

### Why it is safe

- Gated entirely behind a completed, authenticated enrollment session.
- Produces only cosmetics + read-only diagnostics; enrolls nothing, signs nothing.
- Lives in a sysext overlay, so it never alters the dm-verity-measured base image.
- Doctrine still holds: the trust chain does not know or care that the egg exists.
