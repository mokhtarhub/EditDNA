# EditDNA — personal-use license, see LICENSE. (c) EditDNA. Do not redistribute or sell.
"""Render a video from a JSON storyboard.

story.json
{
  "style": "style.json", "vo": "vo.wav", "words": "words.json", "format": "16:9" | "9:16", "fps": 60,
  "intro_at": 12.4,            # optional: seconds into the VO where the channel intro is inserted (null = no intro)
  "elements": [ {"type": "...", "at": TIME, "until": TIME, ...}, ... ],
  "mascot": [ {"at": TIME, "do": "show|hop|wiggle|spin|big|dock|hide"} ],
  "camera": [ {"at": TIME, "zoom": 1.3, "x": 0.5, "y": 0.5, "ease": "expo|smooth"} ],
  "transitions": [TIME, ...], "shakes": [TIME, ...], "captions": false
}
TIME = seconds (12.3) | "w:57" (index in words.json) | "money" / "money@2" (2nd time that word is said) | any of these + "+0.2" / "-0.1"
"""
import os, re, json, math, subprocess, multiprocessing as mp
from PIL import Image
from .style import Style
from .draw import Painter
from . import comps as C
from .fx import Camera, Transitions, AnimatedBG
from . import sound

STAMP = 'Made with EditDNA (personal-use license)'


