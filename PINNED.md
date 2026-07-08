# PINNED.md — yubiOS approved refs & digests

All GitHub Actions and container image references used across the yubi-OS org
must appear here before being added to any workflow or Containerfile.
Non-pinned refs (mutable tags, branch names) are not permitted.

**This file is the single source of truth.** AGENTS.md and every workflow refer
here; do not duplicate the digest list elsewhere.

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
| `dhi.io/debian-base` (multi-arch INDEX) | `sha256:1cefd55d979ddbd9110cf73cf3de11798a7893a4598050ba57624bc754b244aa` | **Canonical for workflows + Containerfile `FROM`.** OCI image *index* (manifest list) for `trixie-debian13-dev`; auto-resolves per runner arch. Use this for any multi-arch (amd64 + arm64) job. |
| ↳ child `linux/amd64` | `sha256:57c88d9180b30314a04650426af8d4301c5c9738e4c5672a1db99a03f6a54721` | resolved automatically; do not pin directly unless an amd64-only job is required |
| ↳ child `linux/arm64` | `sha256:1634f8387e3172f2b8bf32d93456c52425815191e6e53b858d06bc5a8ef75f47` | resolved automatically |
| `quay.io/fedora/fedora-bootc:45` (multi-arch INDEX) | `sha256:88f7ab696754cf257ced669479c3ce5d35222f3a123f745989239bf56dbf8d0a` | **Containerfile `FROM` base.** OCI image *index*; auto-resolves per arch. Re-resolved 2026-07-08 (prior digest 404d on quay). |
| `ghcr.io/actions/jekyll-build-pages` | `sha256:6791ebfd912185ed59bfb5fb102664fa872496b79f87ff8b9cfba292a7345041` | |
| `ghcr.io/hadolint/hadolint:v2.14.0-debian` | `sha256:158cd0184dcaa18bd8ec20b61f4c1cabdf8b32a592d062f57bdcb8e4c1d312e2` | |

> Superseded single-arch digests (no longer used in workflows; kept for audit only):
> `62bc0610151db7155b7225f1a03c299bf109ab0b884da6777d1f808c7834d4ea` (amd64-only manifest),
> `9415967aa0ed8adea8b5c048994259d1982026dca143d0303c7bbe0e11ed67d3` (older single-arch).
> `b7b34d8720b2e0ccaba980fd92347e7820051496ca0e639704172c6f3fb8877d` (prior quay fedora-bootc:45 index, rotated out of quay → 404).
> `8a1c786152eaf72346a339ae2b869f5f7445cd311700f932f8bc94433a0e7d1b` (2026-07-07 quay fedora-bootc:45 index, also rotated out → 404 as of 2026-07-08).
> Resolve the current index with the `fetch-dhi-manifest` workflow (it requests the OCI index media type).

---

## Policy

- All container image `FROM` statements in Containerfile and `uses:` in workflows must reference a SHA pinned here.
- For multi-arch (amd64 + arm64) jobs, reference the **INDEX** digest so it auto-resolves per runner architecture — never pin a single-arch child in a matrix job.
- Mutable tags (`:latest`, `:main`, branch refs) are rejected by `yubiOS.rego` and AGENTS.md policy.
- To add or roll a ref: obtain the digest (for the base image, run `fetch-dhi-manifest`), update a row here, update `yubiOS.rego` if a new registry is introduced, open a PR.
- Digests are verified at build time via Docker Build Policy (`--policy reset=true,strict=true`).
