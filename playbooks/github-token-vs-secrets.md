# github.token vs secrets.X (2026-08-01)

## Context

Apply when writing or reviewing any credential line in a workflow: `token:` on `actions/checkout`, `GH_TOKEN:` in a step env, a `git push` URL, a registry login.

The fleet runs on **three secrets** — `DOCKER`, `GITHUB_TOKEN`, `WORKFLOW` — plus automatic `github.token`. A fourth, `GH_TK`, was a same-repo PAT used where `github.token` would do; PR #148 removed all six references.

## Decision

**Same-repo, single-run, ephemeral ⇒ `${{ github.token }}` with an explicit `permissions:` block.** Cross-repo, external service, or a capability `GITHUB_TOKEN` structurally cannot have ⇒ a named secret.

| Need | Use |
|---|---|
| checkout / REST call / `git push` on **this** repo | `github.token` + matching `permissions:` |
| dispatch a workflow in **another** repo | `secrets.WORKFLOW` |
| container registry login | `secrets.DOCKER` |
| must outlive the run, or trigger another workflow's `on:` events | named secret (PAT) |

The load-bearing asymmetry: `github.token` is bounded by the workflow's `permissions:` block, and pushes made with it **do not trigger** other workflows' event triggers. A PAT is unbounded. Prefer the bounded credential and declare the bound.

## Mechanism

```yaml
permissions:
  contents: read          # default posture
  # actions: write        # only for the ci-callback pattern
  # contents: write       # only for the fetch-*.yml family that commits to main
```

```yaml
- uses: actions/checkout@3d3c42e5aac5      # v7.0.1 — pinned by SHA
  with: { token: "${{ github.token }}" }

- name: Push the resolved pin
  env: { GH_TOKEN: "${{ github.token }}" }  # requires contents: write above
  run: git commit -am "chore: bump pinned digest" && git push

- uses: docker/login-action@<pinned-sha>
  with:
    username: ${{ secrets.DOCKER_USERNAME }}
    password: ${{ secrets.DOCKER }}
```

```bash
rg -n 'GH_TK' .github/workflows/ && echo STALE || echo clean   # expect zero hits
rg -n 'secrets\.[A-Z_]+|github\.token' .github/workflows/ | sort -u
for f in .github/workflows/*.yml; do
  grep -q '^permissions:' "$f" || echo "no top-level permissions: $f"; done
```

Failure modes:

- **403 on a callback or push** — the `permissions:` block lacks the scope, or the org default moved. Fix the block; do not reach for a PAT. Only `ci.yml` declares `permissions: actions: write` at top level; the 24 children rely on per-job or inherited grants — that's the latent 403.
- **Push lands, downstream workflow never fires** — expected with `github.token`. If you truly need the cascade, that's the legitimate named-secret case; yubiOS dispatches explicitly instead.
- **`actions/checkout` auth failure** — check the pinned action SHA before blaming the token; that was the real root cause behind PR #147.

## Verified working (2026-08-01)

**PR #148** (branch `ci/remove-gh-tk-references`, commit **`a49e95db`**, 2026-07-29) replaced all **6** `GH_TK` references across **3** files with `github.token`:

- `fetch-dhi-manifest.yml` — checkout token, a dead env var, `git push` (3)
- `fetch-released-tag-ref.yml` — checkout token + compare endpoint env (2)
- `fetch-fedora-bootc-manifest.yml` — `git push` (1)

All three declare `permissions: { contents: write, actions: write }` at workflow level, so `github.token` inherits write capability. After merge, `GH_TK` in repo Settings → Secrets is referenced by no workflow and can be deleted.

**Scope of the claim:** PR #148 is **hygiene, not a bug fix.** The chain break it was believed to fix was actually fixed by the `actions/checkout` v6→v7.0.1 SHA bump in PR #147 (`8b5b20b`), proven by smoke test [30484718456](https://github.com/yubi-OS/yubiOS/actions/runs/30484718456), which succeeded on `8b5b20b` while `GH_TK` was still in place.

## Cross-references

- **See also:** `docs/BLOCKERS.md` → "Not Current Blockers" (the old workflow-token-scope warning is obsolete — do not reinstate); `PROJECT_RULES.md` → "GH_TK cleanup landed (PR #148, 2026-07-29)".
- PRs **#148** (`a49e95db`), **#147** (`8b5b20b`). Run 30484718456.
- Secrets in use: `DOCKER`, `WORKFLOW` (cross-repo dispatch in the `fetch-*` family), `GITHUB_TOKEN` (declared on `ci_test-vgpu-vm.yml`).
- `refs/actions-checkout-v6-includeif-investigation-2026-07-29.md`.
- Open gap: no central `permissions:` audit — Gap 11 / Linear candidate 11.
- Playbooks: [dispatch-chain-verification](dispatch-chain-verification.md) — this is an instance of "read the patch, not the title".


## Verification

- Read `github-token-vs-secrets.md` end-to-end against this section's claim.
- Run the relevant CI workflow on a draft branch (see `docs/CI_MAP.md`).

_Atomic RSI cycle-6 flip._
