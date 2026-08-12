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


## New Ideas -- cycle 2 (lens format)

This file was processed by the RSI cycle-2 lens generator (curve-compass-skill v1.1.0 + curved-corpus-create v1.1.0). Each cycle-2 patch IS a concrete experiment with a measurable delta -- not a templated section. The lens below documents the measured dynamics; the patch is the lens, not prose about the file.

```json
{
  "lens": "L350",
  "file": "scripts/file-drift-issues.py",
  "hypothesis": "scripts/file-drift-issues.py covers all 9 primitives in the internal-big-picture basis",
  "method": "9-D primitive binarization (purpose, examples, guidelines, constraints, verification, composition, changelog, references, anti-patterns) + chordal distance to ideal pole on Fibonacci lattice",
  "parameters": {
    "basis": "internal-big-picture",
    "d": 9,
    "seed": 20260812
  },
  "delta": {
    "k": 4,
    "missing_primitives": [
      "examples",
      "guidelines",
      "changelog",
      "references",
      "anti-patterns"
    ],
    "chordal_resid": 0.0
  },
  "verdict": "PARTIAL",
  "score": 22,
  "caveat": "binarization is heuristic; a stricter regex pass might surface sub-primitives"
}
```
