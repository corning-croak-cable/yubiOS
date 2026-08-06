"""Generate cycle-9 PNG charts for paper §8.2 (Phase A->H progression, A-H view).
Extends cycle-7 chart generation with Phase H (cycle 9) added as 5-seed preservation
per 4.3% corpus growth below 25% re-fit trigger (hyperspherical-harmonic-curve §Lifecycle).

Uses PIL.ImageDraw (no matplotlib). Run via bash with python3 (3.9) — PIL._imaging is broken on python3.12.
"""

import json
import os
from PIL import Image, ImageDraw, ImageFont


def get_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/google-noto-vf/NotoSans[wght].ttf",
    ]
    if bold:
        candidates.append("/usr/share/fonts/google-noto-vf/NotoSans-Italic[wght].ttf")
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def png_line_chart_with_errors(out_path, title, subtitle, x_labels,
                                 sphere_mean, sphere_std,
                                 flat_mean, flat_std,
                                 delta_mean, delta_std,
                                 width=900, height=560):
    """Phase progression with error bars (vertical lines at each point)."""
    img = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(img)
    f_title = get_font(22)
    f_sub = get_font(15)
    f_label = get_font(13)
    f_legend = get_font(12)
    margin_l, margin_r, margin_t, margin_b = 100, 50, 80, 70
    plot_w = width - margin_l - margin_r
    plot_h = height - margin_t - margin_b
    plot_bottom_y = height - margin_b
    plot_top_y = margin_t

    d.text((width / 2, 18), title, fill="#1a3a5c", font=f_title, anchor="mt")
    d.text((width / 2, 46), subtitle, fill="#666666", font=f_sub, anchor="mt")

    all_vals = list(sphere_mean) + list(flat_mean) + list(delta_mean) + [0]
    y_min = min(all_vals) - 0.15
    y_max = max(all_vals) + 0.15
    if y_min > 0:
        y_min = -0.1
    if y_max < 0:
        y_max = 0.1

    def to_y(value):
        frac = (value - y_min) / (y_max - y_min)
        return plot_bottom_y - frac * plot_h

    n_ticks = 7
    for i in range(n_ticks + 1):
        y = plot_top_y + (i / n_ticks) * plot_h
        val = y_min + (i / n_ticks) * (y_max - y_min)
        d.line([(margin_l, y), (margin_l + plot_w, y)], fill="#dddddd", width=1)
        d.text((margin_l - 8, y), f"{val:+.1f}", fill="#666666", font=f_label, anchor="rm")

    d.line([(margin_l, plot_bottom_y), (margin_l, plot_top_y)], fill="#444444", width=2)
    d.line([(margin_l, plot_bottom_y), (margin_l + plot_w, plot_bottom_y)], fill="#444444", width=2)
    zero_y = to_y(0)
    d.line([(margin_l, zero_y), (margin_l + plot_w, zero_y)], fill="#888888", width=1)

    n_pts = len(x_labels)
    for i, lbl in enumerate(x_labels):
        x = margin_l + (i + 0.5) / n_pts * plot_w
        d.text((x, plot_bottom_y + 20), lbl, fill="#333333", font=f_label, anchor="mt")

    def plot_with_errors(means, stds, color, label):
        coords = []
        for i, (m, s) in enumerate(zip(means, stds)):
            x = margin_l + (i + 0.5) / n_pts * plot_w
            y = to_y(m)
            coords.append((x, y))
            if s > 0:
                y_top = to_y(m + s)
                y_bot = to_y(m - s)
                d.line([(x, y_top), (x, y_bot)], fill=color, width=2)
                d.line([(x - 5, y_top), (x + 5, y_top)], fill=color, width=2)
                d.line([(x - 5, y_bot), (x + 5, y_bot)], fill=color, width=2)
        for i in range(len(coords) - 1):
            d.line([coords[i], coords[i + 1]], fill=color, width=3)
        for (x, y), m, s in zip(coords, means, stds):
            if s > 0:
                d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=color)
                d.text((x + 12, y - 4), f"{m:+.3f}\u00b1{s:.3f}", fill=color, font=f_label, anchor="lm")
            else:
                d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=color)
                d.text((x + 12, y - 4), f"{m:+.3f}", fill=color, font=f_label, anchor="lm")

    plot_with_errors(sphere_mean, sphere_std, "#1a3a5c", "Hyperspherical sphere")
    plot_with_errors(flat_mean, flat_std, "#cc6633", "Flat k=2 baseline")
    plot_with_errors(delta_mean, delta_std, "#228b22", "Matched-parameter \u03b4")

    d.text((28, height / 2), "Holdout R\u00b2", fill="#333333", font=f_label, anchor="mm", rotation=90)
    leg_x = margin_l
    leg_y = height - 22
    for label, color in [("Hyperspherical sphere", "#1a3a5c"),
                          ("Flat k=2 baseline", "#cc6633"),
                          ("Matched-parameter \u03b4", "#228b22")]:
        d.ellipse([leg_x - 5, leg_y - 5, leg_x + 5, leg_y + 5], fill=color)
        d.text((leg_x + 10, leg_y), label, fill="#333333", font=f_legend, anchor="lm")
        leg_x += 260
    img.save(out_path, "PNG", dpi=(150, 150))
    print(f"  saved {out_path} ({os.path.getsize(out_path)} bytes)")


