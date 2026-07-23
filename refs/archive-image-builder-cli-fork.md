> **Archived research snapshot** synced from the assistant knowledge base (`documents/github-yubios-KS9n5GAT/knowledge/`) on 2026-07-23. May predate current specs — treat `PINNED.md` and the dated `refs/*` notes as the live source of truth; this is background research context only.

---

# yubi-OS/image-builder-cli — Fork Scope

**Forked from**: osbuild/image-builder-cli  
**Forked**: 2026-05-11T02:24:14Z (today)  
**URL**: https://github.com/yubi-OS/image-builder-cli  
**Description**: Building operating system artifacts (disk images, ISOs, etc.)  
**License**: Apache 2.0  
**Languages**: Go (55%), Python (41%), Makefile (2%), Dockerfile (1%), Shell (<1%)

---

## What it is

A modern, stateless CLI tool for building OS images (disk images, ISOs, containers) from blueprint TOML files. Replaces the service-based `osbuild-composer` / `composer-cli` stack. Used by `bootc-image-builder` as its internal build engine (PR #1157 merged it in).

---

## Key files

| File | Purpose |
|---|---|
| `README.md` | Usage: podman container run + dnf install instructions |
| `Containerfile` | OCI container image for ibcli |
| `Containerfile.bib` | bootc-image-builder specific container build |
| `go.mod` / `go.sum` | Go module deps |
| `Makefile` | Build targets |
| `HACKING.md` | Dev setup and contribution guide |
| `image-builder.spec` | RPM spec for `dnf install image-builder` |
| `Schutzfile` | Dependency pinning (osbuild-specific format) |
| `go-vendor-tools.toml` | Go vendor tooling config |
| `.packit.yaml` | Packit CI integration (COPR builds) |
| `.golangci.yml` | Go linting config |
| `setup.cfg` | Python package config (testing/tooling) |
| `.pre-commit-config.yaml` | Pre-commit hooks |
| `.spellcheck.yml` | Spell checking config |

Total: 125 files

---

## Run via container (quickstart)

```bash
sudo podman run --privileged \
  -v ./output:/output \
  ghcr.io/osbuild/image-builder-cli:latest \
  build \
  --distro fedora-43 \
  minimal-raw
```

---

## Install via COPR (dev snapshots)

```bash
dnf copr enable @osbuild/osbuild
dnf copr enable @osbuild/image-builder
dnf install image-builder
```

For RHEL:
```bash
dnf copr enable @osbuild/osbuild rhel-10-x86_64
```

---

## Why this fork matters for yubiOS

- `image-builder-cli` is the tool that turns yubiOS OCI images into bootable disk artifacts (qcow2, raw, ISO)
- It's also what `bootc-image-builder` uses internally now
- Forking gives the ability to add yubiOS-specific image types or customizations (e.g. a `yubios-disk` type that pre-enrolls FIDO2 during image generation)
- Short-term: probably just tracking upstream; long-term: potential customization entry point

---

## Next steps for this fork

1. Add upstream remote: `git remote add upstream https://github.com/osbuild/image-builder-cli`
2. Review `HACKING.md` for dev setup
3. Identify if any yubiOS-specific image type or FIDO2 pre-enrollment hook is worth upstreaming or maintaining as a patch
4. Consider adding `Containerfile.yubios` for a yubiOS-configured ibcli image

---

## Relationship to other forks

| Fork | Purpose |
|---|---|
| `yubi-OS/bootc` | Core bootc runtime fork |
| `yubi-OS/mkosi` | mkosi image builder |
| `yubi-OS/bcvk` | Ephemeral VM testing |
| `yubi-OS/image-builder-cli` | **This fork** — disk image builder |

`image-builder-cli` complements `bcvk`: bcvk is for ephemeral VM testing; ibcli produces the actual installable artifacts.

---

## Source references
- https://github.com/yubi-OS/image-builder-cli
- https://github.com/osbuild/image-builder-cli
- https://osbuild.org/docs/on-premises/overview/
