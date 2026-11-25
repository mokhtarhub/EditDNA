# EditDNA — personal-use license, see LICENSE. (c) EditDNA. Do not redistribute or sell.
"""Style preview: one board image with every element + an 8-second demo clip, so the person can approve the look."""
import os, subprocess, tempfile
from PIL import Image, ImageDraw
from .style import Style
from .draw import Painter
from . import comps as C, sound
from .fx import AnimatedBG, Transitions, Camera


def _demo_shot(P):
    im = Image.new('RGB', (1600, 900), (236, 238, 242)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1600, 90), fill=(40, 44, 52)); d.rounded_rectangle((80, 160, 760, 420), 18, fill=(255, 255, 255))
    d.rounded_rectangle((840, 160, 1520, 420), 18, fill=(255, 255, 255)); d.rounded_rectangle((80, 480, 1520, 820), 18, fill=(255, 255, 255))
    d.rounded_rectangle((1240, 700, 1480, 780), 14, fill=P.st.col('accent'))
    return im


def scene(st, W=1920, H=1080, lang_sample=None):
    P = Painter(st, W, H); ar = st.rtl
    s = lang_sample or (['هنعمل', 'ده', 'في', 'دقيقة', 'واحدة'] if ar else ['make', 'this', 'in', 'one', 'minute'])
    words = [(w, .3 + i * .22) for i, w in enumerate(s)]
    items = [C.Step(P, 1, 'المرحلة الأولى' if ar else 'First step', .1),
             C.Kinetic(P, words, (.5, .2), 92, {s[3].lower(), s[4].lower()}, set(), .8),
             C.Headline(P, 'مجاناً' if ar else 'FREE', 1.6, None, (.17, .45), 120),
             C.Card(P, 'كارت عنوان' if ar else 'Title card', 'سطر صغير' if ar else 'small detail line', 1.9, None, (.17, .7), 60),
             C.Stat(P, '{:,.0f}', 0, 25000, 'مشاهدة' if ar else 'views', 2.2, None, (.84, .4), 120),
             C.Checklist(P, [('خطوة واحد' if ar else 'Step one', 2.6), ('خطوة اتنين' if ar else 'Step two', 3.0)], (.84, .74), .26, 'قايمة' if ar else 'checklist', None, 36)]
    sh = C.Shot(P, _demo_shot(P), 1.2, None, (.5, .6), .34, .4, 'screen'); items.insert(2, sh)
    items.append(C.Callout(P, sh.box((.77, .77, .93, .87)), 3.3, None, 'اضغط هنا' if ar else 'click here'))
    mimg = st.file(st['mascot']['image']) if st['mascot'].get('image') else None
    over = [C.Mascot(P, Image.open(mimg), [(.4, 'show', None, None), (3.6, 'hop', None, None)])] if mimg else []
    return P, items, over


def board(style_path, out):
    st = Style(style_path); P, items, over = scene(st); fr = AnimatedBG(P)(1.0)
    for c in items: c.draw(fr, 6.0)
    for c in over: c.draw(fr, 6.0)
    fr.convert('RGB').save(out, quality=92); return out


def demo(style_path, out, fps=30, dur=6.5):
    st = Style(style_path); P, items, over = scene(st); bg = AnimatedBG(P)
    cam = Camera([(0, 1, .5, .5), (3.25, 1, .5, .5), (3.5, 1.35, .78, .78), (5.2, 1.38, .78, .78, 'smooth'), (5.5, 1, .5, .5)], P.W, P.H)
    fx = Transitions(st, [0.0, 3.5], [(1.6, 14)] if st['motion']['shake'] else [], P.W, P.H)
    tmp = tempfile.mkdtemp(); v = os.path.join(tmp, 'v.mp4'); a = os.path.join(tmp, 'a.wav')
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{P.W}x{P.H}', '-r', str(fps), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', v], stdin=subprocess.PIPE)
    ev = [(0, 'transition'), (3.5, 'transition')]
    for c in items + over: ev += c.sfx
    for i in range(int(dur * fps)):
        t = i / fps; fr = bg(t)
        for c in items:
            if c.a <= t < c.b: c.draw(fr, t)
        fr = cam.apply(fr, t)
        for c in over: c.draw(fr, t)
        p.stdin.write(fx(fr, t).tobytes())
    p.stdin.close(); p.wait(); sound.mix(ev, dur, a, st['sound']['profile'], st['sound']['volume'])
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', v, '-i', a, '-c:v', 'copy', '-c:a', 'aac', '-shortest', '-metadata', 'comment=Made with EditDNA', out], check=True)
    return out
