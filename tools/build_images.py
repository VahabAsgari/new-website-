"""Download public-domain sources and render every site image.

    pip install opencv-python-headless numpy
    python3 tools/build_images.py

Sources are cached in tools/source/ (not committed). Output: assets/img/.
"""
import os
import urllib.request

import cv2

import treatments as T

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "source")
OUT = os.path.join(HERE, "..", "assets", "img")
MET = "https://images.metmuseum.org/CRDImages/"

# name: (process, source url, crop x0,y0,x1,y1 as fractions, widths)
IMAGES = {
    # ---- engraving (joveyra.com home)
    "hercules":   ("engraving", MET + "dp/original/DP880248.jpg", (0.12, 0.02, 0.88, 0.86), (1600, 900)),
    "apollo":     ("engraving", MET + "dp/original/DP821105.jpg", (0.08, 0.04, 0.92, 0.96), (1100, 700)),
    "farnese":    ("engraving", MET + "dp/original/DP102198.jpg", (0.10, 0.03, 0.90, 0.80), (1600, 900)),
    "melencolia": ("engraving", MET + "dp/original/DP815742.jpg", (0.02, 0.02, 0.98, 0.97), (1400, 800)),
    "atlas":      ("engraving", MET + "dp/original/DP822474.jpg", (0.12, 0.03, 0.88, 0.97), (2000, 1000)),
    "moon":       ("engraving", MET + "dp/original/DP822421.jpg", (0.00, 0.00, 1.00, 0.90), (1400, 800)),
    # ---- cyanotype (the firm, the platform)
    "astrolabe":  ("cyan-object", MET + "is/original/DP170383.jpg", None, (1600, 900)),
    "astrolabe-rete": ("cyan-photo", MET + "is/original/DP170383.jpg", (0.22, 0.30, 0.82, 0.75), (1600, 900)),
    "globe":      ("cyan-object", MET + "es/original/DP231286.jpg", None, (1600, 900)),
    "horse":      ("cyan-photo", MET + "ph/original/DP275111.jpg", (0.04, 0.135, 0.965, 0.44), (2400, 1200)),
}


def fetch(url):
    os.makedirs(SRC, exist_ok=True)
    path = os.path.join(SRC, url.rsplit("/", 1)[1])
    if not os.path.exists(path):
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=180) as r, open(path, "wb") as f:
            f.write(r.read())
    return path


def render(process, path, crop):
    if process == "engraving":
        return T.engraving(T.load_gray(path, crop))
    im = T.load_bgr(path, crop)
    light = T.object_light(im) if process == "cyan-object" else T.photo_light(im)
    return T.cyanotype(light)


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, (process, url, crop, widths) in IMAGES.items():
        img = render(process, fetch(url), crop)
        for w in widths:
            h = round(img.shape[0] * w / img.shape[1])
            small = cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)
            T.save(small, os.path.join(OUT, f"{name}-{w}.webp"))
        print(name, img.shape[1], "x", img.shape[0])


if __name__ == "__main__":
    main()
