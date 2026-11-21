#!/usr/bin/env python3
"""VELMARA — a travel poster for a place that does not exist.

Draws a 768x1024 travel poster with the Python standard library only
(no Pillow, no numpy, no third-party packages) and writes it to
/output/entry.png. The PNG is encoded by hand with zlib.

Scene: the floating isles of Velmara at dusk — a ringed planet, a low
sun, one great floating island with a beacon spire, a waterfall pouring
into a sea of clouds, and the place name set large across the sky.
"""

import hashlib
import math
import os
import random
import struct
import sys
import zlib

W, H = 768, 1024
OUT = os.environ.get("ENTRY_OUTPUT", "/output/entry.png")

# ---------------------------------------------------------------- image buffer
img = [bytearray(W * 3) for _ in range(H)]


def lerp(a, b, t):
    return a + (b - a) * t


def sstep(a, b, x):
    t = (x - a) / (b - a)
    t = 0.0 if t < 0.0 else 1.0 if t > 1.0 else t
    return t * t * (3.0 - 2.0 * t)


# ---------------------------------------------------------------- primitives
def fill_span(y, x0, x1, col):
    if y < 0 or y >= H:
        return
    x0 = max(0, x0)
    x1 = min(W, x1)
    if x0 >= x1:
        return
    img[y][x0 * 3:x1 * 3] = bytes(col) * (x1 - x0)


def blend_span(y, x0, x1, col, a):
    if y < 0 or y >= H:
        return
    x0 = max(0, x0)
    x1 = min(W, x1)
    if x0 >= x1 or a <= 0.0:
        return
    row = img[y]
    r, g, b = col
    ia = 1.0 - a
    for x in range(x0, x1):
        i = x * 3
        row[i] = int(row[i] * ia + r * a)
        row[i + 1] = int(row[i + 1] * ia + g * a)
        row[i + 2] = int(row[i + 2] * ia + b * a)


def fill_rect(x0, y0, x1, y1, col):
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(W, x1)
    y1 = min(H, y1)
    if x0 >= x1 or y0 >= y1:
        return
    row = bytes(col) * (x1 - x0)
    for y in range(y0, y1):
        img[y][x0 * 3:x1 * 3] = row


def fill_circle(cx, cy, r, col):
    r2 = r * r
    for y in range(max(0, cy - r), min(H, cy + r + 1)):
        dy = y - cy
        dx = int(math.sqrt(r2 - dy * dy))
        fill_span(y, cx - dx, cx + dx + 1, col)


def fill_circle_alpha(cx, cy, r, col, a):
    r2 = r * r
    for y in range(max(0, cy - r), min(H, cy + r + 1)):
        dy = y - cy
        dx = int(math.sqrt(r2 - dy * dy))
        blend_span(y, cx - dx, cx + dx + 1, col, a)


def fill_annulus(cx, cy, rx, ry, irx, iry, col, y_min=None, y_max=None):
    for y in range(max(0, cy - ry), min(H, cy + ry + 1)):
        if y_min is not None and y < y_min:
            continue
        if y_max is not None and y > y_max:
            continue
        t = (y - cy) / ry
        if abs(t) >= 1.0:
            continue
        ox = rx * math.sqrt(1.0 - t * t)
        ti = (y - cy) / iry
        if abs(ti) < 1.0:
            ix = irx * math.sqrt(1.0 - ti * ti)
            fill_span(y, int(cx - ox), int(cx - ix) + 1, col)
            fill_span(y, int(cx + ix), int(cx + ox) + 1, col)
        else:
            fill_span(y, int(cx - ox), int(cx + ox) + 1, col)


def fill_poly(pts, col):
    ys = [p[1] for p in pts]
    y0, y1 = max(0, min(ys)), min(H - 1, max(ys))
    n = len(pts)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            x0, yy0 = pts[i]
            x1, yy1 = pts[(i + 1) % n]
            if (yy0 <= y < yy1) or (yy1 <= y < yy0):
                t = (y - yy0) / (yy1 - yy0)
                xs.append(x0 + t * (x1 - x0))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            fill_span(y, int(xs[i]), int(xs[i + 1]) + 1, col)


def draw_line(x0, y0, x1, y1, col, w=2):
    steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(steps + 1):
        t = i / steps
        x = int(x0 + (x1 - x0) * t)
        y = int(y0 + (y1 - y0) * t)
        fill_rect(x - w // 2, y - w // 2, x + w // 2 + 1, y + w // 2 + 1, col)


# ---------------------------------------------------------------- 5x7 block font
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
}


def text_width(text, scale, spacing):
    return len(text) * (5 * scale + spacing) - spacing


def draw_text(text, x, y, scale, col, spacing):
    for ch in text:
        glyph = FONT.get(ch, FONT[" "])
        for r in range(7):
            row = glyph[r]
            for c in range(5):
                if row[c] == "1":
                    fill_rect(x + c * scale, y + r * scale,
                              x + (c + 1) * scale, y + (r + 1) * scale, col)
        x += 5 * scale + spacing


