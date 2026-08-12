# Sealed-UKI VM debug decision tree (2026-08-01)

## Context

Apply when `.github/workflows/ci_test_sealed-uki-vm.yml` fails — the lane that builds a PKCS#11-signed UKI (SoftHSM slot emulating PIV 9c), boots it under OVMF Secure Boot, and runs negative tamper tests. Three jobs: `build-and-verify-uki`, `boot-secure-vm`, `negative-tamper-tests`; 6 assertions.

V25 → V39 burned **~15 runs over 2 days**, roughly half on failures that were not what the log appeared to say. Canonical pattern to diff against: `ci_mkosi-installer.yml` (SoftHSM bootstrap + `mkosi --secure-boot-key-source provider:pkcs11`).

## Decision

1. **Diff against the canonical, never improvise.** The stub diverged from `ci_mkosi-installer.yml` in 7+ ways; the canonical is right.
2. **Trust nothing in the workflow's own comments.** V25's "systemd-sbsign is part of systemd" burned V26 and V27.
3. **Check parse state before step logs.** `total_count: 0` ⇒ the YAML didn't parse; no step ran.
4. **One change per iteration, with a verifying step.** Every fix so far uncovered the next failure.

## Mechanism — the decision tree

**Row 0 — `conclusion=failure` in ~0s.** Not a step failure. YAML parse failure.
```bash
curl -sS ".../actions/runs/${RUN}/jobs" | jq '.total_count'   # 0 ⇒ parse error
python3 -c "import yaml;print(list(yaml.safe_load(open('.github/workflows/ci_test_sealed-uki-vm.yml'))['jobs']))"
```
Cause seen twice: **unquoted colon inside a step name** — YAML 1.1 reads the text after `:` as a flow-mapping key.
```diff
-      - name: Generate PKI as plain files (V38: cert + PKCS#8 PEM on host)
+      - name: "Generate PKI as plain files (V38: cert + PKCS#8 PEM on host)"
```
Expect PyYAML top-level keys `['name', True, 'permissions', 'jobs']` — `on:` → `True` is a YAML 1.1 quirk GitHub handles. Don't "fix" it.

**Row 1 — `systemd-sbsign: command not found` / `ukify not found in PATH`.** The binary ships inside the `systemd` package at `/usr/lib/systemd/systemd-sbsign` and is **not on PATH**. There is no `systemd-sbsign` dnf package (`No match for argument` is expected). Call it by full path. Also: each `docker run` is a fresh container — a dnf install in one does not persist to the next.

**Row 2 — the sign command fragments; `--private-key-source=…` runs as its own command.** Unquoted `;` in a PKCS#11 URI inside `bash -c "…"`. Single-quote the URI and embed the PIN (`pkcs11-provider` needs it or signing hangs / `C_Login`-fails):
```bash
/usr/lib/systemd/systemd-sbsign sign \
  --private-key-source=provider:pkcs11 \
  --private-key='pkcs11:token=yubiOS-ci;object=sb-key;type=private?pin-value=1234' \
  --certificate=/output/pki/sb.crt ...
```
`provider:pkcs11`, **not** `engine:pkcs11` — ADR-008 / OMN-116; OpenSSL 3.x deprecates the engine API. Prefer single-line `bash -c` with `&&`/`;`.

**Row 3 — `cpio: chown failed - No data available` installing softhsm.** A host mount shadows the RPM's own file target. Never mount over `/var/lib/softhsm`; cross-mount to `/run/yubios-hsm` and point `SOFTHSM2_CONF`'s `directories.tokendir` there — or drop the mount (row 5).

**Row 4 — `Failed to load X.509 certificate from /output/pki/sb.crt`, while an earlier step's `/output/yubios.unsigned.efi` is visible.** Two `docker run` invocations with the same `-v` mount **can diverge**. Collapse UKI build and signing into **one** `docker run`, or pass cert + PKCS#8 key as **base64 env vars**. Single-file bind-mounts give `EISDIR` when the path is a directory.

**Row 5 — `Input/output error` from pkcs11-provider on a cross-mounted token.** Cross-version SoftHSM BDB token files (host 2.6.1 Debian trixie vs container 2.7.0-2.fc45) are unreadable across versions. Don't cross-mount tokens: init inside the container (`softhsm2-util --init-token` + `--import /tmp/sb.p8`) from PEM passed as env vars, and **remove the mount** — a leftover `:ro` mount gives `EROFS` on the container's own token-dir writes.

**Row 6 — `KEY_P8_B64: unbound variable`, no other output.** `set -euo pipefail` + `set -u` + a `docker run` declaring only *some* `-e` vars. The first `echo "$UNSET"` exits before anything useful logs. Declare every var on the `docker run` line; `printenv`-check between outer and inner bash.

