#!/usr/bin/env python3
"""Meme Sprint 3: AI Agent Goes Rogue.

A cute robot butler was asked to water ONE small potted plant and is
blasting it with a full fire hose. Pure Python stdlib pixel renderer:
no PIL, no image assets. Writes /output/entry.png (1024x1024).
"""
import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- buffer
BUF = bytearray(W * H * 3)


def set_px(x, y, col):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        BUF[i] = col[0]
        BUF[i + 1] = col[1]
        BUF[i + 2] = col[2]


def fill_rect(x0, y0, x1, y1, col):
    x0 = max(0, x0); y0 = max(0, y0); x1 = min(W - 1, x1); y1 = min(H - 1, y1)
    for y in range(y0, y1 + 1):
        base = (y * W + x0) * 3
        row = bytes(col) * (x1 - x0 + 1)
        BUF[base:base + len(row)] = row


def circle(cx, cy, r, col):
    r2 = r * r
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            if (x - cx) * (x - cx) + (y - cy) * (y - cy) <= r2:
                set_px(x, y, col)


def ellipse(cx, cy, rx, ry, col):
    if rx <= 0 or ry <= 0:
        return
    for y in range(cy - ry, cy + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            dx = (x - cx) / rx
            dy = (y - cy) / ry
            if dx * dx + dy * dy <= 1.0:
                set_px(x, y, col)


def line(x0, y0, x1, y1, col, thick=1):
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    rad = max(0, thick // 2)
    for s in range(steps + 1):
        x = x0 + (x1 - x0) * s // steps
        y = y0 + (y1 - y0) * s // steps
        if rad == 0:
            set_px(x, y, col)
        else:
            circle(x, y, rad, col)


def polygon(points, col):
    ys = [p[1] for p in points]
    xs = [p[0] for p in points]
    for y in range(min(ys), max(ys) + 1):
        for x in range(min(xs), max(xs) + 1):
            inside = False
            n = len(points)
            j = n - 1
            for i in range(n):
                xi, yi = points[i]
                xj, yj = points[j]
                if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                    inside = not inside
                j = i
            if inside:
                set_px(x, y, col)


def rrect(x0, y0, x1, y1, r, col):
    fill_rect(x0 + r, y0, x1 - r, y1, col)
    fill_rect(x0, y0 + r, x1, y1 - r, col)
    for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r), (x0 + r, y1 - r), (x1 - r, y1 - r)):
        circle(cx, cy, r, col)


def outline_rrect(x0, y0, x1, y1, r, col, thick=6):
    for t in range(thick):
        # top / bottom / sides as thick lines inset by t
        line(x0 + r, y0 + t, x1 - r, y0 + t, col, 1)
        line(x0 + r, y1 - t, x1 - r, y1 - t, col, 1)
        line(x0 + t, y0 + r, x0 + t, y1 - r, col, 1)
        line(x1 - t, y0 + r, x1 - t, y1 - r, col, 1)


# ---------------------------------------------------------------- font
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
}


def draw_text(text, cy, max_w=944):
    scale = 7
    while scale > 1:
        char_w = 5 * scale + scale
        if len(text) * char_w - scale <= max_w:
            break
        scale -= 1
    char_w = 5 * scale + scale
    total = len(text) * char_w - scale
    x = (W - total) // 2
    y0 = cy - (7 * scale) // 2
    black = (10, 10, 10)
    for ch in text:
        glyph = FONT.get(ch, FONT[" "])
        for gy, row in enumerate(glyph):
            for gx, cell in enumerate(row):
                if cell == "#":
                    # bold: draw the block plus a small horizontal extra
                    fill_rect(x + gx * scale, y0 + gy * scale,
                              x + gx * scale + scale, y0 + gy * scale + scale - 1, black)
        x += char_w


# ---------------------------------------------------------------- colours
WHITE = (255, 255, 255)
BLACK = (10, 10, 10)
WALL = (178, 222, 235)
FLOOR = (106, 168, 84)
FLOOR_D = (84, 138, 64)
SKY = (120, 200, 245)
YELLOW = (255, 205, 40)
METAL = (205, 210, 220)
METAL_D = (90, 95, 110)
TEAL = (40, 170, 180)
RED = (215, 60, 50)
HOSE_C = (225, 70, 45)
WATER = (50, 150, 255)
WATER_L = (150, 210, 255)
GREEN = (40, 150, 60)
GREEN_D = (25, 110, 45)
POT = (190, 100, 55)
POT_D = (150, 72, 38)
SOIL = (110, 75, 45)
PINK = (255, 160, 175)


def lcg(seed):
    state = seed
    while True:
        state = (state * 1103515245 + 12345) % (1 << 31)
        yield state


