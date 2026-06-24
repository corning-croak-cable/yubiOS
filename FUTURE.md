# FUTURE.md — Post-Launch: A yubiOS-Owned Root of Trust on ARM64

> *No TPM. No OEM. No trust anchors you don't control.*
>
> Status: **Planning** — post-launch (after Phase 0 ships). Nothing here blocks launch.
> Scope: ARM64 only (ADR-017). x86-64 keeps its existing UKI + SecureBoot + dm-verity chain.

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
- **U-Boot** — our non-secure bootloader (BL33) that measures the OS and talks to our fTPM.

End state: an ARM64 board where every layer from the boot ROM key onward is signed by keys we hold,
the TPM is software we audit, and the YubiKey stays the user-facing root of trust. The fTPM guards
the *device fabric*; the YubiKey guards the *user identity*. They are complementary, not redundant.

---

## The trust chain we are building

```
ROTPK (our key hash in SoC OTP/fuses)
   │
  BL1  (boot ROM / first-stage)        ── measures ──┐
   │                                                  │
  BL2  (Trusted Boot stage)            ── measures ──┤   TCG2 event log
   │   verifies every image vs FIP certs (TBB)       │   (carried forward
   ├─► BL31  EL3 Secure Monitor (PSCI, SMC routing)  │    in memory)
   ├─► BL32  OP-TEE OS  ──► fTPM TA (ms-tpm-20-ref) ─┤
   └─► BL33  U-Boot                                   │
        │   replays event log → TPM2_PCR_Extend ──────┘
        │   measures kernel + DTB + initramfs (PCR 8/9)
        │   hands log to Linux via DTB chosen node
        ▼
      Linux  (tpm_ftpm_tee driver, IMA, /dev/tpm0)
        │
        └─► LUKS2 root: unlocked by YubiKey FIDO2 hmac-secret (unchanged)
            sealing/attestation: bound to fTPM PCR 0/1/7
```

Two roots of trust, two jobs:

| | fTPM (in OP-TEE) | YubiKey 5 |
|---|---|---|
| **Role** | Platform integrity, PCR measurement, attestation, optional seal | User identity, secret unlock, signing |
| **Lives in** | Secure world (Secure-EL1/EL0), on-device | External hardware, off-device |
| **Answers** | "Is this exact firmware + OS stack what we signed?" | "Is the authorized human present?" |
| **Survives OS reinstall** | NV state in RPMB (device-bound) | Yes — token is independent of the machine |
| **yubiOS stance** | We **own** it (our OP-TEE build, our keys) | Primary RoT, unchanged from x86-64 design |

The YubiKey still unlocks the disk (FIDO2 hmac-secret, ADR-003). The fTPM does **not** replace that.
The fTPM gives us measured-boot PCRs and a local attestation root on ARM64 that no vendor controls,
and a place to bind `ConditionSecurity=measured-os` (ADR-016) on hardware that otherwise has no TPM.

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

### 4. U-Boot (BL33, non-secure bootloader)

- Kconfig: `CONFIG_TEE=y`, `CONFIG_OPTEE=y`, `CONFIG_TPM=y`, `CONFIG_TPM_V2=y`,
  `CONFIG_TPM2_FTPM_TEE=y` (driver `tpm2_ftpm_tee.c`), `CONFIG_MEASURED_BOOT=y`,
  `CONFIG_TPM2_EVENT_LOG_SIZE=0x10000`.
- Device tree node: `tpm { compatible = "microsoft,ftpm"; };`
- `tpm2` command suite (`tpm2 init`, `tpm2 startup`) drives the fTPM; U-Boot replays the firmware
  event log into PCRs and measures kernel/DTB/initramfs.
- Hands the log to Linux by writing **`linux,sml-base`** and **`linux,sml-size`** into the kernel's
  `/chosen` DTB node.

### 5. Linux (normal-world consumer)

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

Internal: [ARCHITECTURE.md](ARCHITECTURE.md) · [ADR.md](ADR.md) (ADR-016 v261, ADR-017 ARM64) ·
[MITIGATE.md](MITIGATE.md) (vendor supply-chain attack surface this project closes).

Skills: `arm-trusted-firmware-optee`, `ftpm-optee-tpm` (github-yubios space).
