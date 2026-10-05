"""Cyanotype plates and the guard film for /product/ and /firm/.

Each Met object is cut from its studio backdrop and printed as a photogram:
the stone carries the light, everything around it is fully exposed and goes
to deep Prussian blue. No border, no frame: the print runs to the edge of the
page.

    PYTHONPATH=tools python3 tools/build_cyan.py [names] [film | film-<name>]
"""
import os
import subprocess
import sys
from multiprocessing import Pool

import cv2
import numpy as np

import engrave as E
import treatments as T

SRC = "tools/source/"
OUT = "assets/img/"
FILM = "assets/film/"
TMP = os.environ.get("FRAMES", "/tmp/jv-cyan-frames/")

# name: src, crop (fractions of source), canvas, box (cx, cy, object height / canvas height),
#       grabcut rect inside the crop (None = no mask), gamma, widths
PLATES = {
    "guard": dict(src="DP-12499-019.jpg", crop=(0, 0, 1, 1), size=(1600, 900), box=(0.64, 0.56, 1.22),
                  rect=(0.01, 0.01, 0.99, 0.99), gamma=1.0, widths=(1920, 960), sat=0.12),
    "procession": dict(src="DP-12499-017.jpg", crop=(0, 0.02, 1, 0.66), size=(1600, 1000), box=(0.70, 0.56, 1.14),
                       rect=(0.06, 0.01, 0.94, 0.999), gamma=1.0, widths=(1600, 800)),
    "bull": dict(src="DP-12499-015.jpg", crop=(0.18, 0.08, 1, 0.82), size=(1600, 1000), box=(0.31, 0.53, 1.45),
                 rect=(0.12, 0.05, 0.99, 0.97), gamma=1.0, widths=(1600, 800), kill=((0.3, 0.8, 0.75, 1),), kill_canvas=((0.26, 0.90, 0.36, 1),)),
    "lamassu": dict(src="DT879.jpg", crop=(0.537, 0.05, 0.804, 0.47), size=(1200, 1500), box=(0.5, 0.5, 1.0),
                    rect=None, gamma=1.3, widths=(1200, 720)),
    "philosopher": dict(src="DP331288.jpg", crop=(0.05, 0.03, 0.95, 0.84), size=(1600, 900), box=(0.66, 0.53, 1.0),
                        rect=(0.04, 0.01, 0.96, 0.995), gamma=1.0, widths=(1920, 960)),
    "servants": dict(src="DP226593.jpg", crop=(0, 0, 1, 1), size=(1600, 1000), box=(0.33, 0.5, 1.12),
                     rect=(0.02, 0.01, 0.98, 0.99), gamma=1.0, widths=(1600, 800)),
}


def light_map(spec, scale=1.0):
    """0..1 exposure map at canvas size x scale: 1 = paper, 0 = full exposure."""
    W, H = int(spec["size"][0] * scale), int(spec["size"][1] * scale)
    cx, cy, hf = spec["box"]
    im = E.load(SRC + spec["src"], crop=spec["crop"], width=2400)
    ih, iw = im.shape[:2]
    hh = int(round(hf * H))
    hw = int(round(iw * hh / ih))
    im = cv2.resize(im, (hw, hh), interpolation=cv2.INTER_AREA if hh < ih else cv2.INTER_CUBIC)
    m = E.subject_mask(im, rect=spec["rect"], iters=6) if spec["rect"] else np.ones((hh, hw), np.float32)
    if "sat" in spec:   # coloured stone on a neutral sweep: drop the grey that GrabCut let in
        sat = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)[..., 1].astype(np.float32) / 255
        keep = (cv2.GaussianBlur(sat, (0, 0), 3) > spec["sat"]).astype(np.uint8)
        keep = cv2.morphologyEx(keep, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
        keep = cv2.morphologyEx(keep, cv2.MORPH_CLOSE, np.ones((31, 31), np.uint8))
        m = m * cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 1.5)
    for k in spec.get("kill", ()):
        m[int(k[1] * hh):int(k[3] * hh), int(k[0] * hw):int(k[2] * hw)] = 0
    L = E.luminance(im)
    t = E.tone(L, m, clip=2.6, tiles=8, gamma=spec["gamma"], lo=1, hi=99.7)
    # the stone holds a floor of light, so the cut edge reads against the blue
    t = 0.12 + 0.88 * t
    canvas = np.zeros((H, W), np.float32)
    M = np.zeros((H, W), np.float32)
    x0, y0 = int(cx * W - hw / 2), int(cy * H - hh / 2)
    sx0, sy0 = max(0, -x0), max(0, -y0)
    dx0, dy0 = max(0, x0), max(0, y0)
    dx1, dy1 = min(W, x0 + hw), min(H, y0 + hh)
    canvas[dy0:dy1, dx0:dx1] = t[sy0:sy0 + dy1 - dy0, sx0:sx0 + dx1 - dx0]
    M[dy0:dy1, dx0:dx1] = m[sy0:sy0 + dy1 - dy0, sx0:sx0 + dx1 - dx0]
    for k in spec.get("kill_canvas", ()):   # mount pins below the object, in canvas fractions
        M[int(k[1] * H):int(k[3] * H), int(k[0] * W):int(k[2] * W)] = 0
    # a contact print is never razor sharp at the silhouette
    M = cv2.GaussianBlur(M, (0, 0), 1.6 * scale)
    return canvas * M


