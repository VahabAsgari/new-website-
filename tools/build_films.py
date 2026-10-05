"""Films for joveyra.com: python3 tools/build_films.py [name ...]

Every film is drawn from the same plate as its still, frame by frame, at
twice the output size and averaged down. Frames go to a scratch folder as
PNG and are encoded to H.264 (MP4) and VP9 (WebM) with ffmpeg.

  open   the opening: the background ruling is cut across the plate, then
         the head is engraved line by line behind a burin point, with a slow
         push-in. Its last frame is the first frame of `hero`.
  hero   the home page loop: the lines creep one pitch along the form while
         a raking light passes over the marble. Seamless.
  end    the closing loop, the same treatment on the head of Demosthenes.
"""
import math
import os
import shutil
import subprocess
import sys
from multiprocessing import Pool

import cv2
import numpy as np

import plates as P

OUT = "assets/film/"
FRAMES = os.environ.get("FRAMES", "/tmp/jv-frames/")
TMP = FRAMES
FPS = 24
SIZE = (1600, 900)

ZEUS = ("DP265183.jpg", (0.14, 0.04, 0.86, 0.84), SIZE, (0.64, 0.55, 1.18), 6.2,
        dict(rect=(0.03, 0.01, 0.97, 0.999)))
DEMOS = ("DP326692.jpg", (0.15, 0.15, 0.87, 0.86), SIZE, (0.31, 0.58, 1.10), 6.2, {})

PLATE = None


def plate(spec):
    src, crop, size, box, sp, kw = spec
    return P.Plate(src, crop, size, box, sp=sp, **kw)


def raking(p, t, width=0.22, gain=0.22, angle=28):
    """A soft band of light across the plate; t from 0 (off left) to 1 (off right)."""
    a = math.radians(angle)
    W, H = p.W * p.S, p.H * p.S
    u = (p.xx * math.cos(a) + p.yy * math.sin(a)) / (W * math.cos(a) + H * math.sin(a))
    c = -width * 1.6 + t * (1 + width * 3.2)
    return gain * np.exp(-((u - c) / width) ** 2)


# ------------------------------------------------------------------ loops
LOOP_S = 9


def loop_frame(i):
    """Phase walks one full line pitch over the loop, light passes once."""
    p, n = PLATE, LOOP_S * FPS
    t = i / n
    light = raking(p, P.smooth((t - 0.15) / 0.7)) if 0.1 < t < 0.9 else None
    img = p.render(phase=t, light=light)
    cv2.imwrite(f"{TMP}{i:04d}.png", P.to8(img))
    return i


# ------------------------------------------------------------------ opening
OPEN_S = 8.0
RULE_IN = (0.2, 2.6)     # seconds: the ruling is cut across the whole plate
FORM_IN = (2.0, 6.0)     # the ruling bends into the head, top first
TONE_IN = (3.0, 6.8)     # the lines take the light
ZOOM = (1.10, 1.0)
OPEN_AUX = {}