# ---------------------------------------------------------------- value noise
def make_grid(gw, gh, rng):
    return [[rng.random() for _ in range(gw + 1)] for _ in range(gh + 1)]


def vnoise(grid, gw, gh, nx, ny):
    xi = min(int(nx), gw - 1)
    yi = min(int(ny), gh - 1)
    xf = nx - xi
    yf = ny - yi
    u = xf * xf * (3.0 - 2.0 * xf)
    v = yf * yf * (3.0 - 2.0 * yf)
    a = grid[yi][xi]
    b = grid[yi][xi + 1]
    c = grid[yi + 1][xi]
    d = grid[yi + 1][xi + 1]
    return lerp(lerp(a, b, u), lerp(c, d, u), v)


# ---------------------------------------------------------------- scene
SKY_STOPS = [
    (0, (26, 20, 62)),
    (260, (66, 40, 100)),
    (470, (138, 66, 112)),
    (600, (214, 108, 88)),
    (700, (248, 168, 96)),
    (780, (252, 190, 120)),
    (1024, (238, 158, 96)),
]


def sky_rows():
    rows = []
    for y in range(H):
        for i in range(len(SKY_STOPS) - 1):
            y0, c0 = SKY_STOPS[i]
            y1, c1 = SKY_STOPS[i + 1]
            if y0 <= y <= y1:
                t = (y - y0) / (y1 - y0)
                rows.append((int(lerp(c0[0], c1[0], t)),
                             int(lerp(c0[1], c1[1], t)),
                             int(lerp(c0[2], c1[2], t))))
                break
        else:
            rows.append(SKY_STOPS[-1][1])
    return rows


