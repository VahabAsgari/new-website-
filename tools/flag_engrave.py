import sys, numpy as np, cv2
from PIL import Image
SRC, MD, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
K = 2
rgb = np.array(Image.open(SRC).convert('RGB')).astype(np.float32)/255
Y0 = 0.2126*rgb[...,0]+0.7152*rgb[...,1]+0.0722*rgb[...,2]
S0 = np.array(Image.open(f'{MD}/subj.png').convert('L')).astype(np.float32)/255
Hl0 = np.array(Image.open(f'{MD}/hill.png').convert('L')).astype(np.float32)/255
h, w = Y0.shape; H, W = h*K, w*K
up = lambda a: cv2.resize(a, (W, H), interpolation=cv2.INTER_CUBIC).clip(0,1)
GB = lambda a, s: cv2.GaussianBlur(a, (0,0), s)
Y = up(Y0); Ms = GB(up(S0), 0.8); Mh = GB(up(Hl0), 1.5)*(1-Ms)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
U0 = 0.94*yy + 0.34*xx
def lines(T, R, P, relief, w0, w1, U=None):
    pp = P*K; u = (U0 if U is None else U) + relief*K*R
    d = np.abs(np.mod(u/pp, 1) - 0.5)*pp
    return ((w0 + w1*T)*pp*0.5 - d + 0.5).clip(0,1)
def stretch(A, m, a, b):
    v = A[m]; lo, hi = np.percentile(v, a), np.percentile(v, b); return ((A-lo)/(hi-lo)).clip(0,1)

# subject: men, rocks, flag; photo contrast kept
flag = np.zeros_like(Y0); cv2.fillPoly(flag, [np.int32([[655,70],[925,170],[880,290],[650,200]])], 1)
logo0 = ((Y0>0.5)*flag*S0).astype(np.float32)
Ts = stretch(Y, (Ms>0.5)&(up(cv2.dilate(logo0,np.ones((5,5))))<0.1), 1.0, 99.0)
# depth: keep the suits dark, only lit planes (shoulders, backs, folds) open up
Tb = GB(Ts, 14*K)
Ts = (0.6*Ts + 0.4*Tb + 1.1*(Ts-GB(Ts, 5*K))).clip(0,1)**1.6
# soften the bright rim the cut-out leaves on the silhouette
inner = GB(cv2.erode((Ms>0.5).astype(np.float32), np.ones((3*K,3*K))), 1.5*K)
Ts = Ts*(0.55+0.45*inner)
VAR = sys.argv[4]
Rr = GB(Ts,3*K)-GB(Ts,20*K)
if VAR == 'a':   # fine straight engraving
    Ls = lines(Ts, Rr, 3.4, 1.5, 0.02, 0.85)
elif VAR == 'b': # lines wrap around the forms (contour engraving)
    Rc = GB(Ts,6*K) - GB(Ts,30*K)
    Ls = lines(Ts, Rc, 4.2, 14, 0.02, 0.85)
else:            # horizontal banknote engraving
    Uh = 1.0*yy + 0.05*xx
    Ls = lines(Ts, GB(Ts,4*K)-GB(Ts,24*K), 4.5, 8, 0.02, 0.85, Uh)