def png_bar_chart(out_path, title, subtitle, x_labels, series, width=900, height=480):
    img = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(img)
    f_title = get_font(22)
    f_sub = get_font(15)
    f_label = get_font(13)
    f_legend = get_font(12)
    margin_l, margin_r, margin_t, margin_b = 100, 50, 80, 70
    plot_w = width - margin_l - margin_r
    plot_h = height - margin_t - margin_b
    plot_bottom_y = height - margin_b
    plot_top_y = margin_t

    d.text((width / 2, 18), title, fill="#1a3a5c", font=f_title, anchor="mt")
    d.text((width / 2, 46), subtitle, fill="#666666", font=f_sub, anchor="mt")

    all_vals = [v for _, vals, _ in series for v in vals] + [0]
    y_min = min(all_vals) - 0.1
    y_max = max(all_vals) + 0.1
    if y_min > 0:
        y_min = -0.05
    if y_max < 0:
        y_max = 0.05

    def to_y(value):
        frac = (value - y_min) / (y_max - y_min)
        return plot_bottom_y - frac * plot_h

    n_ticks = 5
    for i in range(n_ticks + 1):
        y = plot_top_y + (i / n_ticks) * plot_h
        val = y_min + (i / n_ticks) * (y_max - y_min)
        d.line([(margin_l, y), (margin_l + plot_w, y)], fill="#dddddd", width=1)
        d.text((margin_l - 8, y), f"{val:+.2f}", fill="#666666", font=f_label, anchor="rm")
    d.line([(margin_l, plot_bottom_y), (margin_l, plot_top_y)], fill="#444444", width=2)
    d.line([(margin_l, plot_bottom_y), (margin_l + plot_w, plot_bottom_y)], fill="#444444", width=2)
    zero_y = to_y(0)
    d.line([(margin_l, zero_y), (margin_l + plot_w, zero_y)], fill="#888888", width=1)

    n = len(x_labels)
    group_w = plot_w / n
    n_series = len(series)
    bar_w = group_w / (n_series + 1) * 0.85

    for i, lbl in enumerate(x_labels):
        cx = margin_l + (i + 0.5) * group_w
        for s_idx, (_, values, color) in enumerate(series):
            x_offset = (s_idx - (n_series - 1) / 2) * bar_w
            x1 = cx + x_offset - bar_w / 2
            x2 = cx + x_offset + bar_w / 2
            v = values[i]
            y_v = to_y(v)
            if v >= 0:
                d.rectangle([x1, y_v, x2, zero_y], fill=color)
                d.text(((x1 + x2) / 2, y_v - 14), f"{v:+.4f}", fill=color, font=f_label, anchor="mm")
            else:
                d.rectangle([x1, zero_y, x2, y_v], fill=color)
                d.text(((x1 + x2) / 2, y_v + 16), f"{v:+.4f}", fill=color, font=f_label, anchor="mm")
        d.text((cx, plot_bottom_y + 20), lbl, fill="#333333", font=f_label, anchor="mt")

    d.text((28, height / 2), "Absolute \u0394R\u00b2 (post \u2212 pre)", fill="#333333", font=f_label, anchor="mm", rotation=90)
    leg_x = margin_l
    leg_y = height - 22
    for label, _, color in series:
        d.rectangle([leg_x - 8, leg_y - 5, leg_x + 8, leg_y + 5], fill=color)
        d.text((leg_x + 14, leg_y), label, fill="#333333", font=f_legend, anchor="lm")
        leg_x += 220
    img.save(out_path, "PNG", dpi=(150, 150))
    print(f"  saved {out_path} ({os.path.getsize(out_path)} bytes)")


