#!/usr/bin/env python3.12
"""render-cycle-4-nd-viewer.py — Cycle-4 repo-history N-D axis viewer, written
into `papers/data/nd-viewer-output/` alongside the existing 24-D skill-corpus
viewer built by `build-nd-axis-viewer.py`.

`build-nd-axis-viewer.py` stacks 9 internal-big-picture primitives + 12
negative-skill-space axes (scored from SKILL.md text) + 3 run-metadata fields
(cycle#, delta, FIRES) = 24-D, for the **79-skill corpus**. The NSS axes
(audience, inputs, outputs, ...) are SKILL.md-specific concepts that don't
apply to a repo-history event (a PR, issue, commit, or Linear ticket has no
"assumption set" or "composition" section to score).

Rather than force-fit the repo-history-skill's 324-item corpus through an
axis basis that doesn't describe it, this script builds a domain-appropriate
**16-D** basis for the SAME corpus already fit for `curve-map-output/`:

  - 9 repo-history primitives (has_purpose, has_sha, has_pr_ref, has_linear_ref,
    has_state_progression, has_author, has_cross_corpus_link, has_evidence,
    has_temporal_anchor) — binary, same as the curve-map fit.
  - 5 one-hot "kind" axes (kind_PR, kind_Issue, kind_Commit, kind_Release,
    kind_Linear) — the repo-history analog of a categorical metadata field.
  - 2 run-metadata fields (t = PC1 coordinate, residual = chordal distance
    to the fitted curve) — the repo-history analog of (cycle#, delta) in the
    skill-corpus viewer; there's no FIRES-equivalent single-cycle-delta here
    since repo-history items aren't RSI-cycled per-item.

Outputs (in `papers/data/nd-viewer-output/`, cycle-4-repo-history-prefixed):
  - nd-vectors-cycle-4-repo-history-2026-08-07.json
  - nd-pca-static-cycle-4-repo-history-2026-08-07.png
  - nd-viewer-cycle-4-repo-history-2026-08-07.html
  - nd-axis-correlation-cycle-4-repo-history-2026-08-07.csv
  - README-cycle-4-repo-history-2026-08-07.md
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import numpy as np
from scipy.linalg import svd
from scipy.special import lpmv

try:
    import plotly.graph_objects as go
except ImportError:
    go = None

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None

# --------------------------------------------------------------------------- #
# Paths.
# --------------------------------------------------------------------------- #
ROOT = Path("/var/workspace")
SPACE_DIR = "github-yubios-KS9n5GAT"
PAPERS_DIR = ROOT / "documents" / SPACE_DIR / "papers"
DATA_DIR = PAPERS_DIR / "data"
OUT_DIR = DATA_DIR / "nd-viewer-output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CYCLE4_ARCHIVE_JSON = DATA_DIR / "repo-history-skill-cycle-4-archive-2026-08-07.json"

PRIMITIVES_9: List[str] = [
    "has_purpose", "has_sha", "has_pr_ref", "has_linear_ref",
    "has_state_progression", "has_author", "has_cross_corpus_link",
    "has_evidence", "has_temporal_anchor",
]
KIND_AXES = ["kind_PR", "kind_Issue", "kind_Commit", "kind_Release", "kind_Linear"]
META_AXES = ["t", "residual"]
ALL_AXES = PRIMITIVES_9 + KIND_AXES + META_AXES
N_DIM = len(ALL_AXES)  # 16


# --------------------------------------------------------------------------- #
# Math pipeline (reused for t + residual, matching curve-map-output render).
# --------------------------------------------------------------------------- #
def pca_topk(M, k=2):
    mu = M.mean(axis=0)
    Mc = M - mu
    U, S, Vt = svd(Mc, full_matrices=False)
    Wk = Vt[:k].T
    var_total = (S ** 2).sum()
    explained = (S[:k] ** 2) / var_total if var_total > 0 else np.zeros(k)
    return Wk, mu, explained


def stereographic_from_south_pole(uv):
    u, v = uv[..., 0], uv[..., 1]
    denom = u * u + v * v + 1.0
    return np.stack([2.0 * u / denom, 2.0 * v / denom, (u * u + v * v - 1.0) / denom], axis=-1)


def real_spherical_harmonic_basis(ell, m, theta, phi):
    from math import factorial
    norm = np.sqrt((2 * ell + 1) / (4 * np.pi) * factorial(ell - abs(m)) / factorial(ell + abs(m)))
    x = np.cos(theta)
    P_lm = lpmv(abs(m), ell, x)
    if m == 0:
        return norm * P_lm
    elif m > 0:
        return np.sqrt(2.0) * norm * P_lm * np.cos(m * phi)
    else:
        return np.sqrt(2.0) * norm * P_lm * np.sin(abs(m) * phi)


def design_matrix(theta, phi, L=3):
    basis = []
    for ell in range(L + 1):
        for m in range(-ell, ell + 1):
            basis.append(real_spherical_harmonic_basis(ell, m, theta, phi))
    return np.stack(basis, axis=-1)


def fit_harmonic_curve(p, t, L=3, ridge_lambda=1e-3):
    theta = np.pi * t
    phi = 2.0 * np.pi * t
    Phi = design_matrix(theta, phi, L=L)
    PtP = Phi.T @ Phi + ridge_lambda * np.eye(Phi.shape[1])
    C = np.linalg.solve(PtP, Phi.T @ p)
    return C


def evaluate_curve(C, t, L=3):
    theta = np.pi * t
    phi = 2.0 * np.pi * t
    Phi = design_matrix(theta, phi, L=L)
    p_hat = Phi @ C
    norm = np.linalg.norm(p_hat, axis=-1, keepdims=True)
    return p_hat / np.where(norm < 1e-12, 1.0, norm)


def coordinate_t(M, W1):
    raw = M @ W1
    if raw.max() - raw.min() < 1e-12:
        return np.zeros_like(raw)
    return (raw - raw.min()) / (raw.max() - raw.min())


# --------------------------------------------------------------------------- #
# Vector construction.
# --------------------------------------------------------------------------- #
def build_meta_and_X(items_meta):
    coverage = np.array([it["coverage"] for it in items_meta], dtype=np.float64)  # [N,9]

    # Re-run the same 9-D curve fit as curve-map-output to get t + residual.
    W2, mu, _ = pca_topk(coverage, k=2)
    Mc = coverage - mu
    uv = Mc @ W2
    p = stereographic_from_south_pole(uv)
    t = coordinate_t(coverage, W2[:, 0])
    C = fit_harmonic_curve(p, t, L=3, ridge_lambda=1e-3)
    p_hat = evaluate_curve(C, t, L=3)
    residual = np.linalg.norm(p - p_hat, axis=-1)

    kinds = ["PR", "Issue", "Commit", "Release", "Linear"]
    meta, rows = [], []
    for i, it in enumerate(items_meta):
        kind_onehot = [1.0 if it["kind"] == k else 0.0 for k in kinds]
        vec = list(coverage[i]) + kind_onehot + [float(t[i]), float(residual[i])]
        assert len(vec) == N_DIM, f"vec len {len(vec)} != {N_DIM}"
        rows.append(vec)
        meta.append({
            "slug": f"{it['kind']}-{it['label']}", "kind": it["kind"],
            "repo": it["repo"], "url": it["url"],
            "missing": it["missing"], "t": float(t[i]), "residual": float(residual[i]),
        })

    X = np.asarray(rows, dtype=np.float64)
    sigma = X.std(axis=0)
    sigma[sigma == 0] = 1.0
    Xz = (X - X.mean(axis=0)) / sigma
    return meta, X, Xz


def pca_2d(Xz):
    U, S, Vt = np.linalg.svd(Xz, full_matrices=False)
    pcs = Xz @ Vt[:2].T
    var_explained = (S ** 2) / (S ** 2).sum()
    return pcs, var_explained[:2].tolist()


# --------------------------------------------------------------------------- #
# Output writers.
# --------------------------------------------------------------------------- #
def write_vectors_json(meta, pcs, X, out_path):
    out = {}
    for i, m in enumerate(meta):
        key = m["slug"]
        axes = {ALL_AXES[j]: float(X[i, j]) for j in range(N_DIM)}
        out[key] = {
            "axes": axes, "pca": [float(pcs[i, 0]), float(pcs[i, 1])],
            "kind": m["kind"], "repo": m["repo"], "url": m["url"],
            "missing_primitives": m["missing"], "t": m["t"], "residual": m["residual"],
        }
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"  saved {out_path} ({len(out)} rows)")


def write_correlation_csv(X, out_path):
    C = np.corrcoef(X.T)
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["axis"] + ALL_AXES)
        for i, name in enumerate(ALL_AXES):
            w.writerow([name] + [f"{C[i, j]:+.4f}" for j in range(N_DIM)])
    print(f"  saved {out_path}")


def write_static_png(meta, pcs, var_explained, out_path):
    if Image is None:
        print("  WARN: PIL not available; skipping static PNG")
        return
    W, H = 1400, 1000
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    try:
        f_title = ImageFont.truetype("/usr/share/fonts/google-noto-vf/NotoSans[wght].ttf", 22)
        f_label = ImageFont.truetype("/usr/share/fonts/google-noto-vf/NotoSans[wght].ttf", 11)
        f_sub = ImageFont.truetype("/usr/share/fonts/google-noto-vf/NotoSans[wght].ttf", 14)
    except Exception:
        f_title = ImageFont.load_default()
        f_label = ImageFont.load_default()
        f_sub = ImageFont.load_default()

    margin_l, margin_r, margin_t, margin_b = 100, 60, 90, 80
    plot_w, plot_h = W - margin_l - margin_r, H - margin_t - margin_b

    d.text((W / 2, 20), "N-D axis viewer — cycle-4 repo-history corpus", fill="#1a3a5c", font=f_title, anchor="mt")
    d.text((W / 2, 50),
           f"16-D vectors (9 primitives + 5 kind-onehot + t/residual) → PCA "
           f"(PC1 {var_explained[0]:.1%} / PC2 {var_explained[1]:.1%})",
           fill="#666666", font=f_sub, anchor="mt")

    xs, ys = pcs[:, 0], pcs[:, 1]
    x_min, x_max = float(xs.min()), float(xs.max())
    y_min, y_max = float(ys.min()), float(ys.max())
    xr = x_max - x_min if x_max > x_min else 1.0
    yr = y_max - y_min if y_max > y_min else 1.0
    x_min -= xr * 0.05; x_max += xr * 0.05
    y_min -= yr * 0.05; y_max += yr * 0.05

    def to_x(v): return margin_l + (v - x_min) / (x_max - x_min) * plot_w
    def to_y(v): return (margin_t + plot_h) - (v - y_min) / (y_max - y_min) * plot_h

    d.line([(margin_l, margin_t), (margin_l, margin_t + plot_h)], fill="#444444", width=2)
    d.line([(margin_l, margin_t + plot_h), (margin_l + plot_w, margin_t + plot_h)], fill="#444444", width=2)
    for i in range(7):
        v = x_min + i / 6 * (x_max - x_min)
        x = to_x(v)
        d.line([(x, margin_t + plot_h), (x, margin_t + plot_h + 4)], fill="#444444")
        d.text((x, margin_t + plot_h + 8), f"{v:+.2f}", fill="#444444", font=f_label, anchor="mt")
        v2 = y_min + i / 6 * (y_max - y_min)
        y = to_y(v2)
        d.line([(margin_l - 4, y), (margin_l, y)], fill="#444444")
        d.text((margin_l - 8, y), f"{v2:+.2f}", fill="#444444", font=f_label, anchor="rm")
    d.text((W / 2, H - margin_b + 35), f"PC1 ({var_explained[0]:.1%})", fill="#1a3a5c", font=f_sub, anchor="mt")
    d.text((30, H / 2), f"PC2 ({var_explained[1]:.1%})", fill="#1a3a5c", font=f_sub, anchor="mm")

    kind_colors = {"PR": "#5a8ec7", "Issue": "#c75a5a", "Commit": "#228b22",
                   "Release": "#cc6633", "Linear": "#9933cc"}
    for i, m in enumerate(meta):
        x, y = to_x(xs[i]), to_y(ys[i])
        c = kind_colors.get(m["kind"], "#888888")
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=c)
        if m["residual"] > 0.5 and i % 5 == 0:
            short = m["slug"][:18]
            d.text((x + 5, y - 5), f"{short} r{m['residual']:.2f}", fill=c, font=f_label, anchor="lm")

    leg_x, leg_y = margin_l, margin_t - 20
    for kind, col in kind_colors.items():
        d.ellipse([leg_x - 5, leg_y - 5, leg_x + 5, leg_y + 5], fill=col)
        d.text((leg_x + 8, leg_y), kind, fill="#444444", font=f_label, anchor="lm")
        leg_x += 100

    img.save(out_path, "PNG", dpi=(150, 150))
    print(f"  saved {out_path} ({out_path.stat().st_size} bytes)")


def write_html_viewer(meta, pcs, X, var_explained, out_path):
    if go is None:
        print("  WARN: plotly not available; skipping HTML viewer")
        return
    kind_vals = [m["kind"] for m in meta]
    kind_map = {"PR": 0, "Issue": 1, "Commit": 2, "Release": 3, "Linear": 4}
    color_vals = [kind_map.get(k, 5) for k in kind_vals]
    labels = [f"{m['slug']} r={m['residual']:.3f}" for m in meta]

    items = [{
        "slug": m["slug"], "kind": m["kind"],
        "axes": {ALL_AXES[j]: float(X[i, j]) for j in range(N_DIM)},
        "pca": [float(pcs[i, 0]), float(pcs[i, 1])],
        "missing": m["missing"], "residual": m["residual"],
    } for i, m in enumerate(meta)]

    axis_meta = []
    for j, name in enumerate(ALL_AXES):
        col = X[:, j]
        is_bool = name in PRIMITIVES_9 + KIND_AXES
        axis_meta.append({"name": name, "min": float(col.min()), "max": float(col.max()),
                          "median": float(np.median(col)), "is_bool": is_bool})

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=pcs[:, 0].tolist(), y=pcs[:, 1].tolist(), mode="markers",
        marker=dict(size=8, color=color_vals, colorscale="Viridis", showscale=True,
                    colorbar=dict(title="kind")),
        text=labels,
        hovertemplate="<b>%{text}</b><br>PC1=%{x:.3f} PC2=%{y:.3f}<extra></extra>",
        name="items",
    ))
    fig.update_layout(
        title=f"N-D axis viewer — cycle-4 repo-history (16-D → PC1 {var_explained[0]:.1%}, PC2 {var_explained[1]:.1%})",
        xaxis_title=f"PC1 ({var_explained[0]:.1%})", yaxis_title=f"PC2 ({var_explained[1]:.1%})",
        width=1100, height=720, margin=dict(l=60, r=40, t=80, b=60),
    )
    chart_html = fig.to_html(include_plotlyjs="cdn", full_html=False, div_id="nd-plot")

    slider_rows = []
    for am in axis_meta:
        if am["is_bool"]:
            slider_rows.append(
                f'<div class="slider-row"><label><b>{am["name"]}</b></label>'
                f'<input type="checkbox" id="ax-{am["name"]}" data-axis="{am["name"]}" checked>'
                f'<span class="hint">bool filter</span></div>')
        else:
            slider_rows.append(
                f'<div class="slider-row"><label><b>{am["name"]}</b></label>'
                f'<span class="val" id="val-{am["name"]}">{am["median"]:.3f}</span>'
                f'<input type="range" id="ax-{am["name"]}" data-axis="{am["name"]}" '
                f'min="{am["min"]:.4f}" max="{am["max"]:.4f}" step="0.01" '
                f'value="{am["median"]:.4f}">'
                f'<span class="hint">≥ threshold (items above)</span></div>')
    rows_html = "\n".join(slider_rows)
    items_json = json.dumps(items)
    axes_json = json.dumps(axis_meta)

    html = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<title>N-D axis viewer — cycle-4 repo-history corpus</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  body {{ font-family: 'Noto Sans', system-ui, -apple-system, sans-serif; margin: 12px; background: #fafafa; color: #222; }}
  h1 {{ color: #1a3a5c; margin: 0 0 6px 0; font-size: 18px; }}
  .sub {{ color: #666; font-size: 13px; margin-bottom: 14px; }}
  .layout {{ display: grid; grid-template-columns: 340px 1fr; gap: 16px; }}
  .panel {{ background: white; border: 1px solid #ddd; border-radius: 6px; padding: 12px; }}
  .panel h2 {{ font-size: 13px; margin: 0 0 8px 0; color: #1a3a5c; text-transform: uppercase; letter-spacing: 0.5px; }}
  .slider-row {{ display: grid; grid-template-columns: 130px 60px 1fr; gap: 6px; align-items: center; font-size: 12px; margin: 4px 0; }}
  .slider-row label {{ color: #1a3a5c; }}
  .slider-row .val {{ font-family: ui-monospace, monospace; color: #444; text-align: right; }}
  .slider-row input[type=range] {{ width: 100%; }}
  .slider-row .hint {{ font-size: 10px; color: #888; grid-column: 1 / -1; margin-top: -2px; }}
  .controls {{ margin-top: 10px; padding-top: 8px; border-top: 1px solid #eee; }}
  .controls button {{ background: #1a3a5c; color: white; border: 0; padding: 6px 10px; border-radius: 4px; font-size: 12px; cursor: pointer; }}
  .controls button:hover {{ background: #2a5a8c; }}
  .meta {{ font-size: 11px; color: #666; margin-top: 8px; }}
  #status {{ font-family: ui-monospace, monospace; font-size: 12px; }}
</style>
</head>
<body>
<h1>N-D axis viewer — cycle-4 repo-history corpus (324 items)</h1>
<div class="sub">9 repo-history primitives + 5 kind-onehot + t/residual = 16 sliders. Each slider sets a minimum threshold; the scatter filters items with axis ≥ threshold.</div>
<div class="layout">
  <div class="panel">
    <h2>Axis thresholds (≥)</h2>
    {rows_html}
    <div class="controls">
      <button onclick="resetSliders()">Reset to median</button>
      <button onclick="zerosAll()">Show all (zeros)</button>
      <div class="meta"><span id="status">0 / 0 items shown</span></div>
    </div>
  </div>
  <div class="panel" id="plot-host">
    {chart_html}
  </div>
</div>
<script>
const items = {items_json};
const axesMeta = {axes_json};

function applyFilters() {{
  const thresholds = {{}};
  for (const am of axesMeta) {{
    const el = document.getElementById('ax-' + am.name);
    if (am.is_bool) {{
      thresholds[am.name] = el.checked ? 1 : 0;
    }} else {{
      thresholds[am.name] = parseFloat(el.value);
      const valEl = document.getElementById('val-' + am.name);
      if (valEl) valEl.textContent = el.value;
    }}
  }}
  const filtered = items.filter(it => {{
    for (const [name, thr] of Object.entries(thresholds)) {{
      if ((it.axes[name] ?? 0) < thr) return false;
    }}
    return true;
  }});
  const x = filtered.map(it => it.pca[0]);
  const y = filtered.map(it => it.pca[1]);
  const txt = filtered.map(it => `${{it.slug}} r=${{it.residual.toFixed(3)}}`);
  const plotDiv = document.getElementById('nd-plot');
  Plotly.react(plotDiv, [{{
    x, y, text: txt, mode: 'markers', type: 'scatter',
    marker: {{ size: 9, color: '#1a3a5c' }},
    hovertemplate: '<b>%{{text}}</b><br>PC1=%{{x:.3f}} PC2=%{{y:.3f}}<extra></extra>',
    name: 'filtered'
  }}], {{ margin: {{ l: 60, r: 40, t: 30, b: 60 }}, xaxis: {{ title: 'PC1' }}, yaxis: {{ title: 'PC2' }} }});
  document.getElementById('status').textContent = `${{filtered.length}} / ${{items.length}} items shown`;
}}

function resetSliders() {{
  for (const am of axesMeta) {{
    const el = document.getElementById('ax-' + am.name);
    if (!el) continue;
    if (am.is_bool) el.checked = true;
    else el.value = am.median;
    el.dispatchEvent(new Event('input'));
  }}
  applyFilters();
}}

function zerosAll() {{
  for (const am of axesMeta) {{
    const el = document.getElementById('ax-' + am.name);
    if (!el) continue;
    if (am.is_bool) el.checked = false;
    else el.value = am.min;
    el.dispatchEvent(new Event('input'));
  }}
  applyFilters();
}}

for (const am of axesMeta) {{
  const el = document.getElementById('ax-' + am.name);
  if (!el) continue;
  el.addEventListener('input', applyFilters);
  el.addEventListener('change', applyFilters);
}}

applyFilters();
</script>
</body></html>
"""
    out_path.write_text(html, encoding="utf-8")
    print(f"  saved {out_path} ({out_path.stat().st_size} bytes)")


