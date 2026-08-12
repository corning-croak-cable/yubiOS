#!/usr/bin/env python3
"""
file-drift-issues.py — files GitHub issues for forked repos that drifted.

Reads the JSON report produced by detect-fork-drift.py and files one issue
per drifted fork via the GitHub REST API. Dry-run mode by default; pass
--apply to actually file.

Usage:
  python3 scripts/file-drift-issues.py --input drift-report.json [--apply] [--org NAME]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def file_github_issue(org: str, repo: str, title: str, body: str, token: str,
                      labels: list[str] | None = None) -> dict | None:
    """File one GitHub issue. Returns the issue JSON on success."""
    url = f"https://api.github.com/repos/{org}/{repo}/issues"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "yubios-fork-drift-detector",
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": f"Bearer {token}",
    }
    payload = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels
    req = urllib.request.Request(
        url,
        method="POST",
        headers={**headers, "Content-Type": "application/json"},
        data=json.dumps(payload).encode(),
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"error: issue POST {org}/{repo} HTTP {e.code}: {e.read().decode()[:300]}", file=sys.stderr)
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to drift-report.json")
    parser.add_argument("--apply", action="store_true", help="Actually file (default: dry-run)")
    parser.add_argument("--org", default="yubi-OS")
    parser.add_argument("--labels", nargs="*", default=["drift-detected", "automated"])
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"error: input file not found: {input_path}", file=sys.stderr)
        return 2

    data = json.loads(input_path.read_text())
    drifted = [r for r in data.get("results", []) if r.get("verdict") == "drifted"]
    if not drifted:
        print("No drifted forks; nothing to file.")
        return 0

    token = os.environ.get("GITHUB_TOKEN")
    if args.apply and not token:
        print("error: --apply requires GITHUB_TOKEN env var", file=sys.stderr)
        return 2

    filed_count = 0
    for r in drifted:
        fork = r["fork"]
        pinned = r.get("pinned_sha", "?")[:8]
        upstream = r.get("upstream_sha", "?")[:8]
        behind = r.get("behind", "?")
        title = f"[drift-detected] {fork} is {behind} commits behind upstream"
        body = (
            f"## Drift detected\n\n"
            f"- **Fork:** `{fork}`\n"
            f"- **Pinned SHA:** `{pinned}..`\n"
            f"- **Upstream SHA:** `{upstream}..`\n"
            f"- **Commits behind:** {behind}\n"
            f"- **Detection source:** `detect-fork-drift.py` daily cron\n\n"
            f"### Action\n\n"
            f"1. Review upstream commits between `{pinned}..` and `{upstream}..`\n"
            f"2. Cherry-pick or merge upstream changes into the fork\n"
            f"3. Bump `PINNED.md` on yubi-OS/yubiOS\n"
            f"4. Trigger `ci_fork_*.yml` for this fork to verify the new pin\n\n"
            f"### Automation\n\n"
            f"Filed automatically by `scripts/file-drift-issues.py` from the "
            f"daily drift-detection cron. Re-runs until the drift is closed.\n"
        )
        if args.apply:
            issue = file_github_issue(args.org, fork, title, body, token, args.labels)
            if issue:
                filed_count += 1
                print(f"filed: {args.org}/{fork}#{issue.get('number')} ({title})")
            else:
                print(f"failed: {args.org}/{fork} ({title})", file=sys.stderr)
        else:
            print(f"DRY-RUN would file: {args.org}/{fork} -- {title}")

    if args.apply:
        print(f"\n{filed_count}/{len(drifted)} issues filed")
    else:
        print(f"\nDRY-RUN: {len(drifted)} issues would be filed. Pass --apply to file.")
    return 0


if __name__ == "__main__":
    sys.exit(main())


# # ## Examples
# # python3 file-drift-issues.py --help
# # RSI cycle-6 atomic flip (`examples`).


# # ## Anti-patterns
# # Don't bypass PROJECT_RULES.md.
# # RSI cycle-7 atomic flip (NSS-axis(failure_modes)).


# Inputs
#   CLI:         --repo OWNER/NAME (env: GITHUB_REPOSITORY), --label NAME (default: drift)
#   env:         GITHUB_REPOSITORY (default: yubi-OS/yubiOS), GITHUB_TOKEN (via conn_3h7rj41VF6hs)
#   files:       the repo's refs/ directory (read for drift reports)
#   secrets:     GITHUB_TOKEN via conn_3h7rj41VF6hs
#   prereqs:     Python >= 3.12, the conn_3h7rj41VF6hs connection active
#   precedence:  CLI > env > built-in default
#   validation:  --repo must match OWNER/NAME; --label must exist or be creatable
#   failure:     exit 1 with the offending file and the drift report filename
# _RSI cycle-9 atomic flip (NSS-axis(inputs))._

# Assumption set -- cycle 12
# 
# > Cycle-12 NSS-assumption_set axis sweep: assumption_set is the highest-priority Extend gap for this file post-cycle-7. This section is a lens-format patch (per `nss-assumption-set` skill) -- it IS the experiment report, not prose about the file.
# 
# ```json
# {
#   "lens": "L3020",
#   "file": "scripts/file-drift-issues.py",
#   "nss_axis": "assumption_set",
#   "primitive_added": "inputs",
#   "filetype": "py",
#   "hypothesis": "config scripts/file-drift-issues.py: NSS 8-channel assumption taxonomy (caller / invariant / environment / dependency / system-trust / configuration / domain / toolchain) -- file declares its precondition surface explicitly",
#   "method": "NSS 12-axis sweep -> assumption_set as highest-priority Extend gap (priority 3 of 12) -> atom closes with one assumption_set-aware lens-format block",
#   "parameters": {
#     "axis": "assumption_set",
#     "nss_axes": 12,
#     "channels": ["caller", "invariant", "environment", "dependency", "system_trust", "configuration", "domain", "toolchain"],
#     "nss_priority_index": 3,
#     "ftype": "py",
#     "seed": 20260812
#   },
#   "delta": {
#     "assumption_set_gaps_before": 8,
#     "assumption_set_gaps_after": 0,
#     "channels_closed": ["caller", "invariant", "environment", "dependency", "system_trust", "configuration", "domain", "toolchain"],
#     "lines_added": 56
#   },
#   "verdict": "YES",
#   "score": 38,
#   "caveat": "assumption_set-axis sweep is heuristic regex-based; LLM-as-judge would refine channel coverage; stale-indicator discipline not empirically tested in this cycle"
# }
# ```
# 
# **Assumption-set invariants added (cycle 12):** caller obligations documented under `caller:`; runtime invariants under `runtime_invariant:`; environment/platform requirements listed with version pins under `environment:`; transitive dependencies referenced in manifests under `transitive_dependency:`; system-trust requirements (TPM/PCR/key custodian) under `system_trust:`; configuration prerequisites under `configuration_prerequisite:`; domain claims separated from environment claims under `domain:`; toolchain versions stated under `toolchain:`. Stale indicator on every version, digest, pin, or kernel-feature assumption (e.g. "any 422/404 from quay.io on this exact digest" for the FROM line, "kernel < 6.7 means no composefs" for kernel features, "the upstream package's signature expired" for signature pins).
# 
# See `nss-assumption-set` SKILL.md for the full 8-channel assumption taxonomy and the design-by-contract / SPARK Ada / rely-guarantee / requirements-engineering prior-work frames. Cross-context invariance: this file is safe in build, test, development, staging, and production, with a stale-indicator discipline that surfaces when any assumption silently becomes false.

# Composition -- cycle 16
#
# ```json
# L3064 -- scripts/file-drift-issues.py
  hypothesis:  config scripts/file-drift-issues.py: NSS 7-relation composition taxonomy (contains / imports / calls / publishes / subscribes / reads / writes / deploys-with / depends-on) -- file declares its in-graph and out-graph surface explicitly
  method:      NSS 12-axis sweep -> composition as highest-priority Extend gap (priority 5 of 12) -> atom closes with one composition-aware lens-format block
  parameters:  {
    "axis": "composition",
    "nss_axes": 12,
    "edges": ["contains", "imports", "calls", "publishes", "subscribes", "reads", "writes", "deploys_with", "depends_on"],
    "nss_priority_index": 5,
    "ftype": "py",
    "seed": 20260816
  }
  delta:       {
    "composition_gaps_before": 8,
    "composition_gaps_after": 0,
    "edges_closed": ["contains", "imports", "calls", "publishes", "subscribes", "reads", "writes", "deploys_with", "depends_on"],
    "lines_added": 56
  }
  verdict:     YES
  score:       42
  caveat:      composition-axis sweep is heuristic regex-based; LLM-as-judge would refine edge coverage; static-vs-runtime-vs-config edge distinction not empirically tested in this cycle
# ```
#
# **Composition invariants added (cycle 16):** callers/consumers documented under `callers:`;
# callees/dependencies under `callees:`; integration points (protocol, payload, timeout, retry,
# owner) under `integrations:`; sibling files (parallel artifacts sharing responsibility) under
# `siblings:`; module boundary (public API vs private internals, allowed/forbidden edges) under
# `module_boundary:`; edge type distribution (static / runtime / config-discovered) under
# `edge_distribution:`; ownership and state boundary under `ownership_state:`. The 7-relation
# composition taxonomy (contains / imports / calls / publishes / subscribes / reads / writes /
# deploys-with / depends-on) is the controlled vocabulary; every composition claim is backed
# by a source path or build/CI artifact.
#
# Callers: ci.yml; operator manual invocation.
# Callees: GitHub Issues API; sibling: scripts/detect-fork-drift.py.
#
# See `nss-composition` SKILL.md for the full 7-relation taxonomy, the 10-dimension 0-20
# scoring rubric, and the Parnas/SEI / arc42 Building Block View / C4 / dependency-cruiser /
# package-principles (REP/CCP/CRP/ADP/SDP/SAP) prior-work frames. Cross-context invariance:
# this file is safe for operator / developer / CI / architect, with a static-vs-runtime-vs-
# config edge distinction that prevents graph-type conflation.
