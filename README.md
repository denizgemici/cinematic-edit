# Cinematic Edit

**Edit like an ad director, not a template.**
Raw footage in. A director's cut out. For Claude Code and any agent that reads skills.

By **Deniz Gemici**, advertising photographer and director (Ankara) · [denizgemici.com](https://denizgemici.com)

---

Most AI edits look the same: random cuts on every beat, template transitions, teal-orange LUTs, punch-in zooms, captions everywhere, tilted horizons, shaky clips, the crew in the background. This skill gives your agent the method a working advertising director uses on real client films for restaurants, hotels and brands, plus local tools that **measure** what a human editor checks by eye.

## What it does

1. **Frame rate first.** Every clip is classified: real high-frame-rate slow motion, in-camera slow motion, or normal speed (and what that means for slow motion).
2. **Watches every clip end to end.** Heads and tails are usually useless; the scan proposes candidate windows in the middle of each take and writes an index sheet, dense paged strips and a start/peak/end triptych per window, so the agent looks at the footage instead of trusting a score.
3. **Judges shots like a cinematographer.** Beauty first, real defects second. A shot of only a hand, a body cut by the frame, a face in shadow is a choice, not an error. Continuity never kills a beautiful shot.
4. **One idea per film.** Twelve proven structures for 10–60 s brand films, openings and endings that land.
5. **Finishes every shot.** Official log conversion (with a check that the LUT really converts), rotation of vertical clips, straightening, basic stabilisation, a basic gentle grade, reframing within a pixel budget, eased push-ins used sparingly.
6. **Slow motion at the centre.** Exact conform ratios, smooth speed ramps and "hang-and-snap" moments from one formula, honest interpolation advice for 25 fps footage.
7. **Cuts to music.** Beat and phrase grid in frames, energy curve, quiet moments.
8. **Checks before anyone sees it.** Plan check (rhythm, repeats, upscaling, slow-motion ratios, log left flat by a wrong LUT), render QC (black and flash frames, judder, tears, loudness, colour tags), contact and cut-pair sheets, an independent critic prompt.
9. **Hands off to humans.** Renders with ffmpeg (finished PNG end cards and logos are overlaid with simple opacity fades), or exports a Premiere Pro / DaVinci Resolve timeline linked to the original camera files, with the reason for every shot in a marker (experimental: not yet import-tested in Premiere Pro / DaVinci Resolve).

## Install

```bash
npx skills add denizgemici/cinematic-edit
```

Claude Code plugin:

```
/plugin marketplace add denizgemici/cinematic-edit
/plugin install cinematic-edit@denizgemici
```

Manual: copy `skills/cinematic-edit` into `~/.claude/skills/`.

Requirements: Python 3.9+ with `numpy` and `Pillow`, and `ffmpeg`/`ffprobe` on your PATH (or set `CE_FFMPEG` / `CE_FFPROBE`). Nothing else.

## Quick start

```bash
S=skills/cinematic-edit/scripts
python3 $S/probe.py footage --json work/probe.json --looks
python3 $S/scan.py footage --out work/analysis --lut OFFICIAL_LOG_TO_709.cube --timeline-fps 25
python3 $S/beats.py track.mp3 --fps 25 --out work/music
python3 $S/plan_check.py work/edit_plan.json
python3 $S/render.py work/edit_plan.json --out work/draft.mp4 --draft
python3 $S/qc.py work/draft.mp4 --out work/qc --plan work/edit_plan.json --every 4
```

Write `work/edit_plan.json` between the beats and the plan check, starting from `skills/cinematic-edit/templates/edit_plan.example.json`. The official LUT comes from your camera maker's website.

## Use

Just ask your agent:

> Edit these clips into a 15-second vertical reel for the restaurant. Footage is in `./footage`, the music is `track.mp3`, and here is a reference I like.

The agent follows the workflow in `SKILL.md`: probe → scan → look → idea → plan → check → draft → critique → deliver.

## Tools

| Script | Purpose |
|---|---|
| `probe.py` | Camera, frame-rate class, log profile (Sony XML, Fujifilm maker note), bit depth, rotation, warnings |
| `scan.py` | Whole-clip analysis, candidate windows with slow-motion advice, index sheet, paged strips, per-window triptychs |
| `reference.py` | Reference film → style card (shot rhythm, light, palette) and one frame per shot |
| `beats.py` | Music → beats, bars, phrases, energy per frame |
| `plan_check.py` | Edit plan checks before rendering, including whether the LUT really converts the log |
| `render.py` | Finishes every shot (LUT, basic stabilisation, basic grade, speed and ramps, straighten, reframe, push, still shots, PNG overlays) and renders the film |
| `qc.py` | Checks the render and makes contact/cut sheets |
| `export_xml.py` | Premiere / Resolve timeline (experimental: not yet import-tested) |
| `lutcheck.py` | Checks that a LUT really converts a log clip |
| `selftest.py` | Offline end-to-end test of every script (about 15 s) |

## Tested on

- Sony FX3, S-Log3 / S-Gamut3.Cine, 4K 50p
- Fujifilm X-S20, F-Log2, 8-bit 4:2:0, 50p, vertical clips stored landscape
- 100p Full HD high-frame-rate footage

## Known limits

- `export_xml.py` is experimental: not yet import-tested in Premiere Pro / DaVinci Resolve. Check speeds, framing and dissolves after import.
- Beat tracking finds beats well, but downbeats (bar 1) are a guess. An agent cannot listen: confirm by ear, or cut on action.
- Interpolated slow motion from 24/25/30 fps footage (`minterpolate`) shows artefacts on liquids, flames, hands and thin objects. Use it for drafts and low-risk shots; use a dedicated interpolator for heroes.
- Stabilisation and grading in `render.py` are basic. Stabilisation needs an ffmpeg with vid.stab; without it the shot is left as is, with a warning. The real grade belongs in the NLE; real stabilisation rescue belongs in Gyroflow or the NLE.
- Text is not typeset by the tools: design end cards and slogans elsewhere (Remotion, HyperFrames or a design tool) and overlay the PNG.

## House rules

Put your own (or your brand's) laws in `CINEMATIC_HOUSE_RULES.md` in the project or in `~/.cinematic-edit/house-rules.md`. They override the defaults.

## Safety

No network access, no downloads, no installs, no hooks, no shell strings. Scripts only read the media you point them to and write to the folders you choose, plus the system temp folder: LUT copies under safe names (`ce_lut_*.cube`), a small LUT-check cache (`ce_lutcheck_cache.json`), and render, scan, QC and self-test intermediates (`ce_*`). Intermediates are deleted when each script finishes; the small LUT copies and the cache are kept for reuse and can be deleted at any time. `export_xml.py --ascii-links DIR` writes symbolic links only into the folder you name. Official camera LUTs are not redistributed: download them from the camera maker.

## Licence

Apache-2.0. Keep the `NOTICE` file when you redistribute. Method and rules © Deniz Gemici.

## Hire the human

The method comes from paid client work. For productions, photography and films: [denizgemici.com](https://denizgemici.com).
