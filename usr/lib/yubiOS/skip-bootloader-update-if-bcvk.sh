#!/usr/bin/env bash
set -euo pipefail

[ -r /proc/mounts ] || exit 0

if awk '$2 == "/" && $3 == "virtiofs" { found=1 } END { exit found ? 0 : 1 }' /proc/mounts; then
  echo "bcvk ephemeral virtiofs root detected; skipping bootloader-update.service."
  exit 1
fi

exit 0


## New Ideas -- cycle 3 (lens external)

This file's lens is **L538** in `lenses.json` (score 0/50, verdict **NO**, k=0/9). Full experiment: hypothesis `usr/lib/yubiOS/skip-bootloader-update-if-bcvk.sh covers all 9 primitives in the internal-big-picture basis`, method `9-D primitive binarization (purpose, examples, guidelines, constraints, verifica...`. See root `new-ideas-2026-08-12.md` for the cycle-3 summary.
