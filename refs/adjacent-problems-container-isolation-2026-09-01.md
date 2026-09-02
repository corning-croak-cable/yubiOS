# Adjacent problems: container isolation on an immutable Linux host

Date: 2026-09-01. Axis: NSS 6/12 Adjacent problems. Origin: SOS Agent FIT #10 lens
`L4-NSS-Adjacent_problems`; one of five files filling the empty cell at z-band 0 /
phi-sector 3. Nearest neighbours: `yubiOS.rego`, `refs/systemd-upstream-progress-2026-07-21.md`.

## Lens

```
L4e -- container-isolation
  hypothesis:  yubiOS uses four isolation mechanisms (podman containers, systemd-nspawn,
               bcvk VMs, systemd unit sandboxing) without one document saying which
               boundary answers which threat and why the others were not used there
  method:      name the family, 4 alternatives, rejection criteria per use, flip conditions,
               boundary with the privilege family
  parameters:  {axis: adjacent_problems, total: 17/20}
  delta:       {adj_gaps_before: 5, adj_gaps_after: 1, dim_closed: 4, family_named: true,
                alternatives_count: 4}
  verdict:     YES
  score:       42
  caveat:      the nspawn-as-portable-service convention is stated in the skill, not yet
               exercised in a CI leg
```

## Focal problem

On a bootc host with a read-only `/usr`, "isolation" is asked four different ways: build a
container image (podman, rootless), run a hermetic dev environment off the signed image
(systemd-nspawn with `RootImage=`), test a whole OS (bcvk ephemeral VM), and confine a
service (unit sandboxing: `PrivateDevices=`, `RestrictNamespaces=`, `SystemCallFilter=` with
a seccomp allowlist). Each is a different boundary with a different cost.

## Problem family

Family: **isolation** (what can a process *see*). Boundary with **privilege minimisation**
(what can it *do*), documented in `refs/adjacent-problems-rootless-privilege-2026-09-01.md`.
Boundary with **integrity** (dm-verity, composefs): integrity protects the image from the
process; isolation protects the process from other processes.

## Alternative solutions and why not, per use

| Use | Chosen | Alternatives considered | Why not |
|---|---|---|---|
| Image build | rootless podman / buildx | rootful daemon; VM per stage | root handoff; minutes per stage |
| Dev environment | systemd-nspawn on the signed image | Docker dev container; toolbox | neither boots the actual image's systemd |
| OS test | bcvk ephemeral VM | nspawn `--boot`; bare metal | nspawn cannot exercise UEFI, LUKS2, FIDO2 unlock; bare metal is the final gate, not the loop |
| Service confinement | unit sandboxing + seccomp | run every service in a container | doubles the image and hides the unit from `systemd-analyze security` |

Relation types: containers vs. nspawn is *substitution*; nspawn vs. VM is *abstraction* (the
VM adds a kernel boundary); unit sandboxing vs. containers is *alternative* at the same
layer. Prior art: systemd-nspawn(1); Poettering "Fitting Everything Together" (2022);
bcvk README; seccomp(2) and the systemd `SystemCallFilter=` groups.

## Related problems

- **Verification chain**: a container is only as trustworthy as the digest the build policy
  admitted. Relation: *prerequisite*.
- **YubiKey boot in a VM**: USB passthrough of a real key into the bcvk VM is the isolation
  boundary letting the FIDO2 leg run at all. Relation: *intersection*.
- **Corpus curve**: isolation is one of the primitives most often absent from sparse cells
  in the yubiOS corpus, which is why this file exists. Relation: *the audit that named it*.
- **GPU passthrough** (`refs/bootc-uki-libvirt-gpu-passthrough-2026-08-07.md`) and **nested
  virtualisation on ARM** (`refs/kvm-arm-nested-virtualization-2026-08-07.md`). Relation:
  *extension* of the VM boundary.

## Flip conditions

Unit sandboxing would give way to per-service containers only if a service needed a
different `/usr` than the host image, which on an immutable host is the signal to ship a
sysext instead. nspawn would give way to VMs for dev if a workflow needed a different kernel.

## Curve placement

Coverage: verification chain (digest admission), rootless privilege and capabilities (the
boundary family), corpus/curve/sparse (this cell), YubiKey boot (the VM passthrough case),
container isolation and seccomp (focal). Omitted clusters omitted by design.
