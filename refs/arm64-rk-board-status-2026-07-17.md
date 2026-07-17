# ARM64 RK board status: 2026-07-17

Status: documentation complete; Path A hardware proof still required.

## Board matrix

| Board | SoC | yubiOS role | Current status |
|---|---|---|---|
| Radxa ROCK 5B | RK3588 | Primary Path A board | Selected primary. Needs sacrificial ROTPK/fuse rehearsal, OP-TEE, StandaloneMM/RPMB variables, fTPM NV, U-Boot UEFI, and signed UKI proof before production language. |
| ROCKPro64 | RK3399 | Supported secondary Path A board | Supported secondary. Follow after ROCK 5B proof; do not let it block primary Path A evidence. |
| QEMU ARM64 virt | vexpress-qemu_armv8a | CI firmware baseline | Useful for fTPM/StMM build and QEMU boot assertions. It is not proof of RPMB-backed real hardware behavior. |

## Path A vs Path B

Path A means owner-owned root of trust on real hardware: TF-A trusted-board-boot, OP-TEE as BL32, StandaloneMM with RPMB-backed variables, fTPM NV backed by real persistent storage, U-Boot UEFI, and a signed UKI boot path.

Path B means CI or emulated firmware can prove build shape and integration behavior but not hardware-backed persistence, fuses, RPMB, or owner root-of-trust custody.

ROCK 5B and ROCKPro64 stay Path B for production claims until the board-specific evidence is recorded in `refs/`.

## Firmware tags

`ci_firmware-rk.yml` publishes:

- `0mniteck/yubios:firmware`
- `0mniteck/yubios:firmware-<sha>`
- `0mniteck/yubios:firmware-qemu-arm64`
- `0mniteck/yubios:firmware-qemu-arm64-<sha>`
- `0mniteck/yubios:firmware-rock5b-rk3588`
- `0mniteck/yubios:firmware-rock5b-rk3588-<sha>`
- `0mniteck/yubios:firmware-rockpro64-rk3399`
- `0mniteck/yubios:firmware-rockpro64-rk3399-<sha>`

Until real hardware lanes produce board-divergent firmware, board-scoped images are metadata/routing placeholders carrying the QEMU-validated payload and a manifest warning.