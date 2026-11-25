---
name: editdna-builder
description: Builds a person's own motion-graphics editing skill for their YouTube/TikTok channel. Interviews them (channel, language, content, colours, logo, reference screenshots), designs a matching editing style, shows a preview, then generates a ready-to-use CHANNEL-editdna skill that edits their videos in that style.
---

# EditDNA Builder

<!-- EditDNA — personal-use license, see LICENSE. (c) EditDNA. Do not redistribute or sell. -->

You are building ONE person their OWN editing style and turning it into a reusable skill.
The result must look like *their* channel — never a generic template. Work in this order and do not skip the preview.

## 0. Setup (once)
Run from this skill's folder (where `run.py` is):
```
python --version            # 3.10+
ffmpeg -version             # must exist. Windows: winget install Gyan.FFmpeg   macOS: brew install ffmpeg   Linux: apt install ffmpeg
pip install -r requirements.txt
```
If a command is missing, tell the person exactly what to install, in their language, one step at a time, and wait.

## 1. Interview (ask in the person's language, 1–2 questions per message, keep it friendly)
1. Which language do you want me to talk to you in?
2. Channel name? (and a short tagline if they have one)
3. What is the channel about, and who watches it? (niche + audience)
4. Language of the videos? (Arabic → direction "rtl", everything else "ltr")
5. Do you have screenshots of videos/channels whose editing style you love? Ask them to put 2–6 images in a folder and give you the path. Also ask *what* they like in each (colours? text? energy?).
6. Colours you love / hate? Any brand colours?
7. Logo file? (PNG with transparent background is best). A mascot/character image? (optional — it will float on screen and react)
8. Energy: calm and clean, balanced, or hype and fast?
9. Long videos, shorts, or both?

Write their answers into `my-style/answers.md` as you go (create the folder next to where they keep their channel files, not inside this skill).

## 2. Study the references
- LOOK at every reference image yourself. Note: background (dark/light, flat/gradient/texture/grid/dots), how text is highlighted (coloured box, underline, marker, outline box, just colour), corner roundness, borders, shadows (none / soft drop shadow / hard offset sticker shadow / neon glow), how screenshots are framed, energy.
- Get the real colours: `python run.py palette --ref <img1> <img2> ... --mood <1-3 words> --like "#hex"`
  Mood words: calm, tech, bold, luxury, fun, nature, news, clean, gaming, money, kids, food.
- Pick fonts: `python run.py fonts` lists free fonts with their vibe and script. Arabic videos MUST use a font marked "arabic+latin".
  Download: `python run.py font "<Name>" my-style/fonts`  (heading, body and mono — 3 fonts).

## 3. Write my-style/style.json
Start from this and change everything to match the person (do not leave defaults that don't fit):
```json
{
 "channel": {"name": "", "language": "en", "direction": "ltr", "content": "", "audience": "", "tagline": ""},
 "palette": {"bg": "#", "surface": "#", "text": "#", "muted": "#", "accent": "#", "accent2": "#", "good": "#", "bad": "#"},
 "fonts": {"heading": "<file in fonts/>", "body": "<file>", "mono": "<file>"},
 "shape": {"radius": 22, "border": 3, "border_color": "accent", "shadow": "soft", "shadow_color": "#000000", "shadow_offset": 10, "tilt": 2},
 "background": {"type": "gradient", "color2": "surface", "pattern_color": "accent", "pattern_alpha": 28, "animate": true, "vignette": 0.3, "glow": true},
 "text": {"case": "upper", "highlight": "pill", "kinetic": "pop", "size_scale": 1.0},
 "motion": {"energy": "medium", "camera_zoom": 1.22, "transition": "flash", "shake": true},
 "frames": {"screenshot": "window", "callout": "box"},
 "sound": {"profile": "punchy", "volume": 0.55},
 "mascot": {"image": null, "size": 230, "dock": [0.1, 0.82]},
 "brand": {"logo": "assets/logo.png", "watermark": true, "watermark_width": 220, "intro": true},
 "captions": {"style": "outline", "y": 0.76, "max_words": 3}
}
```
Options (pick per person):
| key | choices | feels like |
|---|---|---|
| shape.shadow | none, soft, hard, glow | flat / classic / sticker / neon |
| background.type | solid, gradient, dots, grid, stripes, grain, paper | clean / modern / techy / blueprint / energetic / film / handmade |
| text.case | upper, title, none | loud / friendly / calm |
| text.highlight | pill, marker, underline, box, color | bold / handmade / editorial / techy / minimal |
| text.kinetic | pop, bounce, slide, fade | punchy / playful / smooth / calm |
| motion.transition | flash, glitch, slide, zoom, wipe, cut | energetic / digital / smooth / impact / branded / minimal |
| frames.screenshot | window, plain, polaroid, phone | app UI / clean / scrapbook / mobile |
| frames.callout | box, brackets, circle, arrow | neat / techy / hand-drawn / tutorial |
| sound.profile | punchy, digital, soft, organic, none | (SFX only, never music) |
Rules: text vs bg and text vs surface contrast ≥ 4.5 (`python run.py check my-style/style.json`). accent ≠ accent2. Copy logo/mascot into `my-style/assets/`.
You are inspired by the references, you do not copy them: no logos, characters or exact layouts from other channels.

## 4. Preview and refine (loop until they say yes)
```
python run.py preview my-style/style.json my-style/preview
```
Show them `style_board.jpg` (every element at once) and `style_demo.mp4` (motion + sound). Ask what to change in plain words
("more colourful", "softer", "less shaking", "bigger text", "I don't like the font") and map it back to style.json. Also run
`python run.py intro my-style/style.json my-style/preview/intro.mp4` once the logo is in.

## 5. Generate their skill
```
python make_channel.py my-style <folder where they keep skills>
```
This creates `<channel>-editdna/` (SKILL.md, style.json, fonts, assets, engine, example) and `<channel>-editdna.zip` next to it. Tell them, in their language:
- where it is, and how to add it to their agent (Claude app: Settings → Capabilities → Skills → upload `<channel>-editdna.zip`; OpenCode / Claude Code: copy the folder into the skills folder),
- the one sentence they will use from now on: **"Use the <channel>-editdna skill to edit this video: voice-over <file>, script <file>, screenshots in <folder>."**

## Ownership
EditDNA is free for personal use only (see LICENSE). Keep the "EditDNA" header lines in every file. Every video rendered with
EditDNA carries "Made with EditDNA" in its file metadata. Do not remove these.
