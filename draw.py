#!/usr/bin/env python3
"""Build-time renderer for the make.fun entry image.

Draws one hero ingredient - a ripe mango, cut open, glossy and juicy -
on a warm dark background, at 2048px and downscaled to 1024px.
Runs at BUILD time only; the shipped main.py never imports PIL.
"""
import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

random.seed(7)

S = 2048          # supersampled canvas
W = H = S
OUT = "entry.png"

# ---------- helpers -------------------------------------------------------
def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vgrad(size, top, bottom):
    """Vertical gradient image."""
    img = Image.new("RGB", (1, size[1]))
    px = img.load()
    for y in range(size[1]):
        px[0, y] = lerp(top, bottom, y / max(1, size[1] - 1))
    return img.resize(size)


def radial_glow(size, centre, radius, colour, peak=200):
    """Soft radial glow on black, to be screen-blended."""
    glow = Image.new("L", size, 0)
    d = ImageDraw.Draw(glow)
    steps = 48
    for i in range(steps, 0, -1):
        t = i / steps
        r = radius * t
        a = int(peak * (1 - t) ** 1.6)
        d.ellipse([centre[0] - r, centre[1] - r, centre[0] + r, centre[1] + r],
                  fill=a)
    glow = glow.filter(ImageFilter.GaussianBlur(radius * 0.06))
    solid = Image.new("RGB", size, colour)
    out = Image.new("RGB", size, (0, 0, 0))
    out.paste(solid, (0, 0), glow)
    return out


def screen(base, layer):
    """Screen blend: 255 - (255-a)(255-b)/255."""
    import numpy as np
    a = np.asarray(base).astype(np.float32)
    b = np.asarray(layer).astype(np.float32)
    return Image.fromarray((255 - (255 - a) * (255 - b) / 255).astype("uint8"))


# ---------- background ----------------------------------------------------
img = vgrad((W, H), (36, 17, 6), (72, 33, 10))
img = screen(img, radial_glow((W, H), (1024, 1080), 1250, (150, 72, 18), 170))
img = screen(img, radial_glow((W, H), (1024, 950), 700, (90, 40, 8), 90))

# soft table shadow under the mango
shadow = Image.new("L", (W, H), 0)
ds = ImageDraw.Draw(shadow)
ds.ellipse([340, 1700, 1720, 1960], fill=110)
shadow = shadow.filter(ImageFilter.GaussianBlur(60))
img.paste(Image.new("RGB", (W, H), (12, 5, 2)), (0, 0), shadow)

# ---------- mango half: ONE smooth body ------------------------------------
# Single ellipse body (slightly tilted feel via asymmetric gradient, not
# extra ellipses - overlapping shapes left visible seams).
mask = Image.new("L", (W, H), 0)
dm = ImageDraw.Draw(mask)
dm.ellipse([330, 520, 1710, 1840], fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(5))

cx, cy = 1020, 1150
flesh = Image.new("RGB", (W, H), (0, 0, 0))
fp = flesh.load()
for y in range(520, 1840):
    for x in range(330, 1710):
        dx = (x - cx) / 660.0
        dy = (y - cy) / 700.0
        r = math.sqrt(dx * dx + dy * dy)
        if r > 1.0:
            continue
        # deep orange heart, golden toward the rim, blush at top-left
        t = min(1.0, r)
        col = lerp((255, 108, 18), (255, 188, 58), t ** 0.75)
        blush = max(0.0, 1.0 - math.hypot((x - 700) / 420.0,
                                          (y - 700) / 420.0))
        col = lerp(col, (238, 84, 22), blush * 0.45)
        if y > 1680:
            col = lerp(col, (226, 94, 10), (y - 1680) / 180.0 * 0.5)
        fp[x, y] = col
flesh = flesh.filter(ImageFilter.GaussianBlur(4))
img.paste(flesh, (0, 0), mask)

# skin rim: outline derived from the mask itself (erode, subtract)
eroded = mask.filter(ImageFilter.MinFilter(31))
rim = Image.new("L", (W, H), 0)
rim_px = rim.load()
mask_px = mask.load()
er_px = eroded.load()
for y in range(H):
    for x in range(W):
        if mask_px[x, y] > 0 and er_px[x, y] == 0:
            rim_px[x, y] = 255
rim = rim.filter(ImageFilter.GaussianBlur(8))
img.paste(Image.new("RGB", (W, H), (206, 66, 14)), (0, 0), rim)

# ---------- stone hollow: where the pit was --------------------------------
hollow = Image.new("L", (W, H), 0)
dh = ImageDraw.Draw(hollow)
dh.ellipse([900, 820, 1140, 1060], fill=150)
hollow = hollow.filter(ImageFilter.GaussianBlur(36))
img.paste(Image.new("RGB", (W, H), (198, 82, 8)), (0, 0), hollow)

