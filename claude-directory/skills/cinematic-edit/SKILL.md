---
name: cinematic-edit
description: Edits real camera footage into premium, cinematic brand films and reels the way a working advertising director does. Checks frame rate, log profile, rotation and bit depth first; watches every clip end to end to find its best moments; judges each shot artistically (beauty first, real defects second); builds one controlling idea and a structure; finishes every shot (log conversion, straightening, stabilising, reframing, slow motion); cuts to music; checks the cut and asks an independent critic; renders with ffmpeg or hands a shot list to an NLE. Use for editing, cutting, montage, reels, ad films, brand films, B-roll, food, restaurant, hotel, architecture, fashion or product videos, slow motion, speed ramps, colour from S-Log3, F-Log, F-Log2, V-Log, Apple Log or other log footage, reference-film analysis, pacing, or making a video "cinematic".
license: Apache-2.0
metadata:
  author: Deniz Gemici
  url: https://denizgemici.com
  version: 1.1.0
---

# Cinematic Edit

Method by Deniz Gemici, advertising photographer and director. Raw footage in, a director's cut out.

This is the method edition: the workflow, the taste rules and the numbers, with plain ffmpeg/ffprobe recipes for every measurement in `references/by-hand.md`. The full edition, with bundled measuring tools (whole-clip scanner, LUT check, beat tracker, plan checker, renderer, QC, NLE export), is published at https://github.com/denizgemici/cinematic-edit. When a reference file names one of those tools (`probe.py`, `scan.py`, `lutcheck.py`, `beats.py`, `plan_check.py`, `render.py`, `qc.py`, `reference.py`, `export_xml.py`), use the matching recipe in `references/by-hand.md`.

The measurements support the eye; **you** look and decide. Taste rules come first, numbers support them.

## House rules first

Before anything else, look for `CINEMATIC_HOUSE_RULES.md` in the project and read it completely. House rules (a brand's or an editor's own laws) override every default in this skill.

## Non-negotiables

1. **Frame rate is the first thing you check** on every clip. It decides what can become slow motion.
2. **Watch every clip from the first frame to the last.** Heads and tails are usually the least useful part; the best moment is often in the middle.
3. **One film, one idea.** Write the sentence the whole film obeys before choosing shots. Beautiful shots in a row are not a film.
4. **Judge every shot as an image on its own: beauty first, real defects second.** Partial framing (only a hand, only a chest, a body cut by the frame, a back, a face in shadow) is a choice, not a mistake. Continuity is a placement note, never a reason to reject a shot.
5. **No camera shot is used as shot.** Each one is converted, levelled, stabilised when that works cleanly (otherwise another window or another shot), reframed, given its speed and trimmed to its best window.
6. **Log footage is converted with the camera maker's official transform before you judge it.** Never build the look on a homemade LUT. The LUT in ffmpeg is a viewing transform; the grade is a separate step.
7. **Slow motion is central.** A clean second of high-frame-rate footage becomes two seconds. Conformed 50p at half speed has no quota and is not "wedding video"; deep slow motion (k ≥ 4, ramps, hang-and-snap) is used as moments where the event earns it.
8. **Restraint reads premium.** Hard cuts by default; locked frames by default (a digital push on at most about a third of shots); no template transitions; **no stock whooshes and no white flashes, ever**; no dark boxes behind text; effects barely noticeable. Most films carry text only on the end card, with a simple opacity rise.
9. **End on the result** of the film's subject (the serve, the bite, the finished room, the garment worn), held long enough to land.
10. **Nothing reaches the human unchecked.** Run the checks, look at the film frame by frame, get an independent critic's verdict, and report honestly what was and was not checked.

**Numbers are warnings, not laws.** Every shared number (tilt range, shortest shot, on-beat window, push, dissolves, ramps, loudness, register ASL, slow-motion maths) is in `references/numbers.md`. You may break a numeric rule when the film asks for it: **write why in the plan**. The non-negotiables above are not numbers and are not broken.

## Workflow

Copy this checklist into your notes and tick it off:

