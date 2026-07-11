# LUKS2 FIDO2 end-to-end test

Status: active CI coverage with hardware-free and hardware-in-the-loop paths. Production trust remains a physical YubiKey; software authenticators are TEST-only.

Relates to yubiOS #20/#25/#33, yubi-OS/bcvk#3, ADR-003, ADR-026.

## Test paths

| Test | Authenticator | Where it runs | Purpose |
|---|---|---|---|
| `tests/vm/test-luks-fido2.sh` | Real YubiKey + `bcvk native-to-disk` | Bare metal / hardware-in-the-loop | Production-path confidence |
| `tests/vm/test-luks-fido2-ci.sh` | swtpm + swu2f via `bcvk ephemeral run` | CI, no hardware | Regression coverage |
| `tests/vm/test-fido2-enrollment.sh` | TEST-only `0mniteck/yubios:dev` image with `passless` | CI / explicit dispatch | CTAP2 hmac-secret legs without a physical token |

## CI coverage

- swtpm provides `/dev/tpm0`/`/dev/tpmrm0` for measured-boot code paths.
- swu2f Layer 1 covers CTAP1/U2F and pam-u2f flows.
- swu2f Layer 2 uses the TEST-only `passless` authenticator in the `dev` image for CTAP2 hmac-secret, covering `systemd-cryptenroll --fido2-device=auto` and systemd-homed legs where available.

## Guardrails

- The `dev` image must never become a production install default.
- Production images must not contain `passless` or any software authenticator used as a YubiKey stand-in.
- Physical-YubiKey passthrough remains the final authority for release confidence.

## bcvk dependency

`--swtpm` and `--swu2f` live on the canonical bcvk branch `yubi-OS/bcvk@feat/swtpm-ci`. bcvk is referenced by yubiOS CI and is not merged into this repository.
