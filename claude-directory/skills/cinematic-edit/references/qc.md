# Final check and honest report

Contents: 1 Numeric gates · 2 Watch it yourself · 3 Film-level critic questions · 4 Delivery specs · 5 The report

## 1. Numeric gates (scripts)

- `plan_check.py`: no FAIL; every WARN fixed or justified in the plan.
- `qc.py` on the render: no FAIL (black frames, flash frames, true peak above −1 dBTP); WARNs explained (frozen holds are fine only if intended; duplicated frames inside moving shots mean a bad slow-motion conform; picture jumps inside a shot mean a flash frame or interpolation tear).
- The LUT check: no shot still measures log-flat after its LUT (`numbers.md` §9). A film that passes every other check but still looks like log is a FAIL.
- Colour tags BT.709 on all three (primaries, transfer, matrix); confirm with `ffprobe` if a tool does not print them.
- Loudness within ±1 LU of the target; true peak ≤ −1 dBTP (`numbers.md` §7).
- Picture duration matches the plan and the audio within one frame.

## 2. Watch it yourself, frame by frame

Open the contact pages (every 4–6 frames) and the cut-pair sheet. Long films are split into pages: open every page; a thumbnail that is too small to judge focus is not a check. Pull 2–3 full-resolution stills of the hero and the last shot. Look for:
- a dead or empty first second; a weak frame 0
- colour or exposure jumps between neighbouring shots of the same place
- shake, jello, warping or ghosting, especially in slow motion (hands, liquids, glass, hair)
- eye-trace jumps at fast cuts (the subject leaps across the frame)
- smeared borders, black corners after straightening, soft upscaled shots
- crew, gear, reflections, test people
- the same shot or moment twice; the same face too often
- text that moves while it should be read, text over faces or the product, text in UI zones
- whether the one idea is actually visible, and whether the ending is the result

Then watch the whole film once with sound and once without. Picture alone must tell the story; sound alone must carry the rhythm. If possible, watch it on a phone.

## 3. Film-level critic questions (add to the critic sub-agent prompt)

1. In one sentence, what is this film's idea? (If the critic cannot say it, the idea is not visible.)
2. Is frame 0 strong? Is the subject clear within 2–5 s?
3. Does the rhythm vary (held moments vs compressed ones), or is it monotonous?
4. Does it end on the result, held long enough?
5. Which shot would you remove first, and why? (Remove-a-shot test.)
6. Any cheap or template-looking move (transition, push on too many shots, text animation, flash, whoosh)?
7. Does any part look AI-made (plastic textures, morphing, fake smoke, over-polished colour)?
8. Score the film 1–10 on: idea, rhythm, image quality, colour, sound, ending. Anything below 7 is fixed before delivery.
The critic judges shots by beauty first (`shot-judging.md`); its approval is evidence, not proof. If the film changes after the critic's review, run it again or report that the critic did not see the final version.

## 4. Delivery specs

| Target | Video | Audio |
|---|---|---|
| Instagram / TikTok / Shorts | 1080×1920, 25 or 30 fps (match the timeline), H.264 High or 10-bit HEVC, BT.709 tagged | AAC 48 kHz, about −14 LUFS, ≤ −1 dBTP |
| 4:5 feed | 1080×1350 | same |
| Web / YouTube 16:9 | 1920×1080 or 3840×2160 | same |
| Broadcast | per the channel's spec (EBU R128 −23 LUFS in Europe) | never send the social master to TV |

## 5. The report

Short, plain sentences. State: the idea; the structure; what each check said; what you changed after the checks; and **what you did not check** (phone viewing, NLE grading, music licence, client approval of text; that you could not hear the music and the beat grid is unverified; whether the critic saw the final file). Never call something verified that you only assumed. If a shot is borderline, say so and let the human decide.
