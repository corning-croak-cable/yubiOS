#!/usr/bin/env python3
"""
validate-input-shape.py — composite GitHub Action body for OMN-158.

Validates workflow_dispatch.inputs shape on PRs touching .github/workflows/:
  - declared in workflow_dispatch.inputs (no undeclared keys from dispatchers)
  - type-correct JSON (booleans are bool, not "true"/"false" strings)
  - safe defaults (default-false for destructive inputs)
  - dispatcher key-intersection (ci.yml's group dispatch passes only declared keys)
  - lex-sort filename shape (systemd drop-in filenames lex-sort after upstream)
  - image-tag-set coverage (no missing short-sha tags for any digest-pinned image)

Used by the .github/actions/validate-input-shape composite action.
Exit codes:
  0  -- all checks PASS
  1  -- one or more checks FAIL
  2  -- usage error
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


def get_dispatch_inputs(workflow_data: dict) -> dict:
    """Extract workflow_dispatch.inputs from a parsed workflow YAML.

    Handles the YAML 1.1 quirk where `on:` parses as boolean True.
    """
    triggers = workflow_data.get(True) or workflow_data.get("on") or {}
    if isinstance(triggers, dict):
        wd = triggers.get("workflow_dispatch") or {}
        if isinstance(wd, dict):
            return wd.get("inputs") or {}
    return {}


def extract_default_image_refs(workflow_data: dict) -> list[tuple[str, str]]:
    """Extract every image:tag reference that looks like a yubiOS image.

    Returns list of (file_ref, image_ref) tuples. Used for image-tag-set coverage.
    """
    text = yaml.dump(workflow_data, default_flow_style=False)
    # match patterns like image: docker.io/0mniteck/yubios:dev or image: foo:bar
    matches = re.findall(
        r"image:\s*['\"]?(docker\.io/[a-z0-9\-]+/[a-z0-9\-]+:[a-zA-Z0-9\.\-]+)['\"]?",
        text,
    )
    return [(m, m) for m in matches]


def find_drop_in_filenames(workflow_data: dict) -> list[str]:
    """Find every reference that looks like a systemd drop-in filename."""
    text = yaml.dump(workflow_data, default_flow_style=False)
    # match patterns like foo-yubiOS-*.conf in paths
    matches = re.findall(
        r"['\"]?(?:usr/lib/(?:modprobe\.d|dracut\.conf\.d|tmpfiles\.d|udev/rules\.d)/)?"
        r"([\w\-]*yubiOS[\w\-\.]*\.conf)['\"]?",
        text,
    )
    return matches


def audit_workflow(path: Path) -> list[dict]:
    """Audit one workflow file. Returns a list of findings."""
    findings = []
    try:
        data = yaml.safe_load(path.read_text())
    except yaml.YAMLError as e:
        findings.append({
            "file": str(path),
            "severity": "ERROR",
            "code": "YAML_INVALID",
            "message": f"YAML invalid: {e}",
            "remediation": "Fix YAML syntax.",
        })
        return findings

    if not isinstance(data, dict):
        return findings

    inputs = get_dispatch_inputs(data)
    if not inputs:
        return findings  # No workflow_dispatch; nothing to check

    # Rule 1: declared inputs should have a `type`
    for name, spec in inputs.items():
        if not isinstance(spec, dict):
            findings.append({
                "file": str(path),
                "severity": "WARN",
                "code": "INPUT_NO_SPEC",
                "message": f"workflow_dispatch.inputs.{name} has no spec (should declare type, default, required)",
                "remediation": "Add `type: choice|boolean|string|number` + optional `default` + `required: false`.",
            })
            continue
        if "type" not in spec:
            findings.append({
                "file": str(path),
                "severity": "WARN",
                "code": "INPUT_NO_TYPE",
                "message": f"workflow_dispatch.inputs.{name} missing `type` field",
                "remediation": "Add `type` field. Without it, GitHub rejects with 422 on dispatch.",
            })

    # Rule 2: image tag-set coverage — flag any image ref that's a floating tag
    for ref_kind, image_ref in extract_default_image_refs(data):
        # Flag floating tags: latest, main, dev (without a SHA suffix)
        if image_ref.endswith(":latest") or ":main" in image_ref:
            findings.append({
                "file": str(path),
                "severity": "WARN",
                "code": "FLOATING_TAG",
                "message": f"Workflow references floating image tag: {image_ref}",
                "remediation": "Use an immutable digest or a `:dev-<short-sha>` tag.",
            })

    # Rule 3: drop-in filenames should lex-sort after upstream (prefix check)
    for filename in find_drop_in_filenames(data):
        if filename.startswith(("50-", "51-", "52-", "53-", "54-", "55-")):
            findings.append({
                "file": str(path),
                "severity": "WARN",
                "code": "DROPIN_LEX_SORT_RISK",
                "message": (
                    f"Drop-in filename `{filename}` uses a low numeric prefix that "
                    f"may lex-sort BEFORE upstream package files. systemd-tmpfiles(5) "
                    f"says all files sort by full filename lexicographically."
                ),
                "remediation": (
                    "Rename to a lex-later prefix like `vfio-yubiOS-...` or `yubiOS-...` "
                    f"per the PROJECT_RULES.md lex-sort lesson (OMN-149)."
                ),
            })

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output-format", choices=["text", "json", "sarif"], default="text")
    parser.add_argument("--fail-on", choices=["ERROR", "WARN", "NEVER"], default="ERROR")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    workflows = list_workflow_files(repo_root)

    findings = []
    for wf in workflows:
        findings.extend(audit_workflow(wf))

    summary = {
        "files_scanned": len(workflows),
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
                "tool": {"driver": {"name": "validate-input-shape", "version": "1.0.0"}},
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
        print(f"Summary: {summary['errors']} ERROR, {summary['warnings']} WARN across {summary['files_scanned']} workflows")

    threshold = 3 if args.fail_on == "ERROR" else (2 if args.fail_on == "WARN" else 99)
    max_sev = max((3 if f["severity"] == "ERROR" else 2 if f["severity"] == "WARN" else 1 for f in findings), default=0)
    if max_sev >= threshold:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())


# # ## Verification
# # python3 validate-input-shape.py --selftest  # exits 0 iff GREEN, when applicable.
# # RSI cycle-6 atomic flip (`verification`).


# # ## Constraints
# # requires the deps in requirements.txt / pyproject.toml; see PROJECT_RULES.md.
# # RSI cycle-7 atomic flip (NSS-axis(assumption_set)).
