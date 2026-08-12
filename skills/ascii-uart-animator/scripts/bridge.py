"""Shared helpers for posting bash scripts to the rock1 shell bridge."""
import json
import time
import urllib.request

BRIDGE_URL = "https://rock1.tail3a04f5.ts.net/run"


def post_to_bridge(bash_script, timeout=120):
    """POST an argv-array command to the rock1 bridge and return (status, elapsed, response_text)."""
    body = json.dumps({"command": ["bash", "-c", bash_script]})
    req = urllib.request.Request(
        BRIDGE_URL,
        data=body.encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        resp = r.read().decode("utf-8")
    return r.status, time.time() - t0, resp


def frame_ansi(line_repr):
    """printf line that writes one frame with ANSI clear+home prefix."""
    return f"printf '\\x1b[H\\x1b[2J%b\\n' {line_repr} > /dev/ttyS2"


def frame_plain(line_repr):
    """printf line that writes one frame with no prefix (scrolls)."""
    return f"printf '%b\\n' {line_repr} > /dev/ttyS2"


## New Ideas -- cycle 2 (lens format)

This file was processed by the RSI cycle-2 lens generator (curve-compass-skill v1.1.0 + curved-corpus-create v1.1.0). Each cycle-2 patch IS a concrete experiment with a measurable delta -- not a templated section. The lens below documents the measured dynamics; the patch is the lens, not prose about the file.

```json
{
  "lens": "L367",
  "file": "skills/ascii-uart-animator/scripts/bridge.py",
  "hypothesis": "skills/ascii-uart-animator/scripts/bridge.py covers all 9 primitives in the internal-big-picture basis",
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