def still(name):
    spec = PLATES[name]
    big = spec["widths"][0]
    s = big / spec["size"][0]
    img = T.cyanotype(light_map(spec, s), edge=False)
    for w in spec["widths"]:
        out = img if w == big else cv2.resize(img, (w, int(round(img.shape[0] * w / big))), interpolation=cv2.INTER_AREA)
        T.save(out, f"{OUT}cy-{name}-{w}.webp", quality=72)
        print(f"{OUT}cy-{name}-{w}.webp", os.path.getsize(f"{OUT}cy-{name}-{w}.webp") // 1024, "KB", flush=True)
    if os.environ.get("PNG"):
        T.save(img, f"{OUT}cy-{name}.png")


# --------------------------------------------------------------------- film
FPS, HALF_S, ZOOM = 24, 8, 0.06
TONE = FOCUS = OUTDIR = None

# film: plate it is printed from, overrides for a 16:9 canvas, and the point the camera pushes towards
FILMS = {
    "guard": dict(plate="guard", focus=(0.60, 0.50)),
    "philosopher": dict(plate="philosopher", focus=(0.66, 0.46)),
    "procession": dict(plate="procession", size=(1600, 900), box=(0.70, 0.55, 1.14), focus=(0.68, 0.42)),
    "servants": dict(plate="servants", size=(1600, 900), box=(0.30, 0.5, 1.12), focus=(0.30, 0.48)),
}


def film_frame(i):
    """Forward half of a ping-pong push-in, with a slow band of light."""
    n = FPS * HALF_S
    u = i / (n - 1)
    k = u * u * (3 - 2 * u)
    z = 1 + ZOOM * k
    H, W = TONE.shape
    w, h = 1600, 900
    # push towards the face, slightly right of centre
    fx, fy = FOCUS[0] * W, FOCUS[1] * H
    cw, ch = W / z, H / z
    x0, y0 = fx - cw * fx / W, fy - ch * fy / H
    A = np.float32([[2 * w / cw, 0, -x0 * 2 * w / cw], [0, 2 * h / ch, -y0 * 2 * h / ch]])
    t = cv2.warpAffine(TONE, A, (2 * w, 2 * h), flags=cv2.INTER_LINEAR)
    t = cv2.resize(t, (w, h), interpolation=cv2.INTER_AREA)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    band = np.exp(-(((xx * 0.88 + yy * 0.47) / w - (0.15 + 0.7 * k)) / 0.28) ** 2)
    t = np.clip(t * (0.94 + 0.10 * band), 0, 1)
    T.rng = np.random.default_rng(11)          # the same grain every frame: it is one print
    img = T.cyanotype(t, edge=False)
    cv2.imwrite(f"{OUTDIR}{i:04d}.png", (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))


def film(name):
    global TONE, FOCUS, OUTDIR
    f = FILMS[name]
    spec = {**PLATES[f["plate"]], **{k: v for k, v in f.items() if k in ("size", "box")}}
    OUTDIR = f"{TMP}{name}/"
    os.makedirs(OUTDIR, exist_ok=True)
    TONE, FOCUS = light_map(spec, 2.0), f["focus"]
    n = FPS * HALF_S
    with Pool(int(os.environ.get("PROCS", "4"))) as pool:
        pool.map(film_frame, range(n), chunksize=4)
    for i in range(n):                         # the way back is the way in, reversed
        j = 2 * n - 1 - i
        if os.path.lexists(f"{OUTDIR}{j:04d}.png"):
            os.remove(f"{OUTDIR}{j:04d}.png")
        os.symlink(f"{OUTDIR}{i:04d}.png", f"{OUTDIR}{j:04d}.png")
    src = f"{OUTDIR}%04d.png"
    common = ["-y", "-loglevel", "error", "-framerate", str(FPS), "-i", src]
    mp4, webm = f"{FILM}{name}.mp4", f"{FILM}{name}.webm"
    subprocess.run(["ffmpeg", *common, "-c:v", "libx264", "-preset", "slow", "-crf", os.environ.get("CRF", "32"),
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", mp4], check=True)
    subprocess.run(["ffmpeg", *common, "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", os.environ.get("VP9CRF", "46"),
                    "-row-mt", "1", "-pix_fmt", "yuv420p", "-an", webm], check=True)
    cv2.imwrite(f"{FILM}{name}-poster.webp", cv2.imread(f"{OUTDIR}0000.png"), [cv2.IMWRITE_WEBP_QUALITY, 70])
    for f in (mp4, webm):
        print(f, os.path.getsize(f) // 1024, "KB", flush=True)


if __name__ == "__main__":
    names = sys.argv[1:] or [*PLATES, "film"]
    for nm in names:
        if nm == "film":
            for k in FILMS:
                film(k)
        elif nm.startswith("film-"):
            film(nm[5:])
        else:
            still(nm)
