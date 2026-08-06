"""Generate the new RSI-79 chart (cycles 10-15, full 79-skill corpus).
Uses the existing chart style: bar chart with primitive coverage progression + cycle deltas.
Vertical error bars for any series with std > 0.
"""
import json
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path("/var/workspace/session/rsi-data")
JSON_PATH = OUT_DIR / "rsi-79-corpus-multi-cycle.json"
OUT_PATH = "/var/workspace/session/chart-RSI-79-cycles-1-6.png"

PRIM_NAMES = [
    "attestation", "trust_chain", "least_privilege", "declarative_policy",
    "continuous_adaptive", "immutability", "audit_evidence",
    "cryptographic_identity", "segmentation",
]


def get_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/google-noto-vf/NotoSans[wght].ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def render_chart():
    data = json.load(open(JSON_PATH))
    cycles_total = data["cycles_total"]
    cum_deltas = data["cumulative_delta_per_cycle"]
    sparse = data["sparse_cells_per_cycle"]
    prim_cov = data["primitive_coverage_per_cycle"]

    W, H = 1400, 760
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    f_title = get_font(24)
    f_sub = get_font(15)
    f_label = get_font(13)
    f_legend = get_font(12)

    margin_l, margin_r, margin_t, margin_b = 110, 60, 100, 110
    plot_w = W - margin_l - margin_r
    plot_h = H - margin_t - margin_b
    plot_bottom_y = H - margin_b
    plot_top_y = margin_t

    d.text((W / 2, 22),
           "Hyper-Sphere RSI on 79-Repo-Skills Corpus \u2014 6-Cycle Fixpoint Run",
           fill="#1a3a5c", font=f_title, anchor="mt")
    d.text((W / 2, 52),
           "Cumulative \u0394 per cycle + per-primitive coverage progression (chordal proxy on S\u00b2, identity M\u00f6bius)",
           fill="#666666", font=f_sub, anchor="mt")

    # Two charts side-by-side: left = cumulative Δ bars, right = primitive coverage lines
    chart_w = (plot_w - 40) // 2

    # === Left chart: Cumulative Δ per cycle (bar chart, with peak markers) ===
    left_x0 = margin_l
    left_x1 = left_x0 + chart_w

    # Y-axis: 0 to max cum Δ * 1.1
    y_max_l = max(cum_deltas) * 1.15
    y_min_l = 0.0

    def to_y_left(v):
        frac = (v - y_min_l) / (y_max_l - y_min_l)
        return plot_bottom_y - frac * plot_h

    # Grid lines (left chart)
    n_ticks_l = 5
    for i in range(n_ticks_l + 1):
        y = plot_top_y + (i / n_ticks_l) * plot_h
        val = y_min_l + (i / n_ticks_l) * (y_max_l - y_min_l)
        d.line([(left_x0, y), (left_x1, y)], fill="#dddddd", width=1)
        d.text((left_x0 - 8, y), f"{val:+.2f}", fill="#666666", font=f_label, anchor="rm")
    d.line([(left_x0, plot_bottom_y), (left_x0, plot_top_y)], fill="#444444", width=2)
    d.line([(left_x0, plot_bottom_y), (left_x1, plot_bottom_y)], fill="#444444", width=2)

    # Bar width
    n_cycles = len(cum_deltas)
    bar_w_l = chart_w / n_cycles * 0.7
    for i, delta in enumerate(cum_deltas):
        cx = left_x0 + (i + 0.5) * (chart_w / n_cycles)
        y_top = to_y_left(delta)
        y_bot = plot_bottom_y
        color = "#5a8ec7" if delta > 0 else "#888888"
        d.rectangle([cx - bar_w_l / 2, y_top, cx + bar_w_l / 2, y_bot], fill=color)
        d.text((cx, y_top - 16), f"{delta:+.2f}", fill="#1a3a5c", font=f_label, anchor="mb")
        d.text((cx, plot_bottom_y + 8), f"C{i+1}", fill="#666666", font=f_label, anchor="mt")

    d.text((left_x0 + chart_w / 2, plot_bottom_y + 30),
           "Cycle (1\u20136)", fill="#333333", font=f_label, anchor="mt")
    d.text((left_x0 - 70, plot_top_y + plot_h / 2),
           "Cumulative \u0394", fill="#333333", font=f_label, anchor="mm", rotation=90)
    d.text((left_x0 + chart_w / 2, plot_top_y - 16),
           "Cumulative \u0394 per cycle", fill="#1a3a5c", font=f_label, anchor="mt")

    # === Right chart: Per-primitive coverage progression (line chart, vertical error bars not applicable) ===
    right_x0 = left_x1 + 40
    right_x1 = margin_l + plot_w

    # Y-axis: 0 to 79 (corpus size)
    y_max_r = 79
    y_min_r = 0

    def to_y_right(v):
        frac = (v - y_min_r) / (y_max_r - y_min_r)
        return plot_bottom_y - frac * plot_h

    # Grid lines (right chart)
    n_ticks_r = 5
    for i in range(n_ticks_r + 1):
        y = plot_top_y + (i / n_ticks_r) * plot_h
        val = int(y_min_r + (i / n_ticks_r) * (y_max_r - y_min_r))
        d.line([(right_x0, y), (right_x1, y)], fill="#dddddd", width=1)
        d.text((right_x0 - 8, y), f"{val}", fill="#666666", font=f_label, anchor="rm")
    d.line([(right_x0, plot_bottom_y), (right_x0, plot_top_y)], fill="#444444", width=2)
    d.line([(right_x0, plot_bottom_y), (right_x1, plot_bottom_y)], fill="#444444", width=2)

    # Plot each primitive as a line
    colors = ["#1a3a5c", "#cc6633", "#228b22", "#9933cc", "#cc6600",
              "#996633", "#339966", "#cc3366", "#666666"]
    n_pts = len(prim_cov)
    x_step = (right_x1 - right_x0) / max(n_pts - 1, 1)

    for pi, name in enumerate(PRIM_NAMES):
        coords = []
        for ci, cov_row in enumerate(prim_cov):
            x = right_x0 + ci * x_step
            y = to_y_right(cov_row[pi])
            coords.append((x, y))
        # Connecting lines
        for i in range(len(coords) - 1):
            d.line([coords[i], coords[i + 1]], fill=colors[pi], width=2)
        # Markers
        for (x, y) in coords:
            d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=colors[pi])

    d.text((right_x0 + chart_w / 2, plot_bottom_y + 30),
           "Cycle (1\u20136)", fill="#333333", font=f_label, anchor="mt")
    d.text((right_x0 - 70, plot_top_y + plot_h / 2),
           "Coverage count (/79)", fill="#333333", font=f_label, anchor="mm", rotation=90)
    d.text((right_x0 + chart_w / 2, plot_top_y - 16),
           "Per-primitive coverage progression", fill="#1a3a5c", font=f_label, anchor="mt")

    # Legend (right side bottom)
    leg_x = right_x0
    leg_y = plot_bottom_y + 50
    for pi, name in enumerate(PRIM_NAMES):
        col = pi % 3
        row = pi // 3
        x_pos = leg_x + col * (chart_w // 3)
        y_pos = leg_y + row * 16
        d.ellipse([x_pos - 4, y_pos - 4, x_pos + 4, y_pos + 4], fill=colors[pi])
        d.text((x_pos + 8, y_pos), name, fill="#333333", font=f_legend, anchor="lm")

    # Summary stats bottom
    cum_total = sum(cum_deltas)
    sparse_total_init = sparse[0]
    sparse_total_final = sparse[-1]
    summary = (f"6 RSI cycles on {data['corpus_size']}-skill corpus   "
               f"Cumulative \u0394 total: +{cum_total:.4f}   "
               f"Sparse cells: {sparse_total_init}\u2192{sparse_total_final}   "
               f"Final coverage: {prim_cov[-1]}/79 = {prim_cov[-1][0]}/{data['corpus_size']} all primitives")
    d.text((W / 2, H - 18), summary, fill="#444444", font=f_label, anchor="mt")

    img.save(OUT_PATH, "PNG", dpi=(150, 150))
    print(f"saved {OUT_PATH} ({os.path.getsize(OUT_PATH)} bytes)")


if __name__ == "__main__":
    render_chart()
