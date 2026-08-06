#!/usr/bin/env python3
"""
Single-action RSI cycle on recursive-self-improvement/SKILL.md.
Per single-action-curve-rsi SKILL.md spec.
"""
import json
import re
import sys
from pathlib import Path
import numpy as np

SKILL_PATH = Path("/var/workspace/skills/github-yubios-KS9n5GAT/recursive-self-improvement/SKILL.md")
OUT_DIR = Path("/var/workspace/documents/github-yubios-KS9n5GAT/subagents/rsi-patch-recursive-self-improvement")

# 9-D primitive basis (single-action-curve-rsi SKILL.md §9-D Primitive Basis)
PATTERNS = {
    "p0_has_purpose":        [r"\bTL;DR\b", r"\bSummary\b", r"\bProblem Statement\b", r"\bGoal\b", r"\bIntent\b"],
    "p1_has_evidence":       [r"\b\d{3,}\b", r"\bverified\b", r"\bPASS\b", r"\bmeasured\b", r"\bProbability:\s*high\b"],
    "p2_has_correction":     [r"\bV\d+\s+failure\b", r"\bwas wrong\b", r"\bsymptom\b", r"\bnot the cause\b", r"\bthe actual root cause\b"],
    "p3_has_constraint":     [r"\bMust\b", r"\bNever\b", r"\bCannot\b", r"\bADR-\d+\b", r"\bDon't\b", r"\bban\b"],
    "p4_has_pushback":       [r"\bPENDING\b", r"\bno release tag\b", r"\blimitations\b", r"\bnot yet\b", r"~3 weeks"],
    "p5_has_test":           [r"V\d+-fix-[A-Z]", r"\bTest:\b", r"\bVerified\b", r"\bverify\b", r"\bPASS\b", r"\bVerification:\b"],
    "p6_has_source":         [r"github\.com/", r"https?://", r"\bPR\s*#\d+", r"\bissue\s*#\d+", r"commit\s+`[0-9a-f]+`"],
    "p7_has_recommendation": [r"\bfix-[A-Z]\b", r"\bsurgical fix\b", r"\bborrowable\b", r"\bV52 fix\b", r"\bordered next steps\b"],
    "p8_has_priority":       [r"\bP0\b", r"\bP1\b", r"\bP2\b", r"\bhigh\b", r"\bmedium\b", r"\blow\b",
                              r"\bProbability:\s*(high|medium|low)\b", r"\bcritical\b"],
}
PRIMITIVES = list(PATTERNS.keys())

def section_coverage(text):
    """Return 9-bit binary coverage vector for a section."""
    cov = np.zeros(9, dtype=int)
    for j, pname in enumerate(PRIMITIVES):
        for pat in PATTERNS[pname]:
            if re.search(pat, text, re.IGNORECASE):
                cov[j] = 1
                break
    return cov

def parse_sections(text):
    """Split SKILL.md into sections by '## ' headers. Return list of (header, body_text, byte_len)."""
    lines = text.split("\n")
    sections = []
    cur_header = None
    cur_body = []
    for ln in lines:
        if ln.startswith("## "):
            if cur_header is not None or cur_body:
                body_text = "\n".join(cur_body)
                sections.append((cur_header or "<intro>", body_text, len(body_text.encode("utf-8"))))
            cur_header = ln[3:].strip()
            cur_body = []
        else:
            cur_body.append(ln)
    if cur_header is not None or cur_body:
        body_text = "\n".join(cur_body)
        sections.append((cur_header or "<intro>", body_text, len(body_text.encode("utf-8"))))
    return sections

def file_coverage(M, weights):
    """Weighted sum (weight = section byte length, normalized) of per-section coverage."""
    w = np.array(weights, dtype=float)
    w = w / w.sum()
    return (M * w[:, None]).sum(axis=0)

def coverage_to_binary(c, threshold=0.5):
    return (c >= threshold).astype(int)

def lift_to_s2(c, M=None):
    """Compressed Stage 1: c → p on S² via PCA top-2 (M must be supplied) → stereographic from south pole.
    Möbius = identity for first cycle.
    """
    if M is None:
        # fallback: use c directly (no PCA, no M) - won't have N≥2 — only use for ideal pole
        # Treat c as 1-row M
        M_arr = c.reshape(1, -1).astype(float)
    else:
        M_arr = M.astype(float)

    if M_arr.shape[0] < 2:
        # No PCA possible; fall back to direct stereographic on c with self-centering
        u = float(c.sum()) - 4.5  # rough centering
        v = 0.0
        return stereographic(u, v)

    # Center rows (subtract mean of M rows)
    mu = M_arr.mean(axis=0)
    Mc = M_arr - mu
    # SVD
    U, S, Vt = np.linalg.svd(Mc, full_matrices=False)
    W2 = Vt[:2].T  # 9×2
    # Project per-section
    proj = Mc @ W2  # N×2
    # File-level aggregate = weighted mean of proj (weights = row weights)
    # We just use simple mean for the S² coordinate (geometric center of section projections)
    uv = proj.mean(axis=0)
    u, v = float(uv[0]), float(uv[1])
    return stereographic(u, v), W2, S

