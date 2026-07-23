> **Archived research snapshot** synced from the assistant knowledge base (`documents/github-yubios-KS9n5GAT/knowledge/`) on 2026-07-23. May predate current specs — treat `PINNED.md` and the dated `refs/*` notes as the live source of truth; this is background research context only.

---

# bootc-dev Org Repos
_Fetched: May 10, 2026 — Source: https://github.com/orgs/bootc-dev/repositories_

## Key Repos (by relevance to yubiOS)

### bcvk ⭐ 98 | Rust | Active
https://github.com/bootc-dev/bcvk
Bootc virtualization kit. Run bootc container images as ephemeral or persistent VMs using QEMU + virtiofsd. Unprivileged (rootless podman). Core dev/test tool for yubiOS.
- Topics: bootc, virtualization
- Lead: cgwalters
- Latest: v0.13.0 (2026-03)

### bootc ⭐ 2041 | Rust | Very Active
https://github.com/bootc-dev/bootc
The core project. Boot and upgrade Linux systems from OCI container images. Transactional in-place updates via `bootc upgrade` / `bootc switch`. The foundation yubiOS runs on.

### podman-bootc ⭐ 66 | Go
https://github.com/bootc-dev/podman-bootc
Predecessor/companion to bcvk. Runs bootc images via podman machine. Less active than bcvk but has useful patterns (rootful vs rootless discussions).

### ocidir-rs ⭐ 19 | Rust
https://github.com/bootc-dev/ocidir-rs
Low-level Rust library for working with OCI directories. Used internally by bcvk and bootc for image layer manipulation.

### containers-image-proxy-rs ⭐ 24 | Rust
https://github.com/bootc-dev/containers-image-proxy-rs
Rust library for proxying container image operations (pull, inspect). Used by bootc to fetch OCI images from registries.

### canon-json-rs ⭐ 2 | Rust
https://github.com/bootc-dev/canon-json-rs
Canonical JSON for Rust — compatible with Docker and TUF canonical JSON implementations. Used for deterministic hashing of image manifests.

### jsonrpc-fdpass ⭐ 0 | Rust
https://github.com/bootc-dev/jsonrpc-fdpass
JSON-RPC with file descriptor passing (Unix socket + SCM_RIGHTS). Used for bcvk ↔ QEMU/virtiofsd IPC.

### jsonrpc-fdpass-go ⭐ 0 | Go
https://github.com/bootc-dev/jsonrpc-fdpass-go
Go implementation of the same JSON-RPC fdpass protocol.

### ci-sandbox ⭐ 1 | Dockerfile
https://github.com/bootc-dev/ci-sandbox
CI sandbox container for bootc-dev workflows.

### infra ⭐ 1 | Python
https://github.com/bootc-dev/infra
CI infrastructure scripts for the bootc-dev org.

### actions ⭐ 0
https://github.com/bootc-dev/actions
Reusable GitHub Actions for bootc-dev CI.

### homebrew-bcvk | Ruby | Fork
https://github.com/bootc-dev/homebrew-bcvk
Homebrew tap for installing bcvk on macOS.

### agent-skills ⭐ 0 | Python | Fork
https://github.com/bootc-dev/agent-skills
Agent skills for the bootc-dev org (fork of agentskills.io). Separate from yubi-OS/agent-skills.

### bootc-dev.github.io | HTML
https://github.com/bootc-dev/bootc-dev.github.io
bootc project website.

### .project
https://github.com/bootc-dev/.project
CNCF project metadata automation.

---

## Architecture Map (yubiOS perspective)

```
dhi.io/debian-base (pinned OCI)
        │
        ▼ Containerfile
  rootless podman build
        │
        ▼ OCI image → dhi.io/yubi-OS/yubiOS
        │
        ├─▶ bootc install to-disk (bare metal)
        │           ↑
        │       bcvk native-to-disk
        │
        ├─▶ bcvk ephemeral run (dev loop)
        │           ↑
        │       QEMU + virtiofsd + u2f-passthru
        │
        └─▶ bcvk to-disk (disk image for CI)
                    ↑
                bootc install to-disk (in ephemeral VM)
```

---

## Dependency Crate Graph (yubiOS → bootc-dev)

```
yubiOS bootc base
  └── bootc (bootc-dev/bootc)
        ├── ocidir-rs (OCI layer I/O)
        ├── containers-image-proxy-rs (registry pulls)
        └── canon-json-rs (manifest hashing)

yubiOS dev/test
  └── bcvk (bootc-dev/bcvk)
        └── jsonrpc-fdpass (QEMU IPC)
```

---

## Notes for yubiOS Work

- `bcvk` is the right tool for dev loop and CI disk image builds. `podman-bootc` is older/less maintained.
- `ocidir-rs` and `containers-image-proxy-rs` are internal dependencies — don't need to fork unless adding new OCI features.
- `canon-json-rs` matters for deterministic image digest computation.
- Watch `bootc` issues for LUKS+FIDO2 enrollment (#421, #477) — these are open upstream problems yubiOS needs to work around.
- bootc-dev has their own `agent-skills` fork — different from yours at yubi-OS/agent-skills.
