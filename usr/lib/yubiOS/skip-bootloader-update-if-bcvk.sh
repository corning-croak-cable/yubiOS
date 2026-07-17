#!/usr/bin/env bash
set -euo pipefail

[ -r /proc/mounts ] || exit 0

if awk '$2 == "/" && $3 == "virtiofs" { found=1 } END { exit found ? 0 : 1 }' /proc/mounts; then
  echo "bcvk ephemeral virtiofs root detected; skipping bootloader-update.service."
  exit 1
fi

exit 0
