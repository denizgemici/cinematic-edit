# Slow motion: frame rate first, then taste

Slow motion is central to this method: a clean second of high-frame-rate footage becomes two seconds and reads cinematic. Done badly (invented frames, slowing people who talk) it is also the fastest way to make a film look cheap. Read this before you set any `speed` below 1.0. Numbers marked **[heuristic]** are working values from practice, not published standards; everything else comes from a vendor document, published research, arithmetic, or our own ffmpeg tests. The shared numbers are collected in `numbers.md` §1.

## Contents
1. Frame rate first
2. Conform vs deep slow motion: premium and cheap
3. The clean second becomes two seconds (conform maths)
4. Speed ramps
5. 24/25/30 fps footage: interpolate or refuse
6. Checking interpolated frames
7. Sound in slow motion
8. Rules an agent can apply
9. Sources

---

## 1. Frame rate first

Check the frame rate of every clip **before any creative decision**. It decides what can become real slow motion.

**Three numbers per clip:**

| Number | What it is | Where it comes from |
|---|---|---|
| Container fps | How fast the file plays | `ffprobe` `r_frame_rate` / `avg_frame_rate` |
| Capture fps | How fast the sensor sampled | Camera metadata, Sony XML sidecar (`captureFps` vs `formatFps`), or measured motion |
| Timeline fps | The delivery rate | The brief: 25p in 50 Hz countries, 23.976/24 for cinema, 29.97/30 in 60 Hz countries |

The container rate alone can lie. Sony S&Q mode records, for example, 120 fps capture into a 25p file that already plays 4.8× slow, and it records no sound. A normal-rate clip with no audio track is therefore a hint that it is already slow.

Run `scripts/probe.py`. It prints an `FPS:` class per clip:

| `probe.py` class | Meaning | What to do |
|---|---|---|
| **in-camera slow motion** (Sony `captureFps` > `formatFps`) | Already slowed in camera | Use it at `speed: 1.0`. Do not slow it again by accident. Slowing further needs interpolation (section 5) |
| **high frame rate, not conformed** (≥ 47 fps) | Real slow-motion material | You choose the slowdown. Conform at the clean ratio (section 3) |
| **normal rate, NO AUDIO** | Possibly S&Q or a high-speed mode | Check motion: water, hair or hands that move unnaturally slowly at 1× mean it is already slow. Otherwise treat as normal speed |
| **normal speed** (23.976–30 fps with audio) | No real slow-motion frames | Use at 1×, or interpolate under the rules of section 5 |
| Variable frame rate warning | Phone footage | Conform to constant fps first (`setpts=N/(R*TB)`), check `nb_frames` before and after |

Then run `scripts/scan.py`. It reports `source_fps` and, for each best window, a `slow_motion` line: either the clean conform speed with the resulting timeline seconds, or "interpolation needed". Its `--min` default is **1.0 s of source**, because one clean second is enough material (section 3).

---

## 2. Conform vs deep slow motion: premium and cheap

Two different things share the name "slow motion":

| Kind | What | Quota |
|---|---|---|
| **Conformed slow motion** | High-frame-rate footage played at its clean conform ratio with a small factor, typically 50p at 50 % on a 25p timeline (k = 2) | **None.** Conformed 50p half-speed B-roll is normal premium material, not "wedding video". It can carry most of a film |
| **Deep slow motion** | k ≥ 4 (100p+ at 25 % or slower), speed ramps, hang-and-snap stop-and-go | Used as **moments**, where the event earns it (section 2.2) |

### 2.1 Earned moments for deep slow motion: physical events the eye cannot read at 1×

| Moment | Real duration | Why slow works |
|---|---|---|
| Pour, splash, drop into liquid, fizz | < 0.5 s | Liquid shape lives for milliseconds |
| Toss, ingredient fall, sauce flick, crumble | 0.05–0.5 s | Layers, texture and crunch become visible |
| Steam, smoke, flame | continuous | Volume and curl become readable |
| Fabric, hair, dress spin, veil | 0.5–1 s | Weight and drape |
| A glance, the onset of a smile, a breath | 0.3–1 s | Emotional micro-moment |
| Hands doing a precise step (plating, garnish, a pen nib) | 1–3 s | The viewer sees the craft |

