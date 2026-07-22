# Reproducible build contract — 2026-07-22

## Scope

This pass turns reproducibility from a pinning aspiration into an executable
test for the production and TEST-only dev OCI subjects. It also applies every
confirmed deterministic control to the installer and ARM64 firmware paths, but
does not claim equality for cryptographic envelopes that intentionally generate
new keys or signatures.

The canonical build identity is the selected yubiOS commit plus its committer
timestamp. `scripts/lib/reproducible-build.sh` derives and validates that pair
once, then exports the same values to local builds and GitHub Actions. A caller
cannot silently assign a different `SOURCE_DATE_EPOCH` to the same revision.

## Implemented contract

| Layer | Control | Evidence |
|---|---|---|
| Build engine | Buildx client and BuildKit daemon are independently pinned; every `docker-container` builder names the daemon image from [PINNED.md](../PINNED.md). | Static workflow inspection plus `buildx inspect --bootstrap` during builds. |
| OCI metadata | Bake passes `SOURCE_DATE_EPOCH` and `BUILDKIT_MULTI_PLATFORM`, fixes the OCI `created` label, clamps layer mtimes with `rewrite-timestamp`, and fixes compression/exporter compatibility settings. | Pinned Buildx `bake --print` and config assertions in the two-build proof. |
| Core contexts | `.dockerignore` admits only the production/dev Dockerfiles and their required tracked inputs. | Runner downloads and workspace debris cannot enter the image context. |
| Production/dev proof | `scripts/verify-reproducible-images.sh` builds the real target twice with separate pinned builders, no cache, and no default attestations, then compares the complete OCI-layout Merkle content. Bake output access is explicitly limited to each run's temporary directory; generated DNF and ldconfig auxiliary state is removed, Python bytecode uses single-worker checked-hash compilation, and Rust debug paths are remapped. A mismatch prints config and layer-member diagnostics before failing. | Blocking ARM64 steps in `yubiOS-ci.yml` and `ci_dev_image.yml`; JSON evidence is retained for 30 days. |
| mkosi | Commit epoch, architecture-scoped deterministic seed, no incremental cache, Dracut reproducible mode, fixed zstd worker count, normalized payload metadata, and sorted SHA-256 manifest. | Remote and Ubuntu 26.04 local paths use the same settings. |
| Firmware | Commit epoch reaches EDK2, U-Boot, and OP-TEE; TF-A receives an explicit timestamp and build string; prepared payload metadata is normalized and checksummed. | Remote and local build manifests record revision, epoch, component refs, and signature boundary. |

The proof compares an unpacked OCI layout rather than `docker image save` or a
GitHub artifact ZIP. Those transport wrappers are not stable equality oracles.
Default provenance is disabled only inside the byte-comparison lane; published
attestations remain a separate envelope whose subject digest must identify the
already-proven image.

## Deliberate boundaries

The following bytes are not yet allowed to support a reproducibility claim:

- The installer creates a fresh non-production SoftHSM RSA key and certificate,
  and embeds both the signed UKI and certificate. Signature validity is checked,
  but that random envelope is explicitly excluded from byte equality.
- QEMU TF-A uses `CREATE_KEYS=1`; certificate serials, validity, and RSA-PSS
  signatures vary. Component payloads must be compared before CoT signing or a
  public fixed test fixture must be introduced before this becomes a gate.
- Fedora and Debian packages are still resolved from live repositories. The
  two-build gate proves equality against the package state observed during that
  run, not rebuildability months later. Immutable repository snapshots and an
  exact package/toolchain closure remain required.
- RK3588 cannot enter reproducibility evidence until the external DDR/TPL blob
  has an approved immutable digest in `PINNED.md`.
- Pinned EDK2 still generates random stack-cookie values in a clean BaseTools
  build. Firmware equality must either preseed those public values or fix the
  pinned fork before StandaloneMM can be a blocking digest oracle.

Run IDs, wall-clock timestamps, temporary paths, and local/CI labels have been
removed from byte-bearing installer and firmware manifests. CI run identity
belongs in workflow summaries or provenance, not inside intended payloads.

## Local proof

On the supported Ubuntu 26.04 host, both proof modes run inside the same pinned
DHI, rootless Docker, Buildx, BuildKit, policy, and Bake graph as CI:

```sh
./scripts/build-local-images.sh repro-production
./scripts/build-local-images.sh repro-dev
```

Successful reports are written under `repro-evidence/`. A mismatch is a hard
failure; preserve the two OCI layouts with `KEEP_REPRO_OUTPUT=1` when invoking
the inner verifier directly and use `diffoscope` for diagnosis.

## Primary sources

- [SOURCE_DATE_EPOCH specification](https://reproducible-builds.org/specs/source-date-epoch/)
- [BuildKit reproducible-build documentation](https://github.com/moby/buildkit/blob/master/docs/build-repro.md)
- [Docker reproducible-build guidance](https://docs.docker.com/build/ci/github-actions/reproducible-builds/)
- [Docker OCI/image exporter options](https://docs.docker.com/build/exporters/oci-docker/)
- [mkosi `SourceDateEpoch=` and `Seed=`](https://github.com/systemd/mkosi/blob/main/mkosi/resources/man/mkosi.1.md)
- [U-Boot reproducible builds](https://docs.u-boot.org/en/stable/build/reproducible.html)
- [TF-A build options](https://github.com/ARM-software/arm-trusted-firmware/blob/master/docs/getting_started/build-options.rst)
- [RPM 4.18 deterministic transaction-clock support](https://rpm.org/wiki/Releases/4.18.0)
- [GNU tar reproducibility guidance](https://www.gnu.org/software/tar/manual/html_node/Reproducibility.html)
- [GitHub artifact permission caveat](https://github.com/actions/upload-artifact/blob/main/README.md)
