"""Build the N-D axis viewer artifact (PR3 of 4-PR hypersphere RSI series).

Stacks the 9-D internal-big-picture primitive basis + 12 NSS axes + 3 run-metadata
fields (cycle#, delta, FIRES) into one 24-D feature vector per (skill, cycle)
corpus row, PCA-projects to 2D, and emits:

  - nd-vectors.json   : {file-key: {axes: {name:value}, pca: [x,y], cycle, delta, FIRES}}
  - nd-pca-static.png : labeled scatter of all items in PCA space
  - nd-viewer.html    : interactive viewer, one slider per axis (live threshold)
  - nd-axis-correlation.csv : pairwise correlation matrix across all N axes
  - README.md         : what this is, how to regenerate, axis list, how the viewer works

Corpus source: yubi-OS/yubiOS papers/data/rsi-79-corpus-multi-cycle-2026-08-06.json
(via GitHub API, domain api.github.com).

Run end-to-end with: python3 papers/scripts/build-nd-axis-viewer.py
"""
from __future__ import annotations
import csv
import io
import json
import math
import os
import re
import sys
import urllib.request
from pathlib import Path
import numpy as np

try:
    import plotly.graph_objects as go
except ImportError:
    go = None

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None

# ---------- Paths ----------
REPO_ROOT = Path("/var/workspace")
GITHUB_YUB = REPO_ROOT / "documents/github-yubios-KS9n5GAT"
SKILL_DIRS = [
    REPO_ROOT / "skills/github-yubios-KS9n5GAT",
    REPO_ROOT / "skills/personal-WbtUgeUv",
]
OUT_DIR = GITHUB_YUB / "papers/data/nd-viewer-output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------- Basis definitions ----------
PRIMITIVES_9 = [
    "attestation", "audit_evidence", "continuous_adaptive",
    "cryptographic_identity", "declarative_policy", "immutability",
    "least_privilege", "segmentation", "trust_chain",
]
NSS_AXES_12 = [
    "audience", "inputs", "outputs", "mode", "assumption_set",
    "adjacent_problems", "failure_modes", "lifecycle", "composition",
    "knowledge_sources", "calibration", "recursion",
]
ALL_AXES = PRIMITIVES_9 + NSS_AXES_12 + ["cycle", "delta", "FIRES"]
N_DIM = 24  # 9 + 12 + 3 (cycle#, delta, FIRES)

# ---------- NSS axis scoring ----------
# Each axis is scored from SKILL.md text by looking for canonical section/keyword patterns.
# Scores are 0..1 floats (presence + frequency, clipped at 1).
NSS_AXIS_PATTERNS = {
    "audience": [r"\bAudience\b", r"\bWho is this for\b", r"\bintended user\b",
                 r"\bTarget audience\b", r"\boperator\b", r"\bdev\b"],
    "inputs": [r"\b## Inputs?\b", r"\b### Inputs?\b", r"\bInput\b.*\bcontext\b",
               r"\bpreconditions?\b"],
    "outputs": [r"\b## Outputs?\b", r"\b### Outputs?\b", r"\bdeliverables?\b",
                r"\bOutput Contract\b"],
    "mode": [r"\b## When to use\b", r"\b## When NOT to use\b", r"\b## Mode\b",
             r"\b## Calibration gate\b"],
    "assumption_set": [r"\b## Assumptions?\b", r"\b## Key Assumptions\b",
                       r"\b## Pre-conditions?\b"],
    "adjacent_problems": [r"\b## Adjacent\b", r"\b## Related\b", r"\b## Related Work\b",
                          r"\b## Composition Rule\b"],
    "failure_modes": [r"\b## Failure modes?\b", r"\b## Red Flags?\b",
                      r"\b## Anti-patterns?\b", r"\b## Risks?\b"],
    "lifecycle": [r"\b## Lifecycle\b", r"\b## Re-fit cadence\b",
                  r"\b## Versioning\b", r"\b## Cadence\b"],
    "composition": [r"\b## Composition\b", r"\b## Interaction with\b",
                    r"\b## Loading order\b", r"\b## Composition Rule\b"],
    "knowledge_sources": [r"\b## Sources?\b", r"\b## References?\b",
                          r"\b## Knowledge sources\b"],
    "calibration": [r"\b## Verification\b", r"\b## Calibration\b",
                    r"\b## Pre-Fit Validation\b", r"\b## Output Contract\b"],
    "recursion": [r"\b## Recursion\b", r"\b## Self-referential\b",
                  r"\b## RSI\b", r"\bself-archaeology\b"],
}


