#!/usr/bin/env python3.12
"""Render cycle-3 repo-refs-skill N-D axis viewer into papers/data/nd-viewer-output/.

Builds a domain-appropriate **14-D** vector basis for the 130-file refs/ corpus:
  - 7 repo-refs primitives (binary): same as curve-map-output
  - 5 size-bucket one-hot: <3KB / 3-6KB / 6-12KB / 12-25KB / ≥25KB
  - 2 run-metadata: t (PC1 coordinate), residual (chordal distance to γ(t))

Outputs (in papers/data/nd-viewer-output/, cycle-3-refs-prefixed):
  - nd-vectors-cycle-3-refs-2026-08-07.json
  - nd-pca-static-cycle-3-refs-2026-08-07.png
  - nd-viewer-cycle-3-refs-2026-08-07.html
  - nd-axis-correlation-cycle-3-refs-2026-08-07.csv
  - README-cycle-3-refs-2026-08-07.md
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.linalg import svd
from scipy.special import lpmv
from math import factorial

try:
    import plotly.graph_objects as go
except ImportError:
    go = None

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None

ROOT = Path("/var/workspace")
SPACE_DIR = "github-yubios-KS9n5GAT"
PAPERS_DIR = ROOT / "documents" / SPACE_DIR / "papers"
DATA_DIR = PAPERS_DIR / "data"
OUT_DIR = DATA_DIR / "nd-viewer-output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CYCLE3_ARCHIVE_JSON = DATA_DIR / "repo-refs-skill-cycle-3-archive-2026-08-07.json"

PRIMITIVES_7 = [
    "has_problem_statement", "has_recommendation", "has_evidence",
    "has_cross_reference", "has_verification_plan", "has_source_citation",
    "has_priority_signal",
]
SIZE_AXES = ["size_lt3k", "size_3to6k", "size_6to12k", "size_12to25k", "size_ge25k"]
META_AXES = ["t", "residual"]
ALL_AXES = PRIMITIVES_7 + SIZE_AXES + META_AXES
N_DIM = len(ALL_AXES)  # 14

SIZE_BUCKETS = [
    (0, 3000, "size_lt3k"),
    (3000, 6000, "size_3to6k"),
    (6000, 12000, "size_6to12k"),
    (12000, 25000, "size_12to25k"),
    (25000, float("inf"), "size_ge25k"),
]


def size_bucket(size):
    for lo, hi, name in SIZE_BUCKETS:
        if lo <= size < hi:
            return name
    return "size_ge25k"


def pca_topk(M, k=2):
    mu = M.mean(axis=0)
    Mc = M - mu
    U, S, Vt = svd(Mc, full_matrices=False)
    Wk = Vt[:k].T
    return Wk, mu, (S[:k] ** 2) / (S ** 2).sum() if (S ** 2).sum() > 0 else np.zeros(k)


def stereographic(uv):
    u, v = uv[..., 0], uv[..., 1]
    d = u * u + v * v + 1.0
    return np.stack([2 * u / d, 2 * v / d, (u * u + v * v - 1.0) / d], axis=-1)


def real_sh(ell, m, theta, phi):
    norm = np.sqrt((2 * ell + 1) / (4 * np.pi) * factorial(ell - abs(m)) / factorial(ell + abs(m)))
    x = np.cos(theta)
    P_lm = lpmv(abs(m), ell, x)
    if m == 0:
        return norm * P_lm
    if m > 0:
        return np.sqrt(2.0) * norm * P_lm * np.cos(m * phi)
    return np.sqrt(2.0) * norm * P_lm * np.sin(abs(m) * phi)


def design_matrix(theta, phi, L=3):
    basis = []
    for ell in range(L + 1):
        for m in range(-ell, ell + 1):
            basis.append(real_sh(ell, m, theta, phi))
    return np.stack(basis, axis=-1)


def fit_curve(p, t, L=3, ridge=1e-3):
    Phi = design_matrix(np.pi * t, 2 * np.pi * t, L=L)
    PtP = Phi.T @ Phi + ridge * np.eye(Phi.shape[1])
    return np.linalg.solve(PtP, Phi.T @ p)


def evaluate_curve(C, t, L=3):
    Phi = design_matrix(np.pi * t, 2 * np.pi * t, L=L)
    p_hat = Phi @ C
    n = np.linalg.norm(p_hat, axis=-1, keepdims=True)
    return p_hat / np.where(n < 1e-12, 1.0, n)


def coord_t(M, W1):
    raw = M @ W1
    if raw.max() - raw.min() < 1e-12:
        return np.zeros_like(raw)
    return (raw - raw.min()) / (raw.max() - raw.min())


def build_X(items):
    cov = np.array([[it["coverage"][p] for p in PRIMITIVES_7] for it in items], dtype=np.float64)
    W2, mu, _ = pca_topk(cov, k=2)
    Mc = cov - mu
    p = stereographic(Mc @ W2)
    t = coord_t(cov, W2[:, 0])
    C = fit_curve(p, t, L=3, ridge=1e-3)
    p_hat = evaluate_curve(C, t, L=3)
    residual = np.linalg.norm(p - p_hat, axis=-1)

    meta, rows = [], []
    for i, it in enumerate(items):
        size_onehot = [1.0 if size_bucket(it["size"]) == k else 0.0 for k in SIZE_AXES]
        vec = list(cov[i]) + size_onehot + [float(t[i]), float(residual[i])]
        assert len(vec) == N_DIM, f"vec len {len(vec)} != {N_DIM}"
        rows.append(vec)
        meta.append({
            "slug": it["name"], "sha": it["sha"], "size": it["size"],
            "size_bucket": size_bucket(it["size"]),
            "missing": [p for p in PRIMITIVES_7 if not it["coverage"][p]],
            "t": float(t[i]), "residual": float(residual[i]),
        })
    X = np.asarray(rows, dtype=np.float64)
    return meta, X


def write_vectors_json(meta, pcs, X, out_path):
    out = {}
    for i, m in enumerate(meta):
        out[m["slug"]] = {
            "axes": {ALL_AXES[j]: float(X[i, j]) for j in range(N_DIM)},
            "pca": [float(pcs[i, 0]), float(pcs[i, 1])],
            "sha": m["sha"], "size": m["size"], "size_bucket": m["size_bucket"],
            "missing_primitives": m["missing"], "t": m["t"], "residual": m["residual"],
        }
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"  saved {out_path} ({len(out)} rows, {out_path.stat().st_size} bytes)")


def write_correlation_csv(X, out_path):
    C = np.corrcoef(X.T)
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["axis"] + ALL_AXES)
        for i, name in enumerate(ALL_AXES):
            w.writerow([name] + [f"{C[i, j]:+.4f}" for j in range(N_DIM)])
    print(f"  saved {out_path} ({out_path.stat().st_size} bytes)")


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
        f_title = f_label = f_sub = ImageFont.load_default()

    margin_l, margin_r, margin_t, margin_b = 100, 60, 90, 80
    plot_w, plot_h = W - margin_l - margin_r, H - margin_t - margin_b
    d.text((W / 2, 20), "N-D axis viewer — cycle-3 repo-refs corpus",
           fill="#1a3a5c", font=f_title, anchor="mt")
    d.text((W / 2, 50),
           f"{N_DIM}-D vectors (7 primitives + 5 size-bucket onehot + t/residual) → PCA "
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
        v = x_min + i / 6 * (x_max - x_min); x = to_x(v)
        d.line([(x, margin_t + plot_h), (x, margin_t + plot_h + 4)], fill="#444444")
        d.text((x, margin_t + plot_h + 8), f"{v:+.2f}", fill="#444444", font=f_label, anchor="mt")
        v2 = y_min + i / 6 * (y_max - y_min); y = to_y(v2)
        d.line([(margin_l - 4, y), (margin_l, y)], fill="#444444")
        d.text((margin_l - 8, y), f"{v2:+.2f}", fill="#444444", font=f_label, anchor="rm")
    d.text((W / 2, H - margin_b + 35), f"PC1 ({var_explained[0]:.1%})", fill="#1a3a5c", font=f_sub, anchor="mt")
    d.text((30, H / 2), f"PC2 ({var_explained[1]:.1%})", fill="#1a3a5c", font=f_sub, anchor="mm")

    bucket_colors = {"size_lt3k": "#5a8ec7", "size_3to6k": "#7ab07a", "size_6to12k": "#c7a85a",
                     "size_12to25k": "#c75a5a", "size_ge25k": "#9933cc"}
    for i, m in enumerate(meta):
        x, y = to_x(xs[i]), to_y(ys[i])
        c = bucket_colors.get(m["size_bucket"], "#888888")
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=c)
        if m["residual"] > 0.5 and i % 7 == 0:
            short = m["slug"][:20]
            d.text((x + 5, y - 5), f"{short} r{m['residual']:.2f}", fill=c, font=f_label, anchor="lm")

    leg_x, leg_y = margin_l, margin_t - 20
    for k, col in bucket_colors.items():
        d.ellipse([leg_x - 5, leg_y - 5, leg_x + 5, leg_y + 5], fill=col)
        d.text((leg_x + 8, leg_y), k.replace("size_", ""), fill="#444444", font=f_label, anchor="lm")
        leg_x += 110

    img.save(out_path, "PNG", dpi=(150, 150))
    print(f"  saved {out_path} ({out_path.stat().st_size} bytes)")


def write_html_viewer(meta, pcs, X, var_explained, out_path):
    if go is None:
        print("  WARN: plotly not available; skipping HTML viewer")
        return
    bucket_vals = [m["size_bucket"] for m in meta]
    bucket_codes = {k: i for i, k in enumerate(SIZE_AXES)}
    color_vals = [bucket_codes.get(b, 5) for b in bucket_vals]
    labels = [f"{m['slug']} r={m['residual']:.3f}" for m in meta]
    items = [{
        "slug": m["slug"], "size_bucket": m["size_bucket"],
        "axes": {ALL_AXES[j]: float(X[i, j]) for j in range(N_DIM)},
        "pca": [float(pcs[i, 0]), float(pcs[i, 1])],
        "missing": m["missing"], "residual": m["residual"],
    } for i, m in enumerate(meta)]

    axis_meta = []
    for j, name in enumerate(ALL_AXES):
        col = X[:, j]
        is_bool = name in PRIMITIVES_7 + SIZE_AXES
        axis_meta.append({"name": name, "min": float(col.min()), "max": float(col.max()),
                          "median": float(np.median(col)), "is_bool": is_bool})

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=pcs[:, 0].tolist(), y=pcs[:, 1].tolist(), mode="markers",
        marker=dict(size=8, color=color_vals, colorscale="Viridis", showscale=True,
                    colorbar=dict(title="size bucket")),
        text=labels,
        hovertemplate="<b>%{text}</b><br>PC1=%{x:.3f} PC2=%{y:.3f}<extra></extra>",
        name="items",
    ))
    fig.update_layout(
        title=f"N-D axis viewer — cycle-3 repo-refs ({N_DIM}-D → PC1 {var_explained[0]:.1%}, PC2 {var_explained[1]:.1%})",
        xaxis_title=f"PC1 ({var_explained[0]:.1%})",
        yaxis_title=f"PC2 ({var_explained[1]:.1%})",
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
                f'<span class="hint">≥ threshold</span></div>')
    rows_html = "\n".join(slider_rows)
    items_json = json.dumps(items)
    axes_json = json.dumps(axis_meta)

    html = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<title>N-D axis viewer — cycle-3 repo-refs corpus</title>
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
<h1>N-D axis viewer — cycle-3 repo-refs corpus (130 items)</h1>
<div class="sub">{N_DIM}-D vectors (7 primitives + 5 size-bucket onehot + t/residual = {N_DIM} sliders). Each slider sets a minimum threshold; the scatter filters items with axis ≥ threshold.</div>
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
    if (am.is_bool) {{ thresholds[am.name] = el.checked ? 1 : 0; }}
    else {{
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
    bucket_count = {}
    for m in meta:
        bucket_count[m["size_bucket"]] = bucket_count.get(m["size_bucket"], 0) + 1
    prim_lines = "\n".join(f"- `{p}` — 1 if the item's text matches the primitive's detection pattern, else 0."
                            for p in PRIMITIVES_7)
    bucket_lines = "\n".join(f"- `{k}` — 1 if the item's size is in `{k.replace('size_', '').replace('lt', '<').replace('to', '-').replace('ge', '≥')} bytes`, else 0."
                              for k in SIZE_AXES)

    md = f"""# N-D axis viewer — cycle-3 repo-refs corpus feature space

