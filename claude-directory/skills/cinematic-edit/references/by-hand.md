# By hand: ffprobe and ffmpeg recipes

Contents: 1 Inventory · 2 LUT check · 3 Watching every clip · 4 Reference films · 5 Music · 6 Plan check · 7 Rendering · 8 QC · 9 NLE hand-off

Every recipe uses only the user's own `ffprobe` and `ffmpeg`. Replace `CLIP`, `OFFICIAL.cube` and the output folders with real paths; quote paths that contain spaces. Write outputs into a `work/` folder in the project. Numbers come from `numbers.md`.

## 1. Inventory (frame rate first)

```
ffprobe -v error -show_streams -show_format -of json CLIP
```

Read from the video stream:

| Field | What it tells you |
|---|---|
| `r_frame_rate`, `avg_frame_rate` | Capture rate. If the two differ, the clip is variable frame rate (phones): conform first |
| `nb_frames`, `duration` | Length; frames ÷ duration should match the rate |
| `pix_fmt` | `yuv420p` = 8-bit 4:2:0; `yuv420p10le` / `yuv422p10le` = 10-bit |
| `color_transfer`, `color_primaries` | `arib-std-b67` = HLG, `smpte2084` = PQ; most log files are tagged as BT.709 and must be identified otherwise |
| `side_data_list` → `rotation`, or a `rotate` tag | Vertical clips stored landscape: rotate, never zoom |
| `width`, `height` | Pixel budget for reframing |

Slow motion: a 50/60p file on a 24/25/30 timeline is real 2× slow motion; 100/120p is 4×. Some cameras record "S&Q" files already conformed (for example 25p playback of 100p capture): the stream says 25 but the motion is already slow. Sony writes both rates into the sidecar XML (`captureFps`, `formatFps`).

Log profile: Sony writes `CaptureGammaEquation` (for example `s-log3-cine`) into the sidecar XML next to the clip. Other makers store it in metadata that ffprobe does not decode: ask the human which profile was used, or check a frame (a log picture is grey, low-contrast and low-saturation; its darkest pixels sit well above black).

One frame to look at:

```
ffmpeg -v error -ss 3 -i CLIP -frames:v 1 work/inv/CLIP_raw.png
```

## 2. LUT check (does the official transform really convert?)

Measure the same frame with the LUT off and on:

```
ffmpeg -v error -ss 3 -i CLIP -frames:v 1 -vf "signalstats,metadata=print:file=work/lut/off.txt" -f null -
ffmpeg -v error -ss 3 -i CLIP -frames:v 1 -vf "lut3d=file=OFFICIAL.cube:interp=tetrahedral,signalstats,metadata=print:file=work/lut/on.txt" -f null -
```

Compare `YLOW`, `YHIGH` (10th and 90th percentile luma) and `SATAVG`:

- A real log → Rec.709 transform widens `YHIGH − YLOW` clearly and raises `SATAVG` about 1.6× or more (`numbers.md` §9).
- If the spread and saturation barely move, the picture is still log-flat: the LUT is wrong (a look LUT, another camera, another curve). **FAIL**: find the right transform.
- A LUT for another camera's log may still "pass": confirm the LUT name matches the camera and curve from §1.

Save both frames and look at them side by side:

```
ffmpeg -v error -ss 3 -i CLIP -frames:v 1 -vf "lut3d=file=OFFICIAL.cube:interp=tetrahedral" work/lut/CLIP_on.png
```

## 3. Watching every clip

Dense strips across the whole clip, through the LUT, four frames per second, 8 × 4 per page:

```
ffmpeg -v error -i CLIP -vf "lut3d=file=OFFICIAL.cube,fps=4,scale=360:-2,drawtext=text='%{pts\:hms}':x=6:y=6:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.5,tile=8x4" -vsync vfr work/scan/CLIP_strip_%02d.png
```

(Without log footage, leave out the `lut3d` part. If your ffmpeg has no `drawtext`, leave that part out and count frames: page n, tile i = (n−1)·32 + i quarter-seconds.)

Motion and change per second, to find the busiest moments you must look at yourself:

```
ffmpeg -v error -i CLIP -vf "fps=5,scale=320:-2,select='gte(scene,0)',metadata=print:key=lavfi.scene_score:file=work/scan/CLIP_scene.txt" -f null -
```

High `scene_score` runs mark camera moves, whip pans, fire, tosses and pours. They are candidates, not defects: look at them.

Sharpness check of a candidate frame (higher = sharper; compare within the same clip only):

```
ffmpeg -v error -ss 7.2 -i CLIP -frames:v 1 -vf "lut3d=file=OFFICIAL.cube,edgedetect=mode=wires,signalstats,metadata=print:key=lavfi.signalstats.YAVG" -f null -
```

For every candidate window write: start, peak, end, what happens, scale, verdict (`shot-judging.md`). Pull start, peak and end frames large before you choose:

```
ffmpeg -v error -ss 7.2 -i CLIP -frames:v 1 -vf "lut3d=file=OFFICIAL.cube" work/scan/CLIP_7.2.png
```

Tilt: check horizons and verticals on the large frame; straighten within the range in `numbers.md` §5.

## 4. Reference films

Cut times:

```
ffmpeg -v error -i REF -vf "select='gt(scene,0.3)',metadata=print:file=work/ref/cuts.txt" -f null -
```

Each `pts_time` line is a cut. Shot lengths = differences between cuts (add 0 and the duration at the ends). ASL = mean, also note the median and the longest held shot. Fast whips and flashes can add false cuts and dissolves can hide real ones: confirm on strips (§3, `fps=4`).

One frame per shot: take the midpoint of each shot with `-ss` as in §3. Palette and light: look at the frames; `signalstats` gives `YAVG` (key) and `SATAVG` (saturation) per frame.

## 5. Music

Loudness and energy per half second:

```
ffmpeg -v error -i TRACK -af "ebur128=metadata=1,ametadata=print:key=lavfi.r128.M:file=work/music/energy.txt" -f null -
```

Quiet moments and drops show as dips and jumps in momentary loudness `M`. Tempo: ask the human, or read the BPM from the track's source page; at 25 fps one beat lasts 1500 ÷ BPM frames (120 BPM = 12.5 frames). Bar 1 is a guess until a human confirms it: cut on action and on clear energy changes when unsure.

Prepare the edit audio once:

```
ffmpeg -v error -i TRACK -ar 48000 -ac 2 work/music/music.wav
```

## 6. Plan check (by eye, line by line)

FAIL items:
- No one-sentence `idea`, or a shot without `reason`.
- A log clip without an official LUT that passed §2.
- A ramp whose last key ≠ `out − in`, or a slowdown k above capture ÷ timeline fps without `interpolate` and a frame check (`slow-motion.md` §4).
- A vertical clip with zoom instead of rotation; a reframe that upscales beyond the pixel budget (`numbers.md` §5).
- A shot window outside the clip's duration.

WARN items (fix, or write why in `reason`):
- Shots shorter than the register's minimum, or ASL far from the brief's register (`numbers.md` §2–3).
- The same moment, person or angle twice; push on more than about a third of shots.
- More than 1–2 deep ramps per 15 s; dissolves outside the allowed lengths.
- Turns not on phrases; the film not ending on the subject's result.

## 7. Rendering

Render each shot to an intermediate at the timeline frame rate, then join them.

Constant speed (example: 50p source at half speed on a 25p timeline, k = 2), with LUT, rotation and a 9:16 reframe:

```
ffmpeg -v error -ss 12.40 -to 14.00 -i CLIP -vf "lut3d=file=OFFICIAL.cube:interp=tetrahedral,setpts=2*(PTS-STARTPTS),fps=25,crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920:flags=lanczos,setsar=1" -an -c:v libx264 -crf 14 -preset slow -pix_fmt yuv420p work/shots/s01.mp4
```

