#!/usr/bin/env python3
"""Nairaview holiday greeting card engine v2.

Renders square (1080x1080) and wide (1200x675) holiday greeting PNGs for
the @Naira_view X account. Design language: cinematic dark-green brand
canvas with dimensional hero elements — a waving Nigerian flag (wave
displacement + fabric shading), floating confetti, bokeh, fireworks —
and bold overlaid typography.

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

GOLD = "#c9a227"
WHITE = "#ffffff"
MUTED = "#9db3a4"
NG_GREEN = "#008751"
DEEP_TOP = "#0d4229"
DEEP_BOT = "#03130b"
RED = "#c0392b"

plt.rcParams["font.family"] = "DejaVu Sans"
rng = np.random.default_rng(20261001)


def hex_to_rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])


def spaced(s):
    return " ".join(s)


def new_canvas(w, h, top=DEEP_TOP, bot=DEEP_BOT):
    fig = plt.figure(figsize=(w / 100.0, h / 100.0), dpi=100)
    t_col, b_col = hex_to_rgb(top), hex_to_rgb(bot)
    t = np.linspace(0, 1, h)[:, None, None]
    img = t_col[None, None, :] * (1 - t) + b_col[None, None, :] * t
    img = np.repeat(img, w, axis=1)
    # vignette: darken edges
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / np.sqrt(2)
    img *= (1 - 0.35 * np.clip(r, 0, 1) ** 2)[:, :, None]
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
            fontweight="bold", color=color, transform=ax.transAxes, zorder=6)


def shadow_text(ax, x, y, s, **kw):
    z = kw.pop("zorder", 6)
    ax.text(x + 0.004, y - 0.006, s, ha="center", va="center", color="black",
            alpha=0.55, transform=ax.transAxes, zorder=z - 1,
            fontsize=kw.get("fontsize", 20), fontweight=kw.get("fontweight", "normal"))
    ax.text(x, y, s, ha="center", va="center", transform=ax.transAxes,
            zorder=z, **kw)


def waving_flag(ax, x0, y0, w, h, zorder=2, alpha=1.0):
    """Nigerian flag as a floating, waving ribbon with fabric shading."""
    n = 240
    m = max(80, int(n * h / w))
    u = np.linspace(0, 1, n)
    v = np.linspace(0, 1, m)
    U, V = np.meshgrid(u, v)
    # fabric wave: stronger amplitude for visible folds
    Z = 0.22 * np.sin(2 * np.pi * (2.1 * U + 0.6 * V) + 1.1) \
        + 0.08 * np.sin(2 * np.pi * (4.9 * U - 1.2 * V) + 0.4)
    dzdx = np.gradient(Z, axis=1)
    bright = np.clip(1.0 - 3.0 * dzdx, 0.38, 1.35)
    green, white = hex_to_rgb(NG_GREEN), np.ones(3)
    base = np.where(U[..., None] < 1 / 3, green,
                    np.where(U[..., None] < 2 / 3, white, green))
    rgb = np.clip(base * bright[..., None], 0, 1)
    # feather the left/right edges; ripple the top/bottom silhouette
    # so the flag reads as floating fabric, not a banner
    ripple = 0.07 * np.sin(2 * np.pi * 2.1 * U + 1.1)
    top_mask = np.clip((0.985 + ripple - V) * 28, 0, 1)
    bot_mask = np.clip((V - (0.015 + ripple)) * 28, 0, 1)
    edge_u = np.clip(np.minimum(U, 1 - U) * 14, 0, 1)
    edge = top_mask * bot_mask * edge_u
    rgba = np.dstack([rgb, np.full_like(bright, alpha) * edge])
    # soft drop shadow: dark blurred copy offset down-right
    sh = np.zeros((m, n, 4))
    sh[..., 3] = 0.4 * np.clip(edge, 0, 1)
    ax.imshow(sh, extent=[x0 + 0.022, x0 + w + 0.022, y0 - 0.028, y0 + h - 0.028],
              aspect="auto", zorder=zorder - 1, interpolation="bilinear")
    ax.imshow(rgba, extent=[x0, x0 + w, y0, y0 + h], aspect="auto",
              zorder=zorder, interpolation="bilinear")


def confetti(ax, n, palette, y_lo=0.05, y_hi=0.95, s_min=6, s_max=16, zorder=3):
    for _ in range(n):
        x, y = rng.random(), y_lo + rng.random() * (y_hi - y_lo)
        c = palette[rng.integers(len(palette))]
        a = 0.35 + rng.random() * 0.55
        if rng.random() < 0.45:
            ax.add_patch(patches.Circle(
                (x, y), rng.uniform(0.004, 0.011), transform=ax.transAxes,
                facecolor=c, alpha=a, edgecolor="none", zorder=zorder))
        else:
            ax.add_patch(patches.Rectangle(
                (x, y), rng.uniform(0.008, 0.02), rng.uniform(0.005, 0.012),
                angle=rng.uniform(0, 180), transform=ax.transAxes,
                facecolor=c, alpha=a, edgecolor="none", zorder=zorder,
                rotation_point="center"))


def bokeh(ax, n, palette, y_lo=0.1, y_hi=0.9, zorder=2):
    for _ in range(n):
        x, y = rng.random(), y_lo + rng.random() * (y_hi - y_lo)
        r = rng.uniform(0.015, 0.05)
        c = palette[rng.integers(len(palette))]
        ax.add_patch(patches.Circle((x, y), r, transform=ax.transAxes,
                                    facecolor=c, alpha=0.10, edgecolor="none", zorder=zorder))
        ax.add_patch(patches.Circle((x, y), r * 0.45, transform=ax.transAxes,
                                    facecolor=c, alpha=0.22, edgecolor="none", zorder=zorder))


def fireworks(ax, bursts, zorder=3):
    for x, y, r, colors in bursts:
        for _ in range(26):
            a = rng.uniform(0, 2 * np.pi)
            rr = r * (0.35 + rng.random() * 0.65)
            c = colors[rng.integers(len(colors))]
            ax.plot([x, x + rr * np.cos(a)], [y, y + rr * np.sin(a) * 0.7],
                    color=c, alpha=0.75, lw=2.5, transform=ax.transAxes, zorder=zorder)
        ax.add_patch(patches.Circle((x, y), 0.012, transform=ax.transAxes,
                                    facecolor=WHITE, alpha=0.9, edgecolor="none", zorder=zorder))


def crescent(ax, x, y, r, zorder=3):
    ax.add_patch(patches.Circle((x, y), r, transform=ax.transAxes,
                                facecolor=GOLD, edgecolor="none", zorder=zorder, alpha=0.95))
    ax.add_patch(patches.Circle((x + r * 0.38, y + r * 0.22), r * 0.82,
                                transform=ax.transAxes, facecolor=DEEP_TOP,
                                edgecolor="none", zorder=zorder))
    ax.text(x + r * 1.25, y + r * 0.1, "\u2605", ha="center", va="center",
            fontsize=34, color=GOLD, transform=ax.transAxes, zorder=zorder)


def light_beam(ax, x0, w_top, zorder=2, alpha=0.10):
    ax.add_patch(patches.Polygon(
        [[x0, 0], [x0 + w_top, 0], [x0 + w_top * 0.4 + 0.10, 1], [x0 - 0.10 + w_top * 0.4, 1]],
        closed=True, transform=ax.transAxes, facecolor=WHITE,
        alpha=alpha, edgecolor="none", zorder=zorder))


def footer(ax, y=0.055):
    ax.text(0.5, y, "nairaview.com", ha="center", va="center", fontsize=24,
            fontweight="bold", color=GOLD, transform=ax.transAxes, zorder=6)
    ax.text(0.5, y - 0.035, spaced("THE NIGERIAN EXCHANGE, DECODED DAILY"),
            ha="center", va="center", fontsize=13, color=MUTED,
            transform=ax.transAxes, zorder=6)


def scene(ax, theme, w):
    """Paint the hero scene for a theme. Returns (headline y, message y)."""
    pal = [NG_GREEN, WHITE, GOLD]
    if theme == "nigeria":
        # flag is the hero up top; headline sits below it on dark canvas
        # so white text never fights the flag's white stripe
        waving_flag(ax, 0.07, 0.60, 0.86, 0.30, zorder=2)
        confetti(ax, 70, pal, y_lo=0.08, y_hi=0.98, zorder=3)
        return 0.46, 0.26
    if theme == "christmas":
        bokeh(ax, 26, [GOLD, RED, "#2e8b57", WHITE], zorder=2)
        confetti(ax, 40, [GOLD, WHITE, RED], zorder=3)
        for x, y, s in ((0.14, 0.80, 40), (0.86, 0.78, 34), (0.80, 0.30, 28), (0.20, 0.32, 24)):
            ax.text(x, y, "\u2605", ha="center", va="center", fontsize=s,
                    color=GOLD, alpha=0.9, transform=ax.transAxes, zorder=3)
        return 0.62, 0.36
    if theme == "eid":
        crescent(ax, 0.5, 0.74, 0.085, zorder=2)
        for x, y, s in ((0.24, 0.80, 26), (0.76, 0.82, 30), (0.82, 0.34, 24), (0.18, 0.36, 22)):
            ax.text(x, y, "\u2605", ha="center", va="center", fontsize=s,
                    color=GOLD, alpha=0.75, transform=ax.transAxes, zorder=3)
        bokeh(ax, 12, [GOLD], zorder=2)
        return 0.58, 0.36
    if theme == "newyear":
        fireworks(ax, [(0.28, 0.78, 0.16, [GOLD, WHITE]),
                       (0.72, 0.82, 0.19, [GOLD, "#e8c86a", WHITE]),
                       (0.52, 0.66, 0.12, [WHITE, GOLD])], zorder=2)
        confetti(ax, 50, [GOLD, WHITE, "#e8c86a"], zorder=3)
        return 0.60, 0.36
    if theme == "workers":
        for i, yy in enumerate((0.70, 0.76, 0.82)):
            ax.text(0.5, yy, "\u25b2", ha="center", va="center", fontsize=64,
                    color=GOLD, alpha=0.22 + i * 0.20, transform=ax.transAxes,
                    zorder=2, fontweight="bold")
        confetti(ax, 45, [GOLD, NG_GREEN, WHITE], zorder=3)
        return 0.58, 0.36
    if theme == "easter":
        light_beam(ax, 0.38, 0.24, zorder=2, alpha=0.13)
        bokeh(ax, 10, [GOLD, WHITE], zorder=2)
        return 0.62, 0.36
    # solemn and default: restrained
    light_beam(ax, 0.44, 0.12, zorder=2, alpha=0.07)
    return 0.62, 0.36


def render(h, w, hgt, suffix):
    fig, ax = new_canvas(w, hgt)
    theme = h.get("theme", "")
    head_y, msg_y = scene(ax, theme, w)
    d = datetime.strptime(h["post_date"], "%Y-%m-%d")
    kicker(ax, 0.5, 0.945,
           h["name"] + "  \u00b7  " + d.strftime("%d %B %Y").lstrip("0").upper(), 19)
    # headline with drop shadow for legibility over the scene.
    # Line breaks are computed once (square-tuned); wide just sizes up.
    words = h["greeting"].split()
    lines, cur = [], ""
    for wd in words:
        if len((cur + " " + wd).strip()) <= 17:
            cur = (cur + " " + wd).strip()
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    if w == 1080:
        size = 60 if len(lines) <= 2 else 48
    else:
        size = 84 if len(lines) == 1 else (64 if len(lines) == 2 else 56)
    y = head_y + 0.05 * (len(lines) - 1)
    for ln in lines:
        shadow_text(ax, 0.5, y, ln, fontsize=size, fontweight="bold",
                    color=WHITE, zorder=6)
        y -= 0.115
    # message
    wrapped = textwrap.wrap(h["message"], width=46 if w == 1080 else 62)
    y = msg_y
    for ln in wrapped[:3]:
        ax.text(0.5, y, ln, ha="center", va="center", fontsize=21,
                color="#d7e2da", transform=ax.transAxes, zorder=6)
        y -= 0.055
    footer(ax)
    slug = h["date"]
    out = os.path.join(OUT_DIR, f"{slug}-{suffix}.png")
    fig.savefig(out, dpi=100)
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
