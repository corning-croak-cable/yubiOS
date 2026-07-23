> **Archived research snapshot** synced from the assistant knowledge base (`documents/github-yubios-KS9n5GAT/knowledge/`) on 2026-07-23. May predate current specs — treat `PINNED.md` and the dated `refs/*` notes as the live source of truth; this is background research context only.

---

# Upstream bootc Base Image Repos

**Scoped**: 2026-05-11

---

## gitlab.com/fedora/bootc/base-images

**Project ID**: 57266724  
**Purpose**: Build and maintain Fedora bootc base images via `rpm-ostree compose image`  
**Language**: Shell, YAML, Just (task runner)  
**CI**: GitLab CI (Tekton + Konflux for official builds; local `just` for dev)

### Key files
| File | Purpose |
|---|---|
| `Containerfile` | Multi-stage OCI build (includes `chunked` build target via chunkah) |
| `Justfile` | Task runner: `just build`, `just build-minimal`, `FEDORA_VERSION=43 just build` |
| `bootc-base-imagectl` | Shell script: rechunk, build OCI base images from rpm-ostree commits |
| `bootc-base-imagectl.md` | Documentation for `bootc-base-imagectl` |
| `fedora-{N}.yaml` | Per-version treefile stubs (with repo overrides for Pungi path) |
| `standard.yaml`, `minimal.yaml`, `minimal-plus.yaml` | Image tier manifest definitions |
| `iot.yaml`, `fedora-iot.yaml` | IoT variant |
| `fedora-includes/` | Shared include fragments |
| `minimal/`, `standard/`, `minimal-plus/`, `iot/` | Per-tier Containerfile and manifest dirs |
| `.tekton/` | Konflux CI pipeline definitions (official Red Hat build system) |
| `ci/` | Shellcheck, whitespace, format validation |
| `CONTRIBUTING.md` | Full dev workflow: prereqs, env vars, examples |
| `RELEASE.md` | Release process for adding/removing Fedora versions |
| `renovate.json` | Automated dependency bumps (Renovate bot) |

### Branches
- `main` — default, tracks rawhide/current
- `f40`, `f41` — historical stable versions
- `renovate/fedora-{N}/...` — automated dependency bump PRs
- `konflux-fedora-bootc-{N}-{tier}` — Konflux CI branches per version+tier
- `appstudio-fedora-bootc-{N}-{tier}` — AppStudio (older Konflux) branches

### Tags
- `v2025.1`, `v2024.1`, `2024.1`, `v2024.0`

### Published images
- `quay.io/fedora/fedora-bootc:42` (standard, current stable)
- `quay.io/fedora/fedora-bootc:43`, `:44`, `:rawhide`
- Dev builds: `quay.io/bootc-devel/fedora-bootc-{version}-{tier}`

### Notable recent changes
- Added `chunked` build target (chunkah for content-based layer splitting)
- Added `clevis-dracut` and `clevis-pin-tpm2` to minimal/standard (2 days ago)
- Shellcheck + whitespace CI added (~10 months ago)

---

## gitlab.com/redhat/centos-stream/containers/bootc

**Project ID**: 57946995  
**Purpose**: CentOS Stream bootc base images (upstream for RHEL Image Mode)  
**Created**: 2024-05-16  
**Branches**: `main` (redirect shell), `c9s`, `c10s`, `add-konflux-rechunking`, `el9.4-backports`, several Konflux automation branches

### Structure
- `main` branch: minimal redirect shell. Contains only a git submodule pointer to `fedora/bootc/base-images`, a `.gitmodules` file, and `README.md` (tells users to look at `c9s`/`c10s`). No actual image definitions here.
- `c9s` branch: CentOS Stream 9 image definitions
- `c10s` branch: CentOS Stream 10 image definitions (in development)

### Published images
- `quay.io/centos-bootc/centos-bootc:stream9`
- `quay.io/centos-bootc/centos-bootc:stream10` (in development)

### Relationship to Fedora
The `main` branch includes `fedora/bootc/base-images` as a git submodule. CentOS builds extend / adapt the Fedora image process. The RHEL Image Mode product is downstream of CentOS Stream 9/10.

### Maintainers
Red Hat; primary recent committer: Wei Shi (wshi@redhat.com)

---

## yubiOS implications

- yubiOS currently derives from `quay.io/fedora/fedora-bootc` (Fedora standard tier)
- When tracking stability or RHEL compatibility, monitor `c9s` branch of CentOS repo
- The `minimal-plus` tier is what Fedora IoT and CoreOS share; if yubiOS wants an IoT-adjacent image, that's the right upstream base
- `clevis-dracut` + `clevis-pin-tpm2` additions (2 days ago) are interesting: clevis handles LUKS unlocking. yubiOS replaces this with YubiKey FIDO2 unlock — be aware of potential conflicts if upstream includes clevis in the boot chain.

---

## Source references
- https://gitlab.com/fedora/bootc/base-images
- https://gitlab.com/redhat/centos-stream/containers/bootc
- https://fedora.gitlab.io/bootc/docs/bootc/base-images/
