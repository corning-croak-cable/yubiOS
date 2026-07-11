# yubiOS Architecture

Last reviewed: 2026-07-11
Status: planning baseline for `main`; ARM64 is primary, x86-64 is secondary and supported.

This document describes the current yubiOS architecture at the level needed for planning, review, and CI triage. Normative requirements live in [SPEC.md](SPEC.md), decisions live in [ADR.md](ADR.md), pinned inputs live in [PINNED.md](PINNED.md), and threat coverage lives in [MITIGATE.md](MITIGATE.md).

## Thesis

yubiOS is a FIDO2-first immutable Linux system where the owner-held YubiKey is the human-presence and identity root of trust. The platform root is intentionally separate: on ARM64, the long-term production path is an owner-provisioned TF-A + OP-TEE + fTPM stack; on x86-64, the platform firmware and TPM remain OEM-supplied, so x86-64 is fully supported but not the flagship ownership story.

## Target Platforms

| Platform | Priority | Trust-chain stance | Current use |
|---|---:|---|---|
| ARM64 / RK3588 Path A | Primary | Owner-burned ROTPK, TF-A Trusted Board Boot, OP-TEE, fTPM, U-Boot UEFI, signed UKI | Flagship target and post-launch hardware bring-up |
| ARM64 / Path B boards | Primary development | FIT verification plus measured/attested boot where fuses are unavailable or unsafe | CI and board bring-up rehearsal |
| x86-64 | Secondary, supported | Owner-enrolled UEFI Secure Boot above OEM firmware; optional TPM/fTPM for measurement only | VM CI, developer installs, compatibility |

## Trust Boundaries

| Boundary | Mechanism | Owner-controlled material | Notes |
|---|---|---|---|
| Secure Boot / UKI signing | `systemd-sbsign` via YubiKey PIV slot 9c | PIV private key and enrolled certificate | Requires CCID/pcscd; not a FIDO2/hidraw operation |
| Disk unlock | LUKS2 + `systemd-cryptenroll --fido2-device=auto --fido2-with-client-pin=yes` | FIDO2 hmac-secret credential plus recovery key | No TPM slot is enrolled as the sole unlock gate |
| User homes | `systemd-homed` LUKS2 + FIDO2 | Per-user FIDO2 credential | Enables per-user cryptographic lock and portable homes |
| SSH | OpenSSH `ed25519-sk` resident keys | FIDO2 resident key | PIN verification is expected for administrative use |
| Login / sudo | pam-u2f >= 1.3.1 | FIDO2/U2F credential | `required`, not `sufficient`, so touch remains mandatory |
| Platform measurement | TPM/fTPM PCRs and `ConditionSecurity=measured-os` | ARM64 fTPM owned by yubiOS on Path A | Measurement is complementary to YubiKey possession, not a replacement |

```mermaid
graph LR
    YK["🔑 YubiKey 5\nSingle hardware root of trust"]

    subgraph CCID["CCID interface (USB smartcard)"]
        PIV["PIV slot 9c\nEC P-256 keypair\nsystemd-sbsign --key pkcs11:..."]
    end

    subgraph HIDRAW["FIDO2 interface (hidraw)"]
        DISK["Disk unlock\nsystemd-cryptenroll --fido2-device=auto\nLUKS2 root + swap"]
        HOME["Home encryption\nhomectl create --fido2-device=auto\nper-user LUKS2 btrfs"]
        SSH["SSH authentication\ned25519-sk -O resident\n-O verify-required"]
        PAM["sudo / login\npam-u2f 1.3.1+\nauth required pam_u2f.so"]
        TOTP["App 2FA\nykman oath\nyubiOS-enroll-totp"]
    end

    YK --> PIV
    YK --> DISK
    YK --> HOME
    YK --> SSH
    YK --> PAM
    YK --> TOTP

    PIV --> SB["Secure Boot\nUEFI db\nUKI signing"]
    DISK --> ROOT["root fs\n/etc + /var"]
    HOME --> HOMES["user homes\n/home/user.homedir"]
    SSH --> SSHD["OpenSSH\nresident key"]
    PAM --> SUDO["sudo + login\ntouch always required"]

    style YK fill:#ff1493,color:#fff
```

## Boot Flow

