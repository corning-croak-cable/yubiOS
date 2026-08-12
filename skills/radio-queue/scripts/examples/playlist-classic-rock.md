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


## Guidelines

- Match the conventions in `docs/STYLE.md`
- See sibling files in this directory for the surrounding context


## Constraints

- Out of scope: changes to `papers/` (historical info) or `.github/workflows/*.yml` (CI workflows)


## Verification

- Spot-check by reading `playlist-classic-rock.md` end-to-end against this section's claim
- Run the relevant CI workflow on a draft branch per `docs/CI_MAP.md`


## Composition

- Sits next to sibling files in this directory; consult them for surrounding context
- For the full yubiOS dependency graph, see `docs/ARCHITECTURE.md`


## Changelog

- 2026-08-12 -- RSI cycle-4: new-idea experiment (primitive-flipped changelog, hypothesis + method + delta + verdict + score + caveat in lenses.json L<N>)


## References

- yubiOS repo: `yubi-OS/yubiOS`
- Architecture: `docs/ARCHITECTURE.md`
- See root `lenses.json` and `new-ideas-2026-08-12.md`
