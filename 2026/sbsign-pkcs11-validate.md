# sbsign PKCS#11 validation

Validate systemd-sbsign + libykcs11 PKCS#11 URI for ECC slot 9c (ADR-008).

```sh
p11-kit list-modules | grep ykcs11
systemd-sbsign sign \
  --private-key "pkcs11:manufacturer=piv_II;id=%9c;type=private" \
  --private-key-source engine:pkcs11 \
  --certificate /etc/yubico/sb-cert.pem \
  --output yubiOS.signed.efi \
  yubiOS.efi
# Verify (sbverify is gone with sbsigntool; systemd-sbsign has no verify verb):
osslsigncode verify -in yubiOS.signed.efi -CAfile /etc/yubico/sb-cert.pem
```

Full runnable test: `tests/validate-pkcs11-uri.sh` (run with a YubiKey after `yubiOS-enroll-sb`).
The signing step is the gate; `osslsigncode` corroborates. Feed the validated URI
into the mkosi `SecureBootKey=` / `SecureBootKeySource=engine:pkcs11` settings.
