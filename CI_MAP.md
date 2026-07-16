# CI_MAP.md

Generated from the `docs/research` branch workflow files after fast-forwarding it to `main` on 2026-07-16 UTC.

This map treats `.github/workflows/*.yml` as the source of truth and focuses on CI steps, file inputs, artifact outputs, registry outputs, and callback handoffs. `PINNED.md` remains the source of truth for approved action SHAs and image digests.

## Workflow Inventory

| Workflow file | Role | Main inputs | Main outputs |
|---|---|---|---|
| `.github/workflows/ci.yml` | Top-level state machine | workflow dispatch inputs, callback state | Dispatches the next workflow in the ordered chain |
| `.github/workflows/fetch-dhi-manifest.yml` | DHI base digest refresh | `dhi.io/debian-base:trixie-debian13-dev`, `PINNED.md` | Updated DHI digest refs committed by workflow when drift exists |
| `.github/workflows/fetch-fedora-bootc-manifest.yml` | Fedora bootc digest refresh | `quay.io/fedora/fedora-bootc:45`, `PINNED.md` | Updated Fedora bootc digest refs committed by workflow when drift exists |
| `.github/workflows/ci_test-int.yml` | ARM64 fTPM firmware integration | yubi-OS firmware forks, pinned refs, StMM/fTPM/U-Boot/TF-A sources | `BL32_AP_MM.fd`, `fip.bin`, `flash.bin`, QEMU verification, optional `0mniteck/yubios:firmware` |
| `.github/workflows/yubiOS-ci.yml` | Production image build and publish | `Containerfile`, `yubiOS.rego`, `usr/**`, `tests/unit/**`, `mkosi.*` | local CI images, optional per-arch and multi-arch `0mniteck/yubios:<sha>` and `latest` |
| `.github/workflows/ci_dev_image.yml` | Test image with software FIDO2 | `Containerfile`, `Containerfile.dev`, `yubiOS.rego` | optional `0mniteck/yubios:dev-<sha>` and `dev` |
| `.github/workflows/ci_test-vm.yml` | VM e2e tests | `tests/vm/*.sh`, pullable yubiOS image, bcvk `feat/swtpm-ci` | bcvk capability gate, VM boot/enrollment test results, callback state |
| `.github/workflows/ci_mkosi-installer.yml` | mkosi disk image and installer artifact | `mkosi.conf`, `mkosi.conf.d/**`, SoftHSM PKCS#11 mock | signed UKI verification, `yubiOS.raw.zst`, optional `0mniteck/yubios:installer` |
| `.github/workflows/ci_pq_tls_verify.yml` | PQ hybrid TLS drift check | DHI base container, live TLS endpoint, OpenSSL and Go floors | non-blocking PQ verification result |
| `.github/workflows/ci_fork_*.yml` | Optional fork component checks | yubi-OS fork feature branches | component build/lint/test artifacts and callback state |

The older `ci_int_stmm.yml`, `ci_int_optee_fip.yml`, and `ci_int_qemu.yml` lane names are not separate files on this branch. Their StMM, OP-TEE/FIP, and QEMU stages are embedded in `.github/workflows/ci_test-int.yml`.

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
    integ["ci_test-int.yml\nARM64 firmware integration"]
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
    fork_gate -- "false" --> integ
    forks --> integ
    integ -. "callback: state=ci_test-int" .-> ci_start
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

## Production Image CI

`yubiOS-ci.yml` runs text and build gates, then optionally publishes the production multi-arch bootc image.

