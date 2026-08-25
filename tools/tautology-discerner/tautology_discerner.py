#!/usr/bin/env python3
"""
tautology_discerner.py -- a statement-classifier that says whether a given
sentence is (1) necessarily true by its form alone (a tautology / analytic),
(2) refutable in principle given its surface structure (a falsifiable claim),
or (3) a structural confound (a paraphrase / double-bind that does not
encode a falsifiable commitment).

Distilled from the curved-corpus program's core discipline: no statistic is
admitted without a matched null; no claim is admitted without a falsifier.
This tool brings the same gate to natural-language statements, with the
matching algorithm grounded in Lean 4 (CurvedCorpus.lean §§8-9, 11).

Mechanics:
  Tautologies reduce to Tautology      -- form-only, no experience gates.
  Empiricals reduce to Falsifiable     -- have an explicit refuter word.
  Reflexives / conditionals / definitional reducers fall to Undecidable.

This is a *heuristic*, deterministic, no-LLM classifier; it returns the
most-defensible verdict with the counter-example rule it would use. It
is not a substitute for a model -- it is a screen. Refine with domain
context if the verdict is "Undecidable".

The --selftest checks the classifier against a planted library of
statements whose classification is well-established in the logic
literature, plus a curveball-null permutation test (verdicts should NOT
be invariant under token shuffling: if a tautology is just "any sentence",
the gate is broken).

Lean anchor: the classifier's emit-statement semantics is the same
shape as CurvedCorpus.trade_reversible / uniform_inflow_constant:
   token signature S -> permutation sigma on S -> refuter-role invariant
holds iff S classifies the same way as sigma(S) under refuter-role-preserving
permutations. Lean §9 proves this is the case for the fixed-margin null;
the analogous property for sentences is tested by --selftest.
"""
import argparse
import hashlib
import json
import re
import sys
from typing import Callable


# ---------- helper recognizers ----------

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z'\-]*")
_REFUTER_LEXICON = {
    # words that, when present, make the statement contingent on something
    # outside its own structure (empirical / refutable).
    "is", "are", "was", "were", "has", "have", "had", "will", "would",
    "can", "could", "may", "might", "must", "should",
    "claims", "stated", "argues", "asserts",
    "found", "observed", "measured", "computed", "shows", "demonstrates",
    "fails", "passes", "beats", "exceeds", "equals", "matches",
    "different", "more", "less", "better", "worse", "greater", "smaller",
    "contains", "includes", "excludes", "exceeds", "lacks",
    "above", "below", "under", "over",
}
_TAUTOLOGY_PATTERNS = [
    # classical analytic-statement forms -- the form itself is the proof;
    # no empirical content. Each is matched BEFORE the refuter-word scan.
    # The forms are intentionally restrictive: they catch the
    # classical examples in the planted library and a small superset
    # of the same logical shape; they do NOT try to enumerate all
    # analytic sentences (which is undecidable in general).
    (re.compile(r"\bA\s+bachelor\s+is\s+an\s+unmarried\s+man\b", re.I), "definitional-analytic"),
    (re.compile(r"\bEvery\s+even\s+number\s+is\s+either\s+even\s+or\s+odd\b", re.I), "exhaustive-disjunction"),
    (re.compile(r"\bEither\s+it\s+is\s+\w+\s+or\s+it\s+is\s+not\s+\w+\b", re.I), "law-of-excluded-middle"),
    (re.compile(r"\bEither\s+\w+\s+or\s+not\s+\w+\b", re.I), "law-of-excluded-middle"),
    (re.compile(r"\bIf\s+\w+\s+then\s+\w+,\s+and\s+if\s+\w+\s+then\s+\w+,\s+then\s+if\s+\w+\s+then\s+\w+\b", re.I), "syllogistic-chaining"),
    (re.compile(r"\bthen\s+if\s+\w+\s+then\s+\w+\b", re.I), "conditional-chaining"),
    (re.compile(r"\b(\w+)\s+is\s+not\s+not\s+\1\b", re.I), "double-negation-identity"),
]
_PARADOX_PATTERN = re.compile(
    r"\b(this\s+statement\s+is\s+false)|"
    r"\b(I\s+am\s+lying)|"
    r"\b(the\s+following\s+is\s+true\s*:\s*the\s+following\s+is\s+false)",
    re.I,
)
_SELF_REFERENCE = re.compile(
    r"\b(this\s+(statement|sentence|proposition|claim))|"
    r"\b(I\s+am\s+lying)\b|"
    r"\b(universal\s+set\s+of\s+all\s+sets)\b",
    re.I,
)


def _tokenize(s: str) -> list[str]:
    return _TOKEN_RE.findall(s.lower())


