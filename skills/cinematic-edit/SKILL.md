---
name: cinematic-edit
description: Edits real camera footage into premium, cinematic brand films and reels the way a working advertising director does. Checks frame rate, log profile, rotation and bit depth first; watches every clip end to end to find its best moments; judges each shot artistically (beauty first, real defects second); builds one controlling idea and a structure; finishes every shot (log conversion, straightening, stabilising, reframing, slow motion); cuts to music; checks the cut with numbers and an independent critic; renders with ffmpeg or exports a Premiere/Resolve timeline. Use for editing, cutting, montage, reels, ad films, brand films, B-roll, food, restaurant, hotel, architecture, fashion or product videos, slow motion, speed ramps, colour from S-Log3, F-Log, F-Log2, V-Log, Apple Log or other log footage, reference-film analysis, pacing, or making a video "cinematic".
license: Apache-2.0
metadata:
  author: Deniz Gemici
  url: https://denizgemici.com
  version: 1.1.1
---

# Cinematic Edit

Method by Deniz Gemici, advertising photographer and director. Raw footage in, a director's cut out.

This skill is a workflow plus local tools. The tools measure; **you** look and decide. Taste rules come first, numbers support them.

## House rules first

Before anything else, look for a house-rules file and read it completely:
`./CINEMATIC_HOUSE_RULES.md` in the project, then `~/.cinematic-edit/house-rules.md`.
House rules (a brand's or an editor's own laws) override every default in this skill.

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
10. **Nothing reaches the human unchecked.** Run the numeric checks, look at the film frame by frame, get an independent critic's verdict, and report honestly what was and was not checked.

**Numbers are warnings, not laws.** Every shared number (tilt range, shortest shot, on-beat window, push, dissolves, ramps, loudness, register ASL, slow-motion maths) is in `references/numbers.md`. You may break a numeric rule when the film asks for it: **write why in the plan**. The non-negotiables above are not numbers and are not broken.

## Tools (all local: Python 3.9+, numpy, Pillow, the user's ffmpeg/ffprobe; no network)

| Script | What it does |
|---|---|
| `scripts/probe.py` | Camera, fps (and VFR), bit depth, chroma, rotation, colour tags, log/HDR profile (Sony XML gamma, Fujifilm maker note), warnings |
| `scripts/scan.py` | Whole-clip scan → candidate windows with slow-motion advice; writes an **index sheet** for the folder, **paged dense strips** per clip and a **start / peak / end triptych** per window |
| `scripts/reference.py` | Deconstructs a reference film: cuts, ASL/median/CV, rhythm curve, light, palette → `style_card.json`, `shots.png`, `rhythm.png` |
| `scripts/beats.py` | Music → beats, bar/phrase grid, energy per frame, quiet moments; writes the WAV to use in the edit |
| `scripts/plan_check.py` | Checks `edit_plan.json` before rendering: idea, rhythm vs register, repeats, pixel budget, slow-motion ratios, rotation, beat timing, and the LUT check |
| `scripts/render.py` | Finishes every shot and renders the film: LUT, two-pass vid.stab stabilisation (skipped with a warning when ffmpeg lacks it), gentle grade, speed and ramps, straighten, reframe, push, dissolves, still-image shots, PNG overlays with opacity fades, music, two-pass loudness, BT.709 tags; `--draft` for quick checks |
| `scripts/qc.py` | Checks the render: contact pages, cut-pair sheet, black/frozen/duplicated frames, jumps, loudness, tags |
| `scripts/export_xml.py` | Timeline for Premiere Pro / DaVinci Resolve (FCP7 XML) linking the original clips, with a marker per shot. Experimental: not yet import-tested in Premiere Pro / DaVinci Resolve |
| `scripts/lutcheck.py` | Checks that a LUT really converts a log clip (range and chroma with the LUT off and on) |
| `scripts/selftest.py` | Offline end-to-end test of every script (about 15 s); run it after installing |

If ffmpeg is not on PATH, set `CE_FFMPEG` and `CE_FFPROBE`. Run each script with `--help` for options. Scanning takes about 2 s per short clip with a LUT, so a large folder takes minutes: run it in the background and keep working on the brief.

## Workflow

Copy this checklist into your notes and tick it off:

