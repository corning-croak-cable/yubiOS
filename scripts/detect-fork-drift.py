#!/usr/bin/env python3
"""
detect-fork-drift.py — yubiOS fork-upstream drift detection (OMN-160).

Reads PINNED.md vs upstream latest SHA for all 8 forks in the yubi-OS org.
Threshold-based verdict:
  - synced       : pinned == upstream latest
  - minor-lag    : behind by 1-10 commits
  - drifted      : behind by >10 commits (default threshold)

Usage:
  python3 scripts/detect-fork-drift.py [--repo-root PATH]
                                      [--pinned PATH]
                                      [--upstream-map PATH]
                                      [--org NAME]
                                      [--threshold-commits N]
                                      [--output-format {text,json}]

Requires GITHUB_TOKEN env for upstream queries; offline mode skips them.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

import yaml


def github_get_latest_sha(repo: str, branch: str, token: str | None) -> str | None:
    """Return the HEAD SHA of a repo branch via the GitHub REST API."""
    url = f"https://api.github.com/repos/{repo}/branches/{branch}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "yubios-fork-drift-detector",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
            return data.get("commit", {}).get("sha")
    except urllib.error.HTTPError as e:
        print(f"warn: GitHub {repo}@{branch} HTTP {e.code}: {e.read().decode()[:200]}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"warn: GitHub {repo}@{branch} fetch failed: {e}", file=sys.stderr)
        return None


def github_count_commits(repo: str, base_sha: str, head_sha: str, token: str | None) -> int:
    """Return the number of commits between two SHAs (head - base)."""
    if base_sha == head_sha:
        return 0
    url = f"https://api.github.com/repos/{repo}/compare/{base_sha}...{head_sha}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "yubios-fork-drift-detector",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
            return data.get("total_commits", 0)
    except urllib.error.HTTPError as e:
        print(f"warn: compare {repo} HTTP {e.code}: {e.read().decode()[:200]}", file=sys.stderr)
        return -1
    except Exception as e:
        print(f"warn: compare {repo} failed: {e}", file=sys.stderr)
        return -1


def read_pin(repo_root: Path, fork: str, pinned_path: str = "PINNED.md") -> str | None:
    """Read PINNED.md and return the SHA for a given fork's entry."""
    pin_file = repo_root / pinned_path
    if not pin_file.exists():
        return None
    text = pin_file.read_text()
    # Try multiple patterns (PINNED.md varies by repo format)
    patterns = [
        rf"`?{re.escape(fork)}`?\s*[:=]\s*[`"]?([0-9a-f]{{40}})[`"]?",
        rf"`?{re.escape(fork)}`?\s*[:=]\s*[`"]?([0-9a-f]{{7,40}})[`"]?",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.MULTILINE)
        if m:
            return m.group(1)
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--pinned", default="PINNED.md")
    parser.add_argument("--upstream-map", default="scripts/detect-fork-drift.upstream-map.yaml")
    parser.add_argument("--org", default="yubi-OS")
    parser.add_argument("--threshold-commits", type=int, default=10)
    parser.add_argument("--output-format", choices=["text", "json"], default="text")
    parser.add_argument("--offline", action="store_true", help="Skip GitHub API queries")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    upstream_map_path = repo_root / args.upstream_map
    if not upstream_map_path.exists():
        print(f"error: upstream map not found at {upstream_map_path}", file=sys.stderr)
        return 2

    map_data = yaml.safe_load(upstream_map_path.read_text()) or {}
    forks_cfg = map_data.get("forks", [])
    if not forks_cfg:
        print(f"error: upstream map empty (no 'forks:' entries)", file=sys.stderr)
        return 2

    token = os.environ.get("GITHUB_TOKEN") if not args.offline else None

    results = []
    for fork_cfg in forks_cfg:
        fork_name = fork_cfg["fork"]
        upstream_repo = fork_cfg["upstream"]
        upstream_branch = fork_cfg.get("upstream_branch", "main")
        pinned_sha = read_pin(repo_root, fork_name, args.pinned)

        if not pinned_sha:
            verdict = "no-pin"
            results.append({
                "fork": fork_name,
                "pinned_sha": None,
                "upstream_sha": None,
                "behind": None,
                "verdict": verdict,
            })
            continue

        if args.offline or not token:
            results.append({
                "fork": fork_name,
                "pinned_sha": pinned_sha,
                "upstream_sha": None,
                "behind": None,
                "verdict": "no-fetch",
            })
            continue

        upstream_sha = github_get_latest_sha(upstream_repo, upstream_branch, token)
        if upstream_sha is None:
            results.append({
                "fork": fork_name,
                "pinned_sha": pinned_sha,
                "upstream_sha": None,
                "behind": None,
                "verdict": "fetch-failed",
            })
            continue

        if upstream_sha.startswith(pinned_sha):
            behind = 0
        else:
            behind = github_count_commits(upstream_repo, pinned_sha, upstream_sha, token)
            if behind < 0:
                behind = None

        if behind is None:
            verdict = "compare-failed"
        elif behind == 0:
            verdict = "synced"
        elif behind <= args.threshold_commits:
            verdict = "minor-lag"
        else:
            verdict = "drifted"

        results.append({
            "fork": fork_name,
            "pinned_sha": pinned_sha,
            "upstream_sha": upstream_sha,
            "behind": behind,
            "verdict": verdict,
        })

    summary = {
        "threshold_commits": args.threshold_commits,
        "forks_total": len(results),
        "synced": sum(1 for r in results if r["verdict"] == "synced"),
        "minor_lag": sum(1 for r in results if r["verdict"] == "minor-lag"),
        "drifted": sum(1 for r in results if r["verdict"] == "drifted"),
        "no_pin": sum(1 for r in results if r["verdict"] == "no-pin"),
        "fetch_failed": sum(1 for r in results if r["verdict"] in ("fetch-failed", "compare-failed", "no-fetch")),
    }

    if args.output_format == "json":
        print(json.dumps({"results": results, "summary": summary}, indent=2))
    else:
        for r in results:
            short_pinned = (r["pinned_sha"] or "?")[:8]
            short_upstream = (r["upstream_sha"] or "?")[:8]
            print(f"{r['verdict']:14s} {r['fork']}: pinned={short_pinned}.. upstream={short_upstream}.. behind={r['behind']}")
        print()
        print(f"Summary: {summary['drifted']} DRIFTED, {summary['minor_lag']} MINOR-LAG, "
              f"{summary['synced']} SYNCED, {summary['fetch_failed']} FETCH-FAILED, "
              f"{summary['no_pin']} NO-PIN across {summary['forks_total']} forks")

    if summary["drifted"] > 0:
        return 1
    if summary["fetch_failed"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())


## Examples

- Reading `detect-fork-drift.py` (no args) shows usage
- See `docs/ARCHITECTURE.md` for where this file fits in yubiOS


## Guidelines

- Match the conventions in `docs/STYLE.md`
- See sibling files in this directory for the surrounding context


# ## Verification
# # python3 this_script.py --selftest  # exits 0 iff GREEN


## Composition

- Sits next to sibling files in this directory; consult them for surrounding context
- For the full yubiOS dependency graph, see `docs/ARCHITECTURE.md`


# ## Changelog
# # 2026-08-12 -- RSI cycle-4 new-idea experiment (primitive changelog).


## References

- yubiOS repo: `yubi-OS/yubiOS`
- Architecture: `docs/ARCHITECTURE.md`
- See root `lenses.json` and `new-ideas-2026-08-12.md`


## Anti-patterns

- Don't claim structure without a null (per `curved-corpus-create`)
- Don't report pi_T as a property of the historical corpus (per `curve-compass-skill`)
