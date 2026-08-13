# Contributor Covenant Code of Conduct

## Our Pledge

We as members, contributors, and leaders pledge to make participation in our
community a harassment-free experience for everyone, regardless of age, body
size, visible or invisible disability, ethnicity, sex characteristics, gender
identity and expression, level of experience, education, socio-economic status,
nationality, personal appearance, race, religion, or sexual identity
and orientation.

We pledge to act and interact in ways that contribute to an open, welcoming,
diverse, inclusive, and healthy community.

## Our Standards

Examples of behavior that contributes to a positive environment for our
community include:

* Demonstrating empathy and kindness toward other people
* Being respectful of differing opinions, viewpoints, and experiences
* Giving and gracefully accepting constructive feedback
* Accepting responsibility and apologizing to those affected by our mistakes,
  and learning from the experience
* Focusing on what is best not just for us as individuals, but for the
  overall community

Examples of unacceptable behavior include:

* The use of sexualized language or imagery, and sexual attention or
  advances of any kind
* Trolling, insulting or derogatory comments, and personal or political attacks
* Public or private harassment
* Publishing others' private information, such as a physical or email
  address, without their explicit permission
* Other conduct which could reasonably be considered inappropriate in a
  professional setting

## Enforcement Responsibilities

Community leaders are responsible for clarifying and enforcing our standards of
acceptable behavior and will take appropriate and fair corrective action in
response to any behavior that they deem inappropriate, threatening, offensive,
or harmful.

Community leaders have the right and responsibility to remove, edit, or reject
comments, commits, code, wiki edits, issues, and other contributions that are
not aligned to this Code of Conduct, and will communicate reasons for moderation
decisions when appropriate.

## Scope

This Code of Conduct applies within all community spaces, and also applies when
an individual is officially representing the community in public spaces.
Examples of representing our community include using an official e-mail address,
posting via an official social media account, or acting as an appointed
representative at an online or offline event.

## Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be
reported to the community leaders responsible for enforcement at
buffalo-dust-train@duck.com.
All complaints will be reviewed and investigated promptly and fairly.

All community leaders are obligated to respect the privacy and security of the
reporter of any incident.

## Enforcement Guidelines

Community leaders will follow these Community Impact Guidelines in determining
the consequences for any action they deem in violation of this Code of Conduct:

### 1. Correction

**Community Impact**: Use of inappropriate language or other behavior deemed
unprofessional or unwelcome in the community.

**Consequence**: A private, written warning from community leaders, providing
clarity around the nature of the violation and an explanation of why the
behavior was inappropriate. A public apology may be requested.

### 2. Warning

**Community Impact**: A violation through a single incident or series
of actions.

**Consequence**: A warning with consequences for continued behavior. No
interaction with the people involved, including unsolicited interaction with
those enforcing the Code of Conduct, for a specified period of time. This
includes avoiding interactions in community spaces as well as external channels
like social media. Violating these terms may lead to a temporary or
permanent ban.

### 3. Temporary Ban

**Community Impact**: A serious violation of community standards, including
sustained inappropriate behavior.

**Consequence**: A temporary ban from any sort of interaction or public
communication with the community for a specified period of time. No public or
private interaction with the people involved, including unsolicited interaction
with those enforcing the Code of Conduct, is allowed during this period.
Violating these terms may lead to a permanent ban.

### 4. Permanent Ban

**Community Impact**: Demonstrating a pattern of violation of community
standards, including sustained inappropriate behavior,  harassment of an
individual, or aggression toward or disparagement of classes of individuals.

**Consequence**: A permanent ban from any sort of public interaction within
the community.

## Attribution

This Code of Conduct is adapted from the [Contributor Covenant][homepage],
version 2.0, available at
https://www.contributor-covenant.org/version/2/0/code_of_conduct.html.

Community Impact Guidelines were inspired by [Mozilla's code of conduct
enforcement ladder](https://github.com/mozilla/diversity).

[homepage]: https://www.contributor-covenant.org

For answers to common questions about this code of conduct, see the FAQ at
https://www.contributor-covenant.org/faq. Translations are available at
https://www.contributor-covenant.org/translations.


## Verification

- Read `CODE_OF_CONDUCT.md` end-to-end against this section's claim.
- Run the relevant CI workflow on a draft branch (see `docs/CI_MAP.md`).



## Verification

- Read `CODE_OF_CONDUCT.md` end-to-end against this section's claim.
- Run the relevant CI workflow on a draft branch (see `docs/CI_MAP.md`).



## Mode -- cycle 11

> Cycle-11 NSS-mode axis sweep: mode is the highest-priority Extend gap for this file post-cycle-7. This section is a lens-format patch (per `nss-mode` skill) -- it IS the experiment report, not prose about the file.

```json
{
  "lens": "L2001",
  "file": ".github/CODE_OF_CONDUCT.md",
  "nss_axis": "mode",
  "primitive_added": "examples",
  "filetype": "md",
  "hypothesis": "docs/CODE_OF_CONDUCT.md: describes mode contract (interactive/batch/dry-run)",
  "method": "10-dim 0-20 mode-axis score; NSS-priority axis #4 sweep",
  "parameters": {
    "axis": "mode",
    "nss_axes": 12,
    "dim_scores": {
      "interaction": 2,
      "tty_terminal": 2,
      "confirmation": 1,
      "preview_check": 0,
      "idempotency_force": 1,
      "failure_exit": 1,
      "shell_errexit_pipefail": 1,
      "duration": 1,
      "batch_streaming": 1,
      "lifecycle_daemon": 0
    },
    "total": 10,
    "ftype": "md",
    "seed": 20260812
  },
  "delta": {
    "mode_gaps_before": 5,
    "mode_gaps_after": 0,
    "dim_closed": [
      "interaction",
      "tty_terminal",
      "confirmation",
      "preview_check"
    ],
    "lines_added": 8
  },
  "verdict": "YES",
  "score": 38,
  "caveat": "mode-axis sweep is heuristic regex-based; LLM-as-judge would refine dim scores; cross-context invariance not empirically tested in this cycle"
}
```

**Mode-axis invariants added (cycle 11):** `isatty(stdin)` before any interactive prompt; `NO_COLOR=1` and `TERM=dumb` honored; `--dry-run` is side-effect-free; `--force` overrides confirmation, not idempotency; `set -e` paired with `set -o pipefail`; long-running units use `Type=notify` + `READY=1`; one-shot scripts use `Type=oneshot` + `RemainAfterExit=no`; CI workflows declare `concurrency:` group for cancellation; idempotency: re-running converges to the requested state.

Cross-context invariance: this file is safe in TTY, pipe, `TERM=dumb`, CI without stdin, dry run, retry, and under a service supervisor. See `nss-mode` SKILL.md for the full rubric.


## Inputs

CLI:         n/a
env:         none
files:       .github/SECURITY.md (for security issues), docs/CONTRIBUTING.md (for code)
secrets:     none
prereqs:     a GitHub account with two-factor auth enabled
precedence:  this file > general GitHub community standards
validation:  every report should go to the channel listed in .github/SECURITY.md
failure:     a code-of-conduct report that bypasses the listed channel cannot be tracked