```
[ ] 0 House rules + brief (purpose, platform/format, length range, references, music, text)
[ ] 1 probe.py on all clips: fps FIRST, log, rotation, bit depth, VFR
[ ] 2 LUT check: the official transform really converts the log
[ ] 3 scan.py on all clips (whole length) + LOOK: index, strips, triptychs; judge shots
[ ] 4 reference.py on each reference; write what you take from it and what you leave
[ ] 5 One-sentence idea + structure (structures.md) + beat outline
[ ] 6 beats.py on the music; structure on phrases (or on action if nobody can listen)
[ ] 7 edit_plan.json: every shot with window, finishing, speed/ramp, role, reason
[ ] 8 plan_check.py → fix FAILs, justify or fix WARNs
[ ] 9 render.py --draft → qc.py → look at every sheet → critic sub-agent
[ ] 10 Colour (colour.md), text (type-and-motion.md), sound (sound-music.md)
[ ] 11 Final render or export_xml.py → qc.py again → critic again if the film changed → honest report
```

### 0. Brief

Ask only what you cannot infer: platform and aspect (9:16, 4:5, 16:9), rough length, references the human likes, music (or permission to choose licensed music), required text (slogan only, logo, end card). If the human gives reference videos, report for each one what you will take (rhythm, light, palette, framing, structure) and what you will not. Never copy a reference's shots; learn its technique.

### 1. Technical inventory, frame rate first

`python3 scripts/probe.py FOOTAGE_DIR --json work/probe.json --looks`

Resolve every warning before editing:
- **High frame rate** (≥ 47 fps): slow-motion material; note the clean conform ratio (50→25 = 50 %, 100→25 = 25 %; `references/numbers.md` §1).
- **24/25/30 fps** clips have no real slow-motion frames; see `references/slow-motion.md` §5 before interpolating.
- **Log** detected: get the maker's official log→Rec.709 transform (the user downloads it from the maker; never ship or invent one) and pass it as `--lut` / `"lut"`, or set the NLE's colour-space override.
- **Rotation**: vertical clips stored landscape get rotated, never zoomed.
- **VFR** (phones): conform to constant frame rate first.
- **8-bit log**: grade gently.

### 2. Check that the LUT converts

A wrong LUT (a look LUT, a "flat" profile LUT) leaves the picture in log, and every later tool happily passes it. Before scanning, run the LUT check on one or two clips per camera:

`python3 scripts/lutcheck.py CLIP_A CLIP_B --lut OFFICIAL.cube`

It measures p2/p50/p98 and chroma with the LUT off and on, and **FAILs** a LUT that leaves log flat (`plan_check.py` runs the same check per shot). It only catches a LUT that does not convert: another camera's log LUT usually passes, so confirm yourself that the LUT matches the camera and curve `probe.py` reported. Also look at one converted frame yourself. Thresholds: `references/numbers.md` §9 and `references/colour.md` §4.

**The official LUT in ffmpeg is a viewing transform**, used so that drafts, scans and checks show real contrast and colour. It is not the grade. If house rules forbid colour work in ffmpeg, the LUT stays a viewing transform for drafts and the grade happens in the NLE.

### 3. Watch everything

`python3 scripts/scan.py FOOTAGE_DIR --out work/analysis --lut OFFICIAL.cube --timeline-fps 25`

The sheets are your eyes; the numbers are not. Open the **index sheet** first (one image for the whole folder), then each clip's **paged strips** (dense frames across the whole clip), then the **triptych** (start / peak / end, large) of every candidate window you might use. For each clip write down its usable windows, what each window does (gesture, light, texture, place), its scale (wide/medium/close/detail) and its verdict with `references/shot-judging.md`. Flag junk clips (camera pointing at the floor, carried between setups).

The windows are **candidates**, not answers. The score rewards still, sharp frames; fire, smoke, tossed food, falling herbs and moving fabric register as "shake" and often score low while being the best moments of the shoot. Always look at the highest-motion seconds of each clip yourself. Keep a variety of people and moments; avoid repeating the same face.

### 4. References

`python3 scripts/reference.py REF.mp4 --out work/ref1`

Read `style_card.json` and look at `shots.png`. Translate proportions, not shots: shot-length rhythm, scale mix, how long the held moment is, light key, palette, how it opens and ends. Map the measured ASL onto the register table in `references/numbers.md` §3.

### 5. Idea and structure

Write the controlling idea in one sentence. Pick a structure from `references/structures.md` that the footage can actually support; structures marked "only if shot for it" (split screens, B&W → colour, stop-motion) need footage filmed for them. Outline 3–5 beats. For genre specifics read `references/genres.md`; for cutting grammar and rhythm `references/cutting.md`; for tricks `references/tricks.md`.

### 6. Music

`python3 scripts/beats.py TRACK --fps 25 --out work/music`

Put structural turns on 4- or 8-bar phrases; the hero moment lands on a strong beat after a quiet moment or a drop. Use `work/music/music.wav` in the edit. Details: `references/sound-music.md`.