def load_skill_text(slug: str) -> str:
    """Load SKILL.md text from either github-yubios or personal skill directories."""
    for base in SKILL_DIRS:
        p = base / slug / "SKILL.md"
        if p.exists():
            return p.read_text(encoding="utf-8", errors="ignore")
    return ""


def score_nss_axes(text: str) -> dict:
    """Compute a 0..1 score per NSS axis from SKILL.md text."""
    out = {}
    if not text:
        # Fall back to slug-derived structural proxies (in case SKILL.md is missing).
        return out
    text_lower = text.lower()
    for axis, patterns in NSS_AXIS_PATTERNS.items():
        hits = 0
        for pat in patterns:
            hits += len(re.findall(pat, text, flags=re.IGNORECASE))
        # normalize: 1 hit -> 0.4, 2 -> 0.6, 3 -> 0.8, 4+ -> 1.0
        if hits == 0:
            out[axis] = 0.0
        elif hits == 1:
            out[axis] = 0.4
        elif hits == 2:
            out[axis] = 0.6
        elif hits == 3:
            out[axis] = 0.8
        else:
            out[axis] = 1.0
    return out


def slug_proxy_axes(slug: str) -> dict:
    """Slug-derived fallback when SKILL.md is missing."""
    parts = slug.replace('_', '-').split('-')
    n = len(parts)
    out = {}
    for axis in NSS_AXES_12:
        # proxy: longer slug => more compositional surface
        out[axis] = min(1.0, n / 8.0)
    return out


# ---------- Corpus loading ----------
CORPUS_LOCAL = REPO_ROOT / "session/cache/rsi-79-corpus.json"


def load_corpus_from_api():
    """Fetch corpus file via GitHub API (api.github.com domain)."""
    url = "https://api.github.com/repos/yubi-OS/yubiOS/contents/papers/data/rsi-79-corpus-multi-cycle-2026-08-06.json"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github.raw",
        "User-Agent": "sauna-pr3-nd-viewer-builder",
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
    return json.loads(raw)


def load_corpus():
    """Load corpus from local cache if present, else fetch via API and cache it."""
    if CORPUS_LOCAL.exists() and CORPUS_LOCAL.stat().st_size > 10000:
        print(f"[io] using cached corpus at {CORPUS_LOCAL}")
        return json.loads(CORPUS_LOCAL.read_text())
    print("[io] fetching corpus via GitHub API...")
    data = load_corpus_from_api()
    CORPUS_LOCAL.parent.mkdir(parents=True, exist_ok=True)
    CORPUS_LOCAL.write_text(json.dumps(data))
    return data