```mermaid
flowchart TD
    wf[".github/workflows/yubiOS-ci.yml"]
    inputs["Repo inputs\nContainerfile\nyubiOS.rego\nusr/lib/yubiOS/*.sh\ntests/unit/**\nmkosi.conf and mkosi.*"]
    pins["PINNED.md\nDHI base index digest\nactions/checkout SHA\nhadolint image digest"]
    shell["job: shellcheck\ninstall shellcheck\nscan usr/lib/yubiOS/*.sh"]
    hadolint["job: hadolint\nlint Containerfile"]
    unit["job: unit-tests matrix\namd64 + arm64\nbats tests/unit/"]
    mkosi["job: mkosi matrix\ninstall yubi-OS/mkosi fork\nmkosi summary"]
    build["job: build matrix\ninstall Docker 29.6 + buildx 0.35\nprivate dockerd on ducker.sock"]
    oci["build OCI image\nbuildx --policy yubiOS.rego\n--platform linux/arch\nlocal tag yubios:ci-arch"]
    verify["container checks\n/usr/lib/yubiOS symlinks\n/usr/bin/yubiOS-* scripts\npam_u2f wiring"]
    arch_push["optional Docker_push\npush 0mniteck/yubios:sha-arch"]
    manifest["job: merge-manifest\ncreate manifest list"]
    registry["Docker Hub outputs\n0mniteck/yubios:sha\n0mniteck/yubios:latest"]
    callback["job: ci-callback\nreports aggregate result to ci.yml"]

    wf --> inputs
    pins --> shell
    pins --> hadolint
    pins --> build
    inputs --> shell
    inputs --> hadolint
    shell --> unit
    hadolint --> unit
    inputs --> mkosi
    shell --> build
    hadolint --> build
    build --> oci --> verify --> arch_push --> manifest --> registry
    shell --> callback
    hadolint --> callback
    unit --> callback
    mkosi --> callback
    build --> callback
    manifest --> callback
```

## Dev Image and VM E2E

The dev image is intentionally separate from production. It layers `Containerfile.dev` on the production image and verifies `passless`, then the VM workflow uses that pullable image for bcvk-backed tests.

```mermaid
flowchart TD
    prod_inputs["Containerfile\nyubiOS.rego"]
    dev_inputs["Containerfile.dev\nsoftware FIDO2 test layer"]
    dev_wf["ci_dev_image.yml"]
    dev_build["job: build matrix\nDocker + buildx in DHI container"]
    base_img["local image\nyubios:base-arch"]
    dev_img["local image\nyubios:dev-arch"]
    passless["verify passless exists\npassless --version"]
    dev_push["optional push\n0mniteck/yubios:dev-sha-arch"]
    dev_manifest["merge dev manifest\n0mniteck/yubios:dev-sha\n0mniteck/yubios:dev"]
    vm_wf["ci_test-vm.yml"]
    vm_inputs["tests/vm/*.sh\nworkflow image input\nbcvk feat/swtpm-ci\nswtpm, swu2f, qemu, KVM"]
    lint_vm["job: lint-vm-scripts\nbash -n + shellcheck"]
    bcvk["job: vm-e2e matrix\nbuild bcvk\nassert --swtpm and --swu2f"]
    gates["runtime gates\nKVM present\nARM64 primary policy\nimage available"]
    tests["run VM scripts\ntest-luks-fido2-ci.sh\ntest-fido2-enrollment.sh"]
    loud_skip["explicit skip outputs\nfor unavailable image, KVM, or known harness limits"]
    cb["ci-callback to ci.yml"]

    dev_wf --> prod_inputs --> dev_build
    dev_wf --> dev_inputs --> dev_build
    dev_build --> base_img --> dev_img --> passless --> dev_push --> dev_manifest
    dev_manifest --> vm_wf
    vm_wf --> vm_inputs --> lint_vm --> bcvk --> gates
    gates --> tests
    gates --> loud_skip
    lint_vm --> cb
    tests --> cb
    loud_skip --> cb
```

## ARM64 fTPM Firmware Integration

`ci_test-int.yml` embeds the former F1/F2/F4 lane stages in one workflow. It builds StMM, folds fTPM into OP-TEE, packages TF-A FIP with U-Boot BL33, boots QEMU, and optionally publishes a firmware OCI artifact.

