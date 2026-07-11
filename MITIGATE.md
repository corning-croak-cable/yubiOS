# yubiOS Mitigation Matrix

Last reviewed: 2026-07-11
Status: planning baseline for `main`

This document maps the main yubiOS threat surfaces to current mitigations and open gaps. It is intentionally concrete: if the project cannot currently mitigate something, that is stated plainly.

## Threat Model Summary

| Area | Assumption |
|---|---|
| Owner | The owner controls the YubiKey, recovery key, Secure Boot enrollment, and installation target |
| Attacker | May control the network, registry mirror, disk at rest, or a stolen powered-off device |
| Strong attacker | May have temporary physical access, malicious firmware supply chain influence, or compromised CI inputs |
| Out of scope | Defeating a malicious CPU/SoC, closed-source ROM behavior, or an owner who enrolls malicious keys |

## Primary Mitigations

| Threat | Mitigation | Residual risk |
|---|---|---|
| Disk theft | LUKS2 root/swap with FIDO2 hmac-secret, PIN, touch, and offline recovery key | An attacker with both YubiKey and PIN can unlock |
| Silent disk decryption | FIDO2 physical presence and PIN | Malware running after unlock can access mounted plaintext while the session is active |
| Mutable `/usr` tampering | composefs over erofs with dm-verity and signed UKI command line | Firmware or kernel compromise can subvert checks below Linux |
| Malicious base image drift | Digest pins in [PINNED.md](PINNED.md), build policy, provenance/SBOM | Pins require active refresh for security fixes |
| Secure Boot key substitution | Owner-enrolled db key, PIV-backed signing, `sbverify` in CI | OEM firmware behavior is still trusted on x86-64 |
| TPM-bound update lockout | FIDO2 hmac-secret avoids PCR-hash-bound LUKS unlock | FIDO2 does not prove which OS asked for the secret |
| Weak local auth | pam-u2f >= 1.3.1, `required` PAM flow | Emergency recovery paths must remain guarded and documented |
| Per-user data exposure | systemd-homed LUKS2 homes with per-user FIDO2 credentials | Active logged-in session remains plaintext to that user's processes |
| Registry TLS downgrade | OpenSSL 3.5+ and Go 1.24+ defaults for `X25519MLKEM768` | Server-side support and future library defaults must keep being checked |

## ARM64-Specific Risks

ARM64 is the primary platform because it enables an owner-owned root below the UKI, but that path is only as strong as the board provisioning evidence.

| Risk | Mitigation | Status |
|---|---|---|
| Vendor secure-world ownership | TF-A + OP-TEE + fTPM stack owned and pinned by yubiOS | Design accepted; hardware validation post-launch |
| Unsafe or irreversible fuse burns | Path A/Path B split, sacrificial-board rehearsal, explicit board classification | Planning baseline; not production-complete |
| RPi 5 Broadcom VideoCore trust anchor | Classified as Path B only | Documented; not a production Path A target |
| RPMB/fTPM NV bootstrap | OP-TEE RPMB-backed NV for production, volatile NV only in CI | Needs real-board proof |
| U-Boot console break-in | Proposed FIDO2/U2F console gate plus recovery plan | Idea-stage, not a current mitigation |
| CoreSight/debug exposure | Secure Boot lockdown and board policy | Needs per-board kernel/config verification |
| Qualcomm-style sideload paths | Prefer non-Qualcomm targets for Path A; dm-verity above firmware boundary | Hardware below firmware remains out of scope |

## x86-64-Specific Risks

x86-64 remains supported but secondary. Its firmware and TPM root are not yubiOS-owned.

| Risk | Mitigation | Residual risk |
|---|---|---|
| OEM UEFI compromise | Owner-enrolled Secure Boot keys above firmware | Cannot remove OEM firmware as a trust anchor today |
| TPM/fTPM vendor ownership | Do not make TPM the sole disk-unlock gate | Measurement evidence may still come from an OEM-controlled stack |
| VM CI false confidence | Keep VM CI as compatibility evidence, not hardware-root evidence | Bare-metal x86 remains separate from ARM64 Path A goals |

## Firmware Validation

`yubiOS-chipsec-firstboot.service` is a one-shot firmware validation service. It is allowed raw hardware access only because firmware inspection requires it, and that exception is explicitly scoped. The service warns by default; fleet deployments may choose fail-closed policy through kernel arguments.

CHIPSEC does not provide a reliable automated Absolute/Computrace verdict. The best current evidence is informational scanning for WPBT and relevant UEFI variables, not a pass/fail guarantee.

## systemd Hardening Notes

