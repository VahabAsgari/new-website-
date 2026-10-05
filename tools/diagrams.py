"""Scientific diagrams drawn as engraved line work.

Each function returns an ink mask (float32, 1 = line) at the requested size.
"""
import math

import cv2
import numpy as np

S = 4  # supersampling


def _canvas(w, h):
    return np.zeros((h * S, w * S), np.uint8)


def _done(big, w, h):
    return cv2.resize(big, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255


def _line(img, p, q, t=1.0):
    cv2.line(img, (int(p[0] * S), int(p[1] * S)), (int(q[0] * S), int(q[1] * S)), 255,
             max(1, int(round(t * S))), cv2.LINE_AA)


def _circle(img, c, r, t=1.0, fill=False):
    cv2.circle(img, (int(c[0] * S), int(c[1] * S)), max(1, int(r * S)), 255,
               -1 if fill else max(1, int(round(t * S))), cv2.LINE_AA)


def _hatch_rect(img, x0, y0, x1, y1, gap=3.0, t=0.8):
    y = y0
    while y <= y1:
        _line(img, (x0, y), (x1, y), t)
        y += gap


def galton(w=1200, h=1200, rows=14, balls=900, seed=11):
    """Galton's quincunx (1889): pegs, the paths of falling shot and the bell curve they build."""
    rng = np.random.default_rng(seed)
    img = _canvas(w, h)
    cx = w / 2
    top, peg_h = h * 0.12, h * 0.42
    dx = w * 0.72 / rows
    dy = peg_h / rows
    # funnel
    _line(img, (cx - w * 0.16, h * 0.03), (cx - dx * 0.6, top - dy * 0.6), 1.4)
    _line(img, (cx + w * 0.16, h * 0.03), (cx + dx * 0.6, top - dy * 0.6), 1.4)
    pegs = []
    for r in range(rows):
        for k in range(r + 1):
            x = cx + (k - r / 2) * dx
            y = top + r * dy
            pegs.append((x, y))
            _circle(img, (x, y), max(2.2, dx * 0.11), fill=True)
    # a few traced paths
    for p in range(5):
        x, y = cx, top - dy * 0.8
        k = 0
        pts = [(x, y)]
        for r in range(rows):
            k += rng.integers(0, 2)
            x = cx + (k - (r + 1) / 2) * dx
            y = top + (r + 0.5) * dy
            pts.append((x, y))
        for a, b in zip(pts, pts[1:]):
            _line(img, a, b, 0.7)
    # bins
    base = h * 0.94
    bin_top = top + rows * dy + dy * 0.4
    nb = rows + 1
    for k in range(nb + 1):
        x = cx + (k - nb / 2) * dx
        _line(img, (x, bin_top), (x, base), 1.0)
    _line(img, (cx - nb / 2 * dx, base), (cx + nb / 2 * dx, base), 1.6)
    # shot piled in bins (binomial counts)
    counts = np.bincount(rng.binomial(rows, 0.5, balls), minlength=nb)
    per_row = 3
    r_ball = dx / (per_row * 2.2 + 0.6)
    stack = math.ceil(counts.max() / per_row)
    r_ball = min(r_ball, (base - bin_top) * 0.92 / (stack * 2.1 + 1.2))
    for k, c in enumerate(counts):
        x0 = cx + (k - nb / 2) * dx + (dx - per_row * 2.2 * r_ball) / 2 - r_ball * 0.15
        for i in range(c):
            col, row = i % per_row, i // per_row
            x = x0 + r_ball * 1.25 + col * 2.2 * r_ball
            y = base - r_ball * 1.25 - row * 2.1 * r_ball
            if y < bin_top:
                break
            _circle(img, (x, y), r_ball * 0.9, fill=True)
    # the curve the shot obeys
    sig = math.sqrt(rows) / 2 * dx
    peak = (r_ball * 1.25 + (counts.max() / per_row) * 2.1 * r_ball) * 1.02
    pts = []
    for i in range(400):
        x = cx - nb / 2 * dx + i / 399 * nb * dx
        y = base - peak * math.exp(-((x - cx) ** 2) / (2 * sig * sig))
        pts.append((x, y))
    for a, b in zip(pts, pts[1:]):
        _line(img, a, b, 1.6)
    return _done(img, w, h)


MOONS = [(1.769, 5.9), (3.551, 9.4), (7.155, 15.0), (16.689, 26.4)]
PHASE = [0.3, 2.1, 4.0, 5.2]


def galileo_rows(w=1200, h=1200, nights=13):
    """Jupiter and the Medicean stars, one row per night, as Galileo recorded them."""
    img = _canvas(w, h)
    cx = w / 2
    unit = w * 0.4 / 27
    row = h * 0.86 / nights
    y0 = h * 0.07 + row / 2
    for n in range(nights):
        y = y0 + n * row
        # date tick and rule
        _line(img, (w * 0.05, y), (w * 0.09, y), 1.0)
        _line(img, (w * 0.12, y), (w * 0.95, y), 0.45)
        _circle(img, (cx, y), unit * 1.1, t=1.6)
        _hatch_rect(img, cx - unit * 0.8, y - unit * 0.55, cx + unit * 0.8, y + unit * 0.55, gap=unit * 0.33, t=0.5)
        for i, (P, a) in enumerate(MOONS):
            x = cx + math.sin(2 * math.pi * n / P + PHASE[i]) * a * unit
            if abs(x - cx) < unit * 1.3:
                continue  # behind or in front of the disc: hidden, as Galileo noted
            _circle(img, (x, y), unit * 0.32, fill=True)
    # mask out the hatch outside discs: redraw discs only (cheap: hatch is clipped by eye-level radius)
    return _done(img, w, h)


def khatam(w=1200, h=1200, cell=None):
    """The khatam: an eight-pointed star of two interlaced squares, tiled as in Persian work."""
    img = _canvas(w, h)
    c = cell or min(w, h) / 4.2
    r = c / 2  # axial points of neighbouring stars meet
    nx, ny = int(w / c) + 2, int(h / c) + 2
    ox, oy = (w - (nx - 1) * c) / 2, (h - (ny - 1) * c) / 2
    for j in range(ny):
        for i in range(nx):
            x, y = ox + i * c, oy + j * c
            for rot in (0, math.pi / 4):
                pts = [(x + math.cos(rot + math.pi / 4 + k * math.pi / 2) * r,
                        y + math.sin(rot + math.pi / 4 + k * math.pi / 2) * r) for k in range(4)]
                for k in range(4):
                    _line(img, pts[k], pts[(k + 1) % 4], 1.3)
            # inner octagon and rosette
            ri = r * 0.5412  # octagon through the star's inner corners
            oct_ = [(x + math.cos(math.pi / 8 + k * math.pi / 4) * ri, y + math.sin(math.pi / 8 + k * math.pi / 4) * ri) for k in range(8)]
            for k in range(8):
                _line(img, oct_[k], oct_[(k + 1) % 8], 0.8)
            _circle(img, (x, y), r * 0.3, t=0.8)
    return _done(img, w, h)


def rosette(w=1200, h=1200, n=8):
    """A single interlaced star rosette: {8/2} and {8/3} star polygons in nested rings."""
    img = _canvas(w, h)
    cx, cy = w / 2, h / 2
    R = min(w, h) * 0.44

    def poly(r, step, rot=0.0, t=1.3):
        pts = [(cx + math.cos(rot + 2 * math.pi * k / n) * r, cy + math.sin(rot + 2 * math.pi * k / n) * r) for k in range(n)]
        for k in range(n):
            _line(img, pts[k], pts[(k + step) % n], t)

    _circle(img, (cx, cy), R * 1.04, t=1.2)
    _circle(img, (cx, cy), R * 1.09, t=0.6)
    for i in range(96):
        a = 2 * math.pi * i / 96
        r1 = R * (1.15 if i % 12 == 0 else 1.12)
        _line(img, (cx + math.cos(a) * R * 1.09, cy + math.sin(a) * R * 1.09), (cx + math.cos(a) * r1, cy + math.sin(a) * r1), 0.8)
    poly(R, 3, -math.pi / 2, 1.5)
    poly(R * 0.86, 2, -math.pi / 2 + math.pi / 8, 1.1)
    poly(R * 0.52, 3, -math.pi / 2, 1.0)
    poly(R * 0.38, 2, -math.pi / 2 + math.pi / 8, 0.9)
    _circle(img, (cx, cy), R * 0.16, t=1.0)
    return _done(img, w, h)


def _solid(name):
    p = (1 + 5 ** .5) / 2
    if name == "cube":
        v = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    elif name == "tetra":
        v = [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)]
    elif name == "octa":
        v = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    elif name == "icosa":
        v = [(0, a, b * p) for a in (-1, 1) for b in (-1, 1)] + [(a, b * p, 0) for a in (-1, 1) for b in (-1, 1)] + [(b * p, 0, a) for a in (-1, 1) for b in (-1, 1)]
    elif name == "dodeca":
        v = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
        v += [(0, a / p, b * p) for a in (-1, 1) for b in (-1, 1)] + [(a / p, b * p, 0) for a in (-1, 1) for b in (-1, 1)] + [(b * p, 0, a / p) for a in (-1, 1) for b in (-1, 1)]
    v = np.array(v, np.float64)
    v /= np.linalg.norm(v, axis=1).max()
    d = np.linalg.norm(v[:, None] - v[None], axis=2)
    m = d[d > 1e-6].min()
    edges = [(i, j) for i in range(len(v)) for j in range(i + 1, len(v)) if abs(d[i, j] - m) < 1e-6]
    return v, edges