```mermaid
graph TD
    FW["⬛ UEFI Firmware\nSecureBoot db"]
    SDB["🔷 systemd-boot\n(UEFI PE signed via PIV)"]
    UKI["📦 Unified Kernel Image\n.linux + .initrd + .cmdline\n.pcrsig + .pcrpkey"]
    VERITY["🔒 /usr partition\ndm-verity squashfs\nMerkle tree on every read"]
    LUKS["🔐 root filesystem\nLUKS2 btrfs\nFIDO2 hmac-secret enrolled"]
    HOMED["🏠 systemd-homed\nper-user LUKS2 btrfs\nFIDO2 per user"]
    YK["🔑 YubiKey 5\nPhysical possession required"]
    PCR["PCR 11 (TPM/fTPM, if present)\nboot phases measured\ninitrd-enter to complete"]

    FW ---|validates + measures| SDB
    SDB ---|picks newest UKI\nvalidates PE signature| UKI
    UKI ---|measures into PCR 11| PCR
    UKI ---|usrhash= in cmdline| VERITY
    UKI ---|initrd unlocks| LUKS
    LUKS ---|FIDO2 PIN + touch| YK
    HOMED ---|FIDO2 PIN + touch| YK
    FW -.-|UKI signed via PIV slot 9c| YK

    style YK fill:#ff1493,color:#fff
    style VERITY fill:#0d6e0d,color:#fff
    style LUKS fill:#0d6e0d,color:#fff
    style HOMED fill:#0d6e0d,color:#fff
```

### ARM64 Primary Path

1. Boot ROM verifies an owner-burned ROTPK hash when the board supports Path A.
2. TF-A BL1/BL2 verify BL31, OP-TEE BL32, and U-Boot BL33.
3. OP-TEE hosts StandaloneMM and the fTPM trusted application; RPMB backs secure variables and TPM NV state on production boards.
4. U-Boot provides UEFI services, Secure Boot variable handling, and measured boot into the fTPM.
5. systemd-boot loads the same signed UKI used on x86-64.
6. `/usr` is immutable and verified through composefs, erofs, and dm-verity.
7. Root, swap, and user homes unlock through YubiKey FIDO2 plus recovery material.

```mermaid
graph TD
    ROTPK["🔑 ROTPK hash\nSoC OTP / eFuse\n(Path A only)"]
    BL1["BL1 boot ROM"]
    BL2["BL2 Trusted Boot\nverifies BL31/32/33 vs FIP certs"]
    BL31["BL31 EL3 Secure Monitor\nPSCI + SMC routing"]
    BL32["BL32 OP-TEE OS\nSecure-EL1"]
    FTPM["fTPM TA (ms-tpm-20-ref)\nSecure-EL0\nUUID bc50d971..."]
    STMM["StandaloneMM TA\nUEFI vars PK/KEK/db/dbx\non RPMB"]
    UBOOT["BL33 U-Boot\nEFI_LOADER = UEFI firmware"]
    SDB["systemd-boot → UKI\nsame artifacts as x86-64"]
    LINUX["Linux\ntpm_ftpm_tee + IMA"]
    YK["🔑 YubiKey 5\nFIDO2 LUKS2 unlock"]

    ROTPK -.->|Path A anchors| BL1
    BL1 -->|measures| BL2
    BL2 --> BL31 --> BL32
    BL32 --> FTPM
    BL32 --> STMM
    BL2 --> UBOOT
    UBOOT -->|EFI_TCG2 measures into| FTPM
    UBOOT -->|reads vars from| STMM
    UBOOT --> SDB --> LINUX
    LINUX -->|/dev/tpm0| FTPM
    LINUX --> YK

    style FTPM fill:#0d6e0d,color:#fff
    style YK fill:#ff1493,color:#fff
    style BL32 fill:#8b4513,color:#fff
    style ROTPK fill:#1a1a2e,color:#fff
```

