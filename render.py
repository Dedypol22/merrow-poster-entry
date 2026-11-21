#!/usr/bin/env python3
"""Render MERROW — travel poster for the town that sails on a whale.
PIL only, deterministic (fixed seed). Writes /tmp/merrow/poster.png (768x1024)."""
import math, os, random, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 768, 1024
SS = 2  # supersample
w, h = W * SS, H * SS
rng = random.Random(7)

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def vgrad(img, top, mid, bot, mid_y=0.55):
    d = ImageDraw.Draw(img)
    for y in range(img.height):
        t = y / img.height
        if t < mid_y:
            c = lerp(top, mid, t / mid_y)
        else:
            c = lerp(mid, bot, (t - mid_y) / (1 - mid_y))
        d.line([(0, y), (img.width, y)], fill=c)

img = Image.new("RGB", (w, h))
# sky: deep indigo -> violet -> amber at horizon (y=640/1024)
sky = Image.new("RGB", (w, int(h * 0.625)))
vgrad(sky, (26, 38, 74), (96, 62, 112), (242, 166, 90), mid_y=0.62)
img.paste(sky, (0, 0))
# sea: deep teal -> darker
sea = Image.new("RGB", (w, h - int(h * 0.625)))
vgrad(sea, (38, 84, 110), (24, 56, 84), (14, 32, 54), mid_y=0.5)
img.paste(sea, (0, int(h * 0.625)))

d = ImageDraw.Draw(img, "RGBA")
HORIZ = int(h * 0.625)

# stars in the upper sky
for _ in range(110):
    x = rng.randint(10, w - 10)
    y = rng.randint(10, int(h * 0.30))
    r = rng.choice([1, 1, 2, 2, 3]) * SS // 2
    a = rng.randint(90, 210)
    d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 244, 214, a))

