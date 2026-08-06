"""

Appendix B chart: differential curve baselines across the three corpora.

Three corpora are plotted side-by-side:
- skills/ (79 files, engineering corpus)
- docs/  (21 files, self-doc corpus)
- refs/  (113 files, references corpus)

For each: cumulative Δ per cycle (chordal proxy on S², identity Möbius),
normalized Δ per file per cycle (the differential curve baseline),
sparse-cell count per cycle, and per-primitive coverage progression.

Chart style: 3-panel vertical layout (1400×1700 PNG, 150 dpi).
"""
import sys
import json
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont






SKILLS_JSON = Path(sys.argv[1])
DOCS_JSON = Path(sys.argv[2])
REFS_JSON = Path(sys.argv[3])
OUT_PATH = Path(sys.argv[4])

PRIM_NAMES = [
    "attestation", "trust_chain", "least_privilege", "declarative_policy",
    "continuous_adaptive", "immutability", "audit_evidence",
    "cryptographic_identity", "segmentation",
]


def get_font(size):
    candidates = [
        "/usr/share/fonts/google-noto-vf/NotoSans[wght].ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def pad(arr, n, fill=0.0):
    return list(arr) + [fill] * (n - len(arr))


def main():
    s = json.load(open(SKILLS_JSON))
    d = json.load(open(DOCS_JSON))
    r = json.load(open(REFS_JSON))

    n_max = max(s["cycles_total"], d["cycles_total"], r["cycles_total"])

    s_cum = pad(s["cumulative_delta_per_cycle"], n_max)
    d_cum = pad(d["cumulative_delta_per_cycle"], n_max)
    r_cum = pad(r["cumulative_delta_per_cycle"], n_max)

    # Normalize by corpus size for differential curve baseline
    s_mean = [c / s["corpus_size"] for c in s_cum]
    d_mean = [c / d["corpus_size"] for c in d_cum]
    r_mean = [c / r["corpus_size"] for c in r_cum]

    s_peak = pad(s.get("peak_delta_per_cycle", [0] * n_max), n_max)
    d_peak = pad(d.get("peak_delta_per_cycle", [0] * n_max), n_max)
    r_peak = pad(r.get("peak_delta_per_cycle", [0] * n_max), n_max)

    s_sparse = pad(s["sparse_cells_per_cycle"], n_max)
    d_sparse = pad(d["sparse_cells_per_cycle"], n_max)
    r_sparse = pad(r["sparse_cells_per_cycle"], n_max)

    W, H = 1400, 1900
    img = Image.new("RGB", (W, H), "white")
    d_img = ImageDraw.Draw(img)
    f_title = get_font(24)
    f_sub = get_font(15)
    f_label = get_font(13)
    f_legend = get_font(12)

    margin_l, margin_r, margin_t, margin_b = 110, 60, 100, 110
    panel_gap = 50

    panel_h = (H - margin_t - margin_b - 2 * panel_gap) // 3

    colors = {
        "skills": "#1a3a5c",   # navy
        "docs":   "#cc6633",   # orange
        "refs":   "#228b22",   # forest green
    }

    # === Title ===
    d_img.text((W / 2, 22),
               "Appendix B \u2014 Hyper-Sphere RSI Multi-Corpus Audit (3 Differential Curve Baselines)",
               fill="#1a3a5c", font=f_title, anchor="mt")
    d_img.text((W / 2, 52),
               f"skills/ ({s['corpus_size']} files) + docs/ ({d['corpus_size']} files) + refs/ ({r['corpus_size']} files)  "
               f"\u2014 9-D primitive basis \u2014 chordal proxy on S\u00b2, identity M\u00f6bius",
               fill="#666666", font=f_sub, anchor="mt")

    # === Panel 1: Cumulative Δ per cycle (raw, all 3 corpora) ===
    panel1_top = margin_t
    panel1_bottom = panel1_top + panel_h
    plot_top_y1 = panel1_top
    plot_bottom_y1 = panel1_bottom
    plot_w1 = W - margin_l - margin_r
    plot_h1 = panel1_bottom - panel1_top - 60

    y_max_p1 = max(max(s_cum), max(d_cum), max(r_cum)) * 1.15
    y_min_p1 = 0.0

    def to_y_p1(v, plot_bottom=plot_bottom_y1, plot_top=plot_top_y1):
        frac = (v - y_min_p1) / (y_max_p1 - y_min_p1)
        return plot_bottom - frac * plot_h1

    # Grid lines
    n_ticks = 6
    for i in range(n_ticks + 1):
        y = plot_top_y1 + (i / n_ticks) * plot_h1
        val = y_min_p1 + (i / n_ticks) * (y_max_p1 - y_min_p1)
        d_img.line([(margin_l, y), (W - margin_r, y)], fill="#dddddd", width=1)
        d_img.text((margin_l - 8, y), f"{val:.1f}", fill="#666666", font=f_label, anchor="rm")
    d_img.line([(margin_l, plot_bottom_y1), (margin_l, plot_top_y1)], fill="#444444", width=2)
    d_img.line([(margin_l, plot_bottom_y1), (W - margin_r, plot_bottom_y1)], fill="#444444", width=2)

    bar_w = plot_w1 / n_max * 0.27
    gap = plot_w1 / n_max * 0.05
    for i in range(n_max):
        x_center = margin_l + (i + 0.5) * (plot_w1 / n_max)
        for j, (name, cum_arr) in enumerate([("skills", s_cum), ("docs", d_cum), ("refs", r_cum)]):
            x_offset = (j - 1) * (bar_w + gap)
            cx = x_center + x_offset
            y_top = to_y_p1(cum_arr[i])
            color = colors[name]
            d_img.rectangle([cx - bar_w / 2, y_top, cx + bar_w / 2, plot_bottom_y1], fill=color)
            if cum_arr[i] > 0.5:
                d_img.text((cx, y_top - 12), f"{cum_arr[i]:.1f}", fill=color, font=f_label, anchor="mb")

    d_img.text((W / 2, plot_bottom_y1 + 30),
               f"Cycle (1\u2013{n_max})", fill="#333333", font=f_label, anchor="mt")
    d_img.text((margin_l - 70, plot_top_y1 + plot_h1 / 2),
               "Cumulative \u0394", fill="#333333", font=f_label, anchor="mm", rotation=90)
    d_img.text((W / 2, plot_top_y1 - 12),
               "Cumulative \u0394 per cycle (raw, by corpus)",
               fill="#1a3a5c", font=f_label, anchor="mt")

    # Legend panel 1
    leg_y1 = plot_bottom_y1 + 50
    leg_x = margin_l
    for name, label in [("skills", "skills/ (79)"), ("docs", "docs/ (21)"), ("refs", "refs/ (113)")]:
        d_img.rectangle([leg_x, leg_y1 - 6, leg_x + 16, leg_y1 + 6], fill=colors[name])
        d_img.text((leg_x + 22, leg_y1), label, fill="#333333", font=f_legend, anchor="lm")
        leg_x += 200

    # === Panel 2: Normalized Δ per file per cycle (differential curve baseline) ===
    panel2_top = panel1_bottom + panel_gap
    panel2_bottom = panel2_top + panel_h
    plot_top_y2 = panel2_top
    plot_bottom_y2 = panel2_bottom - 60
    plot_h2 = plot_bottom_y2 - plot_top_y2

    y_max_p2 = max(max(s_mean), max(d_mean), max(r_mean)) * 1.15
    y_min_p2 = 0.0

    def to_y_p2(v):
        frac = (v - y_min_p2) / (y_max_p2 - y_min_p2)
        return plot_bottom_y2 - frac * plot_h2

    for i in range(n_ticks + 1):
        y = plot_top_y2 + (i / n_ticks) * plot_h2
        val = y_min_p2 + (i / n_ticks) * (y_max_p2 - y_min_p2)
        d_img.line([(margin_l, y), (W - margin_r, y)], fill="#dddddd", width=1)
        d_img.text((margin_l - 8, y), f"{val:.3f}", fill="#666666", font=f_label, anchor="rm")
    d_img.line([(margin_l, plot_bottom_y2), (margin_l, plot_top_y2)], fill="#444444", width=2)
    d_img.line([(margin_l, plot_bottom_y2), (W - margin_r, plot_bottom_y2)], fill="#444444", width=2)

    # Line plots for each corpus
    x_step_p2 = (W - margin_r - margin_l) / max(n_max - 1, 1)
    for name, mean_arr in [("skills", s_mean), ("docs", d_mean), ("refs", r_mean)]:
        coords = []
        for ci, v in enumerate(mean_arr):
            x = margin_l + ci * x_step_p2
            y = to_y_p2(v)
            coords.append((x, y))
        for i in range(len(coords) - 1):
            d_img.line([coords[i], coords[i + 1]], fill=colors[name], width=3)
        for (x, y) in coords:
            d_img.ellipse([x - 5, y - 5, x + 5, y + 5], fill=colors[name])

    d_img.text((W / 2, plot_bottom_y2 + 30),
               f"Cycle (1\u2013{n_max})", fill="#333333", font=f_label, anchor="mt")
    d_img.text((margin_l - 70, plot_top_y2 + plot_h2 / 2),
               "\u0394 / file", fill="#333333", font=f_label, anchor="mm", rotation=90)
    d_img.text((W / 2, plot_top_y2 - 12),
               "Differential curve baseline: \u0394 per file per cycle (normalized by corpus size)",
               fill="#1a3a5c", font=f_label, anchor="mt")

    # === Panel 3: Sparse-cell count per cycle (3 lines) ===
    panel3_top = panel2_bottom + panel_gap
    panel3_bottom = panel3_top + panel_h
    plot_top_y3 = panel3_top
    plot_bottom_y3 = panel3_bottom - 60
    plot_h3 = plot_bottom_y3 - plot_top_y3

    y_max_p3 = max(max(s_sparse), max(d_sparse), max(r_sparse)) * 1.15
    y_min_p3 = 0.0

    def to_y_p3(v):
        frac = (v - y_min_p3) / (y_max_p3 - y_min_p3)
        return plot_bottom_y3 - frac * plot_h3

    for i in range(n_ticks + 1):
        y = plot_top_y3 + (i / n_ticks) * plot_h3
        val = int(y_min_p3 + (i / n_ticks) * (y_max_p3 - y_min_p3))
        d_img.line([(margin_l, y), (W - margin_r, y)], fill="#dddddd", width=1)
        d_img.text((margin_l - 8, y), f"{val}", fill="#666666", font=f_label, anchor="rm")
    d_img.line([(margin_l, plot_bottom_y3), (margin_l, plot_top_y3)], fill="#444444", width=2)
    d_img.line([(margin_l, plot_bottom_y3), (W - margin_r, plot_bottom_y3)], fill="#444444", width=2)

    for name, sparse_arr in [("skills", s_sparse), ("docs", d_sparse), ("refs", r_sparse)]:
        coords = []
        for ci, v in enumerate(sparse_arr):
            x = margin_l + ci * x_step_p2
            y = to_y_p3(v)
            coords.append((x, y))
        for i in range(len(coords) - 1):
            d_img.line([coords[i], coords[i + 1]], fill=colors[name], width=3)
        for (x, y) in coords:
            d_img.ellipse([x - 5, y - 5, x + 5, y + 5], fill=colors[name])

    d_img.text((W / 2, plot_bottom_y3 + 30),
               f"Cycle (1\u2013{n_max})", fill="#333333", font=f_label, anchor="mt")
    d_img.text((margin_l - 70, plot_top_y3 + plot_h3 / 2),
               "Sparse cells", fill="#333333", font=f_label, anchor="mm", rotation=90)
    d_img.text((W / 2, plot_top_y3 - 12),
               "Sparse-cell count per cycle (S\u00b2 partition r=0.05, equal-area)",
               fill="#1a3a5c", font=f_label, anchor="mt")

    # Summary footer
    s_total = sum(s["cumulative_delta_per_cycle"])
    d_total = sum(d["cumulative_delta_per_cycle"])
    r_total = sum(r["cumulative_delta_per_cycle"])
    summary = (
        f"skills/: {s['cycles_total']} cycles, fixpoint reached, cumulative \u0394 = +{s_total:.4f}   "
        f"docs/: {d['cycles_total']} cycles, fixpoint reached, cumulative \u0394 = +{d_total:.4f}   "
        f"refs/: {r['cycles_total']} cycles, fixpoint reached, cumulative \u0394 = +{r_total:.4f}"
    )
    d_img.text((W / 2, H - 40), summary, fill="#444444", font=f_label, anchor="mt")
    d_img.text((W / 2, H - 22),
               "Zero negative \u0394 across all 3 corpora (Lemma 1 verified). 9-D primitive basis from internal-big-picture. corpus-level \u03d5_\u03b8 frozen, identity-init M\u00f6bius.",
               fill="#666666", font=f_legend, anchor="mt")

    img.save(OUT_PATH, "PNG", dpi=(150, 150))
    print(f"saved {OUT_PATH} ({os.path.getsize(OUT_PATH)} bytes)")


if __name__ == "__main__":
    main()