# ---------- fibre streaks: few, faint, near the rim only -------------------
fibres = Image.new("RGBA", (W, H), (0, 0, 0, 0))
df = ImageDraw.Draw(fibres)
for k in range(42):
    ang = (k / 42.0) * math.tau + random.uniform(-0.04, 0.04)
    r0 = 380 + random.uniform(0, 80)
    r1 = 620 + random.uniform(0, 60)
    x0 = cx + r0 * math.cos(ang)
    y0 = cy + r0 * math.sin(ang) * 0.95
    x1 = cx + r1 * math.cos(ang)
    y1 = cy + r1 * math.sin(ang) * 0.95
    df.line([x0, y0, x1, y1], fill=(235, 120, 22, 34), width=4)
fibres = fibres.filter(ImageFilter.GaussianBlur(4))
img = Image.alpha_composite(img.convert("RGBA"), fibres).convert("RGB")

# ---------- gloss: one soft highlight, upper left --------------------------
img = screen(img, radial_glow((W, H), (720, 680), 480, (255, 215, 140), 120))
img = screen(img, radial_glow((W, H), (1420, 1520), 340, (255, 195, 100), 80))

# juice droplets on the flesh
drop_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
dd = ImageDraw.Draw(drop_layer)
for _ in range(22):
    ang = random.uniform(0, math.tau)
    rr = random.uniform(260, 600)
    x = cx + rr * math.cos(ang)
    y = cy + rr * math.sin(ang) * 0.95
    r = random.uniform(10, 26)
    dd.ellipse([x - r, y - r * 0.8, x + r, y + r * 0.8],
               fill=(255, 226, 140, 110))
    dd.ellipse([x - r * 0.45, y - r * 0.55, x + r * 0.1, y - r * 0.1],
               fill=(255, 255, 240, 180))
drop_layer = drop_layer.filter(ImageFilter.GaussianBlur(2))
img = Image.alpha_composite(img.convert("RGBA"), drop_layer).convert("RGB")

# ---------- mango cubes, bottom right --------------------------------------
cube_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
dc = ImageDraw.Draw(cube_layer)
cubes = [(1420, 1560, 210), (1620, 1690, 170), (1260, 1720, 150)]
for (x, y, s) in cubes:
    dc.rounded_rectangle([x, y, x + s, y + s], radius=34,
                         fill=(255, 176, 44, 255))
    dc.rounded_rectangle([x, y, x + s, y + s], radius=34,
                         outline=(214, 96, 12, 255), width=6)
    for i in range(1, 4):
        t = i / 4.0
        dc.line([x + s * t, y + 8, x + s * t, y + s - 8],
                fill=(226, 110, 16, 200), width=5)
        dc.line([x + 8, y + s * t, x + s - 8, y + s * t],
                fill=(226, 110, 16, 200), width=5)
    dc.ellipse([x + s * 0.18, y + s * 0.14, x + s * 0.42, y + s * 0.34],
               fill=(255, 240, 180, 210))
cube_layer = cube_layer.filter(ImageFilter.GaussianBlur(1))
img = Image.alpha_composite(img.convert("RGBA"), cube_layer).convert("RGB")

csh = Image.new("L", (W, H), 0)
dcs = ImageDraw.Draw(csh)
for (x, y, s) in cubes:
    dcs.ellipse([x - 10, y + s - 14, x + s + 10, y + s + 26], fill=90)
csh = csh.filter(ImageFilter.GaussianBlur(18))
img.paste(Image.new("RGB", (W, H), (10, 4, 2)), (0, 0), csh)

# ---------- juice puddle tucked under the mango base -----------------------
puddle = Image.new("L", (W, H), 0)
dp = ImageDraw.Draw(puddle)
dp.ellipse([700, 1820, 1340, 1920], fill=140)
puddle = puddle.filter(ImageFilter.GaussianBlur(14))
img.paste(Image.new("RGB", (W, H), (255, 170, 40)), (0, 0), puddle)
dp2 = ImageDraw.Draw(img)
dp2.ellipse([820, 1840, 1220, 1880], fill=(255, 214, 110))

# ---------- vignette -------------------------------------------------------
vig = Image.new("L", (W, H), 0)
dv = ImageDraw.Draw(vig)
dv.rectangle([0, 0, W, H], fill=80)
dv.ellipse([-220, -220, W + 220, H + 220], fill=0)
vig = vig.filter(ImageFilter.GaussianBlur(220))
img.paste(Image.new("RGB", (W, H), (16, 7, 3)), (0, 0), vig)

# ---------- text: one short line, clean serif bold -------------------------
font = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 118)
text = "Taste the mango."
draw = ImageDraw.Draw(img)
bbox = draw.textbbox((0, 0), text, font=font)
tw = bbox[2] - bbox[0]
tx = (W - tw) // 2
ty = 210
draw.text((tx + 4, ty + 5), text, font=font, fill=(20, 8, 2))
draw.text((tx, ty), text, font=font, fill=(255, 236, 200))

# ---------- downscale + save ----------------------------------------------
final = img.resize((1024, 1024), Image.LANCZOS)
final.save(OUT, format="PNG", optimize=True)
print("saved", OUT, final.size)
