"""Home hero: the ATV orbit render, engraved with the flag's line screen and grade.

  python3 tools/sat_film.py SRC.mp4 OUTDIR [start_s dur_s] [--test]

Frames are read through ffmpeg, drawn at K x size and averaged down, written
to OUTDIR as PNG. The last XF seconds are cross-faded into the first so the
loop has no seam.
"""
import os, subprocess, sys
from multiprocessing import Pool
import cv2, numpy as np
from PIL import Image

W0, H0, K, FPS, XF = 1920, 1080, 2, 25, 1.6
GB = lambda a, s: cv2.GaussianBlur(a, (0, 0), s)
H, W = H0*K, W0*K
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
U0 = 0.94*yy + 0.34*xx                      # same diagonal as the flag
vy = np.linspace(-1, 1, H)[:, None]; vx = np.linspace(-1, 1, W)[None, :]
vig = (1 - 0.30*(vx**2 + 0.5*vy**2)).clip(0.45, 1)
# earth recedes: brightness falls off below the limb, so the craft stands in front
fall = 1 - 0.42*((vy + 0.05)/1.05).clip(0, 1)**0.8
noise = 0.006*np.random.default_rng(3).standard_normal((H0, W0)).astype(np.float32)


def lines(T, R, P, relief, w0, w1):
    pp = P*K; u = U0 + relief*K*R
    d = np.abs(np.mod(u/pp, 1) - 0.5)*pp
    return ((w0 + w1*T)*pp*0.5 - d + 0.5).clip(0, 1)


def engrave(rgb):
    rgb = cv2.resize(rgb.astype(np.float32)/255, (W, H), interpolation=cv2.INTER_CUBIC).clip(0, 1)
    Y = 0.2126*rgb[..., 0] + 0.7152*rgb[..., 1] + 0.0722*rgb[..., 2]
    # craft: bright, saturated-free metal; separate it from the blue limb/clouds by local contrast
    T = (Y*fall).clip(0, 1)
    T = (0.55*T + 0.45*GB(T, 10*K) + 1.0*(T - GB(T, 4*K))).clip(0, 1)**1.45
    R = GB(T, 3*K) - GB(T, 22*K)
    L = lines(T, R, 3.6, 2.0, 0.02, 0.85)
    amp = 0.20 + 0.75*T
    o = (0.45*(0.02 + 0.85*T)*amp + 0.55*L*amp)*vig
    o = 0.012 + 0.97*o
    o = cv2.resize(o, (W0, H0), interpolation=cv2.INTER_AREA) + noise
    g = (o.clip(0, 1)**(1/1.08)*255)
    return np.dstack([g*0.985, g*0.995, g]).clip(0, 255).astype(np.uint8)


def read(src, start, dur):
    cmd = ['ffmpeg', '-v', 'error', '-ss', str(start), '-t', str(dur), '-i', src,
           '-vf', f'scale={W0}:{H0}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H0, W0, 3)


def job(a):
    i, fr, out = a
    Image.fromarray(engrave(fr)).save(f'{out}/f{i:04d}.png')


if __name__ == '__main__':
    src, out = sys.argv[1], sys.argv[2]
    start = float(sys.argv[3]) if len(sys.argv) > 3 else 0
    dur = float(sys.argv[4]) if len(sys.argv) > 4 else 16
    os.makedirs(out, exist_ok=True)
    if '--test' in sys.argv:
        fr = read(src, start, 0.04)[0]
        Image.fromarray(engrave(fr)).save(f'{out}/test.png'); sys.exit()
    frs = read(src, start, dur + XF).copy()
    n = int(round(dur*FPS)); m = len(frs) - n
    # tail cross-fades into the head: frame i (< m) = mix of head i and tail n+i
    for i in range(m):
        a = (i + 0.5)/m
        frs[i] = (frs[i]*a + frs[n + i].astype(np.float32)*(1 - a)).round().astype(np.uint8)
    frs = frs[:n]
    with Pool(4) as p:
        for _ in p.imap_unordered(job, ((i, frs[i], out) for i in range(n)), chunksize=2): pass
        p.close(); p.join()
    print('done', n)
