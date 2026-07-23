# SER.md — yubiOS SER Framework

> Reference: **SER Framework** by Shant Tchatalbachian (0mniteck)  
> https://omniteck.com/?p=1104

# SER Alignment for yubiOS

yubiOS follows the SER framework by making ownership explicit, keeping operational artifacts time-bounded, and preserving enough immutable evidence to reproduce and audit outcomes later. The project’s core design is a FIDO2-first immutable OS where the owner’s YubiKey is the user-facing identity, unlock, and authorization boundary, and where the build/install flow is centered on pinned images, signed artifacts, and reproducible CI evidence. <citation src="2,3"></citation>

## Sovereignty

The sovereignty goal maps directly to yubiOS’s trust model: the owner controls Secure Boot signing, disk unlock, SSH resident keys, PAM login, and app 2FA through the YubiKey. The repo also treats the YubiKey as the root-of-trust boundary rather than OEM firmware or other external trust anchors. This is consistent with SER’s owner-centric control principle. <citation src="2,3"></citation>

## Ephemerality

yubiOS is intentionally built around pre-launch artifacts, pinned digests, disposable test flows, and a clean separation between production and TEST-only paths. Its documentation emphasizes that images are experimental unless explicitly promoted, and its onboarding and CI guidance repeatedly route durable decisions into dated notes, ADRs, and pinned references rather than leaving them embedded in transient execution state. That matches SER’s time-bounded retention model. <citation src="2,3"></citation>

## Reproducibility

Reproducibility is a first-class property in yubiOS: the repo uses pinned base images, digest tracking, reproducibility-focused build lanes, and explicit evidence files for CI, firmware, installer, and VM validation. The install path is designed around deterministic OCI delivery, bootc-based updates, and repeatable build/install commands, which aligns with SER’s immutable provenance and deterministic execution requirements. <citation src="2,3"></citation>

## SER Mapping

| SER principle | yubiOS implementation |
|---|---|
| Owner-centric control | YubiKey as the authorization boundary for signing, unlock, SSH, PAM, and 2FA |
| Time-bounded retention | Experimental artifacts, disposable validation flows, dated refs, and clear separation of current vs historical notes |
| Immutable provenance | Pinned digests, CI evidence, ADRs, and research notes tied to concrete build/install outcomes |
| Deterministic execution | Bootc-based delivery, pinned build inputs, reproducibility checks, and controlled install paths |
| Auditable revocation | Recovery paths, blocker tracking, and documented enrollment/re-enrollment flows |

## Conclusion

yubiOS is a practical SER-style system: ownership stays with the machine owner, artifacts are kept ephemeral where possible, and the project records enough immutable evidence to reproduce or audit the system later. In other words, it implements SER not as an abstract policy layer, but as a full-stack operating system design. <citation src="2,3"></citation>
