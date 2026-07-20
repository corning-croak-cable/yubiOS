# CI_MAP.md

Regenerated from the `main` workflow shape at `7809d5c` on 2026-07-20 UTC.

This map treats `.github/workflows/*.yml` as the source of truth for events, runners, jobs, artifacts, and callback handoffs. `yubiOS-bake.hcl` is the source of truth for every Docker build in the non-`ci_fork*` chain dispatched by `ci.yml`. `PINNED.md` remains the source of truth for approved action SHAs and image digests.

## Workflow Inventory

| Workflow file | Role | Main inputs | Main outputs |
|---|---|---|---|
| `.github/workflows/ci.yml` | Top-level state machine | callback state, target ref, four publish flags, fork gate, VM image | Dispatches the next workflow in the ordered chain |
| `.github/workflows/fetch-dhi-manifest.yml` | DHI base digest refresh | `dhi.io/debian-base:trixie-debian13-dev`, `PINNED.md` | Updated DHI digest refs committed by workflow when drift exists |
| `.github/workflows/fetch-fedora-bootc-manifest.yml` | Fedora bootc digest refresh | `quay.io/fedora/fedora-bootc:45`, `PINNED.md` | Updated Fedora bootc digest refs committed by workflow when drift exists |
| `.github/workflows/ci_firmware-rk.yml` | Orchestrated ARM64/RK firmware integration and publish lane | yubi-OS firmware forks, pinned refs, board matrix, `yubiOS-bake.hcl` | `BL32_AP_MM.fd`, `fip.bin`, `flash.bin`, QEMU verification, optional original and board-scoped firmware tags through Bake |
| `.github/workflows/ci_test-int.yml` | Legacy/manual ARM64 fTPM firmware integration reference | same firmware source family as the RK lane | manual QEMU firmware verification and optional historical `firmware` tags; no longer in the top-level `ci.yml` path |
| `.github/workflows/yubiOS-ci.yml` | Production image build and publish | `Containerfile`, `yubiOS-bake.hcl`, `yubiOS.rego`, `usr/**`, unit tests | Bake build/smoke results; optional per-arch tags and multi-arch `0mniteck/yubios:<sha>` plus `latest` |
| `.github/workflows/ci_dev_image.yml` | TEST-only image with software FIDO2 | `Containerfile.dev`, production target context, `yubiOS-bake.hcl`, `yubiOS.rego` | Bake build/smoke results; optional `0mniteck/yubios:dev-<sha>` and `dev` |
| `.github/workflows/ci_test-vm.yml` | VM e2e tests | pullable yubiOS image, bcvk source, Podman storage, VM scripts | bcvk capability gate, DirectBoot SSH credential transport, VM enrollment results, callback state |
| `.github/workflows/ci_mkosi-installer.yml` | mkosi disk image and installer artifact | `mkosi.conf`, `mkosi.conf.d/**`, SoftHSM PKCS#11 mock, `yubiOS-bake.hcl` | signed UKI verification, `yubiOS.raw.zst`, optional installer tags through Bake |
| `.github/workflows/ci_pq_tls_verify.yml` | PQ hybrid TLS drift check | `yubiOS-bake.hcl`, `yubiOS.rego`, pinned DHI base, live TLS endpoint | uncached, non-blocking Bake verification result |
| `.github/workflows/test.yml` | Standalone self-hosted ARM64/KVM diagnostic | pullable yubiOS image, Podman, bcvk/QEMU host capabilities | QEMU kernel bind-mount diagnostics; not in the `ci.yml` chain |
| `.github/workflows/ci_fork_*.yml` | Optional fork component checks | yubi-OS fork feature branches | component build/lint/test artifacts and callback state |

