# EditDNA — personal-use license, see LICENSE. (c) EditDNA. Do not redistribute or sell.
"""Camera + transitions + background animation."""
import math, random
import numpy as np
from PIL import Image, ImageDraw
from .comps import clamp


def _ease(x, kind):
    x = clamp(x)
    if kind == 'smooth': return x * x * (3 - 2 * x)
    return 2 ** (20 * x - 10) / 2 if x < .5 else (2 - 2 ** (-20 * x + 10)) / 2   # expo in-out


class Camera:
    """keys [(t, zoom, fx, fy[, 'expo'|'smooth'])] with fx, fy in 0..1."""
    def __init__(self, keys, W, H):
        self.W, self.H = W, H; self.keys = sorted(keys or [(0, 1, .5, .5)], key=lambda k: k[0])
    def at(self, t):
        ks = self.keys
        if t <= ks[0][0]: return ks[0][1:4]
        for a, b in zip(ks, ks[1:]):
            if a[0] <= t <= b[0]:
                k = _ease((t - a[0]) / (b[0] - a[0] + 1e-9), b[4] if len(b) > 4 else 'expo')
                return tuple(a[i] + (b[i] - a[i]) * k for i in (1, 2, 3))
        return ks[-1][1:4]
    def speed(self, t):
        a, b = self.at(t), self.at(t + 1 / 30); return abs(a[0] - b[0]) * 3000 + (abs(a[1] - b[1]) * self.W + abs(a[2] - b[2]) * self.H)
    def apply(self, fr, t):
        z, fx, fy = self.at(t)
        if abs(z - 1) < 1e-3: return fr
        cw, ch = self.W / z, self.H / z; cx = min(max(fx * self.W, cw / 2), self.W - cw / 2); cy = min(max(fy * self.H, ch / 2), self.H - ch / 2)
        return fr.resize((self.W, self.H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))


class Transitions:
    """kind from style.motion.transition: flash | glitch | slide | zoom | wipe | cut ; shakes [(t, amp)]"""
    def __init__(self, st, times, shakes, W, H):
        self.st, self.times, self.shakes, self.W, self.H = st, sorted(times), shakes, W, H; self.kind = st['motion']['transition']
    def __call__(self, fr, t):
        out = fr
        for g in self.times:
            if g - .12 <= t < g + .25:
                q = (t - g) / .25; k = self.kind
                if k == 'flash' and 0 <= q < 1:
                    out = out.copy(); out.alpha_composite(Image.new('RGBA', out.size, self.st.col('accent') + (int(120 * (1 - q)),)))
                elif k == 'glitch' and 0 <= q < 1:
                    a = np.asarray(out).copy(); r = random.Random(int(t * 120)); s = int(26 * (1 - q))
                    a[..., 0] = np.roll(a[..., 0], s, 1); a[..., 2] = np.roll(a[..., 2], -s, 1)
                    for _ in range(int(6 * (1 - q)) + 1):
                        y = r.randint(0, self.H - 60); h = r.randint(8, 60); a[y:y + h] = np.roll(a[y:y + h], r.randint(-120, 120), 1)
                    out = Image.fromarray(a, 'RGBA')
                elif k == 'slide':
                    qq = (t - g + .12) / .37; off = int((1 - abs(qq * 2 - 1)) * self.W * .05)
                    a = np.roll(np.asarray(out), off, 1); out = Image.fromarray(a, 'RGBA')
                elif k == 'zoom' and 0 <= q < 1:
                    z = 1 + .12 * (1 - q); cw, ch = self.W / z, self.H / z
                    out = out.resize((self.W, self.H), Image.BILINEAR, box=((self.W - cw) / 2, (self.H - ch) / 2, (self.W + cw) / 2, (self.H + ch) / 2))
                elif k == 'wipe':
                    qq = (t - g + .12) / .37; x = -self.W * .3 + qq * self.W * 1.6; out = out.copy(); d = ImageDraw.Draw(out)
                    d.polygon([(x, 0), (x + self.W * .18, 0), (x + self.W * .08, self.H), (x - self.W * .1, self.H)], fill=self.st.col('accent'))
                    d.polygon([(x - self.W * .06, 0), (x, 0), (x - self.W * .1, self.H), (x - self.W * .16, self.H)], fill=self.st.col('accent2'))
                break
        for st_, amp in self.shakes:
            if st_ <= t < st_ + .3:
                q = 1 - (t - st_) / .3; r = random.Random(int(t * 200))
                out = Image.fromarray(np.roll(np.roll(np.asarray(out), int(r.uniform(-1, 1) * amp * q), 1), int(r.uniform(-1, 1) * amp * q), 0), 'RGBA')
        return out


class AnimatedBG:
    def __init__(self, P, seed=1):
        self.P = P; self.base, self.pat = P.background(seed); self.anim = P.st['background'].get('animate', True); self.glow = P.st['background'].get('glow', True)
        if self.glow:
            from PIL import ImageFilter
            g = Image.new('L', (900, 900), 0); ImageDraw.Draw(g).ellipse((150, 150, 750, 750), fill=55); g = g.filter(ImageFilter.GaussianBlur(140))
            self.b1 = Image.new('RGBA', (900, 900), P.st.col('accent') + (0,)); self.b1.putalpha(g)
            self.b2 = Image.new('RGBA', (900, 900), P.st.col('accent2') + (0,)); self.b2.putalpha(g.point(lambda v: v * 2 // 3))
    def __call__(self, t):
        fr = self.base.copy(); W, H = self.P.W, self.P.H
        if self.glow:
            bx = W * .5 + math.sin(t * .23) * W * .22; by = H * .45 + math.cos(t * .19) * H * .18
            fr.alpha_composite(self.b1, (int(bx - 450), int(by - 450))); fr.alpha_composite(self.b2, (int(W - bx - 450), int(H - by - 300)))
        o = int((t * 14) % 92) if self.anim else 0
        fr.alpha_composite(self.pat.crop((o, o, o + W, o + H)))
        return fr