class Story:
    def __init__(self, path, preview_fps=None):
        self.path = os.path.abspath(path); self.root = os.path.dirname(self.path)
        self.s = json.load(open(path, encoding='utf-8'))
        self.st = Style(self.rel(self.s.get('style', 'style.json')))
        self.W, self.H = (1080, 1920) if self.s.get('format') == '9:16' else (1920, 1080)
        self.fps = preview_fps or self.s.get('fps', 60)
        self.P = Painter(self.st, self.W, self.H)
        self.words = json.load(open(self.rel(self.s['words']), encoding='utf-8')) if self.s.get('words') else []
        self.vo = self.rel(self.s['vo']) if self.s.get('vo') else None
        self.dur = self.s.get('duration') or (self._probe(self.vo) + .4 if self.vo else (self.words[-1]['t'] + 2 if self.words else 10))
        self.items, self.ev = [], []; self.build()

    def rel(self, p): return p if os.path.isabs(p) else os.path.join(self.root, p)
    def _probe(self, f): return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f], capture_output=True, text=True).stdout)

    # ---------- time ----------
    def T(self, v, default=None):
        if v is None: return default
        if isinstance(v, (int, float)): return float(v)
        m = re.match(r'^(.*?)([+-]\d+(?:\.\d+)?)?$', str(v).strip()); base, off = m.group(1), float(m.group(2) or 0)
        if base.startswith('w:'): return self.words[int(base[2:])]['t'] + off
        try: return float(base) + off
        except ValueError: pass
        key, n = (base.rsplit('@', 1) + ['1'])[:2] if '@' in base else (base, '1')
        cl = lambda x: re.sub(r'[^\w$%\']', '', x.lower()); k = cl(key)
        hits = [w['t'] for w in self.words if cl(w['w']) == k] or [w['t'] for w in self.words if k and k in cl(w['w'])]
        if not hits: raise ValueError(f'word "{key}" not found in words.json')
        return hits[min(int(n), len(hits)) - 1] + off

    def wrange(self, a, b):
        return [(w['w'], w['t']) for w in self.words if a - .001 <= w['t'] < b]

    # ---------- build ----------
    def img(self, p): return Image.open(self.rel(p))

    def build(self):
        P, st = self.P, self.st; shots = {}
        for e in self.s.get('elements', []):
            ty = e['type']; at = self.T(e.get('at')); un = self.T(e.get('until'))
            pos = tuple(e.get('pos', (.5, .5)))
            if ty == 'kinetic':
                fr = self.T(e.get('from', e.get('at'))); to = self.T(e.get('to'), fr + 3)
                ws = self.wrange(fr, to + .001) if not e.get('text') else [(w, fr + i * .18) for i, w in enumerate(e['text'].split())]
                if not ws: continue
                c = C.Kinetic(P, ws, pos, e.get('size', 96), set(x.lower() for x in e.get('hl', [])), set(x.lower() for x in e.get('hl2', [])), e.get('width', .8), un if un is not None else to + .6)
            elif ty == 'headline': c = C.Headline(P, e['text'], at, un, pos, e.get('size', 110), e.get('color', 'accent'), e.get('boxed', True))
            elif ty == 'card': c = C.Card(P, e['title'], e.get('sub'), at, un, pos, e.get('size', 64))
            elif ty == 'stat': c = C.Stat(P, e.get('fmt', '{:.0f}'), e.get('from', 0), e['to'], e.get('label', ''), at, un, pos, e.get('size', 190), e.get('dur', .8))
            elif ty == 'checklist':
                items = [(x[0], self.T(x[1])) for x in e['items']]; c = C.Checklist(P, items, pos, e.get('width', .42), e.get('title'), un, e.get('size', 42))
            elif ty == 'flow':
                nodes = [(n[0], n[1], self.T(n[2])) for n in e['nodes']]; c = C.Flow(P, nodes, e.get('y', .5), e.get('width', .86), un, e.get('size', 54))
            elif ty == 'screenshot':
                im = self.img(e['src'])
                if e.get('crop'): cr = e['crop']; im = im.crop((int(cr[0] * im.size[0]), int(cr[1] * im.size[1]), int(cr[2] * im.size[0]), int(cr[3] * im.size[1])))
                c = C.Shot(P, im, at, un, pos, e.get('width', .6), e.get('maxh', .62), e.get('label'))
                if e.get('id'): shots[e['id']] = c
            elif ty == 'callout':
                sh = shots[e['on']]; box = sh.box(e['box']) if 'on' in e else tuple(v * (self.W if i % 2 == 0 else self.H) for i, v in enumerate(e['box']))
                c = C.Callout(P, box, at, un, e.get('label'), e.get('kind'))
            elif ty == 'cross':
                b = e['box']; c = C.Cross(P, (b[0] * self.W, b[1] * self.H, b[2] * self.W, b[3] * self.H), at, un)
            elif ty == 'logo': c = C.Logo(P, self.img(e['src']), at, un, pos, e.get('h', 150), e.get('plate', True))
            elif ty == 'step': c = C.Step(P, e.get('n', 1), e['title'], at, un)
            elif ty == 'progress': c = C.Progress(P, e.get('label', ''), at, un, pos, e.get('width', .52), e.get('dur', 1.4))
            elif ty == 'bubble':
                d = st['mascot']['dock']; anc = (d[0] * self.W + 60 * P.k, d[1] * self.H - st['mascot']['size'] * P.k * .6)
                c = C.Bubble(P, e['text'], anc, at, un)
            else: raise ValueError('unknown element type ' + ty)
            self.items.append(c); self.ev += c.sfx
            if e.get('sfx'): self.ev.append((at, e['sfx']))
        self.caps = []                      # captions are drawn after the camera so a zoom never pushes them off screen
        if self.s.get('captions'):
            cy = st['captions']['y']; mx = st['captions']['max_words']; ch = []
            for w in self.words:
                ch.append((w['w'], w['t']))
                if len(ch) >= mx or w['w'].endswith(('.', ',', '?', '!', '،', '؟')): self._cap(ch, cy); ch = []
            if ch: self._cap(ch, cy)
        self.over = []
        mimg = st.file(st['mascot']['image']) if st['mascot'].get('image') else None
        if mimg:
            keys = [(self.T(m['at']), m.get('do', 'show'), None, None) for m in self.s.get('mascot', [])] or [(.3, 'show', None, None)]
            if self.s.get('format') == '9:16': mc = C.Mascot(P, Image.open(mimg), keys, dock=(.14 * self.W, .64 * self.H), size=st['mascot']['size'] * .9)
            else: mc = C.Mascot(P, Image.open(mimg), keys)
            self.over.append(mc); self.ev += mc.sfx
        self.cam = Camera([(self.T(k['at']), k.get('zoom', 1), k.get('x', .5), k.get('y', .5), k.get('ease', 'expo')) for k in self.s.get('camera', [])] or [(0, 1, .5, .5)], self.W, self.H)
        tr = [self.T(x) for x in self.s.get('transitions', [])]; sh = [(self.T(x), 14 * P.k) for x in self.s.get('shakes', [])] if st['motion']['shake'] else []
        self.fx = Transitions(st, tr, sh, self.W, self.H); self.ev += [(x, 'transition') for x in tr] + [(x[0], 'big') for x in sh]
        self.bg = AnimatedBG(P)

    def _cap(self, ch, cy):
        idx = self.st['captions']; t0 = ch[0][1]
        nxt = [w['t'] for w in self.words if w['t'] > ch[-1][1]]; t1 = (nxt[0] - .2) if nxt else self.dur
        k = C.Kinetic(self.P, ch, (.5, cy), 104 if self.W < self.H else 80, set(), set(), .88, t1); k.sfx = []
        self.caps.append(k)

    # ---------- render ----------
    def frame(self, t):
        fr = self.bg(t)
        for c in self.items:
            if c.a <= t < c.b: c.draw(fr, t)
        fr = self.cam.apply(fr, t)
        for c in self.caps:
            if c.a <= t < c.b: c.draw(fr, t)
        for c in self.over: c.draw(fr, t)
        return self.fx(fr, t)

    def render_range(self, i0, i1, out):
        cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{self.W}x{self.H}', '-r', str(self.fps), '-i', '-',
               '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '12', '-pix_fmt', 'yuv420p', out]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(i0, i1):
            t = i / self.fps
            if self.cam.speed(t) > 25:
                import numpy as np
                a = (np.asarray(self.frame(t), np.float32) + np.asarray(self.frame(t + .5 / self.fps), np.float32)) / 2
                fr = Image.fromarray(a.astype('uint8'), 'RGBA')
            else: fr = self.frame(t)
            p.stdin.write(fr.tobytes())
        p.stdin.close(); p.wait(); return out


