# yubiOS — Architecture

> *No TPM. No OEM. No trust anchors you don't control.*

YubiKey replaces the TPM at every trust boundary: Secure Boot signing, disk encryption,
home directory encryption, SSH, and PAM authentication. ARM64 is yubiOS's primary target
platform (ADR-023) — it is the only platform where yubiOS owns the hardware root of trust
all the way to the boot ROM key (§7, ADR-018/019/020/021). x86-64 is a fully supported
secondary platform with an identical trust chain above the UKI.

---

## 1. Boot Trust Chain

Every component from firmware to userspace is cryptographically signed and measured.
The YubiKey is the sole un-exportable root of trust.

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

---

## 2. YubiKey Interface Map

One hardware token. Five trust boundaries.

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

---

## 3. Build Pipeline

Single OCI image. Three deployment paths.

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

---

## 4. Disk Partition Layout

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

---

## 5. A/B Update Lifecycle

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

---

## 6. Modularity Ladder

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

---

## 7. ARM64 Secure-World Stack (Primary Platform; Hardware Bring-Up Post-Launch — ADR-018/019/020/021/023)

> ARM64 is yubiOS's primary target platform (ADR-023). This section is the owner-owned root of
> trust yubiOS builds itself: TF-A, OP-TEE, the fTPM, and U-Boot. Hardware bring-up on real boards
> is post-launch; the YubiKey stays the primary RoT, the fTPM is the platform-integrity root. Full plan: [FUTURE.md](FUTURE.md).

### 7a. ARM64 boot trust chain (TF-A → OP-TEE/fTPM → U-Boot UEFI)

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

### 7b. Two provisioning paths (root of trust)

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

---

## Key Version Requirements

| Component | Minimum | Reason |
|---|---|---|
| systemd | **261** | `ConditionSecurity=measured-os`, `systemd-sbsign`, FIDO2 cryptenroll |
| YubiKey firmware | **5.2.3** | ed25519-sk support |
| OpenSSH | **8.2** | FIDO2 key types |
| pam-u2f | **1.3.1** | CVE-2025-23013 fix |
| Fedora | **45** post-June-19 | systemd 261, fedora-bootc purpose-built base |

---

*All architectural decisions with rationale and sources in [ADR.md](ADR.md).*