**Never slow:** people talking (lip sync breaks, always wrong).
**Cheap in deep slow motion:** waiting, generic room B-roll, wide establishing shots, hand-held drift with no action, and any shot where nothing changes faster than about 0.5 s. These are fine at a gentle conform (50 % from 50p), not at 4× or in a hang. A fashion walk or turn is a pose and takes slow motion well. The "wedding video" look comes from interpolated, floaty deep slow motion on everything under soft piano, not from conformed 50p.

### 2.2 Deep slow motion: how long, how many [heuristic]

These limits apply to **deep** slow motion only (k ≥ 4, ramps, hangs). Conformed k = 2 footage is not counted.

| Film length | Deep slow moments (incl. ramps) |
|---|---|
| 15 s | 1–2 |
| 30 s | 2–4 |
| 60 s | 4–6 |

- **One deep slow shot on screen:** 1.0–3.0 s. A hero shot may hold up to 4 s, but only while something keeps changing (liquid still moving, fabric still falling).
- **No runtime share limit.** A film may be mostly conformed 50p; keep deep slow as moments so they still land.
- **Alternate** speeds: never put 3 deep-slow shots of the same speed back to back. Real-time shots between slow ones give the slow ones weight.
- **One main deep-slow speed per film** (for example 4×), and reserve the extreme factor (8–10×) for the single hero moment.
- **Hero moment:** the most important image (pour crown, product reveal, hero bite) sits in the slowest section and lands on a **downbeat** or after a silence or riser.
- A strong unit: real-time context → slow detail → real-time result (pour → crown splash → glass set down).
- Do not cut between two different slowdowns of the same subject; it reads as an error.

### 2.3 The luxury evidence, with its caveat

Jung & Dubois (*Journal of Marketing Research*, 2023; 12 experiments, about 27,000 participants in the US, UK and France) found that the same product shown in slow motion was rated more luxurious, raised willingness to pay and purchase intention, and the wine was even rated more luxurious after tasting. The mechanism is **immersion**.

**Caveats that matter for editing:**
- Blur or buffering weakens the effect because it breaks immersion. Smeared, badly interpolated slow motion therefore likely loses the benefit.
- Purchase intention rose only when an indulgence or self-reward goal was present: pair slow motion with indulgent copy and music.
- The effect vanished for viewers with very low or very high absorption tendency.
- Public summaries give no slowdown factor or effect size. Do not quote a "best speed" from this paper.

---

## 3. The clean second becomes two seconds (conform maths)

A clean, beautiful second of a raw take (sharp, steady, the action at its peak) can become **2 seconds or more** on the timeline and read cinematic. Do not reject a take because its usable part is short; take the clean second and slow it.

**Conform** means every captured frame plays once at the timeline rate: speed = timeline fps ÷ capture fps. Nothing is dropped or invented, so it is always smooth.

**Conform table** (speed %, and timeline seconds from **1 s** of source):

| Capture fps | 23.976/24 timeline | 25 timeline | 29.97/30 timeline |
|---|---|---|---|
| 50 | 48 % → 2.08 s | **50 % → 2.00 s** | 60 % → 1.67 s |
| 59.94/60 | **40 % → 2.50 s** | 41.7 % → 2.40 s | **50 % → 2.00 s** |
| 100 | 24 % → 4.17 s | **25 % → 4.00 s** | 30 % → 3.33 s |
| 119.88/120 | **20 % → 5.00 s** | 20.8 % → 4.80 s | **25 % → 4.00 s** |
| 200 | 12 % → 8.33 s | **12.5 % → 8.00 s** | 15 % → 6.67 s |
| 239.76/240 | **10 % → 10.0 s** | 10.4 % → 9.60 s | **12.5 % → 8.00 s** |

