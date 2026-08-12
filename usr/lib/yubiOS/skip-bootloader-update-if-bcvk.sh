#!/usr/bin/env bash
set -euo pipefail

[ -r /proc/mounts ] || exit 0

if awk '$2 == "/" && $3 == "virtiofs" { found=1 } END { exit found ? 0 : 1 }' /proc/mounts; then
  echo "bcvk ephemeral virtiofs root detected; skipping bootloader-update.service."
  exit 1
fi

exit 0


# ## Purpose
# # set -euo pipefail
# #
# # Added by RSI cycle-4 new-idea generator -- hypothesis: closing primitive p0 via purpose comment.


# ## Examples
# # ./this-script.sh [args]
# # See docs/ARCHITECTURE.md for context.


## Guidelines

- Match the conventions in `docs/STYLE.md`
- See sibling files in this directory for the surrounding context


## Constraints

- Out of scope: changes to `papers/` (historical info) or `.github/workflows/*.yml` (CI workflows)


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