# ---------- Vector construction ----------
def build_meta_and_X(corpus):
    """Build per-row meta + 24-D feature matrix X."""
    all_cycles = corpus["all_cycles"]
    primitives_set = set(corpus["primitives"])
    assert primitives_set == set(PRIMITIVES_9), f"primitives mismatch: {primitives_set ^ set(PRIMITIVES_9)}"

    # Cache SKILL.md scores per slug (avoid re-loading).
    skill_text_cache = {}
    skill_axes_cache = {}

    meta = []
    rows = []
    for entry in all_cycles:
        slug = entry["slug"]
        cycle = entry["cycle"]
        d_pre = float(entry.get("d_pre", 0.0))
        d_post = float(entry.get("d_post", 0.0))
        delta_d = float(entry.get("delta_d", 0.0))
        missing = set(entry.get("missing_primitives") or [])
        fires = bool(delta_d > 0)

        # 9 primitives: present = not in missing
        primitive_vec = [0.0 if p in missing else 1.0 for p in PRIMITIVES_9]

        # 12 NSS axes: load SKILL.md once per slug
        if slug not in skill_axes_cache:
            text = load_skill_text(slug)
            scored = score_nss_axes(text)
            if not scored:
                scored = slug_proxy_axes(slug)
            skill_axes_cache[slug] = scored
        nss_vec = [float(skill_axes_cache[slug].get(axis, 0.0)) for axis in NSS_AXES_12]

        # 3 run metadata
        run_vec = [float(cycle), float(delta_d), 1.0 if fires else 0.0]

        vec = primitive_vec + nss_vec + run_vec
        assert len(vec) == N_DIM, f"vec len {len(vec)} != {N_DIM}"

        meta.append({
            "slug": slug, "cycle": cycle,
            "d_pre": d_pre, "d_post": d_post, "delta_d": delta_d,
            "FIRES": fires, "missing": sorted(missing),
        })
        rows.append(vec)

    X = np.asarray(rows, dtype=np.float64)
    # standardize each axis for PCA (zero-mean, unit-var)
    mu = X.mean(axis=0)
    sigma = X.std(axis=0)
    sigma[sigma == 0] = 1.0  # avoid div by zero on constant axes
    Xz = (X - mu) / sigma
    return meta, X, Xz, mu, sigma, skill_axes_cache


def pca_2d(Xz):
    """PCA to 2D using SVD on the standardized matrix."""
    U, S, Vt = np.linalg.svd(Xz, full_matrices=False)
    pcs = Xz @ Vt[:2].T
    var_explained = (S ** 2) / (S ** 2).sum()
    return pcs, var_explained[:2].tolist()


# ---------- Output writers ----------
def write_vectors_json(meta, pcs, X, out_path):
    out = {}
    for i, m in enumerate(meta):
        key = f"{m['slug']}__c{m['cycle']}"
        axes = {ALL_AXES[j]: float(X[i, j]) for j in range(N_DIM)}
        out[key] = {
            "axes": axes,
            "pca": [float(pcs[i, 0]), float(pcs[i, 1])],
            "cycle": int(m['cycle']),
            "delta": float(m['delta_d']),
            "FIRES": bool(m['FIRES']),
            "d_pre": float(m['d_pre']),
            "d_post": float(m['d_post']),
            "missing_primitives": m['missing'],
        }
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2)
    print(f"[io] wrote {out_path} ({len(out)} rows)")


def write_correlation_csv(X, out_path):
    # Pearson correlation on the raw (un-standardized) axes.
    C = np.corrcoef(X.T)
    with open(out_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(["axis"] + ALL_AXES)
        for i, name in enumerate(ALL_AXES):
            row = [name] + [f"{C[i, j]:+.4f}" for j in range(N_DIM)]
            w.writerow(row)
    print(f"[io] wrote {out_path}")


def write_static_png(meta, pcs, var_explained, out_path):
    if Image is None:
        print("[warn] PIL not available; skipping static PNG")
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
    plot_w = W - margin_l - margin_r
    plot_h = H - margin_t - margin_b

    d.text((W / 2, 20), "N-D axis viewer — static PCA scatter", fill="#1a3a5c", font=f_title, anchor="mt")
    d.text((W / 2, 50),
           f"24-D vectors (9 primitives + 12 NSS axes + cycle/delta/FIRES) projected to 2D via PCA "
           f"(PC1 {var_explained[0]:.1%} / PC2 {var_explained[1]:.1%})",
           fill="#666666", font=f_sub, anchor="mt")

    xs = pcs[:, 0]
    ys = pcs[:, 1]
    x_min, x_max = float(xs.min()), float(xs.max())
    y_min, y_max = float(ys.min()), float(ys.max())
    # pad
    xr = x_max - x_min if x_max > x_min else 1.0
    yr = y_max - y_min if y_max > y_min else 1.0
    x_min -= xr * 0.05; x_max += xr * 0.05
    y_min -= yr * 0.05; y_max += yr * 0.05

    def to_x(v): return margin_l + (v - x_min) / (x_max - x_min) * plot_w
    def to_y(v): return (margin_t + plot_h) - (v - y_min) / (y_max - y_min) * plot_h

    # axes
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

    # points, color-coded by cycle
    cycle_colors = {1: "#5a8ec7", 2: "#c75a5a", 3: "#228b22", 4: "#cc6633",
                    5: "#9933cc", 6: "#1a3a5c"}
    for i, m in enumerate(meta):
        x = to_x(xs[i]); y = to_y(ys[i])
        c = cycle_colors.get(m['cycle'], "#888888")
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=c)
        # label FIRES points; skip label for dense overlap
        if m['FIRES'] and i % 7 == 0:
            short = m['slug'][:18]
            d.text((x + 5, y - 5), f"c{m['cycle']}·{short} Δ{m['delta_d']:+.2f}",
                   fill=c, font=f_label, anchor="lm")

    # legend
    leg_x = margin_l; leg_y = margin_t - 20
    for cyc, col in cycle_colors.items():
        d.ellipse([leg_x - 5, leg_y - 5, leg_x + 5, leg_y + 5], fill=col)
        d.text((leg_x + 8, leg_y), f"cycle {cyc}", fill="#444444", font=f_label, anchor="lm")
        leg_x += 100

    img.save(out_path, "PNG", dpi=(150, 150))
    print(f"[io] wrote {out_path} ({out_path.stat().st_size} bytes)")


