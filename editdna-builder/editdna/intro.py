# EditDNA — personal-use license, see LICENSE. (c) EditDNA. Do not redistribute or sell.
"""2.5 s channel intro generated from the style: logo + name + tagline, with the channel's motion and sound."""
import os, subprocess, tempfile
from PIL import Image
from .draw import Painter
from .fx import AnimatedBG, Transitions
from . import comps as C, sound


def make_intro(st, out, W=1920, H=1080, fps=60, dur=2.6):
    P = Painter(st, W, H); ch = st['channel']; items = []; ev = [(0, 'transition')]
    lg = st.file(st['brand']['logo']) if st['brand'].get('logo') else None
    if lg: items.append(C.Logo(P, Image.open(lg), .15, dur - .2, (.5, .38), 220, plate=False)); ev.append((.15, 'big'))
    words = [(w, .55 + i * .12) for i, w in enumerate(ch['name'].split())]
    items.append(C.Kinetic(P, words, (.5, .62 if lg else .48), 120, {words[-1][0].lower()} if len(words) > 1 else set(), set(), .9, dur - .15))
    ev += [(t, 'enter') for _, t in words]
    if ch.get('tagline'): items.append(C.Headline(P, ch['tagline'], 1.2, dur - .15, (.5, .78 if lg else .66), 52, 'accent2')); ev.append((1.2, 'pop'))
    bg = AnimatedBG(P); fx = Transitions(st, [0.0, dur - .05], [], W, H)
    tmp = tempfile.mkdtemp(); v = os.path.join(tmp, 'v.mp4'); a = os.path.join(tmp, 'a.wav')
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-r', str(fps), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '12', '-pix_fmt', 'yuv420p', v], stdin=subprocess.PIPE)
    for i in range(int(dur * fps)):
        t = i / fps; fr = bg(t)
        for c in items:
            if c.a <= t < c.b: c.draw(fr, t)
        p.stdin.write(fx(fr, t).tobytes())
    p.stdin.close(); p.wait()
    sound.mix(ev, dur, a, st['sound']['profile'], st['sound']['volume'])
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', v, '-i', a, '-c:v', 'copy', '-c:a', 'aac', '-ar', '48000', '-ac', '1', '-shortest', out], check=True)
    return out
