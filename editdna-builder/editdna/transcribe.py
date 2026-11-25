# EditDNA — personal-use license, see LICENSE. (c) EditDNA. Do not redistribute or sell.
"""voice-over -> words.json [{"w": word, "t": start, "e": end}] with faster-whisper (word timestamps)."""
import json, subprocess, os


def clean_vo(src, out):
    """broadcast-style polish: low cut, de-ess, compression, -14 LUFS"""
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-af', 'highpass=f=80,equalizer=f=250:t=q:w=1:g=-2,equalizer=f=3500:t=q:w=1.2:g=3,'
                    'deesser=i=0.4,acompressor=threshold=-20dB:ratio=3:attack=5:release=80:makeup=3,loudnorm=I=-14:TP=-1.5:LRA=7', '-ar', '48000', out], check=True)
    return out


def transcribe(wav, out, language=None, model='small', script=None):
    """script (optional): the exact text that was read — words are re-spelled to match it (better captions)."""
    from faster_whisper import WhisperModel
    m = WhisperModel(model, device='cpu', compute_type='int8')
    segs, _ = m.transcribe(wav, language=language, word_timestamps=True, vad_filter=True)
    W = [dict(w=w.word.strip(), t=round(w.start, 3), e=round(w.end, 3)) for s in segs for w in s.words if w.word.strip()]
    if script:
        txt = open(script, encoding='utf-8').read().split()
        if abs(len(txt) - len(W)) <= max(3, len(W) * .03):
            import difflib
            sm = difflib.SequenceMatcher(a=[x['w'].lower().strip('.,!?') for x in W], b=[x.lower().strip('.,!?') for x in txt])
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                if tag == 'replace' and i2 - i1 == j2 - j1:
                    for k in range(i2 - i1): W[i1 + k]['w'] = txt[j1 + k]
    json.dump(W, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    return out
