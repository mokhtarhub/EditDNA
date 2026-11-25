# EditDNA — personal-use license, see LICENSE. (c) EditDNA. Do not redistribute or sell.
"""Components. Each one: .a/.b (active window), .draw(canvas, t), .sfx -> [(t, event)]."""
import math, random
from PIL import Image, ImageDraw
from .style import ink_for


def clamp(x, a=0., b=1.): return max(a, min(b, x))
def eo(x): x = clamp(x); return 1 - (1 - x) ** 3
def eback(x, s=1.7): x = clamp(x) - 1; return x * x * ((s + 1) * x + s) + 1
def eexpo(x): x = clamp(x); return 1 if x == 1 else 1 - 2 ** (-10 * x)


def place(c, spr, cx, cy, sc=1., rot=0., op=1.):
    if sc <= .01 or op <= .01: return
    s = spr
    if abs(sc - 1) > .005: s = s.resize((max(1, int(s.size[0] * sc)), max(1, int(s.size[1] * sc))), Image.BILINEAR)
    if abs(rot) > .05: s = s.rotate(rot, resample=Image.BICUBIC, expand=True)
    if op < .99: s = s.copy(); s.putalpha(s.getchannel('A').point(lambda v: int(v * op)))
    c.alpha_composite(s, (int(cx - s.size[0] / 2), int(cy - s.size[1] / 2)))


class Comp:
    entry = 'pop'
    def __init__(self, P, t0, t1=None, pos=(.5, .5)):
        self.P, self.t0, self.t1 = P, t0, t1; self.a = t0 - .05; self.b = (t1 if t1 is not None else 1e9) + .3
        self.x, self.y = pos[0] * P.W, pos[1] * P.H; self.sfx = [(t0, 'enter')]
        self.seed = random.random() * 6
    def anim(self, t, dur=.22):
        """-> (scale, opacity, dx, dy) for the channel's entry style; quick exit at t1"""
        if t < self.t0: return 0, 0, 0, 0
        x = (t - self.t0) / (dur / self.P.st.energy); kind = self.P.st['text']['kinetic']
        sc, op, dx, dy = 1, clamp(x * 2), 0, 0
        if kind == 'pop': sc = 1.22 - .22 * eo(x) if x < 1 else 1
        elif kind == 'slide': dy = (1 - eexpo(x)) * 60 * self.P.k
        elif kind == 'fade': op = clamp(x)
        elif kind == 'bounce': sc = eback(x, 2.2) if x < 1 else 1
        if self.t1 is not None and t > self.t1:
            q = (t - self.t1) / .15
            if q >= 1: return 0, 0, 0, 0
            op *= 1 - q; sc *= 1 - .1 * q
        return sc, op, dx, dy
    def bob(self, t, amp=4): return math.sin(t * 2.1 + self.seed) * amp * self.P.k
    def tilt(self): return (random.Random(int(self.seed * 1000)).uniform(-1, 1)) * self.P.st['shape']['tilt']


class Kinetic(Comp):
    """words [(word, t)] — every word lands on its own time; hl = keywords in the highlight style."""
    def __init__(self, P, words, pos=(.5, .5), size=96, hl=(), hl2=(), width=.8, t1=None, align='center'):
        super().__init__(P, words[0][1], t1, pos); size *= P.st['text']['size_scale'] * P.k
        clean = lambda w: ''.join(ch for ch in w.lower() if ch.isalnum() or ch in "$%'")
        sp = []
        for w, t in words:
            s = w.rstrip(',.?!:;،؟') or w; c = clean(w)
            sp.append((P.word(s, size, c in hl or c in hl2, hl_color='accent2' if c in hl2 else 'accent'), t))
        gap = size * .3; W = width * P.W; lines, cur, cw = [], [], 0
        for s, t in sp:
            if cur and cw + gap + s.size[0] > W: lines.append(cur); cur, cw = [], 0
            cw += (gap if cur else 0) + s.size[0]; cur.append((s, t))
        if cur: lines.append(cur)
        lh = size * 1.2; y0 = self.y - (len(lines) - 1) * lh / 2; self.items = []
        for li, ln in enumerate(lines):
            tw = sum(s.size[0] for s, _ in ln) + gap * (len(ln) - 1); x = self.x - tw / 2
            seq = ln[::-1] if P.st.rtl else ln
            for s, t in seq: self.items.append((s, x + s.size[0] / 2, y0 + li * lh, t)); x += s.size[0] + gap
        self.sfx = [(t, 'tick') for _, t in words]
    def draw(self, c, t):
        for s, x, y, t0 in self.items:
            self.t0 = t0 - .03; sc, op, dx, dy = self.anim(t, .14)
            if op > 0: place(c, s, x + dx, y + dy, sc, 0, op)


