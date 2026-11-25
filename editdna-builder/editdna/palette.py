# EditDNA — personal-use license, see LICENSE. (c) EditDNA. Do not redistribute or sell.
"""Palette ideas from reference screenshots + mood words. Always returns contrast-safe palettes."""
import colorsys, json
import numpy as np
from PIL import Image
from .style import rgb2hex, contrast, hex2rgb

MOODS = {  # mood word -> (bg lightness, saturation, base hues)
    'calm': (.12, .35, [200, 170]), 'tech': (.08, .8, [210, 285, 160]), 'bold': (.07, .95, [345, 50, 80]), 'luxury': (.08, .45, [42, 30]),
    'fun': (.1, .9, [300, 55, 190]), 'nature': (.1, .55, [120, 90, 35]), 'news': (.95, .7, [0, 210]), 'clean': (.96, .6, [215, 250]),
    'gaming': (.06, 1., [270, 140, 320]), 'money': (.07, .85, [140, 48]), 'kids': (.94, .9, [45, 200, 330]), 'food': (.95, .8, [20, 45, 95]),
}


def dominant(paths, k=6):
    px = []
    for p in paths:
        im = Image.open(p).convert('RGB'); im.thumbnail((200, 200)); px.append(np.asarray(im).reshape(-1, 3))
    X = np.concatenate(px).astype(np.float32); rng = np.random.default_rng(0); Cc = X[rng.choice(len(X), k, replace=False)]
    for _ in range(12):
        lab = ((X[:, None] - Cc[None]) ** 2).sum(-1).argmin(1)
        Cc = np.array([X[lab == i].mean(0) if (lab == i).any() else Cc[i] for i in range(k)])
    cnt = np.bincount(lab, minlength=k); order = cnt.argsort()[::-1]
    return [(tuple(int(v) for v in Cc[i]), cnt[i] / len(X)) for i in order]


def _hsl(h, s, l): r, g, b = colorsys.hls_to_rgb((h % 360) / 360, l, s); return (int(r * 255), int(g * 255), int(b * 255))


def build(bg, accent, accent2):
    dark = sum(bg) / 3 < 128
    h, l, s = colorsys.rgb_to_hls(*[v / 255 for v in bg])
    surface = _hsl(h * 360, min(1, s * .9), l + (.07 if dark else -.05)); text = (244, 244, 240) if dark else (20, 22, 26)
    muted = _hsl(h * 360, .12, .62 if dark else .42)
    for c in (accent, accent2):
        pass
    P = dict(bg=bg, surface=surface, text=text, muted=muted, accent=accent, accent2=accent2, good=(46, 204, 113) if dark else (24, 150, 80), bad=(255, 77, 77) if dark else (210, 40, 40))
    out = {k: rgb2hex(v) for k, v in P.items()}
    out['_contrast'] = round(contrast(text, bg), 1); return out


def suggest(refs=(), moods=(), liked=()):
    """-> 3 palettes. refs: screenshot paths; moods: words from MOODS; liked: hex colours the person said they like."""
    S = []
    if refs:
        dom = dominant(refs)
        darks = sorted([c for c, _ in dom], key=lambda c: sum(c)); vivid = sorted([c for c, _ in dom], key=lambda c: -(max(c) - min(c)))
        S.append(build(darks[0], vivid[0], vivid[1] if len(vivid) > 1 else vivid[0]))
    for m in list(moods)[:3]:
        L, sat, hues = MOODS.get(m, MOODS['tech'])
        bg = _hsl(hues[0], .25, L); acc = _hsl(hues[1 % len(hues)] if len(hues) > 1 else hues[0], sat, .58 if L < .5 else .45)
        acc2 = _hsl(hues[-1] + 25, sat, .62 if L < .5 else .5); S.append(build(bg, acc, acc2))
    for hx in liked:
        a = hex2rgb(hx); h, l, s = colorsys.rgb_to_hls(*[v / 255 for v in a])
        S.append(build(_hsl(h * 360, .3, .08), a, _hsl(h * 360 + 150, max(.6, s), .6)))
    return S[:4] or [build((16, 20, 24), (77, 163, 255), (255, 176, 32))]
