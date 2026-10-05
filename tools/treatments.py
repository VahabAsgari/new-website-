"""Joveyra image treatments.

Two processes, one rule each:
  engraving  -> the paper of the print becomes the page blue, the ink becomes
                near-black. Only the engraved lines carry the image.
  cyanotype  -> light becomes paper white, shadow becomes Prussian blue, with
                uneven exposure, grain and a brushed emulsion edge.
"""
import cv2
import numpy as np

rng = np.random.default_rng(7)


def bgr(hex_):
    h = hex_.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (4, 2, 0)], np.float32)


def load_gray(path, crop=None, maxw=2400):
    g = cv2.imread(path, cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255
    return _crop_resize(g, crop, maxw)


def load_bgr(path, crop=None, maxw=2400):
    return _crop_resize(cv2.imread(path), crop, maxw)


def _crop_resize(im, crop, maxw):
    if crop:
        h, w = im.shape[:2]
        x0, y0, x1, y1 = crop
        im = im[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]
    if im.shape[1] > maxw:
        s = maxw / im.shape[1]
        im = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    return im


# --------------------------------------------------------------------- engraving
ENGRAVING = dict(paper="#3352c4", ink="#02040b")


def engraving(gray, paper=ENGRAVING["paper"], ink=ENGRAVING["ink"], gamma=1.15):
    # flatten the paper tone with a wide max-filter so old, stained paper reads
    # as one even field (wide window = no halos at line scale)
    est = cv2.GaussianBlur(cv2.dilate(gray, np.ones((61, 61))), (0, 0), 40)
    n = np.clip(gray / np.maximum(est, 1e-3), 0, 1)
    lo = np.percentile(n, 2)
    light = np.clip((n - lo) / (0.97 - lo), 0, 1) ** gamma
    return bgr(ink) + (bgr(paper) - bgr(ink)) * light[..., None]


# --------------------------------------------------------------------- cyanotype
CYAN_DEEP, CYAN_PRUSS, CYAN_MID, CYAN_PAPER = (
    bgr("#06204f"), bgr("#0d3b86"), bgr("#4573b5"), bgr("#eef1ea"))


def _noise(shape, sigma):
    n = cv2.GaussianBlur(rng.standard_normal(shape).astype(np.float32), (0, 0), sigma)
    return n / (n.std() + 1e-6)


def cyanotype(light, edge=True):
    """light: 0..1, 1 = unexposed paper (white), 0 = full exposure (deep blue)."""
    h, w = light.shape
    t = light + 0.06 * _noise((h, w), max(h, w) / 18) \
              + 0.03 * _noise((h, w), max(h, w) / 60) \
              + 0.035 * _noise((h, w), 0.8)
    t = np.clip(t, 0, 1)[..., None]
    out = np.where(t < 0.35, CYAN_DEEP + (CYAN_PRUSS - CYAN_DEEP) * (t / 0.35),
          np.where(t < 0.7, CYAN_PRUSS + (CYAN_MID - CYAN_PRUSS) * ((t - 0.35) / 0.35),
                   CYAN_MID + (CYAN_PAPER - CYAN_MID) * ((t - 0.7) / 0.3)))
    if edge:  # brushed emulsion border that dissolves into the page colour
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        d = np.minimum.reduce([xx, yy, w - 1 - xx, h - 1 - yy]) / max(h, w)
        m = np.clip((d + 0.012 * _noise((h, w), 6) - 0.01) / 0.05, 0, 1)[..., None]
        out = CYAN_DEEP + (out - CYAN_DEEP) * m
    return out


def photo_light(im, gamma=1.1):
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    lo, hi = np.percentile(g, [1, 99.5])
    return np.clip((g - lo) / (hi - lo), 0, 1) ** gamma


def object_light(im):
    """A museum object shot on a grey sweep: the object prints as luminous
    detail, the sweep becomes fully exposed (deep blue) - a photogram."""
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(np.float32)
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    m = ((hsv[..., 1] / 255 > 0.18) |
         (np.abs(g - cv2.GaussianBlur(g, (0, 0), 40)) > 0.08)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    keep = (lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8) if n > 1 else m
    keep = cv2.morphologyEx(keep, cv2.MORPH_CLOSE, np.ones((41, 41), np.uint8))
    ff = keep.copy()
    cv2.floodFill(ff, np.zeros((ff.shape[0] + 2, ff.shape[1] + 2), np.uint8), (0, 0), 1)
    keep = keep | (1 - ff)
    soft = cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 3)
    return np.clip(photo_light(im, 0.85) * 1.08, 0, 1) * soft


def save(img, path, quality=74):
    out = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    if path.endswith(".webp"):
        cv2.imwrite(path, out, [cv2.IMWRITE_WEBP_QUALITY, quality])
    else:
        cv2.imwrite(path, out, [cv2.IMWRITE_JPEG_QUALITY, quality])
