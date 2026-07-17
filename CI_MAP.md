# CI_MAP.md

Regenerated from the `main` workflow shape on 2026-07-17 UTC.

This map treats `.github/workflows/*.yml` as the source of truth and focuses on CI steps, file inputs, artifact outputs, registry outputs, and callback handoffs. `PINNED.md` remains the source of truth for approved action SHAs and image digests.

## Workflow Inventory

| Workflow file | Role | Main inputs | Main outputs |
|---|---|---|---|
| `.github/workflows/ci.yml` | Top-level state machine | workflow dispatch inputs, callback state | Dispatches the next workflow in the ordered chain |
| `.github/workflows/fetch-dhi-manifest.yml` | DHI base digest refresh | `dhi.io/debian-base:trixie-debian13-dev`, `PINNED.md` | Updated DHI digest refs committed by workflow when drift exists |
| `.github/workflows/fetch-fedora-bootc-manifest.yml` | Fedora bootc digest refresh | `quay.io/fedora/fedora-bootc:45`, `PINNED.md` | Updated Fedora bootc digest refs committed by workflow when drift exists |
| `.github/workflows/ci_firmware-rk.yml` | Orchestrated ARM64/RK firmware integration and publish lane | yubi-OS firmware forks, pinned refs, StMM/fTPM/U-Boot/TF-A sources, board matrix | `BL32_AP_MM.fd`, `fip.bin`, `flash.bin`, QEMU verification, optional original and board-scoped firmware tags |
| `.github/workflows/ci_test-int.yml` | Legacy/manual ARM64 fTPM firmware integration reference | same firmware source family as the RK lane | manual QEMU firmware verification and optional historical `firmware` tags; no longer in the top-level `ci.yml` path |
| `.github/workflows/yubiOS-ci.yml` | Production image build and publish | `Containerfile`, `yubiOS.rego`, `usr/**`, `tests/unit/**`, `mkosi.*` | local CI images, optional per-arch and multi-arch `0mniteck/yubios:<sha>` and `latest` |
| `.github/workflows/ci_dev_image.yml` | Test image with software FIDO2 | `Containerfile`, `Containerfile.dev`, `yubiOS.rego` | optional `0mniteck/yubios:dev-<sha>` and `dev` |
| `.github/workflows/ci_test-vm.yml` | VM e2e tests | `tests/vm/*.sh`, pullable yubiOS image, bcvk `feat/swtpm-ci` | bcvk capability gate, VM boot/enrollment test results, callback state |
| `.github/workflows/ci_mkosi-installer.yml` | mkosi disk image and installer artifact | `mkosi.conf`, `mkosi.conf.d/**`, SoftHSM PKCS#11 mock | signed UKI verification, `yubiOS.raw.zst`, optional `0mniteck/yubios:installer` |
| `.github/workflows/ci_pq_tls_verify.yml` | PQ hybrid TLS drift check | DHI base container, live TLS endpoint, OpenSSL and Go floors | non-blocking PQ verification result |
| `.github/workflows/ci_fork_*.yml` | Optional fork component checks | yubi-OS fork feature branches | component build/lint/test artifacts and callback state |

The older `ci_int_stmm.yml`, `ci_int_optee_fip.yml`, and `ci_int_qemu.yml` lane names are not separate files on this branch. Their StMM, OP-TEE/FIP, and QEMU stages are embedded in the firmware integration workflows.

## Top-Level State Machine

`ci.yml` is the coordinator. Each child workflow reports back by dispatching `ci.yml` with `state=<completed workflow name>` and `completed_conclusion=<success|failure|cancelled>`. The coordinator stops on non-success before dispatching the next workflow.

