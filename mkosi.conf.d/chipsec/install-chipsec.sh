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

# ## Examples
# # Reading the file with no arguments shows the help text.
# # See docs/ARCHITECTURE.md for where this fits in yubiOS.

# ## Guidelines
# # Follow the conventions in docs/STYLE.md. Match the structure of surrounding files.

# ## Verification
# # Run the relevant CI workflow on a draft branch (see docs/CI_MAP.md); the result is the gate.

# ## Changelog
# # 2026-08-12 -- primitive-closure pass via curve-compass-skill + curved-corpus-create (this PR).

# ## References
# # yubiOS repo: yubi-OS/yubiOS
# # See docs/ARCHITECTURE.md and the two new skills in skills/github-yubios-KS9n5GAT/.

# ## Anti-patterns
# # Don't claim structure without a null (see curved-corpus-create skill).
# # Don't report pi_T statistics as properties of the historical corpus.

