# Changelog

## 1.1.1 (2026-11-27)

**Windows fix.** On Windows the LUT log conversion (`lut3d`) and stabilisation (`vidstabdetect` / `vidstabtransform`) failed, because a path such as `C:\Users\...\Temp\stab003.trf` breaks an ffmpeg filter string (`:` separates options and `\` escapes). A new `ff_path()` in `scripts/_common.py` turns backslashes into slashes, escapes `:` and quotes the whole path. `lut_filter()` and `render.py` use it for every file path given to a filter. The quoted form is also valid on macOS and Linux, so it is used everywhere.

Verified: `selftest.py` 25/25 on Windows 11 (14/18 before the fix, reported by a tester) and 25/25 on macOS; `vidstabdetect` and `vidstabtransform` also run with a path that contains spaces, Turkish letters and a colon.

## 1.1.0 (2026-11-25)

Script fixes after two independent reviews (a code review and a field test on real Fuji F-Log2 and Sony S-Log3 footage). This entry covers only `scripts/` and `templates/`. Run `python3 scripts/selftest.py` to check an install: it is offline and takes about 15 s.

### New
- **Release notes.** The XML export is labelled experimental in `--help`, in a comment inside the XML and in the README.
- **`scripts/lutcheck.py`**: checks whether a LUT really converts a log clip. It measures luma p2/p50/p98 and chroma on 3 frames, without and with the LUT. It fails when the range and the colour barely change. Results are cached. On the field-test footage, a stand-in "flat Rec.709" LUT fails (range ×1.00) and the camera maker's official LUT passes (range ×1.88, chroma ×2.26). It only catches a LUT that does not convert; another camera's log LUT usually passes.
- **`scripts/selftest.py`**: an offline end-to-end test with 25 checks:
  - tilt recovery under synthetic rotation
  - lutcheck
  - beats
  - plan_check
  - render: frame counts, BT.709 tags, audio length, NTSC, colour accuracy, push smoothness
  - qc, including true and false judder
  - export_xml
  - a BT.601-tagged (`bt470bg`) source through render, scan and lutcheck
- **`export_xml.py --selftest`**: a structural XML check that needs no media.

### plan_check.py
- **Rotation rule fixed.** The old rule failed `"rotate": 0` on vertical clips, which pushed the edit the wrong way. ffmpeg already applies the rotation flag, so the check now only warns when a flagged clip also gets an extra `rotate`.
- **Shared check for render.py.** `check_plan()` is now importable, and `render.py` uses it.
- **Field validation.** Every field is checked and errors come back as clear FAIL lines, with no tracebacks. This covers `speed > 0`, `in`/`out` order and source length, ramp keys, transition syntax, grade ranges, overlays, stills, missing files and LUT paths.
- **Dissolve-aware timing.** Totals and beat checks use the exact frame layout that `render.py` produces. A dissolve's cut point is its middle.
- **Beat window and per-cut offsets.** A cut from 2 frames early to 0.5 frames late counts as on the beat. Every cut's offset in frames is listed. Cuts 2 or more frames late are flagged. The "consecutive beats" warning now really tests consecutive beats, which removes the field-test false alarm.
- **Log and LUT checks.** A log clip with no `lut` gets a WARN. A LUT that does not convert the log is a FAIL (through `lutcheck`).
- **Push-in limit.** More than about 1/3 of shots with a push gets a WARN (the Ken Burns look).
- **Slow motion classes.** Conformed slow motion (real frames) has no quota. Deep slow motion (k ≥ 4) and ramps are limited to about 2 per 15 s and no 3 in a row. A high-frame-rate clip used at real speed gets an info note.
- **Shortest shot.** Under 0.5 s gets a WARN. For role `accent` or `breath` the limit is 12 frames (`references/numbers.md`).
- **Effective upscale.** The calculation now includes the stabiliser's zoom.

### render.py
- **Refuses to render** when the plan check fails. `--force` overrides this.
- **Paths and validation.** `lut` is resolved relative to the plan folder. `in`/`out`/`speed` are validated before any work starts.
- **Exact frame count.** Each shot is padded, then trimmed to N frames, and every intermediate is written with `-r`. Without `-r`, the mov edit list hid the last frame. Dissolves are blended as separate pieces and joined with one concat, because chained xfade lost frames. Verified on the field plan: 396/396 frames, with audio of the same length.
- **NTSC.** `29.97` becomes `30000/1001`, and the string `"30000/1001"` is accepted.
- **Colour.** YUV→RGB uses an explicit matrix and range: the source tags, or BT.709 when untagged (the Sony FX3 case). RGB→YUV uses an explicit BT.709 matrix. On test bars the colour error is now under 1.3 code values.
- **Speed.** Interpolation (minterpolate) now runs after crop and downscale, and the LUT is applied after the downscale.
- **Smooth push.** A sub-pixel push uses the `perspective` filter with per-frame float corners on a 2× canvas, then a lanczos downscale. On a 4 s push of a real frame:
  - new: no frame without movement, steady 0.12 px/frame at the corner
  - old: 59 of 60 middle frames did not move, and the zoom advanced in steps
- **New `grade` field.** Fields: `exposure`, `temp`, `tint`, `contrast`, `saturation`. It is gentle, applied in RGB after the LUT, and built from `colorchannelmixer` and `lutrgb`.
- **New `stabilize` field.** Uses two-pass vid.stab with an automatic crop-safe zoom. When ffmpeg has no vid.stab, or the plan asks for `"deshake"`, the shot is left unstabilised and a warning recommends Gyroflow or the NLE: ffmpeg's `deshake` was a no-op on real log footage (identical output). Limitations:
  - the shot is processed in 8-bit 4:2:0
  - rolling-shutter wobble and parallax are not fixed
- **New `overlays`.** Designed PNGs with alpha, with start/end times, an opacity fade, and x/y/scale/opacity. Colour is converted with BT.709.
- **Still-image shots.** A `src` of .png/.jpg plus `duration`.
- **Silent music.** Silent or near-silent music skips loudnorm instead of crashing.
- **`--hevc10` fallback.** When it cannot be used, render now warns instead of failing silently.

### export_xml.py (rewritten; experimental, not yet import-tested in Premiere Pro / DaVinci Resolve)
- **Speed-changed clips.** `in`/`out` are written in speed-adjusted clip-timebase frames (`in = source_in × fps / speed`), and `out − in = end − start`. A self-check verifies this.
- **Ramps.** A ramp is written as its average constant speed, with a RAMP marker listing the keys and a printed warning.
- **Basic Motion.**
  - Scale: cover-fit × reframe zoom × straighten zoom × push start, where 100 = native pixels.
  - Rotation: from the file's rotation flag plus `rotate` plus `straighten`. Use `--nle-applies-rotation` or `--flip-rotation` if the NLE behaves differently.
  - Center: from `reframe`, as an offset divided by the source width and height.
- **Dissolves** are written as centred `transitionitem` Cross Dissolves, at the same frames the render uses.
- **Markers** sit at each clip's in point.
- **Music** is a linked stereo pair on audio tracks 1 and 2.
- **Overlays** go on video track 2.
- **Exact NTSC rates.**
- **`--ascii-links DIR`** works around Premiere's silent import failure on non-ASCII paths.

### scan.py
- **One decode per clip.** The order is fps → downscale → LUT. 7 clips with a LUT take 22–27 s, against about 15 s per clip before.
- **Tilt detection works.** It uses projection-profile (Hough-like) accumulation on 640 px frames, with quarter-pixel Gaussian-smoothed bins (no bias towards 0°). Near-horizontal and near-vertical families are measured separately, and line evidence is required. In the synthetic ±1/2/3° rotation test, errors were ≤ 0.06° on two real Sony kitchen frames and on a generated wall. Organic frames return no reading.
- **Action counts as value.** Camera motion is trusted only when the 3×3 tiles agree. Subject action (fire, toss, smoke, pour) counts as value. "Event" candidates are added, and the strongest action second is always proposed unless the take is junk.
- **Sharpness and junk.** Sharpness and action are contrast-normalised and absolute, so a take that is soft throughout is flagged SOFT. Junk or featureless takes are flagged.
- **Dense pages.** `NAME_strip.png` (then `_strip_p2.png`, …) shows one frame every 0.5 s (1 s for takes over 30 s), in several rows, with candidate spans marked and a graph.
- **Candidate sheets.** `NAME_cN.png` shows each candidate's IN / PEAK / OUT frames at 640 px.
- **Folder index.** `_index.png` (paged) shows one frame per clip. `_summary.json` is ranked.
- **Slow-motion advice.** The clip is conformed whenever capture fps > timeline fps × 1.05 (50→30 = 60 %). Otherwise the advice is interpolation. The advice is printed once per scan, not per window.
- **Duplicate names.** Duplicate basenames get unique output names (`cardA__C0001`).
- **Candidates.** Windows are now called `candidates` (`windows` is kept as an alias), and `peak_t` is the real action or quality peak.
- **Other.** Progress and ETA lines are printed, and `--timeline-fps` accepts 29.97 or `30000/1001`.

### qc.py
- **Judder.** Frame-repeat judder is found by comparing frame-difference phases (period 2–4) inside each shot. It works on slow, gentle motion. Verified: 50p at 25 % without interpolation is flagged, and the interpolated version and normal films are not.
- **Dissolve-aware cuts.** Cut points and cut pairs follow the dissolves, showing the frame before a dissolve starts and the frame after it ends.
- **Length checks.** Video frames are compared with the plan's frame count and with the audio duration. These are hard fails.
- **Paged sheets.** `contact*.png` and `cuts*.png` are paged. `slow_shotNN*.png` shows every frame of each slowed or ramped shot. `still_hero.png` and `still_end.png` are full resolution, for the critic.
- **Per-shot numbers.** Sharpness against the median of the real footage shots (stills, end cards, titles and shots under a PNG overlay are left out, and without a plan the last shot), exposure and chroma, plus the colour jump at each cut. The soft-shot warning fires only below 30 % of that median.
- **Still-log warning.** A warning when the film still measures like log. Colour tags are written to `qc.json`.
- **Loudness tolerance** is now ±1 LU.

### beats.py
- **Tempo candidates.** Prints tempo candidates with a confidence value, and warns when the top two are close.
- **`--bpm`.** Tracking is constrained to ±4 % of the given tempo with a stiff penalty. `--bpm 110` now gives 110.0, against 117.5 before.
- **Errors.** Clean error messages for missing or undecodable files and silent tracks.

### probe.py and _common.py
- **probe.py.** Log names are searched only in metadata (QuickTime udta/meta/uuid atoms, XMP, Sony XML sidecars), never in the compressed picture, and short spellings (`DLog`, `NLog`, `LogC`) were removed: a finished H.264 render had been labelled "DJI D-Log" from random bytes. Files without atoms (MXF, MTS) are searched for long names only. Adds a folder summary: orientation counts, frame rates, log profiles, and warnings common to every clip. It also adds `log_profile()` for plan_check, and the fps-class text names both 25p and 30p.
- **_common.py.** Adds the shared `layout()`, `parse_fps`/`fps_str`, `scale_in_opts` (correct matrix; BT.601 tags such as `bt470bg` now map to a value the scale filter accepts instead of crashing render, scan and lutcheck), stills and transition parsing. Gray and RGB frame readers apply the LUT after the downscale, and the LUT temp copy is named by content hash.

### templates/edit_plan.example.json
- Adds examples of `ramp`, `grade`, `stabilize`, a still end card and `overlays`, and a `_fields` block that documents every field.

### Known limits
- The XML has not been imported into Premiere or Resolve. The rotation sign and the center units follow field notes and the FCP7 specification.
- Event scoring still misses some action under a moving camera, such as grill smoke in a handheld take. The dense strips show it.
- Stabilisation is 8-bit, and the push uses an 8-bit RGB step.