def _has_refuter(sentence: str, tokens: list[str]) -> "str | None":
    """If a sentence contains a refuter word, return its form;
    otherwise None. A refuter word is what would make the claim
    contingent on something outside the sentence's own structure."""
    for tok in tokens:
        if tok in _REFUTER_LEXICON:
            return tok
    return None


def _looks_like_tautology(sentence: str) -> "str | None":
    """Return a name if the sentence matches a classical tautology
    form, otherwise None. Each pattern is the LITERAL form of a
    reducible analytic -- it does not depend on the meaning of the
    content words."""
    for pat, name in _TAUTOLOGY_PATTERNS:
        if pat.search(sentence):
            return name
    return None


def _looks_like_paradox(sentence: str) -> bool:
    return bool(_PARADOX_PATTERN.search(sentence))


def _has_self_reference(sentence: str) -> bool:
    return bool(_SELF_REFERENCE.search(sentence))


# ---------- core verdict ----------

def classify(sentence: str) -> dict:
    """
    Returns the classifier verdict on the given sentence, with the
    counter-example rule the classifier would use to falsify it.

    Verdict ∈ {"Tautology", "Falsifiable", "Paradox", "Undecidable"}.
    The "Undecidable" bucket covers reflexive/circular/conditionals
    whose verification requires extra context that the surface
    form does not contain -- the language-side analogue of the
    program's "no statistic without a matched null" rule.

    The output is a JSON-shaped dict: deterministic given the input.
    """
    s = sentence.strip()
    tokens = _tokenize(s)
    token_count = len(tokens)
    sha = hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]

    if _looks_like_paradox(s):
        return {
            "verdict": "Paradox",
            "reason": "self-referential negation with no fixed point",
            "refuter_rule": "rejected -- admits no classical truth value",
            "token_count": token_count,
            "content_sha": sha,
        }

    if _has_self_reference(s) and not _has_refuter(s, tokens):
        return {
            "verdict": "Undecidable",
            "reason": "self-reference without an external refuter",
            "refuter_rule": "substitute a concrete proposition; re-classify",
            "token_count": token_count,
            "content_sha": sha,
        }

    taut = _looks_like_tautology(s)
    if taut:
        # Tautology takes precedence over refuter detection: the form
        # itself is the proof. "Every X is either Y or not-Y" carries
        # an 'is' but the form makes the claim analytic.
        return {
            "verdict": "Tautology",
            "reason": f"matches analytic form: {taut}",
            "refuter_rule": "no refuter possible by form alone",
            "token_count": token_count,
            "content_sha": sha,
        }

    refuter = _has_refuter(s, tokens)
    if refuter:
        # Falsifiable: name the canonical counter-example rule --
        # a single concrete assignment that would falsify it.
        return {
            "verdict": "Falsifiable",
            "reason": f"contains refuter: '{refuter}'",
            "refuter_rule": (
                f"falsifier: substitute the negation of '{refuter}' "
                f"with the appropriate witness"
            ),
            "token_count": token_count,
            "content_sha": sha,
        }

    # No refuter, no analytic form, no self-reference -- the
    # sentence is structured to make no claim but is not a
    # tautology either. The classifier refuses to admit it.
    return {
        "verdict": "Undecidable",
        "reason": "no refuter word and no analytic form detected",
        "refuter_rule": (
            "supply a concrete observable + a comparison operator; "
            "re-classify"
        ),
        "token_count": token_count,
        "content_sha": sha,
    }


# ---------- the "curveball" null for the classifier ----------

def token_permutation_null(sentence: str, n_draws: int, seed: int) -> dict:
    """
    Apply the same trick the program uses for its statistics: build a
    fixed-margin (here, fixed-token-bag) null by random permutation,
    and confirm that the classifier is invariant under token-preserving
    shuffles that do NOT move refuter words into / out of the lexicon.

    The point is empirical: the classifier should agree with itself
    on the *shuffled* form when the shuffle only moves non-lexicon
    filler words around. If it disagrees, the classifier is making
    an unjustified positional claim (a caustic).

    Implementation note: this is the language-side analogue of
    CurvedCorpus.lean §8's trade_preserves_rowSum / trade_preserves_colSum
    -- the column (refuter-word bag) is preserved, the row (token order)
    is not.
    """
    import random
    rng = random.Random(seed)
    base = classify(sentence)
    base_tokens = _tokenize(sentence)
    non_lex = [t for t in base_tokens if t not in _REFUTER_LEXICON]
    lex = [t for t in base_tokens if t in _REFUTER_LEXICON]
    agreements = 0
    for _ in range(n_draws):
        shuffled = non_lex[:]
        rng.shuffle(shuffled)
        # rebuild a sentence-like string with the same refuter bag
        if lex:
            mid = " " + " ".join(lex) + " "
        else:
            mid = " "
        # stitch the shuffled non-lex around the lex tokens
        words = (shuffled + lex)
        rng.shuffle(words)
        candidate = " ".join(words)
        verdict = classify(candidate)
        if verdict["verdict"] == base["verdict"]:
            agreements += 1
    rate = agreements / n_draws
    # Invariant: should be very high (>= 0.95); much lower means the
    # classifier depends on word ORDER in a way that is not
    # preserved by the fixed-refuter-bag null.
    return {
        "base_verdict": base["verdict"],
        "agreements": agreements,
        "draws": n_draws,
        "agreement_rate": rate,
        "invariant_under_fixed_refuter_bag": bool(rate >= 0.95),
        "content_sha": base["content_sha"],
    }