The older `ci_int_stmm.yml`, `ci_int_optee_fip.yml`, and `ci_int_qemu.yml` lane names are not separate files on current `main`. Their StMM, OP-TEE/FIP, and QEMU stages are embedded in the firmware integration workflows.

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
    dev -. "callback: state=yubiOS dev/test image (swu2f, ADR-026)" .-> ci_start
    ci_start --> vm
    vm -. "callback: state=yubiOS VM e2e (tests/vm)" .-> ci_start
    ci_start --> installer
    installer -. "callback: state=yubiOS mkosi-installer" .-> ci_start
    ci_start --> pq
    pq -. "callback: state=PQ hybrid TLS verification (ADR-025)" .-> ci_start
    ci_start --> done
```

## Canonical Docker Bake Graph

The merged `yubiOS-bake.hcl` replaces workflow-local `docker build` and `docker buildx build` commands in every non-fork workflow dispatched by `ci.yml`. GitHub Actions still owns event handling, runner selection, Docker/Buildx installation, active-builder selection, artifact transfer, host/Podman/KVM work, and final multi-architecture index assembly. The design rationale and Docker primary-source trail are recorded in [the Bake consolidation note](refs/docker-bake-consolidation-2026-07-17.md).

Four hidden targets provide the shared contract:

- `_policy` loads exactly one `yubiOS.rego` policy with `reset=true` and `strict=true`;
- `_source-metadata` supplies the source and revision OCI labels;
- `_image-export` selects Docker output when `PUSH=false` and registry output when `PUSH=true`; and
- `_yubios-base` defines the pinned production `Containerfile` build consumed by production and dev targets.

```mermaid
flowchart TD
    policy["_policy\nyubiOS.rego\nreset + strict"]
    metadata["_source-metadata\nsource + revision labels"]
    exporter["_image-export\nDocker or registry"]
    base["_yubios-base\nContainerfile"]
    prod["yubios"]
    prod_smoke["yubios-smoke\ncacheonly"]
    dev["yubios-dev"]
    dev_smoke["yubios-dev-smoke\ncacheonly"]
    artifacts["firmware\ninstaller"]
    pq["pq-tls-verify\nno-cache + cacheonly"]

    policy --> base
    metadata --> base
    base --> prod
    exporter --> prod
    base -. "target context" .-> prod_smoke
    policy --> prod_smoke
    base -. "target context" .-> dev
    policy --> dev
    metadata --> dev
    exporter --> dev
    dev -. "target context" .-> dev_smoke
    policy --> dev_smoke
    policy --> artifacts
    metadata --> artifacts
    exporter --> artifacts
    policy --> pq
