"""Engraved plates and films for joveyra.com.

A Plate places one statue on a canvas of the page's proportions, works out
its line fields once, and then draws them as often as needed: once for a
still, a few hundred times for a film. Only the line phase and the line
weight change from frame to frame, so a frame costs one pass of
engrave.lines() per family of lines.
"""
import math

import cv2
import numpy as np

import engrave as E

SRC = "tools/source/"
GROUND, LINE, RULE, COPPER = "#070a1c", "#eef0f6", "#2c3fd6", "#c4733f"


class Plate:
    def __init__(self, src, crop, size, box, sp=8.0, theta=-14, relief=3.0, curl=0.0, calm=0.0,
                 gamma=1.6, rect=None, kill=(), hatch=True, rule=0.2, bend=70, S=2, mask_iters=6):
        """src:  Met file name in tools/source
        crop: (x0, y0, x1, y1) fractions of the source that hold the head
        size: (w, h) of the output in px
        box:  (cx, cy, hf) head centre as fractions of the canvas and head
              height as a fraction of canvas height
        sp:   line pitch at output size, px
        kill: rectangles (fractions of the cropped head) taken out of the mask"""
        self.W, self.H, self.S = size[0], size[1], S
        W, H = self.W * S, self.H * S
        cx, cy, hf = box
        hh = int(round(hf * H))
        im = E.load(SRC + src, crop=crop, width=2000)
        ih, iw = im.shape[:2]
        hw = int(round(iw * hh / ih))
        im = cv2.resize(im, (hw, hh), interpolation=cv2.INTER_AREA if hh < ih else cv2.INTER_CUBIC)
        m = E.subject_mask(im, rect=rect, iters=mask_iters)
        for k in kill:
            m[int(k[1] * hh):int(k[3] * hh), int(k[0] * hw):int(k[2] * hw)] = 0
        # paste into the canvas
        L = np.zeros((H, W), np.float32)
        M = np.zeros((H, W), np.float32)
        x0, y0 = int(cx * W - hw / 2), int(cy * H - hh / 2)
        sx0, sy0 = max(0, -x0), max(0, -y0)
        dx0, dy0 = max(0, x0), max(0, y0)
        dx1, dy1 = min(W, x0 + hw), min(H, y0 + hh)
        L[dy0:dy1, dx0:dx1] = E.luminance(im)[sy0:sy0 + dy1 - dy0, sx0:sx0 + dx1 - dx0]
        M[dy0:dy1, dx0:dx1] = m[sy0:sy0 + dy1 - dy0, sx0:sx0 + dx1 - dx0]
        M = cv2.GaussianBlur(M, (0, 0), 2 * S)
        self.mask = M
        spS = sp * S
        self.sp = spS
        Ls = cv2.GaussianBlur(L, (0, 0), 0.4 * spS)
        self.T = E.tone(Ls, M, gamma=gamma)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        self.yy, self.xx = yy, xx
        self.bphi = yy + bend * S * cv2.GaussianBlur(M, (0, 0), 50 * S)
        self.bpitch = E.pitch_of(self.bphi, spS)
        self.rule = rule
        self.Ls = Ls
        self.hatch = hatch
        self.field(theta, relief, curl, calm)

    def field(self, theta=-14, relief=3.0, curl=0.0, calm=0.0, sig_curl=5.0, hatch_at=0.78, hatch_cover=0.5):
        Ls, M, spS = self.Ls, self.mask, self.sp
        self.phi = E.form_field(Ls, M, math.radians(theta), spS, relief=relief, curl=curl,
                                sig_curl=spS * sig_curl, calm=calm)
        self.pitch = E.pitch_of(self.phi, spS)
        if self.hatch:
            self.phi2 = E.form_field(Ls, M, math.radians(theta + 52), spS, relief=relief, curl=curl * 0.4,
                                     sig_curl=spS * sig_curl)
            self.pitch2 = E.pitch_of(self.phi2, spS)
            self.hatch_at, self.hatch_cover = hatch_at, hatch_cover
            self.hi = np.clip((self.T - hatch_at) / (1 - hatch_at), 0, 1)

    # -------------------------------------------------------------- drawing
    def layers(self, phase=0.0, light=None, reveal=None, breveal=None, weight=1.0):
        """light:   extra cover added to the head lines (a band of light)
        reveal:  0..1 per pixel, how much of each head line has been cut
        breveal: the same for the background ruling
        weight:  0 = every head line a hairline, 1 = full tone"""
        T = self.T if light is None else np.clip(self.T + light, 0, 1)
        cover = (0.06 + 0.94 * T * weight) * self.mask
        head = E.lines(self.phi, self.sp, cover, phase=phase, pitch=self.pitch)
        if self.hatch:
            hi = self.hi if light is None else np.clip((T - self.hatch_at) / (1 - self.hatch_at), 0, 1)
            head = np.maximum(head, E.lines(self.phi2, self.sp, hi * self.hatch_cover * weight * self.mask,
                                            phase=phase, pitch=self.pitch2))
        if reveal is not None:
            head = head * reveal
        bg = E.lines(self.bphi, self.sp, np.full_like(self.T, self.rule), pitch=self.bpitch) * (1 - self.mask)
        if breveal is not None:
            bg = bg * breveal
        return bg, head

    def render(self, zoom=1.0, extra=(), **kw):
        bg, head = self.layers(**kw)
        img = E.compose([(bg, RULE), (head, LINE), *extra], GROUND)
        return self.down(img, zoom)

    def down(self, img, zoom=1.0):
        H, W = img.shape[:2]
        if zoom != 1.0:
            cw, ch = W / zoom, H / zoom
            x0, y0 = (W - cw) / 2, (H - ch) / 2
            # crop with sub-pixel accuracy, then area-average down to output
            M = np.float32([[1, 0, -x0], [0, 1, -y0]])
            img = cv2.warpAffine(img, M, (int(math.ceil(cw)), int(math.ceil(ch))), flags=cv2.INTER_LINEAR)
        return cv2.resize(img, (self.W, self.H), interpolation=cv2.INTER_AREA)

    def line_index(self):
        """Integer index of the head line each pixel belongs to, 0..1."""
        k = np.floor(self.phi / self.sp + 0.5)
        sel = k[self.mask > 0.5]
        return np.clip((k - sel.min()) / max(sel.max() - sel.min(), 1), 0, 1)

    def rule_index(self):
        k = np.floor(self.bphi / self.sp + 0.5)
        return (k - k.min()) / max(k.max() - k.min(), 1)


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def to8(img):
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)