```mermaid
graph TD
    Q{Can we burn\nROTPK to OTP/eFuse?}

    Q -->|Yes — Path A| A["ENFORCING\nfull Trusted Board Boot\nROTPK in fuses\nBL1 rejects unsigned images\nbad code never runs"]
    Q -->|No / locked / dev board — Path B| B["MEASURED + ATTESTED\nU-Boot FIT verified boot\nkey in control DTB\nmeasure into fTPM PCRs\ntrust decided AFTER boot"]

    A --> AT["Targets: RK3588 (Orange Pi 5, Rock 5B),\nRK3399 (RockPro64), Ampere"]
    B --> BT["Targets: dev boards, early bring-up,\nRPi 5 (VideoCore closes owner RoT)"]

    A --> SEAL["fTPM PCRs + YubiKey\nrelease secrets / gate access"]
    B --> SEAL

    style A fill:#0d6e0d,color:#fff
    style B fill:#8b4513,color:#fff
    style SEAL fill:#ff1493,color:#fff
```

### x86-64 Supported Path

1. Owner-enrolled UEFI Secure Boot verifies systemd-boot and the signed UKI.
2. TPM measurement is used where available, but the TPM is not the owner-held identity root.
3. `/usr`, root, swap, and home follow the same immutable and FIDO2-gated runtime model as ARM64.

## Build And Distribution

The project keeps both build paths active:

| Path | Output | Purpose |
|---|---|---|
| bootc / OCI | `docker.io/0mniteck/yubios:latest`, `<sha>`, and test tags | Day-2 update stream and VM test source |
| mkosi | signed UKI and disk image | Installer and image-level validation |
| firmware OCI tags | `firmware`, `firmware-<sha>` | ARM64 secure-world bundle publication |
| dev OCI tags | `dev`, `dev-<sha>` | TEST-only swu2f-enabled boot validation image |

```mermaid
graph LR
    BASE["fedora-bootc:45\ndigest-pinned, see PINNED.md"]
    CF["Containerfile\nyubiOS packages + usr/ overlay"]
    REGO["yubiOS.rego\nOPA/Rego Build Policy\nisCanonical + dhi.io registry"]
    OCI["OCI Image\nyubiOS:latest"]
    REG["docker.io/0mniteck/yubios\n:latest + immutable :commit-sha"]

    BASE -->|FROM digest-pinned| CF
    CF -->|docker buildx build\n--policy strict=true\n--attest provenance,sbom| REGO
    REGO -->|policy passes| OCI
    OCI --> REG

    REG -->|bcvk native-to-disk\nno QEMU| HW["💽 Physical disk\n/dev/nvme0n1"]
    REG -->|bcvk to-disk\nQEMU VM| IMG["📁 qcow2 image\nfor cloud/VM"]
    REG -->|bcvk ephemeral run\nYubiKey passthrough| VM["🖥 Ephemeral VM\nCI / dev loop"]

    HW -->|first boot| ENROLL["yubiOS-enroll.service\nConditionSecurity=measured-os\nYubiKey tap"]

    style REGO fill:#8b0000,color:#fff
    style HW fill:#0d6e0d,color:#fff
    style ENROLL fill:#ff1493,color:#fff
```

```mermaid
graph LR
    subgraph SHIP["Shipped image — 2 partitions"]
        ESP["1 ESP\nvFAT /efi\nsystemd-boot + UKI"]
        USRA["2 /usr A\nerofs ro\ndm-verity + PKCS7 sig\nyubiOS_0.x"]
        VERTA["3 /usr A verity\nMerkle tree"]
        SIGA["4 /usr A sig\nPKCS7 of root hash"]
    end

    subgraph REPART["Created on first boot — systemd-repart"]
        USRB["5-7 /usr B\n_empty until first update"]
        ROOTFS["8 root fs\nLUKS2 btrfs\nFIDO2 enrolled\nsized to disk"]
        HOMEFS["9 home fs\nhomed per-user LUKS2"]
        SWAPFS["10 swap\nencrypted"]
    end

    SHIP --> REPART

    style USRA fill:#0d6e0d,color:#fff
    style ROOTFS fill:#8b4513,color:#fff
    style HOMEFS fill:#4b0082,color:#fff
```

