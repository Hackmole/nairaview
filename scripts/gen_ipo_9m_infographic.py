#!/usr/bin/env python3
"""Dangote Refinery IPO 9M-results infographic.

Renders a square (1080x1080) and wide (1200x675) "9M 2026 results" PNG in the
site's green/gold treatment, using only the verified unaudited 9M figures
(released 13 Oct 2026, Nairametrics/ThisDay):
  - Revenue $22.48bn (+144% YoY)
  - Net profit $4.73bn (vs $117.2m loss)
  - EBITDA $5.52bn (+780% YoY)
  - Offer closes 27 October 2026

Usage:
    python3 gen_ipo_9m_infographic.py         # writes dated + -latest copies
Output:
    assets/img/infographics/dangote-ipo-9m-YYYYMMDD{-square,-wide}.png
"""
import os
import shutil
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_infographics import (  # noqa: E402
    new_canvas, kicker, label, hline, GREEN, GOLD, WHITE, MUTED, hex_to_rgb,
)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "assets", "img", "infographics")

FACTS = [
    ("$22.48bn", "9M revenue (+144% YoY)"),
    ("$4.73bn", "9M net profit (vs $117m loss)"),
    ("$5.52bn", "9M EBITDA (+780% YoY)"),
    ("27 Oct", "offer closes 2026"),
]


def draw(ax, wide):
    # kicker + headline
    kicker(ax, 0.5, 0.90, "Dangote Refinery · 9M 2026 (unaudited)", 26 if not wide else 22)
    ax.text(0.5, 0.80, "Nine months, in three numbers", ha="center", va="center", fontsize=34,
            color=MUTED, transform=ax.transAxes, zorder=4)
    hline(ax, 0.70)
    # facts
    if wide:
        # two columns: 2 + 2
        cols = [(0.30, FACTS[:2]), (0.72, FACTS[2:])]
        for x, items in cols:
            y = 0.58
            for val, cap in items:
                ax.text(x, y, val, ha="center", va="center", fontsize=44,
                        fontweight="bold", color=GOLD, transform=ax.transAxes, zorder=4)
                label(ax, x, y - 0.07, cap, 17)
                y -= 0.20
    else:
        y = 0.62
        for val, cap in FACTS:
            ax.text(0.5, y, val, ha="center", va="center", fontsize=44,
                    fontweight="bold", color=GOLD, transform=ax.transAxes, zorder=4)
            label(ax, 0.5, y - 0.045, cap, 19)
            y -= 0.115
    hline(ax, 0.10 if not wide else 0.14)
    label(ax, 0.5, 0.05 if not wide else 0.07, "nairaview.com", 20, color=WHITE, weight="bold")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d")
    for name, w, h in [("square", 1080, 1080), ("wide", 1200, 675)]:
        fig, ax = new_canvas(w, h)
        draw(ax, wide=(name == "wide"))
        dated = os.path.join(OUT_DIR, f"dangote-ipo-9m-{stamp}-{name}.png")
        latest = os.path.join(OUT_DIR, f"dangote-ipo-9m-latest-{name}.png")
        fig.savefig(dated, dpi=100, bbox_inches="tight", pad_inches=0)
        plt.close(fig)
        shutil.copy(dated, latest)
        print("wrote", dated, os.path.getsize(dated), "bytes")


if __name__ == "__main__":
    main()