def write_readme(meta, var_explained, archive, out_path):
    n = len(meta)
    kinds_count = {}
    for m in meta:
        kinds_count[m["kind"]] = kinds_count.get(m["kind"], 0) + 1
    prim_lines = "\n".join(f"- `{p}` — 1 if the item's text matches the primitive's detection pattern, else 0."
                            for p in PRIMITIVES_9)
    kind_lines = "\n".join(f"- `{k}` — 1 if this item is a `{k[5:]}`, else 0 (one-hot)." for k in KIND_AXES)

    md = f"""# N-D axis viewer — cycle-4 repo-history corpus feature space

Generated by `render-cycle-4-nd-viewer.py` on **{datetime.now(timezone.utc).isoformat()}**.

## Why this exists here, and how it differs from the 24-D skill-corpus viewer

`nd-viewer-output/` is normally owned by `build-nd-axis-viewer.py`, which builds a
**24-D** vector (9 internal-big-picture primitives + 12 negative-skill-space axes
scored from SKILL.md text + 3 run-metadata fields) for the **79-skill corpus**.

The repo-history-skill's 324-item corpus (PRs, issues, commits, releases, Linear
tickets) has no SKILL.md text and no per-cycle RSI metadata — the 12 NSS axes and
the (cycle#, delta, FIRES) triple don't apply to a git commit. Rather than force
an inapplicable basis onto this corpus, this script builds a domain-appropriate
**{N_DIM}-D** vector instead:

1. **9 repo-history primitives** (binary, same basis as `curve-map-output/`'s
   cycle-4 render): has_purpose, has_sha, has_pr_ref, has_linear_ref,
   has_state_progression, has_author, has_cross_corpus_link, has_evidence,
   has_temporal_anchor.
2. **5 kind-onehot axes** — the repo-history analog of a categorical field
   (there's no single natural NSS-style multi-axis breakdown for a PR vs a
   commit vs a Linear ticket, so kind is the most informative categorical
   signal available).
3. **2 run-metadata fields** — `t` (PC1 coordinate of the 9-D coverage, same as
   the curve-map fit) and `residual` (chordal distance to the fitted γ(t) curve)
   — the analog of (cycle#, delta) in the skill-corpus viewer, since repo-history
   items aren't RSI-cycled per-item the way skills are.

## Axis list

### 9 repo-history primitives (same as curve-map-output/'s cycle-4 render)

{prim_lines}

### 5 kind-onehot axes

{kind_lines}

### 2 run-metadata fields

- `t` — PC1 coordinate of the centered 9-D coverage matrix, min-max scaled to [0,1].
- `residual` — chordal S² distance to the fitted spherical-harmonic curve γ(t).

## Stats

- Corpus: **{n} items** ({archive['corpus_breakdown']})
- PCA explained variance: **PC1 {var_explained[0]:.1%}, PC2 {var_explained[1]:.1%}** (sum {sum(var_explained):.1%})
- Kind breakdown: {kinds_count}

## Outputs (in `papers/data/nd-viewer-output/`, cycle-4-repo-history-prefixed)

| File | Description |
|---|---|
| `nd-vectors-cycle-4-repo-history-2026-08-07.json` | Every item's {N_DIM}-D axis values + 2D PCA coords |
| `nd-pca-static-cycle-4-repo-history-2026-08-07.png` | Labeled static PCA scatter, color = kind |
| `nd-viewer-cycle-4-repo-history-2026-08-07.html` | Interactive Plotly scatter, {N_DIM} sliders |
| `nd-axis-correlation-cycle-4-repo-history-2026-08-07.csv` | Pairwise correlation across all {N_DIM} axes |
| `README-cycle-4-repo-history-2026-08-07.md` | This file |

## How to regenerate

```bash
python3.12 papers/scripts/render-cycle-4-nd-viewer.py
```

Requires the cached archive at `papers/data/repo-history-skill-cycle-4-archive-2026-08-07.json`
(produced by `render-cycle-4-fit.py`'s corpus fetch step). No live API calls — pure
re-render of already-fetched data.

## Deviation from the spec (honestly flagged)

This is NOT a drop-in extension of the existing 24-D viewer's corpus — it's a
**parallel, smaller viewer for a different corpus with a different, domain-fit
basis** ({N_DIM}-D vs 24-D). Merging the two would require inventing NSS-axis
scores for git commits and Linear tickets, which has no principled basis. If a
true unified viewer across both corpora is wanted later, the right approach is
a shared projection of the primitive-count / saturation signal only (the one
axis both bases share conceptually), not a literal 24-D ⊕ {N_DIM}-D stack.
"""
    out_path.write_text(md, encoding="utf-8")
    print(f"  saved {out_path} ({out_path.stat().st_size} bytes)")


