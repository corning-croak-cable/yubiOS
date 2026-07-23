> **Archived research snapshot** synced from the assistant knowledge base (`documents/github-yubios-KS9n5GAT/knowledge/`) on 2026-07-23. May predate current specs — treat `PINNED.md` and the dated `refs/*` notes as the live source of truth; this is background research context only.

---

# yubiOS CI — Analysis and Fixed Workflow
_Updated: 2026-05-10_

## Repo
`yubi-OS/yubiOS` — public, default branch `main`

## Open PRs / Issues
- **PR #12**: shellcheck + ci.yml fixes + rego policy — `fix/shellcheck-sc2034-sc2064-sc2027`
- **Issue #11**: shellcheck CI output that triggered PR #12

---

## Original ci.yml Issues (vs AGENTS.md)

| Issue | Detail | Fix |
|---|---|---|
| Floating action refs | `actions/checkout@v4`, `@v6` — not pinned | `@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2` |
| Disallowed action | `hadolint/hadolint-action@v3.1.0` — not in allowed-refs list | `apt-get install hadolint` (trixie package) |
| No pinned container | Bare `ubuntu-24.04` runner, no `dhi.io/debian-base` container | `container:` block with pinned image on all 3 jobs |
| Broken YAML structure | `hadolint` + `yarn install` steps indented inside `shellcheck` `run:` block — never executed | Extracted as proper sibling steps |
| Mixed checkout versions | `@v4` on lint, `@v6` on unit-tests and build | All → same pinned SHA |
| `runs-on: ubuntu-24.04` | AGENTS.md standard is `ubuntu-latest` | `runs-on: ubuntu-latest` |
| `podman build` in container | `podman` absent in `dhi.io/debian-base`; GHA forwards docker socket | `docker buildx build --policy ...` |

---

## AGENTS.md Rules Applied

```yaml
# Every job must use:
runs-on: ubuntu-latest
container:
  credentials:
    username: 0mniteck42
    password: ${{ secrets.DOCKER }}
  image: docker://dhi.io/debian-base@sha256:9415967aa0ed8adea8b5c048994259d1982026dca143d0303c7bbe0e11ed67d3

# Checkout must be:
uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2

# Allowed refs (complete list from AGENTS.md):
# - actions/attest@59d89421af93a897026c735860bf21b6eb4f7b26
# - actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd
# - actions/configure-pages@45bfe0192ca1faeb007ade9deae92b16b8254a0d
# - actions/deploy-pages@cd2ce8fcbc39b97be8ca5fce6e763baed58fa128
# - actions/upload-artifact@bbbca2ddaa5d8feaa63e36b76fdaad77386f024f
# - actions/upload-pages-artifact@fc324d3547104276b827a68afc52ff2a11cc49c9
# - 0mniteck/.pki/.github/*/*@*
# - docker://dhi.io/debian-base@sha256:9415967...
# - docker://ghcr.io/actions/jekyll-build-pages@sha256:6791ebfd...
```

---

## yubiOS.rego — Docker Build Policy

Pushed to branch at repo root. Applied via:
```bash
docker buildx build --policy reset=true,strict=true,filename=yubiOS.rego .
```

### Rules

| Rule | Condition | Behaviour |
|---|---|---|
| Local | `input.local` | Always allow (no FROM pull) |
| Approved + pinned | `approved_registry(ref)` AND `isCanonical` | Allow |
| Wrong registry | not in `quay.io/fedora/` or `dhi.io/` | Deny with message |
| Mutable tag | approved registry but `!isCanonical` (e.g. `:latest`) | Deny with pin instructions |
| Provenance | `hasProvenance` check — **commented out** | Enable once fedora-bootc ships SLSA attestations |

### Current Containerfile violation

```dockerfile
FROM quay.io/fedora/fedora-bootc:latest  # ← mutable tag — will fail the policy
```

Fix — pin the digest:
```bash
skopeo inspect --format '{{.Digest}}' docker://quay.io/fedora/fedora-bootc:latest
# → sha256:<hash>
```
Then update Containerfile:
```dockerfile
FROM quay.io/fedora/fedora-bootc@sha256:<hash>
```
This is a separate PR from #12 (policy file landed first, Containerfile pin after).

---

## Fixed ci.yml Pipeline

```
lint (pinned container, pinned checkout)
  └── shellcheck: find usr/lib/yubiOS -name '*.sh' | xargs shellcheck
  └── hadolint: apt-get install hadolint && hadolint --ignore DL3041 Containerfile

unit-tests (needs: lint)
  └── bats tests/unit/

build (needs: lint)
  └── docker buildx build --policy reset=true,strict=true,filename=yubiOS.rego -t yubiOS:ci .
  └── verify symlinks + scripts
  └── verify PAM wiring
```

---

## Files

| File | Location | Status |
|---|---|---|
| Fixed `ci.yml` | `session/ci-workflows/yubiOS-ci.yml` | Manual push needed (`workflow` scope) |
| `yubiOS.rego` | Pushed to `yubi-OS/yubiOS` branch | ✅ On `fix/shellcheck-sc2034-sc2064-sc2027` |

Push ci.yml:
```bash
# On branch fix/shellcheck-sc2034-sc2064-sc2027
cp yubiOS-ci.yml .github/workflows/ci.yml
git add .github/workflows/ci.yml
git commit -m "fix(ci): pin all action refs + container per AGENTS.md, fix broken YAML, add rego policy"
git push
```


---

## Publish target (added 2026-06-26)

The main CI (`yubiOS-ci.yml`) now publishes the OS image to **Docker Hub `0mniteck/yubios`** via a `merge-manifest` job that stitches the per-arch `build` outputs into a multi-arch OCI index.

- **Primary download:** `docker.io/0mniteck/yubios:latest` (amd64 + arm64).
- Per-build immutable tag `:<commit-sha>`; SLSA provenance + SBOM attestations attached.
- Current `:latest` = run #113 / commit `bfbc38f` = index `sha256:c965a816b9173cf6f227e6b5b09e321e841ab5f8a49075c112657a0a40b5e761` (amd64 `f0c1ed8f…`, arm64 `cca2fe05…`).
- Registry auth: username `0mniteck42`, `${{ secrets.DOCKER }}`.
- Build base (`FROM`) is `quay.io/fedora/fedora-bootc:45` (digest-pinned); CI runner container is `dhi.io/debian-base` — both distinct from the published image.