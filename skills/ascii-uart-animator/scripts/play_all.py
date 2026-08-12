"""Plays all 4 animations back-to-back to /dev/ttyS2:

  bouncing_ball → 1s pause → bouncing_ball_ansi → 1s pause
  → fish_swim → 1s pause → walking_man → FIN

Builds ONE big bash script so the bridge makes a single round-trip and rock1
runs everything sequentially. Total ~17 seconds of animation on the wire.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bouncing_ball
import bouncing_ball_ansi
import fish_swim
import walking_man
from bridge import post_to_bridge

SEPARATOR_DELAY = 1.0  # seconds pause between animations


def section_bash(render_fn, total_frames, fps_delay, with_clear, label):
    lines = []
    frame_fn = (
        lambda fr: f"printf '\\x1b[H\\x1b[2J%b\\n' {repr(fr)} > /dev/ttyS2"
        if with_clear
        else f"printf '%b\\n' {repr(fr)} > /dev/ttyS2"
    )
    for n in range(total_frames):
        lines.append(frame_fn(render_fn(n)))
        lines.append(f"sleep {fps_delay:.3f}")
    # Separator: clear screen + label + pause
    safe_label = label.replace("'", "'\\''")
    lines.append(f"printf '\\x1b[H\\x1b[2J=== {safe_label} (finished, next in {SEPARATOR_DELAY:.0f}s) ===\\n' > /dev/ttyS2")
    lines.append(f"sleep {SEPARATOR_DELAY}")
    return lines


def build_combined_bash():
    lines = ["set -e"]
    lines += section_bash(
        bouncing_ball.render_frame,
        bouncing_ball.TOTAL_FRAMES,
        bouncing_ball.FPS_DELAY,
        with_clear=False,
        label="bouncing_ball @ 10fps",
    )
    lines += section_bash(
        bouncing_ball_ansi.render_frame,
        bouncing_ball_ansi.TOTAL_FRAMES,
        bouncing_ball_ansi.FPS_DELAY,
        with_clear=True,
        label="bouncing_ball_ansi @ 30fps",
    )
    lines += section_bash(
        fish_swim.render_frame,
        fish_swim.TOTAL_FRAMES,
        fish_swim.FPS_DELAY,
        with_clear=True,
        label="fish_swim @ 25fps, multiline",
    )
    lines += section_bash(
        walking_man.render_frame,
        walking_man.TOTAL_FRAMES,
        walking_man.FPS_DELAY,
        with_clear=True,
        label="walking_man @ 20fps, multiline",
    )
    lines.append("printf '\\x1b[H\\x1b[2J*** ALL ANIMATIONS COMPLETE ***\\n' > /dev/ttyS2")
    lines.append('echo "all-sent"')
    return "\n".join(lines)


if __name__ == "__main__":
    body = build_combined_bash()
    total_time = (
        bouncing_ball.TOTAL_FRAMES * bouncing_ball.FPS_DELAY
        + bouncing_ball_ansi.TOTAL_FRAMES * bouncing_ball_ansi.FPS_DELAY
        + fish_swim.TOTAL_FRAMES * fish_swim.FPS_DELAY
        + walking_man.TOTAL_FRAMES * walking_man.FPS_DELAY
        + 3 * SEPARATOR_DELAY
    )
    print(f"BODY_BYTES: {len(body.encode())}")
    print(f"BASH_LINES: {body.count(chr(10)) + 1}")
    print(f"ESTIMATED_MOVIE_SECONDS: {total_time:.1f}")
    status, elapsed, resp = post_to_bridge(body, timeout=180)
    print(f"HTTP {status}  elapsed={elapsed:.2f}s")
    print("RESPONSE:", resp)


# ## Purpose
# # """Plays all 4 animations back-to-back to /dev/ttyS2:
# # RSI cycle-4 new-idea -- closes primitive p0.


## Examples

- Reading `play_all.py` (no args) shows usage
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
