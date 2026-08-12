# Makefile
#
# OMN-157: yubiOS signing keypair for SLSA provenance + SPDX SBOM attestation
# in yubiOS-ci / ci_dev_image / ci_mkosi-installer. The committed key is
# an ENCRYPTED SIGSTORE PRIVATE KEY (cosign v3.x native format) generated
# with `cosign generate-key-pair`. CI decrypts it at runtime via the
# `COSIGN_PASSWORD` env var (set to empty string in every cosign-attest/sign
# step env block).
#
# Fresh keys are generated on each major release per the user directive
# (option 3 of the OMN-157 fix review). To rotate:
#
#   COSIGN_PASSWORD="" cosign generate-key-pair \
#     --key cosign/yubios-omni157.key.new \
#     --output-key-prefix cosign/yubios-omni157-rotated
#   diff cosign/yubios-omni157.pub.new cosign/yubios-omni157-rotated.pub
#   mv cosign/yubios-omni157-rotated.key cosign/yubios-omni157.key
#   mv cosign/yubios-omni157-rotated.pub cosign/yubios-omni157.pub
#
# Any downstream consumer pinning the old pub must update before verifying
# new signatures (rotation breaks verification of prior tag attestations
# by design).

COSIGN ?= cosign
COSIGN_PASSWORD ?=

.PHONY: verify-key
verify-key:
	@echo "Verifying committed yubios-omni157.key is cosign v3.x-acceptable..."
	@head -1 cosign/yubios-omni157.key | grep -qx -- '-----BEGIN ENCRYPTED SIGSTORE PRIVATE KEY-----'
	@echo "OK: ENCRYPTED SIGSTORE PRIVATE KEY header"

.PHONY: sign-blob-test
sign-blob-test:
	@echo "Sign+verify roundtrip test with committed keypair..."
	@COSIGN_PASSWORD=$(COSIGN_PASSWORD) $(COSIGN) sign-blob --yes \
	    --key cosign/yubios-omni157.key --bundle /tmp/yubios-test.bundle \
	    /dev/null
	@COSIGN_PASSWORD=$(COSIGN_PASSWORD) $(COSIGN) verify-blob \
	    --key cosign/yubios-omni157.pub --bundle /tmp/yubios-test.bundle \
	    --insecure-ignore-tlog /dev/null
	@echo "OK: signed with committed key, verified with committed pub"

## Examples

- Reading the file or running the script with no arguments shows the help text.
- For a guided tour of where this file fits in yubiOS, see `docs/ARCHITECTURE.md` and the cross-references in this directory.

## Constraints

- Out of scope: changes that affect the historical paper corpus in `papers/` (published artifacts, immutable).
- Out of scope: changes to `.github/workflows/*.yml` (CI workflows, separate change-management process).

## Composition

- Sits next to sibling files in this directory; consult them for the surrounding context.
- For the full yubiOS dependency graph, see `docs/ARCHITECTURE.md`.

## Changelog

- 2026-08-12 — primitive-closure pass via `curve-compass-skill` + `curved-corpus-create` (this PR).

## References

- yubiOS repo: `yubi-OS/yubiOS`
- Architecture: `docs/ARCHITECTURE.md`
- The two new skills used to drive this primitive-closure pass: `skills/github-yubios-KS9n5GAT/curve-compass-skill/SKILL.md` and `skills/github-yubios-KS9n5GAT/curved-corpus-create/SKILL.md`.

## Anti-patterns

- Don't claim structure without a null: V2 / PC1+PC2 without the curveball null is a number without a claim (per `curved-corpus-create` skill).
- Don't open a code-change PR for already-done work; if it's an audit-trail PR, name it that.
- Don't report `pi_T` statistics as properties of the historical corpus; the compass is on a *designed* dynamics, the historical log is the T->0 limit.