**Gentler than full conform** is allowed when it keeps every k-th frame with k a whole number: speed = k × (timeline ÷ capture). Example: 100p on 25p at `speed: 0.5` takes every 2nd frame → 1 s becomes 2 s, still smooth. 120p on 25p at 0.5 gives k = 2.4 (uneven drops, judder); use 0.417 (k = 2, 2.4 s) or the full 0.208 instead. `plan_check.py` warns when a speed is not a clean ratio; set `"optical_flow_ok": true` only after you have checked an interpolated result frame by frame.

**Do not slow beyond capture ÷ timeline** without interpolation. 50p on 25p gives at most 2×; asking for 25 % means inventing every second frame (section 5).

**50 Hz flicker** (mains lights pulse 100 times per second in 50 Hz countries):

| Capture fps | Under ordinary mains light |
|---|---|
| 25, 50, 100 | Safe (divides 100) |
| 120, 200, 240 | Flicker likely. Needs flicker-free LED, daylight, DC or HMI with a high-frequency ballast |

The longest exposure at 120 fps is 1/120 s, shorter than one 1/100 s light cycle, so no shutter fixes it. Detect flicker as a periodic oscillation of mean luma in a static area; fix with a deflicker tool or reject the shot. In 60 Hz countries the safe family is 30/60/120.

**Shutter check:** 180° (1/(2×fps)) looks natural when conformed. A long exposure at high fps (100p at 1/100) smears in slow motion; a very short exposure (1/2000) played at 1× looks staccato.

**Grade high-fps clips as their own group:** high-speed modes often crop, read a lower resolution (some 1080/240 modes read well under 1080 lines) or drop bit depth. Check them at 100 % against neighbouring shots.

---

## 4. Speed ramps

A ramp is real time → slow at the peak → back out, inside one shot. Ramp **across a real event**, never across nothing. At most 1–2 ramps per 15 s in premium work [heuristic].

| Parameter | Default at 25p [heuristic] | Notes |
|---|---|---|
| Ramp-down (1× → slow) | 6–10 frames (0.24–0.4 s) | < 4 frames reads as a jump; > 12 feels floaty |
| Slow hold | 1–3 s on screen | Covers the physical peak (crown, apex, impact) |
| Ramp-up (slow → 1× or faster) | 4–8 frames | May overshoot to 1.5–3× to snap out into the cut |
| Curve | Ease in-out (smoothstep) on speed | Linear ramps show a kink at both ends |
| Start of slow hold | 2–4 frames **before** the event | The contact or impact must be fully inside the slow part |
| Music | Event on a downbeat; ramp-down starts one beat before | 120 BPM = 12.5 frames per beat at 25p |
| Direction | Bridges into the next shot | Slow → fast into a cut on action |

**Source rule:** the slow hold needs native high-fps frames (100p for 4× on 25p). The real-time parts then use every 4th frame, which has a crisp short-shutter look; add a little motion blur there if it strobes.

**In the plan:** give the shot a `"ramp": [[source_s, k], ...]` instead of `speed`. Times are source seconds from the shot's `in` point; k is the slowdown (1 = real time, 4 = quarter speed, 0.5 = double speed). `render.py` eases between keys with smoothstep and maps every source frame by the exact integral T(t) = ∫k dt, so screen time = Σ (k_a + k_b)/2 × gap. Tested: predicted 198 frames, rendered 198. `plan_check.py` warns when the last key ≠ `out − in`, and when the ramp's max k exceeds the clip's real frames.

**Frame budget:** real frames per source second = capture fps; each one is shown for k/capture seconds. Clean as long as k ≤ capture ÷ timeline (4 for 100p into 25p, 2 for 50p, 4.8 for 120p). Above that, either set `"interpolate": true` and check every frame (section 6), or accept a deliberate frame hold (each real frame repeats; reads as a stutter-stop, which can be a style on a near-stop hang but never by accident).

### 4.1 Ramp patterns (keys for 100p on a 25p timeline, peak at source 0.9 s)