```

| Workflow | CI target/group | Explicit publication target | Builder ownership |
|---|---|---|---|
| `yubiOS-ci.yml` | `yubios-ci` (`yubios` + `yubios-smoke`) | `yubios` | Containerized job creates and names user-scoped `hardened` builder |
| `ci_dev_image.yml` | `yubios-dev-ci` (`yubios-dev` + `yubios-dev-smoke`) | `yubios-dev` | Containerized job creates and names user-scoped `hardened` builder |
| `ci_firmware-rk.yml` | None unless publication is requested | `firmware` | Every Stage 1–4 job uses the pinned DHI container and creates a user-scoped `hardened` builder |
| `ci_mkosi-installer.yml` | DHI-contained mkosi validation plus artifact handoff | `installer` | Every build and publication job uses the pinned DHI container and creates a user-scoped `hardened` builder |
| `ci_pq_tls_verify.yml` | `pq-tls-verify` | None; output is `cacheonly` | Containerized job creates and names user-scoped `hardened` builder |

Production and dev publication remains a two-stage operation: native runners publish immutable per-architecture tags through Bake, then existing `imagetools` jobs create the `<sha>`/`latest` and `dev-<sha>`/`dev` multi-architecture indexes. Firmware and installer targets publish directly with the registry exporter from privileged DHI container jobs that check out the policy-bound Bake definition and explicitly select their user-scoped `hardened` builders.

## ARM64/RK Firmware Integration

`ci_firmware-rk.yml` is the orchestrated firmware lane. Every build, verification, and publication stage runs in the pinned multi-arch DHI container and installs Docker/Buildx through the shared `wcurl` pattern, creating a user-scoped `hardened` builder. The workflow preserves the firmware integration shape, prepares one board payload per matrix entry, then invokes the Bake `firmware` target with `PUSH=true` when publication is requested. The QEMU board retains the compatibility `firmware` tags; every publishable board receives board-scoped tags.

```mermaid
flowchart TD
    wf["ci_firmware-rk.yml"]
    refs["Pinned env refs\nTF-A\nOP-TEE OS\noptee_ftpm\nU-Boot\nEDK2\nEDK2 platforms\nms-tpm-20-ref\nmbedTLS"]
    stmm["DHI job: stmm\nuser-scoped hardened builder\nbuild EDK2 StandaloneMM\nPlatformStandaloneMmRpmb"]
    stmm_out["artifact\nBL32_AP_MM-arch\nBL32_AP_MM.fd"]
    optee["DHI job: optee_fip\nuser-scoped hardened builder\nbuild U-Boot BL33\nbuild OP-TEE TA dev kit\nbuild fTPM TA\nrebuild OP-TEE BL32 with Early TA and StMM"]
    optee_out["artifact\nfip-flash-arch\nfip.bin\nflash.bin\nbl1.bin\nBL32_AP_MM.fd\ntee-*_v2.bin\nu-boot.bin\nfip-info.txt"]
    qemu["DHI job: qemu\nuser-scoped hardened builder\ndownload fip-flash\nassemble flash.bin if needed\nboot qemu-system-aarch64"]
    asserts["QEMU asserts\nfTPM Early TA loads\nTPM self-test marker\nno known failure signatures\nStMM SP loaded"]
    publish["job: firmware-publish in DHI container\ncheckout + user-scoped hardened builder\nmatrix: qemu-arm64, rock5b-rk3588, rockpro64-rk3399\nif workflow_dispatch + Docker_push=true"]
    fw_payload["/firmware payload\nboard MANIFEST.txt\nfip.bin flash.bin bl1.bin\nBL32_AP_MM.fd u-boot.bin tee bins"]
    bake["Bake target: firmware\nstrict yubiOS.rego policy\nregistry exporter"]
    fw_registry["Docker Hub outputs\nfirmware[-sha] for QEMU compatibility\nfirmware-qemu-arm64[-sha]\nfirmware-rock5b-rk3588[-sha]\nfirmware-rockpro64-rk3399[-sha]"]
    cb["ci-callback to ci.yml\nstate=yubiOS RK firmware"]

    wf --> refs
    refs --> stmm --> stmm_out --> optee --> optee_out --> qemu --> asserts
    optee_out --> publish --> fw_payload --> bake --> fw_registry
    stmm --> cb
    optee --> cb
    qemu --> cb
    publish --> cb
```

`ci_test-int.yml` remains available for manual/historical comparison, but `ci.yml` no longer dispatches it and no longer waits for a `yubiOS firmware` callback state.

## Production, Dev, VM, Installer, and PQ Lanes

```mermaid
flowchart TD
    prod_wf["yubiOS-ci.yml\nnative amd64 + arm64"]
    prod_bake["Bake: yubios-ci / yubios\nbuild + smoke"]
    prod_out["per-arch sha-arch\nimagetools -> sha + latest"]
    dev_wf["ci_dev_image.yml\nTEST-only swu2f/passless"]
    dev_bake["Bake: yubios-dev-ci / yubios-dev\nproduction target context + smoke"]
    dev_out["per-arch dev-sha-arch\nimagetools -> dev-sha + dev"]
    vm["ci_test-vm.yml\nsudo Podman storage + bcvk\nARM64 DirectBoot credential"]
    vm_out["VM boot, LUKS/FIDO2, enrollment results\nexplicit loud skips"]
    installer["ci_mkosi-installer.yml DHI build job\nuser-scoped hardened builder\nmkosi + SoftHSM PKCS#11 signing"]
    installer_payload["prepared installer payload\nworkflow artifact handoff"]
    installer_bake["DHI publish job\nuser-scoped hardened builder\nBake: installer + registry exporter"]
    installer_out["installer\ninstaller-sha"]
    pq["ci_pq_tls_verify.yml"]
    pq_bake["Bake: pq-tls-verify\nno-cache + cacheonly"]
    pq_out["non-blocking PQ TLS result"]

    prod_wf --> prod_bake --> prod_out
    dev_wf --> dev_bake --> dev_out --> vm --> vm_out
    installer --> installer_payload --> installer_bake --> installer_out
    pq --> pq_bake --> pq_out
