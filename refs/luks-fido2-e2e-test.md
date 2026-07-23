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

## Latest CI milestone

Run [29525332901](https://github.com/yubi-OS/yubiOS/actions/runs/29525332901) on 2026-07-16 is a useful milestone even though the ARM64 job failed. The `arm64` lane on self-hosted `rock1` reached a booted Fedora 45 aarch64 guest, showed a serial login prompt, reached `multi-user.target` and `graphical.target`, and started core services including `systemd-homed.service`, `pcscd.service`, `NetworkManager.service`, and `sshd.service`.

The host/harness wins from that run are now evidence-backed:

- real ARM64 KVM was available on `rock1`;
- `/dev/fuse` was present for virtiofsd/bwrap paths;
- pinned QEMU commit `3a18e8a25992d1643707e2cebdd6e9bb2bd7d3b9` booted the zstd EFI zboot image path;
- the immutable yubi-OS/bcvk release descendant in `PINNED.md` built and exposed `--swtpm` plus `--swu2f`;
- the yubiOS image was pulled into podman storage for bcvk;
- AppArmor profile relaxation completed before boot.

The active failure moved inside the guest: `bootloader-update.service` failed during `tests/vm/test-luks-fido2-ci.sh`, and `tests/vm/test-fido2-enrollment.sh` skipped because that earlier step failed. Full run evidence is recorded in [vm-e2e-run-29525332901.md](vm-e2e-run-29525332901.md).

## Guardrails

- The `dev` image must never become a production install default.
- Production images must not contain `passless` or any software authenticator used as a YubiKey stand-in.
- Physical-YubiKey passthrough remains the final authority for release confidence.

## bcvk dependency

`--swtpm` and `--swu2f` are required from the immutable yubi-OS/bcvk release-descendant commit in `PINNED.md`. bcvk is referenced by yubiOS CI and is not merged into this repository.
