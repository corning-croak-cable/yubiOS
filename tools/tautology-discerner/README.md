# tautology-discerner

A natural-language statement classifier. Given a sentence, it returns one of
four verdicts and the refuter rule the classifier would use to falsify it.

| verdict     | meaning                                                                                                |
|-------------|--------------------------------------------------------------------------------------------------------|
| Tautology   | necessarily true by form alone (copula-with-no-comparison, exhaustive disjunction, universal restatement). No external evidence can refute it. |
| Falsifiable | contains a refuter word (`is`, `shows`, `exceeds`, `found`, ...); the refuter rule names a concrete witness that would falsify the claim. |
| Paradox     | self-referential negation with no classical truth value (`This statement is false.`). |
| Undecidable | no refuter word, no analytic form, no self-reference. Refuses to admit the statement until a concrete observable + comparison is supplied. |

The "Undecidable" bucket is the natural-language analogue of the program's
core discipline: **no statistic admitted without a matched null**, **no claim
admitted without a falsifier**. Sentences that don't carry an explicit
commitment are returned as Undecidable rather than guessed at.

## Quick start

```bash
./tautology_discerner.py --selftest
./tautology_discerner.py --classify "Either it rains or it does not rain."
./tautology_discerner.py --classify "The data shows a +12.3 z deflection."
./tautology_discerner.py --classify "This statement is false."
./tautology_discerner.py --classify "Hello."
./tautology_discerner.py --null-check "The corpus deflects +21.7 dBc above the curveball vacuum."
./tautology_discerner.py --classify-file statements.txt
```

## What it is not

This is a *heuristic* classifier. It does not understand semantics; it
detects surface-form commitments. The library in `--selftest` is the
calibration set; statements that fall outside that library should be
audited manually when the verdict is Undecidable.

The "fixed-refuter-bag invariance" check in `--null-check` is the
language-side analogue of `CurvedCorpus.lean` §§8-9: if shuffling
non-lexicon words around the refuter bag changes the verdict, the
classifier is making an unjustified positional claim.

## Lean anchor

`CurvedCorpus.lean` §8 (`trade_preserves_rowSum / trade_preserves_colSum`)
proves that the curveball trade preserves row and column sums on the
fixed-margin fibre -- the refuter-bag invariance property here is the
language analogue of that proof. §9 (`trade_reversible /
uniform_inflow_constant`) proves that reversible trades admit a
canonical uniform null on the fibre; the "any sentence" rejection
threshold is the natural-language analogue of "the canonical null is
the one and only null".

## Connection to the curved-corpus program

The classifier's verdict surface is exactly the program's admission
surface restated for statements. A sentence is admitted iff it carries
a refuter (a measurable commitment); a statistic is admitted iff it
carries a matched null (a measurable comparison). The "Undecidable"
bucket is the program refusing to admit undefended claims.

## Implementation

Pure Python 3, stdlib only. Deterministic given the input. The
library classifier is a token-pattern recognizer; no LLM, no external
dependency.
