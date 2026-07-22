# PINNED.md - yubiOS approved refs & digests

_Last reviewed: 2026-07-22 during the reproducible-build substrate audit._

All GitHub Actions, external GitHub source refs, container image references, and directly downloaded workflow artifacts used across the yubi-OS org must appear here before being added to any workflow or Containerfile. Non-pinned refs such as mutable tags and branch names are not permitted.

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

## Direct Workflow Downloads

Every `wcurl` payload is verified with GNU `sha512sum --check --strict` before it is extracted, installed, or executed.

| Artifact URL | Platform | Pinned SHA-512 |
|--------------|----------|----------------|
| `https://download.docker.com/linux/static/stable/x86_64/docker-29.6.0.tgz` | `linux/amd64` | `42401384ef853dab0a1986a7990420e77d3ee2bc39e178f8817d27ba6c4403998b7aacf3c28c7172135cdeec281cd328a8f2af949b5f57db44a211a093cfd20b` |
| `https://download.docker.com/linux/static/stable/x86_64/docker-rootless-extras-29.6.0.tgz` | `linux/amd64` | `184b583a0f325bef12feaf1ca175ff5ea4a65a168f2136eb1daf9c2ae646eecf02134ed65766c8800bd8eb03ac4d338d1e5d700248bc33632027b5b0b52de48a` |
| `https://github.com/docker/buildx/releases/download/v0.35.0/buildx-v0.35.0.linux-amd64` | `linux/amd64` | `710f4f48a101af939c4a4cace5ca93ab8c1a1a9ae244a4ef73b2a900f228614472b635bd202fae383c851686d383a37cdeddf45e6d54b36cae8458826c272262` |
| `https://download.docker.com/linux/static/stable/aarch64/docker-29.6.0.tgz` | `linux/arm64` | `04713ac54030bed8b2c096280d034b02f5430ed73ba8bcc4a686f7bbbf4a3444eb027847e896cd9ee91c3237dbe1c25a4cfca43d1dcd922a1a10009c960ace0b` |
| `https://download.docker.com/linux/static/stable/aarch64/docker-rootless-extras-29.6.0.tgz` | `linux/arm64` | `37649acdaacc597c115d2f19b71a4729a0119c6debbba4b4af18da2fd497ac28f5691df13137b7fc59903551ab0e08868f4b976a9a5704e2b7958b3b5b0cc0af` |
| `https://github.com/docker/buildx/releases/download/v0.35.0/buildx-v0.35.0.linux-arm64` | `linux/arm64` | `6dc0d4ed11a7bbd8148dab8897594d7050e7f3bc43e6d130e629aa443e50266e77beed8816737e5dc34b7d43617e7a4eef8121561042ef9a87479aea14383058` |

## External GitHub Source Refs

Workflows use the immutable commit in the third column. Branches and tags are retained only as provenance labels for maintainers.

| Repository | Reviewed branch/tag | Pinned commit | Workflow role |
|------------|---------------------|---------------|---------------|
| `docker/buildx` | `v0.35.0` | `a319e5b15052cf6557ceb666eb8ff6e32380b782` | Buildx release assets; payloads are additionally pinned by SHA-512 above. |
| `Mbed-TLS/mbedtls` | `mbedtls-3.6.6` | `0bebf8b8c7f07abe3571ded48a11aa907a1ffb20` | TF-A trusted-board-boot dependency. |
| `pando85/passless` | `v0.11.2` | `b67ccdf22e18cf21bcd140e03d22af413342d605` | TEST-image in-guest CTAP2 authenticator; yubiOS enables soft-fido2's implemented `hmac-secret` extension at build time. |
| `qemu/qemu` | upstream commit | `3a18e8a25992d1643707e2cebdd6e9bb2bd7d3b9` | ARM64 zstd-capable DirectBoot QEMU. |
| `yubi-OS/arm-trusted-firmware` | `feat/ci` | `f9e106415eb569ff9b19404e2c3f64167af08d21` | TF-A fork CI and firmware assembly. |
| `yubi-OS/bcvk` | `feat/ci` | `6fe199c7304782f2bc01063c7f28075e402c5538` | bcvk fork validation. |
| `yubi-OS/bcvk` | `feat/swtpm-ci` | `c29246b1a1ea0114fcb92530298a364627f0cae0` | VM end-to-end test harness. |
| `yubi-OS/edk2` | `feat/ci` | `9f13e2a137c97a2825f874b4321c3963ca87c747` | EDK2 fork CI and StandaloneMM firmware build. |
| `yubi-OS/edk2-platforms` | firmware integration commit | `4e1e7a4e64470ef7eefeaa1021c86763ab28beee` | StandaloneMM platform build. |
| `yubi-OS/mkosi` | `feature/yubiOS-profile` | `b2b1ea6ad59621a6f955e4cbceee72580a91889a` | mkosi fork CI, production summary, and installer build. |
| `yubi-OS/ms-tpm-20-ref` | `feat/ci` | `db43de77e3951482e732b9dbd9cee92f29df1007` | TPM reference fork validation. |
| `yubi-OS/ms-tpm-20-ref` | firmware integration commit | `98b60a44aba79b15fcce1c0d1e46cf5918400f6a` | fTPM and firmware builds. |
| `yubi-OS/optee_ftpm` | `feat/ci` | `28abbe7f33a96302cccf07b86b9ea46cf3dc278f` | fTPM fork validation. |
| `yubi-OS/optee_ftpm` | `feat/volatile-nv-ci` | `5e09cdbe1bcb1bc3bcf4875ebafb4e1a1154417c` | Firmware fTPM TA build. |
| `yubi-OS/optee_os` | `feat/ci` | `cc1847276821220facbffec13812c1888b44e6cb` | OP-TEE fork validation. |
| `yubi-OS/optee_os` | `master` | `a8ac329662c021d4df9415dd54001ca6283cb53e` | OP-TEE TA dev-kit dependency for fTPM fork validation. |
| `yubi-OS/optee_os` | `feat/stmm-volatile-storage-ci` | `440b10c3f9b1c8501f2550e282ae071bb5424972` | Firmware BL32 build. |
| `yubi-OS/u-boot` | `feat/ci` | `ef2ab32418943c161d0889af24375a52b14e10f9` | U-Boot fork CI and firmware BL33 build. |