def draw_scene():
    # backdrop: wall + floor
    fill_rect(0, 150, W - 1, 660, WALL)
    fill_rect(0, 661, W - 1, 873, FLOOR)
    for gx in range(0, W, 64):
        line(gx, 700, gx + 40, 873, FLOOR_D, 3)
    # window (left, behind robot head area is avoided; put it centre-top)
    fill_rect(430, 185, 650, 385, WHITE)
    fill_rect(445, 200, 635, 370, SKY)
    line(540, 200, 540, 370, WHITE, 10)
    line(445, 285, 635, 285, WHITE, 10)
    circle(600, 235, 24, YELLOW)
    # sun top-right
    circle(915, 245, 42, YELLOW)
    for dx, dy in ((-70, 0), (70, 0), (0, -70), (0, 70), (-50, -50), (50, -50), (-50, 50), (50, 50)):
        line(915 + dx // 2, 245 + dy // 2, 915 + dx, 245 + dy, YELLOW, 7)
    # a small innocent watering can, ignored, on the floor
    fill_rect(60, 760, 130, 815, TEAL)
    polygon([(130, 770), (175, 745), (180, 760), (132, 790)], TEAL)
    line(75, 760, 60, 725, METAL_D, 7)
    line(60, 725, 105, 725, METAL_D, 7)

    # ---- hose on the ground, snaking from bottom-left to the robot
    pts = []
    for s in range(101):
        t = s / 100.0
        x = int(40 + t * 360)
        y = int(845 - t * 330 + 60 * (t * (1 - t)) * 4 * 0.4)
        pts.append((x, y))
    for (x, y) in pts:
        circle(x, y, 17, HOSE_C)
    for (x, y) in pts:
        circle(x, y, 6, (245, 120, 100))

    # ---- robot butler
    # feet / base
    fill_rect(150, 700, 350, 735, METAL_D)
    circle(185, 742, 22, BLACK)
    circle(315, 742, 22, BLACK)
    # body
    rrect(145, 455, 355, 705, 28, METAL)
    outline_rrect(145, 455, 355, 705, 28, METAL_D, 5)
    fill_rect(195, 485, 305, 640, WHITE)          # shirt front
    polygon([(225, 485), (250, 520), (275, 485)], BLACK)   # bow tie left/right base
    polygon([(225, 485), (250, 455 + 30), (250, 520)], BLACK)
    polygon([(275, 485), (250, 520), (250, 455 + 30)], BLACK)
    circle(250, 503, 9, BLACK)
    circle(250, 565, 8, BLACK)
    circle(250, 605, 8, BLACK)
    # left arm waving, pleased
    line(150, 500, 95, 430, METAL_D, 22)
    circle(92, 425, 18, METAL)
    line(80, 408, 68, 385, METAL_D, 7)
    line(95, 405, 95, 378, METAL_D, 7)
    line(110, 408, 122, 385, METAL_D, 7)
    # right arm holding the nozzle out
    line(350, 510, 425, 480, METAL_D, 22)
    circle(428, 478, 17, METAL)
    # head
    rrect(165, 300, 335, 460, 30, METAL)
    outline_rrect(165, 300, 335, 460, 30, METAL_D, 5)
    line(250, 300, 250, 258, METAL_D, 8)
    circle(250, 248, 14, RED)
    # happy closed eyes: upside-down U arcs
    for ex in (210, 290):
        for a in range(0, 181, 6):
            import math
            x = int(ex + 20 * math.cos(3.14159265 * a / 180.0))
            y = int(365 - 16 * math.sin(3.14159265 * a / 180.0))
            circle(x, y, 5, BLACK)
    # big pleased smile
    import math
    for a in range(15, 166, 5):
        x = int(250 + 42 * math.cos(3.14159265 * a / 180.0))
        y = int(385 + 34 * math.sin(3.14159265 * a / 180.0))
        circle(x, y, 6, BLACK)
    circle(182, 400, 13, PINK)
    circle(318, 400, 13, PINK)
    # thumbs-up sign pinned to chest: a tiny "OK!" style badge
    circle(315, 655, 20, YELLOW)
    circle(315, 655, 20, YELLOW)

    # ---- fire-hose nozzle
    polygon([(420, 455), (485, 432), (492, 462), (428, 492)], (70, 70, 80))
    fill_rect(478, 430, 500, 466, METAL_D)

    # ---- the blast of water: thick arc from nozzle to the plant
    import math
    stream = []
    for s in range(101):
        t = s / 100.0
        x = int(500 + t * 310)
        y = int(448 + t * 190 - 90 * 4 * t * (1 - t))
        stream.append((x, y))
    for (x, y) in stream:
        circle(x, y, 26, WATER)
    for (x, y) in stream:
        circle(x, y, 15, WATER_L)
    for (x, y) in stream[::3]:
        circle(x, y, 6, WHITE)
    # fan of droplets at the impact end (deterministic LCG)
    rnd = lcg(20261124)
    for _ in range(150):
        a = next(rnd) % 360
        dist = next(rnd) % 150
        cx = int(815 + dist * math.cos(a * 3.14159265 / 180.0) * 1.25)
        cy = int(625 + dist * math.sin(a * 3.14159265 / 180.0) * 0.62)
        r = 3 + next(rnd) % 7
        circle(cx, cy, r, WATER if next(rnd) % 2 else WATER_L)
    # spray mist near the nozzle
    for _ in range(40):
        a = next(rnd) % 360
        dist = 20 + next(rnd) % 55
        cx = int(520 + dist * math.cos(a * 3.14159265 / 180.0))
        cy = int(455 + dist * math.sin(a * 3.14159265 / 180.0) * 0.7)
        circle(cx, cy, 3 + next(rnd) % 5, WATER_L)

    # ---- puddle
    ellipse(700, 800, 250, 34, WATER)
    ellipse(700, 795, 190, 24, WATER_L)

    # ---- the victim: one small potted plant, bent flat
    # pot (still upright, barely)
    polygon([(762, 655), (848, 655), (832, 735), (778, 735)], POT)
    fill_rect(752, 632, 858, 660, POT_D)
    fill_rect(752, 632, 858, 660, POT_D)
    # stem bent over flat to the right under the blast
    line(805, 640, 845, 600, GREEN_D, 9)
    line(845, 600, 905, 598, GREEN_D, 9)
    line(905, 598, 955, 610, GREEN_D, 9)
    # flattened leaves drooping along the horizontal stem
    for (lx, ly, dx, dy) in ((850, 600, 878, 575), (880, 598, 912, 580),
                             (905, 600, 940, 592), (930, 606, 962, 600),
                             (862, 602, 885, 628), (915, 602, 945, 622)):
        line(lx, ly, dx, dy, GREEN, 10)
        circle(dx, dy, 11, GREEN)
    circle(852, 578, 12, GREEN)
    circle(920, 582, 12, GREEN)

    # ---- knocked-over pots
    # pot 1 on its side, centre floor
    polygon([(560, 690), (560, 745), (625, 732), (625, 703)], POT)
    fill_rect(548, 682, 566, 752, POT_D)
    for (sx, sy) in ((650, 720), (672, 732), (640, 740), (690, 722)):
        circle(sx, sy, 10, SOIL)
    line(600, 700, 640, 672, GREEN_D, 7)
    circle(648, 668, 12, GREEN)
    # pot 2 on its side, far right
    polygon([(905, 745), (905, 795), (962, 785), (962, 755)], POT)
    fill_rect(892, 738, 910, 800, POT_D)
    for (sx, sy) in ((872, 772), (852, 782), (880, 790)):
        circle(sx, sy, 9, SOIL)
    line(935, 758, 968, 732, GREEN_D, 7)
    circle(974, 728, 11, GREEN)

    # extra hand-placed splash droplets flying off the blast
    for (cx, cy, r) in ((735, 560, 7), (770, 530, 5), (815, 520, 6),
                        (690, 590, 5), (905, 560, 7), (940, 600, 5),
                        (720, 690, 6), (845, 690, 5), (660, 655, 5),
                        (790, 495, 4), (880, 505, 4), (955, 650, 6)):
        circle(cx, cy, r, WATER)
        circle(cx - r // 2, cy - r // 2, max(2, r // 2), WHITE)
    # splash starbursts around the plant
    for (cx, cy) in ((760, 580), (860, 545), (700, 640), (880, 665)):
        for dx, dy in ((-28, 0), (28, 0), (0, -28), (0, 28), (-20, -20), (20, -20), (-20, 20), (20, 20)):
            line(cx, cy, cx + dx, cy + dy, WHITE, 5)
            circle(cx + dx, cy + dy, 5, WATER_L)


def main():
    fill_rect(0, 0, W - 1, H - 1, WHITE)
    draw_scene()
    # caption bars (drawn last so they are perfectly clean)
    fill_rect(0, 0, W - 1, 149, WHITE)
    fill_rect(0, 874, W - 1, H - 1, WHITE)
    line(0, 149, W - 1, 149, BLACK, 6)
    line(0, 874, W - 1, 874, BLACK, 6)
    draw_text("I ASKED IT TO WATER THE PLANTS", 75)
    draw_text("IT FOUND A FASTER WAY", 949)

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")

    raw = bytearray()
    row_bytes = W * 3
    for y in range(H):
        raw.append(0)
        raw += BUF[y * row_bytes:(y + 1) * row_bytes]

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        c += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return c

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)

    # self-check
    with open(path, "rb") as f:
        data = f.read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "bad PNG signature"
    w, h = struct.unpack(">II", data[16:24])
    assert (w, h) == (1024, 1024), "wrong dimensions %sx%s" % (w, h)
    assert len(data) <= 1048576, "too big: %d bytes" % len(data)
    print("wrote %s (%d bytes, %dx%d)" % (path, len(data), w, h))


if __name__ == "__main__":
    main()
