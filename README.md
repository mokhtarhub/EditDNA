# EditDNA 🧬
**Turn your channel into its own editing style — then edit every video in that style with one sentence.**

EditDNA is a skill for AI agents (Claude, Claude Code, OpenCode). It interviews you about your channel, studies screenshots of
editing styles you love, designs *your* motion-graphics style (colours, fonts, shapes, motion, sound, logo, mascot), shows you a
preview, and then builds a second skill — `<your-channel>-editdna` — that edits your videos in that style from a voice-over.

## What you need
- Python 3.10+ and ffmpeg
- An AI agent that can run commands: Claude app (paid) · Claude Code · OpenCode (free models available)

## Quick start
1. Open the [latest release](https://github.com/mokhtarhub/EditDNA/releases/latest), download **Source code (zip)** and unzip it.
   Claude app users: upload **EditDNA-builder-v1.0.zip** from the same page as a skill.
2. Give your agent the `editdna-builder` folder as a skill, then say:
   **"Use the editdna-builder skill to build my channel's editing style."**
3. Answer its questions, send your screenshots and logo, approve the preview.
4. From then on: **"Use the &lt;channel&gt;-editdna skill to edit this video: voice-over vo.wav, screenshots in shots/."**

## License
Free for personal use only — see [LICENSE](LICENSE). Every video made with EditDNA carries a "Made with EditDNA" metadata stamp.