class Headline(Comp):
    def __init__(self, P, text, t0, t1=None, pos=(.5, .5), size=110, color='accent', boxed=True):
        super().__init__(P, t0, t1, pos); s = size * P.k * P.st['text']['size_scale']
        sp = P.pill(P.case(text), s, color) if boxed else P.text(P.case(text), s, P.st.col(color))
        self.spr = P.shadowed(sp); self.rot = self.tilt(); self.sfx = [(t0, 'big' if size >= 120 else 'enter')]
    def draw(self, c, t):
        sc, op, dx, dy = self.anim(t)
        if op > 0: place(c, self.spr, self.x + dx, self.y + dy + self.bob(t), sc, self.rot, op)


class Card(Comp):
    def __init__(self, P, title, sub, t0, t1=None, pos=(.5, .5), size=64):
        super().__init__(P, t0, t1, pos); s = size * P.k
        a = P.text(P.case(title), s, P.st.col('text')); b = P.text(sub, s * .46, P.st.col('accent'), 'mono') if sub else None
        w = max(a.size[0], b.size[0] if b else 0) + s * 1.3; h = a.size[1] + (b.size[1] + s * .25 if b else 0) + s * .9
        im = P.box(w, h); im.alpha_composite(a, (int((w - a.size[0]) / 2), int(s * .42)))
        if b: im.alpha_composite(b, (int((w - b.size[0]) / 2), int(s * .42 + a.size[1] + s * .2)))
        self.spr = P.shadowed(im); self.rot = self.tilt() * .6
    def draw(self, c, t):
        sc, op, dx, dy = self.anim(t)
        if op > 0: place(c, self.spr, self.x + dx, self.y + dy + self.bob(t), sc, self.rot, op)


class Stat(Comp):
    def __init__(self, P, fmt, v0, v1, label, t0, t1=None, pos=(.5, .45), size=190, dur=.8):
        super().__init__(P, t0, t1, pos); self.fmt, self.v0, self.v1, self.dur, self.s = fmt, v0, v1, dur, size * P.k
        self.lab = P.text(P.case(label), self.s * .2, P.st.col('muted'), 'mono'); self.cache = {}
        self.sfx = [(t0, 'count'), (t0 + dur, 'success')]
    def draw(self, c, t):
        sc, op, dx, dy = self.anim(t)
        if op <= 0: return
        k = eo((t - self.t0) / self.dur); txt = self.fmt.format(self.v0 + (self.v1 - self.v0) * k)
        if txt not in self.cache: self.cache[txt] = self.P.shadowed(self.P.text(txt, self.s, self.P.st.col('accent')), 'accent' if self.P.st['shape']['shadow'] == 'glow' else None)
        n = self.cache[txt]; place(c, n, self.x + dx, self.y + dy, sc, 0, op)
        place(c, self.lab, self.x, self.y + self.s * .78, 1, 0, op)


