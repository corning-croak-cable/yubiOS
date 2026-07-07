<div align="center">

<img src="https://raw.githubusercontent.com/yubi-OS/yubiOS/main/assets/logo.png" alt="yubiOS" width="140"/>

## yubiOS Onboarding Guide

*From blank YubiKey to fully enrolled system — four steps.*

</div>

---

## Prerequisites

| | |
|---|---|
| YubiKey 5 series | firmware ≥ 5.2.3 |
| systemd | **≥ 261** (ADR-016) |
| OpenSSH | ≥ 8.2 |
| pam-u2f | **≥ 1.3.1** (CVE-2025-23013) |

Install packages if not already present:

```sh
# Fedora
dnf install yubikey-manager libfido2 pam-u2f opensc yubico-piv-tool fido2-tools

# Debian/Ubuntu
apt install yubikey-manager libfido2-1 libpam-u2f opensc yubico-piv-tool fido2-tools
```

## Step 0: Verify YubiKey

```sh
fido2-token -L         # /dev/hidrawN should appear
ykman info             # shows firmware version + enabled interfaces

# Enable required interfaces:
ykman config usb --enable FIDO --enable CCID
```

## Step 1: Set PINs

```sh
ykman fido access change-pin    # FIDO2 PIN (used for disk unlock + SSH + PAM)
ykman piv access change-pin     # PIV PIN (used for Secure Boot signing)
ykman piv access change-puk     # PIV PUK (recovery for PIV PIN lockout)
```

## Step 2: Secure Boot signing

```sh
sudo yubiOS-enroll-sb
```

Generates ECC key in PIV slot 9c (key never leaves YubiKey). Signs UKIs in `/efi/EFI/Linux/`.
Exports `yubiOS-sb.cer` for UEFI enrollment.

**UEFI enrollment:**
1. Copy `yubiOS-sb.cer` to USB or `/efi/`
2. Enter firmware setup (commonly F2 / Del / Esc at power-on; on Surface: Volume Up + Power)
3. Security → Secure Boot → Reset to Setup Mode
4. Enroll Platform Key from file → `yubiOS-sb.cer`
5. Re-enable Secure Boot

## Step 3: Disk encryption (FIDO2)

```sh
# Save a recovery key first — print it and keep it offline
sudo systemd-cryptenroll --recovery-key /dev/nvme0n1p3

# Enroll YubiKey (touch + PIN required at every boot)
sudo yubiOS-enroll-luks
```

On next boot: touch YubiKey when the LED flashes, enter FIDO2 PIN.

## Step 4: SSH keys (ed25519-sk)

```sh
yubiOS-enroll-ssh
```

Generates a resident `ed25519-sk` key. Private key stays on YubiKey.

```sh
# Add to GitHub / remote hosts:
cat ~/.ssh/id_ed25519_sk.pub

# On a new machine, recover stub from YubiKey:
ssh-keygen -K
```

## Step 5: sudo / login (pam-u2f)

```sh
sudo yubiOS-enroll-pam

# Test in a new terminal BEFORE closing this session:
sudo whoami     # should prompt for YubiKey touch
```

---

## Recovery: lost YubiKey

1. Boot with recovery key (saved in Step 3)
2. Add `rd.break` in UEFI boot menu kernel cmdline
3. `mount -o remount,rw /sysroot`
4. Comment out `pam_u2f.so` line in `/sysroot/etc/pam.d/sudo`
5. Reboot, gain sudo, enroll new YubiKey

## Backup YubiKey

Run each script a second time with the backup key plugged in.
LUKS2 and pam-u2f support multiple enrolled keys natively.
