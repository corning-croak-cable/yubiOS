# yubios — FIDO2-first immutable OS image (Fedora base)
# Build: podman build -t yubios .
# Source: bootc design https://github.com/bootc-dev/bootc
# Source: particleos ethos https://github.com/systemd/particleos

FROM quay.io/fedora/fedora-bootc:latest

# ── YubiKey and FIDO2 stack ──────────────────────────────────────────────
# libfido2:       FIDO2/CTAP2 library; used by systemd-cryptenroll, OpenSSH, pam-u2f
# yubikey-manager: ykman CLI for PIV, FIDO2, OATH management
# yubico-piv-tool: PIV operations for Secure Boot signing (slot 9c)
# opensc:          PKCS#11 middleware; sbsign uses this to talk to YubiKey PIV
# pam-u2f:         PAM module for FIDO2/U2F; requires >= 1.3.1 (CVE-2025-23013)
#                  Source: https://www.yubico.com/support/security-advisories/ysa-2025-01/
# pcsc-lite:       PC/SC daemon; needed for PIV/CCID interface
# sbsigntool:      sbsign for Secure Boot UKI signing via PKCS#11
# tpm2-tools:      kept for compatibility; not used as trust anchor
RUN dnf install -y \
      libfido2 \
      libfido2-devel \
      yubikey-manager \
      yubico-piv-tool \
      opensc \
      pam-u2f \
      pam-u2f-devel \
      pcsc-lite \
      pcsc-lite-ccid \
      sbsigntool \
      sbctl \
      tpm2-tools \
      tpm2-tss \
      cryptsetup \
      openssh-clients \
      openssh-server \
      fido2-tools && \
    dnf clean all

# ── Overlay yubios config tree ───────────────────────────────────────────
COPY usr/ /usr/

# ── Permissions for enrollment scripts ───────────────────────────────────
RUN chmod +x /usr/lib/yubios/*.sh /usr/bin/yubios-enroll*

# ── Apply systemd presets ─────────────────────────────────────────────────
RUN systemctl preset-all

# ── PAM: create u2f_keys directory ───────────────────────────────────────
RUN mkdir -p /etc/yubico && touch /etc/yubico/u2f_keys && chmod 600 /etc/yubico/u2f_keys