def png_table(out_path, title, table_data, col_widths, width=900, height=420):
    img = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(img)
    f_title = get_font(20)
    f_cell = get_font(13)
    f_header = get_font(14, bold=True)
    d.text((width / 2, 18), title, fill="#1a3a5c", font=f_title, anchor="mt")
    assert abs(sum(col_widths) - 1.0) < 0.01
    n_rows = len(table_data)
    n_cols = len(table_data[0])
    table_x = 30
    table_y = 60
    table_w = width - 60
    row_h = (height - 80) / n_rows
    col_x = [table_x + sum(col_widths[:i]) * table_w for i in range(n_cols + 1)]
    for r in range(n_rows):
        y = table_y + r * row_h
        is_header = (r == 0)
        is_total = (r == n_rows - 1)
        if is_header:
            d.rectangle([table_x, y, table_x + table_w, y + row_h], fill="#1a3a5c")
        elif is_total:
            d.rectangle([table_x, y, table_x + table_w, y + row_h], fill="#fff4d6")
        elif r % 2 == 0:
            d.rectangle([table_x, y, table_x + table_w, y + row_h], fill="#f8f8f8")
        for c in range(n_cols):
            cx = (col_x[c] + col_x[c + 1]) / 2
            cy = y + row_h / 2
            text = table_data[r][c]
            color = "white" if is_header else "#1a3a5c" if is_total else "#222222"
            font = f_header if is_header else f_cell
            d.text((cx, cy), text, fill=color, font=font, anchor="mm")
        d.line([(table_x, y), (table_x + table_w, y)], fill="#cccccc", width=1)
    d.line([(table_x, table_y + n_rows * row_h), (table_x + table_w, table_y + n_rows * row_h)], fill="#cccccc", width=1)
    for x in col_x:
        d.line([(x, table_y), (x, table_y + n_rows * row_h)], fill="#cccccc", width=1)
    img.save(out_path, "PNG", dpi=(150, 150))
    print(f"  saved {out_path} ({os.path.getsize(out_path)} bytes)")


# === Load all cycle fit data ===
with open("session/cycle5-fit-results.json") as f:
    c5 = json.load(f)
with open("session/cycle6-fit-results.json") as f:
    c6 = json.load(f)
with open("session/cycle7-fit-results.json") as f:
    c7 = json.load(f)
with open("session/cycle8-fit-results.json") as f:
    c8 = json.load(f)
with open("session/cycle9-fit-results.json") as f:
    c9 = json.load(f)
with open("session/cycle9-coverage.json") as f:
    c9_cov = json.load(f)

# === Phase A->H progression (A-H view, 8 phases) ===
# Phase A-D: single-seed (123)
# Phase E-H: 5-seed mean +/- std
phases = ["A (pre-c5)", "B (post-c5)", "C (post-c5 base)", "D (post-c6)",
           "E (post-c6 base)", "F (post-c7)", "G (post-c8)", "H (post-c9)"]
sphere_mean = [c5["phase_A"]["sphere_r2"], c5["phase_B"]["sphere_r2"],
                c6["phase_C"]["sphere_r2"], c6["phase_D"]["sphere_r2"],
                c7["phase_E"]["sphere_r2_mean"], c7["phase_F"]["sphere_r2_mean"],
                c8["phase_G"]["sphere_r2_mean"], c9["phase_H"]["sphere_r2_mean"]]