```mermaid
flowchart TD
    user["Manual workflow_dispatch\n.github/workflows/ci.yml\nstate=start"]
    ci_start["ci.yml\nDispatch next workflow"]
    dhi["fetch-dhi-manifest.yml"]
    fedora["fetch-fedora-bootc-manifest.yml"]
    fork_gate{"ci_fork_run?"}
    forks["Optional ci_fork_* chain\nmkosi -> bcvk -> TF-A -> OP-TEE OS -> ms-tpm -> optee_ftpm -> U-Boot -> EDK2"]
    firmware["ci_firmware-rk.yml\nARM64/RK firmware integration"]
    prod["yubiOS-ci.yml\nproduction image CI"]
    dev["ci_dev_image.yml\ntest image with passless"]
    vm["ci_test-vm.yml\nbcvk VM e2e"]
    installer["ci_mkosi-installer.yml\nsigned installer artifact"]
    pq["ci_pq_tls_verify.yml\nPQ hybrid TLS check"]
    done["Ordered CI chain complete"]

    user --> ci_start
    ci_start --> dhi
    dhi -. "callback: state=fetch-dhi-manifest" .-> ci_start
    ci_start --> fedora
    fedora -. "callback: state=fetch-fedora-bootc-manifest" .-> ci_start
    ci_start --> fork_gate
    fork_gate -- "true" --> forks
    forks -. "callback after each fork workflow" .-> ci_start
    fork_gate -- "false" --> firmware
    forks --> firmware
    firmware -. "callback: state=yubiOS RK firmware" .-> ci_start
    ci_start --> prod
    prod -. "callback: state=yubiOS CI" .-> ci_start
    ci_start --> dev
    dev -. "callback: state=yubiOS dev/test image" .-> ci_start
    ci_start --> vm
    vm -. "callback: state=yubiOS VM e2e" .-> ci_start
    ci_start --> installer
    installer -. "callback: state=ci_mkosi-installer" .-> ci_start
    ci_start --> pq
    pq -. "callback: state=PQ hybrid TLS verification" .-> ci_start
    ci_start --> done
```

## ARM64/RK Firmware Integration

`ci_firmware-rk.yml` is the orchestrated firmware lane. It preserves the firmware integration shape from `ci_test-int.yml`, then publishes the original firmware tag plus board-scoped variants when `Docker_push=true`.

```mermaid
flowchart TD
    wf["ci_firmware-rk.yml"]
    refs["Pinned env refs\nTF-A\nOP-TEE OS\noptee_ftpm\nU-Boot\nEDK2\nEDK2 platforms\nms-tpm-20-ref\nmbedTLS"]
    stmm["job: stmm\nbuild EDK2 StandaloneMM\nPlatformStandaloneMmRpmb"]
    stmm_out["artifact\nBL32_AP_MM-arch\nBL32_AP_MM.fd"]
    optee["job: optee_fip\nbuild U-Boot BL33\nbuild OP-TEE TA dev kit\nbuild fTPM TA\nrebuild OP-TEE BL32 with Early TA and StMM"]
    optee_out["artifact\nfip-flash-arch\nfip.bin\nflash.bin\nbl1.bin\nBL32_AP_MM.fd\ntee-*_v2.bin\nu-boot.bin\nfip-info.txt"]
    qemu["job: qemu\ndownload fip-flash\nassemble flash.bin if needed\nboot qemu-system-aarch64"]
    asserts["QEMU asserts\nfTPM Early TA loads\nTPM self-test marker\nno known failure signatures\nStMM SP loaded"]
    publish["job: firmware-publish\nmatrix: qemu-arm64, rock5b-rk3588, rockpro64-rk3399\nif Docker_push=true"]
    fw_payload["/firmware payload\nboard MANIFEST.txt\nfip.bin flash.bin bl1.bin\nBL32_AP_MM.fd u-boot.bin tee bins"]
    fw_registry["Docker Hub outputs\nfirmware, firmware-sha\nfirmware-qemu-arm64[-sha]\nfirmware-rock5b-rk3588[-sha]\nfirmware-rockpro64-rk3399[-sha]"]
    cb["ci-callback to ci.yml\nstate=yubiOS RK firmware"]

    wf --> refs
    refs --> stmm --> stmm_out --> optee --> optee_out --> qemu --> asserts
    optee_out --> publish --> fw_payload --> fw_registry
    stmm --> cb
    optee --> cb
    qemu --> cb
    publish --> cb
```

`ci_test-int.yml` remains available for manual/historical comparison, but `ci.yml` no longer dispatches it and no longer waits for a `yubiOS firmware` callback state.

## Production, Dev, VM, Installer, and PQ Lanes

