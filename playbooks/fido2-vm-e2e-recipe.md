# FIDO2 VM e2e — the known-working recipe (2026-08-01)

## Context

Apply when the software FIDO2 / LUKS2 / systemd-homed VM lane regresses, or before changing anything it depends on: `passless`, host `swu2f`, `pam-u2f`, `homectl`, `ssh-keygen -t ed25519-sk`, or the image's PAM/enrollment units.

`B-VM-CTAP2` is **RESOLVED** (2026-07-25) — the chain is proven end-to-end with no skips. This playbook **freezes** that recipe so a regression is recognized as a regression instead of reopening the same ground.

Scope boundary: this is the **software** lane. It proves the code path, not physical-presence semantics, firmware ownership, or RPMB freshness — that is `B-REAL-FIDO2`, open.

## Decision

The known-working configuration, which any change must preserve:

- Host launches the guest via **`bcvk --swu2f`** (uhid software authenticator) plus **`swtpm`**.
- In-guest **`passless`**, pinned to an immutable commit, exposes `/dev/hidraw0` with **CTAP2 `hmac-secret`**.
- **`pamu2fcfg` must be in the built image** — on Fedora Rawhide it is a separate subpackage from `pam-u2f`, and it must be added in the **production `Containerfile`**, not `mkosi.conf`.
- `homectl create` for a FIDO2 home must pass **`--enforce-password-policy=no`**; an empty `NEWPASSWORD=` otherwise hangs ~5 minutes instead of failing fast.
- `pam-u2f` wired **`required`** (not `sufficient`) with a **1.3.1** floor.
- Real-key interaction is guarded — see [hw-device-and-allow-real-u2f](hw-device-and-allow-real-u2f.md).

## Mechanism

```
host: bcvk --swu2f (uhid) + swtpm
  → in-guest `passless` up
    → /dev/hidraw0 enumerated, CTAP2 hmac-secret available
      → LUKS2 FIDO2 enroll + unlock                PASS
        → systemd-homed FIDO2 home create          PASS
          → pamu2fcfg FIDO2 registration           OK
            → ssh-keygen -t ed25519-sk             OK
```

```bash
IMG=docker.io/0mniteck/yubios:dev-<short-sha>   # or an immutable @sha256 digest
curl -sS -X POST \
  "https://api.github.com/repos/yubi-OS/yubiOS/actions/workflows/ci_test-vm.yml/dispatches" \
  -H 'Accept: application/vnd.github+json' \
  -d "{\"ref\":\"main\",\"inputs\":{\"image\":\"${IMG}\",\"hw_device\":\"\",\"allow_real_u2f\":\"false\"}}"
# then verify the INNER run and read for SKIPs, not just conclusion=success
```

```bash
tests/vm/test-luks-fido2-ci.sh      # passless + swtpm: LUKS2 + homed (CI, passless-only)
tests/vm/test-fido2-enrollment.sh   # CTAP2 hmac-secret legs
tests/vm/test-luks-fido2.sh         # hardware-in-the-loop variant

bats tests/unit/test-pam-u2f-stack.bats   # asserts `required` + 1.3.1 floor
bats tests/unit/test-enroll-{luks,pam,ssh,unit}.bats
```

| Symptom | First suspect |
|---|---|
| `pamu2fcfg: command not found` in-guest | the subpackage was dropped from the **production `Containerfile`** — check that file, not `mkosi.conf` |
| `homectl create` hangs ~5 min | missing `--enforce-password-policy=no` |
| `/dev/hidraw0` absent | `--swu2f` not passed, or the host uhid load failed |
| CTAP2 `hmac-secret` unsupported | the `passless` pin moved — it is pinned immutably for exactly this reason |
| passless tests **skipped**, guard message about a real device | a physical key is attached; the refusal is correct |
| lane green but assertions skipped | read the log for skip lines — `success` with skips is **not** coverage |

**Do not** "fix" a guard refusal by unplugging the key or patching `assert_passless_only`. **Do not** move the enrollment fix back to `mkosi.conf` — that build path does not ship the image, which is exactly why the first attempt (PR #102) had no effect.

## Verified working (2026-08-01)

- Run [30139433902](https://github.com/yubi-OS/yubiOS/actions/runs/30139433902) / job **89629762908** proves the whole chain **with no skips**: host `bcvk --swu2f` uhid load → in-guest `passless` → `/dev/hidraw0` CTAP2 hmac-secret enumeration → LUKS2 FIDO2 enroll/unlock **PASS** → systemd-homed FIDO2 home create **PASS** → `pamu2fcfg` registration **OK** → `ssh-keygen -t ed25519-sk` **OK**. Both scripts report PASS.
- Two real bugs got it there: (1) `pamu2fcfg` missing from the built image (Rawhide subpackage split) — fixed in the production `Containerfile` in **PR #125**, after an earlier fix to the wrong build path (`mkosi.conf`, **PR #102**) had no effect; (2) `homectl create` hanging 5 min on an empty `NEWPASSWORD=` — fixed with `--enforce-password-policy=no` (**PR #102**).
- `B-VM-CTAP2` **RESOLVED (2026-07-25)** in `docs/BLOCKERS.md`; Linear **OMN-48 Done**.
- Related: `B-VM-SSH` + `B-VM-BOOTLOADER-UPDATE` retired by run [29872832727](https://github.com/yubi-OS/yubiOS/actions/runs/29872832727).

## Tradeoffs

The software lane is deterministic and cheap, and proves interface behavior only. It cannot prove physical presence, PIN retry/lockout, multi-key `hidraw` races, recovery-token use, revocation, or the PIV 9c signing ceremony's display/confirmation — the 12 scenarios behind `B-REAL-FIDO2` (OMN-42 / OMN-63), none of which has a test today. **Never describe a green run of this lane as production confidence.**

## Cross-references

- **See also:** `docs/BLOCKERS.md` → "Not Current Blockers" → **B-VM-CTAP2 RESOLVED** (authoritative chain description) and → **B-REAL-FIDO2**; plus Permanent CI-Evidence Patterns.
- Runs **30139433902** (job 89629762908), 29872832727, 29525332901 (superseded ARM64 evidence).
- PRs **#125**, **#102**, **#144**, **#137**. Linear **OMN-48** (Done), OMN-42, OMN-63.
- `refs/luks-fido2-e2e-test-2026-07-23.md`, `refs/fido2-ci-emulator-status-2026-07-23.md`, `refs/bcvk-swtpm-ci-2026-07-23.md`, `refs/vm-e2e-run-29525332901.md`, `refs/yubikey-hw-validation-scenarios-2026-07-25.md` (the 12 scenarios), `refs/zboot-workaround-runner-qemu-audit-2026-07-25.md` (B-QEMU-ZBOOT workaround still required).
- ADRs: ADR-003, ADR-026, ADR-002.
- Playbooks: [hw-device-and-allow-real-u2f](hw-device-and-allow-real-u2f.md), [dispatch-chain-verification](dispatch-chain-verification.md).
