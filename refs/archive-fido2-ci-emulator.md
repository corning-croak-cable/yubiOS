> **Archived research snapshot** synced from the assistant knowledge base (`documents/github-yubios-KS9n5GAT/knowledge/`) on 2026-07-23. May predate current specs — treat `PINNED.md` and the dated `refs/*` notes as the live source of truth; this is background research context only.

---

# FIDO2 Software Emulator for CI — Research Findings
_Updated: 2026-05-10_

## Verdict: Viable

GitHub Actions hosted runners support `modprobe vhci-hcd` and `/dev/uhid`.
Both USB/IP and UHID-based emulators work without hardware.

---

## Options

| Tool | Mechanism | Language | Best for |
|---|---|---|---|
| **virtual-fido** | USB/IP (`vhci-hcd`) | Go | General CTAP2, persistent creds, most maintained |
| **passless** | UHID (`/dev/uhid`) | Rust | Passkeys, CTAP 2.1, native Linux feel |
| **softfido** | USB/IP + SoftHSM | Rust | PKCS#11 signing in CI (yubiOS Secure Boot path) |

**Recommendation for yubiOS CI:**
- **`virtual-fido`** for LUKS2 + PAM U2F enrollment tests (hidraw-based FIDO2)
- **`softfido`** for mkosi PKCS#11 signing tests (PIV simulation via SoftHSM)

---

## GitHub Actions setup

```yaml
- name: Load USB/IP kernel module
  run: |
    sudo modprobe vhci-hcd
    sudo modprobe usbip-core

- name: Start virtual-fido emulator
  run: |
    go install github.com/standard-library/virtual-fido/cmd/virtual-fido@latest
    sudo ~/go/bin/virtual-fido &
    sleep 2  # wait for /dev/hidrawX to appear

- name: Verify FIDO2 device visible
  run: fido2-token -L   # should list the virtual device

- name: Run yubiOS enrollment test (mocked device)
  run: bats tests/unit/   # unit tests mock fido2-token anyway

- name: Run LUKS enrollment e2e (virtual device)
  run: sudo systemd-cryptenroll --fido2-device=auto /tmp/test.luks
```

For UHID path (passless):
```yaml
- name: Check /dev/uhid
  run: ls -la /dev/uhid   # available on ubuntu-24.04 runners

- name: Start passless
  run: |
    cargo install passless
    sudo passless &
```

---

## SoftHSM for PKCS#11 signing (mkosi profile CI)

For CI builds of the yubiOS mkosi profile (Secure Boot signing without a real YubiKey):

```bash
# Install
sudo dnf install softhsm opensc

# Init token
softhsm2-util --init-token --slot 0 --label "yubiOS-ci" --pin 1234 --so-pin 1234

# Generate EC key
pkcs11-tool --module /usr/lib64/libsofthsm2.so \
  --login --pin 1234 \
  --keypairgen --key-type EC:prime256v1 \
  --label "sb-key" --usage-sign

# Export self-signed cert
# ... use openssl with pkcs11 engine to self-sign ...

# Use in mkosi
mkosi --profile yubiOS \
  --secure-boot-key-source=engine:pkcs11 \
  --secure-boot-key="pkcs11:token=yubiOS-ci;object=sb-key;type=private" \
  --secure-boot-certificate=mkosi.secure-boot.pem \
  build
```

---

## Sources
- https://github.com/standard-library/virtual-fido — USB/IP Go emulator (active 2025)
- https://github.com/pando85/passless — UHID Rust emulator (passkeys, CTAP 2.1)
- `modprobe vhci-hcd` confirmed working on `ubuntu-24.04` GitHub-hosted runners
- SoftHSM2 available in Fedora 42, Ubuntu 24.04, Debian 12 packages
