# Genre playbooks

Read the playbook for the job's genre after `cutting.md` and before writing `edit_plan.json`. Each playbook gives the register (ASL range checked by `plan_check.py`), structure options, slow-motion use and typical mistakes. Frame values are **@24 / @25 / @30 fps**. Shared numbers are in `numbers.md`; genre rules are warnings: break one with a written reason.

## Contents
1. Rules shared by every genre
2. Slow motion: conform table
3. Structure devices (shared toolbox)
4. Food and restaurant
5. Hotel and architecture
6. Fashion
7. Product
8. People and events
9. Sources

---

## 1. Rules shared by every genre

- **One idea per film.** Write it in one sentence. Pick one structure device from §3 that makes the idea visible, and commit to it to the end. Do not mix three devices in 15 s.
- **Watch everything.** Scan every clip end to end before selecting. No good shot stays outside the film, but each shot is used only as long as it is good. Length follows the amount of good footage; never pad.
- **Judge beauty first.** Partial framing (hands, torso, fabric, cropped heads), faceless shots and bold angles are valid. Reject only real defects: shake, blur, jello, blown highlights over large areas, crew in shot, broken colour, ghost frames.
- **No raw shots.** Every shot is graded, straightened (tilts of 0.2–15° to exactly 0°/90°; a strong Dutch angle is deliberate; `numbers.md` §5), reframed for the aspect, conformed for speed and trimmed to its best window before it enters the cut.
- **No repeats.** The same shot, face or moment never appears twice in one film, and the same shot is not reused across films of the same series.
- **Cause before effect.** Never show a result before its cause unless reversal is the idea.
- **End on the result.** The final held shot is the payoff of the idea, the longest or second-longest shot.
- **Cutaways are close details of the subject's own action,** not a literal picture of a word (a haircut gets the hair detail, not another salon).

## 2. Slow motion: conform table

Use real high-frame-rate frames at an exact ratio (`speed` = timeline fps ÷ capture fps). `plan_check.py` flags non-clean conforms.

| Capture → timeline | `speed` | Note |
|---|---|---|
| 48 → 24 | 0.50 | gentle slow motion |
| 50 → 25 | 0.50 | |
| 60 → 30 | 0.50 | |
| 100 → 25 | 0.25 | peak slow motion |
| 120 → 24 | 0.20 | |
| 120 → 30 | 0.25 | |
| 60 → 25 | 0.417 | non-integer; prefer 50p capture for 25p timelines |

- **Conform is free; deep slow is a moment.** Conformed high-frame-rate footage (50p at 50 % on 25p) has no quota and is not "wedding video": it can carry most of the B-roll. Deep slow motion (k ≥ 4, ramps, hang-and-snap) goes on **physical events and materials** where it earns it: pour, drop, steam, pull, flame, splash, fabric swing, hair, water. Never on talking people (`numbers.md` §1).
- Slowing 24/25/30p footage means invented frames: follow the decision table in `slow-motion.md` §5.1 (low-risk subjects up to 1.7×; hero and high-risk subjects only after a passing frame-by-frame check). If the source is too short, shorten the shot.
- In speed ramps, pick source frames with `floor()`, not `round()`, or every second frame repeats.
- After a slow-motion moment, return to real time with real sound. The energy "rushes back in".
- Slow motion measurably raises perceived luxury (Jung & Dubois 2023) when it is clean. Stutter or blur kills the effect.

## 3. Structure devices (shared toolbox)

Each device gives the viewer a rule to learn in 2 s. Choose one per film.