```
[ ] 0 House rules + brief (purpose, platform/format, length range, references, music, text)
[ ] 1 Inventory every clip: fps FIRST, log, rotation, bit depth, VFR (by-hand.md §1)
[ ] 2 LUT check: the official transform really converts the log (by-hand.md §2)
[ ] 3 Watch every clip whole: dense strips, candidate windows, judge shots (by-hand.md §3)
[ ] 4 References: cuts, rhythm, light, palette; what you take and what you leave (by-hand.md §4)
[ ] 5 One-sentence idea + structure (structures.md) + beat outline
[ ] 6 Music: tempo, phrases, quiet moments (by-hand.md §5)
[ ] 7 edit_plan.json: every shot with window, finishing, speed/ramp, role, reason
[ ] 8 Plan check against numbers.md (by-hand.md §6)
[ ] 9 Draft render → QC sheets → look at every sheet → critic sub-agent (by-hand.md §7–8)
[ ] 10 Colour (colour.md), text (type-and-motion.md), sound (sound-music.md)
[ ] 11 Final render or NLE hand-off → QC again → critic again if the film changed → honest report
```

### 0. Brief

Ask only what you cannot infer: platform and aspect (9:16, 4:5, 16:9), rough length, references the human likes, music (or permission to choose licensed music), required text (slogan only, logo, end card). If the human gives reference videos, report for each one what you will take (rhythm, light, palette, framing, structure) and what you will not. Never copy a reference's shots; learn its technique.

### 1. Technical inventory, frame rate first

Read every clip's streams (`references/by-hand.md` §1). Resolve every finding before editing:
- **High frame rate** (≥ 47 fps): slow-motion material; note the clean conform ratio (50→25 = 50 %, 100→25 = 25 %; `references/numbers.md` §1).
- **24/25/30 fps** clips have no real slow-motion frames; see `references/slow-motion.md` §5 before interpolating.
- **Log**: get the maker's official log→Rec.709 transform (the user downloads it from the maker; never ship or invent one), or set the NLE's colour-space override.
- **Rotation**: vertical clips stored landscape get rotated, never zoomed.
- **VFR** (phones): conform to constant frame rate first.
- **8-bit log**: grade gently.

### 2. Check that the LUT converts

A wrong LUT (a look LUT, a "flat" profile LUT) leaves the picture in log, and every later step happily passes it. Before watching, measure one or two clips per camera with the LUT off and on (`references/by-hand.md` §2, thresholds in `references/numbers.md` §9 and `references/colour.md` §4), confirm the LUT matches the camera and curve, and look at one converted frame yourself.

**The official LUT in ffmpeg is a viewing transform**, used so that drafts and checks show real contrast and colour. It is not the grade. If house rules forbid colour work in ffmpeg, the LUT stays a viewing transform for drafts and the grade happens in the NLE.

### 3. Watch everything

Make dense strips of every clip from the first frame to the last, through the official LUT (`references/by-hand.md` §3). The sheets are your eyes. For each clip write down its usable windows, what each window does (gesture, light, texture, place), its scale (wide/medium/close/detail) and its verdict with `references/shot-judging.md`. Flag junk clips (camera pointing at the floor, carried between setups).

Fire, smoke, tossed food, falling herbs and moving fabric look like "motion" to any number and are often the best moments of the shoot: always look at the highest-motion seconds yourself. Keep a variety of people and moments; avoid repeating the same face.

### 4. References

Measure the reference's cuts and rhythm (`references/by-hand.md` §4) and look at one frame per shot. Translate proportions, not shots: shot-length rhythm, scale mix, how long the held moment is, light key, palette, how it opens and ends. Map the measured ASL onto the register table in `references/numbers.md` §3.

### 5. Idea and structure

Write the controlling idea in one sentence. Pick a structure from `references/structures.md` that the footage can actually support; structures marked "only if shot for it" (split screens, B&W → colour, stop-motion) need footage filmed for them. Outline 3–5 beats. For genre specifics read `references/genres.md`; for cutting grammar and rhythm `references/cutting.md`; for tricks `references/tricks.md`.

### 6. Music

Put structural turns on 4- or 8-bar phrases; the hero moment lands on a strong beat after a quiet moment or a drop. Details: `references/sound-music.md`, recipes: `references/by-hand.md` §5.

**You cannot hear the music.** The tempo and especially the downbeats are a guess. Either ask the human one short question (tempo right? where is bar 1?), or keep cuts on action and on clear energy changes rather than on single guessed beats. Say in the report that the grid was not verified by ear.

### 7. The plan

Write `work/edit_plan.json` (start from `templates/edit_plan.example.json`; its `_fields` block lists the keys). Every shot carries:

