> **Archived research snapshot** synced from the assistant knowledge base (`documents/github-yubios-KS9n5GAT/knowledge/`) on 2026-07-23. May predate current specs — treat `PINNED.md` and the dated `refs/*` notes as the live source of truth; this is background research context only.

---

# 0pointer.net / Lennart Poettering — Knowledge File
_Source: https://0pointer.net/blog/ — Refreshed: June 23, 2026_

## Who / Context

Lennart Poettering: creator of systemd, PulseAudio, Avahi. Blog "Pid Eins" (PID 1). Co-founder (2026) of **Amutable** — building immutable Linux systems with integrity, determinism, and verification. Most relevant person in the industry for yubiOS architecture decisions.

Mastodon: @pid_eins@mastodon.social

---

## Amutable (2026)

Lennart + core systemd contributors (Christian Brauner, David Strauss, Michael Vogt, Zbigniew Jedrzejewski-Szmek, etc.) founded Amutable to commercialize image-based Linux.
Direct alignment with yubiOS philosophy. Watch https://amutable.com/ for reference implementations.

---

## "Fitting Everything Together" — Core Architecture Vision

Source: https://0pointer.net/blog/fitting-everything-together.html

This is the foundational document for yubiOS design. Key points:

### Design Goals (directly applicable)
1. **Image-based over package-based** — reproducible, immutable, cattle not pets
2. **Trust chain from boot loader to apps** — all code cryptographically validated before execution
3. **Offline security** — data encrypted at rest, TPM2-bound (yubiOS: YubiKey-bound)
4. **Cryptographic measurement everywhere** — remote attestation
5. **Self-updating** — A/B atomic upgrades via systemd-sysupdate
6. **Robust against power loss** — A/B partition scheme
7. **Factory reset** — systemd-repart erases flagged partitions on request
8. **Vendor/system/user separation** — `/usr` immutable, `/etc` + `/var` writable
9. **Adaptive** — first-boot partition creation via systemd-repart
10. **No installer** — any image is a live image; dd to disk
11. **Local key generation** — no pre-provisioned secrets

### Partition Layout
```
1. ESP (UEFI System Partition)
2. /usr A — immutable, Verity-protected, signed
3. /usr B — immutable, Verity-protected, signed (A/B updates)
4. root fs — writable, LUKS2-encrypted (TPM2-bound; yubiOS: YubiKey-bound)
```

Discoverable Partitions Specification (DPS) partition UUIDs — self-describing, no /etc/fstab needed.

### Boot Chain
- **Unified kernels** (UKI) = kernel + initrd + cmdline + splash → single UEFI PE binary
- **systemd-boot** picks newest by version sort
- `usrhash=` kernel parameter → dm-verity root hash in signed cmdline
- **systemd-repart** creates root fs on first boot, encrypts, enrolls TPM2 key
- yubiOS delta: replace TPM2 enrollment with YubiKey FIDO2 via systemd-cryptenroll

### Modularity Layers
| Layer | Tool | Trust |
|---|---|---|
| OS extensions | systemd-sysext | Verity + PKCS#7 signed, overlayfs on /usr |
| Isolated services | Portable Services (RootImage=) | Verity + signed, own namespace |
| Apps | flatpak / OCI | weaker — no attestation |

### Key Insight for yubiOS
The entire stack is already designed for hardware root-of-trust. The only yubiOS delta is:
- Replace TPM2 with YubiKey everywhere `systemd-cryptenroll` is called
- The rest (UKI signing, dm-verity, systemd-sysext, systemd-repart) is upstream

---

## systemd Versions — Recent Features (yubiOS relevant)

### v260 (March 17, 2026) — current stable
- **`.mstack` Overlay Mount Stacks** (`RootMStack=`) — overlayfs layers + bind mounts for services
- **NvPCR Measurements for Activated DDIs** — improved measurement of extension images
- **LUKS Volume Key Fixation** — pin LUKS key slot after enrollment
- **Unprivileged Portable Services** — portable services without root
- **Image Policy Improvements** — finer-grained DDI image policy
- **`PrivateUsers=managed`** — automatic UID management for user namespaces
- **`RefreshOnReload=` in service units** — signal service on credential rotation
- **`BindNetworkInterface=`** — restrict service to specific network interface
- `importctl pull-oci` — pull OCI containers into machined
- TPM2 quirks database in udev

