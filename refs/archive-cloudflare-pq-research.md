> **Archived research snapshot** synced from the assistant knowledge base (`documents/github-yubios-KS9n5GAT/knowledge/`) on 2026-07-23. May predate current specs — treat `PINNED.md` and the dated `refs/*` notes as the live source of truth; this is background research context only.

---

# Cloudflare Post-Quantum Key Agreement
_Source: https://pq.cloudflareresearch.com/ — Refreshed: June 23, 2026_

## Current Deployment Status

Cloudflare has enabled hybrid post-quantum key agreement on essentially all domains they serve, including origin-to-Cloudflare connections (rolling out).

Reference: https://blog.cloudflare.com/pq-2025 — "State of the Post-Quantum Internet"

---

## Deployed Key Agreements (TLSv1.3 + HTTP/3 / QUIC)

| Key Agreement | TLS Identifier | Status |
|---|---|---|
| **X25519MLKEM768** | `0x11ec` | **Recommended** (current standard) |
| X25519Kyber768Draft00 | `0x6399` | Obsolete |
| ~~X25519Kyber512Draft00~~ | ~~`0xfe30`~~ | Removed |

**Migration**: Kyber768Draft00 (`0x6399`) was the original deployment. X25519MLKEM768 is the IETF-standardized replacement. New implementations should target `0x11ec`.

Standard: https://datatracker.ietf.org/doc/draft-kwiatkowski-tls-ecdhe-mlkem

---

## What is X25519MLKEM768?

Hybrid KEM combining:
- **X25519** — classical ECDH (for classical adversaries)
- **ML-KEM-768** (CRYSTALS-Kyber Level 3) — lattice-based KEM (for quantum adversaries)

Security: secure if either X25519 or ML-KEM-768 is secure. Harvest-now-decrypt-later threat model addressed.

---

## Relevance to yubiOS

### TLS/mTLS for yubiOS services
When yubiOS services communicate over TLS (e.g. attestation endpoints, update server, admin API):
- Use TLS libraries with X25519MLKEM768 support
- BoringSSL (used by Chrome): yes
- OpenSSL 3.5+: yes (ML-KEM support)
- GnuTLS 3.8.5+: partial

### YubiKey + PQ
Current YubiKey hardware does NOT support ML-KEM natively (PIV + FIDO2 are classical). yubiOS threat model:
- YubiKey provides hardware-bound authentication (unprovable key compromise)
- PQ layer on top handles harvest-now attacks on transport
- Combine: YubiKey auth + X25519MLKEM768 TLS = layered protection

### Software support check
https://developers.cloudflare.com/ssl/post-quantum-cryptography/pqc-support/

---

## References

- Cloudflare PQ status: https://pq.cloudflareresearch.com/
- Blog post (2025): https://blog.cloudflare.com/pq-2025
- Large ClientHello breakage (tldr.fail): https://tldr.fail/
- IETF draft: https://datatracker.ietf.org/doc/draft-kwiatkowski-tls-ecdhe-mlkem
- Contact: ask-research@cloudflare.com
