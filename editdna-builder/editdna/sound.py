# EditDNA — personal-use license, see LICENSE. (c) EditDNA. Do not redistribute or sell.
"""Procedural SFX (never music). A 'profile' gives the channel its own sound family.
events: enter, big, tick, tick2, whoosh, success, fail, count, transition, mascot, pop, money"""
import os, wave, numpy as np
SR = 48000


def _t(d): return np.arange(int(SR * d)) / SR
def _env(n, a=.003, r=6.):
    e = np.ones(n); na = max(1, int(a * SR)); e[:na] = np.linspace(0, 1, na); e[na:] = np.exp(-np.linspace(0, r, n - na)); return e
def _sweep(f0, f1, d, wave_='sin'):
    t = _t(d); f = f0 * (f1 / f0) ** (t / d); ph = 2 * np.pi * np.cumsum(f) / SR
    return {'sin': np.sin(ph), 'sq': np.sign(np.sin(ph)) * .6, 'tri': 2 / np.pi * np.arcsin(np.sin(ph))}[wave_]
def _noise(d, seed=0): return np.random.default_rng(seed).uniform(-1, 1, int(SR * d))
def _bp(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X[(f < lo) | (f > hi)] *= .04; return np.fft.irfft(X, len(x))
def _crush(x, bits=6, hold=5): q = 2 ** bits; y = np.round(x * q) / q; return np.repeat(y[::hold], hold)[:len(x)]


def _whoosh(d, lo, hi, seed=1): x = _bp(_noise(d, seed), lo, hi); return x * np.hanning(len(x)) ** 1.4
def _thump(f=60, d=.35): return np.sin(2 * np.pi * f * _t(d) * (1 + 1.5 * np.exp(-_t(d) * 30))) * _env(int(SR * d), .002, 5)
def _click(d=.02, lo=2000, hi=9000, seed=3): return _bp(_noise(d, seed), lo, hi) * _env(int(SR * d), .0005, 8)
def _tone(f, d, w='sin', r=6): return _sweep(f, f, d, w) * _env(int(SR * d), .002, r)
def _two(a, b, gap=.07):
    out = np.zeros(len(a) + int(gap * SR) + len(b)); out[:len(a)] += a; out[int(gap * SR):int(gap * SR) + len(b)] += b; return out


PROFILES = {
    'digital': lambda: dict(enter=_sweep(300, 1400, .06) * _env(int(SR * .06), r=4), big=_crush(_thump(55, .4) + _sweep(2000, 200, .4, 'sq') * .3 * _env(int(SR * .4), r=5)),
                            tick=_click(.015) * .7, tick2=_tone(1800, .05, 'sin', 7), whoosh=_crush(_whoosh(.4, 400, 5000), 7, 3),
                            success=_two(_tone(950, .05), _tone(1600, .07)), fail=(_sweep(190, 170, .22, 'sq') + _sweep(202, 180, .22, 'sq')) * .5 * _env(int(SR * .22), r=2.5),
                            count=_sweep(180, 1400, .45, 'sq') * np.linspace(.3, 1, int(SR * .45)) * _env(int(SR * .45), r=.8),
                            transition=_crush(_noise(.22, 9) * .6 + _sweep(300, 3000, .22, 'sq') * .4, 4, 9) * _env(int(SR * .22), r=2),
                            mascot=_sweep(500, 1300, .09) * _env(int(SR * .09), r=3), pop=_sweep(300, 1400, .05) * _env(int(SR * .05), r=5),
                            money=_two(_tone(988, .07, 'sq', 2), _tone(1319, .25, 'sq', 4))),
    'soft': lambda: dict(enter=_tone(660, .12, 'tri', 5) * .7, big=_thump(70, .5) * .8 + _whoosh(.5, 200, 1200) * .5, tick=_click(.012, 1500, 5000) * .4,
                         tick2=_tone(880, .1, 'tri', 5), whoosh=_whoosh(.45, 300, 2500), success=_two(_tone(660, .12, 'tri', 4), _tone(990, .2, 'tri', 4), .09),
                         fail=_tone(220, .3, 'tri', 3), count=_sweep(300, 900, .5, 'tri') * np.linspace(.2, 1, int(SR * .5)) * _env(int(SR * .5), r=1),
                         transition=_whoosh(.4, 250, 2000, 5), mascot=_sweep(500, 900, .14, 'tri') * _env(int(SR * .14), r=3), pop=_tone(700, .06, 'tri', 6),
                         money=_two(_tone(1046, .1, 'tri', 3), _tone(1568, .3, 'tri', 3))),
    'punchy': lambda: dict(enter=_whoosh(.16, 1500, 7000, 2) * .8 + _click(.02) * .6, big=_thump(48, .45) + _click(.03, 800, 6000) * .8, tick=_click(.014, 3000, 10000) * .5,
                           tick2=_click(.03, 1200, 5000), whoosh=_whoosh(.3, 600, 7000), success=_two(_click(.02), _tone(1200, .12, 'sin', 5)),
                           fail=_thump(90, .3) + _tone(150, .3, 'sq', 3) * .4, count=_sweep(200, 1200, .4, 'sin') * np.linspace(.3, 1, int(SR * .4)) * _env(int(SR * .4), r=.8),
                           transition=_whoosh(.32, 400, 8000, 4) + _thump(55, .3) * .6, mascot=_sweep(400, 1200, .1) * _env(int(SR * .1), r=3), pop=_sweep(250, 1100, .05) * _env(int(SR * .05), r=5),
                           money=_two(_click(.03, 2000, 8000), _tone(1800, .2, 'sin', 4))),
    'organic': lambda: dict(enter=_bp(_noise(.05, 4), 300, 3000) * _env(int(SR * .05), .001, 9), big=_thump(65, .5) * .9, tick=_bp(_noise(.01, 5), 1500, 6000) * _env(int(SR * .01), .0005, 6) * .5,
                            tick2=_tone(520, .08, 'sin', 9) + _bp(_noise(.08, 6), 800, 3000) * .3 * _env(int(SR * .08)), whoosh=_whoosh(.5, 150, 1800, 7),
                            success=_two(_tone(523, .09, 'sin', 6), _tone(784, .16, 'sin', 5)), fail=_tone(180, .25, 'sin', 4) + _thump(80, .25) * .5,
                            count=_sweep(200, 700, .45, 'sin') * _env(int(SR * .45), r=1.2), transition=_whoosh(.45, 120, 1500, 8), mascot=_tone(600, .1, 'sin', 6),
                            pop=_bp(_noise(.04, 7), 400, 2500) * _env(int(SR * .04), .001, 7), money=_two(_tone(784, .1, 'sin', 5), _tone(1046, .22, 'sin', 4))),
}
GAIN = dict(enter=.7, big=.85, tick=.18, tick2=.6, whoosh=.5, success=.55, fail=.65, count=.4, transition=.55, mascot=.3, pop=.6, money=.75)


def bank(profile):
    if profile == 'none': return {}
    S = PROFILES.get(profile, PROFILES['punchy'])()
    return {k: (np.asarray(v, np.float32) / (np.abs(v).max() or 1) * .89) for k, v in S.items()}


def mix(events, dur, out, profile='punchy', volume=.55):
    B = bank(profile); buf = np.zeros(int(SR * (dur + 2)), np.float32)
    for t0, ev in events:
        x = B.get(ev)
        if x is None or t0 < 0: continue
        i = int(t0 * SR); n = min(len(x), len(buf) - i)
        if n > 0: buf[i:i + n] += x[:n] * GAIN.get(ev, .5)
    buf = np.clip(buf[:int(SR * dur)] * volume, -1, 1)
    with wave.open(out, 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((buf * 32767).astype(np.int16).tobytes())
    return out
