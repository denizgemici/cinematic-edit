# Cinematic tricks: premium vs cheap

Contents: 1 How to use tricks · 2 Editing tricks · 3 Post camera moves · 4 Look · 5 Sound · 6 Shoot tricks to recommend · 7 Avoid · 8 Top 20 · Sources

Frame maths used below: 12 f = 0.5 s at 24 fps, 0.48 s at 25, 0.4 s at 30. Numbers marked *(start)* are starting points to test on the real footage, not laws. Shared numbers (push, dissolves, ramps, the closed doors on whooshes and flashes) are in `numbers.md`.

## 1. How to use tricks

"Cinematic" comes from light, composition, staging and story. A trick can only support an image that already works; it cannot rescue a weak one.

- **Taste rules (these override popular tutorials):**
  - Restraint reads premium. The hard cut is the default join.
  - Effects are barely there. If a viewer can name the effect, it is too strong.
  - If the viewer notices the trick before the image, remove the trick.
  - Every trick must be motivated by the image: a real object, a real movement, a real light source.
  - One idea per film. Never repeat the same signature trick in one film.
  - Deep slow motion (k ≥ 4, ramps, hangs) only on physical events (pour, drop, steam, flame, fabric, toss), as moments. Conformed 50p at half speed is ordinary material, not a trick (`slow-motion.md` §2).
  - Never fake smoke, fake light leaks or AI-looking polish. No dark boxes or blotches behind text.
- **Budget per 30 s:** 1–2 signature tricks in total (for example one match cut with meaning plus one speed ramp). Everything else is straight cuts, split edits (J/L) and cuts on action. These invisible tools have no budget.
- **No stacking.** Never combine a ramp with a flash, shake, zoom-blur or whoosh on the same cut.
- **Intent test.** Before adding a trick, write one line: "this makes the viewer feel/understand ___". If the only answer is "it looks cool", drop it. Log the line in the shot's `reason`.
- **Two-pass check.** Watch the cut once without sound and once without picture. If the picture pass relies on effects, or the sound pass is music alone, revise.

## 2. Editing tricks that read premium

### 2.1 Cut on action (match on action)
- **What:** cut from shot A to shot B in the middle of one movement, so two takes read as one continuous action.
- **When:** all genres. Pours, slicing, plating, a turn, a door opening, a hand placing a glass.
- **Recipe:** set A's `out` 2–4 frames after the movement starts its fastest phase; set B's `in` on the same phase of the movement *(start)*. The moving part (hand, head, bottle neck) sits in the same screen area on both sides. Use `transition: "cut"`.
- **Fails when:** the movement restarts on B (a visible repeat) or jumps backwards; or the moving part changes screen side and the eye has to search.

### 2.2 Graphic match cut with meaning
- **What:** a cut between two shots that share shape, line, colour or idea: a round plate to a round lamp, a glass rim to an arch, melted butter to a golden sauce, a menu photo to the real dish.
- **When:** food (ingredient → dish), hotel/architecture (shape → detail), fashion (silhouette, colour), product (form → origin). Limit to 1–2 per film.
- **Recipe:** put the shared shape in the same screen position at a similar size. Align with `reframe {x, y, zoom}`; keep `zoom` ≤ 1.10 and within the pixel budget (`finishing.md`). Cut on the frame where both shapes are cleanest. Hard cut; a 4–8 f dissolve only if both shots are slow.
- **Fails when:** the link is only decorative, the shapes don't actually overlap on screen, or a transition-pack "match" fakes it. A colour/material chain (terracotta → shadow → water → bronze) at ~2 s per shot is the calmest form of this trick.