class Checklist(Comp):
    def __init__(self, P, items, pos=(.5, .55), width=.42, title=None, t1=None, size=42):
        super().__init__(P, items[0][1] - .25, t1, pos); s = size * P.k; self.s = s
        self.rows = [P.text(P.case(x), s * .92, P.st.col('text'), 'heading') for x, _ in items]; self.times = [t for _, t in items]
        self.lh = int(s * 1.9); self.top = int(s * 1.7) if title else int(s * .6); w = width * P.W
        h = self.top + self.lh * len(items) + s * .5; self.base = P.box(w, h)
        if title:
            tt = P.text(P.case(title), s * .6, P.st.col('accent'), 'mono'); self.base.alpha_composite(tt, (int(w - tt.size[0] - s * .8) if P.st.rtl else int(s * .8), int(s * .5)))
        self.sfx = [(tt, 'success') for tt in self.times]
    def draw(self, c, t):
        sc, op, dx, dy = self.anim(t)
        if op <= 0: return
        P = self.P; im = self.base.copy(); d = ImageDraw.Draw(im); s = self.s; acc = P.st.col('accent'); good = P.st.col('good')
        for k, (r, tt) in enumerate(zip(self.rows, self.times)):
            if t < tt - .05: continue
            y = self.top + k * self.lh + self.lh / 2; q = eback((t - tt + .05) / .22, 2)
            rtl = P.st.rtl; bx = (im.size[0] - s * 1.8) if rtl else s * .8
            d.rounded_rectangle((bx, y - s * .5, bx + s, y + s * .5), s * .22, outline=acc, width=max(3, int(s * .09)))
            if q > 0:
                z = s * .5 * min(1, q); d.rounded_rectangle((bx + s / 2 - z, y - z, bx + s / 2 + z, y + z), s * .18, fill=good)
                if q > .6: d.line([(bx + s * .25, y), (bx + s * .45, y + s * .2), (bx + s * .78, y - s * .25)], fill=ink_for(good), width=max(3, int(s * .13)), joint='curve')
            xo = int((1 - min(1, q)) * s); rx = (bx - s * .5 - r.size[0] - xo) if rtl else (bx + s * 1.5 + xo)
            im.alpha_composite(r, (int(rx), int(y - r.size[1] / 2)))
        place(c, P.shadowed(im), self.x + dx, self.y + dy + self.bob(t, 2), sc, 0, op)


class Flow(Comp):
    def __init__(self, P, nodes, y=.5, width=.86, t1=None, size=54):
        super().__init__(P, nodes[0][2], t1, (.5, y)); n = len(nodes); W = width * P.W
        self.xs = [P.W / 2 - W / 2 + W * (i + .5) / n for i in range(n)]; self.times = [t for _, _, t in nodes]
        self.cards = [P.shadowed(Card(P, a, b, 0, None, (0, 0), size).spr) for a, b, _ in nodes]
        self.cards = [Card(P, a, b, 0, None, (0, 0), size).spr for a, b, _ in nodes]
        self.sfx = [(tt, 'enter') for tt in self.times]
    def draw(self, c, t):
        if self.t1 is not None and t > self.t1 + .15: return
        P = self.P; d = ImageDraw.Draw(c); acc2 = P.st.col('accent2'); acc = P.st.col('accent')
        for i in range(1, len(self.xs)):
            if t > self.times[i] - .12:
                k = eexpo((t - self.times[i] + .12) / .25); xa = self.xs[i - 1] + self.cards[i - 1].size[0] * .35; xb = self.xs[i] - self.cards[i].size[0] * .35
                d.line((xa, self.y, xa + (xb - xa) * k, self.y), fill=acc2, width=max(4, int(6 * P.k)))
                if k >= 1:
                    p = (t * 1.2 + i * .37) % 1; px = xa + (xb - xa) * p; r = 9 * P.k; d.ellipse((px - r, self.y - r, px + r, self.y + r), fill=acc)
        for i, cd in enumerate(self.cards):
            self.t0 = self.times[i]; sc, op, dx, dy = self.anim(t)
            if op > 0: place(c, cd, self.xs[i] + dx, self.y + dy + self.bob(t + i, 3), sc, 0, op)


class Shot(Comp):
    """screenshot in the channel's frame; geometry exposed for callouts (fractions of the picture)."""
    def __init__(self, P, img, t0, t1=None, pos=(.5, .52), width=.6, maxh=.62, label=None):
        super().__init__(P, t0, t1, pos); spr, geo, isz = P.frame(img, width * P.W, maxh * P.H, label)
        self.spr = P.shadowed(spr); pad = (self.spr.size[0] - spr.size[0]) // 2
        self.ix = self.x - self.spr.size[0] / 2 + pad + geo[0]; self.iy = self.y - self.spr.size[1] / 2 + pad + geo[1]; self.isz = isz
        self.sfx = [(t0, 'whoosh')]
    def box(self, fb):
        return (self.ix + fb[0] * self.isz[0], self.iy + fb[1] * self.isz[1], self.ix + fb[2] * self.isz[0], self.iy + fb[3] * self.isz[1])
    def draw(self, c, t):
        if t < self.t0: return
        x = (t - self.t0) / .3; sw, sh = self.spr.size
        if self.t1 is not None and t > self.t1:
            q = (t - self.t1) / .15
            if q < 1: place(c, self.spr, self.x, self.y, 1 - .06 * q, 0, 1 - q)
            return
        if x >= 1: place(c, self.spr, self.x, self.y + self.bob(t, 2), 1, 0); return
        k = eexpo(x); place(c, self.spr, self.x, self.y + (1 - k) * .3 * self.P.H, .94 + .06 * k, (1 - k) * 4, clamp(x * 3))


