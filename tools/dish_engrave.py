import sys, numpy as np, cv2
from PIL import Image
SRC, MSK, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
K = 2
rgb = np.array(Image.open(SRC).convert('RGB')).astype(np.float32)/255
Y0 = (0.2126*rgb[...,0]+0.7152*rgb[...,1]+0.0722*rgb[...,2])
M0 = np.array(Image.open(MSK).convert('L')).astype(np.float32)/255
h, w = Y0.shape; H, W = h*K, w*K
up = lambda a: cv2.resize(a, (W, H), interpolation=cv2.INTER_CUBIC)
Y, M = up(Y0).clip(0,1), up(M0).clip(0,1)
GB = lambda a, s: cv2.GaussianBlur(a, (0,0), s)

md = cv2.dilate((M0>0.3).astype(np.uint8), np.ones((9,9),np.uint8))
bg8 = cv2.inpaint((Y0*255).astype(np.uint8), md, 9, cv2.INPAINT_TELEA)
B = up(bg8.astype(np.float32)/255)

# bigger dishes (sky is cropped below to make room)
s, ax, ay, bx = 1.25, 466*K, 1190*K, 540*K
A = np.float32([[s,0,bx-s*ax],[0,s,ay-s*ay]])
Yd = cv2.warpAffine(Y, A, (W,H), flags=cv2.INTER_CUBIC, borderValue=1)
Md = GB(cv2.warpAffine(M, A, (W,H), flags=cv2.INTER_LINEAR), 0.8).clip(0,1)

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
U0 = 0.94*yy + 0.34*xx
def lines(T, R, P, relief, w0, w1):
    pp = P*K
    u = U0 + relief*K*R
    d = np.abs(np.mod(u/pp, 1) - 0.5)*pp
    return ((w0 + w1*T)*pp*0.5 - d + 0.5).clip(0,1)

# dishes: keep the photo's own contrast (global stretch, steeper curve)
v = Yd[Md>0.5]; lo, hi = np.percentile(v, 0.5), np.percentile(v, 99.8)
Td = ((Yd-lo)/(hi-lo)).clip(0,1)
Td = (Td + 0.6*(Td-GB(Td, 12*K))).clip(0,1)**2.1
Ld = lines(Td, GB(Td,3*K)-GB(Td,22*K), 6.0, 4, 0.03, 0.80)
dish = 0.01 + 0.98*Ld*(0.38+0.62*Td)

# floor: snow, same engraving but recessed
fy = 1192*K
Fm = (1/(1+np.exp(-(yy-fy)/(3*K)))) * (1-Md)
fv = B[int(fy)+8*K:]; flo, fhi = np.percentile(fv, 1), np.percentile(fv, 99.5)
Tf = ((B-flo)/(fhi-flo)).clip(0,1)
Tf = (GB(Tf,1.2*K) + 0.9*(Tf-GB(Tf, 10*K))).clip(0,1)**1.3          # bring out footprints/drifts
depth = 1 - 0.45*((yy-fy)/(H-fy)).clip(0,1)                # recede towards the viewer
Lf = lines(Tf, GB(Tf,3*K)-GB(Tf,18*K), 6.0, 3, 0.10, 0.55)

vy = np.linspace(-1,1,H)[:,None]; vx = np.linspace(-1,1,W)[None,:]
vig = (1-0.35*(vx**2+0.6*vy**2)).clip(0.4,1)
sky = (0.035 + 0.10*((B-0.55)/0.45).clip(0,1)**1.6)*vig

def render(fk, tag, crop=260):
    floor = 0.03 + fk*Lf*(0.45+0.55*Tf)*depth
    bgv = sky*(1-Fm) + floor*vig*Fm
    o = bgv*(1-Md) + dish*Md
    o = o + 0.006*np.random.default_rng(3).standard_normal(o.shape)
    g = (o.clip(0,1)**(1/1.08)*255).astype(np.uint8)[crop*K:]
    im = Image.fromarray(np.dstack([g*0.985, g*0.995, g]).clip(0,255).astype(np.uint8))
    im.save(f'{OUT}/dish_v4_{tag}.png'); return im

ims = [render(0.28,'final')]
print(ims[0].size)
