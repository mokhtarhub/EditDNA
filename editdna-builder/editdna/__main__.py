# EditDNA — personal-use license, see LICENSE. (c) EditDNA. Do not redistribute or sell.
"""python -m editdna <command>
  fonts                         list the free font catalog
  font  "<name>" <dir>          download a font into <dir>
  palette [--ref a.png ...] [--mood tech ...] [--like '#hex' ...]   suggest palettes (JSON)
  check   style.json            contrast / missing files
  preview style.json [out_dir]  board.jpg + demo.mp4
  intro   style.json out.mp4    channel intro
  clean   in.wav out.wav        polish the voice-over
  words   vo.wav words.json [--lang en] [--script text.txt]   word timings (faster-whisper)
  render  story.json [--preview] [--out file.mp4]"""
import sys, json, os, argparse


def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    if not a or a[0] in ('-h', '--help'): print(__doc__); return
    cmd, rest = a[0], a[1:]
    if cmd == 'fonts':
        from .fonts import CATALOG
        for k, (p, vibe, sc) in CATALOG.items(): print(f'{k:20s} {sc:13s} {vibe}')
    elif cmd == 'font':
        from .fonts import get; print(get(rest[0], rest[1]))
    elif cmd == 'palette':
        ap = argparse.ArgumentParser(); ap.add_argument('--ref', nargs='*', default=[]); ap.add_argument('--mood', nargs='*', default=[]); ap.add_argument('--like', nargs='*', default=[])
        o = ap.parse_args(rest); from .palette import suggest; print(json.dumps(suggest(o.ref, o.mood, o.like), indent=1))
    elif cmd == 'check':
        from .style import Style; p = Style(rest[0]).check(); print('\n'.join(p) if p else 'OK')
    elif cmd == 'preview':
        from .preview import board, demo; out = rest[1] if len(rest) > 1 else os.path.dirname(os.path.abspath(rest[0])); os.makedirs(out, exist_ok=True)
        print(board(rest[0], os.path.join(out, 'style_board.jpg'))); print(demo(rest[0], os.path.join(out, 'style_demo.mp4')))
    elif cmd == 'intro':
        from .style import Style; from .intro import make_intro; print(make_intro(Style(rest[0]), rest[1]))
    elif cmd == 'clean':
        from .transcribe import clean_vo; print(clean_vo(rest[0], rest[1]))
    elif cmd == 'words':
        ap = argparse.ArgumentParser(); ap.add_argument('vo'); ap.add_argument('out'); ap.add_argument('--lang'); ap.add_argument('--script'); ap.add_argument('--model', default='small')
        o = ap.parse_args(rest); from .transcribe import transcribe; print(transcribe(o.vo, o.out, o.lang, o.model, o.script))
    elif cmd == 'render':
        ap = argparse.ArgumentParser(); ap.add_argument('story'); ap.add_argument('--preview', action='store_true'); ap.add_argument('--out'); ap.add_argument('--jobs', type=int)
        o = ap.parse_args(rest); from .story import render; print(render(o.story, o.out, o.preview, o.jobs))
    else: print(__doc__)


if __name__ == '__main__': main()