```

The VM lane intentionally remains outside Bake. bcvk hardcodes Podman for its privileged ephemeral container and reads from Podman's local image store, so the workflow pulls the selected image with `sudo podman`. Guest SSH runs from inside that outer container. For ARM64 DirectBoot, the public root key is delivered without firmware through systemd's kernel-command-line `tmpfiles.extra` credential path.

The installer self-change push trigger validates mkosi without publishing. Only a `workflow_dispatch` with `Docker_push=true` uploads the prepared `inst/installer` payload, hands it to the containerized publish job, and packages it through the policy-bound Bake `installer` target.

## Optional Fork Component CI

When `ci_fork_run=true`, `ci.yml` runs component workflows before firmware integration. They validate yubi-OS fork feature branches but do not stitch a full firmware image; stitching happens in `ci_firmware-rk.yml`.

```mermaid
flowchart TD
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

The orchestrated path is `workflow_dispatch` driven. Narrow `push` triggers validate current-main workflow edits without starting the callback chain; every callback is guarded by both `github.event_name == 'workflow_dispatch'` and `ci_callback == true`.

```mermaid
flowchart TD
    push_main["push to main"]
    yw_paths["yubiOS-ci.yml build inputs\nworkflow file\nContainerfile\nyubiOS-bake.hcl\nyubiOS.rego\nusr/** + tests/unit/** + mkosi.*"]
    self_paths["workflow-only self-change paths\nfetch manifests\nfirmware + dev + VM + installer + PQ\nci_test-int + test.yml\nselected ci_fork files"]
    dispatch_only["workflow_dispatch only\nci.yml\nremaining ci_fork workflows"]
    run_yw["run yubiOS-ci.yml"]
    run_self["run changed self-trigger workflow"]
    manual["manual or orchestrated dispatch"]

    push_main --> yw_paths --> run_yw
    push_main --> self_paths --> run_self
    dispatch_only --> manual
```

## Artifact and Registry Output Map

```mermaid
flowchart TD
    source["Source files\nprepared firmware/installer payloads"]
    pins["PINNED.md digests and action SHAs"]
    policy["yubiOS.rego\nstrict inherited target.policy"]
    bake["yubiOS-bake.hcl\ntargets, tags, platforms, labels, outputs"]
    prod["Production OCI\nsha-arch -> sha + latest"]
    dev["TEST-only OCI\ndev-sha-arch -> dev-sha + dev"]
    firmware["Firmware OCI\nfirmware[-sha]\nfirmware-board[-sha]"]
    installer["Installer OCI\ninstaller[-sha]"]
    pq["PQ TLS verification\ncacheonly result"]
    vm["Host/Podman/KVM evidence"]
    ci_logs["CI outputs\nartifacts, step summaries,\nexplicit skips, callback states"]

    source --> bake
    pins --> bake
    policy --> bake
    bake --> prod
    bake --> dev
    bake --> firmware
    bake --> installer
    bake --> pq
    source --> vm
    prod --> ci_logs
    dev --> ci_logs
    firmware --> ci_logs
    installer --> ci_logs
    pq --> ci_logs
    vm --> ci_logs
```

## Callback Contract

Every orchestrated child workflow accepts the same internal callback fields. The child workflow computes an aggregate result from `needs`, then dispatches `ci.yml` so the state machine can proceed. `state` is the workflow display name from `github.workflow`, not necessarily the filename; for example, the installer reports `yubiOS mkosi-installer`, which is the exact state matched by current `ci.yml`.

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