| Pattern | Keys | Screen time | Use for |
|---|---|---|---|
| **(a) Classic** real → slow → real | `[[0,1],[0.8,1],[1.1,4],[1.6,4],[1.9,1],[2.6,1]]` | 5.0 s | A pour, a plating step, a walk-in reveal. The default ramp |
| **(b) Hang and snap**: near-stop at the peak, then snap back | `[[0,1],[0.7,1],[0.85,12],[0.95,12],[0.97,1],[1.5,1]]` | 3.5 s (hang 1.2 s, snap ≈ 3 frames) | Fries at the top of a toss, a splash crown, fabric at full spread, hair at the top of a turn |
| **(c) Fast-in → hang** | `[[0,0.5],[0.6,0.5],[0.75,8],[0.95,8],[0.98,1],[1.4,1]]` | 3.1 s | Energy films: rush into the moment at 2×, freeze it, release |
| **(d) Speed wave across a beat** | `[[0,1],[0.3,3],[0.6,3],[0.65,0.5],[1.0,0.5],[1.1,1],[1.5,1]]` | 2.24 s (snap at screen 1.50–1.59 s) | Music films: slow before the beat, snap to fast **on the downbeat**; place the shot so screen 1.50 s lands on the beat |

- **Snap:** the k drop happens over a very short key gap (0.02–0.05 s of source) so the transition lasts **2–4 timeline frames**. Shorter reads as a glitch; longer loses the snap. Duration of a transition = (k_a + k_b)/2 × gap.
- **Hang:** k 8–20 for only a few source frames (0.05–0.15 s) around the peak. At k 12 on 100p each real frame covers 3 timeline frames, so the hang needs interpolation or is an intended frame hold. With 200/240p capture a k 8–10 hang is clean.
- Put the peak 2–4 timeline frames inside the hang, and the snap (or the hang start) on a downbeat. One hang per 15 s; it is the hero gesture, not a habit [heuristic].
- On 24/25/30 fps sources, any k > 1 is invented frames: patterns (b) and (c) are refused on high-risk subjects unless the frame check passes (section 5).

**Outside `render.py`:** the same integral works as one ffmpeg `setpts` expression (`setpts='T(t)'/TB,fps=25`, a nested `if(lt(t,b),segment,…)` of the closed form `T = T_a + k_a·(t−a) + (k_b−k_a)·L·(u³ − u⁴/2)`, u = (t−a)/L). Verify measured frames = round(screen seconds × fps) ± 1 with `ffprobe -count_frames`.

---

## 5. 24/25/30 fps footage: interpolate or refuse

Normal-fps footage has no slow-motion frames. Slowing it means a program **invents** frames. Before interpolating, always offer a real high-fps clip of the same moment if one exists.

### 5.1 Decision table

Factor = slowdown beyond what capture gives (25p at 50 % on a 25p timeline = 2×).

| Interpolation factor | Low risk: architecture, slow camera move, slow fabric drape, steam | Medium: faces at rest, a slow glance, hair, fabric in motion, slow hands | High: liquids, pours, splashes, glass and reflections, hands crossing, flame, whip pans |
|---|---|---|---|
| ≤ 1.7× (speed ≥ 60 %) | Any optical flow, even ffmpeg `minterpolate` | Dedicated ML tool, then check | ML tool and strict check; otherwise keep 1× |
| 2× (50 %) | ML tool (Topaz Apollo, Speed Warp, FCP Best, RIFE) | Topaz Apollo or Speed Warp Better, strict check | **Refuse by default.** Allow only if the check passes and the user approves a viewed sample |
| 4× (25 %) | Topaz Apollo/Aion or Speed Warp Better, strict check | Topaz Aion, strict check | **Refuse** |
| > 4× | Topaz Aion only, shot ≤ 2 s | **Refuse** unless the check passes and the user signs off | **Refuse** |

**Refuse any shot (keep it real time) when:** the subject is already motion-blurred in the source; it crosses more than about 5 % of the frame width per source frame; a cut, flash or strobe lies inside the segment; the check flags more than 2 bad frames per output second; or any artefact touches the product or logo on a hero shot.

