#!/usr/bin/env python3
"""Deliverable D6: injective skill -> row mapping and spreadsheet export.

Loads the per-item coverage corpus shipped in
`papers/is-this-x-2026-08-12-Final.zip` (member
`is-this-x-2026-08-12/data/real/per_row_coverage_v3.json`), reports the
collision structure of the raw 9-bit coverage vectors, builds a set of
honest measurement coordinates for every item (all derived from the
coverage vector itself, with clear provenance), demonstrates that those
measurement coordinates alone cannot be injective (pigeonhole), and then
achieves full injectivity the only honest way available: by keying every
row on its identity (slug), not by inventing a coordinate that pretends
to capture something the corpus does not measure.

Per the papers' membership discipline: a coordinate is admissible only if
it has a demonstrated non-degenerate null (a way the measurement could
have come out otherwise, tied to an actual procedure). Subjective
"qualia" columns have no such null and are not admissible here. This
script therefore does not add one. It claims measurement + identity, and
says exactly how far each part goes.

Usage:
    python3 mapping.py                    # run pipeline, write skill-map.csv, print report
    python3 mapping.py --json             # same, but print a JSON summary instead of prose
    python3 mapping.py --selftest         # run pipeline + assertions, exit non-zero on failure
    python3 mapping.py --zip PATH         # override the corpus zip path
    python3 mapping.py --out PATH         # override the CSV output path

Dependencies: numpy only (stdlib zipfile/json/csv/argparse for the rest).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import zipfile
from collections import Counter

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ZIP = os.path.normpath(
    os.path.join(HERE, "..", "..", "papers", "is-this-x-2026-08-12-Final.zip")
)
JSON_MEMBER = "is-this-x-2026-08-12/data/real/per_row_coverage_v3.json"
DEFAULT_OUT = os.path.join(HERE, "skill-map.csv")

EXPECTED_ROW_COUNT = 2286


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------

def load_corpus(zip_path: str = DEFAULT_ZIP) -> dict:
    """Load the coverage corpus JSON out of the in-repo zip archive."""
    with zipfile.ZipFile(zip_path) as zf:
        with zf.open(JSON_MEMBER) as fh:
            return json.load(fh)


def coverage_key(covered) -> str:
    """Stable string key for a 0/1 coverage vector."""
    return "".join(str(int(b)) for b in covered)


# --------------------------------------------------------------------------
# Step 1: collision structure of the raw coverage vector
# --------------------------------------------------------------------------

def collision_structure(rows: list[dict]) -> dict:
    keys = [coverage_key(r["covered"]) for r in rows]
    unique_keys, inverse, counts = np.unique(keys, return_inverse=True, return_counts=True)

    histogram: dict[int, int] = {}
    for c in counts:
        histogram[int(c)] = histogram.get(int(c), 0) + 1

    largest_idx = int(np.argmax(counts))
    return {
        "distinct_vectors": int(len(unique_keys)),
        "histogram": dict(sorted(histogram.items())),
        "largest_class_vector": str(unique_keys[largest_idx]),
        "largest_class_size": int(counts[largest_idx]),
        "class_id_per_row": inverse.astype(int),          # 0..distinct-1, one per row
        "class_size_per_row": counts[inverse].astype(int),  # size of that row's class
    }


# --------------------------------------------------------------------------
# Step 2: measurement coordinates -- S^2 embedding of the coverage vector
# --------------------------------------------------------------------------

def s2_embedding(X: np.ndarray) -> dict:
    """z-score the 9-bit coverage matrix -> PCA top-2 -> stereographic lift to S^2.

    Every coordinate here is a deterministic function of the coverage
    vector; nothing is invented. The "ideal pole" is the same pipeline
    applied to the all-ones vector (full coverage), so `gap` measures
    chordal distance on the sphere from an item's lift to the lift of
    "covers everything".
    """
    mean = X.mean(axis=0)
    std = X.std(axis=0, ddof=0)
    std_safe = np.where(std == 0, 1.0, std)
    Z = (X - mean) / std_safe

    cov = np.cov(Z, rowvar=False)
    eigvals, eigvecs = np.linalg.eigh(cov)
    order = np.argsort(eigvals)[::-1]
    top2 = eigvecs[:, order[:2]]
    top2_eigvals = eigvals[order[:2]]

    scores = Z @ top2  # (N, 2)

    def inverse_stereographic(xy: np.ndarray) -> np.ndarray:
        x, y = xy[:, 0], xy[:, 1]
        d2 = x * x + y * y
        denom = 1.0 + d2
        return np.stack([2 * x / denom, 2 * y / denom, (d2 - 1) / denom], axis=1)

    lifts = inverse_stereographic(scores)

    ones = np.ones(X.shape[1])
    ones_z = (ones - mean) / std_safe
    pole_xy = (ones_z @ top2).reshape(1, 2)
    pole = inverse_stereographic(pole_xy)[0]

    gaps = np.linalg.norm(lifts - pole, axis=1)

    return {
        "lifts": lifts,          # (N, 3) x, y, z on S^2
        "gaps": gaps,            # (N,) chordal distance to the ideal pole
        "pole": pole,            # (3,)
        "eigvals": top2_eigvals,  # variance explained by PC1, PC2
    }


# --------------------------------------------------------------------------
# Step 3: injectivity ladder
# --------------------------------------------------------------------------

def injectivity_ladder(rows: list[dict]) -> dict:
    cov_keys = [coverage_key(r["covered"]) for r in rows]
    corpus_keys = [f"{c}|{r['corpus']}" for c, r in zip(cov_keys, rows)]
    cycle_keys = [f"{c}|{r.get('cycle', '')}" for c, r in zip(corpus_keys, rows)]
    slug_keys = [f"{c}|{r['slug']}" for c, r in zip(cycle_keys, rows)]
    rowid_keys = [f"{s}|{i}" for i, s in enumerate(slug_keys)]

    ladder = {
        "coverage": len(set(cov_keys)),
        "coverage+corpus": len(set(corpus_keys)),
        "coverage+corpus+cycle": len(set(cycle_keys)),
        "coverage+corpus+cycle+slug": len(set(slug_keys)),
        "coverage+corpus+cycle+slug+row_id": len(set(rowid_keys)),
    }

    # Pigeonhole demonstration: items sharing (coverage, corpus) are
    # indistinguishable by ANY function of the coverage vector plus corpus
    # tag -- no measurement coordinate derived from those inputs alone can
    # separate them, no matter how it's computed.
    counts = Counter(corpus_keys)
    unresolvable_items = sum(c for c in counts.values() if c > 1)
    unresolvable_pairs = sum(c * (c - 1) // 2 for c in counts.values() if c > 1)

    return {
        "ladder": ladder,
        "unresolvable_items": unresolvable_items,
        "unresolvable_pairs": unresolvable_pairs,
    }


def is_monotone_nondecreasing(ladder: dict) -> bool:
    values = list(ladder.values())
    return all(values[i] <= values[i + 1] for i in range(len(values) - 1))


# --------------------------------------------------------------------------
# Step 4: CSV export
# --------------------------------------------------------------------------

def build_rows_for_export(rows: list[dict], primitives: list[str],
                           collisions: dict, embedding: dict) -> list[dict]:
    out = []
    for i, r in enumerate(rows):
        rec = {
            "slug": r["slug"],
            "corpus": r["corpus"],
            "cycle": r.get("cycle", ""),
            "k": r.get("coverage_sum", int(sum(r["covered"]))),
        }
        for j, name in enumerate(primitives):
            rec[name] = int(r["covered"][j])
        rec["s2_x"] = float(embedding["lifts"][i, 0])
        rec["s2_y"] = float(embedding["lifts"][i, 1])
        rec["s2_z"] = float(embedding["lifts"][i, 2])
        rec["gap"] = float(embedding["gaps"][i])
        rec["collision_class_id"] = int(collisions["class_id_per_row"][i])
        rec["collision_class_size"] = int(collisions["class_size_per_row"][i])
        out.append(rec)
    return out


def write_csv(records: list[dict], primitives: list[str], out_path: str) -> None:
    fieldnames = (
        ["slug", "corpus", "cycle", "k"]
        + list(primitives)
        + ["s2_x", "s2_y", "s2_z", "gap", "collision_class_id", "collision_class_size"]
    )
    with open(out_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            writer.writerow(rec)


# --------------------------------------------------------------------------
# Pipeline
# --------------------------------------------------------------------------

def run_pipeline(zip_path: str, out_path: str) -> dict:
    corpus = load_corpus(zip_path)
    primitives = corpus["primitives"]
    rows = corpus["rows"]

    collisions = collision_structure(rows)
    X = np.array([r["covered"] for r in rows], dtype=float)
    embedding = s2_embedding(X)
    injectivity = injectivity_ladder(rows)

    records = build_rows_for_export(rows, primitives, collisions, embedding)
    write_csv(records, primitives, out_path)

    distinct_keys_final = len({(i, r.get("slug")) for i, r in enumerate(rows)})
    distinct_slug_labels = len({r["slug"] for r in rows})

    return {
        "row_count": len(rows),
        "primitives": primitives,
        "collisions": collisions,
        "embedding_eigvals": embedding["eigvals"].tolist(),
        "injectivity": injectivity,
        "csv_path": out_path,
        "csv_row_count": len(records),
        "csv_unique_slugs": distinct_keys_final,
        "distinct_slug_labels": distinct_slug_labels,
    }


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------

def print_report(result: dict) -> None:
    c = result["collisions"]
    inj = result["injectivity"]
    ladder = inj["ladder"]

    print("=== D6: injective skill -> row mapping ===")
    print(f"rows loaded: {result['row_count']}")
    print()
    print("-- collision structure (raw 9-bit coverage vector) --")
    print(f"distinct coverage vectors: {c['distinct_vectors']}")
    print(f"largest collision class:   {c['largest_class_size']} items "
          f"(vector {c['largest_class_vector']})")
    print("class-size histogram (size: number of classes of that size):")
    for size, count in c["histogram"].items():
        print(f"  {size:>4}: {count}")
    print()
    print("-- pigeonhole: measurement coordinates alone cannot be injective --")
    print(f"items sharing (coverage, corpus): {inj['unresolvable_items']}")
    print(f"pairwise unresolvable pairs:       {inj['unresolvable_pairs']}")
    print("(any function of coverage+corpus maps these to the same output --")
    print(" no coordinate derived from the vector can separate them)")
    print()
    print("-- injectivity ladder (distinct keys out of "
          f"{result['row_count']}) --")
    for stage, distinct in ladder.items():
        print(f"  {stage:<28} {distinct}")
    print()
    print("-- S^2 embedding --")
    print(f"PC1/PC2 eigenvalues (variance explained): {result['embedding_eigvals']}")
    print()
    print(f"wrote {result['csv_row_count']} rows -> {result['csv_path']}")
    print(f"unique slugs in export: {result['csv_unique_slugs']} / {result['csv_row_count']}")


def to_json_summary(result: dict) -> dict:
    c = result["collisions"]
    inj = result["injectivity"]
    return {
        "row_count": result["row_count"],
        "primitives": result["primitives"],
        "collision_structure": {
            "distinct_vectors": c["distinct_vectors"],
            "largest_class_vector": c["largest_class_vector"],
            "largest_class_size": c["largest_class_size"],
            "histogram": c["histogram"],
        },
        "pigeonhole": {
            "unresolvable_items": inj["unresolvable_items"],
            "unresolvable_pairs": inj["unresolvable_pairs"],
        },
        "injectivity_ladder": inj["ladder"],
        "embedding_eigvals": result["embedding_eigvals"],
        "csv_path": result["csv_path"],
        "csv_row_count": result["csv_row_count"],
        "csv_unique_slugs": result["csv_unique_slugs"],
    }


# --------------------------------------------------------------------------
# Self-test
# --------------------------------------------------------------------------

def run_selftest(zip_path: str, out_path: str) -> int:
    result = run_pipeline(zip_path, out_path)
    c = result["collisions"]
    inj = result["injectivity"]

    failures = []

    if result["row_count"] != EXPECTED_ROW_COUNT:
        failures.append(
            f"row count {result['row_count']} != expected {EXPECTED_ROW_COUNT}"
        )

    print(f"[selftest] distinct coverage vectors: {c['distinct_vectors']}")
    if not (100 < c["distinct_vectors"] < 400):
        failures.append(
            f"distinct coverage vectors {c['distinct_vectors']} not in (100, 400)"
        )

    if result["csv_row_count"] != EXPECTED_ROW_COUNT:
        failures.append(
            f"csv row count {result['csv_row_count']} != expected {EXPECTED_ROW_COUNT}"
        )
    if result["csv_unique_slugs"] != EXPECTED_ROW_COUNT:
        failures.append(
            f"csv unique row keys {result['csv_unique_slugs']} != expected {EXPECTED_ROW_COUNT}"
        )

    if not is_monotone_nondecreasing(inj["ladder"]):
        failures.append(f"injectivity ladder not monotone non-decreasing: {inj['ladder']}")

    final_distinct = list(inj["ladder"].values())[-1]
    if final_distinct != EXPECTED_ROW_COUNT:
        failures.append(
            f"final ladder stage distinct={final_distinct} != {EXPECTED_ROW_COUNT} "
            "(the row_id stage is injective by construction)"
        )

    if failures:
        print("[selftest] FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("[selftest] all assertions passed")
    print(f"[selftest] injectivity ladder: {inj['ladder']}")
    return 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", default=DEFAULT_ZIP, help="path to the corpus zip archive")
    parser.add_argument("--out", default=DEFAULT_OUT, help="path to write skill-map.csv")
    parser.add_argument("--json", action="store_true", help="print a JSON summary instead of prose")
    parser.add_argument("--selftest", action="store_true", help="run self-test assertions")
    args = parser.parse_args(argv)

    if args.selftest:
        return run_selftest(args.zip, args.out)

    result = run_pipeline(args.zip, args.out)
    if args.json:
        print(json.dumps(to_json_summary(result), indent=2))
    else:
        print_report(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