Generated by `render-cycle-3-refs-nd-viewer.py` on **{datetime.now(timezone.utc).isoformat()}**.

## Why this exists here, and how it differs from the 24-D skill-corpus viewer

`nd-viewer-output/` is normally owned by `build-nd-axis-viewer.py`, which builds a **24-D** vector
(9 internal-big-picture primitives + 12 negative-skill-space axes scored from SKILL.md text + 3
run-metadata fields) for the **79-skill corpus**.

The repo-refs-skill's 130-item corpus (refs/*.md markdown docs in yubi-OS/yubiOS) has no SKILL.md
text and no per-cycle RSI metadata — the 12 NSS axes and the (cycle#, delta, FIRES) triple don't
apply to a markdown file. Rather than force an inapplicable basis onto this corpus, this script
builds a domain-appropriate **{N_DIM}-D** vector instead:

1. **7 repo-refs primitives** (binary, same basis as `curve-map-output/`'s cycle-3 render):
   has_problem_statement, has_recommendation, has_evidence, has_cross_reference,
   has_verification_plan, has_source_citation, has_priority_signal.
2. **5 size-bucket onehot axes** — the repo-refs analog of a categorical field. There is no natural
   NSS-style multi-axis breakdown for markdown docs (no PR vs commit vs Linear ticket here), so
   doc-size is the most informative categorical signal available.
3. **2 run-metadata fields** — `t` (PC1 coordinate of the 7-D coverage) and `residual` (chordal
   distance to the fitted γ(t) curve) — the analog of (cycle#, delta) in the skill-corpus viewer.

## Axis list

### 7 repo-refs primitives (same as curve-map-output/'s cycle-3 render)

{prim_lines}

### 5 size-bucket onehot axes

{bucket_lines}

### 2 run-metadata fields

- `t` — PC1 coordinate of the centered 7-D coverage matrix, min-max scaled to [0,1].
- `residual` — chordal S² distance to the fitted spherical-harmonic curve γ(t).

## Stats

- Corpus: **{n} items** (130 refs/*.md, yubi-OS/yubiOS)
- PCA explained variance: **PC1 {var_explained[0]:.1%}, PC2 {var_explained[1]:.1%}** (sum {sum(var_explained):.1%})
- Size-bucket breakdown: {bucket_count}
- Source archive: `papers/data/repo-refs-skill-cycle-3-archive-2026-08-07.json`

## Outputs (in `papers/data/nd-viewer-output/`, cycle-3-refs-prefixed)

| File | Description |
|---|---|
| `nd-vectors-cycle-3-refs-2026-08-07.json` | Every item's {N_DIM}-D axis values + 2D PCA coords |
| `nd-pca-static-cycle-3-refs-2026-08-07.png` | Labeled static PCA scatter, color = size bucket |
| `nd-viewer-cycle-3-refs-2026-08-07.html` | Interactive Plotly scatter, {N_DIM} sliders |
| `nd-axis-correlation-cycle-3-refs-2026-08-07.csv` | Pairwise correlation across all {N_DIM} axes |
| `README-cycle-3-refs-2026-08-07.md` | This file |

## How to regenerate

```bash
python3.12 papers/scripts/render-cycle-3-refs-nd-viewer.py
```

Requires the cached archive at `papers/data/repo-refs-skill-cycle-3-archive-2026-08-07.json`. No
live API calls — pure re-render.

## Deviation from the spec (honestly flagged)

This is NOT a drop-in extension of the existing 24-D viewer's corpus — it's a **parallel, smaller
viewer for a different corpus with a different, domain-fit basis** ({N_DIM}-D vs 24-D). Merging the
two would require inventing NSS-axis scores for markdown docs, which has no principled basis. If a
true unified viewer across both corpora is wanted later, the right approach is a shared projection
of the primitive-coverage signal only (the one axis both bases share conceptually), not a literal
24-D ⊕ {N_DIM}-D stack.
"""
    out_path.write_text(md, encoding="utf-8")
    print(f"  saved {outme_path if False else out_path} ({out_path.stat().st_size} bytes)")


def main():
    print("=== CYCLE-3 REPO-REFS N-D VIEWER → nd-viewer-output/ ===")
    print(f"Date: {datetime.now(timezone.utc).isoformat()}")
    if not CYCLE3_ARCHIVE_JSON.exists():
        print(f"FATAL: {CYCLE3_ARCHIVE_JSON} not found", file=sys.stderr)
        sys.exit(1)

    with open(CYCLE3_ARCHIVE_JSON) as f:
        archive = json.load(f)
    items = archive["corpus"]
    print(f"[1/3] Loaded {len(items)} items from cache")

    meta, X = build_X(items)
    sigma = X.std(axis=0); sigma[sigma == 0] = 1.0
    Xz = (X - X.mean(axis=0)) / sigma
    mu = Xz.mean(axis=0)
    _, S, Vt = np.linalg.svd(Xz - mu, full_matrices=False)
    pcs = Xz @ Vt[:2].T
    var_explained_full = (S[:2] ** 2) / (S ** 2).sum()
    var_explained = var_explained_full.tolist() if hasattr(var_explained_full, "tolist") else list(var_explained_full)
    print(f"[2/3] Built {X.shape} matrix, PCA PC1={var_explained[0]:.4f} PC2={var_explained[1]:.4f}")

    print("[3/3] Writing outputs...")
    write_vectors_json(meta, pcs, X, OUT_DIR / "nd-vectors-cycle-3-refs-2026-08-07.json")
    write_correlation_csv(X, OUT_DIR / "nd-axis-correlation-cycle-3-refs-2026-08-07.csv")
    write_static_png(meta, pcs, var_explained, OUT_DIR / "nd-pca-static-cycle-3-refs-2026-08-07.png")
    write_html_viewer(meta, pcs, X, var_explained, OUT_DIR / "nd-viewer-cycle-3-refs-2026-08-07.html")
    write_readme(meta, var_explained, archive, OUT_DIR / "README-cycle-3-refs-2026-08-07.md")
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
