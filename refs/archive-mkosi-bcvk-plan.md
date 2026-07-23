> **Archived research snapshot** synced from the assistant knowledge base (`documents/github-yubios-KS9n5GAT/knowledge/`) on 2026-07-23. May predate current specs — treat `PINNED.md` and the dated `refs/*` notes as the live source of truth; this is background research context only.

---

# mkosi + bcvk Fork Planning
_Updated: 2026-05-10_

## Context

These two forks are **build + test infrastructure** for `yubiOS` — the FIDO2-first immutable OS
where a YubiKey replaces the TPM at every trust boundary.

| Fork | Upstream | Role in yubiOS |
|------|----------|----------------|
| `corning-croak-cable/mkosi` | `systemd/mkosi` | Build-time: constructs OCI images, UKI signing, dm-verity |
| `corning-croak-cable/bcvk` | `bootc-dev/bcvk` | Dev/test: runs yubiOS as ephemeral VM, hardware-in-the-loop testing |

The third fork in play is `bootc` (already has 2 open PRs for Surface x86/ARM64 support).

---

## mkosi fork

### What it is
Python tool that wraps `dnf`/`apt`/`pacman`/`zypper` to build bespoke OS images — disk images,
UKIs, sysexts, initrds. particleos uses it directly; yubiOS needs it for the image construction
pipeline before bootc takes over for day-2 upgrades.

### What yubiOS needs from this fork

#### 1. PIV/PKCS11 UKI signing
The yubiOS trust chain uses YubiKey PIV slot 9c (CCID) for Secure Boot signing. mkosi's current
`ukify` integration calls `sbsign` with a file-based key. We need a signing shim that routes
through `pkcs11-provider` or `yubico-piv-tool`.

**Target:** `mkosi/resources/man/mkosi.1.md` UKI signing section + new `finalize-scripts/50-sign-uki-piv.py`

#### 2. FIDO2 enrollment hook
After image construction, an optional enrollment script should set up the `systemd-cryptenroll
--fido2-device=auto` binding so the first boot prompts for YubiKey tap to seal the LUKS slot.

**Target:** `mkosi/finalize-scripts/60-enroll-fido2.sh`

#### 3. yubiOS mkosi.conf.d profile
A `mkosi.conf.d/yubiOS/` directory mirroring the pattern of `azure-centos-fedora/` that sets:
- `Bootloader=uki`
- `SecureBootKey=` pointing to PIV slot
- `Packages=` list: `pam-u2f`, `yubikey-manager`, `libfido2`, `opensc`
- `KernelCommandLine=` with `rd.luks.options=fido2-device=auto`

#### 4. CI workflow
`.github/workflows/yubiOS.yml` — builds a minimal yubiOS OCI image in CI without hardware
(software FIDO2 emulator via `uhid-fido` or similar), runs mypy + ruff on new scripts.

### Build/test commands (from AGENTS.md)
```
mypy mkosi tests kernel-install/*.install
ruff format mkosi tests kernel-install/*.install
ruff check --fix mkosi tests kernel-install/*.install
python3 -m pytest ...
```

### AI contribution rules (mkosi)
- Must disclose in commit messages: `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`
- All AI output requires thorough human review before submission
- PR review: check out in `worktrees/`, review locally, remove worktree when done

---

## bcvk fork

### What it is
Rust-based "bootc virtualization kit". Runs bootc containers as ephemeral QEMU VMs (no root),
creates disk images, libvirt integration for persistent VMs. Rust workspace, nextest, Justfile.

### Direction: native-first, QEMU as fallback

Current `bcvk to-disk` routes through an ephemeral QEMU VM (virtiofsd + SSH + virtio-blk). For
flashing yubiOS to real hardware (USB, NVMe, SD card) that overhead is purely in the way.

The native path is a privileged podman container directly calling `bootc install to-disk`:
```
podman run --privileged --pid=host --net=none \
  -v /sys:/sys:ro -v /dev:/dev \
  -v <storage>:<storage>:ro \
  containers-storage:yubiOS:latest \
  bootc install to-disk --generic-image /dev/sdX
```
No QEMU, no virtiofsd, no SSH. Faster. Works without KVM.

### What landed in PR #1

**`crates/kit/src/native_to_disk.rs`** — new module, `bcvk native-to-disk <image> <device>`:
- Block device validation (`fstat S_IFBLK`)
- `/proc/mounts` check — refuses if any partition on device is mounted
- Interactive confirmation: prints model + size via `blockdev --getsize64` + sysfs, requires "yes"
- `--yes` for CI/scripts; `--rootful` prepends `sudo` for rootless-constrained environments
- Container storage mounted read-only: avoids re-pulling
- Table-driven unit tests per REVIEW.md: mount check (4 cases), human_size (3), cmd construction

**`crates/kit/src/main.rs`** — `bcvk native-to-disk` CLI subcommand wired in

### Command decision matrix

| Use case | Command |
|---|---|
| Flash yubiOS to USB/NVMe (bare metal) | `bcvk native-to-disk` |
| Build a disk image file for cloud/VM import | `bcvk to-disk` |
| Dev testing in ephemeral QEMU VM | `bcvk ephemeral run` |

### Code quality rules (bcvk, from REVIEW.md)
- Table-driven unit tests (not one test per case)
- Split parsers from I/O — parsers accept `&str`, separate fn reads from disk
- Strict assertions, not just "didn't crash"
- AI attribution: `Assisted-by: Sauna (claude-sonnet-4-6)`
- No `Signed-off-by` on AI-generated commits — human must add after review
---

## Priority order

1. **bcvk: YubiKey USB passthrough** — blocks all hardware-in-the-loop testing
2. **mkosi: yubiOS mkosi.conf.d profile** — needed to build yubiOS images cleanly
3. **mkosi: PIV/PKCS11 UKI signing** — needed for real Secure Boot flow
4. **bcvk: Secure Boot test mode** — needed to verify signed UKI boots
5. **bcvk: FIDO2 enrollment workflow** — CI automation for enrollment testing
6. **mkosi: FIDO2 enrollment hook** — post-build enrollment script
7. **CI workflows** for both forks

---

## Relationship map

```
YubiKey (PIV slot 9c)
       │
       ▼ sbsign via PKCS11
  mkosi fork ──────────► OCI container image (yubiOS)
       │                         │
       │                         ▼ bootc install/upgrade
       │                   bare metal / VM disk
       │
       └─────► bcvk fork ──────► ephemeral VM (test)
                    │                  ▲
                    └── USB passthrough YubiKey hidraw
```

---

## Next steps (suggested)

- [ ] Branch `feature/yubikey-usb-passthrough` in bcvk fork
- [ ] Branch `feature/yubiOS-profile` in mkosi fork
- [ ] File tracking issues in yubiOS repo linking to both PRs
- [ ] Check if `uhid-fido` / software FIDO2 emulator is viable for CI (no hardware)