| Device | How it works | Timing |
|---|---|---|
| **Locked frame, changing subject** | Tripod, same light, same mark; only the object or person changes (glass on a bar, plate on a table, a guest in a doorway). Swap by hard cut or a 4–8 frame dissolve. | ~2 s per object (48 / 50 / 60); last round 2× longer, or an empty frame for 2 s |
| **Process / result split** (only if shot for it) | Screen split in two halves: preparation in one, the finished result in the other, simultaneously. The split must carry a sentence ("making / made", "kitchen / dining room", "noon / night"). | 3 pairs × ~1.4 s (34 / 35 / 42); last 2 s one full-frame hero |
| **Fixed title, changing shots** | A thin serif title sits still in one place; the shots underneath change by hard cuts. | shots 45–60 frames @24/25 (55–75 @30), title holds throughout |
| **Breath shot** | One wide locked shot of the place returns between inserts, like breathing. | wide 60 / 63 / 75, insert ~48 / 50 / 60, 5–6 parts |
| **Object or motif continuity** | The same object, pattern or logo appears in every shot; cut on the object's motion. | shots 48–60 frames, final logo hold 72 / 75 / 90 |
| **Shape / motion match** | Every cut carries a shape, colour or motion direction (round plate → sun → glass rim). Plan from the scan. | 5 shots × 48–55 frames; motion starts 3–4 frames before the cut |
| **Foreground reveal** | A foreground element (glass, leaf, door leaf, net, curtain, hand) fills the frame; the cut hides on it. | wipe ~12 frames, new shot ~60 |
| **Water / reflection** | The second shot is the reflection or the underwater world of the first. | surface ~36, reflection ~24, new world ~48 |
| **One gesture, no cut** | A cloche lifts or a plate builds in one locked take. The edit is only the in and out. A stop-motion "table sets itself" only if the shoot was planned for it. | 120–150 frames for one fluid gesture |
| **Colour as a move** (only if shot for it) | Black-and-white process shots, colour opening at the dish or action moment. At most once or twice per film. | colour opening ~34 frames, inside an action |

Rejected as cheap in premium work: panel collages that fill a grid at 0.3–0.8 s per cell, vertical stripe wipes, social-media transition packs, counters and gimmick props, shaking camera, kinetic type, sub-1 s cuts with blurred pan bridges in hotel or fine-dining films.

## 4. Food and restaurant

**Register.** Fine dining: `luxury` (2.5–5 s). Premium restaurant: `premium` (2–4 s) or `brand` (1.2–2.5 s). Casual and fast food: `brand` to `hype` (0.4–1.2 s), cut on action and beat. Process steps 1.3–2 s (2 s for prestige); one beautiful movement 2.5–7 s; place or chef portrait about 2.5 s.

**Order (cause → result).** Raw ingredient → knife, hands → heat (flame, sizzle, steam) → plating → serving → first bite or the dish on the table. Never jump from raw straight to served: put a heat shot between them. Never show a full glass before the pour, or a set table before the cloth is laid.

**Process / result split.** Divide the film's time: the process builds; the result holds. Cold and raw shots run long, heat shots slightly shorter, the serving shot longest (3–4 s).

**Hero last.** The hero shot (dish, drink or bite) sits in the last 2–4 s (48–96 / 50–100 / 60–120 frames): sharp, well lit, the product fully in frame and not cropped, centred inside the safe zone. It is the longest or second-longest shot.

**Physical events.** Steam, pour, cheese or sauce pull, drop, flame, sizzle and condensation carry food films. Keep ice, droplets and condensation details; without them a clean shot feels empty. Use macro for texture (crumb, crust, glaze, fish skin) and hold macro shots longer than they seem to need.

**Breath inserts.** Short details of the place (light on a wall, the sea, a terrace, a door, linen) go between the main shots: about 0.5 s each (12 / 12–13 / 15 frames), 2–3 at a time at most, then straight back to the subject. They breathe; they do not flash. **At least 60% of the running time stays on the main subject.** A burger film is about the burger; the place decorates it and never replaces it.

**Slow motion is central.** Conformed 50p at half speed suits most food B-roll. Deep slow (ramps, hangs, 4× and more) goes on the physical events: pour, drop, steam, pull, flame, toss, sauce. Fire, smoke and tossed food score as "shake" in `scan.py`: look at the frames, these are usually the best moments. Typical shape: slow detail at the table → kitchen details with one ramp on the toss or the flame → result at the table.

**Ending.** End on serving, the first bite, or the dish landing on the table. Never on a filler detail, and a static top-down plate alone is a weak outro. The final shot resolves and fades or cuts to the end card; it does not freeze.

**Typical mistakes.**
- Result before cause (served before prepared).
- A "sequence of nice dishes" with no idea; every dish the same framing.
- Unflattering eating moments: mouth wide open, tongue, full chewing, a hand covering the mouth. Use the moment just before the bite or the first closed-mouth reaction.
- Readable alcohol brands or competitor logos in frame; drinks as the main subject when the brief is food.
- Interpolated slow motion warping steam and liquid.
- Flat stock music with no build; no foley (sizzle, pour, cutlery).
- Breath details taking over the film.

