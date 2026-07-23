---
name: docker-login-action
description: "Authenticate to a container registry (Docker Hub, GHCR, quay.io, dhi.io, etc.) using docker/login-action in GitHub Actions. Use when a workflow needs to push images to any registry before building or pushing. Triggers on: docker login, registry auth, ghcr.io, quay.io login, GITHUB_TOKEN registry."
---

# docker/login-action

## When to use
Authenticate to a container registry before pushing images. Place at the start of any job that pushes to a registry. Supports Docker Hub, GHCR, quay.io, dhi.io, and any OCI-compatible registry.

## Action reference
```yaml
- uses: docker/login-action@v3
  with:
    registry: ghcr.io          # omit for Docker Hub
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

## Supported registries
| Registry | `registry` value | Credential |
|---|---|---|
| Docker Hub | (omit) | `DOCKERHUB_TOKEN` secret |
| GHCR | `ghcr.io` | `GITHUB_TOKEN` (auto, `packages: write`) |
| quay.io | `quay.io` | quay robot account token |
| dhi.io | `dhi.io` | dhi.io credentials |
| Any OCI | hostname | username + password |

## yubiOS pattern (quay.io + GHCR)
```yaml
- uses: docker/login-action@v3
  with:
    registry: quay.io
    username: ${{ secrets.QUAY_USERNAME }}
    password: ${{ secrets.QUAY_TOKEN }}

- uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

## Permissions required
```yaml
permissions:
  packages: write   # for GHCR
  contents: read
```

## Notes
- Must precede any `docker/build-push-action` step that pushes
- Login persists for the job; no explicit logout needed
- For GHCR, `GITHUB_TOKEN` is automatically available; no extra secret needed

## Source
https://github.com/docker/login-action
https://docs.docker.com/build/ci/github-actions/
