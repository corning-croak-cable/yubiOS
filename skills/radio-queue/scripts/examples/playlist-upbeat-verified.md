# Verified upbeat playlist

All six YouTube IDs in this file were verified via `yt-dlp --no-check-certificates --skip-download --dump-single-json <url>` on rock1 on 2026-08-05 — every URL resolved to its claimed title with the correct ID, so the daemon can download + transcode without burning through `Video unavailable` failures.

This playlist is what Jenny asked for verbatim: *"use the radio skill and play me an upbeat playlist."* The skill shipped the example classic-rock file but no upbeat counterpart — adding it here as the default starting point for the "queue something upbeat" workflow.

## How these IDs were verified

Before queueing, each URL was probed with rock1's installed yt-dlp:

```bash
# On rock1, via the bridge
yt-dlp --no-check-certificates --skip-download --dump-single-json 'https://www.youtube.com/watch?v=ID' 2>&1
```

A verified URL returns a JSON blob containing the title + id fields; an unverified one returns `ERROR: [youtube] <id>: Video unavailable` (region-locked, removed, or the ID is wrong). The skill's "Errors don't kill the daemon" anti-pattern only stops infinite loops — it doesn't keep the log clean. Verify before you queue, especially for playlists.

## The playlist

Copy-paste any of these lines into `/tmp/audio/queue/queue.txt` on rock1 (one per line), or pipe the whole block:

```
# Don't Stop Me Now — Queen (1978) — verified 2026-08-05
https://www.youtube.com/watch?v=HgzGwKwLmgM

# Walking on Sunshine — Katrina & The Waves (1985) — verified 2026-08-05
https://www.youtube.com/watch?v=iPUmE-tne5U

# Happy — Pharrell Williams (2013) — verified 2026-08-05
https://www.youtube.com/watch?v=ZbZSe6N_BXs

# September — Earth, Wind & Fire (1978) — verified 2026-08-05
https://www.youtube.com/watch?v=Gs069dndIYk

# I Gotta Feeling — The Black Eyed Peas (2009) — verified 2026-08-05
https://www.youtube.com/watch?v=uSD4vsh1zDA

# Uptown Funk — Mark Ronson ft. Bruno Mars (2014) — verified 2026-08-05
https://www.youtube.com/watch?v=OPf0YbXqDm0
```

## Why "upbeat"

Each track is a high-tempo, positive-energy song that's stood the test of time on radio rotation. The selection spans 1978–2014 so a session can run through without feeling samey. Tempo-wise: Don't Stop Me Now (~156 BPM) > Walking on Sunshine (~104 BPM) > Happy (~160 BPM) > September (~126 BPM) > I Gotta Feeling (~128 BPM) > Uptown Funk (~115 BPM) — three of the six are > 120 BPM (Walking on Sunshine and Uptown Funk are the gentler mid-tempo anchors that keep the set from feeling frantic).

## Push the whole block from Sauna in one bridge call

```bash
B64=$(base64 -w0 skills/personal-WbtUgeUv/radio-queue/examples/playlist-upbeat-verified.md | sed 's/^#.*$//')
curl -X POST "$BRIDGE/run" -d "$(python3 -c "import json; print(json.dumps({'command':['bash','-c',f'printf \"%s\" \\\"$(cat /tmp/playlist.b64)\\\" | base64 -d >> /tmp/audio/queue/queue.txt && wc -l /tmp/audio/queue/queue.txt']}))")"
```

## Verification history

- 2026-08-05 — initial verification + deployment; all 6 IDs returned correct titles + ids via `--dump-single-json`; daemon successfully downloaded + transcoded + played them on rock1 end-to-end.

## Guidelines

- Follow the conventions in `docs/STYLE.md` (or the most relevant style guide referenced from this directory).
- Match the existing structure of surrounding files: `## Examples`, `## Verification`, `## Changelog`, `## Anti-patterns`.

## Constraints

- Out of scope: changes that affect the historical paper corpus in `papers/` (published artifacts, immutable).
- Out of scope: changes to `.github/workflows/*.yml` (CI workflows, separate change-management process).

## Changelog

- 2026-08-12 — primitive-closure pass via `curve-compass-skill` + `curved-corpus-create` (this PR).

## References

- yubiOS repo: `yubi-OS/yubiOS`
- Architecture: `docs/ARCHITECTURE.md`
- The two new skills used to drive this primitive-closure pass: `skills/github-yubios-KS9n5GAT/curve-compass-skill/SKILL.md` and `skills/github-yubios-KS9n5GAT/curved-corpus-create/SKILL.md`.