_S = None
def _work(args):
    i0, i1, out = args; return _S.render_range(i0, i1, out)


def render(story_path, out=None, preview=False, jobs=None):
    """full pipeline: frames (parallel) + SFX + VO + intro + watermark + EditDNA stamp."""
    global _S
    _S = S = Story(story_path, 15 if preview else None)
    out = os.path.abspath(out) if out else os.path.join(S.root, ('preview' if preview else 'final') + '.mp4'); work = out + '_parts'; os.makedirs(work, exist_ok=True)
    n = int(round(S.dur * S.fps)); jobs = jobs or max(1, (os.cpu_count() or 2) - (0 if preview else 0)); cut = [round(n * k / jobs) for k in range(jobs + 1)]
    parts = [(cut[k], cut[k + 1], os.path.join(work, f'p{k}.mp4')) for k in range(jobs)]
    with mp.get_context('fork').Pool(jobs) as pool: pool.map(_work, parts)
    open(os.path.join(work, 'l.txt'), 'w').write(''.join(f"file '{p[2]}'\n" for p in parts))
    vid = os.path.join(work, 'video.mp4'); subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', os.path.join(work, 'l.txt'), '-c', 'copy', vid], check=True)
    sfx = sound.mix(S.ev, S.dur, os.path.join(work, 'sfx.wav'), S.st['sound']['profile'], S.st['sound']['volume'])
    st = S.st; intro_at = S.s.get('intro_at'); intro = None
    if intro_at is not None and st['brand'].get('intro') and not preview:
        from .intro import make_intro
        intro = make_intro(st, os.path.join(work, 'intro.mp4'), S.W, S.H, S.fps)
    logo = st.file(st['brand']['logo']) if st['brand'].get('logo') and st['brand'].get('watermark') else None
    finish(vid, S.vo, sfx, out, intro, float(intro_at or 0), logo, int(st['brand'].get('watermark_width', 220) * S.P.k), S.dur)
    return out


def finish(vid, vo, sfx, out, intro=None, intro_at=0., logo=None, wmw=220, dur=None):
    """mux VO + SFX; optional intro inserted at intro_at; optional watermark; EditDNA stamp in metadata."""
    tmp = out + '_tmp'; os.makedirs(tmp, exist_ok=True)
    a_in = ['-i', vo] if vo else ['-f', 'lavfi', '-t', str(dur), '-i', 'anullsrc=r=48000:cl=mono']
    mixed = os.path.join(tmp, 'mix.wav')
    subprocess.run(['ffmpeg', '-v', 'error', '-y'] + a_in + ['-i', sfx, '-filter_complex', '[0:a]aresample=48000,apad[v];[1:a]aresample=48000[s];[v][s]amix=inputs=2:normalize=0:duration=longest,alimiter=limit=0.95[a]',
                    '-map', '[a]', '-t', str(dur), mixed], check=True)
    if intro:
        A = os.path.join(tmp, 'a.mp4'); B = os.path.join(tmp, 'b.mp4')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', vid, '-i', mixed, '-t', str(intro_at), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '12', '-c:a', 'aac', A], check=True)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(intro_at), '-i', vid, '-ss', str(intro_at), '-i', mixed, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '12', '-c:a', 'aac', B], check=True)
        seq = [A, intro, B] if intro_at > 0 else [intro, B]
        open(os.path.join(tmp, 'l.txt'), 'w').write(''.join(f"file '{x}'\n" for x in seq))
        joined = os.path.join(tmp, 'joined.mp4')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', os.path.join(tmp, 'l.txt'), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '12', '-c:a', 'aac', joined], check=True)
        src = ['-i', joined]; amap = ['-map', '0:a']
    else:
        src = ['-i', vid, '-i', mixed]; amap = ['-map', '1:a']
    meta = ['-metadata', f'comment={STAMP}', '-metadata', 'encoded_by=EditDNA', '-metadata', 'software=EditDNA']
    enc = ['-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart']
    if logo:
        n_in = len([x for x in src if x == '-i'])
        subprocess.run(['ffmpeg', '-v', 'error', '-y'] + src + ['-i', logo, '-filter_complex', f'[{n_in}:v]scale={wmw}:-1,format=rgba,colorchannelmixer=aa=0.85[w];[0:v][w]overlay=W-w-30:H-h-24[v]',
                        '-map', '[v]'] + amap + enc + meta + [out], check=True)
    else:
        subprocess.run(['ffmpeg', '-v', 'error', '-y'] + src + ['-map', '0:v'] + amap + enc + meta + [out], check=True)
    return out