```mermaid
flowchart TD
    wf["ci_test-int.yml"]
    refs["Pinned env refs\nTF-A\nOP-TEE OS\noptee_ftpm\nU-Boot\nEDK2\nEDK2 platforms\nms-tpm-20-ref\nmbedTLS"]
    stmm["job: stmm\nbuild EDK2 StandaloneMM\nPlatformStandaloneMmRpmb"]
    stmm_out["artifact\nBL32_AP_MM-arch\nBL32_AP_MM.fd"]
    optee["job: optee_fip\nbuild U-Boot BL33\nbuild OP-TEE TA dev kit\nbuild fTPM TA\nrebuild OP-TEE BL32 with Early TA and StMM"]
    optee_out["artifact\nfip-flash-arch\nfip.bin\nflash.bin\nbl1.bin\nBL32_AP_MM.fd\ntee-*_v2.bin\nu-boot.bin\nfip-info.txt"]
    qemu["job: qemu\ndownload fip-flash\nassemble flash.bin if needed\nboot qemu-system-aarch64"]
    asserts["QEMU asserts\nfTPM Early TA loads\nTPM self-test marker\nno known failure signatures\nStMM SP loaded"]
    publish["job: firmware-publish\nif Docker_push=true"]
    fw_payload["/firmware payload\nMANIFEST.txt\nfip.bin flash.bin bl1.bin\nBL32_AP_MM.fd u-boot.bin tee bins"]
    fw_registry["Docker Hub outputs\n0mniteck/yubios:firmware\n0mniteck/yubios:firmware-sha"]
    cb["ci-callback to ci.yml"]

    wf --> refs
    refs --> stmm --> stmm_out --> optee --> optee_out --> qemu --> asserts
    optee_out --> publish --> fw_payload --> fw_registry
    stmm --> cb
    optee --> cb
    qemu --> cb
    publish --> cb
```

## Optional Fork Component CI

When `ci_fork_run=true`, `ci.yml` runs these component workflows before integration. They validate yubi-OS fork feature branches but do not stitch a full firmware image; stitching happens in `ci_test-int.yml`.

```mermaid
flowchart LR
    start["ci.yml after Fedora digest refresh"]
    mkosi["ci_fork_mkosi.yml\nrepo: yubi-OS/mkosi\nref: feature/yubiOS-profile\nprofile syntax, shellcheck, ruff"]
    bcvk["ci_fork_bcvk.yml\nrepo: yubi-OS/bcvk\nref: feat/ci\nRust unit tests, cargo check, advisory clippy"]
    tfa["ci_fork_arm-trusted-firmware.yml\nrepo: yubi-OS/arm-trusted-firmware\nref: feat/ci\nBL31 + placeholder TBB FIP"]
    optee["ci_fork_optee-os.yml\nrepo: yubi-OS/optee_os\nref: feat/ci\nBL32 + TA dev kit"]
    ms["ci_fork_ms-tpm-20-ref.yml\nrepo: yubi-OS/ms-tpm-20-ref\nref: feat/ci\ntpm2 simulator + libtpm"]
    ftpm["ci_fork_optee-ftpm.yml\nrepo: yubi-OS/optee_ftpm\nref: feat/ci\nfTPM TA vs OP-TEE dev kit"]
    uboot["ci_fork_u-boot.yml\nrepo: yubi-OS/u-boot\nref: feat/ci\nBL33 with fTPM and measured boot config"]
    edk2["ci_fork_edk2.yml\nrepo: yubi-OS/edk2\nref: feat/ci\nStandaloneMM AARCH64 build"]
    integ["ci_test-int.yml\nfull integration after optional fork chain"]

    start --> mkosi --> bcvk --> tfa --> optee --> ms --> ftpm --> uboot --> edk2 --> integ
```