### v259 (Dec 2025)
- NvPCR support (non-volatile PCR)
- `run0 --empower` (capability escalation without sudo)
- `systemd-repart` Varlink IPC API
- `ExecReloadPost=` — run commands after successful reload
- `systemd-repart --defer-partitions-factory-reset=` — factory reset rework

### v258 (Sep 2025)
- `homectl list-signing-keys` / `add-signing-key` — FIDO2 signing key management for homed **[critical for yubiOS]**
- **Offline Signing of Artifacts** — sign DDIs without the key on the build host
- `PAMName=` in services with ask-password protocol
- `PrivateUsers=full` — complete user namespace isolation
- `LoadCredentialEncrypted=` in per-user service manager
- Factory Reset rework (`systemd-repart`)
- `fsverity` in systemd-repart

### v257 (Dec 2024)
- **SecureBoot signing with systemd-sbsign** tool (replaces sbsigntools) **[critical for yubiOS UKI]**
- Multi-Profile UKIs
- **Combined signed PCR + locally managed PCR policies** for disk encryption
- IPE LSM support (Integrity Policy Enforcement)
- `systemd-sysusers` fully locked accounts
- SecureBoot key enrollment prep with `bootctl`
- ID-mapped mounts for per-service directories

### v256 (Jun 2024)
- `run0` as sudo replacement
- **ssh into systemd-homed accounts** — SSH key in home record
- `systemd-vmspawn`
- Mutable systemd-sysext
- `systemd-cryptenroll` without device argument

---

## mkosi (Daan De Meyer re-introduction)

Source: https://0pointer.net/blog/a-re-introduction-to-mkosi-a-tool-for-generating-os-images.html

### What it builds
- GPT disk images (via systemd-repart)
- Tar / CPIO archives
- USIs (Unified System Images = full OS in UKI)
- Sysext, confext, portable images
- Directory trees

### Key workflow
```ini
# mkosi.conf
[Host]
Distribution=debian
Release=trixie

[Output]
Format=disk
OutputDirectory=mkosi.output/

[Content]
Bootable=yes
Packages=systemd-boot
         systemd-cryptsetup
         pcscd
         libpam-yubico
```

### Partition customization
`mkosi.repart/` directory — systemd-repart partition definitions:
- Encrypted root partition
- dm-verity signed partitions
- `/usr` only (no root partition)
- XBOOTLDR, swap

### Build scripts
- `mkosi.postinst` — runs on host after packages installed
- `mkosi.postinst.chroot` — runs inside image
- `mkosi.extra/` — extra files copied into image

### For CI (yubiOS context)
```bash
mkosi build    # build image
mkosi boot     # boot in systemd-nspawn
mkosi qemu     # boot in QEMU
mkosi -f build # force rebuild
```

---

## Key Directives Quick Reference (yubiOS service hardening)

From the "Fitting Everything Together" analysis + systemd exec docs:

### For YubiKey-auth services
```ini
[Service]
Type=notify
DynamicUser=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
NoNewPrivileges=yes
CapabilityBoundingSet=CAP_DAC_OVERRIDE
SystemCallFilter=~@mount @reboot @debug
RestrictAddressFamilies=AF_UNIX AF_NETLINK
ProtectKernelModules=yes
ProtectKernelTunables=yes
ProtectControlGroups=yes
LockPersonality=yes
RestrictRealtime=yes
```

### For cryptenroll / LUKS services
```ini
[Service]
CapabilityBoundingSet=CAP_SYS_ADMIN CAP_DAC_READ_SEARCH
PrivateDevices=no       # needs /dev/sda etc
ProtectSystem=strict
ReadWritePaths=/etc/crypttab
```

---

## Links
- Main blog: https://0pointer.net/blog/
- Fitting Everything Together: https://0pointer.net/blog/fitting-everything-together.html
- Amutable: https://amutable.com/
- Mastodon stories index: https://mastodon.social/@pid_eins
- All Systems Go conference: https://all-systems-go.io/
