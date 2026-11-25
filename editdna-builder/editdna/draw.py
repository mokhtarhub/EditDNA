# EditDNA — personal-use license, see LICENSE. (c) EditDNA. Do not redistribute or sell.
"""Style-driven drawing primitives. Every shape, shadow, highlight and background reads the Style."""
import os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, features
from .style import ink_for

RAQM = features.check('raqm')


class Painter:
    def __init__(self, st, W=1920, H=1080):
        self.st, self.W, self.H = st, W, H; self._f = {}; self.k = min(W, H) / 1080
        self.fdir = os.path.join(st.root, 'fonts')

    # ---------- text ----------
    def font(self, kind, size):
        key = (kind, int(size))
        if key not in self._f:
            name = self.st['fonts'][kind]
            p = self.st.file(os.path.join('fonts', name)) or self.st.file(name)
            try:
                f = ImageFont.truetype(p, int(size)) if p else ImageFont.load_default(int(size))
                if p and '[' in os.path.basename(p):
                    try:
                        ax = f.get_variation_axes(); want = 700 if kind == 'heading' else (500 if kind == 'mono' else 450)
                        f.set_variation_by_axes([max(a['minimum'], min(a['maximum'], want)) if a.get('name', b'') in (b'Weight', 'Weight') else a['default'] for a in ax])
                    except Exception: pass
            except Exception: f = ImageFont.load_default(int(size))
            self._f[key] = f
        return self._f[key]

    def _kw(self, s):
        if RAQM and any('؀' <= ch <= 'ۿ' for ch in s): return dict(direction='rtl', language='ar')
        return {}

    def case(self, s):
        c = self.st['text']['case']
        if any('؀' <= ch <= 'ۿ' for ch in s): return s
        return s.upper() if c == 'upper' else (s.title() if c == 'title' else s)

    def text(self, s, size, color, kind='heading', stroke=0, stroke_color=(0, 0, 0)):
        if kind == 'mono' and any('\u0600' <= ch <= '\u06ff' for ch in s): kind = 'body'   # mono fonts rarely have Arabic
        f = self.font(kind, size); d = ImageDraw.Draw(Image.new('L', (8, 8))); kw = self._kw(s)
        b = d.textbbox((0, 0), s, font=f, stroke_width=stroke, **kw)
        im = Image.new('RGBA', (b[2] - b[0] + 10, b[3] - b[1] + 10), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((5 - b[0], 5 - b[1]), s, font=f, fill=color, stroke_width=stroke, stroke_fill=stroke_color, **kw)
        return im

    def tlen(self, s, kind, size):
        return ImageDraw.Draw(Image.new('L', (8, 8))).textlength(s, font=self.font(kind, size), **self._kw(s))

    # ---------- shapes ----------
    def shadowed(self, img, color=None):
        sh = self.st['shape']; kind = sh['shadow']; off = int(sh['shadow_offset'] * self.k)
        if kind == 'none': return img
        col = self.st.col(color or sh['shadow_color'])
        pad = max(off, 8) * 3
        out = Image.new('RGBA', (img.size[0] + pad * 2, img.size[1] + pad * 2), (0, 0, 0, 0))
        a = Image.new('L', out.size, 0); a.paste(img.getchannel('A'), (pad, pad))
        if kind == 'hard':
            m = Image.new('L', out.size, 0); m.paste(a.point(lambda v: 255 if v > 90 else 0), (off, off))
            s = Image.new('RGBA', out.size, col + (255,)); s.putalpha(m); out.alpha_composite(s)
        elif kind == 'soft':
            m = Image.new('L', out.size, 0); m.paste(a, (off // 2, off)); m = m.filter(ImageFilter.GaussianBlur(off * 1.2)).point(lambda v: v * 150 // 255)
            s = Image.new('RGBA', out.size, col + (255,)); s.putalpha(m); out.alpha_composite(s)
        elif kind == 'glow':
            m = a.filter(ImageFilter.GaussianBlur(max(6, off * 1.6))).point(lambda v: min(255, int(v * 1.3)))
            s = Image.new('RGBA', out.size, col + (255,)); s.putalpha(m); out.alpha_composite(s)
        out.alpha_composite(img, (pad, pad)); return out

    def box(self, w, h, fill='surface', border=None, radius=None, alpha=255):
        sh = self.st['shape']; r = int((sh['radius'] if radius is None else radius) * self.k)
        bw = int(sh['border'] * self.k) if border is None else border
        im = Image.new('RGBA', (int(w), int(h)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, w - 1, h - 1), min(r, int(h // 2)), fill=self.st.col(fill) + (alpha,),
                            outline=self.st.col(sh['border_color']) + (255,) if bw else None, width=bw)
        return im

    def pill(self, s, size, fill='accent', kind='heading'):
        col = self.st.col(fill); ink = ink_for(col)
        t = self.text(s, size, ink, kind); px, py = int(size * .42), int(size * .2)
        r = int(min(self.st['shape']['radius'] * self.k * 1.4, (t.size[1] + py * 2) / 2))
        im = Image.new('RGBA', (t.size[0] + px * 2, t.size[1] + py * 2), (0, 0, 0, 0))
        ImageDraw.Draw(im).rounded_rectangle((0, 0, im.size[0] - 1, im.size[1] - 1), r, fill=col + (255,))
        im.alpha_composite(t, (px, py)); return im

    def word(self, s, size, hl=False, color='text', hl_color='accent'):
        """one word in the channel's highlight style"""
        s = self.case(s); kind = self.st['text']['highlight']
        if not hl: return self.text(s, size, self.st.col(color))
        hc = self.st.col(hl_color)
        if kind == 'pill': return self.pill(s, size * .86, hl_color)
        if kind == 'color': return self.text(s, size, hc)
        t = self.text(s, size, self.st.col(color)); im = Image.new('RGBA', (t.size[0] + 16, t.size[1] + 22), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        if kind == 'underline': d.rounded_rectangle((8, im.size[1] - 16, im.size[0] - 8, im.size[1] - 4), 6, fill=hc)
        elif kind == 'marker': d.rectangle((4, im.size[1] * .45, im.size[0] - 4, im.size[1] - 8), fill=hc + (200,))
        elif kind == 'box': d.rounded_rectangle((0, 0, im.size[0] - 1, im.size[1] - 1), 8, outline=hc, width=max(3, int(4 * self.k)))
        im.alpha_composite(t, (8, 4)); return im

    # ---------- background ----------
    def background(self, seed=1):
        st, W, H = self.st, self.W, self.H; B = st['background']
        bg = np.array(st.col('bg'), np.float32); c2 = np.array(st.col(B.get('color2', 'surface')), np.float32)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        if B['type'] in ('gradient', 'dots', 'grid', 'stripes', 'grain', 'paper'):
            g = (yy / H * .65 + xx / W * .35)[..., None]; arr = bg * (1 - g * .55) + c2 * g * .55
        else: arr = np.ones((H, W, 3), np.float32) * bg
        if B['type'] in ('grain', 'paper'):
            n = np.random.default_rng(seed).normal(0, 7 if B['type'] == 'grain' else 11, (H, W, 1)); arr = arr + n
        v = B.get('vignette', .3)
        if v: arr *= (1 - v * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2))[..., None].clip(0, 1) * .99 + .01
        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGB').convert('RGBA')
        pc = st.col(B.get('pattern_color', 'accent')) + (int(B.get('pattern_alpha', 28)),)
        pat = Image.new('RGBA', (W + 120, H + 120), (0, 0, 0, 0)); d = ImageDraw.Draw(pat); s = int(46 * self.k)
        if B['type'] == 'dots':
            for y in range(0, H + 120, s):
                for x in range(0, W + 120, s): d.ellipse((x - 2.2, y - 2.2, x + 2.2, y + 2.2), fill=pc)
        elif B['type'] == 'grid':
            for x in range(0, W + 120, s * 2): d.line((x, 0, x, H + 120), fill=pc, width=1)
            for y in range(0, H + 120, s * 2): d.line((0, y, W + 120, y), fill=pc, width=1)
        elif B['type'] == 'stripes':
            for x in range(-H, W + 120, s): d.line((x, H + 120, x + H, 0), fill=pc, width=int(s * .3))
        return im, pat

    # ---------- screenshot frame ----------
    def frame(self, img, w, maxh, label=None):
        st = self.st; kind = st['frames']['screenshot']; im = img.convert('RGB')
        k = min(w / im.size[0], maxh / im.size[1]); im = im.resize((max(1, int(im.size[0] * k)), max(1, int(im.size[1] * k))), Image.LANCZOS)
        r = int(st['shape']['radius'] * self.k * .6); m = Image.new('L', im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.size[0] - 1, im.size[1] - 1), r, fill=255)
        if kind == 'plain':
            out = Image.new('RGBA', im.size, (0, 0, 0, 0)); out.paste(im, (0, 0), m); geo = (0, 0)
        elif kind == 'polaroid':
            p = int(22 * self.k); out = Image.new('RGBA', (im.size[0] + p * 2, im.size[1] + p * 4), (0, 0, 0, 0))
            ImageDraw.Draw(out).rounded_rectangle((0, 0, out.size[0] - 1, out.size[1] - 1), 8, fill=(250, 250, 246, 255))
            out.paste(im, (p, p)); geo = (p, p)
            if label: t = self.text(label, 34 * self.k, (30, 30, 30), 'body'); out.alpha_composite(t, ((out.size[0] - t.size[0]) // 2, im.size[1] + p + (p * 3 - t.size[1]) // 2))
            label = None
        elif kind == 'phone':
            p = int(18 * self.k); out = Image.new('RGBA', (im.size[0] + p * 2, im.size[1] + p * 2), (0, 0, 0, 0))
            ImageDraw.Draw(out).rounded_rectangle((0, 0, out.size[0] - 1, out.size[1] - 1), int(46 * self.k), fill=(20, 20, 22, 255), outline=st.col('accent'), width=int(3 * self.k))
            out.paste(im, (p, p), m); geo = (p, p)
        else:  # window / neon
            top = int(48 * self.k); p = int(14 * self.k)
            out = self.box(im.size[0] + p * 2, im.size[1] + top + p, 'surface')
            d = ImageDraw.Draw(out)
            for i, c in enumerate(('bad', 'accent2', 'good')): d.ellipse((p + 6 + i * 26 * self.k, top / 2 - 8 * self.k, p + 22 * self.k + i * 26 * self.k, top / 2 + 8 * self.k), fill=st.col(c))
            out.paste(im, (p, top), m); geo = (p, top)
        if label:
            lb = self.pill(label, 26 * self.k, 'accent', 'mono'); big = Image.new('RGBA', (out.size[0], out.size[1] + lb.size[1] // 2), (0, 0, 0, 0))
            big.alpha_composite(out, (0, lb.size[1] // 2)); big.alpha_composite(lb, (out.size[0] - lb.size[0] - int(20 * self.k), 0)); out = big; geo = (geo[0], geo[1] + lb.size[1] // 2)
        return out, geo, im.size
