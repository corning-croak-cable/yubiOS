---
name: Bug report
about: Create a report to help us improve
title: ''
labels: ''
assignees: ''

---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Desktop (please complete the following information):**
 - OS: [e.g. iOS]
 - Browser [e.g. chrome, safari]
 - Version [e.g. 22]

**Smartphone (please complete the following information):**
 - Device: [e.g. iPhone6]
 - OS: [e.g. iOS8.1]
 - Browser [e.g. stock browser, safari]
 - Version [e.g. 22]

**Additional context**
Add any other context about the problem here.

## Examples

- Reading the file or running the script with no arguments shows the help text.
- For a guided tour of where this file fits in yubiOS, see `docs/ARCHITECTURE.md` and the cross-references in this directory.

## Guidelines

- Follow the conventions in `docs/STYLE.md` (or the most relevant style guide referenced from this directory).
- Match the existing structure of surrounding files: `## Examples`, `## Verification`, `## Changelog`, `## Anti-patterns`.

## Constraints

- Out of scope: changes that affect the historical paper corpus in `papers/` (published artifacts, immutable).
- Out of scope: changes to `.github/workflows/*.yml` (CI workflows, separate change-management process).

## Verification

- Spot-check by reading the file end-to-end against this section's claim.
- Run the relevant CI workflow on a draft branch (per `docs/CI_MAP.md`); the result is the gate.

## Composition

- Sits next to sibling files in this directory; consult them for the surrounding context.
- For the full yubiOS dependency graph, see `docs/ARCHITECTURE.md`.

## Changelog

- 2026-08-12 — primitive-closure pass via `curve-compass-skill` + `curved-corpus-create` (this PR).

## References

- yubiOS repo: `yubi-OS/yubiOS`
- Architecture: `docs/ARCHITECTURE.md`
- The two new skills used to drive this primitive-closure pass: `skills/github-yubios-KS9n5GAT/curve-compass-skill/SKILL.md` and `skills/github-yubios-KS9n5GAT/curved-corpus-create/SKILL.md`.

## Anti-patterns

- Don't claim structure without a null: V2 / PC1+PC2 without the curveball null is a number without a claim (per `curved-corpus-create` skill).
- Don't open a code-change PR for already-done work; if it's an audit-trail PR, name it that.
- Don't report `pi_T` statistics as properties of the historical corpus; the compass is on a *designed* dynamics, the historical log is the T->0 limit.

