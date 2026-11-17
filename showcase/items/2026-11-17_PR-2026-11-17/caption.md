# PR-2026-11-17: "The crew has a life", a fun content series built on five real events of 17 Nov

**What it shows:** a draft content pack where the AI agents are characters with a clearly marked made-up life (dashed orange: rivalries, a slow-burn, hobbies, crew chat) around real engineering from one day (solid green boxes with sources): a safety guard that could never fire, a feature merged into the wrong branch, a prototype that would sleep before reading a sensor, 8 of 23 QA tricks that beat a safety filter, and an honest list of what does not work yet. Ten images (1080x1350, 1080x1920, 1200x627) and a 25 s vertical rough-cut video with synthesised sound (no voice-over yet).

- Where: `showcase/content/2026-11-17/` (`episodes.md`, `posts.md`, `video-script.md`, `claim-check.md`, `images/`, `video/`, `build_pack.py`, `build_video.py`)
- Persona: Poppy (PR & Social) · Owner direction: Arsany, 17 Nov 2026 · Drafts only, nothing published or scheduled.
- Checks run: both build scripts run offline (headless Chrome, numpy, ffmpeg); every PNG opened and read after layout fixes; `showcase/brand/check_contrast.py` and `check_svg_wellformed.py` pass (118 SVGs, 0 not well-formed); `ffprobe` on the MP4: 25.2 s, h264 + aac, 1080x1920; audio peak -3.0 dB, mean -22.4 dB.
- Unverified: the sound was never heard (no audio output here); German texts unchecked by a native speaker; the care-tip approval by the owner is second-hand (Theo's review); fonts Space Grotesk and JetBrains Mono were not installed, so renders use Inter and DejaVu Sans Mono.
