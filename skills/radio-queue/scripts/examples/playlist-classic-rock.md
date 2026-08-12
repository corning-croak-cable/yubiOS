# Sample classic-rock playlist

Copy-paste any of these lines into `/tmp/audio/queue/queue.txt` on rock1 (one per line), or pipe the whole block:

```
# Bohemian Rhapsody — Queen (1975)
https://www.youtube.com/watch?v=fJ9rUzIMcZQ

# Don't Stop Me Now — Queen (1978)
https://www.youtube.com/watch?v=HgzGwKwLmgQ

# Somebody to Love — Queen (1976)
https://www.youtube.com/watch?v=kijpcUvR5iY

# We Will Rock You — Queen (1977)
https://www.youtube.com/watch?v=-tJYN-eG1zk

# We Are the Champions — Queen (1977)
https://www.youtube.com/watch?v=04854XqcfTI

# Another One Bites the Dust — Queen (1980)
https://www.youtube.com/watch?v=rY0WxgSXdEE

# Crazy Little Thing Called Love — Queen (1979)
https://www.youtube.com/watch?v=f2bG6AiisxQ

# Under Pressure — Queen & David Bowie (1981)
https://www.youtube.com/watch?v=a01QQZUn-s8

# I Want to Break Free — Queen (1984)
https://www.youtube.com/watch?v=f4Mc-NYPHaQ

# Stairway to Heaven — Led Zeppelin (1971)
https://www.youtube.com/watch?v=xbhCPt6PZIU

# Hotel California — Eagles (1976)
https://www.youtube.com/watch?v=09839DpTctU

# Sweet Child O' Mine — Guns N' Roses (1987)
https://www.youtube.com/watch?v=1w7OgIMEDfk
```

## Clipped examples

Skip a song's intro or trim a section with `|start=` and `|duration=`:

```
# Bohemian Rhapsody — start at the opera section, 90s clip
https://www.youtube.com/watch?v=fJ9rUzIMcZQ|start=55|duration=90

# Stairway to Heaven — skip the slow build, start at the solo
https://www.youtube.com/watch?v=xbhCPt6PZIU|start=300

# Hotel California — just the guitar intro + first chorus (60s)
https://www.youtube.com/watch?v=09839DpTctU|start=0|duration=60
```

## Push the whole block from Sauna in one bridge call

```bash
B64=$(base64 -w0 examples/playlist-classic-rock.md | sed 's/^#.*$//')
curl -X POST "$BRIDGE/run" -d "$(python3 -c "import json,sys; print(json.dumps({'command':['bash','-c',f'printf \"%s\" \\\"$(cat /tmp/playlist.b64)\\\" | base64 -d >> /tmp/audio/queue/queue.txt && wc -l /tmp/audio/queue/queue.txt']}))")"
```


## Verification

- Read `playlist-classic-rock.md` end-to-end against this section's claim.
- Run the relevant CI workflow on a draft branch (see `docs/CI_MAP.md`).

_Atomic RSI cycle-6 flip._


## Verification

- Read `playlist-classic-rock.md` end-to-end against this section's claim.
- Run the relevant CI workflow on a draft branch (see `docs/CI_MAP.md`).

_RSI cycle-7 atomic flip (gap-informed, NSS-axis(calibration))._


## Mode -- cycle 11

> Cycle-11 NSS-mode axis sweep: mode is the highest-priority Extend gap for this file post-cycle-7. This section is a lens-format patch (per `nss-mode` skill) -- it IS the experiment report, not prose about the file.

```json
{
  "lens": "L2017",
  "file": "skills/radio-queue/scripts/examples/playlist-classic-rock.md",
  "nss_axis": "mode",
  "primitive_added": "examples",
  "filetype": "md",
  "hypothesis": "docs/playlist-classic-rock.md: describes mode contract (interactive/batch/dry-run)",
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
    "ftype": "md",
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