```mermaid
flowchart TD
    prod["yubiOS-ci.yml\nproduction bootc image"]
    prod_out["0mniteck/yubios:<sha>\n0mniteck/yubios:latest"]
    dev["ci_dev_image.yml\nTEST-only swu2f/passless image"]
    dev_out["0mniteck/yubios:dev-<sha>\n0mniteck/yubios:dev"]
    vm["ci_test-vm.yml\nbcvk VM e2e"]
    vm_out["VM boot, LUKS/FIDO2, enrollment-surface results\nexplicit loud skips"]
    installer["ci_mkosi-installer.yml\nmkosi + SoftHSM PKCS#11 signing"]
    installer_out["0mniteck/yubios:installer\n0mniteck/yubios:installer-<sha>"]
    pq["ci_pq_tls_verify.yml\nOpenSSL/Go hybrid PQ TLS drift check"]
    pq_out["non-blocking verification result"]

    prod --> prod_out
    dev --> dev_out --> vm --> vm_out
    installer --> installer_out
    pq --> pq_out
```

## Optional Fork Component CI

When `ci_fork_run=true`, `ci.yml` runs component workflows before firmware integration. They validate yubi-OS fork feature branches but do not stitch a full firmware image; stitching happens in `ci_firmware-rk.yml`.

```mermaid
flowchart LR
    start["ci.yml after Fedora digest refresh"]
    mkosi["ci_fork_mkosi.yml"]
    bcvk["ci_fork_bcvk.yml"]
    tfa["ci_fork_arm-trusted-firmware.yml"]
    optee["ci_fork_optee-os.yml"]
    ms["ci_fork_ms-tpm-20-ref.yml"]
    ftpm["ci_fork_optee-ftpm.yml"]
    uboot["ci_fork_u-boot.yml"]
    edk2["ci_fork_edk2.yml"]
    firmware["ci_firmware-rk.yml"]

    start --> mkosi --> bcvk --> tfa --> optee --> ms --> ftpm --> uboot --> edk2 --> firmware
```

## Push Triggers and Self-Change Validation

Most workflows are `workflow_dispatch` driven. Narrow `push` triggers are used only where the workflow file itself or relevant source paths should validate automatically.

```mermaid
flowchart TD
    push_main["push to main"]
    yw_paths["yubiOS-ci.yml paths\nworkflow file\nContainerfile\nyubiOS.rego\nusr/**\ntests/unit/**\nmkosi.*"]
    self_paths["self-change workflow paths\nfetch manifests\nci_firmware-rk\nci_test-int\nci_dev_image\nci_pq_tls_verify\nselected ci_fork files"]
    dispatch_only["workflow_dispatch only\nci.yml\nci_test-vm\nci_mkosi-installer\nsome fork workflows"]
    run_yw["run yubiOS-ci.yml"]
    run_self["run changed self-trigger workflow"]
    manual["manual or orchestrated dispatch"]

    push_main --> yw_paths --> run_yw
    push_main --> self_paths --> run_self
    dispatch_only --> manual
```

## Artifact and Registry Output Map

```mermaid
flowchart LR
    source["Source files and fork refs"]
    pins["PINNED.md digests and action SHAs"]
    policy["yubiOS.rego\nDocker Build Policy"]
    prod["Production OCI image\n0mniteck/yubios:sha\n0mniteck/yubios:latest"]
    dev["Dev/test OCI image\n0mniteck/yubios:dev-sha\n0mniteck/yubios:dev"]
    firmware["Firmware OCI artifacts\n0mniteck/yubios:firmware\nfirmware-sha\nfirmware-board\nfirmware-board-sha"]
    installer["Installer OCI artifact\n0mniteck/yubios:installer\n0mniteck/yubios:installer-sha"]
    ci_logs["CI outputs\nartifacts, step summaries,\nexplicit skips, callback states"]

    source --> policy --> prod
    source --> dev
    source --> firmware
    source --> installer
    pins --> prod
    pins --> dev
    pins --> firmware
    pins --> installer
    prod --> ci_logs
    dev --> ci_logs
    firmware --> ci_logs
    installer --> ci_logs
```

## Callback Contract

Every orchestrated child workflow accepts the same internal callback fields. The child workflow computes an aggregate result from `needs`, then dispatches `ci.yml` so the state machine can proceed.

```mermaid
sequenceDiagram
    participant C as ci.yml
    participant W as child workflow
    participant J as jobs in child workflow

    C->>W: workflow_dispatch(ref, inputs, ci_callback=true)
    W->>J: run declared jobs and matrices
    J-->>W: needs JSON with job results
    W->>W: reduce needs to success or failure
    W->>C: workflow_dispatch(state, completed_conclusion, original inputs)
    C->>C: stop on non-success, else dispatch next workflow
```