**Why these subjects fail:** interpolators guess motion. They break on occlusion (hands crossing, revealed background), thin structures (wires, fries, herbs), transparency and reflections (two motions in one pixel), and shapes with no frame-to-frame correspondence (flame, splash). Our own test: 50 fps footage slowed to 25 % with ffmpeg `minterpolate` was usable overall, but falling fries showed ghosting and smearing on the fast thin pieces.

### 5.2 Tools

| Tool | Quality | Price / licence | Platform | Use for |
|---|---|---|---|---|
| **Topaz Video (AI)**: Apollo (2×/4×/8×), Chronos (≤ 4×), Aion (large motion, highest, slowest) | High | Commercial subscription (check current price) | macOS (Apple silicon), Windows; cloud | Hero shots, high factors. Removes audio: keep it separately |
| **DaVinci Resolve Studio: Speed Warp** (Better/Faster) | High | Paid one-time licence | macOS, Windows, Linux | Hero shots in a Resolve pipeline. Render cache to judge |
| **Resolve (free): Optical Flow Enhanced** | Medium | Free | same | Low-risk shots |
| **Final Cut Pro: Best (Machine Learning) / Smooth Slo-Mo** | High | One-time purchase | macOS, Apple silicon only | Hero shots on a Mac |
| **Premiere Pro: Optical Flow** | Medium | Creative Cloud subscription | macOS, Windows | Simple motion; render to judge; ramps with optical flow are unreliable by user reports, test first |
| **RIFE** (Practical-RIFE; **rife-ncnn-vulkan** CLI) | High for its speed | Code MIT; check model weight terms | Python/PyTorch; ncnn binaries for Windows, Linux, macOS | Scriptable free option |
| **Flowframes** (GUI over RIFE) | as RIFE | Free, donation | Windows only | Non-technical users on Windows |
| **Google FILM** | Strong on large motion, slow | Apache-2.0; repository archived (no maintenance) | Python/TensorFlow | Research or a fallback |
| **Apple VTFrameProcessor** (Frame Rate Conversion) | Unmeasured; Apple shows demos only | Free, part of the OS | macOS 15.4+, needs a small Swift helper | Native Mac pipeline |
| **ffmpeg `minterpolate`** (what `render.py` uses with `"interpolate": true`) | Low–medium: block halos, edge tearing, ghosting on fast thin objects | Free | Everywhere | Drafts, previews and low-risk shots only |

Recommended order on a Mac: Topaz (if licensed) → Resolve Studio Speed Warp → FCP Best → RIFE → `minterpolate` for low-risk or draft only.

### 5.3 `minterpolate` recipe and its end-frame loss

`render.py` with `"interpolate": true` runs `minterpolate` (mi_mode=mci, mc_mode=aobmc, me_mode=bidir, vsbmc=1) to fps ÷ speed before `setpts`; without it, a slowed low-fps shot repeats frames and `render.py` warns about judder. `minterpolate` loses frames at the ends of a clip (50 source frames at 4× gave 193 instead of 200). When you need an exact count, pad and trim:

```bash
# 25p -> 4x slow on 25p: exactly 200 frames from 50
ffmpeg -i in_25p.mov -vf "minterpolate=fps=100:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1:scd=fdiff,\
setpts=N/(25*TB),tpad=stop_mode=clone:stop=16,trim=end_frame=200,setpts=N/(25*TB)" -an -c:v prores_ks -profile:v 3 out.mov
```

Pad by at least 4 × factor frames, then trim to round(seconds × fps). Encode intermediates as ProRes, not long-GOP H.264. Check that your ffmpeg has `minterpolate`, `setpts` and `tpad` (`ffmpeg -filters`); some bundled builds lack them.

### 5.4 What to tell the user

Say it in one short paragraph, in the user's language, with fps, factor, subject risk, **one** recommendation and at most one fallback. Template:

> "This clip was shot at 25 fps, so it has no real slow-motion frames. Slowing it to 50 % means inventing every second frame, and a pour into glass is the hardest case for that. I recommend keeping this shot in real time and putting the slow-motion beat on clip C0123, which was shot at 100 fps. If you want this one slow anyway, use Topaz Video (Apollo) or DaVinci Resolve Studio Speed Warp (both paid); free options are RIFE or Resolve's Optical Flow, which are weaker on liquid. I will render a 2-second test and show you the worst frames before it goes in the film."

Name a paid tool only if the user has it, or say that it is paid. For future shoots, recommend 50/100 fps on 25p projects (60/120 on 30p).

---

## 6. Checking interpolated frames

Every interpolated or retimed shot is checked frame by frame before anyone sees the film.

1. **`qc.py` on the render.** "Duplicated frames inside moving shots" means judder from a bad conform or a missing `interpolate`. "Sudden picture jumps inside shots" means an interpolation tear, warp or flash frame. Fix both.
2. **Frame-by-frame sheet of each slow shot.** Make a contact sheet of every frame (or every 2nd) of the slowed section and look at it at full size. Look for:
   - edges that bend or tear (hands, fingers, glass rims, cutlery, fries, herbs);
   - ghost doubles or halos around moving objects;
   - liquid that smears into a blob or loses its droplets;
   - reflections and highlights that swim or strobe;
   - faces: eyes, teeth and hairlines that wobble;
   - sharpness pulsing (invented frames softer than real ones, in a rhythm matching the factor);
   - backgrounds that ripple where a foreground object passes.
3. **Difference curve** (optional, numeric): `ffmpeg -i shot.mov -vf "tblend=all_mode=difference,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=diff.txt" -f null -`. Flag frames above 2.5 × the rolling median [heuristic], and a saw-tooth whose period equals the factor.
4. **Round-trip test** (most honest): drop a real frame B between A and C, interpolate B' from A and C, compare B with B'. Low similarity on the subject (SSIM below about 0.90 [heuristic]) means the tool will fail on this shot at higher factors.
5. **Independent critic:** give the worst frames to the critic agent with the shot-judging prompt.

**Refuse and fall back** when any artefact is visible on the product, the logo, a face or the hero action, or when more than 2 frames per output second are bad. Fallbacks, in order: a real high-fps take of the same moment; the same shot at 1× (trimmed to its best second); a gentler speed (70–80 %); a slow digital push instead of slow motion. A clean real-time shot always beats a smeared slow one.

---

## 7. Sound in slow motion

Full rules: `sound-music.md` §6. In short:

- **Never** let speed-changed sync sound through. `render.py` keeps a shot's real sound (`sound_db`) only for shots at `speed: 1.0`; slowed shots are silent unless you design sound for them.
- Never stretch dialogue; never slow a person talking.
- In the slow section, let the music carry it, or duck the ambience 6–12 dB and place **one** believable hero sound (the pour, the crunch) on the visual peak, at real pitch or pitched down about an octave. No stacks of generic whooshes.
- Cut back to real time with real sound: the room "rushes back in". That contrast makes the slow moment feel premium.
- Real-time cuts sit on beats; a slow shot spans one or two bars; the hero peak lands on a downbeat.

---

## 8. Rules an agent can apply