# soft warm clouds near horizon
for cx, cy, cw, chh, a in [(200, 400, 280, 16, 34), (560, 350, 320, 18, 30),
                            (380, 470, 360, 14, 38), (120, 300, 200, 12, 26)]:
    cloud = Image.new("RGBA", (cw * SS, chh * SS * 2), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cloud)
    cd.ellipse([0, 0, cw * SS, chh * SS * 2], fill=(255, 190, 130, a))
    cloud = cloud.filter(ImageFilter.GaussianBlur(12 * SS))
    img.paste(cloud, (cx * SS - cw * SS // 2, cy * SS - chh * SS), cloud)
d = ImageDraw.Draw(img, "RGBA")

# sun: halo + disc, low over the horizon, right of centre
sx, sy, sr = 525 * SS, 545 * SS, 46 * SS
for rr, a in [(150, 18), (120, 28), (95, 45), (70, 70)]:
    d.ellipse([sx - rr, sy - rr, sx + rr, sy + rr], fill=(255, 214, 130, a))
d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(255, 233, 168, 255))

# sun glitter path on the sea
for _ in range(240):
    x = int(rng.gauss(540, 70)) * SS
    y = rng.randint(HORIZ + 8, h - 20)
    ln = rng.randint(6, 26) * SS
    a = max(30, int(200 * (1 - (y - HORIZ) / (h - HORIZ)) * rng.random()))
    d.line([(x - ln // 2, y), (x + ln // 2, y)], fill=(255, 214, 140, a), width=2 * SS)

# --- the whale: back arches out of the sea, head left, tail right ---
def back_y(x):
    t = (x - 70) / 630
    if t < 0 or t > 1:
        return HORIZ
    return HORIZ - int(math.sin(t * math.pi) ** 0.8 * 95 * SS)

def bez(p0, p1, p2, n=16):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])
            for t in [i / n for i in range(n + 1)]]

whale = Image.new("RGBA", (w, h), (0, 0, 0, 0))
wd = ImageDraw.Draw(whale)
top = []
for x in range(70 * SS, 701 * SS, 4):
    t = (x / SS - 70) / 630
    y = HORIZ - int((math.sin(t * math.pi) ** 0.8) * 95 * SS)
    top.append((x, y))
# body: back curve, then a gentle wave for the waterline bottom
bottom = [(x, HORIZ + 14 * SS + int(math.sin(x / (w / 5.0)) * 4 * SS))
          for x in range(700 * SS, 69 * SS, -4)]
wd.polygon(top + bottom, fill=(35, 48, 72, 255))
# head: merged bump at the left end of the back
wd.ellipse([62 * SS, HORIZ - 58 * SS, 158 * SS, HORIZ + 16 * SS], fill=(35, 48, 72, 255))
# tail fluke: broad two-lobed shape rising from the tail stalk, base sunk
# deep into the body so it reads as one connected shape
fluke = ([(612 * SS, HORIZ + 6 * SS)] +
         bez((612 * SS, HORIZ + 6 * SS), (668 * SS, HORIZ - 96 * SS), (716 * SS, HORIZ - 118 * SS)) +
         bez((716 * SS, HORIZ - 118 * SS), (738 * SS, HORIZ - 104 * SS), (722 * SS, HORIZ - 82 * SS)) +
         bez((722 * SS, HORIZ - 82 * SS), (706 * SS, HORIZ - 62 * SS), (700 * SS, HORIZ - 46 * SS)) +
         bez((700 * SS, HORIZ - 46 * SS), (716 * SS, HORIZ - 40 * SS), (700 * SS, HORIZ - 22 * SS)) +
         [(668 * SS, HORIZ + 6 * SS)])
wd.polygon(fluke, fill=(35, 48, 72, 255))
# whale eye: one small warm dot on the head
wd.ellipse([(96 - 3) * SS, (HORIZ // SS - 34 - 3) * SS,
            (96 + 3) * SS, (HORIZ // SS - 34 + 3) * SS], fill=(255, 224, 150, 255))
# gentle smile line under the head
wd.arc([78 * SS, (HORIZ // SS - 30) * SS, 150 * SS, (HORIZ // SS - 2) * SS],
       15, 105, fill=(16, 22, 40, 200), width=2 * SS)
# spout: tight fan of droplets right above the head
for ox, oy, r in [(-8, -14, 3), (0, -22, 4), (8, -14, 3), (-14, -6, 2), (14, -6, 2)]:
    wd.ellipse([(105 + ox - r) * SS, (HORIZ // SS - 56 + oy - r) * SS,
                (105 + ox + r) * SS, (HORIZ // SS - 56 + oy + r) * SS],
               fill=(255, 250, 235, 230))
# top-edge highlight along the back, sitting just inside the body
for i in range(len(top) - 1):
    x0, y0 = top[i]
    x1, y1 = top[i + 1]
    wd.line([(x0, y0 + 3 * SS), (x1, y1 + 3 * SS)], fill=(140, 160, 190, 220), width=2 * SS)
img.paste(whale, (0, 0), whale)
d = ImageDraw.Draw(img, "RGBA")
# foam line where the whale meets the sea
for x in range(60 * SS, 710 * SS, 14):
    y = HORIZ + 16 * SS + int(math.sin(x / (w / 5.0)) * 4 * SS)
    ln = rng.randint(4, 10) * SS
    d.line([(x, y), (x + ln, y)], fill=(235, 242, 250, 150), width=2 * SS)

# --- tiny lantern town along the whale's back ---
def town_y(x):
    t = (x - 70) / 630
    return HORIZ - int((math.sin(max(0, min(1, t)) * math.pi) ** 0.8) * 95 * SS)

houses = [(120, 15, 18), (165, 12, 15), (205, 16, 20), (250, 13, 16),
          (295, 17, 21), (430, 14, 17), (470, 16, 20), (515, 13, 16),
          (555, 15, 19), (595, 12, 15)]
for hx, hw, hh in houses:
    by = town_y(hx)
    x0, x1 = (hx - hw // 2) * SS, (hx + hw // 2) * SS
    y1 = by
    y0 = by - hh * SS
    d.rectangle([x0, y0, x1, y1], fill=(24, 30, 48, 255))
    d.polygon([(x0 - 2 * SS, y0), (hx * SS, y0 - 8 * SS), (x1 + 2 * SS, y0)],
              fill=(52, 34, 44, 255))
    # warm glowing windows
    for wx in (hx - hw // 4, hx + hw // 4):
        d.rectangle([(wx - 2) * SS, (y0 // SS + hh // 3) * SS,
                     (wx + 2) * SS, (y0 // SS + hh // 3 + 4) * SS],
                    fill=(255, 214, 138, 255))
    d.ellipse([(hx - 2) * SS, (y0 // SS - 3) * SS, (hx + 2) * SS, (y0 // SS + 1) * SS],
              fill=(255, 214, 138, 180))

# lighthouse on the whale's peak (x~380)
lx = 380 * SS
ly = town_y(380)
# light beam sweeping right-down
beam = Image.new("RGBA", (w, h), (0, 0, 0, 0))
bd = ImageDraw.Draw(beam)
bd.polygon([(lx + 8 * SS, ly - 52 * SS), (700 * SS, ly - 6 * SS),
            (700 * SS, ly + 26 * SS), (lx + 8 * SS, ly - 40 * SS)],
           fill=(255, 224, 150, 110))
beam = beam.filter(ImageFilter.GaussianBlur(6 * SS))
img.paste(beam, (0, 0), beam)
d = ImageDraw.Draw(img, "RGBA")
d.rectangle([lx - 7 * SS, ly - 52 * SS, lx + 7 * SS, ly], fill=(245, 240, 225, 255))
d.rectangle([lx - 7 * SS, ly - 40 * SS, lx + 7 * SS, ly - 30 * SS], fill=(198, 70, 62, 255))
d.rectangle([lx - 7 * SS, ly - 20 * SS, lx + 7 * SS, ly - 10 * SS], fill=(198, 70, 62, 255))
d.rectangle([lx - 10 * SS, ly - 58 * SS, lx + 10 * SS, ly - 52 * SS], fill=(24, 30, 48, 255))
d.ellipse([lx - 5 * SS, ly - 64 * SS, lx + 5 * SS, ly - 54 * SS], fill=(255, 214, 138, 255))
d.ellipse([lx - 12 * SS, ly - 70 * SS, lx + 12 * SS, ly - 48 * SS], fill=(255, 224, 150, 70))

# --- sailboats ---
def boat(bx, by, s, sail=(250, 240, 214)):
    d.polygon([(bx * SS, by * SS), ((bx + 26 * s) * SS, by * SS),
               ((bx + 20 * s) * SS, (by + 9 * s) * SS), ((bx + 6 * s) * SS, (by + 9 * s) * SS)],
              fill=(20, 26, 42, 255))
    d.line([(bx + 13 * s) * SS, by * SS, (bx + 13 * s) * SS, (by - 26 * s) * SS],
           fill=(20, 26, 42, 255), width=2 * SS)
    d.polygon([((bx + 14 * s) * SS, (by - 25 * s) * SS), ((bx + 14 * s) * SS, (by - 2 * s) * SS),
               ((bx + 30 * s) * SS, (by - 2 * s) * SS)], fill=sail + (255,))
    d.polygon([((bx + 12 * s) * SS, (by - 22 * s) * SS), ((bx + 12 * s) * SS, (by - 2 * s) * SS),
               ((bx + 1 * s) * SS, (by - 2 * s) * SS)], fill=(240, 200, 150, 255))
boat(150, 800, 1.2)
boat(610, 880, 1.0)

# gulls
for gx, gy, gs in [(180, 260, 10), (230, 300, 8), (600, 240, 9), (650, 290, 7)]:
    d.arc([(gx - gs) * SS, (gy - gs // 2) * SS, gx * SS, (gy + gs // 2) * SS],
          200, 340, fill=(30, 34, 52, 220), width=2 * SS)
    d.arc([gx * SS, (gy - gs // 2) * SS, (gx + gs) * SS, (gy + gs // 2) * SS],
          200, 340, fill=(30, 34, 52, 220), width=2 * SS)

# foreground wave silhouettes
d.polygon([(0, h), (0, h - 46 * SS)] +
          [(x, h - 46 * SS + int(math.sin(x / (w / 6.0)) * 14 * SS)) for x in range(0, w, 8)] +
          [(w, h)], fill=(12, 20, 36, 255))
d.polygon([(0, h), (0, h - 20 * SS)] +
          [(x, h - 20 * SS + int(math.sin(x / (w / 5.0) + 2) * 8 * SS)) for x in range(0, w, 8)] +
          [(w, h)], fill=(8, 14, 26, 255))

# --- type ---
def tracked(font, text, tracking):
    total = 0
    widths = []
    for ch in text:
        wdth = font.getlength(ch)
        widths.append(wdth)
        total += wdth + tracking
    return total - tracking, widths

title_font = ImageFont.truetype(SERIF, 118 * SS)
desc_font = ImageFont.truetype(SANS, 25 * SS)
CREAM = (255, 243, 214, 255)
SHADOW = (16, 22, 44, 220)

title = "MERROW"
tw, widths = tracked(title_font, title, 10 * SS)
tx = (w - tw) // 2
ty = 78 * SS
for ox, oy, col in [(3 * SS, 4 * SS, SHADOW), (0, 0, CREAM)]:
    x = tx + ox
    for ch, wdth in zip(title, widths):
        d.text((x, ty + oy), ch, font=title_font, fill=col)
        x += wdth + 10 * SS

desc = "THE TOWN THAT SAILS ON A WHALE"
dw, dwidths = tracked(desc_font, desc, 6 * SS)
dx = (w - dw) // 2
dy = 208 * SS
x = dx
for ch, wdth in zip(desc, dwidths):
    d.text((x, dy), ch, font=desc_font, fill=CREAM)
    x += wdth + 6 * SS
# rules flanking the descriptor
ry = dy + 14 * SS
d.line([(dx - 52 * SS, ry), (dx - 14 * SS, ry)], fill=CREAM, width=2 * SS)
d.line([(dx + dw + 14 * SS, ry), (dx + dw + 52 * SS, ry)], fill=CREAM, width=2 * SS)

# thin poster border
d.rectangle([26 * SS, 26 * SS, w - 26 * SS, h - 26 * SS], outline=(255, 243, 214, 160), width=3 * SS)

img = img.resize((W, H), Image.LANCZOS)
_repo = sys.argv[1] if len(sys.argv) > 1 else "."
img.save("/tmp/merrow-poster.png", optimize=True)
img.save(os.path.join(_repo, "poster.png"), optimize=True)
print("saved /tmp/merrow-poster.png", img.size)
import os
print("bytes:", os.path.getsize("/tmp/merrow-poster.png"))
