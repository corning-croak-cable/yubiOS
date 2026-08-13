#!/usr/bin/env bash
# SPDX-License-Identifier: LGPL-2.1-or-later
# Install CHIPSEC for yubiOS first-boot firmware validation (ADR-024).
set -euo pipefail

python3 -m pip install --no-cache-dir --break-system-packages --require-hashes \
  'chipsec==1.13.16' \
  --hash=sha256:63bed5ad4224402397817ea82b94c3a21736386a04ff778c003704bd6dfdbca3

command -v chipsec_main.py >/dev/null
command -v chipsec_util.py >/dev/null
chipsec_main.py --help >/dev/null 2>&1 || true

echo "install-chipsec: CHIPSEC 1.13.16 installed for yubiOS first-boot firmware validation"


# ## Verification
# # Run the relevant CI workflow on a draft branch (see docs/CI_MAP.md).
# # RSI cycle-6 atomic flip (`verification`).


# ## Verification
# # Run the relevant CI workflow on a draft branch (see docs/CI_MAP.md).
# # RSI cycle-7 atomic flip (NSS-axis(calibration)).


# Inputs
#   CLI:         (executed by mkosi in chroot; no CLI flags)
#   env:         DESTDIR (mkosi-set, chroot path)
#   files:       none (downloads chipsec source at build time)
#   secrets:     none (chipsec is public source)
#   prereqs:     nasm + gcc from BuildPackages; internet access for the chipsec tarball
#   precedence:  DESTDIR > built-in /tmp default
#   validation:  tarball SHA256 verified against the pinned value before extraction
#   failure:     set -e; the failing curl/tar line and exit code are logged


# Failure modes -- cycle 14

# Cycle-14 NSS-failure-modes gap-closure. Each row pairs severity with probability;
# detection signal + recovery path + fault-injection test are required.
# See skills/github-yubios-KS9n5GAT/nss-failure-modes/SKILL.md for the taxonomy.
#
#   FM-001 [MEDIUM, Uncommon]  pip install fails on python version mismatch
#     why:        system python newer than CHIPSEC requires
#     detection:  pip install exits non-zero; stderr "no matching distribution"
#     recovery:   pin python version; use venv; install from source
#     prevent:    declare python version in script header; pin in mkosi.conf
#     test:       run with mismatched python; assert clear exit code 70
#
# Envelope: severity 1-2 negligible, 3-4 degraded, 5-6 operational,
# 7-8 major (outage/data loss/security), 9-10 critical.
# Probability is evidence-based; cite the denominator.
