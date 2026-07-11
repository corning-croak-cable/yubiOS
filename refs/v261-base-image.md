# v261 base-image bump

Status: completed; keep this note as the historical checklist for future base-image refreshes. Current approved image digests live only in [../PINNED.md](../PINNED.md).

## Current source of truth

- `PINNED.md` owns the live `quay.io/fedora/fedora-bootc:45` OCI index digest.
- `fetch-fedora-bootc-manifest.yml` is the workflow used to refresh that digest.
- `Containerfile` must use the multi-arch index digest from `PINNED.md`, not a copied value from an ADR or old PR note.

## Completed gate

The original v261 gate was:

```sh
docker buildx imagetools inspect quay.io/fedora/fedora-bootc:45
docker run --rm <new-digest> systemd --version
```

The base bump unblocked `ConditionSecurity=measured-os`, `systemd-tpm2-swtpm.service`, and the current yubiOS enrollment-unit hardening work.

## Consistency note

Do not conflate these two systemd controls:

- `RestrictFileSystems=`: older BPF-LSM filesystem-type allow/deny control. yubiOS uses `RestrictFileSystems=~@network` in the enrollment unit.
- `RestrictFileSystemAccess=`: v261 control for restricting execution to signed and verified dm-verity-backed filesystems.

Future work may evaluate the v261 `RestrictFileSystemAccess=` control, but the current shipped unit uses `RestrictFileSystems=`.