def main():
    print("=== CYCLE 4 REPO-HISTORY N-D AXIS VIEWER → nd-viewer-output/ ===")
    print(f"Date: {datetime.now(timezone.utc).isoformat()}")
    print(f"Output: {OUT_DIR}\n")

    if not CYCLE4_ARCHIVE_JSON.exists():
        print(f"FATAL: {CYCLE4_ARCHIVE_JSON} not found — run render-cycle-4-fit.py first.", file=sys.stderr)
        sys.exit(1)

    with open(CYCLE4_ARCHIVE_JSON) as f:
        archive = json.load(f)
    items_meta = archive["items"]
    print(f"[1/3] Loaded {len(items_meta)} items from cache")

    meta, X, Xz = build_meta_and_X(items_meta)
    pcs, var_explained = pca_2d(Xz)
    print(f"[2/3] Built {X.shape} matrix, PCA PC1={var_explained[0]:.4f} PC2={var_explained[1]:.4f}")

    print("[3/3] Writing outputs...")
    write_vectors_json(meta, pcs, X, OUT_DIR / "nd-vectors-cycle-4-repo-history-2026-08-07.json")
    write_correlation_csv(X, OUT_DIR / "nd-axis-correlation-cycle-4-repo-history-2026-08-07.csv")
    write_static_png(meta, pcs, var_explained, OUT_DIR / "nd-pca-static-cycle-4-repo-history-2026-08-07.png")
    write_html_viewer(meta, pcs, X, var_explained, OUT_DIR / "nd-viewer-cycle-4-repo-history-2026-08-07.html")
    write_readme(meta, var_explained, archive, OUT_DIR / "README-cycle-4-repo-history-2026-08-07.md")

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