sphere_std  = [0, 0, 0, 0,
                c7["phase_E"]["sphere_r2_std"], c7["phase_F"]["sphere_r2_std"],
                c8["phase_G"]["sphere_r2_std"], c9["phase_H"]["sphere_r2_std"]]
flat_mean = [c5["phase_A"]["flat_r2"], c5["phase_B"]["flat_r2"],
              c6["phase_C"]["flat_r2"], c6["phase_D"]["flat_r2"],
              c7["phase_E"]["flat_r2_mean"], c7["phase_F"]["flat_r2_mean"],
              c8["phase_G"]["flat_r2_mean"], c9["phase_H"]["flat_r2_mean"]]
flat_std  = [0, 0, 0, 0,
              c7["phase_E"]["flat_r2_std"], c7["phase_F"]["flat_r2_std"],
              c8["phase_G"]["flat_r2_std"], c9["phase_H"]["flat_r2_std"]]
delta_mean = [s - f for s, f in zip(sphere_mean, flat_mean)]
delta_std  = [0, 0, 0, 0,
              ((c7["phase_E"]["delta_std"]**2 + c7["phase_E"]["sphere_r2_std"]**2 + c7["phase_E"]["flat_r2_std"]**2)**0.5),
              ((c7["phase_F"]["delta_std"]**2 + c7["phase_F"]["sphere_r2_std"]**2 + c7["phase_F"]["flat_r2_std"]**2)**0.5),
              ((c8["phase_G"]["delta_std"]**2 + c8["phase_G"]["sphere_r2_std"]**2 + c8["phase_G"]["flat_r2_std"]**2)**0.5),
              ((c9["phase_H"]["delta_std"]**2 + c9["phase_H"]["sphere_r2_std"]**2 + c9["phase_H"]["flat_r2_std"]**2)**0.5)]

print(f"=== Phase A->H progression ===")
for i, p in enumerate(phases):
    print(f"  {p}: sphere={sphere_mean[i]:+.4f}+/-{sphere_std[i]:.4f}, flat={flat_mean[i]:+.4f}+/-{flat_std[i]:.4f}, delta={delta_mean[i]:+.4f}+/-{delta_std[i]:.4f}")

# Per-cycle absolute delta (4 RSI cycles now)
print(f"\n=== Per-cycle absolute dR^2 ===")
c5_d_s = sphere_mean[1] - sphere_mean[0]
c5_d_f = flat_mean[1]   - flat_mean[0]
c6_d_s = sphere_mean[3] - sphere_mean[2]
c6_d_f = flat_mean[3]   - flat_mean[2]
c7_d_s = sphere_mean[5] - sphere_mean[4]
c7_d_f = flat_mean[5]   - flat_mean[4]
c8_d_s = sphere_mean[6] - sphere_mean[5]
c8_d_f = flat_mean[6]   - flat_mean[5]
c9_d_s = sphere_mean[7] - sphere_mean[6]
c9_d_f = flat_mean[7]   - flat_mean[6]
print(f"  Cycle 5 (B-A): sphere {c5_d_s:+.4f}, flat {c5_d_f:+.4f}")
print(f"  Cycle 6 (D-C): sphere {c6_d_s:+.4f}, flat {c6_d_f:+.4f}")
print(f"  Cycle 7 (F-E): sphere {c7_d_s:+.4f}, flat {c7_d_f:+.4f}")
print(f"  Cycle 8 (G-F): sphere {c8_d_s:+.4f}, flat {c8_d_f:+.4f}")
print(f"  Cycle 9 (H-G): sphere {c9_d_s:+.4f}, flat {c9_d_f:+.4f} (null: preserved Phase G)")

# Per-primitive coverage (pre-c5 -> post-c9)
prim_names = ["attestation", "trust chain", "least privilege", "declarative policy",
              "continuous/adaptive", "immutability", "audit/evidence",
              "cryptographic identity", "segmentation", "self-describing"]
