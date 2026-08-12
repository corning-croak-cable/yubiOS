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


## New Ideas -- cycle 2 (lens format)

This file was processed by the RSI cycle-2 lens generator (curve-compass-skill v1.1.0 + curved-corpus-create v1.1.0). Each cycle-2 patch IS a concrete experiment with a measurable delta -- not a templated section. The lens below documents the measured dynamics; the patch is the lens, not prose about the file.

```json
{
  "lens": "L150",
  "file": ".github/CONTRIBUTING.md",
  "hypothesis": ".github/CONTRIBUTING.md covers all 9 primitives in the internal-big-picture basis",
  "method": "9-D primitive binarization (purpose, examples, guidelines, constraints, verification, composition, changelog, references, anti-patterns) + chordal distance to ideal pole on Fibonacci lattice",
  "parameters": {
    "basis": "internal-big-picture",
    "d": 9,
    "seed": 20260812
  },
  "delta": {
    "k": 2,
    "missing_primitives": [
      "guidelines",
      "constraints",
      "verification",
      "composition",
      "changelog",
      "references",
      "anti-patterns"
    ],
    "chordal_resid": 0.0
  },
  "verdict": "NO",
  "score": 11,
  "caveat": "binarization is heuristic; a stricter regex pass might surface sub-primitives"
}
```
