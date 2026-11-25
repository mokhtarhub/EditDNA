# EditDNA — personal-use license, see LICENSE. (c) EditDNA. Do not redistribute or sell.
"""style.json: the channel's 'DNA'. Every look decision the engine makes comes from here."""
import json, os, copy, colorsys

DEFAULT = {
    "tool": "EditDNA", "version": 1,
    "channel": {"name": "My Channel", "language": "en", "direction": "ltr", "content": "", "audience": "", "tagline": ""},
    "palette": {"bg": "#101418", "surface": "#1C232B", "text": "#F4F4F0", "muted": "#8C96A3",
                "accent": "#4DA3FF", "accent2": "#FFB020", "good": "#2ECC71", "bad": "#FF4D4D"},
    "fonts": {"heading": "Inter-Bold.ttf", "body": "Inter-Regular.ttf", "mono": "JetBrainsMono-Regular.ttf"},
    "shape": {"radius": 22, "border": 3, "border_color": "accent", "shadow": "soft", "shadow_color": "#000000",
              "shadow_offset": 10, "tilt": 2.0},
    "background": {"type": "gradient", "color2": "surface", "pattern_color": "accent", "pattern_alpha": 28,
                   "animate": True, "vignette": 0.3, "glow": True},
    "text": {"case": "upper", "highlight": "pill", "kinetic": "pop", "size_scale": 1.0},
    "motion": {"energy": "medium", "camera_zoom": 1.22, "transition": "flash", "shake": True},
    "frames": {"screenshot": "window", "callout": "box"},
    "sound": {"profile": "punchy", "volume": 0.55},
    "mascot": {"image": None, "size": 230, "dock": [0.1, 0.82]},
    "brand": {"logo": None, "watermark": True, "watermark_width": 220, "intro": True},
    "captions": {"style": "outline", "y": 0.76, "max_words": 3},
}


def hex2rgb(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb2hex(c): return '#%02X%02X%02X' % tuple(int(v) for v in c[:3])


def lum(c):
    def ch(v):
        v = v / 255; return v / 12.92 if v <= .03928 else ((v + .055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in c[:3]); return .2126 * r + .7152 * g + .0722 * b


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True); return (la + .05) / (lb + .05)


def ink_for(bg, light=(245, 245, 240), dark=(16, 18, 22)):
    return dark if contrast(bg, dark) >= contrast(bg, light) else light


def _merge(a, b):
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict): _merge(a[k], v)
        else: a[k] = v
    return a


class Style:
    def __init__(self, path_or_dict):
        if isinstance(path_or_dict, str):
            self.path = os.path.abspath(path_or_dict); self.root = os.path.dirname(self.path)
            d = json.load(open(path_or_dict, encoding='utf-8'))
        else:
            self.path, self.root, d = None, os.getcwd(), path_or_dict
        self.d = _merge(copy.deepcopy(DEFAULT), d)
        P = self.d['palette']
        self.c = {k: hex2rgb(v) for k, v in P.items()}

    def __getitem__(self, k): return self.d[k]

    def col(self, name_or_hex):
        """palette name ('accent') or '#hex' -> rgb"""
        if isinstance(name_or_hex, (tuple, list)): return tuple(name_or_hex[:3])
        if name_or_hex in self.c: return self.c[name_or_hex]
        return hex2rgb(name_or_hex)

    def file(self, rel):
        if not rel: return None
        p = rel if os.path.isabs(rel) else os.path.join(self.root, rel)
        return p if os.path.exists(p) else None

    @property
    def rtl(self): return self.d['channel'].get('direction') == 'rtl'

    @property
    def energy(self): return {'calm': .6, 'medium': 1.0, 'hype': 1.45}.get(self.d['motion']['energy'], 1.0)

    def check(self):
        """problems a human should fix (contrast etc.)"""
        out = []; c = self.c
        if contrast(c['text'], c['bg']) < 4.5: out.append('text on bg contrast < 4.5')
        if contrast(c['text'], c['surface']) < 4.5: out.append('text on surface contrast < 4.5')
        for k in ('heading', 'body', 'mono'):
            if not self.file(os.path.join('fonts', self.d['fonts'][k])) and not self.file(self.d['fonts'][k]): out.append(f'font missing: {k} -> {self.d["fonts"][k]}')
        return out
