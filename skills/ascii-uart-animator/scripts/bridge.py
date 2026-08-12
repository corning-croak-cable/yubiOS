"""Shared helpers for posting bash scripts to the rock1 shell bridge."""
import json
import time
import urllib.request

BRIDGE_URL = "https://rock1.tail3a04f5.ts.net/run"


def post_to_bridge(bash_script, timeout=120):
    """POST an argv-array command to the rock1 bridge and return (status, elapsed, response_text)."""
    body = json.dumps({"command": ["bash", "-c", bash_script]})
    req = urllib.request.Request(
        BRIDGE_URL,
        data=body.encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        resp = r.read().decode("utf-8")
    return r.status, time.time() - t0, resp


def frame_ansi(line_repr):
    """printf line that writes one frame with ANSI clear+home prefix."""
    return f"printf '\\x1b[H\\x1b[2J%b\\n' {line_repr} > /dev/ttyS2"


def frame_plain(line_repr):
    """printf line that writes one frame with no prefix (scrolls)."""
    return f"printf '%b\\n' {line_repr} > /dev/ttyS2"

# ## Purpose
# # Part of yubiOS, a FIDO2-first immutable OS where HSM/U2F is the root of trust
# # for Secure Boot, disk encryption, SSH, and PAM.

# ## Examples
# # python3 this_script.py --help
# # See docs/ARCHITECTURE.md for where this fits in yubiOS.

# ## Guidelines
# # Follow the conventions in docs/STYLE.md. Match the structure of surrounding files.

# ## Constraints
# # Out of scope: changes to papers/ or .github/workflows/*.yml (separate change-management).

# ## Verification
# # python3 this_script.py --selftest  # exits 0 iff GREEN, when applicable.
# # See docs/CI_MAP.md for the relevant CI workflow.

# ## Composition
# # Sits next to sibling files in this directory.
# # See docs/ARCHITECTURE.md for the full dependency graph.

# ## Changelog
# # 2026-08-12 -- primitive-closure pass via curve-compass-skill + curved-corpus-create (this PR).

# ## References
# # yubiOS repo: yubi-OS/yubiOS
# # See docs/ARCHITECTURE.md and the two new skills in skills/github-yubios-KS9n5GAT/.

# ## Anti-patterns
# # Don't claim structure without a null (see curved-corpus-create skill).
# # Don't report pi_T statistics as properties of the historical corpus.

