---
name: docker-setup-buildx-action
description: 'Set up Docker Buildx (BuildKit) in GitHub Actions for multi-platform builds, cache export/import, SLSA attestations, and advanced build features. Use before docker/build-push-action when needing cache, attestations, or multi-platform. Triggers on: Docker Buildx, BuildKit, setup-buildx, multi-platform build, cache export, build attestations.'
---

# docker/setup-buildx-action

## When to use
Required before `docker/build-push-action` when using: cache export/import, SLSA provenance/SBOM attestations, multi-platform builds, or custom buildkitd config.

## Action reference
```yaml
- uses: docker/setup-buildx-action@v3
  with:
    version: latest          # pin for reproducibility
    driver: docker-container # default; needed for cache/attestations
```

## Minimal usage (most workflows)
```yaml
- name: Set up Buildx
  uses: docker/setup-buildx-action@v3
```

## With buildkitd config (registry mirrors)
```yaml
- uses: docker/setup-buildx-action@v3
  with:
    buildkitd-config-inline: |
      [registry."quay.io"]
        mirrors = ["mirror.example.com"]
```

## With network host (for accessing local services during build)
```yaml
- uses: docker/setup-buildx-action@v3
  with:
    driver-opts: network=host
```

## Notes
- The `docker-container` driver runs BuildKit in a container; required for cache/attestations
- Use `docker` driver only for simple single-platform builds without extra features
- Pin action SHA for AGENTS.md-compliant workflows; `@v3` acceptable for dev
- For yubiOS CI: always include before building bootc images with attestations

## Driver comparison
| Driver | Cache export | Attestations | Multi-platform |
|---|---|---|---|
| `docker-container` (default) | Yes | Yes | Yes |
| `docker` | No | No | No |
| `kubernetes` | Yes | Yes | Yes |

## Source
https://github.com/docker/setup-buildx-action
https://docs.docker.com/build/ci/github-actions/configure-builder/