Dynamic refs such as `github.sha`, `github.ref_name`, `target_ref`, and `ci_chain_ref` select commits within `yubi-OS/yubiOS` for the triggering run and the internal workflow chain. They are runtime identities, not external dependency refs; the default `actions/checkout` behavior checks out the triggering commit.

## Container Images

| Image | Pinned Digest | Notes |
|-------|---------------|-------|
| `docker.io/moby/buildkit:v0.31.2` (multi-arch INDEX) | `sha256:2f5adac4ecd194d9f8c10b7b5d7bceb5186853db1b26e5abd3a657af0b7e26ec` | BuildKit daemon used by every `docker-container` Buildx builder. Buildx 0.35.0 is only the client and does not pin this daemon implicitly. |
| `dhi.io/debian-base` (multi-arch INDEX) | `sha256:5c45913e72c90581fc4cca57c3a7cd7dcac2d9fa44fce24fe4cfa342e5ccb7a6` | **Canonical for workflows + Containerfile `FROM` where DHI is used.** OCI image index for `trixie-debian13-dev`; auto-resolves per runner arch. |
| child `linux/amd64` | `sha256:d33cf549d45223143a9c10670403cd52f422518b9f7b934b2b2abf4d73653399` | Resolved automatically; do not pin directly unless an amd64-only job requires it. |
| child `linux/arm64` | `sha256:beac2c1f3d82cf1ae889f2a6ffdbc21eba293e5fa690a2615b9716d8beb7d4a0` | Resolved automatically. |
| `quay.io/fedora/fedora-bootc:45` (multi-arch INDEX) | `sha256:9153b0fc9db4c7008c1c33d0795a2666a8eb43bb6fc407f9a21ed0d28a6dc2db` | **Containerfile `FROM` base.** OCI image index; auto-resolves per arch. Re-resolved 2026-07-22. Refresh with `fetch-fedora-bootc-manifest`. |
| `ghcr.io/actions/jekyll-build-pages` | `sha256:6791ebfd912185ed59bfb5fb102664fa872496b79f87ff8b9cfba292a7345041` | Pages build image. |
| `ghcr.io/hadolint/hadolint:v2.14.0-debian` | `sha256:158cd0184dcaa18bd8ec20b61f4c1cabdf8b32a592d062f57bdcb8e4c1d312e2` | Hadolint image. |

> Superseded single-arch or rotated digests kept for audit only:
> `62bc0610151db7155b7225f1a03c299bf109ab0b884da6777d1f808c7834d4ea`,
> `9415967aa0ed8adea8b5c048994259d1982026dca143d0303c7bbe0e11ed67d3`,
> `b7b34d8720b2e0ccaba980fd92347e7820051496ca0e639704172c6f3fb8877d`,
> `8a1c786152eaf72346a339ae2b869f5f7445cd311700f932f8bc94433a0e7d1b`.

---

## Policy

- All container image `FROM` statements in Containerfiles, `uses:` entries, external GitHub source refs, and direct workflow downloads must reference an identity pinned here.
- Every `wcurl` request must be followed by a matching `sha512sum --check --strict` verification before the payload is consumed.
- Versioned GitHub release URLs may retain their tag-shaped path only when the downloaded bytes are independently pinned and checked by SHA-512.
- For multi-arch jobs, reference the OCI index digest so it auto-resolves per runner architecture; do not pin a single-arch child in a matrix job.
- Mutable tags such as `:latest`, `:main`, or branch refs are rejected by `yubiOS.rego` and AGENTS.md policy.
- To add or roll a ref: obtain the digest, update this file, update repo references to the old digest, update `yubiOS.rego` if a new registry is introduced, and open a PR.
- Use `fetch-dhi-manifest` for `dhi.io/debian-base` and `fetch-fedora-bootc-manifest` for `quay.io/fedora/fedora-bootc:45`.
- Digests are verified at build time by the explicit `yubiOS.rego` `target.policy` inherited from `yubiOS-bake.hcl` (`reset=true`, `strict=true`).
