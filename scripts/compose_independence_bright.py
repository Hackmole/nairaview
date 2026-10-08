#!/usr/bin/env python3
"""Bright-style Independence Day card compositor (reference-driven).

Takes a bright photographic background and lays out the full reference
design: coat-of-arms-friendly top, giant serif anniversary numeral with
ribbon swoosh, serif headline, letterspaced labels, script accents,
message, and a bottom dark-green band with value icons + brush banner.

Usage:
    python3 compose_independence_bright.py --bg <bg.jpg> --out <card.png>
"""
import argparse
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "assets", "fonts")

DARK = (11, 61, 42)          # deep green ink
DARKER = (7, 45, 31)
BAND = (10, 53, 39)          # bottom band green
GOLD = (201, 162, 39)
WHITE = (255, 255, 255)
INK = (43, 43, 43)

SIZE = 1080
random.seed(7)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def tracked(draw, xy, text, fnt, fill, tracking=0, anchor="ma"):
    x, y = xy
    widths = [draw.textlength(ch, font=fnt) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    if anchor == "ma":
        x -= total / 2
    elif anchor == "ra":
        x -= total
    for ch, wch in zip(text, widths):
        draw.text((x, y), ch, font=fnt, fill=fill, anchor="la")
        x += wch + tracking
    return total


def star(draw, cx, cy, r, fill):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.42
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    draw.polygon(pts, fill=fill)


def ribbon(draw, cx, y, w):
    """Green-white-green wavy ribbon (three stacked sine bands)."""
    n = 120
    xs = [cx - w / 2 + w * i / n for i in range(n + 1)]
    for k, col in enumerate([(0, 135, 81), (255, 255, 255), (0, 135, 81)]):
        off = (k - 1) * 13
        pts = [(x, y + off + 10 * math.sin(2 * math.pi * (x - (cx - w / 2)) / (w * 0.55)))
               for x in xs]
        draw.line(pts, fill=col, width=13, joint="curve")


def white_glow(img, cx, cy, rx, ry, alpha=80):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(255, 255, 255, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(70))
    img.alpha_composite(layer)


# ------------------------------------------------------------- value icons
def icon_unity(d, cx, cy, s, col):
    for dx, dy, r in ((-16, -4, 9), (0, -9, 10), (16, -4, 9)):
        d.ellipse([cx + dx - r, cy + dy - r, cx + dx + r, cy + dy + r], outline=col, width=3)
    d.arc([cx - 26, cy + 2, cx - 6, cy + 26], 200, 340, fill=col, width=3)
    d.arc([cx - 10, cy - 2, cx + 10, cy + 26], 200, 340, fill=col, width=3)
    d.arc([cx + 6, cy + 2, cx + 26, cy + 26], 200, 340, fill=col, width=3)


def icon_sprout(d, cx, cy, s, col):
    d.line([(cx, cy + 22), (cx, cy - 12)], fill=col, width=3)
    d.ellipse([cx - 24, cy - 22, cx - 4, cy - 6], outline=col, width=3)   # left leaf
    d.ellipse([cx + 4, cy - 22, cx + 24, cy - 6], outline=col, width=3)    # right leaf
    d.line([(cx, cy + 22), (cx - 14, cy + 22)], fill=col, width=3)
    d.line([(cx, cy + 22), (cx + 14, cy + 22)], fill=col, width=3)


def icon_dove(d, cx, cy, s, col):
    # olive branch: curved stem + paired leaves (reads clearly at small size)
    d.arc([cx - 22, cy - 24, cx + 22, cy + 20], 200, 340, fill=col, width=3)
    for t, flip in ((0.25, 1), (0.5, -1), (0.75, 1)):
        ang = math.radians(200 + t * 140)
        lx = cx + 22 * math.cos(ang)
        ly = cy - 2 + 22 * math.sin(ang) * 0.8
        d.ellipse([lx - 9, ly - 5, lx + 9, ly + 5], outline=col, width=3)


def icon_chart(d, cx, cy, s, col):
    for i, h in enumerate((14, 24, 34)):
        x0 = cx - 20 + i * 14
        d.rectangle([x0, cy + 18 - h, x0 + 10, cy + 18], outline=col, width=3)
    d.line([(cx - 24, cy + 2), (cx + 22, cy - 22)], fill=col, width=3)
    d.line([(cx + 22, cy - 22), (cx + 10, cy - 20)], fill=col, width=3)
    d.line([(cx + 22, cy - 22), (cx + 20, cy - 10)], fill=col, width=3)


def icon_heart(d, cx, cy, s, col):
    r = 11
    d.ellipse([cx - 2 * r, cy - r - 4, cx, cy + r - 4], outline=col, width=3)
    d.ellipse([cx, cy - r - 4, cx + 2 * r, cy + r - 4], outline=col, width=3)
    d.polygon([(cx - 2 * r + 2, cy), (cx + 2 * r - 2, cy), (cx, cy + 22)],
              outline=col, width=3)


ICONS = [
    ("UNITY", icon_unity),
    ("PROSPERITY", icon_sprout),
    ("PEACE", icon_dove),
    ("DEVELOPMENT", icon_chart),
    ("A BRIGHTER\nTOMORROW", icon_heart),
]


def brush_banner(d, cx, y0, w, h, text, fnt, text_fill):
    """White brush-stroke bar with jittered edges."""
    top, bot = [], []
    n = 160
    for i in range(n + 1):
        x = cx - w / 2 + w * i / n
        jt = random.uniform(-4, 4)
        jt2 = random.uniform(-4, 4)
        top.append((x, y0 + jt))
        bot.append((x, y0 + h + jt2))
    d.polygon(top + bot[::-1], fill=WHITE)
    tw = d.textlength(text, font=fnt)
    d.text((cx - tw / 2, y0 + (h - 30) / 2), text, font=fnt, fill=text_fill)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bg", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    bg = Image.open(a.bg).convert("RGB").resize((SIZE, SIZE), Image.LANCZOS)
    img = bg.convert("RGBA")
    d = ImageDraw.Draw(img)

    # bright wash behind the type block (as in the reference)
    white_glow(img, 560, 500, 400, 340, alpha=85)
    white_glow(img, 540, 800, 430, 210, alpha=70)
    white_glow(img, 540, 815, 460, 175, alpha=105)
    d = ImageDraw.Draw(img)

    # top-right heritage script
    f_script_sm = font("DancingScript-Bold.ttf", 36)
    for i, line in enumerate(("Our Heritage,", "Our Pride,", "Our Future")):
        tracked(d, (905, 52 + i * 44), line, f_script_sm, DARK, anchor="ma")
    d.line([(830, 200), (980, 200)], fill=(0, 135, 81, 255), width=4)

    # stars + HAPPY
    for sx in (490, 540, 590):
        star(d, sx, 260, 13, DARK)
    f_happy = font("BarlowSemiCondensed-SemiBold.ttf", 38)
    tracked(d, (540, 284), "HAPPY", f_happy, DARK, tracking=22)

    # giant 67TH
    f_num = font("PlayfairDisplay-Black.ttf", 195)
    d.text((435, 318), "67", font=f_num, fill=DARK, anchor="la")
    w67 = d.textlength("67", font=f_num)
    f_th = font("PlayfairDisplay-Black.ttf", 60)
    d.text((435 + w67 + 12, 340), "TH", font=f_th, fill=DARK, anchor="la")

    # ribbon swoosh
    ribbon(d, 560, 560, 380)

    # INDEPENDENCE DAY
    f_head = font("PlayfairDisplay-Black.ttf", 58)
    tracked(d, (540, 596), "INDEPENDENCE DAY", f_head, DARK, tracking=2)

    # — NIGERIA —
    f_ng = font("PlayfairDisplay-Black.ttf", 40)
    tracked(d, (540, 664), "NIGERIA", f_ng, (0, 135, 81), tracking=18)
    d.line([(250, 686), (400, 686)], fill=DARK + (255,), width=3)
    d.line([(680, 686), (830, 686)], fill=DARK + (255,), width=3)

    # date
    f_date = font("BarlowSemiCondensed-SemiBold.ttf", 26)
    tracked(d, (540, 722), "1 OCTOBER 1960 \u2013 2027", f_date, (0, 135, 81), tracking=8)

    # message
    f_msg = font("Barlow-Regular.ttf", 24)
    msg = ("Today we celebrate 67 years of freedom, resilience and",
           "progress. We honour the heroes who fought for our",
           "independence and we recommit to building a greater",
           "Nigeria \u2014 stronger, united and full of hope.")
    my = 764
    for line in msg:
        tracked(d, (540, my), line, f_msg, INK, anchor="ma")
        my += 33

    # script accent
    f_script = font("DancingScript-Bold.ttf", 44)
    tracked(d, (540, 894), "One Nation. One People. One Nigeria.", f_script, DARK, anchor="ma")

    # bottom band with wavy top edge
    band_y = 945
    n = 120
    wave = [(i * SIZE / n, band_y + 10 * math.sin(2 * math.pi * i / n * 1.5)) for i in range(n + 1)]
    d.polygon(wave + [(SIZE, SIZE), (0, SIZE)], fill=BAND)

    # flag-fabric sweeps in the bottom corners (behind the icons)
    for k, col in enumerate([(0, 135, 81), (255, 255, 255), (0, 135, 81)]):
        inset = k * 30
        d.arc([-190 + inset, 890 + inset, 190 - inset, 1270 - inset],
              180, 270, fill=col, width=26)
        d.arc([890 + inset, 890 + inset, 1270 - inset, 1270 - inset],
              270, 360, fill=col, width=26)

    # value icons (drawn large, then scaled down for crisp thin lines)
    f_lab = font("BarlowSemiCondensed-SemiBold.ttf", 14)
    for i, (label, fn) in enumerate(ICONS):
        cx = 210 + i * 165
        layer = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
        dl = ImageDraw.Draw(layer)
        fn(dl, 60, 60, 38, WHITE)
        layer = layer.resize((72, 72), Image.LANCZOS)
        img.alpha_composite(layer, (cx - 36, 944))
        d = ImageDraw.Draw(img)
        ly = 1000
        for ln in label.split("\n"):
            tracked(d, (cx, ly), ln, f_lab, WHITE, tracking=2, anchor="ma")
            ly += 18

    # brush banner
    f_brush = font("Barlow-Bold.ttf", 20)
    brush_banner(d, 540, 1022, 520, 36, "HAPPY INDEPENDENCE DAY, NIGERIA!", f_brush, DARK)

    # brand
    f_brand = font("BarlowSemiCondensed-SemiBold.ttf", 14)
    tracked(d, (540, 1056), "nairaview.com", f_brand, (255, 255, 255, 175), tracking=5)

    img.convert("RGB").save(a.out, quality=92)
    print("wrote", a.out)


if __name__ == "__main__":
    sys.exit(main())
