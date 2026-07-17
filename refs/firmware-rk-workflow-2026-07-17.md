# RK firmware workflow split: 2026-07-17

Status: workflow/docs prepared; CI run intentionally not polled in this pass.

## Change

Add `.github/workflows/ci_firmware-rk.yml` as the orchestrated firmware lane and remove the top-level `ci.yml` path that dispatched `ci_test-int.yml` for the `yubiOS firmware` state.

The new callback state is the workflow name:

```text
yubiOS RK firmware
```

## Publish contract

When `Docker_push=true`, the workflow publishes the original firmware tags plus board-scoped variants under the existing Docker Hub namespace:

- `0mniteck/yubios:firmware`
- `0mniteck/yubios:firmware-<sha>`
- `0mniteck/yubios:firmware-qemu-arm64`
- `0mniteck/yubios:firmware-qemu-arm64-<sha>`
- `0mniteck/yubios:firmware-rock5b-rk3588`
- `0mniteck/yubios:firmware-rock5b-rk3588-<sha>`
- `0mniteck/yubios:firmware-rockpro64-rk3399`
- `0mniteck/yubios:firmware-rockpro64-rk3399-<sha>`

The current board variants carry board metadata and manifest warnings while the payload remains QEMU-validated CI firmware. Real hardware lanes must replace those placeholders when RK3399/RK3588 payloads diverge.

## Callback chain

`ci.yml` dispatches `ci_firmware-rk.yml` after `fetch-fedora-bootc-manifest` when `ci_fork_run=false`, and after `ci_fork_edk2` when the optional fork chain is enabled. On callback state `yubiOS RK firmware`, `ci.yml` continues to `yubiOS-ci.yml`.

## Static validation

The workflow YAML was parsed locally before commit. No main CI, QEMU, Docker push, or hardware validation was run in this pass.