**You cannot hear the music.** The tempo and especially the downbeats are a guess. Either ask the human one short question (tempo right? where is bar 1?) and pass `--bpm` / `--first-downbeat`, or keep cuts on action and on clear energy changes rather than on single guessed beats. Say in the report that the grid was not verified by ear.

### 7. The plan

Write `work/edit_plan.json` (start from `templates/edit_plan.example.json`; its `_fields` block and `render.py --help` list the exact keys). Every shot can carry:

- `src`, `in`, `out` (source seconds), `role` (hook / build / turn / hero / end / accent / end-card), `scale`, `reason`
- `speed` (+ `interpolate`, `optical_flow_ok`) for a constant speed, **or** `ramp` for a speed ramp or hang-and-snap: `[[source_s, k], ...]`, k = slowdown (1 real time, 4 quarter speed, 0.5 double), times from the shot's `in`, last key = `out − in` (`references/slow-motion.md` §4)
- `lut` (official viewing transform), `grade` (gentle per-shot exposure, white balance, contrast, saturation; `references/colour.md` §5)
- `stabilize` (two-pass vid.stab; skipped with a warning when ffmpeg lacks it; only if the result is clean), `rotate`, `straighten`, `reframe`, `push` (only on the shots that need it)
- `transition` (`cut` default; `dissolve:N`), `sound_db` (real shot sound, barely there)
- **Still shots**: a shot can be a still image (a supplied end card or photo) held for a duration
- **Overlays** (plan level): pre-designed PNG layers (end card, logo, slogan) with start/end times and opacity fades only; designed elsewhere (`references/type-and-motion.md`)

Finishing decisions follow `references/finishing.md`; slow motion follows `references/slow-motion.md`; numbers follow `references/numbers.md`. When you break a numeric rule, write why in `reason`.

### 8. Check the plan

`python3 scripts/plan_check.py work/edit_plan.json`

Fix every FAIL (a FAIL on the LUT check means the film would still be log: fix the LUT). For each WARN, fix it or write in the plan why it is intentional.

### 9. Draft, check, critique

```
python3 scripts/render.py work/edit_plan.json --out work/draft.mp4 --draft
python3 scripts/qc.py work/draft.mp4 --out work/qc --plan work/edit_plan.json --every 4
```

Open every contact page and the cut-pair sheet yourself; pull 2–3 full-resolution stills of the hero and the last shot (thumbnails cannot show focus). Look for: empty or dead openings, colour jumps between shots, a picture that still looks like log, shake, warping in slow motion, eye-trace jumps at cuts, repeated shots, a push on too many shots, whether the idea is visible.

Then launch an **independent critic sub-agent** with the prompt in `references/shot-judging.md` §6 plus the film-level questions in `references/qc.md` §3. Give it only the sheets, the full-resolution stills, the numbers and the brief, not your reasoning. Fix and repeat until both of you would ship it. **If the film changes after the critic's review** (shots swapped, trimmed, retimed, regraded), run the critic again on the new version, or state in the report that it did not see the final file.

### 10. Colour, text, sound

- Colour: `references/colour.md` (official transform → balance → contrast → primaries → secondaries for skin/food/sky → subtle look; measured, not guessed). The fine grade belongs in the NLE (export the timeline); the plan's `grade` fields are for gentle balance and matching on simple deliveries.
- Text: `references/type-and-motion.md`. Most films carry text only on the end card. Never add words to client copy; no boxes or blotches behind text. `render.py` only overlays finished PNG layers with opacity fades.
- Sound: real, barely-there foley from what is on screen; no stock whooshes; loudness to target.

### 11. Deliver and report

`python3 scripts/render.py work/edit_plan.json --out FINAL.mp4 [--hevc10]` or `python3 scripts/export_xml.py work/edit_plan.json --out timeline.xml` for a human editor (experimental; check the imported timeline against the render: speeds, framing and dissolves may need fixing in the NLE). Run `qc.py` again on the final file.

Report in a few plain sentences: the idea, the structure, what each check said, what you fixed, **what you did not check** (for example: music not heard and beat grid unverified, not watched on a phone, colour not graded in the NLE, music licence not verified, critic did not see the final version). Never present a guess as a check.

## Reference files (read when the step needs them)

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

The scripts only read the media you point them at and write into the output folders you choose. They never download, upload, call an API, install anything or run shell strings. Third-party tools mentioned in the references (Gyroflow, frame interpolators, NLEs, Remotion, HyperFrames) are suggestions the human installs and runs themselves.
