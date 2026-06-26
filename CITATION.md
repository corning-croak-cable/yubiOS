# Citing yubiOS

If you reference yubiOS in academic or technical work, please cite the project and,
where relevant, the primary sources below that ground its design.

## Cite this project

> Latuu, J. (2026). *yubiOS: A FIDO2-first immutable operating system with a hardware
> security key as the sole root of trust.* yubi-OS. https://github.com/yubi-OS/yubiOS

```bibtex
@software{yubios2026,
  author  = {Tchatalbachian, Shant},
  title   = {{yubiOS}: A {FIDO2}-first immutable operating system with a
             hardware security key as the sole root of trust},
  year    = {2026},
  url      = {https://github.com/yubi-OS/yubiOS},
  note    = {YubiKey replaces the TPM at every trust boundary:
             Secure Boot signing, disk encryption, SSH, and PAM}
}
```

---

## Primary sources grounding the design

### Authentication: FIDO2 / WebAuthn / CTAP

- W3C. *Web Authentication: An API for accessing Public Key Credentials (WebAuthn) — Level 2.* W3C Recommendation, 2021. https://www.w3.org/TR/webauthn-2/
- FIDO Alliance. *Client to Authenticator Protocol (CTAP) 2.1.* FIDO Alliance Proposed Standard, 2021. https://fidoalliance.org/specs/fido-v2.1-ps-20210615/
- IETF. Pechanec, J. & Moustakas, D. *RFC 7512: The PKCS #11 URI Scheme.* 2015. https://www.rfc-editor.org/rfc/rfc7512

### Trusted boot, measured boot, and platform integrity

- Arbaugh, W. A., Farber, D. J., & Smith, J. M. (1997). *A Secure and Reliable Bootstrap Architecture.* IEEE Symposium on Security and Privacy. (Foundational chain-of-trust boot.)
- Sailer, R., Zhang, X., Jaeger, T., & van Doorn, L. (2004). *Design and Implementation of a TCG-based Integrity Measurement Architecture.* USENIX Security Symposium. (IMA / PCR measurement.)
- Parno, B., McCune, J. M., & Perrig, A. (2011). *Bootstrapping Trust in Modern Computers.* Springer. (Survey of TPM-rooted trust; motivates the YubiKey-as-RoT substitution.)
- Trusted Computing Group. *TPM 2.0 Library Specification.* https://trustedcomputinggroup.org/resource/tpm-library-specification/
- UEFI Forum. *Unified Extensible Firmware Interface (UEFI) Specification, v2.10.* (Secure Boot `db`/`KEK`/`PK`, Authenticode PE signing.) https://uefi.org/specifications

### Firmware-supply-chain hardening (NIST)

- NIST SP 800-147. *BIOS Protection Guidelines.* https://csrc.nist.gov/pubs/sp/800/147/final
- NIST SP 800-155 (Draft). *BIOS Integrity Measurement Guidelines.*
- NIST SP 800-193. *Platform Firmware Resiliency Guidelines.* https://csrc.nist.gov/pubs/sp/800/193/final

### Image-based OS, immutability, and the systemd model

- Poettering, L. *Fitting Everything Together.* 0pointer.net, 2022. https://0pointer.net/blog/fitting-everything-together.html
- Poettering, L. *Brave New Trusted Boot World.* 0pointer.net, 2022. https://0pointer.net/blog/brave-new-trusted-boot-world.html
- systemd project. *systemd-sbsign(1), systemd-cryptenroll(1), systemd-homed(8), systemd-repart(8), Unified Kernel Image (UKI) & Discoverable Partitions Specification.* https://www.freedesktop.org/software/systemd/man/latest/
- Linux kernel. *fs-verity: read-only file-based authenticity protection* and *dm-verity.* https://www.kernel.org/doc/html/latest/filesystems/fsverity.html

### Disk encryption

- Broz, M. et al. *LUKS2 On-Disk Format Specification.* cryptsetup project. https://gitlab.com/cryptsetup/cryptsetup
- Fruhwirth, C. (2005). *New Methods in Hard Disk Encryption.* Institute for Computer Languages, TU Wien. (LUKS design rationale, XTS/sector tweaking.)

### Software supply chain & provenance

- OpenSSF. *SLSA: Supply-chain Levels for Software Artifacts (v1.0).* https://slsa.dev/spec/v1.0/
- Sigstore project. *cosign / Rekor transparency log.* https://docs.sigstore.dev/

### Referenced security advisory

- Yubico. *YSA-2025-01: pam-u2f partial authentication bypass (CVE-2025-23013).* https://www.yubico.com/support/security-advisories/ysa-2025-01/

---

_Internal design rationale lives in [ADR.md](ADR.md); the firmware-supply-chain threat
model this project closes is in [MITIGATE.md](MITIGATE.md); the post-launch ARM64
secure-world plan is in [FUTURE.md](FUTURE.md)._
