"""Render every image on the Joveyra site.

    pip install opencv-python-headless numpy
    python3 tools/build_images.py

Sources (public domain) are cached in tools/source/ and are not committed;
see SOURCES below for where each one comes from. Output: assets/img/.
"""
import math
import os
import sys
import urllib.parse
import urllib.request

import cv2
import numpy as np

import diagrams as D
import lineart as L
import treatments as T

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "source")
OUT = os.path.join(HERE, "..", "assets", "img")

ON_BLUE = L.hexrgb("#eef1ff")
BLUE = L.hexrgb("#1424c4")
PRUSS = L.hexrgb("#123b80")
CY_PAPER = L.hexrgb("#f1f0ea")

COMMONS = "https://commons.wikimedia.org/wiki/"
SOURCES = {
    "hevelius_sextant.jpg": COMMONS + "File:Johannes_%26_Elisabetha_Hevelius_Sextant_1673.png",
    "galileo_portrait.jpg": "https://images.metmuseum.org/CRDImages/dp/original/DP854186.jpg",
    "kepler_model.jpg": COMMONS + "File:Mysterium_Cosmographicum_solar_system_model.jpg",
    "huygens.jpg": COMMONS + "File:Christiaan_Huygens_Clock_and_Horologii_Oscillatorii.jpg",
    "hev_14.jpg": COMMONS + "File:Illustrations_de_Machinae_coelestis..._-_(Non_identifi%C3%A9)_;_Johannes_Hevelius,_aut._de_texte_-_btv1b2600012h_(14_of_31).jpg",
    "sufi_ursa.jpg": COMMONS + "File:Al_Sufi_-_Book_of_Fixed_Stars_-_Ursa_Major_(The_Great_Bear)_-_Bodleian_Library_-_Marsh_144(illustrationonly).jpg",
}

B8 = np.array([0, 32, 8, 40, 2, 34, 10, 42, 48, 16, 56, 24, 50, 18, 58, 26, 12, 44, 4, 36, 14, 46, 6, 38,
               60, 28, 52, 20, 62, 30, 54, 22, 3, 35, 11, 43, 1, 33, 9, 41, 51, 19, 59, 27, 49, 17, 57, 25,
               15, 47, 7, 39, 13, 45, 5, 37, 63, 31, 55, 23, 61, 29, 53, 21], np.float32).reshape(8, 8) / 64


