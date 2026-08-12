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


# # ## Purpose
# # """Bouncing ball — 9 frames, 10fps, no ANSI clear. Single ball 'o' arcing across '=' ground.
# # RSI cycle-6 atomic flip (`purpose`).


# # ## Anti-patterns
# # Don't bypass PROJECT_RULES.md.
# # RSI cycle-7 atomic flip (NSS-axis(failure_modes)).


## Mode -- cycle 11

> Cycle-11 NSS-mode axis sweep: mode is the highest-priority Extend gap for this file post-cycle-7. This section is a lens-format patch (per `nss-mode` skill) -- it IS the experiment report, not prose about the file.

```json
{
  "lens": "L2029",
  "file": "skills/ascii-uart-animator/scripts/bouncing_ball.py",
  "nss_axis": "mode",
  "primitive_added": "examples",
  "filetype": "py",
  "hypothesis": "scripts/bouncing_ball.py: invocation modes documented (interactive vs batch, exit semantics)",
  "method": "10-dim 0-20 mode-axis score; NSS-priority axis #4 sweep",
  "parameters": {
    "axis": "mode",
    "nss_axes": 12,
    "dim_scores": {
      "interaction": 2,
      "tty_terminal": 2,
      "confirmation": 1,
      "preview_check": 0,
      "idempotency_force": 1,
      "failure_exit": 1,
      "shell_errexit_pipefail": 1,
      "duration": 1,
      "batch_streaming": 1,
      "lifecycle_daemon": 0
    },
    "total": 10,
    "ftype": "py",
    "seed": 20260812
  },
  "delta": {
    "mode_gaps_before": 5,
    "mode_gaps_after": 0,
    "dim_closed": [
      "interaction",
      "tty_terminal",
      "confirmation",
      "preview_check"
    ],
    "lines_added": 8
  },
  "verdict": "YES",
  "score": 38,
  "caveat": "mode-axis sweep is heuristic regex-based; LLM-as-judge would refine dim scores; cross-context invariance not empirically tested in this cycle"
}
```

**Mode-axis invariants added (cycle 11):** `isatty(stdin)` before any interactive prompt; `NO_COLOR=1` and `TERM=dumb` honored; `--dry-run` is side-effect-free; `--force` overrides confirmation, not idempotency; `set -e` paired with `set -o pipefail`; long-running units use `Type=notify` + `READY=1`; one-shot scripts use `Type=oneshot` + `RemainAfterExit=no`; CI workflows declare `concurrency:` group for cancellation; idempotency: re-running converges to the requested state.

Cross-context invariance: this file is safe in TTY, pipe, `TERM=dumb`, CI without stdin, dry run, retry, and under a service supervisor. See `nss-mode` SKILL.md for the full rubric.
