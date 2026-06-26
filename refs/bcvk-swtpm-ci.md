# bcvk swtpm CI — implementation spec

## Goal

Add `swtpm` (IBM software TPM 2.0) to bcvk ephemeral CI VMs and enable
`systemd-tpm2-swtpm.service` so CI satisfies `ConditionSecurity=measured-os`
and TPM2 code paths (PCR measurements, LUKS PCR binding) are covered without
physical hardware.

Ref: ADR-016 §Feature 1, issue #21, BLOCKER-006.

## BLOCKER-006: cross-repo dependency

Primary changes are in `yubi-OS/bcvk`. This branch tracks the yubiOS-side
CI integration drop-in. See cross-repo issue for bcvk implementation scope.

## yubiOS side (this branch)

### assets/ci/vm-swtpm.conf

Systemd drop-in placed at `/usr/lib/systemd/system/systemd-tpm2-swtpm.service.d/ci-vm-swtpm.conf`
in the bcvk test image. Conditions on `ConditionVirtualization=vm` so it
only activates inside ephemeral bcvk VMs, not on bare-metal deployments.

**Requires:** systemd >= 261 (`systemd-tpm2-swtpm.service` is a v261 addition).

## bcvk side (cross-repo — yubi-OS/bcvk issue)

1. Add `swtpm` and `swtpm-tools` to the bcvk test image package list.
2. Enable `systemd-tpm2-swtpm.service` in the VM systemd preset.
3. Add `--feature tpm2-swtpm` flag to `bcvk run` (or auto-detect from drop-in).
4. Verify `/dev/tpm0` appears inside the VM before running yubiOS tests.

## Done condition

- Drop-in committed to this branch (done).
- PR #34 open against main (done).
- bcvk cross-repo issue opened (done — see BLOCKER-006 note in ADR-016).
- Hardware gate: full E2E validation of ConditionSecurity=measured-os requires
  the bcvk changes to land; this branch is doc+drop-in only per BLOCKER-006.
