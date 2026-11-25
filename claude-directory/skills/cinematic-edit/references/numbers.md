# Shared numbers: the one table

Every number that more than one file uses lives here. Other files point to this page instead of repeating it. If a file and this page disagree, **this page wins** (and house rules win over this page).

**How to read the numbers.** Most of them are working values from practice **[heuristic]**, not laws. They are warnings, not gates: you may break one when the footage or the idea asks for it, but **write in the shot's `reason` (or the plan's `notes`) why you broke it**. Only the items marked **hard** are never broken.

The director's principles behind the numbers: one idea per film; beauty first; no camera shot used raw; frame rate checked first; slow motion is central; restraint (hard cuts, no template transitions, no whooshes, no white flashes, no boxes behind text, effects barely there); locked frames by default.

## 1. Frame rate and slow motion

| Item | Value | Notes |
|---|---|---|
| Conform speed | `speed = timeline fps ÷ capture fps` | 50p→25p = 0.5; 60p→30p = 0.5; 100p→25p = 0.25; 120p→24p = 0.2; 60p→25p = 0.417 (prefer 50p for 25p) |
| Gentler clean speed | `speed = k × timeline ÷ capture`, k a whole number | 100p→25p at 0.5 (every 2nd frame). Non-whole k judders |
| Clean slowdown limit | `k_max = capture ÷ timeline` | 50p on 25p: 2×; 100p: 4×; 120p: 4.8×. Beyond it: interpolate and check, or a deliberate frame hold |
| Timeline seconds from 1 s of source | 50p→25p: 2.00 s · 100p→25p: 4.00 s · 120p→24p: 5.00 s · 60p→30p: 2.00 s | "A clean second becomes two seconds" |
| **Conformed slow motion** (k = 2, e.g. 50p at 50 % on 25p) | **No quota** | Conformed 50p half-speed B-roll is normal material, not "wedding video". It can carry most of a film |
| **Deep slow motion** (k ≥ 4, ramps, hang-and-snap) | About 1–2 moments per 15 s, 2–4 per 30 s, 4–6 per 60 s [heuristic] | Used as moments where it earns it: a pour, toss, splash, fabric, hair, a glance |
| Deep slow shot on screen | 1–3 s; hero up to ~4 s while something still changes [heuristic] | |
| Speed ramps | 1–2 per 15 s [heuristic] | Across a real event only |
| Hang-and-snap | 1 per 15 s [heuristic] | k 8–20 for 0.05–0.15 s of source around the peak |
| Ramp-down / ramp-up / snap | 6–10 f / 4–8 f / 2–4 f at 25p [heuristic] | Slow part starts 2–4 f before the event |
| Interpolating normal-speed (24/25/30p) footage | Allowed only per the decision table in `slow-motion.md` §5.1 | Low-risk subjects (architecture, steam, slow drape) up to 1.7× (speed ≥ 60 %) with any optical flow; higher factors or medium/high-risk subjects need an ML tool and a passing frame check; liquids, glass, hands crossing, flame at ≥ 2×: refuse by default |
| Repeated speeds | Never 3 deep-slow shots of the same speed in a row; never cut between two different slowdowns of the same subject | |
| Flicker under 50 Hz mains | 25/50/100p safe; 120/200/240p likely flicker | 60 Hz countries: 30/60/120 safe |

## 2. Shot lengths

| Item | Value | Notes |
|---|---|---|
| Shortest shot | **12 frames** (0.48 s @25) | Only for accents and breath inserts |
| One readable subject | ≥ 0.5 s (12 f @24/25, 15 f @30) | Short shots need motion inside them |
| Breath inserts (place/light details) | 12 f each, 2–3 between main shots | Allowed in food and restaurant films. ≥ 60 % of runtime stays on the main subject |
| Hotels and architecture | Prefer ≥ 1 s per shot | Sub-1 s cuts read restless in calm places |
| New place or person | ≥ 1.5 s (36 / 38 / 45 f @24/25/30) | |
| Locked architectural frame | ≥ 2.5 s | |
| Dead-air limit | ~3 s with nothing changing | Cure with motion in frame, not a cut for its own sake |
| Shot carrying text | 2 s or 0.5 s + 0.3 s per word, whichever is longer | |
| Final held shot / end card | ≥ 2 s; end card 1.5–2.5 s on the music's resolution | |
| Release after a fast build | ≥ 3× the last short shot | |

## 3. Rhythm (warnings, never targets)

Register ASL table (identical to `plan_check.py`):

| Register | ASL | Typical use |
|---|---|---|
| `luxury` | 2.5–5 s | luxury hotel, architecture, fine dining, high fashion |
| `premium` | 2–4 s | premium restaurant, boutique hotel, design product |
| `brand` | 1.2–2.5 s | general brand film, casual dining, lifestyle |
| `social` | 0.8–1.8 s | organic Reels/TikTok for a brand |
| `hype` | 0.4–1.2 s | fast food, nightlife, sport, events |

`reference.py` prints a rough word for a reference's rhythm ("premium/luxury", "lively social"); map its measured ASL onto this table, not its word.