def write_html_viewer(meta, pcs, X, var_explained, out_path):
    if go is None:
        print("[warn] plotly not available; skipping HTML viewer")
        return
    n = len(meta)
    # build marker arrays per item
    cycle_vals = [int(m['cycle']) for m in meta]
    delta_vals = [float(m['delta_d']) for m in meta]
    fires_vals = [bool(m['FIRES']) for m in meta]
    slugs = [m['slug'] for m in meta]
    labels = [f"c{m['cycle']}·{m['slug']} Δ{m['delta_d']:+.3f} {'FIRES' if m['FIRES'] else 'no-fire'}" for m in meta]

    # Build the slider-panel HTML as a JSON blob for client-side filtering.
    items = [{
        "slug": m['slug'], "cycle": int(m['cycle']),
        "delta": float(m['delta_d']), "fires": bool(m['FIRES']),
        "axes": {ALL_AXES[j]: float(X[i, j]) for j in range(N_DIM)},
        "pca": [float(pcs[i, 0]), float(pcs[i, 1])],
        "missing": m['missing'],
    } for i, m in enumerate(meta)]

    axis_meta = []
    for j, name in enumerate(ALL_AXES):
        col = X[:, j]
        axis_meta.append({"name": name, "min": float(col.min()), "max": float(col.max()),
                          "median": float(np.median(col)), "is_bool": name == "FIRES"})

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=pcs[:, 0].tolist(),
        y=pcs[:, 1].tolist(),
        mode='markers',
        marker=dict(size=8, color=cycle_vals, colorscale='Viridis', showscale=True,
                    colorbar=dict(title="cycle")),
        text=labels,
        customdata=np.stack([cycle_vals, delta_vals, fires_vals], axis=1),
        hovertemplate="<b>%{text}</b><br>PC1=%{x:.3f} PC2=%{y:.3f}<extra></extra>",
        name="items",
    ))
    fig.update_layout(
        title=f"N-D axis viewer — 24-D vectors PCA-projected (PC1 {var_explained[0]:.1%}, PC2 {var_explained[1]:.1%})",
        xaxis_title=f"PC1 ({var_explained[0]:.1%})",
        yaxis_title=f"PC2 ({var_explained[1]:.1%})",
        width=1100, height=720,
        margin=dict(l=60, r=40, t=80, b=60),
    )

    # Use plotly's to_html to embed the chart, then inject our custom slider panel.
    chart_html = fig.to_html(include_plotlyjs='cdn', full_html=False, div_id="nd-plot")
    slider_rows = []
    for am in axis_meta:
        if am['is_bool']:
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
<title>N-D axis viewer — 24-D RSI corpus</title>
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
<h1>N-D axis viewer — 24-D RSI corpus feature space</h1>
<div class="sub">9 primitives + 12 NSS axes + cycle#/delta/FIRES = 24 sliders. Each slider sets a minimum threshold; the scatter filters items with axis ≥ threshold. FIRES is a checkbox (true = show fired items only).</div>
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
  let firesChecked = true;
  for (const am of axesMeta) {{
    if (am.is_bool) {{
      const el = document.getElementById('ax-' + am.name);
      firesChecked = el.checked;
    }} else {{
      const el = document.getElementById('ax-' + am.name);
      thresholds[am.name] = parseFloat(el.value);
      const valEl = document.getElementById('val-' + am.name);
      if (valEl) valEl.textContent = el.value;
    }}
  }}
  const filtered = items.filter(it => {{
    if (am_name => false) {{}}
    if (firesChecked && !it.fires) return false;
    for (const [name, thr] of Object.entries(thresholds)) {{
      if ((it.axes[name] ?? 0) < thr) return false;
    }}
    return true;
  }});
  const x = filtered.map(it => it.pca[0]);
  const y = filtered.map(it => it.pca[1]);
  const txt = filtered.map(it => `c${{it.cycle}}·${{it.slug}} Δ${{it.delta.toFixed(3)}} ${{it.fires ? 'FIRES' : 'no-fire'}}`);
  const cycles = filtered.map(it => it.cycle);
  const plotDiv = document.getElementById('nd-plot');
  Plotly.react(plotDiv, [{{
    x, y, text: txt, mode: 'markers', type: 'scatter',
    marker: {{ size: 9, color: cycles, colorscale: 'Viridis', showscale: true, colorbar: {{ title: 'cycle' }} }},
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

// initial render
applyFilters();
</script>
</body></html>
"""
    out_path.write_text(html, encoding='utf-8')
    print(f"[io] wrote {out_path} ({out_path.stat().st_size} bytes)")


def write_readme(meta, pcs, var_explained, skill_axes_cache, out_path):
    n = len(meta)
    n_fires = sum(1 for m in meta if m['FIRES'])
    fires_pct = 100.0 * n_fires / n if n else 0.0
    avg_delta = float(np.mean([m['delta_d'] for m in meta])) if meta else 0.0

    prim_lines = "\n".join(
        f"- `{p}` — 1 if the skill has this primitive at the given cycle, 0 if it was in `missing_primitives`."
        for p in PRIMITIVES_9
    )
    nss_lines = "\n".join(
        f"- `{a}` — 0..1 score from SKILL.md section-presence + keyword hit count "
        f"(1 hit→0.4, 2→0.6, 3→0.8, 4+→1.0; falls back to slug-length proxy when SKILL.md missing)."
        for a in NSS_AXES_12
    )

    readme = f"""# N-D axis viewer — 24-D RSI corpus feature space

**PR3 of 4-PR hypersphere RSI series** — built {Path(__file__).name}.

## What this is

For each row in `papers/data/rsi-79-corpus-multi-cycle-2026-08-06.json` (a corpus item
at a specific RSI cycle), we construct a **24-D feature vector** combining three bases:

1. **9 internal-big-picture primitives** (binary presence / missing-flag from the corpus)
2. **12 negative-skill-space axes** (scored 0..1 from each skill's SKILL.md text)
3. **3 run-metadata fields** (cycle#, geodesic delta, FIRES bool)

We PCA-project the standardized 24-D space to 2D, then expose:

- `nd-vectors.json` — every row's axis values + 2D PCA coordinates + cycle/delta/FIRES
- `nd-pca-static.png` — labeled scatter of all {n} items in PCA space
- `nd-viewer.html` — interactive Plotly scatter with **one slider per axis** (24 sliders)
- `nd-axis-correlation.csv` — pairwise Pearson correlation across all 24 axes
- this README

## Stats

- Corpus: **{n} items** ({len(skill_axes_cache)} unique skills × 6 cycles)
- FIRES count: **{n_fires} / {n}** ({fires_pct:.1f}%)
- Mean Δ across all items: **{avg_delta:+.4f}**
- PCA explained variance: **PC1 {var_explained[0]:.1%}, PC2 {var_explained[1]:.1%}** (sum {sum(var_explained):.1%})

## Axis list

### 9 internal-big-picture primitives

{prim_lines}

### 12 negative-skill-space axes

{nss_lines}

### 3 run-metadata fields

- `cycle` — the RSI cycle number (1..{max(m['cycle'] for m in meta)})
- `delta` — the geodesic-distance improvement `d_pre − d_post` for that row
- `FIRES` — bool, true iff `delta > 0` (the verification metric satisfied its gate for this item)

## How to regenerate

```bash
python3 papers/scripts/build-nd-axis-viewer.py
```

The script will:
1. Fetch the corpus via GitHub API (`papers/data/rsi-79-corpus-multi-cycle-2026-08-06.json`,
   domain `api.github.com`) — falls back to the local cache at `session/cache/rsi-79-corpus.json`.
2. Load each skill's `SKILL.md` text from `skills/github-yubios-KS9n5GAT/<slug>/SKILL.md`
   (or `skills/personal-WbtUgeUv/<slug>/SKILL.md`) for NSS-axis scoring.
3. Build the 24-D matrix, standardize, PCA → 2D.
4. Emit all five artifacts to `papers/data/nd-viewer-output/`.

## How the viewer works

Open `nd-viewer.html` in any browser (no server needed — Plotly loads from CDN).
Each of the 24 sliders sets a **minimum threshold** for its axis; items with `axis ≥ threshold`
remain on the scatter. Drag any slider to filter live. FIRES is a checkbox (checked = show
only fired items; uncheck to allow no-fire items). The status bar at the bottom of the panel
shows live `shown / total` counts.

**Controls:**
- **Reset to median** — set every threshold to the per-axis median
- **Show all (zeros)** — set every threshold to the per-axis min + uncheck FIRES (show everything)

## Deviations from the spec

- **N = 24, not 23.** The spec lists 9 primitives + 12 NSS axes + 3 run-metadata
  fields (cycle#, delta, FIRES) = **24 axes**, not 23. The spec text says "23 sliders"
  (e.g. "9 + 12 + cycle# + delta + FIRES = 23 sliders") — that arithmetic is off by one.
  We use **24** because that matches the math (24 sliders are emitted).
- **Primitive list:** The corpus primitives file lists 9 (attestation,
  audit_evidence, continuous_adaptive, cryptographic_identity, declarative_policy,
  immutability, least_privilege, segmentation, trust_chain) — exactly the 9 the
  spec calls for. The internal-big-picture skill text mentions a 10th
  (self-describing) but the corpus file is the source of truth for this artifact.
- **FIRES definition:** Bool, true iff `delta_d > 0`. (Verification metric fires
  iff geodesic distance improved for that item at that cycle.)
- **NSS axis scores** are derived from SKILL.md text patterns; scores are coarse
  (0..1 in 0.2 steps based on keyword/section hit count) but stable.
- **Vector granularity:** one vector per (skill, cycle) row = {n} rows
  ({len(skill_axes_cache)} skills × 6 cycles). Folding to one-per-skill would
  lose the per-cycle metadata the spec asks for.
"""
    out_path.write_text(readme, encoding='utf-8')
    print(f"[io] wrote {out_path} ({out_path.stat().st_size} bytes)")


# ---------- Main ----------
def main():
    print("=== Building N-D axis viewer (PR3) ===")
    corpus = load_corpus()
    print(f"[io] corpus: {len(corpus['all_cycles'])} rows across {len(corpus['primitives'])} primitives; "
          f"{corpus['corpus_size']} corpus_size, fixpoint_reached={corpus['fixpoint_reached']}")

    meta, X, Xz, mu, sigma, skill_axes_cache = build_meta_and_X(corpus)
    pcs, var_explained = pca_2d(Xz)
    print(f"[pca] PC1 var explained: {var_explained[0]:.4f}, PC2: {var_explained[1]:.4f}")

    write_vectors_json(meta, pcs, X, OUT_DIR / "nd-vectors.json")
    write_correlation_csv(X, OUT_DIR / "nd-axis-correlation.csv")
    write_static_png(meta, pcs, var_explained, OUT_DIR / "nd-pca-static.png")
    write_html_viewer(meta, pcs, X, var_explained, OUT_DIR / "nd-viewer.html")
    write_readme(meta, pcs, var_explained, skill_axes_cache, OUT_DIR / "README.md")

    print("=== Done ===")


if __name__ == "__main__":
    main()