- Rotation: add `transpose=1` (clockwise) or `transpose=2` before cropping.
- Straighten: `rotate=-0.8*PI/180:ow=iw:oh=ih:c=black`, then crop inside the black corners (`finishing.md`).
- Speed ramp: build the `setpts` expression from the ramp keys as in `slow-motion.md` §4 (closed-form smoothstep integral per segment), then `fps=25`. Check the frame count with `ffprobe -count_frames`.
- Interpolated slow motion from 24/25/30 fps: `minterpolate=fps=50:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1` before `setpts`; check every frame (`slow-motion.md` §5–6).
- Gentle grade: `eq=brightness=0.02:contrast=1.04:saturation=1.03`, `colorbalance`, `colortemperature` (small values only; `colour.md` §5).
- Stabilise (when your ffmpeg has vid.stab): pass 1 `vidstabdetect=result=work/shots/s01.trf`, pass 2 `vidstabtransform=input=work/shots/s01.trf:smoothing=15,unsharp=5:5:0.6`. If the result warps or crops too much, use another window or another shot.
- Push-in: `zoompan` or a crop that shrinks over time with an eased expression, at most the push in `numbers.md` §5.

Join hard cuts with the concat demuxer (`work/shots/list.txt` holds lines like `file 's01.mp4'`):

```
ffmpeg -v error -f concat -safe 0 -i work/shots/list.txt -c copy work/picture.mp4
```

A dissolve between two shots: `xfade=transition=fade:duration=0.4:offset=…` on both inputs after `settb=AVTB,fps=25`.

Overlay a finished PNG end card with an opacity rise:

```
ffmpeg -v error -i work/picture.mp4 -loop 1 -t 3 -i endcard.png -filter_complex "[1]format=rgba,fade=t=in:st=0:d=0.6:alpha=1,setpts=PTS+12/TB[o];[0][o]overlay=eof_action=pass" -c:v libx264 -crf 14 -pix_fmt yuv420p work/picture_card.mp4
```

Music and loudness (two-pass: measure first, then apply the measured values):

```
ffmpeg -v error -i work/picture_card.mp4 -i work/music/music.wav -af "loudnorm=I=-14:TP=-1:LRA=11:print_format=summary" -map 1:a -f null -
ffmpeg -v error -i work/picture_card.mp4 -i work/music/music.wav -map 0:v -map 1:a -af "loudnorm=I=-14:TP=-1:LRA=11:measured_I=…:measured_TP=…:measured_LRA=…:measured_thresh=…,afade=t=out:st=…:d=1.5" -c:v libx264 -crf 16 -pix_fmt yuv420p -vf "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709" -color_primaries bt709 -color_trc bt709 -colorspace bt709 -c:a aac -b:a 320k -shortest FINAL.mp4
```

Drafts: `scale=iw/2:-2`, `-preset veryfast -crf 23`.

## 8. QC

```
ffmpeg -v error -i FINAL.mp4 -vf "blackdetect=d=0.04:pix_th=0.10" -an -f null -
ffmpeg -v error -i FINAL.mp4 -vf "freezedetect=n=0.002:d=0.12" -an -f null -
ffmpeg -v error -i FINAL.mp4 -af "ebur128=peak=true" -f null -
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames,r_frame_rate,color_primaries,color_transfer,color_space -of default=nw=1 FINAL.mp4
```

- Any black or frozen stretch you did not plan is a FAIL.
- Integrated loudness within ±1 LU of the target, true peak ≤ −1 dBTP.
- Colour tags BT.709; frame count = duration × fps.

Contact pages (every 4th frame) and the frames either side of each cut:

```
ffmpeg -v error -i FINAL.mp4 -vf "select='not(mod(n,4))',scale=320:-2,tile=8x6" -vsync vfr work/qc/contact_%02d.png
```

Look at every page, then pull 2–3 full-resolution stills of the hero and the last shot.

## 9. NLE hand-off

When the grade or final cut happens in Premiere Pro or DaVinci Resolve, hand over a shot list from `edit_plan.json`: per shot the source file, source in/out (timecode), timeline position, speed or ramp keys, rotation, straighten angle, reframe, and the reason. The editor rebuilds it on the original camera files with the camera's official colour management. The full edition at https://github.com/denizgemici/cinematic-edit exports this as a timeline file.
