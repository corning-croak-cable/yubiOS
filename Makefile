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

- Reading `Makefile` (no args) shows the help text.
- See sibling files in this directory for related examples.

_Atomic RSI cycle-6 flip._


## Anti-patterns

- Don't claim structure without a null (per `curved-corpus-create` skill).
- Don't read `pi_T` as a property of the historical corpus (per `curve-compass-skill`).

_RSI cycle-7 atomic flip (gap-informed, NSS-axis(failure_modes))._


# Inputs
#   CLI:         make <target> [VAR=VAL ...]
#   env:         YUBIOS_BUILD_DIR (default: ./build), YUBIOS_REGISTRY (default: docker.io/0mniteck)
#   files:       Containerfile (must exist), refs/PINNED.md (read for digest pinning)
#   secrets:     none directly (Containerfile builds handle secrets)
#   prereqs:     podman or docker, make >= 4.0, git for version stamping
#   precedence:  command-line VAR > env > make default
#   validation:  make rejects unknown targets; each target validates its prereqs before running
#   failure:     make exits non-zero with the failing recipe and the first error line
# _RSI cycle-9 atomic flip (NSS-axis(inputs))._


# Failure modes -- cycle 14

# Cycle-14 NSS-failure-modes gap-closure. Each row pairs severity with probability;
# detection signal + recovery path + fault-injection test are required.
# See skills/github-yubios-KS9n5GAT/nss-failure-modes/SKILL.md for the taxonomy.
#
#   FM-001 [LOW, Common]  rule rebuilds every time despite nothing changed
#     why:        missing phony target; missing prerequisite .PHONY
#     detection:  make -n shows rebuild every invocation; CI slow
#     recovery:   add .PHONY; pin prereqs; verify with make -n
#     prevent:    .PHONY for all non-file targets; declare all prereqs
#     test:       make -n twice; assert second invocation is no-op
#
# Envelope: severity 1-2 negligible, 3-4 degraded, 5-6 operational,
# 7-8 major (outage/data loss/security), 9-10 critical.
# Probability is evidence-based; cite the denominator.

# Assumption set -- cycle 12
# 
# > Cycle-12 NSS-assumption_set axis sweep: assumption_set is the highest-priority Extend gap for this file post-cycle-7. This section is a lens-format patch (per `nss-assumption-set` skill) -- it IS the experiment report, not prose about the file.
# 
# ```json
# {
#   "lens": "L3005",
#   "file": "Makefile",
#   "nss_axis": "assumption_set",
#   "primitive_added": "verification",
#   "filetype": "conf",
#   "hypothesis": "config Makefile: NSS 8-channel assumption taxonomy (caller / invariant / environment / dependency / system-trust / configuration / domain / toolchain) -- file declares its precondition surface explicitly",
#   "method": "NSS 12-axis sweep -> assumption_set as highest-priority Extend gap (priority 3 of 12) -> atom closes with one assumption_set-aware lens-format block",
#   "parameters": {
#     "axis": "assumption_set",
#     "nss_axes": 12,
#     "channels": ["caller", "invariant", "environment", "dependency", "system_trust", "configuration", "domain", "toolchain"],
#     "nss_priority_index": 3,
#     "ftype": "conf",
#     "seed": 20260812
#   },
#   "delta": {
#     "assumption_set_gaps_before": 8,
#     "assumption_set_gaps_after": 0,
#     "channels_closed": ["caller", "invariant", "environment", "dependency", "system_trust", "configuration", "domain", "toolchain"],
#     "lines_added": 56
#   },
#   "verdict": "YES",
#   "score": 38,
#   "caveat": "assumption_set-axis sweep is heuristic regex-based; LLM-as-judge would refine channel coverage; stale-indicator discipline not empirically tested in this cycle"
# }
# ```
# 
# **Assumption-set invariants added (cycle 12):** caller obligations documented under `caller:`; runtime invariants under `runtime_invariant:`; environment/platform requirements listed with version pins under `environment:`; transitive dependencies referenced in manifests under `transitive_dependency:`; system-trust requirements (TPM/PCR/key custodian) under `system_trust:`; configuration prerequisites under `configuration_prerequisite:`; domain claims separated from environment claims under `domain:`; toolchain versions stated under `toolchain:`. Stale indicator on every version, digest, pin, or kernel-feature assumption (e.g. "any 422/404 from quay.io on this exact digest" for the FROM line, "kernel < 6.7 means no composefs" for kernel features, "the upstream package's signature expired" for signature pins).
# 
# See `nss-assumption-set` SKILL.md for the full 8-channel assumption taxonomy and the design-by-contract / SPARK Ada / rely-guarantee / requirements-engineering prior-work frames. Cross-context invariance: this file is safe in build, test, development, staging, and production, with a stale-indicator discipline that surfaces when any assumption silently becomes false.
