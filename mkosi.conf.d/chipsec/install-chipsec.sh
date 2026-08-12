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
# # ./this-script.sh [args]
# # See docs/ARCHITECTURE.md for context.


## Guidelines

- Match the conventions in `docs/STYLE.md`
- See sibling files in this directory for the surrounding context


# ## Verification
# # Run the relevant CI workflow (see docs/CI_MAP.md).


## Composition

- Sits next to sibling files in this directory; consult them for surrounding context
- For the full yubiOS dependency graph, see `docs/ARCHITECTURE.md`


# ## Changelog
# # 2026-08-12 -- RSI cycle-4 new-idea experiment (primitive changelog).


## References

- yubiOS repo: `yubi-OS/yubiOS`
- Architecture: `docs/ARCHITECTURE.md`
- See root `lenses.json` and `new-ideas-2026-08-12.md`


## Anti-patterns

- Don't claim structure without a null (per `curved-corpus-create`)
- Don't report pi_T as a property of the historical corpus (per `curve-compass-skill`)
