# Colour: from camera file to premium Rec.709 delivery

Read this before touching colour on any shot. Numbers marked **[heuristic]** are starting values from practice, not standards: measure and adjust. Everything else comes from a manufacturer, a standard, or a measured result.

## Contents
1. Golden rules
2. Per-camera table
3. Technical checks before grading
4. Prove the input transform
5. Grading order with safe ranges
6. Matching a reference and matching shots
7. Skin and food pitfalls
8. Things that look cheap or "AI-made"
9. Delivery
10. LUT licensing and the grey-patch test
11. Sources

---

## 1. Golden rules

1. **Convert log with the maker's official transform before you judge anything.** Exposure, white balance and "the look" are meaningless on raw log. One transform per clip, never two (NLE colour management OR one official cube OR one CST, not stacked).
2. **Never build the look on a custom or creative LUT.** Home-made log→709 cubes and film-print LUTs applied to log clip highlights, twist hues and lift blacks. Use the official transform as the base; build the look with ordinary grading tools on top.
3. **Grade like a colourist, in order** (section 5): balance first, look last, one look per film.
4. **Measure, don't guess.** Every decision is checked on a decoded Rec.709 frame: percentiles, neutral a/b, skin hue, saturation. Look at full-size stills, not thumbnails; small previews hide skin errors.
5. **Do colour in one place, from the original file, reversibly.** The official LUT applied in ffmpeg (`scan.py --lut`, the plan's `"lut"`) is a **viewing transform** for drafts and checks, not a grade. The real grade is done in the NLE (hand off with `export_xml.py`), or, for simple deliveries without an NLE, with the plan's gentle per-shot `"grade"` fields (exposure, white balance, contrast, saturation) inside the safe ranges of section 5. If the grade lives in Premiere/Resolve, do not add "small fixes" in the ffmpeg pass as well.
6. **Prove the LUT converts.** A LUT that leaves the picture log-flat (wrong camera, wrong curve, a look LUT with a technical name) is the most common silent failure. The LUT check (in `plan_check.py`, also run by `lutcheck`) measures p2/p50/p98 and chroma with the LUT off and on and **FAILs** a LUT that barely moves them (`numbers.md` §9). Never ship a film that still measures like log.
7. **Report honestly.** If a shot cannot carry the look (8-bit and 2 stops under, VFR, jello), drop or flag it.

## 2. Per-camera table

Run `scripts/probe.py` on every clip first. Container colour tags (`color_transfer`, `color_primaries`) are **not** reliable for log: Sony S-Log3 and Fujifilm F-Log2 often arrive tagged bt709 or unknown, and NLEs then silently treat them as Rec.709. Detect from maker metadata.

18 % grey given as 10-bit code value (CV) and % of legal range (`% = (CV − 64) / 876 × 100`).

| Format | How detected (strongest first) | Official transform | 18 % grey |
|---|---|---|---|
| Sony S-Log3 / S-Gamut3.Cine | NRT XML in sidecar or MP4 tail: `CaptureGammaEquation="s-log3-cine"`, `CaptureColorPrimaries` (probe.py reads it) | NLE override "S-Log3/S-Gamut3.Cine"; Sony LC-709 / s709 cube; OCIO built-in | CV 420 / 41 % |
| Sony S-Cinetone, Rec.709, HLG | same XML (`s-cinetone`, `rec709`, `hlg`) | **No log transform.** S-Cinetone is already a display look | — |
| Fujifilm F-Log | Maker note `0x3803` = 0x10 | Override "F-Log/Rec.2020"; Fujifilm per-model cube | CV 470 / 46 % |
| Fujifilm F-Log2 | `0x3803` = 0x30 | Override "F-Log2/Rec.2020"; Fujifilm cube; Fujifilm IDT | CV 400 / 38.4 % |
| Fujifilm F-Log2 C | `0x3803` value undocumented; model X-H2/X-H2S/GFX100 II/GFX ETERNA | F-Log2 C cube / IDT (wider F-Gamut C) | CV 400 / 38 % |
| Fujifilm HLG | `0x3803` = 0x20; `arib-std-b67` | HLG→SDR tone map | — |
| Panasonic V-Log | maker notes (unverified per body); raw-log signature | Override "V-Log/V-Gamut"; Panasonic V-709 cube | CV 433 / 42 % |
| Canon Log 2 / Log 3 | MXF descriptors; maker notes in MP4 | Override "Canon Log 2/3"; Canon LUT | ≈ 39.8 % / ≈ 34.3 % |
| Nikon N-Log | maker notes | Nikon N-Log 3D LUT | CV 372 / 35 % |
| Apple Log (iPhone 15/16 Pro) | Apple make + `bt2020` primaries + transfer **not** PQ/HLG + 10-bit ProRes/HEVC [heuristic: no documented ffprobe tag] | Override "Apple Log/Rec.2020"; Apple LUT | ≈ 0.488 normalised |
| Apple Log 2 (iPhone 17 Pro) | as above + device model | Apple Log 2 LUT (Apple Gamut; differs from Log 1) | ≈ same curve |
| iPhone HDR (Dolby Vision 8.4 / HLG) | `arib-std-b67`, bt2020, DOVI side data | HLG→SDR tone map (not a re-tag) | — |
| Android HDR10/HDR10+ | `smpte2084`, bt2020, mastering metadata | PQ→SDR tone map | — |
| DJI D-Log | model in tags + user | Override "DJI D-Log/D-Gamut"; DJI LUT | ≈ CV 408 |
| DJI D-Log M | model + user declaration | Official DJI "D-Log M to Rec.709" cube only (no public curve) | not published |
| GoPro Protune Flat | GPMF / user | No log transform; gentle contrast | — |
| GoPro GP-Log2 | GPMF / user | GoPro Labs LUT generator (default applies +1.8 EV) | CV 554 |
| Blackmagic Film / BRAW | BRAW metadata | Resolve RCM / CST | 0.3836 normalised |
| ARRI LogC3 / LogC4 | ARRI metadata (Premiere misses LogC4 in MXF) | Override / CST / OCIO | ≈ 39 % / ≈ 28 % |
| RED Log3G10 | R3D (IPP2) | IPP2 / CST | 1/3 of code |

Black levels that are **normal**, not errors: S-Log3 3.5 %, V-Log 7.3 %, Canon Log 3 12.5 %. Never "fix" a lifted log black before the transform.

Unknown non-zero Fujifilm `0x3803` value, unknown gamma string, or low-confidence detection: **stop and ask the user**, showing one frame.

Transcodes, proxies and Gyroflow renders lose maker metadata: take the transform from the original clip's probe, not the derived file.

## 3. Technical checks before grading

`probe.py` reports these; act on them.

| Check | Warn / block when | Why |
|---|---|---|
| Bit depth | `pix_fmt` yuv420p/yuvj420p on a log clip = **8-bit log** | ~20 codes per stop; bands and noise when lifted |
| Bitrate | 4K log < 100 Mb/s 8-bit, < 150 Mb/s 10-bit Long-GOP [heuristic] | macroblocking in graded shadows |
| Chroma | 4:2:0 source in keying/heavy secondaries | HSL qualifiers fringe; 8-bit hue curves can blotch beige/white fabric magenta |
| Range | `pc` tag on a camera file normally `tv`; or Y < 64 / > 940 (10-bit) on a `tv` clip | wrong range = milky or crushed blacks. Verify with `signalstats`, not the tag |
| HDR | `smpte2084` / `arib-std-b67`, DOVI or mastering side data | needs a tone map, never a re-tag |
| VFR | `r_frame_rate` ≠ `avg_frame_rate` by > 0.1 %, or > 1 % of packet deltas off by > 25 % [heuristic] | drift; conform to CFR intermediate first (`-fps_mode cfr`) |
| Rotation | displaymatrix ±90 on phones; **missing** on vertical mirrorless clips | rotate to upright, never zoom a lying frame to fill 9:16 |
| Interlace / SAR | `field_order` not progressive; SAR ≠ 1:1 | deinterlace / desqueeze |

**Raw-log exposure** (before transform): `stops ≈ (measured_CV10 − grey_CV10) / codes_per_stop`; S-Log3 ≈ 78.7 codes/stop at 10-bit, ≈ 19.7 at 8-bit. Flag < −1 stop "under", < −2 "rescue only". Or run `scan.py --lut official.cube` to judge exposure on converted picture.

**Limits on lifting** [heuristic]: 8-bit log max +1 stop clean (+1.5 with denoise); 10-bit max +1.5 to +2 with denoise; 8-bit noisy clip max 1.3× punch-in. **Denoise on log before colour**, never after a lift (lift-then-denoise gives waxy skin and "sandy" mud). Do not raise blacks to the noise floor.

**Observed trap (Fujifilm F-Log2 files)**: some bodies store the log curve scaled into narrow range (raw black ≈ 8-bit Y 36–37, 10-bit 144–150, not the data-sheet 95). If the NLE decodes code/1023, blacks go milky and whites grey. Do not crush this with a Blacks slider; expand levels in the intermediate (`Y' = (Y − 64) · 1023 / 876`) and confirm with the grey-patch test. Read the raw Y plane with `-pix_fmt yuv420p`; `format=gray` expands range and lies.

## 4. Prove the input transform

An NLE saying "detected" is not proof (Premiere's scripting API reported Rec.709 after a working override). Export the **same frame** with no grade, transform off vs on, from the sequence (not the source monitor):

- HSV saturation median rises **≥ 1.6×** with the transform on;
- darkest 1 % luma falls from ~9 to 0–5 (RGB8) for S-Log3-like curves;
- neutral grey lands at 40–46 % Y.

Identical frames = transform not active = **no grading, no render**. A change in grey alone proves nothing (tone mapping can leave grey near the same value).

Double-transform traps: NLE "detect log" + sequence input tone mapping; override + manufacturer LUT in Lumetri Input LUT; RCM + CST node in Resolve. Choose one.

## 5. Grading order with safe ranges

Decode for measurement: `-vf scale=in_color_matrix=bt709:in_range=tv:out_range=pc,format=rgb48le`. Without an explicit matrix ffmpeg uses BT.601 and every number is wrong.

Order: **transform → exposure/WB → contrast/curves → lift/gamma/gain → secondaries → look → vignette/halation/grain → output.** Put balance (exposure, WB, contrast, whites, blacks) on the clip; put the shared look on one adjustment layer / timeline node. Do not start every shot with a fixed "contrast + saturation" block; it makes every film look the same and nothing like colour grading.

### 5.1 Exposure: subject, not frame
- Anchor on **face luma** if a face exists, else the subject/salient region median, else the frame median. Never normalise on p98 (pushes too far) or on frame median alone (dark-background close-ups blow out).
- Targets (full-range %) [heuristic]: light skin 55–75 %, medium 40–60 %, dark 25–45 %; product/food subject 40–65 %, never below 35 % in a restaurant/food ad; subject median ≥ 15 points above frame median; daytime frame mean 30–50 %, night ≥ 22 %.
- Low-key is allowed: darken the surround, not the subject. Clients reject "too dark" films when the subject itself is dark.
- Correction cap per shot: ±1 stop 8-bit, ±1.5 stops 10-bit, then flag. Apply as a linear multiply or log offset, not a gamma lift on 8-bit display-referred data.
- NLE sliders are non-linear and differ between colour-managed and non-managed sequences: measure the effect of every slider move on the exported frame.

### 5.2 Contrast and curves [heuristic]
- Black point p0.5 → **2–5 %** (deep and clean; < 1 % crushed, > 8 % milky). White p99.5 → **92–97 %**, rolled off, not clipped. Any channel ≥ 254 on > 0.3 % of frame is a problem; > 1 % on the subject is an error.
- Pivot at the key level: 0.30–0.40 low-key, 0.45–0.55 daylight. Toe slope 0.7–0.9, mid slope 1.1–1.3, shoulder 0.5–0.7. Mean Y should move ≤ 2 % from the contrast move itself.
- Highlights/Shadows-type sliders within ±40; no local contrast/clarity above 10 %.

### 5.3 White balance and lift-gamma-gain
- Find neutral patches (plates, walls, shirts, grey card: OKLab C < 0.02, L 0.5–0.9). Target |R−G|, |B−G| ≤ 3 (RGB8), |a*| < 2, |b*| < 4.
- Keep intentional warmth: tungsten interior whites b* +4..+8. Neutralise a cast at most ~40 % on mixed scenes; forcing a beige garment to white turned skin pink.
- Grey-world only as a ≤ 50 % weighted fallback; it fails on sunsets, food, neon.
- Wheels ≤ 3 % each on 8-bit, ≤ 5 % on 10-bit. NLE temperature/tint are unitless (not Kelvin); verify with the b*/a* of a white object.

### 5.4 Secondaries
- **Skin [heuristic]:** there is no single correct skin hue. Measure the person's own skin under the most neutral light in the shoot and protect it. Rough Lab/LCh hue ranges: light/rosy skin 38–47°, medium/olive 44–55°, deep 45–60°; chroma about 15–30 (`numbers.md` §9). The vectorscope skin line (≈ 123°, I-line) is a guide, not a target. A hue clearly above the person's real tone reads jaundiced; clearly below reads sunburnt. Measure on the face mask's luma P25–P75 only. Move the **mean**, keep per-pixel variation (cheek and nose red).
- **LED / pink-purple light pollution:** hue-vs-sat on 300–345° −20..−50 %; afterwards skin hue moves ≤ 2°, chroma ≤ 3 %. Fix LED green/magenta with tint on neutrals, not on skin. Heavy cleanup can turn a shot green: small steps.
- **Sky / sea:** keep their own hue; never rotate the ≥ 225° band; never darken sky or sea with hue-vs-luma on compressed footage (blocks appear).
- **Greens / foliage:** −5..−10 saturation for premium; desaturate mint/teal toward olive if the palette asks.
- **Food:** see section 7.

### 5.5 Saturation caps that read premium [heuristic]
- Global saturation 95–110 % (never above 110; food 100–110, red/orange dishes up to +5..+15; 125+ never). Vibrance ≤ +15 (vibrance protects skin; raise saturation only if skin chroma is low; if skin C > 31, drop saturation to 85–98).
- Mean HSV-S 25–40 % cinematic, 35–50 % food/ad; p95 S < 75 %.
- Saturation roll-off: 70–80 % at Y < 0.08 and Y > 0.90. Density: saturated colours darker than the neutral mean (hue-vs-luma −5..−12 % on reds/blues/magentas, skin ≤ −3 %).
- After the look, if mean saturation rose > 10 % over the balanced grade, take 5–10 back. Saturation creeps up during a session.
- Separate with contrast, tone and light, not saturation.

### 5.6 Look and film emulation (subtle)
- One look family per film; a second look only when location/light changes. Choose a palette from an outside reference (a real film still), 4–5 colours. Never derive the palette from your own approved frames (it proves nothing).
- The tone must be visible: a "clean" technical grade with tiny wheel moves (0.05) reads as no grade. Split tone [heuristic]: shadows b* −1..−4 (cool) or toward the palette's dark colour, highlights b* +2..+6; mids |a|,|b| ≤ 1.5; at night shadows a* ≤ +1 (no magenta). Visible, never exaggerated: if you cannot name the tone at first glance, it is too weak; if it fights skin, it is too strong.
- Bundled NLE looks/film cubes: only as a last layer at 20–40 % intensity; they move mid-grey by up to +0.6 stop, so re-measure grey and blacks after.
- **Local light** matters more than global colour: darken the surround −0.4..−0.8 stop with a large soft mask that follows the subject's shape; never a visible circle or halo, never across a flat sky/wall/water. A vignette is not local light (it has no direction). Keep light true to the time of day.
- Halation: threshold > 90 % Y, blur 0.2–0.6 % of width, red-orange, 3–8 % screen. Grain: temporal, luma-weighted, σ 1–2.5 % at 1080p. Diffusion 0.3–0.5 px at 4K before grain; never sharpen graded log. Print emulation: low strength, not a full PFE LUT on mixed footage.

## 6. Matching a reference and matching shots

When the user gives a reference, the target is **the reference, not your taste**. Pick **one** reference frame (the user's own if given) and approach it by measurement. A reference shows direction; it is not a recipe to copy. Sometimes the best reference is a still photo from the same shoot (same tables, same light).

**Measure the reference on 3–5 frames** (`scripts/reference.py` gives per-shot light and palette):
1. Luma percentiles p0.5, p50, p99.5 and p25–p75 slope.
2. HSV-S mean and p95.
3. Per-band tint: mean a*/b* of dark (Y < 0.25), mid and light (Y > 0.7) pixels.
4. Hue shares: k = 5 dominant hues and their pixel share (e.g. "85 % of saturated pixels red/orange, greens olive").
5. Face luma and skin chroma.

**Apply in this order:** neutral base → per-shot exposure on the face → luma CDF match → per-band tint and saturation match → hue corrections (pull off-palette hues toward the palette or desaturate −0.5..−0.75) → film emulation → side-by-side sheet against the reference **before** rendering.

**Acceptance** [heuristic]: hero shot within ±10 % of each reference number. Then lock the hero, match others to it:
- Match L with a CDF match on subject masks at 50–70 % strength, smoothed to a monotone 5-point curve (raw LUTs posterise).
- Match a,b by mean/std only; never move skin hue > 3°; never pull a motivated light colour to neutral.
- Pass: subject L ±0.02, neutral a/b ±0.01, skin hue ±3°, p0.5/p99.5 ±2 %. ΔE2000 < 2 pass, 2–4 look, > 4 fix; skin across a cut ΔE00 < 3.
- Same scene, same warmth: two shots of one sunset with different temperature read as two cameras.
- Make a strip of one frame every 3 s next to the palette strip; read the film as a whole.

Limits: no orange "mud" over everything; kitchen steel stays neutral dark grey; sea never brown; no colour that breaks the real time of day.

## 7. Skin and food pitfalls

**Skin**
- Flattening every face to one hue/chroma erases life and makes everyone the same tone. Move means only, per person.
- "Make it stronger" usually means more light and contrast, not more yellow.
- HSV hue < 5° or > 35° on skin = wrong. Do not mix HSV and Lab angles.
- Check left/right halves of a face before baking a local skin fix (it can split into yellow-green and orange).
- Wide-gamut log → 709 under pink LED gives oversaturated skin; fix with a magenta secondary, not by switching the transform off.
- Plastic skin from denoise: skin high-pass RMS should stay ≥ 60 % of source [heuristic].

**Food**
- Neutral, not cool, shadows (b* ≥ −2). Plate whites clean (|a|,|b| ≤ 3).
- Greens hue 90–130°, S 35–60 %; reds p95 S ≤ 80 %.
- Food turns yellow easily: reduce saturation, not only temperature.
- When darkening a scene, never darken the plate or the food. Centre of interest is brighter.
- Product colours (garments, packaging) stay true: check ΔE on the product. A creative LUT can turn a green sweater navy.

**Non-log footage (phone SDR, Rec.709 profiles, HLG):** touch lightly (≈ +0.1 EV, almost no contrast). Dark, contrasty "brand looks" on such footage are often worse than the camera's own colour. Never change a garment's hue; adjust luma contrast only. HLG→709 by plain transfer conversion clips; use a tone map (zscale + hable/mobius).

## 8. Things that look cheap or "AI-made"

| Symptom | Cause | Rule |
|---|---|---|
| Teal shadows + orange skin on everything | split tone by default, on all hues | only if the reference asks; shadow tint ≤ 4 b*, never on skin hues; sky/sea keep their hue |
| Muddy crushed blacks | blacks pulled down on low-contrast or 8-bit shots; teal in shadows | deep **clean** blacks: p0.5 2–5 %, neutral or palette-tinted, detail kept; try −8 before −20 on a Blacks slider |
| Milky blacks | lifted lift, wrong range, Full/10-bit forced onto an 8-bit clip | check range; p0.5 ≤ 5 % |
| HDR halo, flat-but-crunchy | local tone mapping, clarity, highlights −/shadows + | local contrast ≤ 10 %; sliders within ±40 |
| Candy / neon colour | saturation used for separation | caps in 5.5 |
| Flat grey "log look" | log left unconverted or grade too timid | transform proven (section 4); visible tone |
| Visible round "spotlight" | small hard mask | big soft shape-following mask, or none |
| Shot-to-shot jumps | per-shot looks | one look per film; match to hero |
| Banding in skies/walls | 8-bit processing, low bitrate | section 9 |

## 9. Delivery

- **Standard:** SDR Rec.709 / BT.1886 (gamma ≈ 2.4 reference, dim room). Phones and laptops in bright rooms behave closer to 2.2/sRGB. With no calibrated monitor, grade on a 2.2 viewer and always check on a phone.
- **Tags:** BT.709 primaries, transfer, matrix (1-1-1), **limited (tv) range**. `render.py` writes them; `qc.py` checks them. Verify: `ffprobe` must read bt709/bt709/bt709/tv. Untagged files get guessed by platforms. Do not deliver HLG/PQ/2020 unless asked.
- **Precision:** keep 10/16-bit until the final encode; **dither once** (zscale `dither=error_diffusion`). For 8-bit outputs with gradients add fine temporal grain or `deband`/`gradfun` before the dither.
- **10-bit HEVC** (`render.py --hevc10`: libx265, yuv420p10le, `-tag:v hvc1`) bands less; Instagram, YouTube and iPhone accept it. 8-bit H.264 (CRF ≤ 18, high profile) for widest compatibility. Platforms re-encode; give them quality. A 1080×1920 file at ~10 Mb/s turned grey gradients into macroblock blotches; ~40 Mb/s H.264 or ProRes was clean.
- **QuickTime gamma shift:** macOS QuickTime/Safari/ColorSync show 1-1-1 files with an effective gamma ≈ 1.96 (lighter, less saturated). Do **not** regrade the master to compensate. Judge in a non-colour-managed player (e.g. VLC) or the NLE; offer a Mac/iPhone side-by-side check.
- **After export:** extract stills from the **delivered file** and re-measure (section 5 numbers); previews can differ from the master.

## 10. LUT licensing and the grey-patch test

- Manufacturer LUTs are **not redistributable** by this skill. Users download them from the official pages (Sony, Fujifilm, Panasonic, Canon, Nikon, DJI, GoPro, Apple, ARRI). Some need a free account. Never download automatically without the user's consent.
- Record per format: official URL, expected filename, and the SHA-256 of the user's first verified download; check the hash before use.
- Redistributable alternative: compute technical transforms from published formulas with colour-science or OpenColorIO (both BSD-3) and bake a 65³ cube locally.
- Creative LUTs (community, print emulation): link only, respect the author's licence, never bundle, never as base.
- **Grey-patch range test (every new cube):** vendors differ on whether 0–1 means legal-expanded (64–940) or full code. Synthesise a frame with a patch at the format's 18 % grey CV (S-Log3 420, F-Log2 400, V-Log 433 …), run the exact chain you will render with (`lut3d` tetrahedral, 16-bit RGB), and check the output grey lands at **40–46 % Y**. About 5 % off means the range assumption is wrong. Also check black stays black and the YUV matrix: camera log is usually BT.709 matrix, Apple Log/HLG/PQ BT.2020 NCL.

## 11. Sources

- Sony S-Log3 18 % = 41 %: https://helpguide.sony.net/di/pp/v1/en/contents/TP0000909109.html
- Fujifilm data sheets and LUTs: https://www.fujifilm-x.com/en-gb/support/download/technical-data/ , https://fujifilm-x.com/en-us/support/download/lut/
- ExifTool Fujifilm tags (0x3803): https://www.exiftool.org/TagNames/FujiFilm.html
- Panasonic V-Log 18 % = 42 IRE: https://eww.pavc.panasonic.co.jp/dscoi/DC-GH7/html/DC-GH7_DVQP3109_eng/0097.html
- Nikon N-Log exposure: https://onlinemanual.nikonimglib.com/technicalguide/log_raw/video_recording_editing/en/correct_exposure_10.html
- Apple Log formula (colour-science): https://colour.readthedocs.io/en/master/_modules/colour/models/rgb/transfer_functions/apple_log_profile.html
- GoPro GP-Log2: https://gopro.github.io/labs/log/
- Resolve colour management: https://blog.frame.io/2023/12/04/color-management-cheat-sheet-davinci-resolve/
- Premiere colour management: https://community.adobe.com/announcements-732/now-released-dramatically-updated-color-management-in-premiere-pro-313927
- Vectorscope skin line: https://docs.kdenlive.org/en/tips_and_tricks/scopes/vectorscope_i_and_q_lines.html
- OKLab: https://bottosson.github.io/posts/oklab/
- YouTube upload colour spec: https://support.google.com/youtube/answer/1722171
- QuickTime gamma: https://www.cined.com/quicktime-gamma
- Display preparation (Yedlin): https://www.yedlin.net/DisplayPrepDemo/
