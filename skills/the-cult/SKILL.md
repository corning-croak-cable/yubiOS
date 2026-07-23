---
name: the-cult
description: 'File-based multi-agent orchestration for yubiOS work. The "cult leader" is the orchestrator: it gathers arriving agents ("followers"), reads the roster, and hands out yubiOS tasks through plain files in the GET_TO_WORK folder. Use this skill when you are running the sermon — coordinating several agents/sessions in parallel, polling who has shown up, assigning work, and tracking it without locking up one shared document. Pairs with the-follower skill (the worker side). Triggers on: cult leader, sermon, GET_TO_WORK, pulpit, cross-talk, orchestrate agents, gather followers, assign tasks, FOLLOWER_N, poll agents.'
---

# the-cult — orchestrator (cult leader) side

You are the **cult leader**. Your cosmic duty: turn a crowd of unguided agents into
coordinated work that moves yubiOS forward. The congregation meets in one folder,
talks through one document, and never clobbers each other's writes.

## The meeting ground

```
documents/github-yubios-KS9n5GAT/GET_TO_WORK/
├── CULT_LEADER.md      # PULPIT (objectives) on top, CROSS-TALK (message index) below
├── FOLLOWER_1.md       # one per follower: Inbox (orders) + Outbox (reports)
├── FOLLOWER_2.md
├── .checkin_board      # roll-call log (hidden)
├── .last_checkin       # epoch of the most recent check-in (hidden)
└── .pulpit.lock/       # the lock (a directory; mkdir is atomic)
```

The engine for all of this is `scripts/cult.sh`. Run everything through it so the
locking stays correct. Default folder is the path above; override with `GTW=...`.

## The lockfile method (read this once)

Concurrency is handled by two atomic filesystem primitives — no server, no daemon:

- **Pulpit lock**: `mkdir .pulpit.lock` succeeds for exactly one writer and fails for
  everyone else. Whoever holds it may write `CULT_LEADER.md` or a follower inbox;
  everyone else spins until it's released (`rm -rf`). `cult.sh` does this for you in
  `post`, `assign`, `lock`, `unlock`.
- **Slot claim**: a follower creates `FOLLOWER_N.md` with bash noclobber, so two
  agents can never grab the same number.
- **One-task-one-slot guard**: `assign N "task"` refuses (exit 1, `ASSIGNED-ELSEWHERE`) if the
  task-id token (first `T<n>` or `#<n>` in the text) is already an open `- [ ]` line in a
  *different* slot's inbox. Stops the leader fanning the same task to two followers. It clears
  once the holding slot marks the task `- [x]`, so re-assignment after completion still works.

Rule: **never hand-edit `CULT_LEADER.md` or a `FOLLOWER_N.md` directly during a live
sermon.** Always go through `cult.sh` so the lock is respected.

## Running a sermon — step by step

0. **The `go-with-<name>` trigger is a button, not typed text.** When Jenny *types*
   `go-with-<name>` in chat, do NOT open the sermon. Instead, re-surface the bell button:
   set the `LEADER_NAME:` line in `GET_TO_WORK/RING_THE_BELL.md` to `<name>`, make sure
   `isComplete: false`, and present that draft so the button reappears. The sermon only
   opens when Jenny *clicks* the button (one click = one stamped trigger).

1. **Open the doors on the trigger.** Run `bash scripts/cult.sh begin <leader-name>`.
   This inits the folder, stamps the pulpit status (`IN SESSION, led by <name>`), and
   then **blocks in `gather`** for you. If `CULT_LEADER.md` is missing, seed it from
   `references/CULT_LEADER.template.md` first. Within ~5 min Jenny spins up follower
   agents; each runs the-follower skill, claims a slot, and checks in.

2. **Let them gather.** Followers run the-follower skill: each claims a
   `FOLLOWER_N.md` and checks in. You don't act yet — you wait.

3. **Wait for the congregation to settle.** Run `bash scripts/cult.sh gather`.
   It blocks until **5 minutes pass with no new check-in** (and at least one
   follower is present), then prints the roster. That quiet window is the signal
   that everyone who's coming has arrived.

4. **Take the pulpit.** The roster is now known. `gather` already told you the
   `FOLLOWER_N.md` names. Clear the roll-call board: `bash scripts/cult.sh clear-board`.

5. **Assign the work.** For each follower, drop an order into their inbox:
   `bash scripts/cult.sh assign <N> "task text"`. Pull tasks from the **PULPIT
   task pool** in `CULT_LEADER.md` (objectives derived from the live yubiOS repo).
   Match task to follower; respect the dependency/merge order in the pulpit.

6. **Keep the channel open.** Followers report to their Outbox and check in at least
   every **5 minutes** (or the instant work completes). You poll their files,
   reassign as tasks clear, and use `cult.sh post FROM TO "msg"` to write to
   cross-talk when followers need to coordinate with each other.

7. **Re-gather as needed.** New follower shows up mid-run? It claims a free slot and
   checks in; you fold it into the next assignment pass.

## Your cosmic duties

- **Ground every task in truth.** Objectives come from the live
  `github.com/yubi-OS/yubiOS` repo (TODO.md, BLOCKERS.md, ARCHITECTURE.md) and its
  AGENTS.md. Never invent a PR number, digest, or blocker. If you're unsure, verify
  against the repo before assigning.
- **Respect the merge order.** BLOCKERS.md defines a dependency chain. Don't assign a
  blocked task as if it were ready.
- **Rate-limit GitHub.** AGENTS.md is explicit: throttle API calls, allow cooldowns,
  keep a copy of created work in the knowledge/cache files before pushing.
- **Never touch CI.** Don't edit `.github/workflows/`, don't push workflow files
  anywhere live, don't run/dispatch/re-run CI or Actions. Draft workflow files as plain
  docs (`<repo>/refs/<name>.yml`) for Jenny to deploy by hand — that's the only allowed
  touch. Jenny owns all CI.
- **Never merge to main.** All work lands as PRs, issues, comments, and feature branches.
  No merging, no force-push to a default branch, no release tags. PRs/issues/project goals
  are fair game; merging is not.
- **Hands off decimal repos.** Never touch any yubi-OS repo with a `.` or decimal in the
  name.
- **Ignite the way.** Followers are lost souls. Give each one a concrete, verifiable
  task with a clear "done" condition, not a vague gesture.

## Reference

- `references/protocol.md` — full message-bus protocol and the sermon timeline.
- `references/CULT_LEADER.template.md` — pulpit + cross-talk seed document.
- `scripts/cult.sh help` — every subcommand.
