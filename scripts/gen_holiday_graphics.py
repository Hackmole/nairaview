#!/usr/bin/env python3
"""Nairaview holiday greeting card engine.

Renders square (1080x1080) and wide (1200x675) holiday greeting PNGs for
the @Naira_view X account, in the same visual language as gen_infographics.py
(deep-green gradient, gold accents, DejaVu Sans).

Reads assets/img/holidays/holidays.json. Only holidays with a post_date get
a card. Output: assets/img/holidays/<slug>-square.png / <slug>-wide.png.

Usage:
    python3 gen_holiday_graphics.py            # all holidays with post_date
    python3 gen_holiday_graphics.py --test     # one sample card to /tmp
"""
import json
import os
import sys
import textwrap
from datetime import datetime

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CAL = os.path.join(HERE, "..", "assets", "img", "holidays", "holidays.json")
OUT_DIR = os.path.join(HERE, "..", "assets", "img", "holidays")

GREEN = "#087a4b"
GOLD = "#c9a227"
WHITE = "#ffffff"
MUTED = "#9db3a4"
DEEP_TOP = "#0d4229"
DEEP_BOT = "#03130b"
RED = "#c0392b"

plt.rcParams["font.family"] = "DejaVu Sans"


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def spaced(s):
    return " ".join(s)  # hair spaces for letterspaced kickers


def new_canvas(w, h, top=DEEP_TOP, bot=DEEP_BOT):
    fig = plt.figure(figsize=(w / 100.0, h / 100.0), dpi=100)
    t_col = np.array(hex_to_rgb(top))
    b_col = np.array(hex_to_rgb(bot))
    t = np.linspace(0, 1, h)[:, None, None]
    img = t_col[None, None, :] * (1 - t) + b_col[None, None, :] * t
    img = np.repeat(img, w, axis=1)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(img, extent=[0, 1, 0, 1], aspect="auto", zorder=0)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.plot([0, 1], [0.996, 0.996], color=GOLD, lw=7, transform=ax.transAxes,
            clip_on=False, zorder=3, solid_capstyle="butt")
    return fig, ax


def kicker(ax, x, y, text, size, ha="center", color=GOLD):
    ax.text(x, y, spaced(text.upper()), ha=ha, va="center", fontsize=size,
            fontweight="bold", color=color, transform=ax.transAxes, zorder=4)


def motif(ax, theme):
    """Per-holiday decorative motif, drawn subtly behind the headline."""
    if theme == "nigeria":
        # green-white-green ribbon across the upper third
        for i, c in enumerate(["#008751", "#ffffff", "#008751"]):
            ax.add_patch(patches.Rectangle(
                (0.07 + i * 0.2867, 0.80), 0.2867, 0.045, transform=ax.transAxes,
                facecolor=c, edgecolor="none", zorder=2, alpha=0.9))
    elif theme == "christmas":
        for x, y, s, c in ((0.15, 0.78, 44, GOLD), (0.85, 0.80, 36, GOLD),
                           (0.78, 0.30, 30, RED), (0.22, 0.28, 26, GOLD),
                           (0.5, 0.86, 30, "#e8c86a")):
            ax.text(x, y, "\u2605", ha="center", va="center", fontsize=s,
                    color=c, alpha=0.85, transform=ax.transAxes, zorder=2)
    elif theme == "eid":
        # gold crescent: filled circle + offset background circle
        ax.add_patch(patches.Circle((0.5, 0.72), 0.075, transform=ax.transAxes,
                                    facecolor=GOLD, edgecolor="none", zorder=2, alpha=0.9))
        ax.add_patch(patches.Circle((0.525, 0.735), 0.065, transform=ax.transAxes,
                                    facecolor=DEEP_TOP, edgecolor="none", zorder=2))
        ax.text(0.60, 0.70, "\u2605", ha="center", va="center", fontsize=30,
                color=GOLD, transform=ax.transAxes, zorder=2)
    elif theme == "newyear":
        # radiating gold rays from top center
        for a in np.linspace(200, 340, 9):
            r = np.radians(a)
            ax.plot([0.5, 0.5 + 0.34 * np.cos(r)], [1.02, 1.02 + 0.30 * np.sin(r)],
                    color=GOLD, alpha=0.28, lw=3, transform=ax.transAxes,
                    zorder=2, clip_on=False)
        for x, y, s in ((0.2, 0.82, 26), (0.8, 0.84, 32), (0.68, 0.30, 24)):
            ax.text(x, y, "\u2605", ha="center", va="center", fontsize=s,
                    color=GOLD, alpha=0.8, transform=ax.transAxes, zorder=2)
    elif theme == "workers":
        # bold upward chevrons
        for i, y in enumerate((0.74, 0.79, 0.84)):
            ax.text(0.5, y, "\u25b2", ha="center", va="center", fontsize=54,
                    color=GOLD, alpha=0.25 + i * 0.18, transform=ax.transAxes,
                    zorder=2, fontweight="bold")
    # solemn / easter: no motif, restrained by design


