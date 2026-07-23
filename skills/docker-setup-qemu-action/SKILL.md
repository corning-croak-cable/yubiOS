---
name: docker-setup-qemu-action
description: 'Register QEMU emulators for cross-platform Docker builds in GitHub Actions. Use when building linux/arm64 or other non-native architectures on standard amd64 runners. Triggers on: QEMU, cross-platform build, multi-architecture, linux/arm64, linux/arm.'
---

# docker/setup-qemu-action

## When to use
Enable cross-platform builds (e.g., build `linux/arm64` on an `amd64` runner). Required when `docker/build-push-action` targets platforms beyond the runner's native architecture.

## Action reference
```yaml
- uses: docker/setup-qemu-action@v3
  with:
    platforms: arm64,arm    # which platforms to emulate; 'all' for everything
```

## Standard multi-platform setup (correct order)
```yaml
- name: Set up QEMU
  uses: docker/setup-qemu-action@v3

- name: Set up Buildx
  uses: docker/setup-buildx-action@v3

- name: Login
  uses: docker/login-action@v3
  with:
    registry: quay.io
    username: ${{ secrets.QUAY_USERNAME }}
    password: ${{ secrets.QUAY_TOKEN }}

- name: Build and push
  uses: docker/build-push-action@v6
  with:
    platforms: linux/amd64,linux/arm64
    push: true
    tags: quay.io/yubi-os/yubios:latest
```

## Order matters
1. `setup-qemu-action` — register QEMU interpreters
2. `setup-buildx-action` — configure BuildKit
3. `login-action` — authenticate
4. `build-push-action` — build

## yubiOS note
yubiOS targets `linux/amd64` primarily. Include QEMU only when building multi-arch yubiOS bootc images. For single-arch CI unit tests, QEMU is not needed.

## Notes
- QEMU emulation is significantly slower (~5-10x) than native; use native runners when CI time matters
- `platforms: all` installs many interpreters; only list what you need
- Not needed when using `matrix` strategy with platform-specific self-hosted runners

## Source
https://github.com/docker/setup-qemu-action
https://docs.docker.com/build/ci/github-actions/multi-platform/