**Row 7 — `EVP_DigestSignUpdate: provider signature failure` (`030000EA`) on ECDSA.** **Not your workflow.** SoftHSM 2.7.0 added the hashed ECDSA mechanisms but implemented them **single-part only**; pkcs11-provider streams TBS bytes via `C_SignUpdate` and the token rejects it. Upstream: [SoftHSMv2#842](https://github.com/softhsm/SoftHSMv2/issues/842) (open; fix in [PR #857](https://github.com/softhsm/SoftHSMv2/pull/857), merged to `main`), [pkcs11-provider#715](https://github.com/openssl-projects/pkcs11-provider/issues/715) (closed, won't-fix provider-side). Two fixes, in order: (1) **pin `pkcs11-provider ≥ 1.2.0`**, which carries [PR #669](https://github.com/openssl-projects/pkcs11-provider/pull/669)'s softhsm fallback — verify with `rpm -q pkcs11-provider` inside the failing container; (2) **swap the CI token to kryoptic** (the provider maintainer's own recommendation; only `--module` and `--token-label` change).

**Row 8 — `boot-secure-vm` fails at OVMF level.** Expected today: neither `ci_test_sealed-uki-vm.yml` nor `ci_test-vgpu-vm.yml` provisions `OVMF_CODE.fd`/`OVMF_VARS.fd` or enrolls the yubiOS ROTPK into `db`. An OVMF rejection here **masks** the enrollment gap — don't read it as a signing failure. Artifact source: `ci_fork_edk2.yml`.

Also: `/runs/{id}/logs` 404s after ~15–30 min — diagnose from the file diff. Duplicate dispatches land 10–20 s apart — list and cancel (`202`).

## Verified working (2026-08-01)

A failure timeline, not a green run — **the lane has not yet produced a green signed-UKI build at this date.**

| Run | Commit | V | Failure (row) |
|---|---|---|---|
| #33 | `9c9cde13b4` | V25 | sbsign not found, ephemeral container (1) |
| #34 | `ec5941c8dd06` | V26 | same; the comment was wrong (1) |
| #35 | `118fc04a6c62` | V27 | `No match for argument`; URI `;` split bash (1, 2) |
| #37 | `9fb28b6d5198` | V28 | `cpio: chown failed` on `/var/lib/softhsm` (3) |
| #38 | `a5b4c97822f0` | V29 | cert missing at `/output/pki/sb.crt` (4) |
| #40/#41 | `4def8b47ce64` | V30 | dup dispatch; cert-verify diagnostic found no fault |
| #42 | `8ed444b93931` | V31/V32 | single-`docker run` merge (4) |
| #43/#44 | `c5516b4f8c0a`, `1968d4da644f` | V33/V34 | base64 cert env var; `EISDIR` (4) |
| #45 | `4d75c23ccf19` | V35 | `EISDIR` persisted; cross-mount tried |
| #46/#47 | `40269e13236a`, `28dc9a10433f` | V36 | cross-version BDB I/O error (5) |
| #48 | `a50ecac42cc0` | V37 | **0 jobs** — colon in step name (0; row 6 latent) |
| #49 | `bbdebc4177b0` | V38 | **0 jobs** — same class (0) |
| #50 (30610224165) | `3211e25a617e` | V39 | YAML parses (3 jobs, PyYAML-verified); awaiting PKI gen + signing |
| #51 (30610238585) | — | — | duplicate of #50, created 17 s later, cancelled (`202`) |

Narrative: `documents/…/sealed-uki-vm-debugging-journal-2026-07-30.md`. Row 7 is source-verified in `…/sealed-uki-vm-pkcs11-ecdsa-deepdive-VERIFIED-2026-07-31.md`.

The lane that **did** go green: PR #154 (`1c284b48826f` — "feat(ci): sealed UKI Secure Boot VM lane (companion to ci_test_bootc-filesystem.yml)") opened the lane on 2026-07-31; **PR #155** (`0cb68518bef0` — "feat(ci): fill in ci_test_sealed-uki-vm.yml stub (OMN-53 sealed UKI VM lane)") **MERGED**; commit **`1d0666d77c0b`** ("ci(V83): arm64 boot_timeout 900->1200s (TCG slack)") tuned arm64 boot timing to GREEN at V83 (run `30652859000`).

## Cross-references

- **See also:** `docs/BLOCKERS.md` → **B-BOOTC-SEAL** (Phase 1 artifact split shipped in PR #143 / `a1940330`; Phase 2 install-time BLSConfig wiring plus Secure Boot / negative-tamper evidence still open) and → Permanent CI-Evidence Patterns.
- Linear **OMN-43** (parent), OMN-52, OMN-47, OMN-53, OMN-150 (Phase 2), OMN-116 (ADR-008). ADRs **ADR-008**, ADR-022, ADR-032.
- `refs/sealed-uki-vm-test-2026-07-30.md` (3 jobs / 6 assertions), `refs/bootc-composefs-sealed-flow-2026-07-22.md`, `refs/kernel-rootfs-split-2026-07-29.md`, `refs/sbsign-pkcs11-validate-2026-07-23.md`.
- Canonical signing: `ci_mkosi-installer.yml`. OVMF artifacts: `ci_fork_edk2.yml`.
- Playbooks: [dispatch-chain-verification](dispatch-chain-verification.md) (row 0 applies it), [fido2-vm-e2e-recipe](fido2-vm-e2e-recipe.md).
- Gaps 1 and 12: no `tests/vm/test-secure-boot-tamper.sh`; negatives 2 and 3 are TODO-only. A `yaml.safe_load` pre-dispatch gate would have caught V37/V38 free.


## Guidelines

- Match the conventions in `docs/STYLE.md`
- See sibling files in this directory for the surrounding context


## Composition

- Sits next to sibling files in this directory; consult them for surrounding context
- For the full yubiOS dependency graph, see `docs/ARCHITECTURE.md`


## Changelog

- 2026-08-12 -- RSI cycle-4: new-idea experiment (primitive-flipped changelog, hypothesis + method + delta + verdict + score + caveat in lenses.json L<N>)
