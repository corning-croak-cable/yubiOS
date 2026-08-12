# Contributing

This is primarily an AI driven project but any human edits are welcome and encouraged. Just submit a PR with your branch and we can go from there.

## How to contribute

- Fork the repository
- Create a branch for your change
- Make your edits
- Open a pull request

## What we welcome

- Bug fixes
- Documentation improvements
- Refactors that make the code easier to understand
- New features that fit the project goals
- Tests and examples

## Suggested workflow

1. Check existing issues and pull requests.
2. Make sure your change is focused and easy to review.
3. Keep commits clear and descriptive.
4. Open a PR with a short explanation of what changed and why.

## Pull request guidelines

- Keep PRs small when possible
- Explain the problem and the solution
- Link related issues if applicable
- Include screenshots or logs when they help
- Mention any breaking changes clearly

## Style

- Match the existing code style
- Prefer simple, readable changes
- Update documentation when behavior changes
- Add tests when practical

## Community expectations

Be respectful, constructive, and collaborative. We want this to stay a friendly project where people can contribute comfortably and learn from each other.

## Questions

If you're not sure where to start, open an issue or submit a draft PR and we can discuss it there.

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

