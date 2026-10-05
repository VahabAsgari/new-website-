"""Banknote line engraving for Joveyra.

A photograph of a statue is redrawn as a single family of engraved lines.
The lines are the level sets of a scalar field `phi`: a straight ruling that
is bent by the form of the head, then evened out with a Poisson solve so the
lines keep a near-constant pitch the way a burin cut does. Each line swells
with the light it carries and thins to nothing in shadow, so the picture is
made of lines only, never of grey pixels.
"""
import math

import cv2
import numpy as np
from scipy import fft


# ------------------------------------------------------------------ input
def load(path, crop=None, width=2000):
    """crop = (x0, y0, x1, y1) as fractions of the source."""
    im = cv2.imread(path, cv2.IMREAD_COLOR)
    if crop:
        h, w = im.shape[:2]
        x0, y0, x1, y1 = crop
        im = im[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]
    h, w = im.shape[:2]
    s = width / w
    im = cv2.resize(im, (width, int(round(h * s))), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    return im


def luminance(im):
    return cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255


def subject_mask(im, rect=None, iters=6):
    """GrabCut from a rectangle. The Met photographs every object against a
    plain backdrop, so this separates marble from studio paper cleanly."""
    h, w = im.shape[:2]
    s = 900 / max(h, w)
    sm = cv2.resize(im, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    sh, sw = sm.shape[:2]
    if rect is None:
        rect = (0.04, 0.02, 0.96, 0.995)
    r = (int(rect[0] * sw), int(rect[1] * sh), int((rect[2] - rect[0]) * sw), int((rect[3] - rect[1]) * sh))
    mask = np.zeros((sh, sw), np.uint8)
    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(sm, mask, r, bgd, fgd, iters, cv2.GC_INIT_WITH_RECT)
    m = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    # keep the largest piece, fill holes
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    if n > 1:
        k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
        m = np.where(lab == k, 255, 0).astype(np.uint8)
    inv = cv2.bitwise_not(m)
    n, lab, st, _ = cv2.connectedComponentsWithStats(inv, connectivity=4)
    for i in range(1, n):
        x, y, ww, hh, a = st[i]
        if x > 0 and y > 0 and x + ww < sw and y + hh < sh:
            m[lab == i] = 255
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    m = cv2.resize(m, (w, h), interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255
    m = cv2.GaussianBlur(m, (0, 0), 1.2)
    return np.clip((m - 0.5) * 3 + 0.5, 0, 1)


def tone(L, mask=None, clip=2.2, tiles=8, gamma=1.0, lo=2, hi=99.5):
    g = (np.clip(L, 0, 1) * 255).astype(np.uint8)
    c = cv2.createCLAHE(clipLimit=clip, tileGridSize=(tiles, tiles)).apply(g).astype(np.float32) / 255
    sel = c[mask > 0.5] if mask is not None and mask.sum() > 100 else c.ravel()
    a, b = np.percentile(sel, lo), np.percentile(sel, hi)
    t = np.clip((c - a) / max(b - a, 1e-3), 0, 1)
    return t ** gamma


# ------------------------------------------------------------------ fields
def poisson(div):
    """Solve lap(phi) = div with Neumann borders (DCT-II)."""
    h, w = div.shape
    d = fft.dctn(div.astype(np.float64), type=2, norm="ortho")
    ky = 2 * np.cos(np.pi * np.arange(h) / h) - 2
    kx = 2 * np.cos(np.pi * np.arange(w) / w) - 2
    den = ky[:, None] + kx[None, :]
    den[0, 0] = 1
    p = d / den
    p[0, 0] = 0
    return fft.idctn(p, type=2, norm="ortho").astype(np.float32)


def even_out(phi, passes=2, floor=0.25):
    """Keep the direction of grad(phi) but make its length one: the lines
    keep their course and get an even pitch."""
    for _ in range(passes):
        gy, gx = np.gradient(phi)
        m = np.sqrt(gx * gx + gy * gy)
        m = np.maximum(m, floor * np.median(m))
        vx, vy = gx / m, gy / m
        div = np.gradient(vx, axis=1) + np.gradient(vy, axis=0)
        phi = poisson(div)
    return phi


def form_field(L, mask, theta, spacing, relief=1.0, curl=0.6, sig_form=None, sig_curl=None, calm=1.0):
    """A ruling at angle theta, displaced by the head's relief.

    relief: large-scale bend (the lines wrap round cheek, brow, skull)
    curl:   mid-scale bend (curls and folds become rings of line)"""
    h, w = L.shape
    sig_form = sig_form or spacing * 9
    sig_curl = sig_curl or spacing * 1.6
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    ramp = yy * math.cos(theta) + xx * math.sin(theta)
    # relief: the lit marble reads as nearer, shaped by the silhouette
    m = mask if mask is not None else np.ones_like(L)
    depth = cv2.GaussianBlur(cv2.distanceTransform((m > 0.5).astype(np.uint8), cv2.DIST_L2, 5), (0, 0), sig_form)
    depth = depth / max(depth.max(), 1)
    shade = cv2.GaussianBlur(L, (0, 0), sig_form * 0.6)
    fine = cv2.GaussianBlur(L, (0, 0), sig_curl) - cv2.GaussianBlur(L, (0, 0), sig_curl * 4)
    fine = fine / (fine.std() + 1e-6)
    fine = 2.2 * np.tanh(fine / 2.2)   # no single pit may close into a ring
    # curls only where the stone is carved busy (hair, beard); smooth skin keeps a calm ruling
    energy = cv2.GaussianBlur(np.abs(fine), (0, 0), spacing * 5)
    busy = np.clip(energy / (np.percentile(energy[m > 0.5], 80) + 1e-6), calm, 1.0) if calm < 1 else 1.0
    scale = max(h, w)
    phi = ramp + relief * scale * 0.06 * (0.6 * np.sqrt(depth) + 0.4 * shade) + curl * spacing * 9 * fine * busy * m
    return phi


# ------------------------------------------------------------------ drawing
def pitch_of(phi, spacing):
    """Local distance between neighbouring lines, in px."""
    gy, gx = np.gradient(phi / spacing)
    g = np.sqrt(gx * gx + gy * gy)
    return 1 / np.clip(g, 1 / (spacing * 3.5), 1 / (spacing * 0.3))


def lines(phi, spacing, cover, phase=0.0, max_frac=0.92, pitch=None):
    """Line coverage in [0,1]. cover is the fraction of each pitch the line
    fills (0 = no line, 1 = solid), so tone survives an uneven pitch. Lines
    sit on integer values of phi/spacing + phase; pass a precomputed pitch
    when the same field is drawn many times (film frames)."""
    s = phi / spacing + phase
    if pitch is None:
        pitch = pitch_of(phi, spacing)
    off = np.abs(s - np.floor(s + 0.5))              # 0 at a line centre, 0.5 between lines
    half = 0.5 * np.clip(cover, 0, max_frac)          # half width, pitch units
    return np.clip((half - off) * pitch + 0.5, 0, 1).astype(np.float32)


def hexbgr(h):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return np.array([b, g, r], np.float32)


def compose(layers, ground):
    """layers: list of (coverage, colour). Lines are laid on the ground in order."""
    h, w = layers[0][0].shape
    out = np.empty((h, w, 3), np.float32)
    out[:] = hexbgr(ground)
    for cov, col in layers:
        c = hexbgr(col) if isinstance(col, str) else col
        out = out * (1 - cov[..., None]) + c[None, None, :] * cov[..., None]
    return out


def save(img, path, q=86):
    out = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    if path.endswith(".webp"):
        cv2.imwrite(path, out, [cv2.IMWRITE_WEBP_QUALITY, q])
    else:
        cv2.imwrite(path, out, [cv2.IMWRITE_JPEG_QUALITY, 92])