## 5. Hotel and architecture

**Register.** `luxury` (2.5–5 s). Long holds of 4–8 s are normal. 6–12 shots for 30 s. Prefer shots of 1 s or more; breath inserts belong to food films.

**Frame rules.**
- **Locked frames** or one slow eased move per shot (push, slide or tilt). No handheld wander, no linear digital zoom.
- **Straight verticals.** Measure the strongest true vertical (door frame, column, window edge) and true horizontal (counter, pool edge, horizon) in every shot. Correct tilts to exactly 0°/90°; use keystone correction for converging verticals when the source has headroom. Budget the scale: 1° needs about +3.1%, 2° about +6.1%.
- **No warp stabilisation** on architecture (subspace warp bends straight lines). Jello in straight lines is a reject.
- **Slow push, sparingly:** within `numbers.md` §5 (3–6 % up to 3 s, 5–8 % over 4–6 s), eased, one direction, on at most about a third of the shots. Never on a shot that already moves; locked frames stay the default.

**Light as subject.** Morning light across linen, shadows of an arch moving on a wall, the pool at blue hour, lamps coming on. Order shots along the day's light (day → golden hour → night) or along a walk through the space (arrival → room → detail → view). Light changes are the story's turns.

**People.** Small in frame and not focal: a figure crossing a corridor, a hand on a balustrade, a back at a window. Faces rarely, never posed to camera unless the brief is about service. No crew in any shot.

**Structure options.** Walk-through (exterior → entrance → interior → detail → view); fixed title over changing shots; locked doorway with a different guest each round; material and colour match cuts (terracotta → palm → water → bronze); a day-to-night arc with one motivated dissolve. Fast city cuts may appear only as a contrast to calm interiors.

**Sound.** Sound carries premium place films: water, sheets smoothed, a door, distant birds, cutlery, a bell. Silence or room tone before the main reveal.

**Slow motion.** Conformed 50p on slow camera moves and on water, curtains, fabric in wind and a pour at the bar is welcome. Deep slow is rare here: one moment at most.

**Typical mistakes.**
- Fast cuts, whip or zoom transitions, blurred pan bridges.
- Tilted verticals; jello; blown windows or sky (clipping across a large area is a reject even if the median exposure looks fine).
- Small figure in a huge empty frame by accident; people as the focal point.
- Same composition 4 times in a row (all symmetric one-point perspectives).
- White-balance jumps between rooms of the same place.

## 6. Fashion

**Register.** Luxury fashion: `luxury` or `premium` (2–5 s). Commercial or streetwear: `brand` to `social` (0.8–2.5 s), rhythm with the music.

**Pose moments only.** Use moments that would work as an advertising photograph. Reject in-between moments: talking, glancing off-camera, looking to the director after a move, adjusting clothes, a half blink. Measure with face landmarks (mouth opening, head angle, gaze, motion) and check each candidate window every 2–3 frames; one-second contact sheets miss open mouths and blinks.

**The walk is a pose.** A walk toward or across the camera, a turn, a fabric swing are poses. Cut on the step (cut on action) and keep screen direction consistent.

**Partial framing.** Hands, collar, sleeve, print, fabric texture, torso without a face are full shots. Frame the garment, not the face, when the product is the garment. In full-body shots: centred horizontally, headroom not smaller than foot room, no feet or head cut accidentally during a push-in, backdrop edges never visible.

**Rhythm with music.** Cut changes of look on the beat; hold the strongest poses longer; build with clean halving ratios into the drop, then release on a held pose. 50–70% of cuts on beats, the rest on movement.

**Ending.** A resolved pose with the gaze in the lens as the music settles, held ≥ 2 s. Not a walk out of frame.

**Slow motion.** On fabric, hair, a turn, a jacket thrown: 50% or 25% from real high-frame-rate footage. Not on faces talking.

**Typical mistakes.**
- Crew or light-test stand-ins used as models; any person in a shot is checked before use.
- The same model or look repeated. Never disguise a repeat (no mirror flips, no punch-in on the same take); use another moment or another look, or leave it out.
- Shaky vertical tracking; per-frame head tracking that wobbles the frame (use one linear drift between start and end instead).
- Beat zoom pulses and motion-blur ghosts.

## 7. Product