class Callout(Comp):
    def __init__(self, P, box, t0, t1=None, label=None, kind=None):
        super().__init__(P, t0, t1, (0, 0)); self.bx = box; self.kind = kind or P.st['frames']['callout']
        self.lab = P.pill(P.case(label), 30 * P.k, 'accent2') if label else None; self.sfx = [(t0, 'tick2')]
    def draw(self, c, t):
        if t < self.t0 or (self.t1 is not None and t > self.t1): return
        P = self.P; k = eback((t - self.t0) / .25, 1.6); x0, y0, x1, y1 = self.bx; col = P.st.col('accent2'); w = max(5, int(7 * P.k))
        pad = (1 - k) * 40 * P.k + 8 * P.k + 3 * P.k * math.sin((t - self.t0) * 8); a, b, cc, dd = x0 - pad, y0 - pad, x1 + pad, y1 + pad
        d = ImageDraw.Draw(c)
        if self.kind == 'circle':
            n = clamp((t - self.t0) / .35); d.arc((a, b, cc, dd), -100, -100 + 360 * n, fill=col, width=w)
        elif self.kind == 'box': d.rounded_rectangle((a, b, cc, dd), int(14 * P.k), outline=col, width=w)
        elif self.kind == 'arrow':
            ax, ay = cc + 140 * P.k, b - 80 * P.k; d.line((ax, ay, cc + 10, b + 10), fill=col, width=w)
            ang = math.atan2(b + 10 - ay, cc + 10 - ax)
            for s in (.5, -.5): d.line((cc + 10, b + 10, cc + 10 - math.cos(ang + s) * 40 * P.k, b + 10 - math.sin(ang + s) * 40 * P.k), fill=col, width=w)
            d.rounded_rectangle((a, b, cc, dd), int(10 * P.k), outline=col, width=max(3, w // 2))
        else:
            L = min(44 * P.k, (x1 - x0) / 3)
            for (x, y, sx, sy) in ((a, b, 1, 1), (cc, b, -1, 1), (a, dd, 1, -1), (cc, dd, -1, -1)):
                d.line((x, y, x + sx * L, y), fill=col, width=w); d.line((x, y, x, y + sy * L), fill=col, width=w)
        if self.lab is not None: place(c, self.lab, (x0 + x1) / 2, b - self.lab.size[1] * .8, min(1, k), 0)


class Cross(Comp):
    def __init__(self, P, box, t0, t1=None):
        super().__init__(P, t0, t1); self.bx = box; self.sfx = [(t0, 'fail')]
    def draw(self, c, t):
        if t < self.t0 or (self.t1 is not None and t > self.t1): return
        x0, y0, x1, y1 = self.bx; d = ImageDraw.Draw(c); k = clamp((t - self.t0) / .22); col = self.P.st.col('bad'); w = int(16 * self.P.k)
        for (a, b), kk in (((x0, y0), (x1, y1)), clamp(k * 2)), (((x1, y0), (x0, y1)), clamp(k * 2 - 1)):
            if kk > 0: d.line((a[0], a[1], a[0] + (b[0] - a[0]) * kk, a[1] + (b[1] - a[1]) * kk), fill=col, width=w)


class Logo(Comp):
    def __init__(self, P, img, t0, t1=None, pos=(.5, .4), h=150, plate=True):
        super().__init__(P, t0, t1, pos); lg = img.convert('RGBA'); hh = h * P.k; lg.thumbnail((int(hh * 3.4), int(hh)))
        if plate:
            im = Image.new('RGBA', (lg.size[0] + int(60 * P.k), lg.size[1] + int(48 * P.k)), (0, 0, 0, 0))
            ImageDraw.Draw(im).rounded_rectangle((0, 0, im.size[0] - 1, im.size[1] - 1), int(P.st['shape']['radius'] * P.k), fill=(246, 246, 242, 255),
                                                 outline=P.st.col(P.st['shape']['border_color']), width=int(P.st['shape']['border'] * P.k))
            im.alpha_composite(lg, (int(30 * P.k), int(24 * P.k))); lg = im
        self.spr = P.shadowed(lg); self.rot = self.tilt()
    def draw(self, c, t):
        sc, op, dx, dy = self.anim(t)
        if op > 0: place(c, self.spr, self.x + dx, self.y + dy + self.bob(t), sc, self.rot, op)


class Step(Comp):
    def __init__(self, P, n, title, t0, t1=None):
        super().__init__(P, t0, t1); s = 40 * P.k; self.num = P.pill(f'{n:02d}' if isinstance(n, int) else str(n), s, 'accent')
        self.ttl = P.text(P.case(title), s * 1.3, P.st.col('text')); self.sfx = [(t0, 'big')]
    def draw(self, c, t):
        if t < self.t0 or (self.t1 is not None and t > self.t1): return
        P = self.P; k = eexpo((t - self.t0) / .3); m = 56 * P.k
        x = (P.W - m - self.num.size[0]) if P.st.rtl else m
        c.alpha_composite(self.num, (int(x + (1 if not P.st.rtl else -1) * -(1 - k) * 300 * P.k), int(m)))
        n = clamp((t - self.t0 - .12) / .35)
        if n > 0:
            w = int(self.ttl.size[0] * n)
            if P.st.rtl: c.alpha_composite(self.ttl.crop((self.ttl.size[0] - w, 0, self.ttl.size[0], self.ttl.size[1])), (int(x - 24 * P.k - w), int(m + (self.num.size[1] - self.ttl.size[1]) / 2)))
            else: c.alpha_composite(self.ttl.crop((0, 0, w, self.ttl.size[1])), (int(x + self.num.size[0] + 24 * P.k), int(m + (self.num.size[1] - self.ttl.size[1]) / 2)))


class Progress(Comp):
    def __init__(self, P, label, t0, t1=None, pos=(.5, .5), width=.52, dur=1.4):
        super().__init__(P, t0, t1, pos); self.w = width * P.W; self.dur = dur; self.lab = P.text(P.case(label), 46 * P.k, P.st.col('text'), 'body')
        self.sfx = [(t0, 'count'), (t0 + dur, 'success')]
    def draw(self, c, t):
        sc, op, dx, dy = self.anim(t)
        if op <= 0: return
        P = self.P; k = clamp((t - self.t0 - .2) / self.dur); h = 40 * P.k; x0 = self.x - self.w / 2; y0 = self.y
        d = ImageDraw.Draw(c); d.rounded_rectangle((x0, y0, x0 + self.w, y0 + h), h / 2, outline=P.st.col('accent'), width=int(4 * P.k))
        if k > 0: d.rounded_rectangle((x0 + 6, y0 + 6, x0 + 6 + (self.w - 12) * k, y0 + h - 6), (h - 12) / 2, fill=P.st.col('accent'))
        c.alpha_composite(self.lab, (int(x0), int(y0 - self.lab.size[1] - 14 * P.k)))
        pct = P.text(f'{int(k * 100)}%', 46 * P.k, P.st.col('accent')); c.alpha_composite(pct, (int(x0 + self.w - pct.size[0]), int(y0 - pct.size[1] - 14 * P.k)))


class Mascot:
    """The channel's own character/logo floating in a corner. keys [(t, action, (x,y)|None, size|None)]
    actions: show, hop, wiggle, spin, big (to centre), dock, hide."""
    def __init__(self, P, img, keys, dock=None, size=None):
        self.P = P; self.img = img.convert('RGBA'); self.img = self.img.crop(self.img.getbbox())
        self.dock = dock or (P.st['mascot']['dock'][0] * P.W, P.st['mascot']['dock'][1] * P.H); self.size = (size or P.st['mascot']['size']) * P.k
        self.keys = sorted(keys, key=lambda k: k[0]); self.cache = {}; self.a, self.b = (self.keys[0][0] if self.keys else 1e9), 1e9
        self.sfx = [(k[0], 'mascot') for k in self.keys if k[1] != 'hide']
    def spr(self, h):
        h = int(h)
        if h not in self.cache:
            r = h / self.img.size[1]; self.cache[h] = self.P.shadowed(self.img.resize((max(1, int(self.img.size[0] * r)), h), Image.LANCZOS))
        return self.cache[h]
    def draw(self, c, t):
        if not self.keys or t < self.keys[0][0]: return
        cur = max((k for k in self.keys if k[0] <= t), key=lambda k: k[0]); act = cur[1]; q = t - cur[0]
        if act == 'hide':
            if q < .25: place(c, self.spr(self.size), self.dock[0], self.dock[1] + q * 1600 * self.P.k, 1, 0, 1 - q * 4)
            return
        big = act == 'big'; pos = ((.8 if not self.P.st.rtl else .2) * self.P.W, self.P.H * .62) if big else self.dock; size = self.size * (2.2 if big else 1)
        sc = eback(q / .35, 2) if (act in ('show', 'big', 'dock') and q < .35) else 1
        x, y = pos; y += math.sin(t * 2.4) * 9 * self.P.k; rot = math.sin(t * 1.7) * 3
        if act == 'hop' and q < .5: y -= math.sin(q / .5 * math.pi) * 90 * self.P.k
        if act == 'wiggle' and q < .6: rot += math.sin(q * 40) * 12 * (1 - q / .6)
        if act == 'spin' and q < .5: rot += 360 * eo(q / .5)
        place(c, self.spr(size), x, y, sc, rot)


class Bubble(Comp):
    def __init__(self, P, text, anchor, t0, t1=None, size=44):
        super().__init__(P, t0, t1); s = size * P.k; self.s = s; f = P.font('body', s); self.text = text
        d = ImageDraw.Draw(Image.new('L', (8, 8))); maxw = .34 * P.W; words = text.split(); lines, cur = [], ''
        for w in words:
            if cur and d.textlength(cur + ' ' + w, font=f) > maxw: lines.append(cur); cur = w
            else: cur = (cur + ' ' + w).strip()
        lines.append(cur); self.lines = lines
        self.w = int(max(d.textlength(l, font=f) for l in lines) + s * 1.3); self.h = int(len(lines) * s * 1.32 + s * .9); self.anc = anchor
        self.sfx = [(t0, 'pop')]
    def draw(self, c, t):
        if t < self.t0 or (self.t1 is not None and t > self.t1 + .15): return
        P = self.P; x = t - self.t0; s = self.s
        im = Image.new('RGBA', (self.w, self.h + int(s * .5)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        fill = (248, 248, 244, 255); d.rounded_rectangle((0, 0, self.w - 1, self.h - 1), int(s * .5), fill=fill, outline=P.st.col('accent'), width=max(3, int(4 * P.k)))
        tx = s * .7 if not P.st.rtl else self.w - s * 1.1; d.polygon([(tx, self.h - 2), (tx + s * .4, self.h - 2), (tx - s * .1, self.h + s * .45)], fill=fill)
        if x < .3:
            for i in range(3): yy = self.h / 2 + math.sin(x * 9 - i) * 5; d.ellipse((s * .6 + i * s * .7, yy - s * .16, s * .92 + i * s * .7, yy + s * .16), fill=(20, 20, 24))
        else:
            n = int((x - .3) * 55); f = P.font('body', s)
            for li, l in enumerate(self.lines):
                part = l[:max(0, n)]; n -= len(l) + 1
                if part: d.text((s * .6, s * .4 + li * s * 1.32), part, font=f, fill=(20, 20, 24), **P._kw(part))
        op = 1 if self.t1 is None or t < self.t1 else 1 - (t - self.t1) / .15
        ax = self.anc[0] + (self.w / 2 if not P.st.rtl else -self.w / 2); ay = self.anc[1] - self.h / 2 - s * .5
        place(c, im, ax, ay, eback(min(1, x / .2), 2), 0, op)
