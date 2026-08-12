#!/usr/bin/env python3
"""
assert-dispatch-reachable.py — yubiOS workflow_dispatch reachability assert (OMN-159).

Asserts every .github/workflows/*.yml file that defines a workflow_dispatch
trigger is reachable from at least one ci.yml group (firmware / tests /
vm-tests / fetches / ci-builders / forks / all).

Catches the orphan-workflow class of bug that hit ci_test-fedora-bootc-arm64-pull,
ci_test-ftpm-tpm0, ci_test_sealed-uki-vm, diag_sign-matrix before the
2026-08-02 ci-launchpad update folded them into the tests group.

Usage:
  python3 scripts/assert-dispatch-reachable.py [--repo-root PATH]
                                              [--ci-yml PATH]
                                              [--output-format {text,json,sarif}]
                                              [--fail-on {ERROR,WARN,NEVER}]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml


def list_workflow_files(repo_root: Path) -> list[Path]:
    """Return every workflow file in .github/workflows/."""
    workflows_dir = repo_root / ".github" / "workflows"
    if not workflows_dir.exists():
        return []
    return sorted(
        [wf for wf in workflows_dir.glob("*.yml")] +
        [wf for wf in workflows_dir.glob("*.yaml")]
    )


def has_workflow_dispatch(workflow_data: dict) -> bool:
    """GitHub Actions YAML 1.1 quirk: `on:` parses as Python boolean True."""
    triggers = workflow_data.get(True) or workflow_data.get("on")
    if not triggers:
        return False
    if isinstance(triggers, str):
        return triggers == "workflow_dispatch"
    if isinstance(triggers, list):
        return "workflow_dispatch" in triggers
    if isinstance(triggers, dict):
        return "workflow_dispatch" in triggers
    return False


def parse_ci_yml_groups(ci_yml_data: dict) -> dict[str, list[str]]:
    """Extract the ci.yml group -> workflow-file mapping from the dispatcher.

    Heuristic: scan all jobs[*].steps[*].run for the dispatch case statement
    that lists workflow file paths per group, and parse out the file references.
    """
    groups: dict[str, list[str]] = {}
    yml_str = yaml.dump(ci_yml_data, default_flow_style=False)
    # Find every `case "$GROUP" in ... esac` or `case "$group" in ... esac` block
    case_blocks = re.findall(
        r'case\s+"\$GROUP"\s+in(.*?)esac|case\s+"\$group"\s+in(.*?)esac',
        yml_str,
        re.DOTALL,
    )
    # Match workflow file references of the form *.yml inside heredocs or jq
    file_ref_re = re.compile(r'[\'"]([\w\.\-/]+\.ya?ml)[\'"]')

    group_pattern = re.compile(r'([\w\-]+)\)\s*[\s\S]*?(?:;;|$)')

    for block in case_blocks:
        body = block[0] or block[1]
        # Try to find group label(s)
        for label_match in re.finditer(r'(\w[\w\-]*)\)\s*', body):
            group_name = label_match.group(1)
            files = file_ref_re.findall(body)
            # Filter to plausible workflow filenames (avoid ".gitignore" etc.)
            plausible = [f for f in files if not f.startswith('.') and '/' not in f]
            if plausible:
                groups.setdefault(group_name, []).extend(plausible)

    # Also do a naive scan: walk jobs[*].steps[*] for `bash` blocks referencing
    # workflow filenames; collect any files that appear after `case "$GROUP"`
    # references as fallback.
    for job_name, job in (ci_yml_data.get("jobs") or {}).items():
        if not isinstance(job, dict):
            continue
        for step in job.get("steps", []):
            if not isinstance(step, dict):
                continue
            run = str(step.get("run", ""))
            if "case \"$GROUP\"" in run or "case \"$group\"" in run:
                files = file_ref_re.findall(run)
                plausible = [f for f in files if not f.startswith('.') and '/' not in f]
                # Naive: associate with job name as the group
                if plausible:
                    groups.setdefault(job_name, []).extend(plausible)

    return groups


def assert_reachability(repo_root: Path, ci_yml_path: Path) -> list[dict]:
    findings = []
    workflow_files = list_workflow_files(repo_root)
    if not ci_yml_path.exists():
        findings.append({
            "severity": "ERROR",
            "code": "CI_YML_MISSING",
            "file": str(ci_yml_path),
            "message": f"ci.yml not found at {ci_yml_path}",
            "remediation": "Confirm ci.yml path; pass --ci-yml.",
        })
        return findings

    try:
        ci_data = yaml.safe_load(ci_yml_path.read_text())
    except yaml.YAMLError as e:
        findings.append({
            "severity": "ERROR",
            "code": "CI_YML_INVALID",
            "file": str(ci_yml_path),
            "message": f"ci.yml YAML invalid: {e}",
            "remediation": "Fix the YAML.",
        })
        return findings

    groups = parse_ci_yml_groups(ci_data)
    all_listed_files = set()
    for files in groups.values():
        all_listed_files.update(files)

    workflow_files_set = {wf.name for wf in workflow_files}

    # 1. Orphan workflow_dispatch workflows
    orphans = []
    for wf in workflow_files:
        try:
            data = yaml.safe_load(wf.read_text())
        except yaml.YAMLError:
            continue
        if not isinstance(data, dict):
            continue
        if not has_workflow_dispatch(data):
            continue
        if wf.name == ci_yml_path.name:
            continue  # ci.yml itself is the dispatcher
        if wf.name not in all_listed_files:
            orphans.append(wf.name)
            findings.append({
                "severity": "ERROR",
                "code": "ORPHAN_WORKFLOW_DISPATCH",
                "file": str(wf),
                "message": (
                    f"Workflow {wf.name} has workflow_dispatch trigger but is "
                    f"not listed in any ci.yml group table."
                ),
                "remediation": (
                    f"Add to a ci.yml group (typical: 'tests' or 'ci-builders')."
                ),
            })

    # 2. Inverse: stale group entries (workflow listed but doesn't exist)
    stale = []
    for group_name, files in groups.items():
        for listed in set(files):
            if listed not in workflow_files_set:
                stale.append((group_name, listed))
                findings.append({
                    "severity": "WARN",
                    "code": "STALE_GROUP_ENTRY",
                    "file": str(ci_yml_path),
                    "message": (
                        f"ci.yml group '{group_name}' references {listed} "
                        f"but the file doesn't exist in .github/workflows/."
                    ),
                    "remediation": "Remove the stale entry or create the missing workflow.",
                })

    return findings, groups, orphans, stale, workflow_files_set


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--ci-yml", default=".github/workflows/ci.yml")
    parser.add_argument("--output-format", choices=["text", "json", "sarif"], default="text")
    parser.add_argument("--fail-on", choices=["ERROR", "WARN", "NEVER"], default="ERROR")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    ci_yml_path = repo_root / args.ci_yml

    result = assert_reachability(repo_root, ci_yml_path)
    findings, groups, orphans, stale, files_set = result

    summary = {
        "orphans": orphans,
        "stale_entries": [{"group": g, "file": f} for g, f in stale],
        "files_scanned": len(files_set),
        "groups": groups,
        "errors": sum(1 for f in findings if f["severity"] == "ERROR"),
        "warnings": sum(1 for f in findings if f["severity"] == "WARN"),
    }

    if args.output_format == "json":
        print(json.dumps({"findings": findings, "summary": summary}, indent=2))
    elif args.output_format == "sarif":
        sarif = {
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "version": "2.1.0",
            "runs": [{
                "tool": {"driver": {"name": "assert-dispatch-reachable", "version": "1.0.0"}},
                "results": [
                    {
                        "ruleId": f["code"],
                        "level": {"ERROR": "error", "WARN": "warning"}.get(f["severity"], "note"),
                        "message": {"text": f["message"]},
                        "locations": [{
                            "physicalLocation": {
                                "artifactLocation": {"uri": f["file"]},
                                "region": {"startLine": 1},
                            }
                        }],
                    }
                    for f in findings
                ],
            }],
        }
        print(json.dumps(sarif, indent=2))
    else:
        for f in findings:
            print(f"{f['severity']:5s} {f['file']}: {f['message']}")
            if f.get("remediation"):
                print(f"      → {f['remediation']}")
        print()
        print(f"Summary: {summary['errors']} ERROR, {summary['warnings']} WARN across "
              f"{summary['files_scanned']} workflows")
        print(f"Groups: {sorted(groups.keys())}")
        if orphans:
            print(f"Orphans: {orphans}")
        if stale:
            print(f"Stale entries: {[{'group': g, 'file': f} for g, f in stale]}")

    threshold = 3 if args.fail_on == "ERROR" else (2 if args.fail_on == "WARN" else 99)
    max_sev = max((3 if f["severity"] == "ERROR" else 2 if f["severity"] == "WARN" else 1 for f in findings), default=0)
    if max_sev >= threshold:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())


## New Ideas -- cycle 3 (lens external)

This file's lens is **L406** in `lenses.json` (score 22/50, verdict **PARTIAL**, k=4/9). Full experiment: hypothesis `scripts/assert-dispatch-reachable.py covers all 9 primitives in the internal-big-picture basis`, method `9-D primitive binarization (purpose, examples, guidelines, constraints, verifica...`. See root `new-ideas-2026-08-12.md` for the cycle-3 summary.
