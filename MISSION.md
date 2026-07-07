# Mission

**To build AI resilient systems using AI.**

yubiOS is built, reviewed, and tested with heavy AI assistance. That is the point, and the paradox: the same class of tools that accelerate development can also generate plausible-looking code, forge provenance, and automate supply-chain attacks at scale. So the systems we ship must hold up even when the thing that built them cannot be trusted.

The answer is structural, not procedural. Nothing in yubiOS asks you to trust an author, human or machine. Every layer is verified before it runs:

- Every base image and CI action is digest-pinned ([PINNED.md](PINNED.md)); mutable tags are rejected by build policy ([yubiOS.rego](yubiOS.rego)).
- Every build passes an OPA/Rego supply-chain gate before a single layer executes, and ships with SLSA provenance and SBOM attestations.
- Every byte of `/usr` is validated on read by dm-verity; every UKI is signed by a key on hardware the owner physically holds.
- Every architectural decision is recorded with rationale and sources ([ADR.md](ADR.md)), and every attack surface is mapped to a control ([MITIGATE.md](MITIGATE.md)).

An AI resilient system is one where a poisoned contribution, wherever it came from, either fails verification or never had the authority to matter.

## With great power, comes great responsibility

A root of trust is concentrated power. Whoever holds the signing key, the ROTPK, or the RPMB write key holds the machine. yubiOS's stance is that this power belongs to the owner of the hardware, and to no one else: not the OEM, not the SoC vendor, not us.

That responsibility cuts inward too. Irreversible operations (fuse burns, RPMB key writes, Secure Boot key enrollment) are treated like production secrets: documented, rehearsed on sacrificial hardware, never automated past a human gate. Recovery paths are mandatory, because locking an owner out of their own machine is a failure of exactly the power we claim to return to them.

## Don't be evil

yubiOS is security infrastructure, and security tooling is dual-use. We publish our threat models, our mitigations, and our gaps ([MITIGATE.md](MITIGATE.md) includes an honest "what we cannot fully prevent" table). We do not ship dark patterns, phone-home telemetry, or trust anchors the owner cannot audit and replace. When a design choice trades user control for convenience, control wins.

If a feature ever needs a security exception to exist, it gets cut.

---

*No TPM. No OEM. No trust anchors you don't control.*
