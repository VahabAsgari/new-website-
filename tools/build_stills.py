"""Still plates for joveyra.com: python3 tools/build_stills.py [name ...]

Each still is drawn at twice its size and averaged down, then written as
WebP at two widths. The statues are Met Open Access photographs (CC0)."""
import os
import sys
from multiprocessing import Pool

import cv2

import plates as P

OUT = "assets/img/"

# name: (source, crop, canvas size, (cx, cy, head height), pitch, extra kwargs)
STILLS = {
    # home page
    "zeus":        ("DP265183.jpg", (0.14, 0.04, 0.86, 0.84), (1920, 1080), (0.64, 0.55, 1.18), 7.4,
                    dict(rect=(0.03, 0.01, 0.97, 0.999))),
    "epikouros":   ("DP333053.jpg", (0.17, 0.13, 0.93, 0.86), (1600, 1000), (0.70, 0.56, 1.12), 6.4, {}),
    "herm":        ("DP107600.jpg", (0.12, 0.06, 0.88, 0.80), (1600, 1000), (0.30, 0.54, 1.12), 6.4,
                    dict(rect=(0.03, 0.02, 0.97, 0.999), kill=((0.62, 0, 0.82, 0.125),))),
    "strategos":   ("DP345013.jpg", (0.19, 0.15, 0.89, 0.86), (1600, 1000), (0.70, 0.56, 1.12), 6.4, {}),
    "youth":       ("DP202807.jpg", (0.23, 0.13, 0.77, 0.86), (1200, 1500), (0.50, 0.53, 0.98), 6.0, {}),
    "demosthenes": ("DP326692.jpg", (0.15, 0.15, 0.87, 0.86), (1920, 1080), (0.50, 0.58, 1.10), 7.4, {}),
}


def build(name):
    src, crop, size, box, sp, kw = STILLS[name]
    p = P.Plate(src, crop, size, box, sp=sp, **kw)
    img = P.to8(p.render())
    cv2.imwrite(OUT + f"{name}.png", img) if os.environ.get("PNG") else None
    w = size[0]
    for ww in (w, w // 2 if w > 1300 else int(w * 0.6)):
        im = img if ww == w else cv2.resize(img, (ww, int(round(size[1] * ww / w))), interpolation=cv2.INTER_AREA)
        cv2.imwrite(OUT + f"{name}-{ww}.webp", im, [cv2.IMWRITE_WEBP_QUALITY, 82])
    return name


if __name__ == "__main__":
    names = sys.argv[1:] or list(STILLS)
    with Pool(min(3, len(names))) as pool:
        for n in pool.imap_unordered(build, names):
            print("done", n, flush=True)
