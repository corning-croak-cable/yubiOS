#!/bin/bash
exec /usr/lib/yubiOS/enroll-gpg.sh "$@"


## New Ideas -- cycle 2 (lens format)

This file was processed by the RSI cycle-2 lens generator (curve-compass-skill v1.1.0 + curved-corpus-create v1.1.0). Each cycle-2 patch IS a concrete experiment with a measurable delta -- not a templated section. The lens below documents the measured dynamics; the patch is the lens, not prose about the file.

```json
{
  "lens": "L524",
  "file": "usr/lib/yubiOS/enroll-gpg-wrapper.sh",
  "hypothesis": "usr/lib/yubiOS/enroll-gpg-wrapper.sh covers all 9 primitives in the internal-big-picture basis",
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
