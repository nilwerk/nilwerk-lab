# Video: "One real bug. Two stubborn engineers." (25 s, 9:16)

Status: **first rough cut exists** (`video/rough-cut_the-guard-that-could-never-fire.mp4`, 25.2 s, 1080x1920, H.264 + AAC) with synthesised music and effects and burned-in captions. **No voice-over**: this environment has no text-to-speech engine (checked: no espeak, pico, flite, pyttsx3, piper) and nothing may be uploaded to an outside service without approval. Rebuild: `/usr/bin/python3 build_video.py` (frames by headless Chrome, sound by numpy, cut by ffmpeg; offline). I verified the file with ffprobe (25.2 s, h264 + aac, peak -3 dB, mean -22 dB) and looked at the frames; **I cannot listen to audio here**, so the sound mix is unchecked by ear.

Fiction/fact: the dialogue is imagined (dashed bubbles); the green boxes are real (claim-check F1-F6). Voice-over must say the closing line "Fictional crew life. Real engineering. AI crew, led and reviewed by humans."

## Storyboard and timing (as built)

| Scene | Time | Picture | On-screen caption | Voice-over (to record) | Sound |
|---|---|---|---|---|---|
| 1 hook | 0.0-3.5 | Big headline "One real bug. Two stubborn engineers." Ines avatar + dashed bubble "Show me the log." | "Tuesday 17 November 2026. The crew are AI agents; their drama is made up." | "One real bug. Two stubborn engineers." | question sting (two square-wave notes) at 0.05 s |
| 2 setup | 3.5-8.0 | Mira avatar + bubble ("I built a guard for stubborn batches. I am extremely proud of it."); green box "BY DESIGN (FIRMWARE SETTING): Every 15 min, the sensor is designed to store a new sample. Not yet observed on a device." | "Mira's guard counted the newest sample. Spot the problem?" | "Her guard counts the newest sample. By design, the sensor stores a new one every fifteen minutes." | whoosh at 3.5; four clock ticks at 5.7, 6.2, 6.7, 7.2 |
| 3 proof | 8.0-12.7 | Ines bubble "Let us make the server say no. A lot. Watch the buffer." (no number inside the bubble); green panel header "QA'S REPRODUCTION (6 REJECTS IN A ROW)"; counter 4, 5, 6 ... 10 samples waiting with growing squares; "guard fired: NO" | "Every retry, a new sample arrives." then "The counter resets. The guard never fires." | "QA checks: six rejects, ten samples waiting. The guard never fires." | whoosh at 8.0; rising blips at 9.0 to 11.5; low buzzer at 11.6 |
| 4 fix | 12.7-16.7 | Mira bubble "...Fine. You were right. I am fixing it." + green box "3rd reject = batch dropped", text "Fix: count from the oldest sample. QA re-ran the same case..." | "Fixed the same morning. Re-checked by QA." | "Fix: count from the oldest. Fixed that morning, re-checked by QA." | whoosh at 12.7; success ding at 15.1 |
| 5 numbers | 16.7-20.7 | Chip "MEASURED, 17 NOV 2026 · HOST TESTS ON A PC"; tiles 622 checks, 49/49 deliberate bugs caught (was 45); orange box "Not run on a real device yet. No Wi-Fi code exists yet." | "Real engineering underneath the fun." | "Six hundred twenty-two checks pass. Forty-nine of forty-nine bugs caught." | ta-da arpeggio at 16.7 |
| 6 end | 20.7-25.2 | nilwerk mark + wordmark; "Fictional crew life. Real engineering."; "AI crew, led and reviewed by humans. The characters' private lives are made up."; @nilwerk · nilwerk.de | none | "Fictional crew life. Real engineering. AI crew, led and reviewed by humans." | end chime at 20.7, music fades out in the last second |

Music bed: an original 8-step arpeggio (C, G, Am, F) at 104 bpm, triangle lead with a quiet square bass, generated in code: no licensing question. Text stays inside the Instagram safe zone (about 150 px top and 300 px bottom reserved).

## Voice-over options (Needs Arsany)
1. A human voice recorded by Arsany or another person with their OK (best, no AI flag). 2. A text-to-speech voice inside CapCut or Canva: allowed only after Arsany's OK; then switch on Instagram's AI flag and add "AI-generated voice" to the caption. Never clone a real person's voice. Total voice-over is about 55 words, speaking pace about 2.3 words/s: record the scenes separately and trim to the timings above.

## Canva / CapCut brief (if Arsany wants to polish)
- Canvas 1080x1920, 30 fps, 25 s. Import `video/frames/*.png` as scenes (durations in `video/frames.txt`; counter frames f3a, f3_5 to f3_10 are 0.5 s each) or rebuild from the brand templates. Fonts: Space Grotesk, Inter, JetBrains Mono (the PNGs fell back to Inter and DejaVu Sans Mono because Space Grotesk and JetBrains Mono are not installed in this build environment; Canva has the real ones).
- Replace the cuts by 0.15 s slides or pops; keep the dashed/solid visual grammar and both fiction/real chips on screen at all times.
- Audio: `video/soundtrack.wav` (synthesised, free to use) or CapCut library music marked commercial-use; no copyrighted songs. Duck the music 8 dB under the voice-over.
- Captions: keep burned-in captions for sound-off viewers (accessibility); add the voice-over as a separate track.
- Export MP4 H.264, 1080x1920, under 100 MB. Upload to Instagram only via Arsany (Reel draft; set the AI flag only if an AI voice or AI imagery is used).
- Canva: connector tools exist in this environment, but I did not create a Canva design: it would mean sending our texts and avatars to an outside service, which is not approved for this task. Say the word and I will create a DRAFT design there (never published from Canva).

## Longer idea (not built): 45 s "Five episodes in 45 seconds"
Eight-second beat per episode (the five hero images with a title card each), same music bed, one shared end card. Only after the first Reel shows whether the format works (Arsany's call).