def stereographic(u, v):
    """(u,v) → (X,Y,Z) on S² from south pole (0,0,-1).
    X = 2u / (1 + u² + v²)
    Y = 2v / (1 + u² + v²)
    Z = (u² + v² - 1) / (1 + u² + v²)
    """
    d = 1.0 + u*u + v*v
    X = 2.0 * u / d
    Y = 2.0 * v / d
    Z = (u*u + v*v - 1.0) / d
    p = np.array([X, Y, Z])
    norm = np.linalg.norm(p)
    assert abs(norm - 1.0) < 1e-6, f"unit-norm check failed: {norm}"
    return p

def chordal(a, b):
    return float(np.linalg.norm(a - b))

def main():
    text = SKILL_PATH.read_text()
    sections = parse_sections(text)
    headers = [h for h, _, _ in sections]
    body_lens = [blen for _, _, blen in sections]
    body_texts = [btxt for _, btxt, _ in sections]

    print(f"File: {SKILL_PATH}")
    print(f"Total bytes: {len(text.encode('utf-8'))}")
    print(f"Sections: {len(sections)}")
    print(f"Headers: {headers}")
    print()

    # Compute per-section coverage matrix M
    M = np.zeros((len(sections), 9), dtype=int)
    for i, btxt in enumerate(body_texts):
        M[i] = section_coverage(btxt)
    print("Per-section coverage matrix M (rows = sections):")
    for i, (h, cov) in enumerate(zip(headers, M)):
        covered = [PRIMITIVES[j] for j in range(9) if cov[j] == 1]
        missing = [PRIMITIVES[j] for j in range(9) if cov[j] == 0]
        print(f"  Section {i:2d}: {h[:50]!r:55s} covered={len(covered)} missing={missing}")
    print()

    # File-level coverage via weighted sum (weights = section byte length, normalized)
    weights = body_lens
    c_cont = file_coverage(M, weights)
    print(f"File-level coverage (continuous, weighted): {c_cont}")
    c_bin = coverage_to_binary(c_cont)
    covered = [PRIMITIVES[j] for j in range(9) if c_bin[j] == 1]
    missing_idx = [j for j in range(9) if c_bin[j] == 0]
    missing = [PRIMITIVES[j] for j in missing_idx]
    print(f"File-level coverage (binary, threshold 0.5): {c_bin.tolist()}")
    print(f"Covered primitives ({len(covered)}/9): {covered}")
    print(f"Missing primitives ({len(missing)}/9): {missing}")
    print()

    # S² lift (compressed Stage 1)
    p, W2, S = lift_to_s2(c_cont, M)
    p_star_ideal = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1], dtype=float)
    p_star_p, _, _ = lift_to_s2(p_star_ideal, M)  # ideal pole lifted through same M
    print(f"S² point p: {p}")
    print(f"‖p‖ = {np.linalg.norm(p):.10f}")
    print(f"PC1 + PC2 explained variance ratio: {(S[0]**2 + S[1]**2) / max(S**2).sum():.4f}" if len(S) >= 2 else "N/A")
    print(f"Ideal pole p* (lifted through same M): {p_star_p}")
    print(f"‖p*‖ = {np.linalg.norm(p_star_p):.10f}")
    print()

    # d_pre = chordal(p, p*)
    d_pre = chordal(p, p_star_p)
    print(f"d_pre (chordal p → p*): {d_pre:.10f}")
    print()

    # For each missing primitive, simulate flip (force 1 in every section) and recompute
    candidates = []
    for j in missing_idx:
        M_flip = M.copy()
        M_flip[:, j] = 1
        c_flip_cont = file_coverage(M_flip, weights)
        p_flip, _, _ = lift_to_s2(c_flip_cont, M_flip)
        # Recompute ideal pole with flipped M (same coverage vector is now [1,1,...,1])
        c_ideal_flip = np.ones(9)
        p_star_flip, _, _ = lift_to_s2(c_ideal_flip, M_flip)
        d_post = chordal(p_flip, p_star_flip)
        delta = d_pre - d_post
        candidates.append({
            "primitive": PRIMITIVES[j],
            "primitive_idx": j,
            "d_post": d_post,
            "delta": delta,
        })
        print(f"Candidate flip {PRIMITIVES[j]:25s} → d_post={d_post:.6f}  Δ={delta:+.6f}")
    print()

    # Single-action target = argmin d_post (geodesic-only criterion)
    candidates_sorted = sorted(candidates, key=lambda x: x["d_post"])
    winner = candidates_sorted[0]
    delta_winner = winner["delta"]
    print(f"Single-action target (geodesic winner): {winner['primitive']}")
    print(f"Δ_winner = {delta_winner:+.6f}")
    print()

    # Cycle outcome
    if all(c["delta"] <= 0 for c in candidates):
        outcome = "local-minimum"
        print(f"Cycle outcome: LOCAL MINIMUM (all Δ ≤ 0)")
    elif delta_winner <= 0:
        outcome = "failed"
        print(f"Cycle outcome: FAILED (winner Δ ≤ 0)")
    else:
        outcome = "succeeded"
        print(f"Cycle outcome: SUCCEEDED (winner Δ > 0)")
    print()

    # Cost ranking (rough heuristic)
    cost_map = {
        "p0_has_purpose": "medium",   # Adding TL;DR / Summary / Goal is moderate
        "p2_has_correction": "medium", # Adding "V\d+ failure / was wrong" needs substantive text
        "p8_has_priority": "low",      # Adding P0/P1/P2 labels is mechanical
    }
    for c in candidates:
        c["cost"] = cost_map.get(c["primitive"], "medium")

    # Predict post-edit residual
    # Per PR1: residual = ‖p - γ(t)‖₂ on S² (chordal from fitted curve at parameter t).
    # PR1 placed this skill at (X=+0.183, Y=+0.983, Z=-0.033) with residual 1.4444, t=0.2801.
    # Predicted post-edit residual ≈ original residual * (1 - Δ/d_pre) — proportional reduction.
    pr1_residual = 1.4444
    pr1_t = 0.2801
    pr1_p = np.array([0.183, 0.983, -0.033])
    # ‖pr1_p‖
    pr1_p_norm = np.linalg.norm(pr1_p)
    print(f"PR1 p (raw, from spec): {pr1_p}, ‖p‖={pr1_p_norm:.6f} (note: PR1 reports raw, may not be unit-norm)")
    # If not unit, normalize for the computation
    if abs(pr1_p_norm - 1.0) > 1e-6:
        pr1_p_unit = pr1_p / pr1_p_norm
        print(f"PR1 p normalized: {pr1_p_unit}, ‖p‖={np.linalg.norm(pr1_p_unit):.6f}")
    else:
        pr1_p_unit = pr1_p

    # Use the Δ-ratio to predict post-edit residual reduction
    if d_pre > 0:
        reduction_ratio = delta_winner / d_pre if delta_winner > 0 else 0.0
    else:
        reduction_ratio = 0.0
    predicted_post_residual = pr1_residual * (1.0 - reduction_ratio)
    print(f"PR1 reported residual: {pr1_residual}")
    print(f"Δ_winner/d_pre ratio: {reduction_ratio:.4f}")
    print(f"Predicted post-edit residual: {predicted_post_residual:.4f}")
    print()

    # Save artifacts
    cycle_data = {
        "file": "recursive-self-improvement",
        "cycle_id": "single-action-rsi-recursive-self-improvement-2026-08-06",
        "basis_used": "single-action-curve-rsi deep-research 9-primitive",
        "basis_mapping_to_pr1": {
            "trust_chain": "≈ has_test (verification patterns)",
            "cryptographic_identity": "≈ has_constraint (must/never/ban patterns)"
        },
        "section_count": len(sections),
        "section_headers": headers,
        "section_byte_lengths": body_lens,
        "section_coverage_matrix_M": M.tolist(),
        "file_coverage_continuous_c": c_cont.tolist(),
        "file_coverage_c": c_bin.tolist(),
        "covered_primitives": covered,
        "missing_primitives": missing,
        "missing_indices": missing_idx,
        "W2": W2.tolist(),
        "S_singular_values": S.tolist(),
        "s2_point_p": p.tolist(),
        "s2_norm_check": float(np.linalg.norm(p)),
        "ideal_pole_p_star": p_star_p.tolist(),
        "ideal_pole_p_star_norm": float(np.linalg.norm(p_star_p)),
        "d_pre": d_pre,
        "candidates": candidates,
        "single_action_target": winner["primitive"],
        "delta": delta_winner,
        "cycle_outcome": outcome,
        "predicted_post_edit_residual": predicted_post_residual,
        "pr1_residual_input": pr1_residual,
        "pr1_t_input": pr1_t,
        "pr1_p_reported_raw": pr1_p.tolist(),
    }
    (OUT_DIR / "cycle.json").write_text(json.dumps(cycle_data, indent=2))
    print(f"Wrote: {OUT_DIR / 'cycle.json'}")

    return cycle_data

if __name__ == "__main__":
    main()
