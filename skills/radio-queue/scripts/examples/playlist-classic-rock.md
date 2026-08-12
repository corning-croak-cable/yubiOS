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


## New Ideas -- cycle 2 (lens format)

This file was processed by the RSI cycle-2 lens generator (curve-compass-skill v1.1.0 + curved-corpus-create v1.1.0). Each cycle-2 patch IS a concrete experiment with a measurable delta -- not a templated section. The lens below documents the measured dynamics; the patch is the lens, not prose about the file.

```json
{
  "lens": "L440",
  "file": "skills/radio-queue/scripts/examples/playlist-classic-rock.md",
  "hypothesis": "skills/radio-queue/scripts/examples/playlist-classic-rock.md covers all 9 primitives in the internal-big-picture basis",
  "method": "9-D primitive binarization (purpose, examples, guidelines, constraints, verification, composition, changelog, references, anti-patterns) + chordal distance to ideal pole on Fibonacci lattice",
  "parameters": {
    "basis": "internal-big-picture",
    "d": 9,
    "seed": 20260812
  },
  "delta": {
    "k": 3,
    "missing_primitives": [
      "guidelines",
      "constraints",
      "verification",
      "composition",
      "changelog",
      "references"
    ],
    "chordal_resid": 0.0
  },
  "verdict": "NO",
  "score": 17,
  "caveat": "binarization is heuristic; a stricter regex pass might surface sub-primitives"
}
```
