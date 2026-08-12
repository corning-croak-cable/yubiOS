# Dispatch chain verification — outer ≠ inner (2026-08-01)

## Context

Apply **every time** you are about to state that a dispatch, chain, PR, or merge is green — and the moment any verification query returns something unexpected.

`ci.yml` is a group router: it dispatches each workflow in the group independently — no chain, no `needs:`, no callback read. `ci.yml conclusion=success` means exactly one thing: **its single dispatch job ran.** Every inner run can still fail.

The PR #150 cycle (2026-07-29) produced five violations of this in one session, including four fabricated run IDs.

## Decision

1. **Verify before claiming.** No run ID, conclusion, or merge state without a fresh API call *in the same turn*.
2. **Outer ≠ inner.** Read the inner runs' own conclusions.
3. **404 / 422 / conflict = stop-the-line.** Surface it; don't retry past it.
4. **Never fabricate.** Unqueried ⇒ say "I haven't verified this yet."
5. **Jenny merges.** Never `PUT /pulls/{n}/merge` — not even after she says she merged. Verify with `GET /pulls/{n}` (`merged: true`).

Corollary: **the patch is ground truth, not the title.** Read `GET /pulls/{n}/files`.

## Mechanism

```bash
REPO=yubi-OS/yubiOS

# 1. dispatch once
curl -sS -o /dev/null -w '%{http_code}\n' -X POST \
  "https://api.github.com/repos/${REPO}/actions/workflows/ci.yml/dispatches" \
  -H 'Accept: application/vnd.github+json' \
  -d '{"ref":"main","inputs":{"group":"fetches","reason":"<why>"}}'

# 2. list immediately — catch duplicate dispatches (10-20s apart)
curl -sS "https://api.github.com/repos/${REPO}/actions/runs?branch=main&per_page=10" \
  | jq -r '.workflow_runs[] | "\(.id)\t\(.name)\t\(.path)\t\(.status)\t\(.conclusion)\t\(.created_at)"'
# duplicate ⇒ POST /actions/runs/{id}/cancel  (202)

# 3. per inner run: confirm identity AND jobs
RUN=<inner-run-id>
curl -sS "https://api.github.com/repos/${REPO}/actions/runs/${RUN}" \
  | jq '{id,name,path,event,head_sha,status,conclusion}'
curl -sS "https://api.github.com/repos/${REPO}/actions/runs/${RUN}/jobs" \
  | jq '{total_count, jobs:[.jobs[]|{name,conclusion}]}'
```

`total_count: 0` on a completed run is **not** "no jobs yet" — it is the structural symptom of a **YAML parse failure**: instant `conclusion: failure`, zero steps executed, indistinguishable from a runtime failure. Check parse state before reading step logs:

```bash
python3 -c "import yaml,sys;print('jobs:',list(yaml.safe_load(open(sys.argv[1]))['jobs']))" \
  .github/workflows/<file>.yml
```

Two more traps this catches:

- **Logs expire.** `GET /runs/{id}/logs` 404s on runs ~15–30 min old. After the first 404, diagnose from the file diff and the jobs endpoint — stop polling.
- **Run listings mislead.** A run surfaced under `?workflow=ci.yml` may be an inner-chain run. Always report `name` **and** `path`.

Merge verification — read-only, always:

```bash
curl -sS "https://api.github.com/repos/${REPO}/pulls/150" \
  | jq '{number,state,merged,merged_by:.merged_by.login,merge_commit_sha}'
curl -sS "https://api.github.com/repos/${REPO}/pulls/150/files" \
  | jq -r '.[] | "\(.status)\t+\(.additions)/-\(.deletions)\t\(.filename)"'
```

`GET /pulls/{n}` returning 404 while someone says it merged ⇒ **stop.** Report the anomaly.

**Reporting template:** `<workflow-file>` run `<id>` (`name=`, `head_sha=`) → `conclusion=`, jobs: `<job>=<conclusion>`; inner runs verified: `<id>(<path>)=<conclusion>`; **unverified:** `<listed explicitly>`.

## Verified working (2026-08-01)

Process playbook — backed by the recorded failure, not a green run.

- **PR #150 cycle, 2026-07-29** (session `ses_0528b4061ffeMa4ZYkxO2lY5rj`): (a) `PUT /pulls/150/merge` called after Jenny merged (`merged_by=foil-copy-overrate`, so a redundant no-op — the violation stands); (b) `GET /pulls/150` returned 404 and the anomaly was ignored; (c) `ci.yml conclusion=success` reported as "chain green" with no inner reads; (d) run IDs `30482053371`, `30482065520`, `30482102387`, `30482136628` **fabricated**; (e) same fabrication pattern in prior sessions.
- **PR #147** (`8b5b20b`) is the patch-vs-title proof: the title claimed a GH_TK swap *and* a checkout bump; `GET /pulls/147/files` showed **only** the `actions/checkout` v6→v7.0.1 SHA bump. Smoke test [30484718456](https://github.com/yubi-OS/yubiOS/actions/runs/30484718456) succeeded on `8b5b20b` — proving the SHA bump was the real chain fix and PR #148 (`a49e95db`) was hygiene.
- **Runs #48/#49 of `ci_test_sealed-uki-vm.yml`** are the `total_count: 0` proof: both "failed" instantly at the parse stage (unquoted colon in a step name), zero jobs; the real bugs were diagnosed from the file diff.

## Operational

- One dispatch per intent; list; cancel duplicates (`202`).
- Never dispatch `group=all` in self-mode — 25 child dispatches in one burst risks the Actions API rate limit. One group per dispatch.
- `fetch-*.yml` hold `contents: write` and commit to `main` on every success. An idle "let me just check" dispatch is an unintended commit.
- All GitHub calls go through `conn_1KXnkOHGgyE4` ("MASTER GIT SU"). No fallback.

## Cross-references

- **See also:** `docs/BLOCKERS.md` → **Permanent CI-Evidence Patterns**; `PROJECT_RULES.md` → "PR #150 cycle — mistakes & lessons" and "PR diff verification — always read the patch, not the message".
- Linear **OMN-150**. PRs **#150**, **#147** (`8b5b20b`), **#148** (`a49e95db`), **#145**. Run 30484718456.
- `docs/CI_MAP.md` — group membership. `ci_test-ftpm-tpm0.yml`, `ci_test-fedora-bootc-arm64-pull.yml`, `ci_test-vgpu-vm.yml` are in **no** group; `group=all` silently misses them (Gap 9).
- Playbooks: [digest-bump-recovery](digest-bump-recovery.md), [hw-device-and-allow-real-u2f](hw-device-and-allow-real-u2f.md), [sealed-uki-vm-debug](sealed-uki-vm-debug.md).


## New Ideas -- cycle 3 (lens external)

This file's lens is **L299** in `lenses.json` (score 33/50, verdict **PARTIAL**, k=6/9). Full experiment: hypothesis `playbooks/dispatch-chain-verification.md covers all 9 primitives in the internal-big-picture basis`, method `9-D primitive binarization (purpose, examples, guidelines, constraints, verifica...`. See root `new-ideas-2026-08-12.md` for the cycle-3 summary.