INRADIUS = {"cube": 1 / 3 ** .5, "tetra": 1 / 3, "dodeca": 0.7947, "icosa": 0.7947, "octa": 1 / 3 ** .5}


def kepler(w=1200, h=1200, rot=(0.55, 0.42, 0.15)):
    """Kepler, Mysterium cosmographicum (1596): the planetary spheres held apart by the five solids."""
    img = _canvas(w, h)
    cx, cy = w / 2, h / 2
    R = min(w, h) * 0.45
    ax, ay, az = rot
    Rx = np.array([[1, 0, 0], [0, math.cos(ax), -math.sin(ax)], [0, math.sin(ax), math.cos(ax)]])
    Ry = np.array([[math.cos(ay), 0, math.sin(ay)], [0, 1, 0], [-math.sin(ay), 0, math.cos(ay)]])
    Rz = np.array([[math.cos(az), -math.sin(az), 0], [math.sin(az), math.cos(az), 0], [0, 0, 1]])
    M = Rz @ Ry @ Rx
    r = R
    for k, name in enumerate(["cube", "tetra", "dodeca", "icosa", "octa"]):
        # sphere: outline plus a tilted equator
        _circle(img, (cx, cy), r, t=1.4 if k == 0 else 0.9)
        eq = [(cx + math.cos(t) * r, cy + math.sin(t) * r * math.sin(ax)) for t in np.linspace(0, 2 * math.pi, 180)]
        for a, b in zip(eq, eq[1:]):
            _line(img, a, b, 0.5)
        v, edges = _solid(name)
        p = (v @ M.T) * r
        for i, j in edges:
            front = (p[i, 2] + p[j, 2]) / 2 > -0.15 * r
            _line(img, (cx + p[i, 0], cy - p[i, 1]), (cx + p[j, 0], cy - p[j, 1]), 1.3 if front else 0.45)
        r *= INRADIUS[name]
    _circle(img, (cx, cy), r, t=0.9)
    _circle(img, (cx, cy), max(3, R * 0.012), fill=True)
    return _done(img, w, h)