```mermaid
sequenceDiagram
    actor User
    participant SU as systemd-sysupdate
    participant Part as /usr B partition
    participant ESP as ESP (/efi)
    participant SDB as systemd-boot
    participant UA as yubiOS-upgrade.service

    User->>SU: bootc upgrade
    SU->>Part: /usr partition (yubiOS_0.y)
    SU->>Part: Verity data partition
    SU->>Part: PKCS#7 sig partition
    SU->>ESP: UKI yubiOS_0.y+3
    Note over Part,ESP: counter +3 = max 3 boot attempts
    SDB->>SDB: strverscmp picks newest UKI
    SDB->>SDB: decrement counter on each boot
    Note over SDB: counter=0 -> skip, fall back to yubiOS_0.x
    SDB-->>UA: boot into yubiOS_0.y
    UA->>UA: verify health
    UA->>ESP: bootctl set-boot-good
    Note over ESP: counter stripped -> yubiOS_0.y permanent
```

`PINNED.md` is the single source of truth for base-image digests and tool pins. Run-specific digests in old workflow logs or historical ADRs are evidence, not evergreen requirements.

## Version Requirements

| Component | Minimum / stance | Why |
|---|---|---|
| systemd | v261 target in current base | `ConditionSecurity=measured-os`, `systemd-tpm2-swtpm.service`, `systemd-sysinstall`, LUO/KHO research, and v261 planning work |
| systemd-sbsign | v257+ | Native PKCS#11 UKI signing path |
| pam-u2f | 1.3.1+ | Avoids CVE-2025-23013 bypass class |
| OpenSSL | 3.5+ for OpenSSL clients | Default hybrid `X25519MLKEM768` group |
| Go | 1.24+ for Go TLS clients | Default hybrid `X25519MLKEM768` group in `crypto/tls` |
| QEMU | Pinned by workflow | zstd EFI zboot boot compatibility is handled through the current pinned workaround |

### systemd hardening correction

The 2026-07-11 research cycle found one important wording bug: `RestrictFileSystems=` is not a new v261 directive. It is the older BPF-LSM filesystem-type limiter documented in `systemd.exec(5)`. systemd v261 added `RestrictFileSystemAccess=`, which should be evaluated separately. Documentation and future hardening audits should avoid gating `RestrictFileSystems=` on v261.

## First-Boot Services

| Service | Gate | Notes |
|---|---|---|
| `yubiOS-chipsec-firstboot.service` | `ConditionSecurity=measured-os`, `ConditionFirstBoot=yes` | One-shot firmware validation; raw hardware access is explicitly scoped |
| `yubiOS-enroll.service` | Measured boot expected | Enrolls owner YubiKey and recovery material after first boot |
| repart / install flow | DPS and systemd-repart | No traditional `/etc/fstab` installer model |

```mermaid
graph TD
    Q{What are
you adding?}

    Q -->|Extends /usr itself
same namespace| SE["systemd-sysext\n\nExamples: debug tools, drivers\nYubiKey tools overlay\n\nTrust: Verity + PKCS#7\nread-only overlayfs on /usr"]
    Q -->|Isolated system service
own root + namespace| PS["Portable Service\nRootImage=\n\nExamples: chipsec, yubikey-agent\n\nTrust: Verity + PKCS#7 GPT image\nsandboxing opt-OUT"]
    Q -->|Full secondary OS
legacy packages| NS["systemd-nspawn\n\nExamples: Debian dev container\nRPM compat layer\n\nTrust: same PKCS#7 Verity"]
    Q -->|End-user app| FL["flatpak / OCI\n\nWeakest trust\nno Verity attestation"]

    style SE fill:#0d6e0d,color:#fff
    style PS fill:#8b4513,color:#fff
    style NS fill:#1a1a2e,color:#fff
    style FL fill:#555,color:#fff
```

## Current Research Notes

The active planning note for this refresh is [refs/planning-cycle-2026-07-11.md](refs/planning-cycle-2026-07-11.md). It records the sources consulted, the inconsistencies found, and follow-up items for CI and hardware validation.

## Open Edges

- ARM64 Path A still needs real-board fuse/RPMB validation before being claimed as a production hardware route.
- The zstd EFI zboot workaround should remain pinned and explicit until upstream QEMU behavior is available in the runner fleet.
- PQ TLS is satisfied by current OpenSSL and Go defaults, but CI should keep asserting it so a future base digest does not silently regress.
- The U-Boot FIDO2/U2F console gate remains idea-stage until the USB HID and recovery model are audited.