def footer(ax, y=0.055):
    ax.text(0.5, y, "nairaview.com", ha="center", va="center", fontsize=24,
            fontweight="bold", color=GOLD, transform=ax.transAxes, zorder=4)
    ax.text(0.5, y - 0.035, spaced("THE NIGERIAN EXCHANGE, DECODED DAILY"),
            ha="center", va="center", fontsize=13, color=MUTED,
            transform=ax.transAxes, zorder=4)


def render(h, w, hgt, suffix):
    fig, ax = new_canvas(w, hgt)
    motif(ax, h.get("theme", ""))
    kicker(ax, 0.5, 0.93, h["name"], 26)
    # headline, wrapped
    words = h["greeting"].split()
    lines, cur = [], ""
    max_chars = 22 if w == 1080 else 34
    for wd in words:
        if len((cur + " " + wd).strip()) <= max_chars:
            cur = (cur + " " + wd).strip()
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    size = 64 if w == 1080 else 72
    if len(lines) > 2:
        size = int(size * 0.82)
    y = 0.60 if len(lines) == 1 else 0.64
    for ln in lines:
        ax.text(0.5, y, ln, ha="center", va="center", fontsize=size,
                fontweight="bold", color=WHITE, transform=ax.transAxes, zorder=4)
        y -= 0.11
    # message
    wrapped = textwrap.wrap(h["message"], width=48 if w == 1080 else 64)
    y = 0.40
    for ln in wrapped[:3]:
        ax.text(0.5, y, ln, ha="center", va="center", fontsize=21,
                color="#d7e2da", transform=ax.transAxes, zorder=4)
        y -= 0.055
    # date line
    d = datetime.strptime(h["post_date"], "%Y-%m-%d")
    ax.text(0.5, 0.22, d.strftime("%d %B %Y").lstrip("0"), ha="center",
            va="center", fontsize=20, color=MUTED, transform=ax.transAxes, zorder=4)
    footer(ax)
    slug = h["date"]
    out = os.path.join(OUT_DIR, f"{slug}-{suffix}.png")
    fig.savefig(out, dpi=100, bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    print("wrote", out)
    return out


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    if "--test" in sys.argv:
        render({"name": "Independence Day",
                "greeting": "Happy Independence Day, Nigeria!",
                "message": "67 years strong. To the builders, the believers — and the bull market ahead.",
                "post_date": "2027-10-01", "date": "test", "theme": "nigeria"},
               1080, 1080, "square")
        return 0
    cal = json.load(open(CAL, encoding="utf-8"))
    n = 0
    for h in cal["holidays"]:
        if not h.get("post_date"):
            continue
        render(h, 1080, 1080, "square")
        render(h, 1200, 675, "wide")
        n += 1
    print(f"done: {n} holidays rendered (square + wide)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