def draw():
    rng = random.Random(20261121)
    sky = sky_rows()

    # 1. sky gradient
    for y in range(H):
        fill_span(y, 0, W, sky[y])

    # 2. stars in the upper sky
    for _ in range(150):
        x = rng.randrange(0, W)
        y = rng.randrange(0, 430)
        if (x - 565) ** 2 + (y - 215) ** 2 < 130 ** 2:
            continue
        b = rng.choice([150, 190, 220, 245])
        col = (b, b, min(255, b + 10))
        if rng.random() < 0.12:
            fill_rect(x - 2, y, x + 3, y + 1, col)
            fill_rect(x, y - 2, x + 1, y + 3, col)
        elif rng.random() < 0.3:
            fill_rect(x, y, x + 2, y + 2, col)
        else:
            fill_rect(x, y, x + 1, y + 1, col)

    # 3. low sun with a smooth glow, left of the island
    for r, a in ((210, 0.05), (185, 0.06), (160, 0.08), (135, 0.10),
                 (110, 0.13), (88, 0.16), (68, 0.20), (52, 0.24)):
        fill_circle_alpha(150, 640, r, (255, 190, 110), a)
    fill_circle(150, 640, 46, (255, 226, 150))
    fill_circle(150, 640, 34, (255, 240, 190))

    # 4. ringed planet, upper right
    px, py, pr = 565, 215, 76
    fill_annulus(px, py, 148, 30, 118, 21, (226, 186, 128))
    fill_circle(px, py, pr, (238, 208, 158))
    # soft bands across the disc
    for y in range(py - 30, py - 8):
        dy = y - py
        dx = int(math.sqrt(pr * pr - dy * dy))
        blend_span(y, px - dx, px + dx + 1, (222, 188, 138), 0.35)
    for y in range(py + 15, py + 36):
        dy = y - py
        dx = int(math.sqrt(pr * pr - dy * dy))
        blend_span(y, px - dx, px + dx + 1, (248, 224, 178), 0.30)
    # craters
    for cx, cy, cr in ((530, 190, 9), (600, 240, 7), (585, 180, 5)):
        fill_circle_alpha(cx, cy, cr, (205, 172, 120), 0.35)
    # front half of the ring passes in front of the disc
    fill_annulus(px, py, 148, 30, 118, 21, (226, 186, 128),
                 y_min=py + 1)

    # 5. (no second islet: one was tried here and it crowded the sun)

    # 6. the great floating island
    # rock body: tapered silhouette down to a point
    for y in range(575, 846):
        t = (y - 575) / 270.0
        half = 190.0 * (1.0 - t ** 1.4) + 8.0
        col = (int(lerp(122, 58, t)), int(lerp(88, 40, t)),
               int(lerp(74, 62, t)))
        fill_span(y, int(384 - half), int(384 + half) + 1, col)
    # rock facets for depth
    fill_poly([(220, 600), (330, 620), (300, 800), (232, 700)], (96, 66, 66))
    fill_poly([(508, 620), (544, 650), (478, 786), (448, 676)], (76, 50, 66))
    # meadow cap
    for y in range(558, 599):
        dy = (y - 578) / 20.0
        if abs(dy) >= 1.0:
            continue
        dx = 196.0 * math.sqrt(1.0 - dy * dy)
        fill_span(y, int(384 - dx), int(384 + dx) + 1, (150, 158, 84))
    for y in range(560, 580):
        dy = (y - 570) / 10.0
        if abs(dy) >= 1.0:
            continue
        dx = 180.0 * math.sqrt(1.0 - dy * dy)
        fill_span(y, int(384 - dx), int(384 + dx) + 1, (172, 178, 104))
    # trees on the meadow
    for tx in (240, 300, 470, 530):
        fill_poly([(tx, 556), (tx - 11, 584), (tx + 11, 584)], (52, 84, 58))
    # the beacon spire — the poster's one landmark
    fill_poly([(368, 580), (400, 580), (392, 392), (376, 392)],
              (216, 178, 128))
    fill_poly([(384, 392), (392, 392), (400, 580), (384, 580)],
              (188, 148, 102))
    for wy in (420, 460, 500, 540):
        fill_rect(381, wy, 387, wy + 7, (255, 214, 120))
    # beacon glow, orb and pennant
    fill_circle_alpha(384, 378, 26, (255, 210, 120), 0.35)
    fill_circle(384, 378, 12, (255, 222, 140))
    draw_line(384, 366, 384, 338, (60, 44, 66), 3)
    fill_poly([(384, 338), (410, 346), (384, 354)], (214, 84, 72))
    # waterfall pouring off the island's edge into the clouds
    fill_poly([(300, 712), (324, 712), (332, 802), (306, 802)],
              (206, 226, 238))
    draw_line(310, 716, 314, 800, (170, 200, 220), 2)
    draw_line(320, 716, 322, 800, (170, 200, 220), 2)

    # 7. sea of clouds along the bottom
    grid1 = make_grid(14, 5, rng)
    grid2 = make_grid(30, 11, rng)
    for y in range(775, H):
        fy = (y - 775) / 248.0
        row = img[y]
        base = sky[y]
        top_fade = min(1.0, (y - 775) / 45.0)
        for x in range(W):
            n = (0.65 * vnoise(grid1, 14, 5, x * 14.0 / W, fy * 5.0)
                 + 0.35 * vnoise(grid2, 30, 11, x * 30.0 / W, fy * 11.0))
            cov = sstep(0.42, 0.72, n) * top_fade * (0.7 + 0.3 * fy)
            if cov <= 0.01:
                continue
            t = sstep(0.4, 0.8, n)
            cr = int(214 + (252 - 214) * t)
            cg = int(170 + (232 - 170) * t)
            cb = int(140 + (200 - 140) * t)
            i = x * 3
            row[i] = int(row[i] * (1.0 - cov) + cr * cov)
            row[i + 1] = int(row[i + 1] * (1.0 - cov) + cg * cov)
            row[i + 2] = int(row[i + 2] * (1.0 - cov) + cb * cov)

    # 8. birds
    for bx, by in ((180, 300), (230, 330), (520, 420), (590, 380),
                   (640, 450), (300, 250)):
        draw_line(bx - 8, by, bx, by + 5, (40, 28, 60), 2)
        draw_line(bx, by + 5, bx + 8, by, (40, 28, 60), 2)

    # 9. double art-deco frame
    cream = (238, 224, 188)
    fill_rect(24, 24, 744, 28, cream)
    fill_rect(24, 996, 744, 1000, cream)
    fill_rect(24, 24, 28, 1000, cream)
    fill_rect(740, 24, 744, 1000, cream)
    fill_rect(34, 34, 734, 36, cream)
    fill_rect(34, 988, 734, 990, cream)
    fill_rect(34, 34, 36, 990, cream)
    fill_rect(732, 34, 734, 990, cream)

    # 10. the place name, set large across the sky
    title = "VELMARA"
    scale, spacing = 11, 12
    tx = (W - text_width(title, scale, spacing)) // 2
    ty = 66
    draw_text(title, tx + 5, ty + 6, scale, (18, 12, 44), spacing)
    draw_text(title, tx, ty, scale, (250, 240, 214), spacing)
    # ornament and subtitle
    gold = (235, 200, 130)
    draw_line(300, 168, 360, 168, gold, 2)
    draw_line(408, 168, 468, 168, gold, 2)
    fill_poly([(384, 158), (392, 168), (384, 178), (376, 168)], gold)
    sub = "ISLES ABOVE THE CLOUDS"
    ss, sp = 3, 5
    sx = (W - text_width(sub, ss, sp)) // 2
    # dark shadow first: the subtitle crosses the pale planet and must
    # stay legible there as well as against the dark sky
    draw_text(sub, sx + 2, 196 + 3, ss, (18, 12, 44), sp)
    draw_text(sub, sx, 196, ss, (232, 196, 118), sp)


# ---------------------------------------------------------------- PNG encoding
def png_chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def write_png(path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: none
        raw += img[y]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    data = b"\x89PNG\r\n\x1a\n"
    data += png_chunk(b"IHDR", ihdr)
    data += png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    data += png_chunk(b"IEND", b"")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    return len(data)


def main():
    draw()
    size = write_png(OUT)
    with open(OUT, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    print(f"wrote {OUT}: {W}x{H} PNG, {size} bytes, sha256={digest}")
    if size > 1048576:
        print("ERROR: over the 1,048,576 byte cap", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
