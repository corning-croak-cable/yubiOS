"""
Cross-seed robustness sweep — runs the falsification harness at multiple
seeds and reports aggregated pass rates per test. Used to verify the
single-seed result isn't a lucky accident.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from falsification_harness import run_harness  # noqa: E402


def sweep(seeds=(7, 13, 42, 99, 256, 512, 1024, 2027, 31337, 65537)):
    results = []
    for s in seeds:
        r = run_harness(seed=s, verbose=False)
        results.append({
            "seed": s,
            "n_observations": r["corpus_stats"]["n_observations"],
            "pc1_pc2": r["tests"]["test_1_basic_fit"]["pc1_pc2"],
            "t1_passed": r["tests"]["test_1_basic_fit"]["passed"],
            "t2_recovery_rate": r["tests"]["test_2_sparse_cell_recovery"]["recovery_rate"],
            "t2_passed": r["tests"]["test_2_sparse_cell_recovery"]["passed"],
            "t3_violations": r["tests"]["test_3_lemma_1_invariant"]["n_delta_negative_violations"],
            "t3_passed": r["tests"]["test_3_lemma_1_invariant"]["passed"],
            "overall_passed": r["overall_passed"],
        })

    n = len(results)
    summary = {
        "n_seeds": n,
        "seeds": list(seeds),
        "t1_pass_rate": sum(1 for r in results if r["t1_passed"]) / n,
        "t2_pass_rate": sum(1 for r in results if r["t2_passed"]) / n,
        "t3_pass_rate": sum(1 for r in results if r["t3_passed"]) / n,
        "overall_pass_rate": sum(1 for r in results if r["overall_passed"]) / n,
        "mean_pc1_pc2": sum(r["pc1_pc2"] for r in results) / n,
        "mean_recovery_rate": sum(r["t2_recovery_rate"] for r in results) / n,
        "mean_n_observations": sum(r["n_observations"] for r in results) / n,
        "per_seed": results,
    }
    out = HERE / "multi_seed_results.json"
    with open(out, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"[sweep] ran {n} seeds; pass rates: "
          f"T1={summary['t1_pass_rate']:.0%} T2={summary['t2_pass_rate']:.0%} "
          f"T3={summary['t3_pass_rate']:.0%} "
          f"overall={summary['overall_pass_rate']:.0%}")
    print(f"[sweep] mean PC1+PC2 = {summary['mean_pc1_pc2']:.4f}; "
          f"mean recovery rate = {summary['mean_recovery_rate']:.0%}; "
          f"mean N = {summary['mean_n_observations']:.0f}")
    print(f"[sweep] wrote {out}")
    return summary


if __name__ == "__main__":
    sweep()
