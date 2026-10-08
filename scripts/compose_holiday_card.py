#!/usr/bin/env python3
"""Professional holiday card compositor (the 'Photoshop' step).

Takes a photographic background (no text) and lays out designer-grade
typography with PIL: letterspaced kicker, condensed-bold headline,
gold rule, message, and brand footer. Legibility scrims included.

Usage:
    python3 compose_holiday_card.py --bg <bg.jpg> --out <card.png> \
        --kicker "INDEPENDENCE DAY · 1 OCTOBER 2027" \
        --headline "Happy Independence Day,|Nigeria!" \
        --message "67 years strong. ..." [--headline-size 118]
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "assets", "fonts")

GOLD = (201, 162, 39)
WHITE = (255, 255, 255)
SOFT = (215, 226, 218)
MUTED = (157, 179, 164)

SIZE = 1080


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def draw_letterspaced(draw, xy, text, fnt, fill, tracking=0, anchor="ma"):
    """Draw text with manual letter tracking (PIL has no native tracking)."""
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


def text_with_shadow(img, xy, text, fnt, fill, tracking=0, anchor="ma",
                     shadow_alpha=160, shadow_off=(0, 4)):
    """Text with a soft drop shadow for depth."""
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(sh)
    draw_letterspaced(d, (xy[0] + shadow_off[0], xy[1] + shadow_off[1]),
                      text, fnt, (0, 0, 0, shadow_alpha), tracking, anchor)
    sh = sh.filter(ImageFilter.GaussianBlur(6))
    img.alpha_composite(sh)
    d = ImageDraw.Draw(img)
    draw_letterspaced(d, xy, text, fnt, fill + (255,), tracking, anchor)


def scrim(img, top_frac=0.42, max_alpha=215):
    """Dark gradient scrim rising from the bottom for type legibility."""
    w, h = img.size
    overlay = Image.new("L", (1, h), 0)
    px = overlay.load()
    start = int(h * top_frac)
    for y in range(start, h):
        t = (y - start) / (h - start)
        px[0, y] = int(max_alpha * (t ** 1.6))
    overlay = overlay.resize((w, h))
    black = Image.new("RGBA", img.size, (2, 20, 16, 255))
    img.alpha_composite(Image.composite(black, Image.new("RGBA", img.size, (0, 0, 0, 0)), overlay))
    # gentle top scrim for the kicker
    overlay2 = Image.new("L", (1, h), 0)
    px = overlay2.load()
    for y in range(0, int(h * 0.16)):
        px[0, y] = int(120 * (1 - y / (h * 0.16)))
    overlay2 = overlay2.resize((w, h))
    img.alpha_composite(Image.composite(black, Image.new("RGBA", img.size, (0, 0, 0, 0)), overlay2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bg", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--kicker", required=True)
    ap.add_argument("--headline", required=True, help="lines separated by |")
    ap.add_argument("--message", required=True)
    ap.add_argument("--headline-size", type=int, default=120)
    ap.add_argument("--brand", default="nairaview.com")
    ap.add_argument("--tagline", default="THE NIGERIAN EXCHANGE, DECODED DAILY")
    a = ap.parse_args()

    bg = Image.open(a.bg).convert("RGB")
    # center-crop to square
    side = min(bg.size)
    left = (bg.size[0] - side) // 2
    top = (bg.size[1] - side) // 2
    bg = bg.crop((left, top, left + side, top + side)).resize((SIZE, SIZE), Image.LANCZOS)
    img = bg.convert("RGBA")
    scrim(img)

    # kicker
    f_kick = font("BarlowSemiCondensed-SemiBold.ttf", 34)
    text_with_shadow(img, (SIZE // 2, 78), a.kicker, f_kick, GOLD, tracking=10)

    # headline (condensed bold, stacked)
    f_head = font("BarlowSemiCondensed-Bold.ttf", a.headline_size)
    y = 470
    for line in a.headline.split("|"):
        text_with_shadow(img, (SIZE // 2, y), line.strip(), f_head, WHITE,
                         shadow_alpha=200, shadow_off=(0, 6))
        y += int(a.headline_size * 1.06)

    # gold rule
    d = ImageDraw.Draw(img)
    rule_y = y + 8
    d.line([(SIZE // 2 - 60, rule_y), (SIZE // 2 + 60, rule_y)], fill=GOLD + (255,), width=5)

    # message
    f_msg = font("Barlow-Regular.ttf", 35)
    my = rule_y + 48
    for line in a.message.split("|"):
        d = ImageDraw.Draw(img)
        draw_letterspaced(d, (SIZE // 2, my), line.strip(), f_msg, SOFT + (255,), anchor="ma")
        my += 52

    # brand footer
    f_brand = font("Barlow-Bold.ttf", 42)
    text_with_shadow(img, (SIZE // 2, SIZE - 105), a.brand, f_brand, GOLD, shadow_alpha=140)
    f_tag = font("Barlow-Medium.ttf", 21)
    d = ImageDraw.Draw(img)
    draw_letterspaced(d, (SIZE // 2, SIZE - 48), a.tagline, f_tag, MUTED + (255,),
                      tracking=6, anchor="ma")

    img.convert("RGB").save(a.out, quality=92)
    print("wrote", a.out)


if __name__ == "__main__":
    sys.exit(main())