prim_pre_c5 = [c5["primitives_pre"][prim_names.index(n)] for n in prim_names]
prim_post_c9 = [c9_cov["primitives_post_c9"][n] for n in prim_names]
prim_delta_total = [prim_post_c9[i] - prim_pre_c5[i] for i in range(10)]
print("\n=== Per-primitive coverage (pre-cycle-5 -> post-cycle-9) ===")
for i, n in enumerate(prim_names):
    marker = "  <-- saturated" if prim_post_c9[i] == 73 else ""
    print(f"  {n}: {prim_pre_c5[i]}/70 -> {prim_post_c9[i]}/73 (delta {prim_delta_total[i]:+d}){marker}")

# === Chart 1: Phase A->H progression with error bars ===
png_line_chart_with_errors("session/chart-A-H-1-progression.png",
                            title="Figure 1: Phase A -> B -> C -> D -> E -> F -> G -> H holdout R\u00b2 progression",
                            subtitle="(cycles 5-9 RSI corpus audit; 70->73 skills; error bars = 5-seed +/- std for E, F, G, H)",
                            x_labels=phases,
                            sphere_mean=sphere_mean, sphere_std=sphere_std,
                            flat_mean=flat_mean, flat_std=flat_std,
                            delta_mean=delta_mean, delta_std=delta_std)

# === Chart 2: Per-cycle absolute delta x 5 cycles ===
png_bar_chart("session/chart-A-H-2-per-cycle-delta.png",
              title="Figure 2: Per-cycle absolute improvement",
              subtitle="(sphere + flat R\u00b2 d across 5 RSI cycles: 5, 6, 7, 8, 9)",
              x_labels=["Cycle 5 (B-A)", "Cycle 6 (D-C)", "Cycle 7 (F-E)", "Cycle 8 (G-F)", "Cycle 9 (H-G)"],
              series=[("Hyperspherical sphere",
                       [c5_d_s, c6_d_s, c7_d_s, c8_d_s, c9_d_s], "#1a3a5c"),
                      ("Flat baseline k=2",
                       [c5_d_f, c6_d_f, c7_d_f, c8_d_f, c9_d_f], "#cc6633")])

# === Chart 3: Per-primitive coverage delta (pre-c5 -> post-c9) ===
png_bar_chart("session/chart-A-H-3-primitive-delta.png",
              title="Figure 3: Per-primitive coverage delta (pre-cycle-5 -> post-cycle-9 corpus)",
              subtitle="(5 RSI cycles cumulative; pre-cycle-5 baseline = 70-skill corpus; post-cycle-9 = 73-skill enriched corpus)",
              x_labels=prim_names,
              series=[("Coverage count delta (post-c9 - pre-c5)", prim_delta_total, "#228b22")],
              width=1000, height=540)

