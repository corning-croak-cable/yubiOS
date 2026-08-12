#!/bin/bash
# scripts/install.sh — install ffmpeg + yt-dlp on the target box, create /tmp/audio/queue/
# Idempotent: safe to re-run. Requires sudo NOPASSWD.
set -euo pipefail

echo "=== apt-get update ==="
sudo -n apt-get update -qq

echo "=== apt-get install ffmpeg ==="
if ! command -v ffmpeg >/dev/null 2>&1; then
  sudo -n DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ffmpeg
else
  echo "ffmpeg already installed: $(ffmpeg -version 2>&1 | head -1)"
fi

echo "=== install yt-dlp ==="
if [ ! -x /usr/local/bin/yt-dlp ]; then
  sudo -n curl -fsSL --max-time 120 \
    -o /usr/local/bin/yt-dlp \
    https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp
  sudo -n chmod +x /usr/local/bin/yt-dlp
else
  echo "yt-dlp already at /usr/local/bin/yt-dlp"
fi

echo "=== fix yt-dlp shebang (source dist needs Python 3.10+) ==="
# The source distribution's shebang is #!/usr/bin/env python3.
# Resolve what that points to on this box and rewrite to absolute path,
# so the dist works regardless of which python3.x is on PATH.
PYTHON3_PATH="$(readlink -f "$(command -v python3)")"
echo "python3 resolves to: $PYTHON3_PATH"
if ! sudo -n head -1 /usr/local/bin/yt-dlp | grep -qF "$PYTHON3_PATH"; then
  sudo -n sed -i "1c#!$PYTHON3_PATH" /usr/local/bin/yt-dlp
fi
echo "yt-dlp shebang now: $(sudo -n head -1 /usr/local/bin/yt-dlp)"

echo "=== verify ==="
ffmpeg -version 2>&1 | head -1
yt-dlp --version

echo "=== create queue dir ==="
mkdir -p /tmp/audio/queue
chmod 755 /tmp/audio/queue

echo
echo "=== install complete ==="
echo "next: push scripts/queue_player.sh + scripts/queue.sh to /tmp/audio/queue/"
echo "      then: nohup /tmp/audio/queue/queue_player.sh </dev/null >/dev/null 2>&1 &"
echo "      then: echo '<youtube-url>' >> /tmp/audio/queue/queue.txt"


## New Ideas -- cycle 2 (lens format)

This file was processed by the RSI cycle-2 lens generator (curve-compass-skill v1.1.0 + curved-corpus-create v1.1.0). Each cycle-2 patch IS a concrete experiment with a measurable delta -- not a templated section. The lens below documents the measured dynamics; the patch is the lens, not prose about the file.

```json
{
  "lens": "L445",
  "file": "skills/radio-queue/scripts/install.sh",
  "hypothesis": "skills/radio-queue/scripts/install.sh covers all 9 primitives in the internal-big-picture basis",
  "method": "9-D primitive binarization (purpose, examples, guidelines, constraints, verification, composition, changelog, references, anti-patterns) + chordal distance to ideal pole on Fibonacci lattice",
  "parameters": {
    "basis": "internal-big-picture",
    "d": 9,
    "seed": 20260812
  },
  "delta": {
    "k": 4,
    "missing_primitives": [
      "examples",
      "guidelines",
      "changelog",
      "references",
      "anti-patterns"
    ],
    "chordal_resid": 0.0
  },
  "verdict": "PARTIAL",
  "score": 22,
  "caveat": "binarization is heuristic; a stricter regex pass might surface sub-primitives"
}
```
