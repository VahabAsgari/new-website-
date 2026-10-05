"""Line-art plates for Joveyra.

Every engraving is reduced to its lines (two tones, no grey), cut into a shape,
and set inside a constructed drawing of measurement lines. Output is RGBA so
the page colour shows through the ink: the lines *are* the page.
"""
import math

import cv2
import numpy as np


def ink_mask(gray, block=31, c=9, min_area=6):
    """1 where the engraver cut a line, 0 for paper."""
    g = (gray * 255).astype(np.uint8) if gray.dtype != np.uint8 else gray
    g = cv2.GaussianBlur(g, (0, 0), 0.6)
    m = cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, block, c)
    # drop isolated specks of paper grain
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    keep = np.zeros(n, bool)
    keep[1:] = st[1:, cv2.CC_STAT_AREA] >= min_area
    return keep[lab].astype(np.float32)


def solid_regions(ink, size=9):
    """Areas that are almost all ink (deep shadow) - kept as solid shadow."""
    dens = cv2.blur(ink, (size, size))
    return (dens > 0.82).astype(np.float32)


def rgba(ink, color, mode="paper", alpha=None):
    """mode 'paper': paper is drawn in `color`, ink is transparent (positive).
    mode 'ink':   ink is drawn in `color`, paper is transparent."""
    a = (1 - ink) if mode == "paper" else ink
    if alpha is not None:
        a = a * alpha
    h, w = ink.shape
    out = np.zeros((h, w, 4), np.float32)
    out[..., :3] = np.array(color, np.float32)[None, None, ::-1]
    out[..., 3] = a
    return out


def hexrgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


# ------------------------------------------------------------- construction lines
def draw_aperture(canvas_shape, cx, cy, r, ticks=180, rays=0, ray_len=(1.05, 1.9), seed=3,
                  rings=(1.0, 1.035), thickness=1.4):
    """Graduated circle (like a sextant limb), optional bundles of sight-lines."""
    h, w = canvas_shape
    S = 4  # supersample for clean antialiased lines
    big = np.zeros((h * S, w * S), np.uint8)
    t = max(1, int(round(thickness * S)))
    for k in rings:
        cv2.circle(big, (int(cx * S), int(cy * S)), int(r * k * S), 255, t, cv2.LINE_AA)
    for i in range(ticks):
        a = 2 * math.pi * i / ticks
        l0 = 1.035 if i % 5 else 1.035
        l1 = 1.07 if i % 5 else 1.11
        p0 = (cx + math.cos(a) * r * l0, cy + math.sin(a) * r * l0)
        p1 = (cx + math.cos(a) * r * l1, cy + math.sin(a) * r * l1)
        cv2.line(big, (int(p0[0] * S), int(p0[1] * S)), (int(p1[0] * S), int(p1[1] * S)), 255, t, cv2.LINE_AA)
    rng = np.random.default_rng(seed)
    for b in range(rays):
        base = rng.uniform(0, 2 * math.pi)
        n = rng.integers(9, 18)
        for j in range(n):
            a = base + rng.normal(0, 0.05)
            l0, l1 = ray_len[0], rng.uniform(ray_len[0] + 0.3, ray_len[1])
            p0 = (cx + math.cos(a) * r * l0, cy + math.sin(a) * r * l0)
            p1 = (cx + math.cos(a + rng.normal(0, 0.03)) * r * l1, cy + math.sin(a + rng.normal(0, 0.03)) * r * l1)
            cv2.line(big, (int(p0[0] * S), int(p0[1] * S)), (int(p1[0] * S), int(p1[1] * S)), 255, t, cv2.LINE_AA)
    return cv2.resize(big, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255


def circle_alpha(shape, cx, cy, r, feather=1.5):
    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    return np.clip((r - d) / feather, 0, 1)


def save_png(img, path):
    out = np.clip(img, 0, 1)
    bgra = (out[..., [0, 1, 2, 3]] * 255).astype(np.uint8)
    cv2.imwrite(path, bgra)


def save_webp(img, path, q=101):
    """q=101 is lossless: two-tone line art is far smaller lossless than lossy."""
    out = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    if q > 100 and out.ndim == 3:
        # snap to a small palette so lossless coding stays compact
        out = (np.round(out / 17) * 17).astype(np.uint8)
    cv2.imwrite(path, out, [cv2.IMWRITE_WEBP_QUALITY, q])