# === Table 1: Headline numbers ===
table_data = [
    ["Phase", "Corpus state", "K_kept", "Sphere R\u00b2", "Flat R\u00b2", "\u03b4 (sphere \u2212 flat)"],
    ["A (pre-cycle-5)", "70 skills, baseline corpus", "8",
     f"{c5['phase_A']['sphere_r2']:+.4f}", f"{c5['phase_A']['flat_r2']:+.4f}",
     f"{c5['phase_A']['delta']:+.4f}"],
    ["B (post-cycle-5)", "70 skills, after cycle-5 RSI", "6",
     f"{c5['phase_B']['sphere_r2']:+.4f}", f"{c5['phase_B']['flat_r2']:+.4f}",
     f"{c5['phase_B']['delta']:+.4f}"],
    ["C (post-cycle-5 baseline)", "70 skills, cycle-6 starting point", str(c6["phase_C"]["K_kept"]),
     f"{c6['phase_C']['sphere_r2']:+.4f}", f"{c6['phase_C']['flat_r2']:+.4f}",
     f"{c6['phase_C']['delta']:+.4f}"],
    ["D (post-cycle-6)", "70 skills, after cycle-6 RSI", str(c6["phase_D"]["K_kept"]),
     f"{c6['phase_D']['sphere_r2']:+.4f}", f"{c6['phase_D']['flat_r2']:+.4f}",
     f"{c6['phase_D']['delta']:+.4f}"],
    ["E (post-cycle-6 baseline)", "70 skills, cycle-7 starting point", str(c7["phase_E"]["K_kept"]),
     f"{c7['phase_E']['sphere_r2_mean']:+.4f} \u00b1 {c7['phase_E']['sphere_r2_std']:.4f}",
     f"{c7['phase_E']['flat_r2_mean']:+.4f} \u00b1 {c7['phase_E']['flat_r2_std']:.4f}",
     f"{c7['phase_E']['delta_mean']:+.4f} \u00b1 {c7['phase_E']['delta_std']:.4f}"],
    ["F (post-cycle-7)", "70 skills, after cycle-7 RSI", str(c7["phase_F"]["K_kept"]),
     f"{c7['phase_F']['sphere_r2_mean']:+.4f} \u00b1 {c7['phase_F']['sphere_r2_std']:.4f}",
     f"{c7['phase_F']['flat_r2_mean']:+.4f} \u00b1 {c7['phase_F']['flat_r2_std']:.4f}",
     f"{c7['phase_F']['delta_mean']:+.4f} \u00b1 {c7['phase_F']['delta_std']:.4f}"],
    ["G (post-cycle-8)", "70 skills, after cycle-8 RSI", str(c8["phase_G"]["K_kept"]),
     f"{c8['phase_G']['sphere_r2_mean']:+.4f} \u00b1 {c8['phase_G']['sphere_r2_std']:.4f}",
     f"{c8['phase_G']['flat_r2_mean']:+.4f} \u00b1 {c8['phase_G']['flat_r2_std']:.4f}",
     f"{c8['phase_G']['delta_mean']:+.4f} \u00b1 {c8['phase_G']['delta_std']:.4f}"],
    ["H (post-cycle-9)", "73 skills (70 + 3 enriched), cycle-9 RSI", str(c9["phase_H"]["K_kept"]),
     f"{c9['phase_H']['sphere_r2_mean']:+.4f} \u00b1 {c9['phase_H']['sphere_r2_std']:.4f}",
     f"{c9['phase_H']['flat_r2_mean']:+.4f} \u00b1 {c9['phase_H']['flat_r2_std']:.4f}",
     f"{c9['phase_H']['delta_mean']:+.4f} \u00b1 {c9['phase_H']['delta_std']:.4f}"],
    ["Cycle-5 \u0394 (B \u2212 A)", "RSI pass #1", "\u2014",
     f"{c5_d_s:+.4f}", f"{c5_d_f:+.4f}", f"{c5_d_s - c5_d_f:+.4f}"],
    ["Cycle-6 \u0394 (D \u2212 C)", "RSI pass #2", "\u2014",
     f"{c6_d_s:+.4f}", f"{c6_d_f:+.4f}", f"{c6_d_s - c6_d_f:+.4f}"],
    ["Cycle-7 \u0394 (F \u2212 E)", "RSI pass #3 (5-seed)", "\u2014",
     f"{c7_d_s:+.4f}", f"{c7_d_f:+.4f}", f"{c7_d_s - c7_d_f:+.4f}"],
    ["Cycle-8 \u0394 (G \u2212 F)", "RSI pass #4 (5-seed)", "\u2014",
     f"{c8_d_s:+.4f}", f"{c8_d_f:+.4f}", f"{c8_d_s - c8_d_f:+.4f}"],
    ["Cycle-9 \u0394 (H \u2212 G)", "RSI pass #5 (null: preserved)", "\u2014",
     f"{c9_d_s:+.4f}", f"{c9_d_f:+.4f}", f"{c9_d_s - c9_d_f:+.4f}"],
    ["Total \u0394 (H \u2212 A)", "All 5 RSI passes", "\u2014",
     f"{sphere_mean[7] - sphere_mean[0]:+.4f}",
     f"{flat_mean[7] - flat_mean[0]:+.4f}",
     f"{delta_mean[7] - delta_mean[0]:+.4f}"],
]
png_table("session/chart-A-H-table-1-headline.png",
          title="Table 1: Headline numbers across cycles 5-9 (phases A-H; 70->73-skill corpus; error bars = 5-seed +/- std for E, F, G, H)",
          table_data=table_data,
          col_widths=[0.18, 0.26, 0.06, 0.16, 0.16, 0.18],
          width=1000, height=620)