# thin parts (pole, hands) drawn solid so they don't break into dashes
sb = (S0>0.5).astype(np.uint8)
thin = up(GB((sb - cv2.morphologyEx(sb, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,9)))).astype(np.float32), 0.6))
# pole: a quiet grey stroke, not a white bar; hands keep a faint solid fill
pole = np.zeros_like(Y0); cv2.fillPoly(pole, [np.int32([[700,55],[722,62],[625,300],[598,296]])], 1)
pole = up(pole)
Ls = np.maximum(Ls, thin*(1-pole)*(0.15+0.5*Ts))
Ls = Ls*(1-pole) + np.maximum(Ls, thin*0.30)*0.75*pole
# flag logo drawn solid white so it stays legible
logo = up(logo0); logo = GB(logo, 0.7)
# flag cloth: its own brighter tone, folds kept
cloth = GB(up(flag*S0)*(1-up(cv2.dilate(logo0,np.ones((3,3))))), 0.8)*(1-pole)
Tc = stretch(Y, cloth>0.5, 1, 99.5)
Tc = (0.3 + 0.55*(GB(Tc,1.5*K) + 0.8*(Tc-GB(Tc,12*K)))).clip(0,1)
Lc = lines(Tc, GB(Tc,4*K)-GB(Tc,24*K), 4.2, 6, 0.06, 0.65)
halo = GB(up(cv2.dilate(logo0,np.ones((5,5)))),1.0)*(1-logo)*0.85
amp = 0.26+0.70*Ts
men = 0.5*(0.02+0.85*Ts)*amp + 0.5*Ls*amp  # lines half-blended into tone: quieter texture, same light
subj = 0.01 + 0.98*np.maximum(men*(1-cloth) + Lc*(0.18+0.30*Tc)*cloth*(1-halo), logo*0.80)

# hill floor: same engraving, recessed (dish B level)
Tf = stretch(Y, Mh>0.5, 1, 99.5)
Tf = (GB(Tf,1.2*K) + 0.9*(Tf-GB(Tf, 10*K))).clip(0,1)**1.3
top = 556*K; depth = 1 - 0.45*((yy-top)/(H-top)).clip(0,1)
Lf = lines(Tf, GB(Tf,3*K)-GB(Tf,18*K), 6.0, 3, 0.10, 0.55)
# distant plain: even quieter
hz = 484*K; Mland = (1/(1+np.exp(-np.clip((yy-hz)/(2*K),-50,50))))*(1-Mh)*(1-Ms)
Tl = stretch(Y, Mland>0.5, 1, 99.5); Tl = GB(Tl, 1.0*K)**1.2
Ll = lines(Tl, 0*Tl, 6.0, 0, 0.06, 0.45)
vy = np.linspace(-1,1,H)[:,None]; vx = np.linspace(-1,1,W)[None,:]
vig = (1-0.35*(vx**2+0.6*vy**2)).clip(0.4,1)
Tsky = stretch(Y, yy<hz-10*K, 1, 99.5)
sky = (0.03 + 0.07*Tsky**1.5)*vig

def render(fk, crop, tag):
    floor = 0.03 + fk*Lf*(0.45+0.55*Tf)*depth
    land = 0.035 + 0.35*fk*Ll*(0.4+0.6*Tl)
    msky = (1-Mland-Mh).clip(0,1)
    bg = sky*msky + land*vig*Mland + floor*vig*Mh
    o = bg*(1-Ms) + subj*Ms
    o = o + 0.006*np.random.default_rng(3).standard_normal(o.shape)
    x0, y0, x1, y1 = [c*K for c in crop]
    g = (o.clip(0,1)**(1/1.08)*255).astype(np.uint8)[y0:y1, x0:x1]
    im = Image.fromarray(np.dstack([g*0.985, g*0.995, g]).clip(0,255).astype(np.uint8))
    im.save(f'{OUT}/flag_v4{VAR}_{tag}.png'); return im

a = render(0.28, (0, 0, 1280, 640), 'a_wide')
b = render(0.28, (190, 20, 1090, 640), 'b_tight')
tw = 900; ah = round(a.height*tw/a.width); bw = round(b.width*ah/b.height)
sh = Image.new('RGB', (tw+bw+30, ah+20), (8,8,9))
sh.paste(a.resize((tw,ah), Image.LANCZOS), (10,10)); sh.paste(b.resize((bw,ah), Image.LANCZOS), (tw+20,10))
sh.save(f'{OUT}/flag_v4'+VAR+'_sheet.jpg', quality=92); print(a.size, b.size)
