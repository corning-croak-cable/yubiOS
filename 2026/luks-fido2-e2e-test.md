# LUKS2 FIDO2 end-to-end test (hardware-free CI path)

Closes #20. Relates to #33, #9. Refs yubiOS#25 (swu2f), yubi-OS/bcvk#3 (swtpm).

Two complementary e2e tests exercise the same trust boundaries:

| Test | Authenticator | Where it runs |
|------|---------------|----------------|
| `tests/vm/test-luks-fido2.sh`    | **real YubiKey** + `bcvk native-to-disk` | bare metal / hardware-in-the-loop |
| `tests/vm/test-luks-fido2-ci.sh` | **software** swtpm + swu2f via `bcvk ephemeral run` | CI, no hardware |

yubiOS production trust anchor stays the **YubiKey FIDO2** device (ADR-003). swtpm/swu2f are TEST-ONLY.

## CI path (`test-luks-fido2-ci.sh`)

Boots `bcvk ephemeral run --swtpm --swu2f <image>` and asserts over SSH:

- **swtpm** (host-side QEMU vTPM, bcvk#3): `/dev/tpm0` + `/dev/tpmrm0` present; `ConditionSecurity=measured-os` probed (skip-tolerant under direct-kernel boot).
- **swu2f Layer 1** (QEMU `u2f-emulated`, libu2f-emu, **CTAP1**, yubiOS#25): emulated token visible via `/dev/hidraw*` + `fido2-token -L`; pam-u2f register via `pamu2fcfg` + `pam_u2f.so` wired in `/etc/pam.d`.

### What is gated, and why

`systemd-cryptenroll --fido2` and systemd-homed FIDO2 need **CTAP2 `hmac-secret`**, which libu2f-emu (CTAP1) cannot provide. That requires **swu2f Layer 2** — an in-guest `/dev/uhid` CTAP2 authenticator shipped in the image — staged as a separate guest-image PR (yubiOS#25 follow-up). Until it lands, the test PROBES for a CTAP2 hmac-secret authenticator and **skips (does not fail)** the LUKS2-FIDO2 and homed-FIDO2 legs. pam-u2f + swtpm legs always run.

## bcvk dependency

`--swtpm` / `--swu2f` live on the canonical bcvk branch `yubi-OS/bcvk@feat/swtpm-ci` (bcvk is referenced, never merged, like the mkosi fork). Build it and put it on PATH before running. Runner host also needs `swtpm`+`swtpm-tools` and `libu2f-emu` with QEMU built `--enable-u2f`.
