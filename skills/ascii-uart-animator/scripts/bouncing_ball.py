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


# ## Purpose
# # """Bouncing ball — 9 frames, 10fps, no ANSI clear. Single ball 'o' arcing across '=' ground.
# # RSI cycle-4 new-idea -- closes primitive p0.


## Examples

- Reading `bouncing_ball.py` (no args) shows usage
- See `docs/ARCHITECTURE.md` for where this file fits in yubiOS


## Guidelines

- Match the conventions in `docs/STYLE.md`
- See sibling files in this directory for the surrounding context


## Constraints

- Out of scope: changes to `papers/` (historical info) or `.github/workflows/*.yml` (CI workflows)


# ## Verification
# # python3 this_script.py --selftest  # exits 0 iff GREEN


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
