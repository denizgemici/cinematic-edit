# Shot finishing: no camera shot is used as shot

Contents: 1 The rule · 2 Order of operations · 3 Best window · 4 Rotation of vertical clips · 5 Straightening · 6 Stabilising · 7 Reframing and pixel budget · 8 Push-ins · 9 Speed · 10 Per-shot finishing log

## 1. The rule

Every shot is finished before it is cut in: converted from log, levelled, stabilised when it needs it and stabilisation works cleanly, recomposed for the output frame, given the right speed, and trimmed to its best moment. A raw take straight from the card never appears in a film. Write each decision into the shot's entry in `edit_plan.json`; `render.py` applies them in its own fixed order. All shared numbers (tilt range, push, pixel budget, stabilisation limit) are in `numbers.md` §5.

## 2. Order of operations (render.py follows this)

1. Official log → Rec.709 transform (`"lut"`), or the NLE's colour-space override. In ffmpeg this is a **viewing transform** for drafts and checks; it is not the grade.
2. Basic stabilisation (`"stabilize"`), when the shot needs it (section 6).
3. Rotation for clips filmed vertically (`"rotate"`; ffmpeg applies the camera's rotation flag automatically).
4. Speed / slow-motion conform (`"speed"`, `"ramp"`, `"interpolate"`), see `slow-motion.md`.
5. Straighten (`"straighten"` in degrees) with the minimum zoom that hides the corners.
6. Reframe to the output aspect (`"reframe": {"x":0.5,"y":0.45,"zoom":1.0}` — x/y are the focal point, 0–1).
7. Eased push-in (`"push": [1.00, 1.05]`), only on the shots that need it (section 8).
8. Gentle per-shot correction (`"grade"`: exposure, white balance, contrast, saturation), then scale to the exact output size and frame rate.

The real grade happens in the NLE (see `colour.md`); the `grade` fields are for gentle balance and shot matching on simple deliveries. Exact keys: `templates/edit_plan.example.json` and `render.py --help`.

## 3. Best window

- Scan the whole take (scan.py samples ≥ 2 frames per second, default 8). The head and tail are usually the least useful: the camera settles, focus hunts, someone calls cut. Value is mostly in the middle.
- A window must contain the shot's **iconic frame**: the peak of the gesture, the moment the light hits, the pour at its fullest. Start late, leave early: begin inside the movement, end as it completes.
- One long take can give several shots: use different windows as different shots, never the same seconds twice.
- A clean, beautiful second is enough: with real slow motion (high frame rate) it becomes 2 s or more on the timeline.
- People: use held, deliberate moments (a pose, a look that is clearly intended). Discard talking to the crew, looking at the monitor, fixing hair or clothes, the glance after the action. A walk is a pose if it is a clean walk.
- The numbers in scan.py are hints. A shallow-focus or moving-subject shot can score low and still be the most beautiful shot of the take: **look at the strip** and decide with `shot-judging.md`.

## 4. Rotation of vertical clips

Many cameras store a vertically filmed clip as a landscape frame with a rotation flag (`probe.py` reports `rotation` and the display size). Never zoom a lying frame to fill 9:16: it throws away most of the picture and the subject stays sideways. Rotate it upright at a scale that fits the whole frame; then reframe. After rotating, still check and straighten small tilts.

## 5. Straightening

- A slight tilt reads as a mistake; a strong tilt reads as a choice. Straighten lines that should be level or plumb (horizon, counter, table edge, window and door frames, walls) when they are off by **0.2–15°** (`numbers.md` §5), to exactly 0° or 90°. Keep a strong, clearly deliberate Dutch angle.
- Measure the angle on a full-size still (scan.py reports `tilt_deg` with `tilt_spread_deg`, how much the readings disagree; treat it as a hint and confirm on the frame). When unsure, straighten.
- Zoom needed so no empty corners show: `k = cos θ + sin θ × (long side / short side)`. In 16:9 that is about +3.1% at 1° and +6.1% at 2°; in 9:16 the same formula applies with the long side vertical. Include it in the pixel budget (section 7).

## 6. Stabilising

**Stance:** stabilise when gyro data or optical flow gives a clean result; otherwise choose a calmer window of the same take, or drop the shot. Never keep a shot whose stabilisation shows wobble, warping or jello.

- `render.py` has a basic optical-flow stabiliser (`"stabilize"` on the shot). Use it for small jitter; for real rescue work use Gyroflow or the NLE, then check the result frame by frame.
- `"stabilize": true` runs two-pass vid.stab only. If ffmpeg lacks vid.stab, `render.py` skips it with a warning: ffmpeg's `deshake` was a no-op on real log footage. vid.stab also chases large moving subjects (a tossed pan), so check every stabilised shot.
- Prefer gyro-based stabilisation when the camera recorded gyro data (many Sony bodies, GoPro, DJI, Insta360; Gyroflow reads them). Fujifilm and Panasonic bodies record no usable gyro data: use optical-flow stabilisation and accept more risk.
- Warp-type stabilisers wobble straight lines: avoid them on architecture and interiors.
- If a shot needs more than about 110% stabiliser zoom at delivery resolution, or shows rolling-shutter jello, it is not a clean result: find a calmer second in the same take first, otherwise drop it.
- Small, organic handheld movement that is consistent can stay as a style; random jerks cannot.

## 7. Reframing and the pixel budget

Effective upscale = cover-fit factor × reframe zoom × straighten zoom × maximum push. `plan_check.py` computes it per shot.

| Shot | Limit |
|---|---|
| Hero, product, faces, close-ups | ≤ 100% (no upscaling) |
| Other shots | ≤ 115%, after checking a 100% view |
| > 150% | fail: choose another shot |

Useful numbers: 4K UHD (3840×2160) into a 1080×1920 vertical film: the 9:16 crop is 1215×2160 px, so you can zoom about 1.12× more before upscaling; into 1920×1080 you have 2× headroom. 1080p landscape into 9:16 has no headroom: the crop is only 607 px wide; do not use such a crop for a hero.

Recompose with intent: when cutting a vertical from a horizontal, choose the focal point (`x`,`y`) per shot so the subject and its direction of movement have room; keep important detail out of the platform's UI zones (see `type-and-motion.md` for safe areas).

## 8. Push-ins

- **The locked frame is the default.** A locked frame is calm and premium; a push on every static shot is the recognisable look of AI edits.
- A push is for emphasis: **at most about one shot in three**, **3–6% over shots up to 3 s, 5–8% over 4–6 s** (`numbers.md` §5), eased in and out, one direction per shot. Never a linear zoom that starts and stops abruptly.
- Don't push a shot that already has a camera move.
- Successive pushes should not all go the same way at the same speed.
- Count the push in the pixel budget. If you push more shots than a third, write why in the plan.

## 9. Speed

See `slow-motion.md` for the full rules. In short: check the source frame rate first (`probe.py`); high-frame-rate footage is conformed at exact ratios (50→25 = 50%, 100→25 = 25%, 120→24 = 20%); normal-frame-rate footage slowed down needs frame interpolation and frame-by-frame checking; slow motion belongs to physical events (pour, toss, steam, fabric, hair, a glance), not to people talking.

## 10. Per-shot finishing log

Before rendering, every shot in the plan answers:

| Field | Question |
|---|---|
| `in`/`out` | Is the iconic frame inside? Head and tail trimmed? |
| `lut` | Is the log converted with the maker's official transform? |
| `rotate` | Vertical clip upright, not zoomed? |
| `straighten` | Lines level within 0.2°, or deliberately tilted? |
| `stabilize` | Calm enough? If not: clean stabilisation (gyro/optical flow), or another window, or drop. |
| `reframe` | Subject and its motion have room in the output frame? |
| `push` | Does this shot need a push, or is it better locked? Within budget and the one-third limit? |
| `grade` | Balanced and matched to its neighbours? |
| `speed` | Real slow motion, or justified interpolation? |
| upscale | Within the pixel budget? |
| `reason` | What does this shot do for the idea? |
