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
