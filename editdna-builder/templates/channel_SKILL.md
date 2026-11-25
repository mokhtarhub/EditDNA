---
name: {{SLUG}}
description: Edits videos for the channel "{{NAME}}" in its own fixed motion-graphics style (made with EditDNA). Use when the person gives a voice-over (and optionally a script and screenshots) and asks for a video, a short, or a preview.
---

# {{NAME}} — video editor (EditDNA)

<!-- EditDNA — personal-use license, see LICENSE. (c) EditDNA. Do not redistribute or sell. -->

The style is FIXED in `style.json` (colours, fonts, shapes, motion, sound, logo). Never change it while editing a video —
if the person wants a different look, they re-run the EditDNA builder. Channel: {{CONTENT}} · audience: {{AUDIENCE}} · video language: {{LANG}} ({{DIR}}) · energy: {{ENERGY}}.

All commands run from this folder: `python run.py <command>`. Setup once: `pip install -r requirements.txt` (+ ffmpeg).

## Workflow (do every step)
1. **Collect** into a new project folder: `vo.wav` (voice-over), `script.txt` (exact text read, optional but better), `shots/` (screenshots/images), logos of tools/brands mentioned (PNG).
2. **Clean the voice:** `python run.py clean vo_raw.wav vo.wav`
3. **Word timings:** `python run.py words vo.wav words.json --lang {{LANG}} --script script.txt`
   Open words.json — every word has its time. You will tie EVERY visual to a word.
4. **Plan** (write it down as a list): split the script into beats (one idea = one beat). For each beat choose ONE main visual and the word it lands on.
5. **Write `story.json`** (format below; start from `examples/example_story.json`).
6. **Preview:** `python run.py render story.json --preview` → `preview.mp4` (15 fps, fast). If you can view images, extract a frame every 2 s
   (`ffmpeg -i preview.mp4 -vf fps=1/2,scale=384:-1,tile=6x5 sheet.jpg`) and check: nothing cut off, nothing overlapping, no beat without a visual for more than ~1 s, text readable.
7. **Final:** `python run.py render story.json` → `final.mp4` (1080p, 60 fps, voice + SFX + intro + watermark). Tell the person it is ready and where.
8. **Shorts:** same voice process, `"format": "9:16"`, `"captions": true`, visuals between y 0.15–0.6, keep the mascot zone (bottom-left) free.

## story.json
```json
{"style": "style.json", "vo": "vo.wav", "words": "words.json", "format": "16:9", "fps": 60, "intro_at": 12.4,
 "elements": [ ... ], "mascot": [ ... ], "camera": [ ... ], "transitions": [ ... ], "shakes": [ ... ], "captions": false}
```
**TIME** (`at`, `until`, `from`, `to`): `"money"` = when the word "money" is said (first time) · `"money@2"` second time · `"w:57"` word #57 ·
`12.3` seconds · add offsets: `"money-0.1"`, `"so+0.3"`. Every element needs `at`; give `until` = the word where the NEXT beat starts minus 0.05 (`"next-0.05"`).
**pos** = [x, y] from 0 to 1 (centre of the element). Keep the bottom-left corner free for the mascot.

| type | fields | use for |
|---|---|---|
| kinetic | from, to, pos, size(60–130), hl[words], hl2[words], width(0.3–0.9) | the spoken sentence written word by word — the main tool |
| headline | text, at, pos, size, color(accent/accent2) | one key word or 2–4 word punchline |
| card | title, sub, at, pos, size | a name, a tool, a concept |
| stat | fmt ("${:.0f}", "{:,.0f} views"), from, to, label, at | any number |
| checklist | items [[text, TIME], ...], title, pos, width | lists, steps, requirements |
| flow | nodes [[title, sub, TIME], ...], y, width | process A → B → C |
| screenshot | id, src, at, pos, width, maxh, label, crop[x0,y0,x1,y1] | showing a screen |
| callout | on (screenshot id), box [x0,y0,x1,y1 as fractions of that picture], label | pointing at a button the moment it is named |
| logo | src, at, pos, h | a brand/tool the moment it is named |
| step | n, title, at, until | tutorial step header (top corner) |
| progress | label, at, dur | installing / waiting |
| cross | box [x0,y0,x1,y1 screen fractions], at | crossing something out (wrong way, myth) |
| bubble | text, at, until | the mascot says a short joke/aside (max ~8 words) |
Optional on any element: `"sfx": "money" | "big" | "fail" | "success" | "pop"`.
**mascot**: `[{"at": TIME, "do": "show|hop|wiggle|spin|big|dock|hide"}]` — react on punchlines ("big" = takes the stage, then "dock").
**camera**: `[{"at": TIME, "zoom": 1.0–1.5, "x": 0.5, "y": 0.5, "ease": "expo|smooth"}]` — punch in on what is being talked about, then back to 1.0.
**transitions**: list of TIMEs at section changes. **shakes**: big moments only.
**intro_at**: seconds after the hook where the channel intro plays (null = no intro).

## Editing rules (this is what makes it look professional)
- Every visual lands ON its word (use the word, not a guessed second). Elements leave just before the next beat (`until`).
- One idea per beat; max 3–4 elements on screen together. Big and readable: headline ≥ 90, kinetic ≥ 60.
- Show, don't repeat: if the voice names a tool → its logo; a number → stat; steps → checklist/flow; a click → screenshot + callout.
- Hook (first 5 s): the topic + the result on screen immediately, a transition and a shake on the strongest word.
- No screen with only background for more than ~1 s.
- Never add music. Sound effects come automatically from the style.
- Keep "Made with EditDNA" headers and metadata (license: personal use only).
