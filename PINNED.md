# PINNED.md - yubiOS approved refs & digests

_Last reviewed: 2026-07-11 during the docs/research planning cycle._

All GitHub Actions and container image references used across the yubi-OS org must appear here before being added to any workflow or Containerfile. Non-pinned refs such as mutable tags and branch names are not permitted.

**This file is the single source of truth.** AGENTS.md, ADRs, research notes, and workflows may point here, but they should not duplicate the live digest list.

---

## GitHub Actions

| Action | Pinned SHA |
|--------|------------|
| `0mniteck/.pki` | `*` (org-internal workflows only, ref matches `.github/*/*@*`) |
| `actions/attest` | `59d89421af93a897026c735860bf21b6eb4f7b26` |
| `actions/checkout` | `9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0` |
| `actions/configure-pages` | `45bfe0192ca1faeb007ade9deae92b16b8254a0d` |
| `actions/deploy-pages` | `cd2ce8fcbc39b97be8ca5fce6e763baed58fa128` |
| `actions/download-artifact` | `37930b1c2abaa49bbe596cd826c3c89aef350131` |
| `actions/upload-artifact` | `bbbca2ddaa5d8feaa63e36b76fdaad77386f024f` |
| `actions/upload-pages-artifact` | `fc324d3547104276b827a68afc52ff2a11cc49c9` |
| `docker/setup-buildx-action` | `d7f5e7f509e45cec5c76c4d5afdd7de93d0b3df5` |

## Container Images

| Image | Pinned Digest | Notes |
|-------|---------------|-------|
| `dhi.io/debian-base` (multi-arch INDEX) | `sha256:712ec3f1c4627b16cdaec6bff3750bcbd84eb9082f2c9f6cd382bc1101abcde0` | **Canonical for workflows + Containerfile `FROM` where DHI is used.** OCI image index for `trixie-debian13-dev`; auto-resolves per runner arch. |
| child `linux/amd64` | `sha256:703d3c166dcf1172ececbd93102a4e16d06542c1098f5430165a328ade9a3541` | Resolved automatically; do not pin directly unless an amd64-only job requires it. |
| child `linux/arm64` | `sha256:0ba4a742c7dbafb91fdf5bc331dbce5dbaa65da1f20ad0f65a17448421e7a7c8` | Resolved automatically. |
| `quay.io/fedora/fedora-bootc:45` (multi-arch INDEX) | `sha256:b2a65b9835493fa0103cdb6f8f96c56a6af98efed321a7bd934986c2adf7a864` | **Containerfile `FROM` base.** OCI image index; auto-resolves per arch. Re-resolved 2026-07-14. Refresh with `fetch-fedora-bootc-manifest`. |
| `ghcr.io/actions/jekyll-build-pages` | `sha256:6791ebfd912185ed59bfb5fb102664fa872496b79f87ff8b9cfba292a7345041` | Pages build image. |
| `ghcr.io/hadolint/hadolint:v2.14.0-debian` | `sha256:158cd0184dcaa18bd8ec20b61f4c1cabdf8b32a592d062f57bdcb8e4c1d312e2` | Hadolint image. |

> Superseded single-arch or rotated digests kept for audit only:
> `62bc0610151db7155b7225f1a03c299bf109ab0b884da6777d1f808c7834d4ea`,
> `9415967aa0ed8adea8b5c048994259d1982026dca143d0303c7bbe0e11ed67d3`,
> `b7b34d8720b2e0ccaba980fd92347e7820051496ca0e639704172c6f3fb8877d`,
> `8a1c786152eaf72346a339ae2b869f5f7445cd311700f932f8bc94433a0e7d1b`.

---

## Policy

- All container image `FROM` statements in Containerfile and `uses:` entries in workflows must reference a SHA pinned here.
- For multi-arch jobs, reference the OCI index digest so it auto-resolves per runner architecture; do not pin a single-arch child in a matrix job.
- Mutable tags such as `:latest`, `:main`, or branch refs are rejected by `yubiOS.rego` and AGENTS.md policy.
- To add or roll a ref: obtain the digest, update this file, update repo references to the old digest, update `yubiOS.rego` if a new registry is introduced, and open a PR.
- Use `fetch-dhi-manifest` for `dhi.io/debian-base` and `fetch-fedora-bootc-manifest` for `quay.io/fedora/fedora-bootc:45`.
- Digests are verified at build time via Docker Build Policy (`--policy reset=true,strict=true`).
