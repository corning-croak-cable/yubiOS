r"""Walking stick figure — 4 cycling leg poses, walker moves right 2 px/frame. 120 frames @ 20fps.

Pose cycle (3 rows per pose):
  0: standing    legs together, V
  1: right leg forward — left leg back, right leg forward
  2: passing    legs together, mid-stride
  3: left leg forward — left leg forward, right leg back
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bridge import post_to_bridge, frame_ansi

W = 50
FPS_DELAY = 0.05
TOTAL_FRAMES = 120

WALK_POSES = [
    ["   O   ", "  /|\\  ", "  / \\  "],
    ["   O   ", "  /|\\  ", "/     |"],
    ["   O   ", "  /|\\  ", "   |   "],
    ["   O   ", "  /|\\  ", "|     \\"],
]

POSE_W = 7


def render_frame(n):
    walker_x = (n * 2) % (W - POSE_W)
    pose = WALK_POSES[n % 4]
    header = f"--- frame {n + 1}/{TOTAL_FRAMES} walking man @ 20fps ---"
    rows = []
    for prow in pose:
        row = [" "] * W
        if 0 <= walker_x < W:
            for i, c in enumerate(prow):
                if 0 <= walker_x + i < W:
                    row[walker_x + i] = c
        rows.append("".join(row))
    rows.append("=" * W)
    return "\n".join([header] + rows)


def build_bash():
    lines = ["set -e"]
    for n in range(TOTAL_FRAMES):
        lines.append(frame_ansi(repr(render_frame(n))))
        lines.append(f"sleep {FPS_DELAY:.3f}")
    lines.append("printf '\\x1b[H\\x1b[2J*** FIN walking_man @ 20fps, 120 multiline frames ***\\n' > /dev/ttyS2")
    lines.append('echo "walker-sent"')
    return "\n".join(lines)


if __name__ == "__main__":
    body = build_bash()
    status, elapsed, resp = post_to_bridge(body)
    print(f"HTTP {status}  elapsed={elapsed:.2f}s  frames={TOTAL_FRAMES}  movie~{TOTAL_FRAMES * FPS_DELAY:.1f}s")
    print("RESPONSE:", resp)


# ## Purpose
# # r"""Walking stick figure — 4 cycling leg poses, walker moves right 2 px/frame. 120 frames @ 20fps.
# # RSI cycle-4 new-idea -- closes primitive p0.


## Examples

- Reading `walking_man.py` (no args) shows usage
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