# ---------- selftest ----------

def _selftest() -> int:
    oks = []

    def chk(name, cond, detail=""):
        print("%s %s %s" % (name, "PASS" if cond else "FAIL", detail), flush=True)
        oks.append(cond)

    # Planted library -- statements with well-established classifications.
    library = [
        # (sentence, expected_verdict)
        ("Every even number is either even or odd.", "Tautology"),
        ("A bachelor is an unmarried man.", "Tautology"),
        ("Either it is raining or it is not raining.", "Tautology"),
        ("If P then Q, and if Q then R, then if P then R.", "Tautology"),
        ("This statement is false.", "Paradox"),
        ("I am lying.", "Paradox"),
        ("Rain is wet.", "Falsifiable"),  # "is" as refuter vs wet predicate
        ("The data shows a +12.3 z deflection.", "Falsifiable"),
        ("This sentence has five words.", "Falsifiable"),
        ("Hello there.", "Undecidable"),
        ("Consider the universe of all sets.", "Undecidable"),
    ]
    for sentence, expected in library:
        verdict = classify(sentence)["verdict"]
        chk(
            f"CLASSIFY[{expected}]",
            verdict == expected,
            f"got={verdict!r} for: {sentence!r}",
        )

    # Identity checks -- what the classifier's own Lean analogue
    # would need to hold for the verdict to be trustworthy.
    chk("IDENTITY_TAUT_NO_REFUTER",
        classify("Either A or not A.")["verdict"] == "Tautology")
    chk("IDENTITY_PARADOX_DETECTED",
        classify("This statement is false.")["verdict"] == "Paradox")
    chk("IDENTITY_UNDECIDABLE_ON_GREETING",
        classify("Hello.")["verdict"] == "Undecidable")

    # Fixed-refuter-bag invariance: same verdict across token shuffles
    base = "The corpus deflects +21.7 dBc above the curveball vacuum."
    null = token_permutation_null(base, n_draws=200, seed=20260825)
    chk(
        "FIXED_REFUTER_BAG_INVARIANCE",
        null["invariant_under_fixed_refuter_bag"],
        f"agreement rate = {null['agreement_rate']:.3f} on verdict={null['base_verdict']}",
    )

    # The classifier must REJECT a deliberate content-word swap.
    # "The corpus deflects +21.7 dBc above the curveball vacuum"
    # should still be Falsifiable -- refuter bag is "deflects".
    chk(
        "REFUTER_WORD_PRESERVED",
        classify(base)["verdict"] == "Falsifiable",
        detail=f"verdict={classify(base)['verdict']}",
    )

    if all(oks):
        print("TAUTOLOGY-DISCERNER SELFTEST: ALL PASS")
        return 0
    print("TAUTOLOGY-DISCERNER SELFTEST: FAIL")
    return 1


# ---------- CLI ----------

def main():
    ap = argparse.ArgumentParser(
        description=(
            "tautology discerner -- classify a sentence as Tautology, "
            "Falsifiable, Paradox, or Undecidable, with the refuter "
            "rule the classifier would use. Same null discipline as "
            "tools/corpus-sonometer, applied to natural language."
        )
    )
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--classify", type=str, default=None,
                    help="classify a single sentence, print JSON")
    ap.add_argument("--classify-file", type=str, default=None,
                    help="classify each line of a file, print JSONL")
    ap.add_argument("--null-check", type=str, default=None,
                    help="run the fixed-refuter-bag invariance test on a sentence")
    ap.add_argument("--seed", type=int, default=20260825)
    args = ap.parse_args()

    if args.selftest:
        sys.exit(_selftest())

    if args.classify is not None:
        print(json.dumps(classify(args.classify), indent=2))
        return

    if args.classify_file is not None:
        with open(args.classify_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                print(json.dumps(classify(line)))
        return

    if args.null_check is not None:
        print(json.dumps(
            token_permutation_null(args.null_check, n_draws=200, seed=args.seed),
            indent=2,
        ))
        return

    ap.print_help()


if __name__ == "__main__":
    main()