Use `RestrictFileSystems=` when a filesystem-type allow/deny policy is appropriate and the kernel has BPF LSM support. Do not describe this as a systemd v261-only feature. Track `RestrictFileSystemAccess=` separately as the v261 filesystem-access primitive to evaluate in future service audits.

## What yubiOS Cannot Fully Prevent

- A malicious or vulnerable CPU/SoC executing below the owner-controlled chain.
- Closed boot ROM or firmware stages that cannot be replaced or verified by the owner.
- Physical coercion of the owner into providing PIN, touch, or recovery material.
- Compromise after the system is unlocked and the owner session is active.
- Supply-chain compromise of a pinned source before the project detects and rotates the pin.

```mermaid
flowchart TD
    OEM["🏭 OEM / Vendor\nSupply Chain Access"]

    subgraph S1["Step 1 — OEM Persistence"]
        S1A["1-A Modified PM firmware\n#PME enforcables\nModified S3 path"]
        S1B["1-B Stacked UEFI / EDK2\nevil-twin firmware\nBroken CNTVOFF_EL2"]
        S1C["1-C CVE exploitation\nPage-cache poisoning\n91 hidden GPT partitions"]
    end

    subgraph S2["Step 2 — Pre-Init Hijack"]
        S2A["2-A Obfuscated kernel modules\nInvisible device tree nodes\nCoresight debug channels"]
        S2B["2-B Firmware sideload\nModified libselinux/libapparmor\n/usr bind-mount poison"]
        S2C["2-C Poisoned generators\nJournal flush\nNVMe / GPT-auto blocked"]
    end

    subgraph S3["Step 3 — Runtime Control"]
        S3A["3-A Faux ACPI tables\nTEE MitM / tz.uefisecapp\nAbsolute Persistence"]
        S3B["3-B Radio persistence\nPassphrase exfil via framebuffer\nttyHS to TX/RX"]
        S3C["3-C dmesg/proc scrub\nfd hijacking\nMagic-number services"]
    end

    OEM --> S1A & S1B & S1C
    S1B --> S2A
    S1C --> S2B
    S2B --> S2C
    S2C --> S3A
    S3A --> S3B & S3C

    M1A["🔍 PCR 4 measurement\nConditionSecurity=measured-os\nchipsec detection"]
    M1B["🛡 Signed UKI + SecureBoot\nPCR 11 + usrhash= cmdline"]
    M1C1["🔄 Fedora 45 CVE patches\ndm-verity read protection"]
    M1C2["🛡 DPS UUID-only automount\nHidden partitions ignored"]
    M2A["🛡 Kernel lockdown SecureBoot\nSigned modules + IMA"]
    M2B["🛡 dm-verity /usr\non every IO read\nModified libs → IO error"]
    M2C["🛡 dm-verity generators\nusrhash= enforced\nDPS fallback discovery"]
    M3A1["🛡 Signed cmdline blocks\nACPI table override"]
    M3A2["✅ No TEE dependency\nYubiKey FIDO2 trust anchor\nNo tz.uefisecapp to MitM"]
    M3A3["🔍 chipsec detects\nComputrace in PCR event log"]
    M3B1["🛡 PrivateNetwork=yes\nBindNetworkInterface="]
    M3B2["✅ No passphrase to capture\nFIDO2 hmac-secret only\npam-u2f touch required"]
    M3C["🛡 dm-verity service units\nDynamicUser + ProtectProc=\nNoNewPrivileges="]

    S1A -. detected by .-> M1A
    S1B -. blocked by .-> M1B
    S1C -. mitigated by .-> M1C1
    S1C -. ignored by .-> M1C2
    S2A -. blocked by .-> M2A
    S2B -. blocked by .-> M2B
    S2C -. blocked by .-> M2C
    S3A -. blocked by .-> M3A1
    S3A -. immune .-> M3A2
    S3A -. detected by .-> M3A3
    S3B -. contained by .-> M3B1
    S3B -. immune .-> M3B2
    S3C -. blocked by .-> M3C

    style M2B fill:#0d6e0d,color:#fff
    style M2C fill:#0d6e0d,color:#fff
    style M1B fill:#0d6e0d,color:#fff
    style M3A2 fill:#ff1493,color:#fff
    style M3B2 fill:#ff1493,color:#fff
    style M3A3 fill:#8b4513,color:#fff
    style M1A fill:#1a1a2e,color:#fff
    style M2A fill:#1a1a2e,color:#fff
    style M3C fill:#1a1a2e,color:#fff
```

## Current Follow-Up

The active inconsistency and mitigation cleanup log is [refs/planning-cycle-2026-07-11.md](refs/planning-cycle-2026-07-11.md). It records the research sources used for the systemd, PQ TLS, bootc, and QEMU corrections.