**Register.** `premium` (2–4 s) for design, beauty, jewellery and tech; `brand` (1.2–2.5 s) for consumer goods.

**Hero reveal.** Build the question before the answer: material, light and partial glimpses first, then the full product, held. The reveal is a turn: shortest shots just before it, then the longest hold of the film.

**Texture and material truth.** Macro on grain, brushed metal, glass, stitching, liquid, powder. The product's real colour, shape, proportions and surface must survive the grade; never let a look change the product's colour. If any shot is AI-assisted, compare it with the real product side by side: shape, layers, colour, texture and proportion must match, or the shot is not used.

**Match cuts.** Products are ideal for shape and motion matches: a round lid → the moon, a bottle silhouette → a column, a rotation continued across shots. Plan them from the scan; place the shape centre on the same spot across the cut.

**Light moves.** A slow light sweep across a static product is often better than any camera move. Use one sweep or one eased push per shot.

**Slow motion.** Drops, splashes, powder, a lid closing, a liquid pour. Real frames only.

**Ending.** The product whole, sharp, uncropped, in the safe zone, with the brand's own end card or logo integrated, held 1.5–2.5 s and timed to the music's resolution. Never a hard cut to a black logo.

**Typical mistakes.**
- Product cropped or off-centre at the bottom of a 9:16 frame (in the UI zone).
- Upscaling hero shots beyond native pixels (limit 1.0 for hero and close shots, 1.15 for others).
- Logo in every shot; too much gold, too much motion, too many logo close-ups.
- Competitor products or logos visible.

## 8. People and events

**Register.** Parties, concerts, nightlife: `hype` (0.4–1.2 s). Corporate events, weddings, gatherings: `social` to `brand` (0.8–2.5 s). A held peak or closing shot is still required.

**Crowd variety.** Build a pool of distinct moments first (aim for many more than you need, about 100 for a party reel): laughs, dances, toasts, hands, reactions, wide crowd, performer peaks. Tag each by person and outfit. **No person appears twice** in one film; a recognisable outfit counts as the same person.

**Peak moments.** Use the top of each action: the jump, the laugh, the toast touching, the confetti hitting the light, the singer's held note. Cut on action, on the beat. Wides establish scale; close reactions carry emotion; alternate them so no more than 3 same-size shots run in a row.

**Flattering moments only.** No frowning, eyes half closed, mouth wide open, shadowed faces or awkward posing. If a strong moment is unflattering up close, use a wider frame where the face is small.

**Consent and crew.** Do not use the face of anyone who has not agreed to appear where the brief requires consent. Crew, photographers and staff with equipment are never guests.

**Structure options.** Arrival → build → peak → release (the scallop); performer-led (the artist's moments as the spine, crowd as response); one continuous song section with cut density changing per section; a "same gesture, different people" chain (toast after toast) matched on motion.

**Slow motion.** One or two peaks per film: confetti, a jump, hair, champagne spray, a dancer's turn. Return to real time on the beat.

**Ending.** The biggest peak or a warm closing wide held ≥ 2 s on the music's resolution; for artist ads, the artist's best held moment.

**Typical mistakes.**
- The same face appearing three times while dozens of other moments go unused.
- Only the first seconds of each clip used; the best moments sit in the middle.
- Every cut on the beat; no hold anywhere.
- Shaky low-light shots kept after a stabilisation that shows jello or wobble; stabilise only when the result is clean, otherwise swap the shot.

## 9. Sources

- Chef's Table cinematography (frame rates, slow to real time): https://theasc.com/articles/chefs-table-a-tasting-menu
- 99% Invisible, *Flying Food* (prep, crave and hero shots): https://99percentinvisible.org/episode/flying-food/transcript/
- Directing liquid in tabletop: https://shots.net/news/view/choreographing-physics-directing-liquid-in-tabletop
- Luxury hotel films carried by sound: https://shots.net/news/view/amans-sounds-of-satisfaction
- Fashion film editing: https://shots.net/news/view/88846-fashion-special-a-more-flattering-cut
- Jung & Dubois 2023, slow motion and luxury: https://knowledge.insead.edu/marketing/how-slow-motion-video-ads-make-products-more-luxurious
- Frame.io, mixed frame rates and conforming: https://blog.frame.io/2019/10/17/mixed-frame-rates-part-3/
- Professional editors on AI cinematic ads (2026): https://arxiv.org/html/2608.24329
