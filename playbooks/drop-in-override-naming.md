# Drop-in override naming — the lex-sort rule (2026-08-01)

## Context

Apply **before shipping any new or renamed yubiOS drop-in** in `usr/lib/modprobe.d/`, `usr/lib/dracut.conf.d/`, `usr/lib/tmpfiles.d/`, `usr/lib/systemd/*.service.d/`, `usr/lib/udev/rules.d/`.

All of them sort by **full filename, lexicographically** — systemd-tmpfiles(5): "All configuration files are sorted by their filename in lexicographic order." Numeric prefixes (`50-`, `53-`) are a sysv-init `rcN.d/` convention that does **not** transfer. A numerically-prefixed override intended to fire *after* upstream fires *before* it, and upstream wins silently. This cost 4 days on OMN-149.

## Decision

Drop-ins whose intent is "fire after upstream" must carry a prefix that lex-sorts **after** every upstream file they override — `vfio-yubiOS-…`, `kvm-yubiOS-…`, `yubiOS-…`. Never a bare numeric prefix. "Fire before upstream" may keep a low numeric prefix. Ordering is verified mechanically at author time, never inferred from the number.

## Mechanism

The arithmetic that bit OMN-149:

```
"53-yubiOS-no-static-vfio.conf"  → '5' = 0x35
"static-nodes-permissions.conf"  → 's' = 0x73
0x35 < 0x73  ⇒  yubiOS fires FIRST, upstream fires LAST
```

Upstream's `z /dev/vfio/vfio 0666 - - -` then re-created the cdev every boot, negating the yubiOS `r /dev/vfio/vfio`.

```bash
# 1. effective sort order for the directory you touched
ls -1 usr/lib/tmpfiles.d/ | sort -u

# 2. prove your file sorts AFTER the upstream file you override
printf '%s\n%s\n' 'vfio-yubiOS-no-static-vfio.conf' \
                  'static-nodes-permissions.conf' | sort | tail -1
# must print YOUR filename

# 3. upstream files that ship in the base image, not the repo
podman run --rm docker.io/0mniteck/yubios:latest \
  sh -c 'ls -1 /usr/lib/tmpfiles.d/ | sort -u'

# 4. assert the runtime effect, not just the name (in-guest)
test ! -e /dev/vfio && echo PASS || { echo "FAIL: /dev/vfio present"; exit 1; }
```

Two corollaries from the same incident:

- Prefer `r ` (remove) over `z ` (adjust-last) in `tmpfiles.d` when an upstream package will re-create the node.
- **Re-verify on base-image bumps.** The guarantee is per-filename-pair, not permanent — a new upstream `static-…` file invalidates it.

## Verified working (2026-08-01)

- Broken ship: commit **`59f4332`** (2026-07-26) added `usr/lib/tmpfiles.d/53-yubiOS-no-static-vfio.conf`. `/dev/vfio` stayed present in every guest for 4 days; `ci_test-vgpu-vm.yml` arm64 step 21 (`tests/vm/test-vgpu-virtio-ci.sh`) failed with `FAIL: /dev/vfio exists in a default yubiOS guest; rule 1 says images ship virtio-gpu only`.
- Fix: commit **`f92c6010`** (2026-07-30) renamed to `vfio-yubiOS-no-static-vfio.conf` (`'v'` 0x76 > `'s'` 0x73).
- Codified same day in `docs/BLOCKERS.md` → Permanent CI-Evidence Patterns → "Systemd drop-in lex-sort rule (est. 2026-07-30, source: OMN-149)".

## Cross-references

- **See also:** `docs/BLOCKERS.md` → **Permanent CI-Evidence Patterns** → "Systemd drop-in lex-sort rule" (doctrine; this playbook is the recipe).
- Linear: **OMN-149**, OMN-141, OMN-146. Commits: `59f4332`, `f92c6010`.
- Tests: `tests/vm/test-vgpu-virtio-ci.sh`, `tests/vm/test-vfio-user-host-ci.sh`.
- Playbooks: [dispatch-chain-verification](dispatch-chain-verification.md) — same incident is why "the test says FAIL" outranks "the file is shipped".
- A proactive CI gate for this rule is unbuilt: Gap 8 in `refs/testing-production-gaps-2026-08-01.md`.
