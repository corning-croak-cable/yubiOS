> **Archived research snapshot** synced from the assistant knowledge base (`documents/github-yubios-KS9n5GAT/knowledge/`) on 2026-07-23. May predate current specs — treat `PINNED.md` and the dated `refs/*` notes as the live source of truth; this is background research context only.

---

# osbuild / Image Builder — On-Premises Overview

**Source**: https://osbuild.org/docs/on-premises/overview/  
**Researched**: 2026-05-11  
**Refresh**: Check osbuild.org quarterly; actively developed

---

## What it is

osbuild is a pipeline execution engine for building customized OS images. Image Builder wraps it with higher-level UX. Two main components:

- **osbuild-composer** — daemon-based service; manages blueprints, queues builds, Weldr/lorax-compatible API
- **image-builder-cli (ibcli)** — modern stateless tool; no daemon, no database; blueprints are local TOML files

osbuild itself is the low-level pipeline engine that both use under the hood.

---

## Supported distributions

- Fedora
- CentOS Stream
- RHEL (via Red Hat subscription)

Available in distro repos; COPR provides bleeding-edge snapshots.

---

## Image types

qcow2, raw, ami (AWS), vmdk, iso, oci, tar, wsl2, iot-commit (OSTree), iot-installer, edge-commit, minimal-raw, and more.

---

## image-builder-cli (preferred for yubiOS)

Stateless, tool-based. No background daemon. Blueprints passed directly as local `.toml` files.

```bash
# Install
dnf install image-builder
# or COPR for latest
dnf copr enable @osbuild/osbuild
dnf copr enable @osbuild/image-builder
dnf install image-builder

# Build a qcow2
image-builder build qcow2 \
  --distro fedora-43 \
  --blueprint blueprint.toml

# Run via container (no install needed)
sudo podman run --privileged \
  -v ./output:/output \
  ghcr.io/osbuild/image-builder-cli:latest \
  build --distro fedora-43 minimal-raw
```

Key flags:
- `--distro` — target distro (fedora-43, centos-stream-9, etc.)
- `--blueprint` — path to TOML blueprint
- `--extra-repo` — add a custom repo for packages
- `--bootc-defaultfs` — (v42+) set default filesystem for bootc images
- `--arch` — cross-arch (requires QEMU on host)

---

## Blueprint format (TOML)

```toml
name = "yubiOS-base"
description = "yubiOS base image"
version = "0.1.0"

[[packages]]
name = "yubikey-manager"

[[packages]]
name = "pcscd"

[[packages]]
name = "opensc"

[[customizations.user]]
name = "admin"
password = "$6$..."
groups = ["wheel"]
key = "ssh-ed25519 AAAA..."

[customizations.kernel]
append = "quiet"

[[customizations.filesystem]]
mountpoint = "/var"
minsize = "10 GiB"
```

Sections: `[[packages]]`, `[[groups]]`, `[customizations]`, `[[customizations.user]]`, `[[customizations.filesystem]]`, `[customizations.kernel]`, `[customizations.services]`, etc.

---

## osbuild-composer (legacy / service-based)

```bash
# Start service
systemctl enable --now osbuild-composer.socket

# Push blueprint
composer-cli blueprints push blueprint.toml

# Start compose
composer-cli compose start blueprint-name qcow2

# Check status
composer-cli compose status

# Download result (tarball with image + manifest + logs)
composer-cli compose results <UUID>
```

---

## OSTree / bootc integration

**Build OSTree commit:**
```bash
image-builder build iot-commit --blueprint blueprint.toml
```
Output: OSTree commit artifact. Deploy via Anaconda kickstart `ostreesetup`.

**bootc-image-builder** (separate project, also uses ibcli):
Build disk images (ISO, qcow2, raw) directly from bootc OCI images:
```bash
sudo podman run --privileged \
  -v ./output:/output \
  -v /var/lib/containers/storage:/var/lib/containers/storage \
  quay.io/centos-bootc/bootc-image-builder:latest \
  --type qcow2 \
  quay.io/yubi-os/yubios:latest
```

GitHub Action: `osbuild/bootc-image-builder-action` (TypeScript, 11 stars as of 2026-05)

---

## 2025-2026 developments

- **image-builder-cli v42** (Nov 2025): bootc/ostree docs + `--bootc-defaultfs` option
- **bootc-image-builder PR #1157**: replacing bib binary with ibcli (convergence)
- **composefs-native backend** planned for bootc: verified filesystem images from OCI
- **Fedora CoreOS** shifted to osbuild for boot image building
- **composefs signatures** for bootc commits merged into ostree

---

## yubiOS relevance

osbuild / bootc-image-builder is the path for building installable disk images from the yubiOS OCI container:
- `type=qcow2` → QEMU testing (pairs with bcvk)
- `type=raw` → bare metal flashing
- `type=iso` → installer ISO for end-user deployment
- Blueprint customizations can inject YubiKey packages, user keys, LUKS policies

---

## Fork

`yubi-OS/image-builder-cli` forked 2026-05-11 from `osbuild/image-builder-cli`. 125 files, Go + Python, MIT license.

---

## Source references
- https://osbuild.org/docs/on-premises/overview/
- https://github.com/osbuild/image-builder-cli
- https://github.com/osbuild/bootc-image-builder
- https://github.com/osbuild/bootc-image-builder-action
