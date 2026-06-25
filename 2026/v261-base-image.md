# v261 base-image bump
Find post-June-19 fedora-bootc:45 digest, update Containerfile FROM, verify systemd>=261 and pam-u2f>=1.3.1, update README.md + ADR.md.

Commands:
```sh
docker buildx imagetools inspect quay.io/fedora/fedora-bootc:45
docker run --rm <new-digest> systemd --version
```
Gate: CONFIG_BPF_LSM=y verification before RestrictFileSystemAccess= (issue #18).
See ADR-015, ADR-016.