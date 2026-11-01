#!/usr/bin/env python3
"""Hero chart: raw tool-selection accuracy by tool count, with the pure-chance
baseline overlaid, so the reader sees both numbers at once instead of just the
scarier raw-accuracy-only version. Results artifact, not decoration (per the
job's hero-priority rule) -- built straight from summary.json, same source as
the article's own numbers."""
import json
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(__file__)
W, H = 1600, 900
BG = (18, 20, 24)
FG = (235, 237, 240)
MUTED = (140, 146, 156)
BAR = (90, 169, 230)
CHANCE = (230, 120, 90)


def font(size, bold=False):
    paths = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default()


def main():
    summary = json.load(open(os.path.join(HERE, "summary.json")))
    ns = [5, 10, 25, 50]

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    title_f = font(40, bold=True)
    sub_f = font(22)
    label_f = font(24, bold=True)
    small_f = font(18)

    d.text((60, 40), "Tool-selection accuracy vs. tool-menu size", font=title_f, fill=FG)
    d.text((60, 92), "Same 20 requests, same model, only the number of available tools changes",
           font=sub_f, fill=MUTED)

    plot_left, plot_right = 140, W - 500
    plot_top, plot_bottom = 180, H - 160
    plot_h = plot_bottom - plot_top
    n_groups = len(ns)
    group_w = (plot_right - plot_left) / n_groups

    # axis
    d.line([(plot_left, plot_top), (plot_left, plot_bottom)], fill=MUTED, width=2)
    d.line([(plot_left, plot_bottom), (plot_right, plot_bottom)], fill=MUTED, width=2)
    for pct in [0, 25, 50, 75, 100]:
        y = plot_bottom - plot_h * (pct / 100)
        d.line([(plot_left - 6, y), (plot_right, y)], fill=(40, 43, 50), width=1)
        d.text((plot_left - 50, y - 10), f"{pct}%", font=small_f, fill=MUTED)

    bar_w = group_w * 0.42
    for i, n in enumerate(ns):
        s = summary[str(n)]
        gx = plot_left + i * group_w + group_w / 2
        acc = s["raw_accuracy"]
        chance = s["chance_baseline"]

        bar_h = plot_h * acc
        bx0 = gx - bar_w / 2
        bx1 = gx + bar_w / 2
        by0 = plot_bottom - bar_h
        d.rectangle([bx0, by0, bx1, plot_bottom], fill=BAR)
        d.text((bx0, by0 - 32), f"{s['correct']}/{s['total']}", font=label_f, fill=FG)
        d.text((bx0, by0 - 58), f"{acc*100:.0f}%", font=label_f, fill=BAR)

        chance_y = plot_bottom - plot_h * chance
        d.line([(bx0 - 8, chance_y), (bx1 + 8, chance_y)], fill=CHANCE, width=3)

        d.text((gx - 40, plot_bottom + 14), f"{n} tools", font=label_f, fill=FG)

    d.rectangle([plot_right + 40, plot_top, plot_right + 70, plot_top + 20], fill=BAR)
    d.text((plot_right + 80, plot_top), "Raw accuracy", font=small_f, fill=FG)
    d.line([(plot_right + 40, plot_top + 50), (plot_right + 70, plot_top + 50)], fill=CHANCE, width=3)
    d.text((plot_right + 80, plot_top + 40), "Pure-chance baseline (1/n)", font=small_f, fill=FG)

    lines = [
        "Accuracy-over-chance",
        "(observed / 1/n):",
        "",
    ]
    for n in ns:
        s = summary[str(n)]
        lines.append(f"n={n}:  {s['accuracy_over_chance']:.1f}x chance")
    y = plot_top + 110
    for line in lines:
        d.text((plot_right + 40, y), line, font=small_f, fill=MUTED if line else FG)
        y += 28

    d.text((60, H - 46), "Image by author. 20 scenarios x 4 tool-menu sizes, gemini-3.5-flash-lite, temperature 0.",
           font=small_f, fill=MUTED)

    out_path = os.path.join(HERE, "charts", "hero-tool-count-accuracy.png")
    img.save(out_path)
    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
