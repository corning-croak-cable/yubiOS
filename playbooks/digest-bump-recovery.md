# Digest bump recovery — stale fedora-bootc pin (2026-08-01)

## Context

Apply when a build fails because the `Containerfile` FROM digest is gone from quay.io: `quay.io/fedora/fedora-bootc:45@sha256:1dcca7ac…: not found`. Same class: an arm64 layer pull dying mid-stream (stream truncation).

Fired **three times in seven days** (2026-07-26 → 2026-07-30). Treat any `fedora-bootc:45@sha256:…` pin as good for days, not weeks. **This is self-mode fixable — do not surface a stale pin to Jenny as a blocker.**

## Decision

Two dispatches, never a hand-edited digest:

1. `ci.yml` with `group=fetches` — `fetch-fedora-bootc-manifest.yml` re-resolves against quay.io and bumps `Containerfile` + `PINNED.md` in **one** commit on `main`.
2. Re-dispatch the failed workflow (usually `ci_dev_image.yml`) at the **new** head.

Hand-swapping the digest breaks the `Containerfile`/`PINNED.md` invariant; the fetch workflow is the only thing that guarantees it.

## Mechanism

```bash
REPO=yubi-OS/yubiOS

# 1. confirm the pin is actually dead
DIGEST=$(grep -oE 'sha256:[0-9a-f]{64}' Containerfile | head -1)
curl -sSI "https://quay.io/v2/fedora/fedora-bootc/manifests/${DIGEST}" \
  -H 'Accept: application/vnd.oci.image.index.v1+json' | head -1

# 2. fire the recovery group (204 = accepted)
curl -sS -X POST \
  "https://api.github.com/repos/${REPO}/actions/workflows/ci.yml/dispatches" \
  -H 'Accept: application/vnd.github+json' \
  -d '{"ref":"main","inputs":{"group":"fetches","reason":"stale fedora-bootc digest"}}'

# 3. verify the INNER runs, not just ci.yml
curl -sS "https://api.github.com/repos/${REPO}/actions/runs?branch=main&per_page=10" \
  | jq -r '.workflow_runs[] | "\(.id)\t\(.name)\t\(.path)\t\(.conclusion)"'

# 4. confirm the bump landed
curl -sS "https://api.github.com/repos/${REPO}/commits?path=Containerfile&per_page=1" \
  | jq -r '.[0] | "\(.sha[0:8]) \(.commit.message)"'

# 5. re-dispatch the builder at the new head
curl -sS -X POST \
  "https://api.github.com/repos/${REPO}/actions/workflows/ci_dev_image.yml/dispatches" \
  -H 'Accept: application/vnd.github+json' \
  -d '{"ref":"main","inputs":{"Docker_push":"false"}}'
```

Rules that keep this boring:

- **One dispatch per POST.** An unconfirmed `204` gets retried and duplicates a run within 10–20 s. List runs immediately; cancel with `POST /actions/runs/{id}/cancel` (`202`).
- **After a bump, let the dispatcher settle.** One clean `group=fetches` round confirms currency; don't loop it.
- **`Docker_push` renames on forward** — children declare `ci_Docker_push`; forwarding the outer name 422s.

**Adjacent case — dev tag / short-SHA mismatch.** Fresh digest but the dev image won't resolve ⇒ the `dev-<short-sha>` tag points at a pre-bump build. Fix landed 2026-07-30 in commit **`95565a0e`** ("ci(workflows): also push dev-<short-sha> tag in merge-manifest (fixes OMN-149 verify pull)") which added a third `-t "$DEV_SHORT_SHA_TAG"` from `${GITHUB_SHA:0:8}` to the `ci_dev_image.yml` `merge-manifest` step. Resolve to a digest and pass the digest, not the tag, to VM dispatches:

```bash
skopeo inspect --raw docker://docker.io/0mniteck/yubios:dev-<short-sha> | sha256sum
```

## Verified working (2026-08-01)

| # | Date | From → to | Commit |
|---|---|---|---|
| 1 (OMN-139) | 2026-07-26 | `sha256:f6b5b775…` (arm64 stream truncation at layer 16,045,778) → re-resolved | rebuilt via `fetch-fedora-bootc-manifest.yml` |
| 2 | 2026-07-29 | `f6b5b775…` → `sha256:1dcca7ac54b243bef0cf65bfca165fb4a514d7891854db216a4ab6cbc10215ff` | `8ccffa71` |
| 3 | 2026-07-30 | `1dcca7ac…` (404) → `sha256:c7e6b35744792c2fc22c6e345d8a820ca83e08b94819f6c06fad4048810c96be` | `d2646452` |

Incident 3 was recovered entirely in self-mode under Jenny's standing directive "stale image? just re-run the fetch group ci".

## Tradeoffs

Dispatch-only recovery costs one extra ~2-min round-trip versus a hand edit and buys an auditable `Containerfile`+`PINNED.md` commit pair. A known improvement — a live quay.io HEAD pre-check in `ci_dev_image.yml` failing fast with "stale pin — bump via fetches group" — is unimplemented; today you pay ~50 s of build first.

## Cross-references

- **See also:** `docs/BLOCKERS.md` → **B-PINS**, and → Permanent CI-Evidence Patterns.
- `refs/digest-bump-checklist-2026-07-25.md`, `refs/fedora-bootc-base-images-status-2026-07-23.md`.
- Linear **OMN-139**. Commits `8ccffa71`, `d2646452`, `95565a0e`.
- Workflows: `fetch-fedora-bootc-manifest.yml` (the recovery tool), `fetch-dhi-manifest.yml`, `fetch-released-tag-ref.yml`, `ci_dev_image.yml`, `ci_test-fedora-bootc-arm64-pull.yml`.
- Playbooks: [dispatch-chain-verification](dispatch-chain-verification.md) — step 3 is not optional.


## Constraints

- Out of scope: changes to `papers/` (historical info) or `.github/workflows/*.yml` (CI workflows).
- See `PROJECT_RULES.md` for the yubiOS change-management doctrine.

_Atomic RSI cycle-6 flip._


## Constraints

- Out of scope: changes to `papers/` (historical info) or `.github/workflows/*.yml` (CI workflows).
- See `PROJECT_RULES.md` for the yubiOS change-management doctrine.

_RSI cycle-7 atomic flip (gap-informed, NSS-axis(assumption_set))._