def huygens(w=1200, h=1200, positions=9):
    """Huygens, Horologium oscillatorium (1673): a pendulum between cycloidal cheeks swings in equal time."""
    img = _canvas(w, h)
    cx = w / 2
    a = w * 0.125  # cycloid generating radius
    top = h * 0.2
    # cheeks: two cycloid arcs hanging from the pivot
    for s in (-1, 1):
        pts = [(cx + s * a * (t - math.sin(t)), top + a * (1 - math.cos(t))) for t in np.linspace(0, math.pi, 120)]
        for p, q in zip(pts, pts[1:]):
            _line(img, p, q, 1.6)
    # the bob's path: an inverted cycloid of the same size, four radii below
    L = 4 * a
    path = [(cx + a * (t + math.sin(t)), top + a * (3 + math.cos(t))) for t in np.linspace(-math.pi, math.pi, 240)]
    for p, q in zip(path, path[1:]):
        _line(img, p, q, 0.9)
    # pendulum positions: thread wraps the cheek, then runs tangent to the bob
    for k in range(positions):
        t = -math.pi * 0.86 + k * (2 * math.pi * 0.86) / (positions - 1)
        bob = (cx + a * (t + math.sin(t)), top + a * (3 + math.cos(t)))
        # contact point on the cheek on the side of the swing
        s = 1 if t > 0 else -1
        u = abs(t)
        contact = (cx + s * a * (u - math.sin(u)), top + a * (1 - math.cos(u)))
        wrap = [(cx + s * a * (q - math.sin(q)), top + a * (1 - math.cos(q))) for q in np.linspace(0, u, 40)]
        for p, q in zip(wrap, wrap[1:]):
            _line(img, p, q, 1.0)
        _line(img, contact, bob, 0.8 if k not in (0, positions // 2, positions - 1) else 1.3)
        _circle(img, bob, w * 0.018 if k == positions // 2 else w * 0.011, fill=True)
    # pivot and frame
    _line(img, (cx - w * 0.38, top), (cx + w * 0.38, top), 2.0)
    _hatch_rect(img, cx - w * 0.38, top - h * 0.04, cx + w * 0.38, top, gap=6, t=0.7)
    # time ticks under the path
    base = top + L + h * 0.08
    _line(img, (cx - w * 0.4, base), (cx + w * 0.4, base), 0.8)
    for i in range(41):
        x = cx - w * 0.4 + i * w * 0.02
        _line(img, (x, base), (x, base + (h * 0.03 if i % 5 == 0 else h * 0.015)), 0.8)
    return _done(img, w, h)