def bayer(shape, cell=3):
    th = np.kron(B8, np.ones((cell, cell)))
    return np.tile(th, (shape[0] // th.shape[0] + 1, shape[1] // th.shape[1] + 1))[:shape[0], :shape[1]]


def src(name):
    p = os.path.join(SRC, name)
    if not os.path.exists(p):
        sys.exit(f"missing source {p}; download it from {SOURCES.get(name, '?')}")
    return p


def gray(name, crop=None, scale=1.0):
    g = cv2.imread(src(name), cv2.IMREAD_GRAYSCALE)
    if crop:
        h, w = g.shape
        x0, y0, x1, y1 = crop
        g = g[int(h * y0):int(h * y1), int(w * x0):int(w * x1)]
    if scale != 1.0:
        g = cv2.resize(g, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    return g


def cutout(ink, close=31, keep_holes_below=0.55, edge=(0.10, 0.10, 0.16, 0.07)):
    """Keep what the engraver drew, drop open paper; edges dissolve through a dither."""
    k = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (r, r))
    obj = (cv2.GaussianBlur(ink, (0, 0), 6) > 0.05).astype(np.uint8)
    obj = cv2.morphologyEx(obj, cv2.MORPH_CLOSE, k(close))
    obj = cv2.morphologyEx(obj, cv2.MORPH_OPEN, k(9))
    H, W = obj.shape
    n, lab, st, _ = cv2.connectedComponentsWithStats((1 - obj).astype(np.uint8))
    for i in range(1, n):
        x, y, bw, bh, a = st[i]
        touches = x == 0 or y == 0 or x + bw >= W or y + bh >= H
        if a < 1800 or (not touches and a < 60000 and y > H * keep_holes_below):
            obj[lab == i] = 1
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    l, r, t, b = edge
    e = np.minimum.reduce([xx / (W * l), (W - 1 - xx) / (W * r), yy / (H * t), (H - 1 - yy) / (H * b)])
    fade = obj * np.clip(e, 0, 1) ** 1.2
    return (fade > bayer(fade.shape) + 0.002).astype(np.float32)


def flat(alpha_rgb, bg):
    """Composite an RGBA float image over a flat colour."""
    a = alpha_rgb[..., 3:4]
    out = alpha_rgb[..., :3] * a + np.array(bg, np.float32)[::-1][None, None] * (1 - a)
    return out


def write(img, name, widths):
    for w in widths:
        h = round(img.shape[0] * w / img.shape[1])
        small = cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)
        L.save_webp(small, os.path.join(OUT, f"{name}-{w}.webp") if len(widths) > 1 else os.path.join(OUT, f"{name}.webp"))


def square(img, cx=0.5, cy=0.5, size=None):
    h, w = img.shape[:2]
    s = size or min(h, w)
    x0 = int(np.clip(cx * w - s / 2, 0, w - s)); y0 = int(np.clip(cy * h - s / 2, 0, h - s))
    return img[y0:y0 + s, x0:x0 + s]


# ---------------------------------------------------------------- hero
def hero():
    g = gray("hevelius_sextant.jpg", (0.06, 0.13, 0.94, 0.93))
    g = cv2.resize(g, None, fx=1875 * 0.86 / 0.88 / g.shape[1] if False else 0.62, fy=0.62, interpolation=cv2.INTER_AREA)
    ink = L.ink_mask(g, block=25, c=11, min_area=8)
    cut = cutout(ink)
    H, W = ink.shape
    plate = L.rgba(ink, ON_BLUE, "paper", cut)
    pad_t, pad_r = int(H * 0.18), int(W * 0.28)
    CH, CW = H + pad_t, W + pad_r
    canvas = np.zeros((CH, CW, 4), np.float32)
    canvas[pad_t:, :W] = plate
    # sight-lines from both observers to one star
    star = (CW * 0.86, CH * 0.07)
    eyes = [(W * 0.16, pad_t + H * 0.575), (W * 0.775, pad_t + H * 0.545)]
    S = 3
    big = np.zeros((CH * S, CW * S), np.uint8)
    rng = np.random.default_rng(5)
    line = lambda p, q: cv2.line(big, (int(p[0] * S), int(p[1] * S)), (int(q[0] * S), int(q[1] * S)), 255, S, cv2.LINE_AA)
    for e in eyes:
        for _ in range(7):
            o = rng.normal(0, CH * 0.006, 2)
            line((e[0] + o[0] * .2, e[1] + o[1] * .2), (star[0] + o[0], star[1] + o[1]))
    for i in range(72):
        a = 2 * math.pi * i / 72
        r0, r1 = CH * 0.022, CH * (0.05 if i % 6 == 0 else 0.034)
        line((star[0] + math.cos(a) * r0, star[1] + math.sin(a) * r0), (star[0] + math.cos(a) * r1, star[1] + math.sin(a) * r1))
    cv2.circle(big, (int(star[0] * S), int(star[1] * S)), int(CH * 0.009 * S), 255, -1, cv2.LINE_AA)
    lines = cv2.resize(big, (CW, CH), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    la = lines * (1 - canvas[..., 3] * 0.95)
    col = np.array(ON_BLUE, np.float32)[::-1]
    a0 = canvas[..., 3:4]
    canvas[..., :3] = (canvas[..., :3] * a0 + col * la[..., None]) / np.maximum(a0 + la[..., None], 1e-4)
    canvas[..., 3] = np.clip(canvas[..., 3] + la, 0, 1)
    write(canvas, "hevelius", (1400, 900))


# ---------------------------------------------------------------- cards (blue tiles, light lines)
def tile_from_ink(ink, name, mode="ink"):
    """Light lines on the blue tile. mode 'ink': lines are light. 'paper': paper is light."""
    rgba = L.rgba(ink, ON_BLUE, mode)
    write(flat(rgba, BLUE), name, (900,))


def cards():
    tile_from_ink(D.galileo_rows(1000, 1000), "card-galileo")
    tile_from_ink(D.galton(1000, 1000), "card-galton")
    tile_from_ink(D.kepler(1000, 1000), "card-kepler")
    tile_from_ink(D.huygens(1000, 1000), "card-huygens")
    # Elisabetha Hevelius at the far end of the instrument, reading the second sight
    g = gray("hevelius_sextant.jpg", (0.50, 0.44, 0.98, 0.92), 0.9)
    ink = square(L.ink_mask(g, block=25, c=11, min_area=8), 0.55, 0.45)
    cut = cutout(ink, keep_holes_below=0.0, edge=(0.08, 0.08, 0.08, 0.08))
    write(flat(L.rgba(ink, ON_BLUE, "paper", cut), BLUE), "card-instrument", (900,))
    # detail of the great sextant: the graduated arc and the observer's hand
    g = gray("hevelius_sextant.jpg", (0.08, 0.38, 0.60, 0.70), 0.9)
    ink = square(L.ink_mask(g, block=25, c=11, min_area=8), 0.45, 0.6)
    cut = cutout(ink, keep_holes_below=0.0, edge=(0.08, 0.08, 0.08, 0.08))
    write(flat(L.rgba(ink, ON_BLUE, "paper", cut), BLUE), "card-sextant", (900,))
    # Galileo, by Villamena
    g = gray("galileo_portrait.jpg", (0.22, 0.17, 0.78, 0.66))
    ink = L.ink_mask(g, block=31, c=9, min_area=8)
    h, w = ink.shape
    s = min(w, int(h * 0.8))
    crop = ink[:int(s * 1.25), (w - s) // 2:(w - s) // 2 + s]
    write(L.rgba(crop, BLUE, "ink"), "galileo-portrait", (900,))


# ---------------------------------------------------------------- cyanotypes (prints on paper)
def cyan_print(light, name, size=1000, edge_to_paper=True):
    light = cv2.resize(light.astype(np.float32), (size, round(light.shape[0] * size / light.shape[1])), interpolation=cv2.INTER_AREA)
    img = T.cyanotype(light, edge=True, edge_to=np.array(CY_PAPER, np.float32)[::-1] if edge_to_paper else None)
    T.save(img, os.path.join(OUT, f"{name}.webp"), quality=80)


def cyan():
    cyan_print(D.galileo_rows(1100, 1100), "cy-galileo")
    cyan_print(D.galton(1100, 1100), "cy-galton")
    cyan_print(D.huygens(1100, 1100), "cy-huygens")
    cyan_print(D.kepler(1100, 1100), "cy-kepler")
    cyan_print(D.rosette(1100, 1100), "cy-rosette")
    fa = cv2.imread(src("persian.png"), cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255
    cyan_print(fa, "cy-persian")
    moon = T.load_gray(os.path.join(SRC, "DP822421.jpg"), (0.02, 0.02, 0.98, 0.86), 1400)
    est = cv2.GaussianBlur(cv2.dilate(moon, np.ones((61, 61))), (0, 0), 40)
    ink = 1 - np.clip(moon / np.maximum(est, 1e-3), 0, 1)
    ink = np.clip((ink - 0.08) / 0.5, 0, 1)
    cyan_print(1 - ink * 0.9, "cy-moon")
    rete = T.load_bgr(os.path.join(SRC, "DP170383.jpg"), (0.22, 0.30, 0.82, 0.75))
    cyan_print(T.photo_light(rete), "cy-rete")
    horse = T.load_bgr(os.path.join(SRC, "DP275111.jpg"), (0.04, 0.135, 0.965, 0.44))
    # four frames of the gallop, stacked into a square print
    hl = T.photo_light(horse)
    fw = hl.shape[1] // 6
    frames = [hl[:, i * fw:(i + 1) * fw] for i in (1, 2, 3, 4)]
    top = np.concatenate(frames[:2], 1); bot = np.concatenate(frames[2:], 1)
    sq = np.concatenate([top, bot], 0)
    hh = sq.shape[0] // 2; sq = sq[:hh * 2]
    sq = np.concatenate([sq[:hh // 2 * 2][: sq.shape[1] // 2], sq[hh:hh + sq.shape[1] // 2]], 0) if sq.shape[0] > sq.shape[1] else sq
    cyan_print(sq, "cy-horse")


def main():
    os.makedirs(OUT, exist_ok=True)
    which = sys.argv[1:] or ["hero", "cards", "cyan"]
    for name in which:
        globals()[name]()
        print("built", name)


if __name__ == "__main__":
    main()