### 2.3 Natural occluder wipe
- **What:** something real in the place fills the frame (a column, door leaf, waiter's back, a lifted menu or cloche), and the next shot begins behind a similar obstruction.
- **When:** hotel and architecture (pillars, doors), restaurant (staff passing, a cloche lifted), fashion (model crosses frame).
- **Recipe:** cut on the frame where the occluder covers ≥ 90% of shot A, and start shot B with its own occluder leaving. For a masked reveal (NLE, Remotion or HyperFrames): track the occluder's edge, feather 5–15 px at 4K, animate the mask with the object.
- **Fails when:** the occluder is a hand slapped over the lens, the two movements go in different directions, or the mask edge chatters.

### 2.4 Hidden cut on motion blur
- **What:** cut inside the blur of two camera moves in the same direction; the viewer reads it like a blink.
- **When:** only when two shots really contain fast moves in the same direction. At most once per film.
- **Recipe:** cut on the most blurred frame of each move. Both moves go the same way at similar speed. Never build a synthetic whip (500% scale + directional blur) on a locked shot.
- **Fails when:** directions differ, one side is sharp, or it becomes a recurring transition.

### 2.5 Locked frame, changing subject
- **What:** the camera never moves; the change happens inside the frame. The same table gets a new plate every ~2 s, the same corridor gets a new guest, a glass changes on the same spot of the bar, a table sets itself.
- **When:** food, bar, hotel interiors, people series. One of the calmest and most premium structures.
- **Recipe:** shoot (or select) shots with the same position and lens; join with hard cuts, or `dissolve:4`–`dissolve:8` when the object changes on its mark. About 45–60 f per state at 24 fps. Any title stays fixed in one place while the shots change underneath it.
- **Fails when:** the frames are not truly matched (a jitter at every change), or the series runs past 4–5 states without a turn at the end.

### 2.6 Focus reveal
- **What:** a soft frame (or a blurred sign or menu) sharpens into the subject.
- **When:** product, food, hotel by the sea, an opening shot.
- **Recipe:** use a real rack focus from the camera. Choose the window so focus lands 0.5–1 s after the cut *(start)*. Never fake it with a blur keyframe on a sharp shot.
- **Fails when:** the focus hunts (back and forth) or the soft part lasts longer than ~1.5 s.

### 2.7 Insert rhythm: wide → detail → detail → wide
- **What:** cut from the establishing frame to details of the same scene and back.
- **When:** always in food and product; also in hotels (room → linen → handle → room with view).
- **Recipe:** plain cuts. Detail shots 1–2 s, wides 2–3 s for calm brands. Order details from cause to result (raw → knife → heat → steam → plate).
- **Fails when:** four shots in a row share the same size and angle, or the order breaks cause and effect (served before cooked).

### 2.8 Speed ramp on one real event
- **What:** real time into slow motion through the peak of one action, then back.
- **When:** food (pour, cheese pull, sauce drop, toss), fashion (turn, hair, fabric), product (reveal). Rarely in hotels. About 1–2 per 15 s (`numbers.md` §1), where the event earns it.
- **Recipe:** source should be high frame rate (50/60/100/120 fps). `render.py` does smooth ramps with the shot field `"ramp": [[source_s, k], ...]` (k = slowdown factor, smoothstep between keys, exact frame maths), e.g. `[[0,1],[1.0,1],[1.3,4],[2.3,4],[2.6,1],[4.0,1]]`: real time → ease to quarter speed over 0.3 s → hold through the peak → back. A near-stop "hang" then a snap back (k 8–20 at the peak, 2–4 frame key gap on the way out) is valuable; it needs interpolation or a deliberate frame hold when k exceeds capture fps ÷ timeline fps. Patterns and frame budgets: `slow-motion.md`. In an NLE: Premiere Time Remapping with split bezier handles, Resolve Retime curve.
- **Fails when:** applied to stillness, to shaky footage (shake gets obvious), to interpolated 24/25 fps footage on fast occluded motion (warping), or combined with flash/shake/whoosh.

### 2.9 Dissolve as time, not as a join
- **What:** a slow dissolve that says "time passed" (morning → evening, the same room in different light) or joins two very slow shots.
- **When:** hotel and architecture, calm hospitality. Not as a default join anywhere.
- **Recipe:** `transition: "dissolve:12"` to `"dissolve:24"` at 24/25 fps (`dissolve:15`–`30` at 30 fps). Both shots slow and tonally close. At most 2 per film.
- **Fails when:** a dissolve sits where a cut belonged (editors flag this as amateur), or between two fast shots (muddy double image).

### 2.10 One contrast cut as the turn
- **What:** a deliberate jump from quiet to loud, or stillness to motion: a calm morning sequence ends in silence, then the kitchen fire and sizzle.
- **When:** once per film, at the structural turn, on a phrase start in the music.
- **Recipe:** hard cut. Drop the music 0.5–1 s before; let the real sound of shot B carry the hit.
- **Fails when:** used twice, or when the "loud" shot is weaker than the quiet ones.

### 2.11 People: cut on the blink or gesture end
- **Recipe:** in people shots, cut on a blink, a glance-away or the end of a gesture; never mid-expression or mid-word. Fashion only: beat-locked jump cuts on a locked frame where the pose changes.
- **Fails when:** a jump cut happens in a talking or fidgeting moment, or framing drifts between the jumps.

## 3. Post camera-move tricks

- **Locked frames first.** The locked frame is the default. A push on every static shot is the recognisable Ken Burns look of AI edits.
- **Eased push-in.** 3–6 % (`push: [1.00, 1.04]`) on shots ≤ 3 s, 5–8 % (`[1.00, 1.05]`–`[1.00, 1.08]`) on 4–6 s shots (render.py eases it); on at most about a third of the shots (`numbers.md` §5). One direction per shot. Only on static shots that need emphasis. Stay within the pixel budget: on 4K → 1080 up to 2× is lossless; on 4K → 4K any push is upscaling, so keep it ≤ 1.04 or skip it. A linear zoom feels digital; a fast "crash zoom" is banned.
- **Carry the push.** If a push leads into the next shot, the next shot continues the motion or is a static close-up of the destination. A push that stops dead at a cut looks broken.
- **Pull-out** (`push: [1.06, 1.00]`) suggests detachment or an ending; use for a final wide, not mid-film.
- **Parallax (2.5D) only if layers exist.** Use it only on stills that separate cleanly (a window frame against a bay, a product against a plain wall) or on real layered artwork. Travel stays small: far layer ~0.5 px/frame, near layer ~2 px/frame at 24 fps over 6–8 s *(start)*. If an edge stretches or tears, drop it. Never fake depth on video.
- **No fake shake on premium work.** No impact shakes, no handheld presets on beats. The only exception is a barely felt drift (1–3 px at 1080p, 0.5–1.5 Hz, ±0.1–0.2°) to blend one locked shot into a handheld sequence, and only in the NLE.
- **Stabilise without warping.** Stabilise only when the result is clean (`numbers.md` §5). On architecture, never use a warping stabiliser (Subspace Warp bends straight lines). If stabilising needs more than ~110% scale at delivery resolution, take another window or reject the shot. Straighten verticals and horizons to exactly 0°/90° (`straighten`, see `finishing.md`).

## 4. Look tricks

Order: correct → motivated grade → slight softening → uniform grain → halation on highlights. Never sharpen. Details in `colour.md`.

- **Letterbox (2.39:1) only when framed for it.** Use it only on horizontal films where every shot was composed (or re-composed with `reframe`) for scope, never on 9:16, never as bars dropped over 16:9 framing. In 1920×1080, 2.39:1 is a 1920×804 picture with 138 px bars (ffmpeg on the finished timeline: `crop=1920:804,pad=1920:1080:0:138`). Better: deliver a true 1920×804 file if the platform allows.
- **Grain, felt not seen.** Apply it once on the whole timeline, same grain on every shot, never per shot. In the NLE: set size, then strength, then lower opacity to ~30%. With ffmpeg on the final timeline: `noise=c0s=3:c0f=t` (luma only, temporal), test 2–5 *(start)*. Check at 100% on a phone. If you see it dancing in the shadows, halve it.
- **Halation and diffusion, felt not seen.** Only on practicals and speculars: candles, lamps, sun on glass, wet food highlights. Small radius, warm red. If it shows on midtones or skin, it is too strong. Do it in the NLE (Resolve Halation/Scatter, Dehancer), not with an ffmpeg blur over the whole frame.
- **Softness over sharpness.** A very slight blur before grain is allowed; added sharpening never is.
- **Colour as a move, only if the footage was shot for it.** Black-and-white process → colour at the hero plate works only when the shoot or brief was designed around it; as a found effect it is a cliché. At most once or twice, and only with the change inside an action (as a fork lifts).
- **Motivated colour.** No global teal/orange LUT. Grade from the real light; protect skin, greens and reds in food.

## 5. Sound tricks

- **Sound bridge (J-cut).** The next scene's ambience or action sound starts 0.5–1.5 s before its picture, with a 6–12 f audio crossfade *(start)*. This is the most premium-feeling invisible trick: sea leads the terrace, sizzle leads the pan, a lobby murmur leads the lobby.
- **L-cut.** The previous sound carries over the new picture to tie two places together (a pour sound continuing over the table).
- **In this toolchain:** `render.py` mixes `sound_db` shot sound in sync, only on shots at `speed: 1.0`, with 40/80 ms fades. Build J/L cuts in the NLE (export with `export_xml.py`) or in Remotion/HyperFrames by offsetting the audio start.
- **Silence before the hero.** Drop or thin the music for 0.5–1 s before the hero shot; let a single real sound (cork, knife, latch) land on the hero frame.
- **Real foley above the music** on hero moments: sizzle, crunch, pour, knife, fabric, a door latch. Record it on set or use the shot's own sound. No stock whooshes, risers or "whoosh-boom" hits at all.
- **Continuous bed.** A room tone or ambience bed (sea, birds, distant room) runs under the whole hotel film; no hard holes in the ambience at cuts.
- **Slow-motion sound.** On the single slow-motion moment, a pitched-down or designed sound reads better than the real-time sound played slow.
- Music choice, loudness and ducking: `sound-music.md`.

## 6. Shoot tricks to recommend for the next shoot

When the footage limits the edit, write these into the report as recommendations for the next shoot:

| Trick | Setup | Why |
|---|---|---|
| Film into the shadow side | Key light from the side/back of the subject, camera on the darker side; no flat front light | Texture, steam and depth; the single biggest "expensive" factor |
| Backlight for food | Light behind the plate or glass, small fill or reflector | Shows steam, syrup, sugar, bubbles |
| Foreground framing | Plant, glass, door frame, curtain or hand close to the lens, subject behind | Depth and natural occluders for wipes (2.3) |
| Planned reveals | Pull back through a doorway, move around a column, lift a cloche, open a curtain | Real reveals beat any digital transition |
| High frame rate for planned slow motion | 100/120 fps (50 fps for gentle) for pours, splashes, fabric, hair; shutter about 1/(2×fps) | Clean slow motion with no interpolation |
| Locked frames for structures | Tripod, same position and lens for each state | Enables 2.5 locked-frame series and title-over-shots films |
| Macro | Macro lens (+ turntable for product) for texture, droplets, grain of fabric | Detail shots for the insert rhythm |
| Slow motivated moves | One slow push or slide per space; slower in bedrooms | Real parallax, no post zoom needed |
| Practicals in frame | Lamps and candles on, windows held (not blown) | Motivates warmth and halation |
| 180° shutter + ND | 1/50 at 25 fps, 1/48 at 24; ND outdoors | Natural motion blur; no flicker under 50 Hz light |
| Clean handles | 2 s before and after every action; matching moves shot in both directions | Room for cut on action and match cuts |
| Room tone | ≥ 30 s per location, plus close foley of hero actions | Sound bridges and foley without stock |

## 7. Avoid

| Trick | Why it reads cheap | Do instead |
|---|---|---|
| Transition packs (zoom, spin, slide, glitch, RGB split) | Viewers recognise the template; a "cheaper knock-off" of real craft | Hard cut, cut on action, motivated match cut |
| Flash frames / white flashes between shots | Social-media template; breaks the image | Cut on action, or a real light change inside the shot |
| Light-leak and film-burn packs | Stock wedding cliché; light with no source | Halation only on real practicals |
| Crash zooms and punch zooms on beats | Low effort; screams phone edit | A locked frame, a real camera move, or a slow eased push within `numbers.md` §5 |
| A digital push on every static shot | The Ken Burns look of AI edits | Locked frames by default; push at most about a third of shots |
| Velocity edits (ramp + flash + shake stacks) | Trend template, dated fast | One ramp, one real event, sound designed into it |
| Fake camera shake / impact shake | Imitates energy the footage lacks | Real handheld or locked frames |
| Synthetic whip on static shots | Blur with no camera motion behind it | Real whip pair or a plain cut |
| Fake letterbox bars over 16:9 framing | Cuts heads and products; cosmetic | Re-compose for scope or deliver 16:9 clean |
| Visible or per-shot grain | "Slapped on", jumps between shots | One uniform grain, ~30% opacity, felt not seen |
| Global teal/orange LUT | Uniform blockbuster look, tanned skin, drained greens | Grade from the real light |
| Slow motion on stillness / interpolated hero shots that warp | Reads as filler or AI | 100% speed; slow-mo only on physical events with HFR footage |
| Fake smoke, steam, fog or AI "polish" | Viewers sense it; product looks unreal | Shoot real steam with backlight, or leave it out |
| Dark boxes or blotches behind text | Hides the image; amateur caption look | Place type on calm areas, use the frame's tones (`type-and-motion.md`) |
| Same signature shot or trick repeated | Loses power after the first use | One trick, once; vary sizes and angles |
| Any stock whoosh, riser or impact SFX | Trailer cliché; sound from no object | Real foley, sound bridges |
| Cutting on every beat | Mechanical, metronomic | Cut on phrases and actions; let 30–50% of cuts fall off-beat |
| Split screen to cram footage | Collage without a sentence | Split only for a comparison (making/made, day/night), and only if the footage was shot for it |
| Stop-motion "table sets itself" or B&W → colour built from found footage | Template look in an agent's hands | Only if the shoot was planned for it |
| Blurred slide bridges under 1 s in hotel films | Restless, not prestigious | 2–3 s shots, hard cuts |

## 8. Top 20 for premium brand films (ranked)

1. **Sound bridge (J-cut):** next scene's sound leads its picture by 0.5–1.5 s, 6–12 f crossfade.
2. **Cut on action:** cut 2–4 f into the movement, moving part in the same screen area.
3. **Hard cut as default:** `transition: "cut"`; anything else needs a written reason.
4. **Insert rhythm:** wide → detail → detail → wide, details in cause-to-result order.
5. **Real foley above the music** on hero moments (sizzle, pour, latch, fabric).
6. **Silence before the hero:** music drops 0.5–1 s, one real sound lands on the hero frame.
7. **Graphic match cut with meaning:** shared shape aligned with `reframe`, 1–2 per film.
8. **Locked frame, changing subject:** same mark, new plate/guest/glass every 45–60 f.
9. **Eased push-in, sparingly:** `push: [1.00, 1.04–1.08]` on at most a third of static shots, within the pixel budget; locked frames are the default.
10. **Natural occluder wipe:** column, door, waiter or cloche covers ≥ 90%, cut behind it.
11. **One speed ramp on one real event:** HFR source, 100 → 20–40% over 6–12 f, hold, back over 4–8 f.
12. **Conformed slow motion:** `speed` = timeline fps ÷ capture fps (50 → 25 = 0.5 freely; 120 → 24 = 0.2 for physical events).
13. **Continuous ambience bed** under the whole film, no holes at cuts.
14. **Fixed title over changing shots:** small serif, 12 f fade in, never moves.
15. **Focus reveal:** real rack focus landing 0.5–1 s after the cut.
16. **Cut on blink or gesture end** for people; never mid-expression.
17. **Dissolve as time:** `dissolve:12`–`24` between two slow, tonally close shots, max 2 per film.
18. **One contrast cut** as the structural turn, on a phrase start.
19. **Uniform grain, felt not seen:** one layer on the timeline, ~30% opacity.
20. **Halation only on practicals and speculars**, small and warm.

## Sources

- Fstoppers, video gimmicks to avoid: https://fstoppers.com/originals/9-video-gimmicks-avoid-2020-445421
- Fstoppers, overused effects and tropes: https://fstoppers.com/video/five-overused-video-effects-and-tropes-181231
- Fstoppers, against fake black bars: https://fstoppers.com/video-editing/please-dont-use-black-bars-videos-anymore-239593
- Frame.io, how a pro colorist uses film grain: https://blog.frame.io/2023/08/14/how-a-pro-colorist-uses-film-grain/
- Frame.io, mixed frame rates and retiming: https://blog.frame.io/2019/10/17/mixed-frame-rates-part-3/
- Adobe, J-cut and L-cut: https://www.adobe.com/creativecloud/video/discover/j-cut-and-l-cut
- Adobe, invisible cuts: https://www.adobe.com/creativecloud/video/hub/ideas/what-is-an-invisible-cut-in-film.html
- StudioBinder, match cuts and speed ramps: https://www.studiobinder.com/blog/match-cut/ · https://www.studiobinder.com/blog/how-to-speed-ramp-in-premiere/
- StudioBinder, Murch's Rule of Six: https://www.studiobinder.com/blog/walter-murch-rule-of-six/
- PremiumBeat, digital zooms from 4K: https://www.premiumbeat.com/blog/create-digital-zooms-4k-footage
- No Film School, eased push in post: https://nofilmschool.com/push-post-vashi-nedomanskys-premiere-pro-preset
- CineD, whip pans: https://www.cined.com/whip-pans-when-and-why-filmmakers-use-them/
- Dehancer, halation: https://blog.dehancer.com/articles/halation/
- Editors' critiques of AI-generated ads (failure modes): https://arxiv.org/html/2608.24329
- Adorama, food videography (HFR, backlight): https://www.adorama.com/alc/tips-food-photography-videography
