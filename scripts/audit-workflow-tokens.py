#!/usr/bin/env python3
"""
audit-workflow-tokens.py — yubiOS workflow token-scope audit (OMN-161).

Walks every .github/workflows/*.yml file in the repo and flags:
  1. Surviving secrets.GH_TK references (PR #148 cleanup was 2026-07-29)
  2. Over-scoped top-level permissions vs per-job permissions
  3. Unknown-secret references (per the allowlist)
  4. job-level vs workflow-level permission mismatches

Usage:
  python3 scripts/audit-workflow-tokens.py [--repo-root PATH]
                                           [--secrets-config PATH]
                                           [--offline]
                                           [--output-format {text,json,sarif}]
                                           [--fail-on {ERROR,WARN,INFO,NEVER}]

Default exit code:
  0  -- no findings at --fail-on threshold
  1  -- findings at --fail-on threshold present
  2  -- usage error
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import yaml


SEVERITY_ORDER = {"ERROR": 3, "WARN": 2, "INFO": 1}


def load_secrets_allowlist(path: Path | None) -> set[str]:
    """Load the allowlist of known repo secret names. Empty if file missing."""
    if path is None or not path.exists():
        return set()
    try:
        data = yaml.safe_load(path.read_text())
    except yaml.YAMLError as e:
        print(f"warn: secrets allowlist YAML invalid: {e}", file=sys.stderr)
        return set()
    return set((data or {}).get("known_secrets", []))


def find_secrets_refs(node: Any, path: tuple[str, ...] = ()) -> list[dict]:
    """Recursively find every `secrets.X` reference under the given YAML node."""
    refs = []
    if isinstance(node, dict):
        for k, v in node.items():
            refs.extend(find_secrets_refs(v, path + (k,)))
    elif isinstance(node, list):
        for i, item in enumerate(node):
            refs.extend(find_secrets_refs(item, path + (f"[{i}]",)))
    elif isinstance(node, str):
        for m in re.finditer(r"\$\{\{\s*secrets\.([A-Z0-9_]+)\s*\}\}", node):
            refs.append({"secret": m.group(1), "context": ".".join(path), "value": m.group(0)})
    return refs


def normalize_perms(perms: Any) -> set[str]:
    """Normalize a permissions block (string or dict) into a set of scoped perms.

    GitHub Actions accepts:
      permissions: read-all          (shorthand)
      permissions: { actions: read } (scoped dict)
      permissions: {}                (no perms)
    """
    if perms is None:
        return set()
    if isinstance(perms, str):
        # read-all / write-all / {}
        if perms == "read-all":
            return {"read-all"}
        if perms == "write-all":
            return {"write-all"}
        return {perms}
    if isinstance(perms, dict):
        return {f"{k}:{v}" for k, v in perms.items()}
    return set()


def audit_workflow_file(path: Path, allowlist: set[str]) -> list[dict]:
    """Audit one workflow file. Return a list of findings."""
    findings = []
    try:
        data = yaml.safe_load(path.read_text())
    except yaml.YAMLError as e:
        findings.append({
            "file": str(path),
            "line": 0,
            "severity": "ERROR",
            "code": "YAML_INVALID",
            "message": f"Workflow YAML is invalid: {e}",
            "remediation": "Fix the YAML syntax error.",
        })
        return findings

    if not isinstance(data, dict):
        return findings  # empty or scalar; nothing to audit

    # GitHub Actions YAML 1.1 quirk: `on:` parses as Python boolean True.
    workflow_meta = data.get(True) or data.get("on") or {}
    top_perms = normalize_perms(data.get("permissions"))

    # 1. Walk all secrets.X references
    for ref in find_secrets_refs(data):
        secret = ref["secret"]
        ctx = ref["context"]
        if secret == "GH_TK":
            findings.append({
                "file": str(path),
                "line": 0,
                "severity": "ERROR",
                "code": "GH_TK_REFERENCED",
                "message": (
                    f"Workflow still references the retired secrets.GH_TK "
                    f"(PR #148 cleanup, 2026-07-29). Context: {ctx}."
                ),
                "remediation": (
                    "Replace with github.token; ensure permissions: "
                    "{contents: write} is declared at workflow or job level."
                ),
            })
        elif secret not in allowlist:
            findings.append({
                "file": str(path),
                "line": 0,
                "severity": "WARN",
                "code": "UNKNOWN_SECRET",
                "message": (
                    f"Workflow references secrets.{secret} (not in allowlist). "
                    f"Context: {ctx}."
                ),
                "remediation": (
                    f"Add secrets.{secret} to "
                    f"scripts/audit-workflow-tokens.allowlist.yaml if it's a "
                    f"known repo secret, or remove the reference."
                ),
            })

    # 2. Per-job permissions audit
    for job_name, job in (data.get("jobs") or {}).items():
        if not isinstance(job, dict):
            continue
        job_perms = normalize_perms(job.get("permissions", top_perms))
        # If top-level is more restrictive than job-level, that's a YAML error
        if top_perms and job_perms:
            # GitHub Actions rule: job-level can't grant scopes the workflow
            # doesn't grant. If top is read-only and job grants write, that's
            # a YAML semantic error.
            write_scopes_top = {p for p in top_perms if p.endswith(":write") or p == "write-all"}
            write_scopes_job = {p for p in job_perms if p.endswith(":write") or p == "write-all"}
            if not write_scopes_top and write_scopes_job:
                findings.append({
                    "file": str(path),
                    "line": 0,
                    "severity": "WARN",
                    "code": "JOB_WIDER_THAN_WORKFLOW",
                    "message": (
                        f"Job '{job_name}' grants write scopes ({sorted(write_scopes_job)}) "
                        f"but workflow top-level permissions are read-only "
                        f"({sorted(top_perms)})."
                    ),
                    "remediation": (
                        "Either widen the top-level permissions to match the "
                        "job's needs, or remove the unused write scopes from the job."
                    ),
                })

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo-root", default=".", help="Repo root (default: .)")
    parser.add_argument("--secrets-config", default="scripts/audit-workflow-tokens.allowlist.yaml",
                        help="Path to secrets allowlist YAML (default: scripts/audit-workflow-tokens.allowlist.yaml)")
    parser.add_argument("--offline", action="store_true", help="Don't call GitHub API; rely on the allowlist only")
    parser.add_argument("--output-format", choices=["text", "json", "sarif"], default="text")
    parser.add_argument("--fail-on", choices=["ERROR", "WARN", "INFO", "NEVER"], default="ERROR",
                        help="Exit non-zero threshold (default: ERROR)")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    workflows_dir = repo_root / ".github" / "workflows"
    if not workflows_dir.exists():
        print(f"error: {workflows_dir} does not exist", file=sys.stderr)
        return 2

    allowlist = load_secrets_allowlist(repo_root / args.secrets_config)
    # Always allow GITHUB_TOKEN (auto-injected by Actions)
    allowlist.add("GITHUB_TOKEN")

    findings = []
    files_scanned = 0
    for wf in sorted(workflows_dir.glob("*.yml")) + sorted(workflows_dir.glob("*.yaml")):
        files_scanned += 1
        findings.extend(audit_workflow_file(wf, allowlist))

    summary = {
        "files_scanned": files_scanned,
        "errors": sum(1 for f in findings if f["severity"] == "ERROR"),
        "warnings": sum(1 for f in findings if f["severity"] == "WARN"),
        "info": sum(1 for f in findings if f["severity"] == "INFO"),
    }

    if args.output_format == "json":
        print(json.dumps({"findings": findings, "summary": summary}, indent=2))
    elif args.output_format == "sarif":
        # SARIF v2.1.0 minimal — sufficient for GitHub code scanning.
        sarif = {
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "version": "2.1.0",
            "runs": [{
                "tool": {"driver": {"name": "audit-workflow-tokens", "version": "1.0.0"}},
                "results": [
                    {
                        "ruleId": f["code"],
                        "level": {"ERROR": "error", "WARN": "warning", "INFO": "note"}.get(f["severity"], "note"),
                        "message": {"text": f["message"]},
                        "locations": [{
                            "physicalLocation": {
                                "artifactLocation": {"uri": f["file"]},
                                "region": {"startLine": f["line"] or 1},
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
        print(f"Summary: {summary['errors']} ERROR, {summary['warnings']} WARN, {summary['info']} INFO "
              f"across {summary['files_scanned']} workflows")

    threshold = SEVERITY_ORDER.get(args.fail_on, 99) if args.fail_on != "NEVER" else 99
    max_severity = max((SEVERITY_ORDER.get(f["severity"], 0) for f in findings), default=0)
    if max_severity >= threshold:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