def open_frame(i):
    """One straight ruling is cut across the plate. Then, inside the head,
    the rules bend into the form and take the light: the statue comes out
    of the ruling itself, with nothing laid on top."""
    p = PLATE
    s = i / FPS
    E = P.E
    rk, yn, xr = OPEN_AUX["rule"], OPEN_AUX["yn"], OPEN_AUX["xr"]
    # 1. ruling: rules start one after another, each cut left to right
    tr = (s - RULE_IN[0]) / (RULE_IN[1] - RULE_IN[0])
    front = tr * 1.5 - rk * 0.5
    cut = front - xr
    breveal = np.clip(cut * 60, 0, 1)
    tip = np.clip(1 - np.abs(cut * 60 - 0.5) * 2, 0, 1) * (front < 1) * (front > 0)
    # 2. form: 0 = the head is part of the ruling, 1 = fully bent
    k = P.smooth((s - FORM_IN[0] - 0.9 * yn) / (FORM_IN[1] - FORM_IN[0] - 0.9))
    w = P.smooth((s - TONE_IN[0] - 0.9 * yn) / (TONE_IN[1] - TONE_IN[0] - 0.9))
    m = p.mask
    phi = p.bphi + k * (p.phi - p.bphi)
    cover = (p.rule * (1 - w) + (0.06 + 0.94 * p.T) * w) * m
    head = E.lines(phi, p.sp, cover, pitch=E.pitch_of(phi, p.sp) if 0 < k.max() and k.min() < 1 else
                   (p.pitch if k.min() >= 1 else p.bpitch))
    if p.hatch:
        head = np.maximum(head, E.lines(p.phi2, p.sp, p.hi * p.hatch_cover * m * w ** 3, pitch=p.pitch2))
    bg = E.lines(p.bphi, p.sp, np.full_like(p.T, p.rule), pitch=p.bpitch) * (1 - m)
    head = head * breveal
    bg = bg * breveal
    rule, line, copper, ground = (E.hexbgr(c) for c in (P.RULE, P.LINE, P.COPPER, P.GROUND))
    col = rule + (line - rule) * w[..., None]
    img = np.empty(head.shape + (3,), np.float32)
    img[:] = ground
    img = img * (1 - bg[..., None]) + rule * bg[..., None]
    img = img * (1 - head[..., None]) + col * head[..., None]
    g = np.maximum(bg, head) * tip
    img = img * (1 - g[..., None]) + copper * g[..., None]
    zt = float(P.smooth(s / OPEN_S))
    img = p.down(img, ZOOM[0] + (ZOOM[1] - ZOOM[0]) * zt)
    cv2.imwrite(f"{TMP}{i:04d}.png", P.to8(img))
    return i


def prepare_open(p):
    OPEN_AUX["rule"] = p.rule_index()
    OPEN_AUX["xr"] = p.xx / (p.W * p.S)
    sel = p.yy[p.mask > 0.5]
    OPEN_AUX["yn"] = np.clip((p.yy - sel.min()) / (sel.max() - sel.min()), 0, 1)


# ------------------------------------------------------------------ encode
def encode(name, n, loop):
    src = f"{TMP}%04d.png"
    mp4, webm = f"{OUT}{name}.mp4", f"{OUT}{name}.webm"
    common = ["-y", "-loglevel", "error", "-framerate", str(FPS), "-i", src]
    subprocess.run(["ffmpeg", *common, "-c:v", "libx264", "-preset", "slow", "-crf", os.environ.get("CRF", "32"),
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", mp4], check=True)
    subprocess.run(["ffmpeg", *common, "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", os.environ.get("VP9CRF", "46"),
                    "-row-mt", "1", "-pix_fmt", "yuv420p", "-an", webm], check=True)
    poster = cv2.imread(f"{TMP}{0 if loop else n - 1:04d}.png")
    cv2.imwrite(f"{OUT}{name}-poster.webp", poster, [cv2.IMWRITE_WEBP_QUALITY, 70])
    for f in (mp4, webm):
        print(f, os.path.getsize(f) // 1024, "KB", flush=True)


def run(name):
    global PLATE, TMP
    TMP = f"{FRAMES}{name}/"            # one folder per film, so a film can be re-encoded alone
    if os.environ.get("ENCODE"):
        n, loop = (int(OPEN_S * FPS), False) if name == "open" else (LOOP_S * FPS, True)
        return encode(name, n, loop)
    shutil.rmtree(TMP, ignore_errors=True)
    os.makedirs(TMP)
    if name == "open":
        PLATE = plate(ZEUS)
        prepare_open(PLATE)
        n, fn, loop = int(OPEN_S * FPS), open_frame, False
    else:
        PLATE = plate(ZEUS if name == "hero" else DEMOS)
        n, fn, loop = LOOP_S * FPS, loop_frame, True
    if os.environ.get("ONLY"):
        frames = [int(x) for x in os.environ["ONLY"].split(",")]
    else:
        frames = range(n)
    with Pool(int(os.environ.get("PROCS", "4"))) as pool:
        for k, _ in enumerate(pool.imap_unordered(fn, frames, chunksize=2)):
            if k % 24 == 0:
                print(name, k, "/", len(frames), flush=True)
    if not os.environ.get("ONLY"):
        encode(name, n, loop)


if __name__ == "__main__":
    for name in sys.argv[1:] or ("hero", "open", "end"):
        run(name)
