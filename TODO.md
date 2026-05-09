# yubios — TODO / Future Work

## High priority

- [ ] Wire yubios-sudo PAM config into /etc/pam.d/sudo via Containerfile
- [ ] Add /usr/bin/ symlinks for yubios-enroll-* commands via Containerfile
- [ ] mkosi profiles: desktop (GNOME), minimal, surface-x86, surface-arm64
- [ ] Test LUKS2 FIDO2 unlock end-to-end in a VM with YubiKey passthrough
- [ ] Validate sbsign + libykcs11 PKCS#11 URI for ECC slot 9c

## Medium priority

- [ ] FIDO2-only Secure Boot path (HMAC-secret wraps signing key, no PIV/CCID needed)
  - Candidate: age-plugin-fido2-hmac for wrapping the ECDSA private key
  - Would allow fully hidraw-only trust chain (see ADR-002)
- [ ] Backup YubiKey enrollment UI in the wizard
- [ ] TOTP enrollment via ykman oath for app 2FA
- [ ] GPG/OpenPGP applet integration for git commit signing
- [ ] surface-x86 and surface-arm64 mkosi profile integration

## Low priority / Research

- [ ] composefs + verity full root verification (particleos-style)
- [ ] Multi-user YubiKey support (each user enrolls their own key)
- [ ] Investigate FIDO2 Large Blob extension for key backup/portability
- [ ] CTAP 2.1 minimum PIN length enforcement (minPinLength extension)