# === Table 2: Per-cycle primitive-closure summary ===
table2_data = [
    ["Cycle", "Per-skill target", "Skills touched", "Primitives targeted"],
    ["Cycle 5",
     "Top-priority corpus missing primitive per skill",
     "70/70 (all skills)",
     "segmentation, trust chain, cryptographic identity, declarative policy, self-describing, attestation, immutability, least privilege, continuous/adaptive, audit/evidence"],
    ["Cycle 6",
     "2nd-priority MOVABLE missing primitive per skill",
     "61/70 (9 already covered all movable)",
     "cryptographic identity (46), declarative policy (10), trust chain (1), attestation (2), least privilege (2)"],
    ["Cycle 7",
     "3rd-priority MOVABLE missing primitive per skill",
     "49/70 (21 already covered all movable)",
     "trust chain (33), declarative policy (6), attestation (4), least privilege (4), immutability (2)"],
    ["Cycle 8",
     "4th-priority MOVABLE missing primitive per skill",
     "49/70 (30 already covered all movable)",
     "declarative policy (22), attestation (15), immutability (6), least privilege (5), continuous/adaptive (1)"],
    ["Cycle 9",
     "5th-priority MOVABLE + corpus enrichment",
     "9/70 substantive + 61/70 audit-only + 3 corpus-enrichment",
     "attestation (8 substantive) + least privilege (1 substantive) + corpus-enrichment: attestation (keylime), LP (k8s-pss-restricted), C/A (falco)"],
]
png_table("session/chart-A-H-table-2-cycle-summary.png",
          title="Table 2: Per-cycle primitive-closure summary (cycles 5-9)",
          table_data=table2_data,
          col_widths=[0.10, 0.30, 0.20, 0.40],
          width=1000, height=380)

# === Table 3: Per-primitive coverage progression ===
# c5 primitives_post may be list (older format) or dict; c6-c9 are dicts (indexed by primitive name)
prim_post_c5 = [c5["primitives_post"][prim_names.index(n)] if isinstance(c5["primitives_post"], list) else c5["primitives_post"][n] for n in prim_names]
prim_post_c6 = [c7["primitives_pre"][n] for n in prim_names]  # cycle-7 pre = cycle-6 post (dict)
prim_post_c7 = [c7["primitives_post"][n] for n in prim_names]  # dict
prim_post_c8 = [c8["primitives_post_c8"][n] for n in prim_names]  # dict
prim_post_c9 = [c9_cov["primitives_post_c9"][n] for n in prim_names]  # dict
prim_delta_total = [prim_post_c9[i] - prim_pre_c5[i] for i in range(10)]  # recompute
table3_data = [
    ["Primitive", "Pre-cycle-5", "Post-cycle-5", "Post-cycle-6", "Post-cycle-7", "Post-cycle-8", "Post-cycle-9 (N=73)", "\u0394 (H \u2212 A)"]
]
for i, name in enumerate(prim_names):
    table3_data.append([name, f"{prim_pre_c5[i]}/70", f"{prim_post_c5[i]}/70",
                        f"{prim_post_c6[i]}/70", f"{prim_post_c7[i]}/70",
                        f"{prim_post_c8[i]}/70", f"{prim_post_c9[i]}/73",
                        f"{prim_post_c9[i] - prim_pre_c5[i]:+d}"])
png_table("session/chart-A-H-table-3-primitive-progression.png",
          title="Table 3: Per-primitive coverage progression (pre-c5 -> post-c9)",
          table_data=table3_data,
          col_widths=[0.20, 0.10, 0.10, 0.10, 0.10, 0.10, 0.15, 0.15],
          width=1100, height=500)

print("\n=== All cycle-9 A-H charts generated ===")
for f in ["session/chart-A-H-1-progression.png", "session/chart-A-H-2-per-cycle-delta.png",
           "session/chart-A-H-3-primitive-delta.png", "session/chart-A-H-table-1-headline.png",
           "session/chart-A-H-table-2-cycle-summary.png", "session/chart-A-H-table-3-primitive-progression.png"]:
    print(f"  {f}: {os.path.getsize(f)} bytes")
