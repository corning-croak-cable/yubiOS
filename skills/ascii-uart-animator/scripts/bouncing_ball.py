"""Bouncing ball — 9 frames, 10fps, no ANSI clear. Single ball 'o' arcing across '=' ground.

Scrolls between frames instead of redrawing — useful for the 'does the receiver
even clear its screen?' check.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bridge import post_to_bridge, frame_plain

W, H = 40, 6
FPS_DELAY = 0.1
TOTAL_FRAMES = 9

CYCLE = [
    (4, 0), (8, 3), (12, 4), (16, 3),
    (20, 0), (24, 3), (28, 4), (32, 3),
    (36, 0),
]


def render_frame(n):
    x, h = CYCLE[n % len(CYCLE)]
    rows = [[" "] * W for _ in range(H)]
    row = H - 1 - h
    if 0 <= row < H:
        rows[row][x] = "o"
    return "\n".join("".join(r) for r in rows) + "\n" + "=" * W


def build_bash():
    lines = ["set -e"]
    for n in range(TOTAL_FRAMES):
        lines.append(frame_plain(repr(render_frame(n))))
        lines.append(f"sleep {FPS_DELAY:.3f}")
    lines.append("printf '\\n        *** FIN bouncing_ball @ 10fps ***\\n' > /dev/ttyS2")
    lines.append('echo "ball-sent"')
    return "\n".join(lines)


if __name__ == "__main__":
    body = build_bash()
    status, elapsed, resp = post_to_bridge(body)
    print(f"HTTP {status}  elapsed={elapsed:.2f}s  frames={TOTAL_FRAMES}  movie~{TOTAL_FRAMES * FPS_DELAY:.1f}s")
    print("RESPONSE:", resp)


## New Ideas -- cycle 2 (lens format)

This file was processed by the RSI cycle-2 lens generator (curve-compass-skill v1.1.0 + curved-corpus-create v1.1.0). Each cycle-2 patch IS a concrete experiment with a measurable delta -- not a templated section. The lens below documents the measured dynamics; the patch is the lens, not prose about the file.

```json
{
  "lens": "L365",
  "file": "skills/ascii-uart-animator/scripts/bouncing_ball.py",
  "hypothesis": "skills/ascii-uart-animator/scripts/bouncing_ball.py covers all 9 primitives in the internal-big-picture basis",
  "method": "9-D primitive binarization (purpose, examples, guidelines, constraints, verification, composition, changelog, references, anti-patterns) + chordal distance to ideal pole on Fibonacci lattice",
  "parameters": {
    "basis": "internal-big-picture",
    "d": 9,
    "seed": 20260812
  },
  "delta": {
    "k": 0,
    "missing_primitives": [
      "purpose",
      "examples",
      "guidelines",
      "constraints",
      "verification",
      "composition",
      "changelog",
      "references",
      "anti-patterns"
    ],
    "chordal_resid": 0.0
  },
  "verdict": "NO",
  "score": 0,
  "caveat": "binarization is heuristic; a stricter regex pass might surface sub-primitives"
}
```