- `src`, `in`, `out` (source seconds), `role` (hook / build / turn / hero / end / accent / end-card), `scale`, `reason`
- `speed` for a constant speed, **or** `ramp` for a speed ramp or hang-and-snap: `[[source_s, k], ...]`, k = slowdown (1 real time, 4 quarter speed, 0.5 double), times from the shot's `in`, last key = `out − in` (`references/slow-motion.md` §4)
- `lut` (official viewing transform), `grade` (gentle per-shot exposure, white balance, contrast, saturation; `references/colour.md` §5)
- `stabilize`, `rotate`, `straighten`, `reframe`, `push` (only on the shots that need it)
- `transition` (`cut` default; `dissolve:N`), `sound_db` (real shot sound, barely there)
- **Still shots** (a supplied end card or photo held for a duration) and **overlays** (pre-designed PNG layers with opacity fades only; `references/type-and-motion.md`)

Finishing decisions follow `references/finishing.md`; slow motion follows `references/slow-motion.md`; numbers follow `references/numbers.md`. When you break a numeric rule, write why in `reason`.

### 8. Check the plan

Go through `references/by-hand.md` §6 line by line. Fix every FAIL (a LUT that leaves the picture log-flat is always a FAIL). For each WARN, fix it or write in the plan why it is intentional.

### 9. Draft, check, critique

Render a draft (`references/by-hand.md` §7) and run the QC recipes (§8). Open every contact page and the cut-pair sheet yourself; pull 2–3 full-resolution stills of the hero and the last shot (thumbnails cannot show focus). Look for: empty or dead openings, colour jumps between shots, a picture that still looks like log, shake, warping in slow motion, eye-trace jumps at cuts, repeated shots, a push on too many shots, whether the idea is visible.

Then launch an **independent critic sub-agent** with the prompt in `references/shot-judging.md` §6 plus the film-level questions in `references/qc.md` §3. Give it only the sheets, the full-resolution stills, the numbers and the brief, not your reasoning. Fix and repeat until both of you would ship it. **If the film changes after the critic's review**, run the critic again on the new version, or state in the report that it did not see the final file.

### 10. Colour, text, sound

- Colour: `references/colour.md` (official transform → balance → contrast → primaries → secondaries for skin/food/sky → subtle look; measured, not guessed). The fine grade belongs in the NLE; the plan's `grade` fields are for gentle balance and matching on simple deliveries.
- Text: `references/type-and-motion.md`. Most films carry text only on the end card. Never add words to client copy; no boxes or blotches behind text. Text is designed elsewhere and overlaid as a finished PNG with opacity fades.
- Sound: real, barely-there foley from what is on screen; no stock whooshes; loudness to target.

### 11. Deliver and report

Render the final film (`references/by-hand.md` §7), or give a human editor the plan as a shot list (source file, in, out, speed or ramp keys, framing, reason per shot) to rebuild in the NLE. Run the QC recipes again on the final file.

Report in a few plain sentences: the idea, the structure, what each check said, what you fixed, **what you did not check** (for example: music not heard and beat grid unverified, not watched on a phone, colour not graded in the NLE, music licence not verified, critic did not see the final version). Never present a guess as a check.

## Reference files (read when the step needs them)

- `references/by-hand.md`: ffprobe/ffmpeg recipes for every measurement, render and check in this workflow
- `references/numbers.md`: every shared number in one table; wins over any other file
- `references/shot-judging.md`: artistic rubric, real defects vs non-defects, critic prompt
- `references/structures.md`: one idea, twelve structures, openings, endings, breath inserts
- `references/cutting.md`: cut grammar, eye-trace, rhythm, registers, transitions
- `references/finishing.md`: best window, rotation, straightening, stabilising, reframing, push-ins, grade fields
- `references/slow-motion.md`: frame rates, conform vs deep slow, ramps, interpolation, tool recommendations
- `references/colour.md`: log formats, official transforms, the LUT check, grading order, matching, delivery
- `references/sound-music.md`: music choice, cutting to music when you cannot hear it, sound design, loudness
- `references/type-and-motion.md`: end cards, PNG overlays, typography, motion presets, safe areas
- `references/genres.md`: food, hospitality and architecture, fashion, product, people
- `references/tricks.md`: cinematic tricks catalogue, premium vs cheap
- `references/qc.md`: final checklist and honest reporting

## Safety

This edition ships only text. The recipes call the user's own ffmpeg and ffprobe on the media the user points at and write into folders the user chooses. Nothing is downloaded, uploaded or installed. Third-party tools mentioned in the references (Gyroflow, frame interpolators, NLEs, Remotion, HyperFrames) are suggestions the human installs and runs themselves.