1. Run `probe.py` on every clip before any creative decision. Record container fps, capture fps, timeline fps and audio presence.
2. Treat a clip classed "in-camera slow motion" as already slow; use it at `speed: 1.0`.
3. Treat a normal-rate clip with no audio as possibly slow; confirm by looking at motion.
4. For each high-fps clip, write down the clean conform speed (timeline ÷ capture) and the timeline seconds per source second.
5. Conform high-frame-rate B-roll freely (50p at 50 % on 25p has no quota). Use deep slow motion (k ≥ 4, ramps, hangs) only on physical events faster than about 0.5 s (pour, toss, splash, steam, flame, fabric, hair, a glance, a precise hand step). Never slow people talking.
6. Use 1 clean second of source as enough material; with 50p on 25p it becomes 2 s, with 100p 4 s.
7. Set speeds only to clean ratios: speed = k × timeline ÷ capture with whole-number k. Resolve every `plan_check.py` ratio warning.
8. Keep each deep slow shot at 1–3 s on screen (hero ≤ 4 s with continuous change).
9. Keep deep slow motion to about 1–2 moments per 15 s, 2–4 per 30 s, 4–6 per 60 s. Conformed k = 2 footage does not count. Break this with a written reason when the event earns it.
10. Never 3 deep-slow shots of the same speed in a row.
11. Use one main deep-slow speed per film and keep the extreme factor for the single hero moment.
12. Put the hero moment in the slowest section, on a downbeat.
13. Under 50 Hz light, check 120/200/240 fps clips for flicker; deflicker or reject.
14. Build ramps with the plan's `ramp` keys: ramp-down 6–10 frames, hold 1–3 s, ramp-up 4–8 frames, slow part starting 2–4 frames before the event; for a hang and snap, k 8–20 for a few source frames and a snap of 2–4 timeline frames. Keep max k ≤ capture ÷ timeline or interpolate and check. Last key = `out − in`.
15. On 24/25/30 fps footage, first look for a real high-fps alternative; then apply the decision table in 5.1. If it says refuse, keep real time.
16. Use `"interpolate": true` (ffmpeg `minterpolate`) only for drafts and low-risk shots; recommend Topaz, Resolve Studio Speed Warp, FCP Best or RIFE for hero shots.
17. Set `"optical_flow_ok": true` only after you have looked at every interpolated frame.
18. Run `qc.py` on every render; fix duplicated frames and picture jumps inside slowed shots.
19. Reject any interpolated shot with an artefact on the product, logo, a face or the hero action.
20. Drop sync sound on slowed shots; design one hero sound or let the music carry it.
21. Give the user one short recommendation paragraph (5.4) whenever slow motion needs interpolation.
22. Watch the finished film once at 1×. Remove any slow shot that can go without losing information or emotion.

---

## 9. Sources

- Jung & Dubois, "When and How Slow Motion Makes Products More Luxurious", *Journal of Marketing Research* 60(6), 2023, doi:10.1177/00222437221146728; summary: https://knowledge.insead.edu/marketing/how-slow-motion-video-ads-make-products-more-luxurious
- Shoot Online, high-speed shooting: https://www.shootonline.com/spw/high-speed-shooting-why-and-how/
- No Film School, slow-motion do's and don'ts: https://nofilmschool.com/2018/06/5-things-you-should-and-shouldnt-do-when-shooting-slow-motion
- Frame.io, mixed frame rates: https://blog.frame.io/2019/10/17/mixed-frame-rates-part-3/
- RED, flicker-free video: https://www.reddigitalcinema.com/red-101/flicker-free-video-tutorial
- Sony S&Q help guide: https://helpguide.sony.net/ilc/2050/v1/en/contents/TP1000189492.html
- Apple, Final Cut Pro speed and video quality: https://support.apple.com/guide/final-cut-pro/ver40b00150/mac
- Topaz, frame interpolation docs: https://docs.topazlabs.com/topaz-video/filters/frame-interpolation
- rife-ncnn-vulkan: https://github.com/nihui/rife-ncnn-vulkan ; Practical-RIFE: https://github.com/hzwer/Practical-RIFE
- Google FILM: https://github.com/google-research/frame-interpolation
- Apple WWDC25 session 300 (VTFrameProcessor): https://developer.apple.com/videos/play/wwdc2025/300/
- FFmpeg filters (`minterpolate`, `setpts`, `tpad`): https://ffmpeg.org/ffmpeg-filters.html
- Boom Box Post, slow-motion sound effects: https://boombox-post.squarespace.com/blog/2017/10/26/lunch-and-learn-sound-effects-editing-slo-mo
- Benchmarking video frame interpolation (failure on large motion and occlusion): https://arxiv.org/abs/2403.17128
