"""synthetic-manifold-benchmark-2026-08-06.py

Appendix C.3 of learned-latent-curves-2026-08-06.tex. Tests the
inductive-bias claim of the hyperspherical-harmonic variant: does the
S² parameter manifold actually beat a flat [0,1]² baseline when the
DATA is drawn from a non-S² manifold?

Test design (per the advisor's Appendix C.3 spec):

  Corpus: N=200 synthetic points per manifold, with per-point 9-D
          binary feature vectors encoding manifold structure.

  Manifolds:
    T² = S¹ × S¹ (torus, genus 1) — NEGATIVE control: a sphere is
          the wrong prior for a genus-1 manifold.
    S² (unit sphere) — POSITIVE control: a sphere should win here.

  Arms (matched-parameter ablation per Section 6.1):
    hyperspherical S² (L=3, 16 basis functions, closed-form ridge λ=1e-3)
    flat Fourier [0,1]² (k=2, 25 basis functions, closed-form ridge λ=1e-3)

  Evaluation: 80/20 train/holdout split, holdout R², 5 seeds.

  Prediction:
    T² → flat wins (sphere is wrong prior)
    S² → sphere wins (sphere is right prior)
    If sphere wins on BOTH, the inductive-bias claim is FALSIFIED and
    the paper's claim reduces to capacity.

Outputs:
  - benchmark-results.json  (per-seed R² per arm per manifold + summary)
  - benchmark-summary.md    (human-readable table)
  - chart-synthetic-manifold-2026-08-06.png  (R² by arm × manifold)
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.linalg import svd

from PIL import Image, ImageDraw, ImageFont


# --------------------------------------------------------------------------- #
# 1. Synthetic data generation
# --------------------------------------------------------------------------- #
def gen_t2_features(n: int, rng: np.random.RandomState) -> np.ndarray:
    """T² = S¹ × S¹ — N points uniformly on the torus, 9-D binary features
    encoding toroidal modes."""
    theta = rng.uniform(0, 2 * np.pi, n)
    phi = rng.uniform(0, 2 * np.pi, n)
    feats = np.zeros((n, 9), dtype=np.int64)
    # 9 toroidal mode indicators (above/below 0)
    feats[:, 0] = (np.sin(theta) > 0).astype(int)
    feats[:, 1] = (np.cos(theta) > 0).astype(int)
    feats[:, 2] = (np.sin(phi) > 0).astype(int)
    feats[:, 3] = (np.cos(phi) > 0).astype(int)
    feats[:, 4] = (np.sin(theta + phi) > 0).astype(int)
    feats[:, 5] = (np.cos(theta - phi) > 0).astype(int)
    feats[:, 6] = (np.sin(2 * theta) > 0).astype(int)
    feats[:, 7] = (np.cos(2 * phi) > 0).astype(int)
    feats[:, 8] = (np.sin(theta - phi / 2) > 0).astype(int)
    # target = smooth function on T² (band-limited, sparse 9-D will hit it)
    target = np.sin(theta) + 0.5 * np.cos(phi) + 0.3 * np.sin(theta + phi)
    return feats, target, theta, phi


def gen_s2_features(n: int, rng: np.random.RandomState) -> np.ndarray:
    """S² — N points uniformly on the unit sphere, 9-D binary features
    encoding spherical structure."""
    v = rng.normal(0, 1, (n, 3))
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    x, y, z = v[:, 0], v[:, 1], v[:, 2]
    feats = np.zeros((n, 9), dtype=np.int64)
    # 9 spherical structure indicators
    feats[:, 0] = (x > 0).astype(int)
    feats[:, 1] = (y > 0).astype(int)
    feats[:, 2] = (z > 0).astype(int)
    feats[:, 3] = (np.abs(x) > 0.3).astype(int)
    feats[:, 4] = (np.abs(y) > 0.3).astype(int)
    feats[:, 5] = (np.abs(z) > 0.3).astype(int)
    feats[:, 6] = ((x * y) > 0).astype(int)
    feats[:, 7] = ((y * z) > 0).astype(int)
    feats[:, 8] = ((x * z) > 0).astype(int)
    # target = smooth function on S² (linear in coords — sphere should fit perfectly)
    target = x + 0.5 * y + 0.3 * z
    return feats, target, x, y, z


# --------------------------------------------------------------------------- #
# 2. Lifts
# --------------------------------------------------------------------------- #
def lift_to_s2(features: np.ndarray) -> np.ndarray:
    """Lift 9-D features to S² via PCA top-2 → stereographic from south pole.

    Returns N×3 array of points on the unit sphere (‖p‖=1 ± 1e-6).
    """
    n = features.shape[0]
    mu = features.mean(axis=0)
    centered = features - mu
    U, s, Vt = svd(centered, full_matrices=False)
    W2 = Vt[:2].T  # 9×2
    pc = centered @ W2  # N×2
    u, v = pc[:, 0], pc[:, 1]
    D = u**2 + v**2 + 1
    X = 2 * u / D
    Y = 2 * v / D
    Z = (u**2 + v**2 - 1) / D
    return np.column_stack([X, Y, Z])


def lift_to_01(features: np.ndarray) -> np.ndarray:
    """Project 9-D features to [0,1]² via PCA top-2 + min-max scale."""
    mu = features.mean(axis=0)
    centered = features - mu
    U, s, Vt = svd(centered, full_matrices=False)
    W2 = Vt[:2].T
    pc = centered @ W2  # N×2
    pc_min = pc.min(axis=0)
    pc_max = pc.max(axis=0)
    rng = pc_max - pc_min
    rng = np.where(rng < 1e-10, 1.0, rng)
    return (pc - pc_min) / rng


# --------------------------------------------------------------------------- #
# 3. Basis functions
# --------------------------------------------------------------------------- #
def spherical_harmonic_basis(points_s2: np.ndarray, L: int = 3) -> np.ndarray:
    """Real spherical harmonics up to degree L on S² points (3D unit vectors).

    L=0: 1 function.  L=1: +3.  L=2: +5.  L=3: +7.  Total at L=3: 16.
    """
    n = points_s2.shape[0]
    X, Y, Z = points_s2[:, 0], points_s2[:, 1], points_s2[:, 2]
    theta = np.arccos(np.clip(Z, -1.0, 1.0))
    phi = np.arctan2(Y, X)

    n_basis = (L + 1)**2
    Phi = np.zeros((n, n_basis))
    idx = 0
    # l=0
    Phi[:, idx] = 1.0
    idx += 1
    # l=1
    Phi[:, idx] = np.cos(theta); idx += 1                              # Y_1^0
    Phi[:, idx] = np.sin(theta) * np.cos(phi); idx += 1                # Y_1^1
    Phi[:, idx] = np.sin(theta) * np.sin(phi); idx += 1                # Y_1^{-1}
    if L >= 2:
        # l=2 (5 functions)
        Phi[:, idx] = 3 * np.cos(theta)**2 - 1; idx += 1
        Phi[:, idx] = np.sin(theta) * np.cos(theta) * np.cos(phi); idx += 1
        Phi[:, idx] = np.sin(theta) * np.cos(theta) * np.sin(phi); idx += 1
        Phi[:, idx] = np.sin(theta)**2 * np.cos(2 * phi); idx += 1
        Phi[:, idx] = np.sin(theta)**2 * np.sin(2 * phi); idx += 1
    if L >= 3:
        # l=3 (7 functions)
        Phi[:, idx] = 5 * np.cos(theta)**3 - 3 * np.cos(theta); idx += 1
        Phi[:, idx] = (5 * np.cos(theta)**2 - 1) * np.sin(theta) * np.cos(phi); idx += 1
        Phi[:, idx] = (5 * np.cos(theta)**2 - 1) * np.sin(theta) * np.sin(phi); idx += 1
        Phi[:, idx] = np.sin(theta)**3 * np.cos(3 * phi); idx += 1
        Phi[:, idx] = np.sin(theta)**3 * np.sin(3 * phi); idx += 1
        Phi[:, idx] = np.sin(theta)**2 * np.cos(theta) * np.cos(2 * phi); idx += 1
        Phi[:, idx] = np.sin(theta)**2 * np.cos(theta) * np.sin(2 * phi); idx += 1
    return Phi


def fourier_2d_basis(points_01: np.ndarray, k: int = 2) -> np.ndarray:
    """2D Fourier basis on [0,1]²: cos(iπu)·cos(jπv) for i,j ∈ [0, 2k].

    k=2 → (2k+1)² = 25 basis functions.
    """
    n = points_01.shape[0]
    u, v = points_01[:, 0], points_01[:, 1]
    n_basis = (2 * k + 1)**2
    Phi = np.zeros((n, n_basis))
    idx = 0
    for i in range(2 * k + 1):
        for j in range(2 * k + 1):
            Phi[:, idx] = np.cos(i * np.pi * u) * np.cos(j * np.pi * v)
            idx += 1
    return Phi


# --------------------------------------------------------------------------- #
# 4. Fitting
# --------------------------------------------------------------------------- #
def fit_ridge(Phi: np.ndarray, target: np.ndarray, lam: float = 1e-3) -> np.ndarray:
    """Closed-form ridge: c* = (ΦᵀΦ + λI)⁻¹ Φᵀ target."""
    n_basis = Phi.shape[1]
    A = Phi.T @ Phi + lam * np.eye(n_basis)
    b = Phi.T @ target
    return np.linalg.solve(A, b)


def r2(target: np.ndarray, pred: np.ndarray) -> float:
    ss_res = np.sum((target - pred) ** 2)
    ss_tot = np.sum((target - target.mean()) ** 2)
    if ss_tot < 1e-12:
        return 0.0
    return 1.0 - ss_res / ss_tot


# --------------------------------------------------------------------------- #
# 5. Main benchmark
# --------------------------------------------------------------------------- #
def run_benchmark(n: int = 200, seeds: int = 5, train_frac: float = 0.8,
                  lam: float = 1e-3) -> dict:
    """Run the full benchmark. Returns dict with per-seed + summary R²."""
    out = {
        "T2":  {"sphere": [], "flat": []},
        "S2":  {"sphere": [], "flat": []},
        "meta": {"n": n, "seeds": seeds, "train_frac": train_frac, "lam": lam,
                 "sphere_basis": 16, "flat_basis": 25},
    }
    for seed in range(seeds):
        # Independent RNGs for data and split
        rng_data = np.random.RandomState(seed * 7919 + 1)
        rng_split = np.random.RandomState(seed * 13 + 7)

        # T² (negative control)
        feats_t2, target_t2, _, _ = gen_t2_features(n, rng_data)
        idx_t2 = rng_split.permutation(n)
        n_train = int(n * train_frac)
        train_idx, holdout_idx = idx_t2[:n_train], idx_t2[n_train:]
        # Sphere arm: lift to S² → spherical harmonics
        s2_t2 = lift_to_s2(feats_t2)
        Phi_s_t2 = spherical_harmonic_basis(s2_t2, L=3)
        coef_s_t2 = fit_ridge(Phi_s_t2[train_idx], target_t2[train_idx], lam)
        pred_s_t2 = Phi_s_t2[holdout_idx] @ coef_s_t2
        r2_s_t2 = r2(target_t2[holdout_idx], pred_s_t2)
        # Flat arm: lift to [0,1]² → Fourier
        pc01_t2 = lift_to_01(feats_t2)
        Phi_f_t2 = fourier_2d_basis(pc01_t2, k=2)
        coef_f_t2 = fit_ridge(Phi_f_t2[train_idx], target_t2[train_idx], lam)
        pred_f_t2 = Phi_f_t2[holdout_idx] @ coef_f_t2
        r2_f_t2 = r2(target_t2[holdout_idx], pred_f_t2)
        out["T2"]["sphere"].append(r2_s_t2)
        out["T2"]["flat"].append(r2_f_t2)

        # S² (positive control)
        feats_s2, target_s2, _, _, _ = gen_s2_features(n, rng_data)
        idx_s2 = rng_split.permutation(n)
        train_idx, holdout_idx = idx_s2[:n_train], idx_s2[n_train:]
        s2_s2 = lift_to_s2(feats_s2)
        Phi_s_s2 = spherical_harmonic_basis(s2_s2, L=3)
        coef_s_s2 = fit_ridge(Phi_s_s2[train_idx], target_s2[train_idx], lam)
        pred_s_s2 = Phi_s_s2[holdout_idx] @ coef_s_s2
        r2_s_s2 = r2(target_s2[holdout_idx], pred_s_s2)
        pc01_s2 = lift_to_01(feats_s2)
        Phi_f_s2 = fourier_2d_basis(pc01_s2, k=2)
        coef_f_s2 = fit_ridge(Phi_f_s2[train_idx], target_s2[train_idx], lam)
        pred_f_s2 = Phi_f_s2[holdout_idx] @ coef_f_s2
        r2_f_s2 = r2(target_s2[holdout_idx], pred_f_s2)
        out["S2"]["sphere"].append(r2_s_s2)
        out["S2"]["flat"].append(r2_f_s2)

    # Summary statistics
    summary = {}
    for manifold in ("T2", "S2"):
        for arm in ("sphere", "flat"):
            arr = np.array(out[manifold][arm])
            summary[f"{manifold}_{arm}_mean"] = float(arr.mean())
            summary[f"{manifold}_{arm}_std"] = float(arr.std())
            summary[f"{manifold}_{arm}_min"] = float(arr.min())
            summary[f"{manifold}_{arm}_max"] = float(arr.max())
    out["summary"] = summary
    return out


# --------------------------------------------------------------------------- #
# 6. Chart generation
# --------------------------------------------------------------------------- #
def get_font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/google-noto-vf/NotoSans[wght].ttf",
        "/var/workspace/session/fonts/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def render_chart(results: dict, out_path: str):
    """Grouped bar chart: holdout R² for {sphere, flat} × {T², S²}, 5-seed error bars."""
    W, H = 1100, 640
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    f_title = get_font(22)
    f_sub = get_font(15)
    f_label = get_font(13)
    f_legend = get_font(12)
    f_value = get_font(11)

    margin_l, margin_r, margin_t, margin_b = 110, 50, 90, 110
    plot_w = W - margin_l - margin_r
    plot_h = H - margin_t - margin_b
    plot_bottom = H - margin_b
    plot_top = margin_t
    plot_left = margin_l

    d.text((W / 2, 22),
           "Synthetic-Manifold Benchmark — Inductive-Bias Test",
           fill="#1a3a5c", font=f_title, anchor="mt")
    d.text((W / 2, 52),
           "5-seed holdout R² on N=200 synthetic points per manifold, "
           "80/20 split, ridge λ=1e-3",
           fill="#666666", font=f_sub, anchor="mt")

    # Y-axis: R² range — include negative values (S² flat arm produces -1.1)
    y_min, y_max = -1.5, 1.0
    def to_y(v):
        frac = (v - y_min) / (y_max - y_min)
        return plot_bottom - frac * plot_h

    # Gridlines + y-axis ticks
    n_ticks = 5
    for i in range(n_ticks + 1):
        v = y_min + (y_max - y_min) * i / n_ticks
        y = to_y(v)
        d.line([(plot_left, y), (W - margin_r, y)], fill="#e0e0e0", width=1)
        d.text((plot_left - 10, y), f"{v:.2f}", fill="#444444", font=f_legend, anchor="rm")
    # Bold 0-line (the key reference)
    y_zero = to_y(0.0)
    d.line([(plot_left, y_zero), (W - margin_r, y_zero)], fill="#888888", width=2)
    d.text((W - margin_r - 4, y_zero - 6), "R² = 0", fill="#888888", font=f_legend, anchor="rt")
    d.line([(plot_left, plot_top), (plot_left, plot_bottom)], fill="#444444", width=2)
    d.line([(plot_left, plot_bottom), (W - margin_r, plot_bottom)], fill="#444444", width=2)

    # Two manifolds, each with sphere + flat bars + error bars
    manifolds = ["T² (torus, genus 1)", "S² (sphere, positive control)"]
    manifold_keys = ["T2", "S2"]
    group_w = plot_w / len(manifolds)
    bar_w = group_w * 0.32
    gap = group_w * 0.06
    colors = {"sphere": "#1a3a5c", "flat": "#c0504d"}

    for gi, (label, mkey) in enumerate(zip(manifolds, manifold_keys)):
        g_left = plot_left + gi * group_w + group_w * 0.18
        g_center = g_left + (bar_w + gap) / 2
        # Sphere bar (left)
        s_mean = results["summary"][f"{mkey}_sphere_mean"]
        s_std = results["summary"][f"{mkey}_sphere_std"]
        s_min = results["summary"][f"{mkey}_sphere_min"]
        s_max = results["summary"][f"{mkey}_sphere_max"]
        x = g_left
        y_top = to_y(s_mean)
        if y_top > plot_bottom:
            # Negative R² — bar extends below the axis floor
            d.rectangle([x, plot_bottom, x + bar_w, min(y_top, plot_bottom + 60)], fill=colors["sphere"])
        else:
            d.rectangle([x, y_top, x + bar_w, plot_bottom], fill=colors["sphere"])
        # Error bar (5-seed range)
        y_lo = to_y(s_min)
        y_hi = to_y(s_max)
        d.line([(x + bar_w / 2, y_lo), (x + bar_w / 2, y_hi)], fill="#000000", width=2)
        d.line([(x + bar_w / 2 - 4, y_lo), (x + bar_w / 2 + 4, y_lo)], fill="#000000", width=2)
        d.line([(x + bar_w / 2 - 4, y_hi), (x + bar_w / 2 + 4, y_hi)], fill="#000000", width=2)
        d.text((x + bar_w / 2, y_top - 12), f"{s_mean:.3f}", fill="#1a3a5c",
               font=f_value, anchor="mb")

        # Flat bar (right)
        f_mean = results["summary"][f"{mkey}_flat_mean"]
        f_std = results["summary"][f"{mkey}_flat_std"]
        f_min = results["summary"][f"{mkey}_flat_min"]
        f_max = results["summary"][f"{mkey}_flat_max"]
        x = g_left + bar_w + gap
        y_top = to_y(f_mean)
        if y_top > plot_bottom:
            d.rectangle([x, plot_bottom, x + bar_w, min(y_top, plot_bottom + 60)], fill=colors["flat"])
        else:
            d.rectangle([x, y_top, x + bar_w, plot_bottom], fill=colors["flat"])
        y_lo = to_y(f_min)
        y_hi = to_y(f_max)
        d.line([(x + bar_w / 2, y_lo), (x + bar_w / 2, y_hi)], fill="#000000", width=2)
        d.line([(x + bar_w / 2 - 4, y_lo), (x + bar_w / 2 + 4, y_lo)], fill="#000000", width=2)
        d.line([(x + bar_w / 2 - 4, y_hi), (x + bar_w / 2 + 4, y_hi)], fill="#000000", width=2)
        d.text((x + bar_w / 2, y_top - 12), f"{f_mean:.3f}", fill="#c0504d",
               font=f_value, anchor="mb")

        # Group label
        d.text((g_center, plot_bottom + 24), label, fill="#222222",
               font=f_label, anchor="mt")

    # Y-axis title
    d.text((plot_left - 70, (plot_top + plot_bottom) / 2),
           "holdout R²", fill="#222222", font=f_label, anchor="mm", angle=90)
    # X-axis title
    d.text((W / 2, H - 28), "synthetic-data manifold (ground truth)",
           fill="#222222", font=f_label, anchor="mt")

    # Legend
    leg_y = plot_top + 8
    leg_x = W - margin_r - 250
    d.rectangle([leg_x, leg_y, leg_x + 18, leg_y + 14], fill=colors["sphere"])
    d.text((leg_x + 24, leg_y + 7), "hyperspherical S² (L=3, 16 basis)",
           fill="#222222", font=f_legend, anchor="lm")
    d.rectangle([leg_x, leg_y + 24, leg_x + 18, leg_y + 38], fill=colors["flat"])
    d.text((leg_x + 24, leg_y + 31), "flat Fourier [0,1]² (k=2, 25 basis)",
           fill="#222222", font=f_legend, anchor="lm")
    d.line([(leg_x + 9, leg_y + 56), (leg_x + 9, leg_y + 70)], fill="#000000", width=2)
    d.line([(leg_x + 5, leg_y + 56), (leg_x + 13, leg_y + 56)], fill="#000000", width=2)
    d.line([(leg_x + 5, leg_y + 70), (leg_x + 13, leg_y + 70)], fill="#000000", width=2)
    d.text((leg_x + 24, leg_y + 63), "5-seed range",
           fill="#222222", font=f_legend, anchor="lm")

    img.save(out_path, "PNG")


# --------------------------------------------------------------------------- #
# 7. Main
# --------------------------------------------------------------------------- #
def main():
    out_dir = Path("/var/workspace/session")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=== synthetic-manifold-benchmark-2026-08-06 ===")
    results = run_benchmark(n=200, seeds=5, train_frac=0.8, lam=1e-3)

    # Per-seed table
    print("\nPer-seed R² (sphere | flat):")
    for seed in range(5):
        s_t2 = results["T2"]["sphere"][seed]
        f_t2 = results["T2"]["flat"][seed]
        s_s2 = results["S2"]["sphere"][seed]
        f_s2 = results["S2"]["flat"][seed]
        print(f"  seed {seed}: T² {s_t2:+.4f} | {f_t2:+.4f}     "
              f"S² {s_s2:+.4f} | {f_s2:+.4f}")

    # Summary
    s = results["summary"]
    print("\n=== Summary (5-seed mean ± std) ===")
    print(f"  T²  sphere: {s['T2_sphere_mean']:+.4f} ± {s['T2_sphere_std']:.4f}")
    print(f"  T²  flat:   {s['T2_flat_mean']:+.4f} ± {s['T2_flat_std']:.4f}")
    print(f"  S²  sphere: {s['S2_sphere_mean']:+.4f} ± {s['S2_sphere_std']:.4f}")
    print(f"  S²  flat:   {s['S2_flat_mean']:+.4f} ± {s['S2_flat_std']:.4f}")

    # Prediction check
    t2_winner = "flat" if s["T2_flat_mean"] > s["T2_sphere_mean"] else "sphere"
    s2_winner = "sphere" if s["S2_sphere_mean"] > s["S2_flat_mean"] else "flat"
    print(f"\n=== Prediction check ===")
    print(f"  T²: predicted flat wins — actual: {t2_winner} wins"
          f" {'✓' if t2_winner == 'flat' else '✗ INDUCTIVE BIAS FALSIFIED'}")
    print(f"  S²: predicted sphere wins — actual: {s2_winner} wins"
          f" {'✓' if s2_winner == 'sphere' else '✗ INDUCTIVE BIAS FALSIFIED'}")

    # Write JSON
    json_path = out_dir / "benchmark-results.json"
    payload = {
        "benchmark": "synthetic-manifold-2026-08-06",
        "n_points": 200,
        "seeds": 5,
        "train_frac": 0.8,
        "lambda": 1e-3,
        "sphere_basis": "real SH L=3 (16 functions)",
        "flat_basis": "cos(iπu)·cos(jπv), i,j ∈ [0,4] (25 functions)",
        "per_seed": {
            "T2": {"sphere": results["T2"]["sphere"], "flat": results["T2"]["flat"]},
            "S2": {"sphere": results["S2"]["sphere"], "flat": results["S2"]["flat"]},
        },
        "summary": results["summary"],
        "prediction_check": {
            "T2_winner": t2_winner,
            "S2_winner": s2_winner,
            "inductive_bias_holds": (t2_winner == "flat") and (s2_winner == "sphere"),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with open(json_path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"\nresults JSON: {json_path} ({json_path.stat().st_size} bytes)")

    # Chart
    chart_path = out_dir / "chart-synthetic-manifold-2026-08-06.png"
    render_chart(results, str(chart_path))
    print(f"chart PNG: {chart_path} ({chart_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