| Heuristic | Value |
|---|---|
| Median shot | ≈ 0.55–0.7 × ASL |
| Variation | CV ≥ 0.3 |
| Longest shot | ≥ 2 × ASL |
| Last shot | longest or second longest |
| Same size/composition in a row | ≤ 3 |
| Cuts on a beat | 50–70 % |
| Consecutive every-beat cuts | ≤ 4 outside a marked build |
| Accents | 2–3 per film, ≤ 1 per 3 s |

These four rhythm rules together can force every film into one shape. Treat each as a warning: break it with a written reason.

## 4. Music timing

| Item | Value |
|---|---|
| On-beat window | A cut **0–2 frames before** the beat counts as on beat. A cut **≥ 2 frames after** the beat is late (flagged) unless marked deliberate |
| Structural turns | On 4- or 8-bar phrase starts |
| Bar sanity | One 4/4 bar lasts 1.6–3.2 s (75–150 BPM); otherwise suspect half/double tempo |
| Downbeats | A guess until a human confirms by ear |
| Frames per beat | `fps × 60 ÷ BPM` (120 BPM at 25p = 12.5 f) |

## 5. Finishing

| Item | Value | Notes |
|---|---|---|
| Straighten | Tilts of **0.2–15°** on lines that should be level or plumb → exactly 0°/90° | Except a strong, clearly deliberate Dutch angle |
| Straighten zoom | `k = cos θ + sin θ × (long side ÷ short side)` | 16:9: +3.1 % at 1°, +6.1 % at 2° |
| Pixel budget (effective upscale) | Hero, product, faces, close-ups ≤ 100 %; others ≤ 115 %; > 150 % **hard** fail | upscale = cover-fit × reframe zoom × straighten zoom × max push |
| Locked frames | **Default** | A locked frame is calm and premium |
| Digital push | 3–6 % over shots ≤ 3 s; 5–8 % over 4–6 s; eased; one direction | On **at most about 1/3 of shots**; never on a shot that already has a camera move |
| Stabilisation | Stabilise when gyro data (Gyroflow) or optical flow gives a clean result: ≤ ~110 % zoom at delivery resolution, no wobble in straight lines, no jello | Otherwise choose another window of the take, or drop the shot. Never warp-stabilise architecture |
| Natural drift to blend a locked shot | 1–3 px at 1080p, 0.5–1.5 Hz, ±0.1–0.2° | NLE only, rare |

## 6. Transitions and effects

| Item | Value |
|---|---|
| Default join | Hard cut |
| Time dissolve (time passing, day → night) | 12–24 f @24/25 (15–30 @30); at most 2 per film |
| Short dissolve (locked-frame object swap, two slow tonally close shots) | 4–8 f @24/25 |
| Signature tricks | 1–2 per 30 s in total |
| Stock whooshes, risers, impact hits | **0, hard** |
| White flashes, flash frames, light-flash bridges | **0, hard** |
| Template transitions (glitch, spin, slide packs, zoom-blur, light leaks, beat zoom pulses) | **0, hard** |
| Covering the lens with a hand as a transition | Not used; only real occluders in the scene (door, column, passing waiter, cloche) |
| Dark boxes, gradients, strokes or patches behind text | **0, hard** |
| Match-action offset | 0 f default; stylistic ≤ 4 f overlap/skip; never skip ≥ 1 s |

## 7. Sound

| Item | Value |
|---|---|
| Social/web master | −14 LUFS **±1 LU**, true peak ≤ −1 dBTP (render default −1.5) |
| Broadcast (EBU R128) | −23 LUFS ±0.5 LU, ≤ −1 dBTP |
| Foley under music | 10–20 dB below music peaks [heuristic]; 1–3 hero sounds a little harder |
| J/L cut | 6–12 f; sound bridge 0.5–1.5 s for a scene change |
| Mid-film silence | 0.5–2 s, films ≥ 20 s |
| Retimed shots | Sync sound dropped (hard) |

## 8. Text

| Item | Value |
|---|---|
| Default | Most films carry text **only on the end card** |
| Entrance | Simple opacity rise, 8–12 f (fixed title 12 f) |
| Read time | 0.5 s + 0.3 s per word after landing, ≥ 2 s |
| Text never moves while read | hard |

## 9. Colour checks

| Item | Value |
|---|---|
| Official transform active (same frame, LUT off vs on) | HSV saturation median rises ≥ 1.6×; darkest 1 % luma falls to 0–5 (RGB8) for S-Log3-like curves; 18 % grey lands at 40–46 % Y |
| LUT effectiveness | If p2–p98 spread and chroma barely move after the LUT, the picture is still log-flat: the LUT is wrong (look LUT, wrong camera, wrong curve). The LUT check FAILs it |
| Black point / white point | p0.5 at 2–5 %; p99.5 at 92–97 %, rolled off [heuristic] |
| Global saturation | 95–110 % [heuristic] |
| Skin (Lab hue) | [heuristic] Measure the subject's own skin; do not pull every face to one number. Rough ranges: light/rosy 38–47°, medium/olive 44–55°, deep 45–60°; chroma about 15–30. A hue well above the person's real tone reads jaundiced; well below reads sunburnt |
