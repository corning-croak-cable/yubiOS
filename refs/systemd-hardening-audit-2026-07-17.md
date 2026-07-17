# systemd hardening audit: 2026-07-17

Status: static audit complete; target-image runtime validation still required.

## Scope

Audited repo-owned yubiOS services found by source search:

- `usr/lib/systemd/system/yubiOS-enroll.service`
- `usr/lib/systemd/system/yubiOS-chipsec-firstboot.service`

The audit covers `ConditionSecurity=measured-os`, `RestrictFileSystems=`, and the newer v261 `RestrictFileSystemAccess=` distinction.

## Findings

| Unit | Finding | Status |
|---|---|---|
| `yubiOS-enroll.service` | Has `ConditionFirstBoot=yes`, `ConditionPathExists=!/var/lib/yubiOS/.enrolled`, and `ConditionSecurity=measured-os` in `[Unit]`. | Correct for first-boot enrollment gating. |
| `yubiOS-enroll.service` | Uses `RestrictFileSystems=~@network`, the deny-list form that blocks network filesystems without allow-listing away local filesystems needed for boot/enrollment. | Correct static shape. |
| `yubiOS-chipsec-firstboot.service` | Has `ConditionSecurity=measured-os`, `ConditionFirstBoot=yes`, and `Before=yubiOS-enroll.service`. | Correct for the first-boot firmware validation exception. |
| `yubiOS-chipsec-firstboot.service` | Intentionally omits `RestrictFileSystems=` and carries raw hardware capabilities for CHIPSEC. | Acceptable documented exception; keep one-shot/offline/narrow write paths. |
| Repo-wide | No repo-owned service currently uses `RestrictFileSystemAccess=`. | Do not add until target systemd and verity-backed execution assumptions are tested. |

## Existing tests

- `tests/unit/test-enroll-unit.bats` checks measured-boot gating, `[Unit]` placement, `RestrictFileSystems=~@network`, and `systemd-analyze verify` with staged Exec stubs.
- `tests/unit/test-chipsec-firstboot-unit.bats` checks measured/first boot gates, one-shot behavior, private network, narrow write paths, explicit capability exception, wrapper result semantics, and `systemd-analyze verify`.

## Remaining evidence gate

Run the Bats tests and `systemd-analyze verify` inside the target image/base after the next non-main-CI-safe opportunity. This pass did not boot the image or run main CI, so it closes the static TODO but not runtime evidence.

## Rule for future hardening

Keep `RestrictFileSystems=` and `RestrictFileSystemAccess=` separate:

- `RestrictFileSystems=` limits filesystem types and is already used for enrollment.
- `RestrictFileSystemAccess=` is a newer v261 control for verified filesystem access semantics and needs a separate design/test pass before use.