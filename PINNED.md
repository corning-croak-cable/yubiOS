# PINNED.md — yubiOS approved refs & digests

All GitHub Actions and container image references used across the yubi-OS org
must appear here before being added to any workflow or Containerfile.
Non-pinned refs (mutable tags, branch names) are not permitted.

---

## GitHub Actions

| Action | Pinned SHA |
|--------|------------|
| `0mniteck/.pki` | `*` (org-internal workflows only, ref matches `.github/*/*@*`) |
| `actions/attest` | `59d89421af93a897026c735860bf21b6eb4f7b26` |
| `actions/checkout` | `9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0` |
| `actions/configure-pages` | `45bfe0192ca1faeb007ade9deae92b16b8254a0d` |
| `actions/deploy-pages` | `cd2ce8fcbc39b97be8ca5fce6e763baed58fa128` |
| `actions/upload-artifact` | `bbbca2ddaa5d8feaa63e36b76fdaad77386f024f` |
| `actions/upload-pages-artifact` | `fc324d3547104276b827a68afc52ff2a11cc49c9` |
| `docker/setup-buildx-action` | `d7f5e7f509e45cec5c76c4d5afdd7de93d0b3df5` |

## Container Images

| Image | Pinned Digest |
|-------|---------------|
| `dhi.io/debian-base` | `sha256:62bc0610151db7155b7225f1a03c299bf109ab0b884da6777d1f808c7834d4ea` |
| `ghcr.io/actions/jekyll-build-pages` | `sha256:6791ebfd912185ed59bfb5fb102664fa872496b79f87ff8b9cfba292a7345041` |
| `ghcr.io/hadolint/hadolint:v2.14.0-debian` | `sha256:158cd0184dcaa18bd8ec20b61f4c1cabdf8b32a592d062f57bdcb8e4c1d312e2` |

---

## Policy

- All container image `FROM` statements in Containerfile and `uses:` in workflows must reference a SHA pinned here.
- Mutable tags (`:latest`, `:main`, branch refs) are rejected by `yubiOS.rego` and AGENTS.md policy.
- To add a new ref: obtain the digest, add a row here, update `yubiOS.rego` if a new registry is introduced, open a PR.
- Digests are verified at build time via Docker Build Policy (`--policy reset=true,strict=true`).
