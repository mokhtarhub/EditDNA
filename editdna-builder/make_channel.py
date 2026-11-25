# EditDNA — personal-use license, see LICENSE. (c) EditDNA. Do not redistribute or sell.
"""Turn an approved style folder into the channel's own editing skill.
python make_channel.py <style_folder> <output_parent_folder>
<style_folder> holds style.json + fonts/ + assets/ (logo, mascot)."""
import os, sys, json, shutil, re

HERE = os.path.dirname(os.path.abspath(__file__))


def slug(s): return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-') or 'my-channel'


def main(src, parent):
    st = json.load(open(os.path.join(src, 'style.json'), encoding='utf-8'))
    name = st['channel']['name']; sl = slug(name) + '-editdna' if not re.search(r'[؀-ۿ]', name) else 'channel-editdna'
    dst = os.path.join(parent, sl)
    if os.path.exists(dst): shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns('preview*', '*.mp4', '*_parts'))
    shutil.copytree(os.path.join(HERE, 'editdna'), os.path.join(dst, 'editdna'), ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copy(os.path.join(HERE, 'run.py'), dst); shutil.copy(os.path.join(HERE, 'requirements.txt'), dst)
    lic = os.path.join(os.path.dirname(HERE), 'LICENSE')
    if os.path.exists(lic): shutil.copy(lic, dst)
    os.makedirs(os.path.join(dst, 'examples'), exist_ok=True)
    shutil.copy(os.path.join(HERE, 'templates', 'example_story.json'), os.path.join(dst, 'examples', 'example_story.json'))
    t = open(os.path.join(HERE, 'templates', 'channel_SKILL.md'), encoding='utf-8').read()
    ch = st['channel']
    rep = {'{{NAME}}': name, '{{SLUG}}': sl, '{{LANG}}': ch.get('language', 'en'), '{{DIR}}': ch.get('direction', 'ltr'),
           '{{CONTENT}}': ch.get('content', ''), '{{AUDIENCE}}': ch.get('audience', ''), '{{TAGLINE}}': ch.get('tagline', ''),
           '{{ENERGY}}': st.get('motion', {}).get('energy', 'medium'), '{{MASCOT}}': 'yes' if st.get('mascot', {}).get('image') else 'no'}
    for k, v in rep.items(): t = t.replace(k, str(v))
    open(os.path.join(dst, 'SKILL.md'), 'w', encoding='utf-8').write(t)
    print(dst)


if __name__ == '__main__': main(sys.argv[1], sys.argv[2])
