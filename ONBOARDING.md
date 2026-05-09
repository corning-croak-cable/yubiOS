# yubios Onboarding Guide

This guide walks you from a blank YubiKey to a fully enrolled yubios system.
Each section can be done independently if you are integrating into an existing system.

## Prerequisites

- YubiKey 5 series (firmware >= 5.2.3 for ed25519-sk)
- yubios installed to disk via `bootc install to-disk` or `mkosi`
- `ykman` installed: `dnf install yubikey-manager` (Fedora) / `apt install yubikey-manager` (Debian)

## Step 0: Verify YubiKey is detected

    fido2-token -L         # should show /dev/hidraw* device
    ykman info             # should show firmware version and enabled interfaces

    # Enable required interfaces if needed:
    ykman config usb --enable FIDO --enable CCID

## Step 1: Set FIDO2 PIN (required for all operations)

    ykman fido access change-pin

    # Also set the PIV PIN and PUK (for Secure Boot signing):
    ykman piv access change-pin   # default: 123456
    ykman piv access change-puk   # default: 12345678

## Step 2: Secure Boot signing (YubiKey PIV)

    sudo yubios-enroll-sb

    # What this does:
    # 1. Generates an ECC signing key in PIV slot 9c (key never leaves YubiKey)
    # 2. Self-signs a Secure Boot db certificate
    # 3. Signs all UKIs in /efi/EFI/Linux/ using sbsign + PKCS#11
    # 4. Exports the db cert for enrollment in UEFI Secure Boot
    # 5. Optionally runs sbctl enroll-keys if in UEFI Setup Mode

## Step 3: Disk encryption (FIDO2 via hidraw)

    sudo yubios-enroll-luks

    # What this does:
    # 1. Detects LUKS2 root partition
    # 2. Enrolls YubiKey FIDO2 (touch + PIN required at every boot)
    # 3. Updates /etc/crypttab with fido2-device=auto
    # 4. Rebuilds initramfs with fido2 dracut module
    # 5. OPTIONALLY removes passphrase slot (irreversible — keep backup!)

    # If removing passphrase, save a recovery key first:
    sudo systemd-cryptenroll --recovery-key /dev/nvme0n1p3
    # Save the recovery key somewhere secure (offline paper backup)

## Step 4: SSH keys (ed25519-sk, resident)

    yubios-enroll-ssh

    # What this does:
    # 1. Generates ed25519-sk resident key on YubiKey FIDO2 storage
    # 2. Saves public key stub to ~/.ssh/id_ed25519_sk
    # 3. Prints the public key for adding to remote authorized_keys
    # 4. On a new machine: ssh-keygen -K to recover stub from YubiKey

## Step 5: PAM U2F (sudo + login)

    sudo yubios-enroll-pam

    # What this does:
    # 1. Runs pamu2fcfg to generate a U2F credential for your user
    # 2. Appends to /etc/yubico/u2f_keys
    # 3. PAM U2F is already wired in /etc/pam.d/sudo
    # 4. From this point, sudo requires YubiKey touch + optional PIN

## Step 6: TOTP (optional, for app 2FA)

    # Add TOTP accounts via Yubico Authenticator or ykman:
    ykman oath accounts add --touch <issuer> <secret>
    ykman oath accounts code <issuer>

## Recovery: Lost YubiKey

1. Boot with recovery key (Step 3 backup) or live USB
2. Add `rd.break` to kernel cmdline in UEFI boot menu
3. In emergency shell: `mount -o remount,rw /sysroot`
4. Edit `/sysroot/etc/pam.d/sudo` — comment out `pam_u2f.so` line
5. Reboot, gain sudo, enroll new YubiKey via the enroll scripts

## Enrolling a backup YubiKey

    # Run each enroll script a second time with the backup YubiKey plugged in.
    # LUKS2 and pam-u2f support multiple enrolled keys.
    sudo yubios-enroll-luks   # second YubiKey
    sudo yubios-enroll-pam    # second YubiKey (appends to u2f_keys)
    # For Secure Boot: sign UKIs with backup key too
    sudo yubios-enroll-sb --additional
