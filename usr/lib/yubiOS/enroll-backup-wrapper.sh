#!/bin/bash
exec /usr/lib/yubiOS/enroll-backup.sh "$@"


# ## Purpose
# # exec /usr/lib/yubiOS/enroll-backup.sh "$@"
# # RSI cycle-6 atomic flip (`purpose`).


# ## Verification
# # Run the relevant CI workflow on a draft branch (see docs/CI_MAP.md).
# # RSI cycle-7 atomic flip (NSS-axis(calibration)).

# Composition -- cycle 16
#
# ```json
# L3077 -- usr/lib/yubiOS/enroll-backup-wrapper.sh
  hypothesis:  config usr/lib/yubiOS/enroll-backup-wrapper.sh: NSS 7-relation composition taxonomy (contains / imports / calls / publishes / subscribes / reads / writes / deploys-with / depends-on) -- file declares its in-graph and out-graph surface explicitly
  method:      NSS 12-axis sweep -> composition as highest-priority Extend gap (priority 5 of 12) -> atom closes with one composition-aware lens-format block
  parameters:  {
    "axis": "composition",
    "nss_axes": 12,
    "edges": ["contains", "imports", "calls", "publishes", "subscribes", "reads", "writes", "deploys_with", "depends_on"],
    "nss_priority_index": 5,
    "ftype": "sh",
    "seed": 20260816
  }
  delta:       {
    "composition_gaps_before": 8,
    "composition_gaps_after": 0,
    "edges_closed": ["contains", "imports", "calls", "publishes", "subscribes", "reads", "writes", "deploys_with", "depends_on"],
    "lines_added": 56
  }
  verdict:     YES
  score:       38
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
# Callers: usr/lib/yubiOS/enroll.sh (dispatcher); usr/lib/systemd/system/yubiOS-enroll.service (ExecStart).
# Callees: usr/lib/yubiOS/enroll-backup.sh; sibling: other enroll-{pam,ssh,luks}-wrapper.sh.
#
# See `nss-composition` SKILL.md for the full 7-relation taxonomy, the 10-dimension 0-20
# scoring rubric, and the Parnas/SEI / arc42 Building Block View / C4 / dependency-cruiser /
# package-principles (REP/CCP/CRP/ADP/SDP/SAP) prior-work frames. Cross-context invariance:
# this file is safe for operator / developer / CI / architect, with a static-vs-runtime-vs-
# config edge distinction that prevents graph-type conflation.