```mermaid
flowchart TD
    fork_files["Fork workflow files\nci_fork_*.yml"]
    upstreams["External fork inputs\nyubi-OS/mkosi\nyubi-OS/bcvk\nyubi-OS/arm-trusted-firmware\nyubi-OS/optee_os\nyubi-OS/ms-tpm-20-ref\nyubi-OS/optee_ftpm\nyubi-OS/u-boot\nyubi-OS/edk2"]
    toolchains["Bare runner toolchains\nRust\nAArch64 cross GCC\nARMhf GCC\nEDK2 BaseTools\nOpenSSL and build deps"]
    artifacts["Workflow artifacts\nTF-A fip.bin\nOP-TEE BL32/devkit checks\nms-tpm simulator\nU-Boot binaries\nEDK2 module outputs"]
    callback["Per-workflow callback\nstate=workflow name\ncompleted_conclusion=aggregate result"]

    fork_files --> upstreams --> toolchains --> artifacts --> callback
```

## Manifest Refreshers

The manifest refresh workflows are intentionally bare-runner jobs because they query registries and update text files. They can commit digest updates directly when a new index digest is found.

```mermaid
flowchart TD
    dhi_wf["fetch-dhi-manifest.yml"]
    dhi_registry["dhi.io registry\n0mniteck42 + DOCKER secret\ndebian-base:trixie-debian13-dev"]
    dhi_index["OCI index digest\namd64 child digest\narm64 child digest"]
    fedora_wf["fetch-fedora-bootc-manifest.yml"]
    quay["quay.io registry\nfedora/fedora-bootc:45"]
    fedora_index["OCI index digest\nper-arch child list in logs"]
    files["Repo text files\nPINNED.md\nworkflow files\nContainerfile and docs with old digests"]
    commit["If changed\ngit commit + push digest refresh"]
    cb["ci-callback to ci.yml"]

    dhi_wf --> dhi_registry --> dhi_index --> files
    fedora_wf --> quay --> fedora_index --> files
    files --> commit --> cb
    files -->|"already current"| cb
```

## Installer and PQ Verification

The installer workflow proves the mkosi plus PKCS#11 signing path using SoftHSM as a CI-safe stand-in for YubiKey PIV slot 9c. The PQ TLS workflow is a drift check for ADR-025 and currently runs non-blocking.

```mermaid
flowchart TD
    mkosi_wf["ci_mkosi-installer.yml"]
    mkosi_inputs["mkosi.conf\nmkosi.conf.d/**\nyubi-OS/mkosi feature/yubiOS-profile\nSoftHSM token in /run/yubios-hsm"]
    build_img["mkosi build\nminimal profile\nsystemd-sbsign via provider:pkcs11"]
    verify_uki["sbverify signed UKI\nagainst CI certificate"]
    installer_payload["/installer payload\nyubiOS.raw.zst\n*.efi\nmanifest files\nci-secure-boot-cert.pem\nMANIFEST.txt"]
    installer_push["optional Docker_push\n0mniteck/yubios:installer\n0mniteck/yubios:installer-sha"]

    pq_wf["ci_pq_tls_verify.yml"]
    pq_inputs["DHI base container\nOpenSSL >= 3.5\ncurl to live TLS endpoint\nGo >= 1.24 if installed"]
    pq_result["non-blocking result\nconfirms MLKEM negotiation or reports drift"]

    mkosi_wf --> mkosi_inputs --> build_img --> verify_uki --> installer_payload --> installer_push
    pq_wf --> pq_inputs --> pq_result
```

## Push Triggers and Self-Change Validation

Most workflows are `workflow_dispatch` driven. Narrow `push` triggers are used only where the workflow file itself or relevant source paths should validate automatically.

```mermaid
flowchart TD
    push_main["push to main"]
    yw_paths["yubiOS-ci.yml paths\nworkflow file\nContainerfile\nyubiOS.rego\nusr/**\ntests/unit/**\nmkosi.*"]
    self_paths["self-change workflow paths\nfetch manifests\nci_test-int\nci_dev_image\nci_pq_tls_verify\nselected ci_fork files"]
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
    firmware["Firmware OCI artifact\n0mniteck/yubios:firmware\n0mniteck/yubios:firmware-sha"]
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
