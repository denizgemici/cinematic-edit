# Cutting: the grammar of the cut

Read this before you write or revise a plan (`edit_plan.json`) and before every `plan_check.py` run. Frame values are given as **@24 / @25 / @30 fps**. Shared numbers live in `numbers.md`; the rhythm numbers here are warnings, not targets: break one when the film asks for it and write why in the plan.

## Contents
1. Every cut needs a reason
2. Murch's priority order: resolving conflicts
3. Choosing in and out points
4. Cut on action
5. Eye-trace across cuts
6. Angle, scale and screen direction
7. Jump cuts
8. Rhythm: lengths, runs, acceleration
9. Registers (ASL targets)
10. Sound across the cut: J and L cuts
11. Short-form specifics
12. Transitions policy
13. The three final tests
14. Quick checklist
15. Sources

---

## 1. Every cut needs a reason

- Write the film's single controlling idea in one sentence before choosing shots. If you cannot write it, you have no film yet, only beautiful shots in a row.
- The viewer should learn the film's "rule" within the first 2 s (48 / 50 / 60 frames). The rule repeats, and at the end it either completes or breaks.
- A cut is justified only by new information, a new emotion, emphasis or rhythm. "It looks good" is not a reason to cut, but it is a reason to keep a shot.
- Label every cut with its relation to the previous shot (Pudovkin): **continuation, contrast, parallel, symbol, simultaneity, repetition**. If no label fits, move or remove the cut.
- Judge each shot artistically on its own first: is this frame beautiful and cinematic by itself? Partial framing (a hand, a torso, cropped heads, fabric only) is a valid choice. Reject shots only for real defects: shake, blur, jello, broken colour, ghost frames, edge artefacts, visible crew, or a shot that breaks the idea.
- Never use a camera shot raw. Every shot gets a finishing decision first (log conversion and grade, straighten, reframe, clean stabilisation or another window, speed conform, best window). Record it in the plan's `reason` field.

## 2. Murch's priority order: resolving conflicts

| Rank | Criterion | Murch weight | The question to ask |
|---|---|---|---|
| 1 | Emotion | 51% | Is the cut true to the feeling of the moment? |
| 2 | Story | 23% | Does it advance the idea? |
| 3 | Rhythm | 10% | Does it land at a rhythmically right moment? |
| 4 | Eye-trace | 7% | Is the new subject where the eye already is? |
| 5 | 2D screen plane | 5% | Are the 180° line and screen direction respected? |
| 6 | 3D space | 4% | Is physical continuity intact? |

How to use it:
- When a cut cannot satisfy everything, give up criteria **from the bottom up**. Never trade emotion for story, story for rhythm, and so on.
- A continuity mismatch (row 6) is acceptable when the incoming frame is more beautiful or more emotional. A wrong emotion is never acceptable to fix continuity.
- In fast vertical cuts (shots under 1 s), raise eye-trace in practice: the viewer has no time to search the frame. Rank stays the same, but check it on every sub-1 s cut.
- The weights are playful. Only the order matters.

## 3. Choosing in and out points

1. **Scan the whole clip** at ≥ 2 frames per second (`scan.py`). The value is usually in the middle. The head (camera settling, focus hunting, crew talking) and the tail (camera lowering, talent releasing the pose) are usually unusable.
2. **Find the iconic frame** first: the moment the shot was filmed for (the pour hitting the glass, the door opening onto the view, the pose landing). The `in`/`out` window must contain it.
3. **Pick the calmest window** that contains the iconic frame. Measure shake on textured points over the exact window you will use. Stabilise only when gyro data or optical flow gives a clean result (`numbers.md` §5); if it wobbles, warps or shows jello, take another window or swap the shot. Fire, smoke and tossed food register as "shake" in the numbers: look at the frames before you discard them.
4. **Start late, leave early** (Dmytryk). Do not open on a subject preparing to act. Do not hold after the action has finished. If a shot needs more frames, add them at the head of the incoming shot, not the tail of the outgoing one.
5. **Hold through completion only when the result is the point** (the plated dish, the hero product). Cut out of a movement before it completes when you want energy.
6. In doubt, cut long in the first pass, then trim in passes.
7. People: cut 1–2 frames **before** a blink, unless the blink itself is the beat. Never use a moment where the subject talks, looks off to the director, or looks bad (mouth wide open while eating, frowning, shadowed face).
8. Long clips may hold several good windows. Use them as separate shots, never as repeats of the same moment.

## 4. Cut on action

- Cut inside the movement, near its middle. The motion carries the eye across the cut.
- **Default: a straight match, 0 frames of overlap or skip.** Viewers' preferred match point is within 1 frame of a straight cut (Langkjær et al. 2023).
- **Stylistic range: overlap or skip ≤ 4 frames.** Perceived smoothness is flat up to about 10 frames (400 ms) either way (Levin et al.). The classic "2–3 frame overlap" is a habit, not a perceptual law.
- **Hard limit:** never skip 1 s (24 / 25 / 30 frames) or more inside an action that should read as continuous.
- Exit/entry: cut out when the subject's leading edge leaves frame. Cut in 3–5 frames before it re-enters from the opposite side.
- Look-off to POV: cut 3–4 frames after the eyes settle on the object.
- Reaction: start the reaction shot 3–4 frames before its first visible change. Never cut to a reaction that has not started.

## 5. Eye-trace across cuts

- Measure, don't guess. For every cut, record the subject centroid (face, plate centre, product logo, brightest high-contrast region) on the outgoing last frame and the incoming first frame.
- For cuts where either shot is under 1 s, keep the centroid distance **≤ 1/3 of frame width** (≤ 360 px on 1080 wide, ≤ 640 px on 1920 wide), unless the outgoing shot's motion or gaze leads the eye to the new position.
- A deliberate graphic match (round plate → round glass mouth → sun) puts the centres on the same spot. This is the strongest invisible cut.
- Viewers look first at faces, eyes, high contrast, bright or saturated colour and sudden motion. Do not put two competing attractors in the incoming frame.
- In 9:16, keep the key point (eyes, product, plate centre) between 30% and 60% of frame height. That keeps it out of the platform UI.

## 6. Angle, scale and screen direction

- **30° / scale rule.** Two consecutive shots of the same subject need ≥ 30° of angle change or a decisive size change (wide → medium → close). A slightly tighter frame on the same axis reads as a mistake (Murch's "ankles-up" problem). Axial cuts are fine only when the size change is large (about 2× or more).
- **Scale progression.** Vary sizes: no more than **3 consecutive shots of the same size or composition** (`plan_check.py` flags this). Save the tightest close-up for the emotional or product peak; at most one extreme close-up per 5 s outside a staccato build.
- **180° rule.** Keep the camera on one side of the axis of action. Cross it only on screen (a camera move, a neutral axial shot or a cutaway), or deliberately for disorientation.
- **Screen direction.** Exit frame right means enter frame left. Movement within a sequence keeps one direction. Opposing directions are allowed only as a deliberate "collision" accent.
- **Camera moves across a cut.** A push-in that leads into the next shot must continue (the next shot moves the same way) or land on a static close-up of the destination. A move that stops dead at the cut reads as amateur.
- Adjacent shots of the same place must match white balance and exposure. A warm-to-cold jump without a story reason reads as stock footage.

## 7. Jump cuts

Jump cuts are allowed only when deliberate:
- to compress time inside one locked setup (a process, a table being set, a person working);
- as a rhythmic accent, in groups of 2 or more;
- to signal nervous or subjective time.

A single, small, unmotivated jump (same angle, slight position change) is a bug. Fix it with a cutaway, a larger size change, or by removing a shot. Never use rapid jump cuts in calm registers (spa, sleep, hotel, fine dining).

## 8. Rhythm: lengths, runs, acceleration

**Distribution** (warnings; write why if you break one).
- Real shot lengths are lognormal: many short shots, a few long ones. Target **median ≈ 0.55–0.7 × ASL** (Salt: 0.62 across 1,520 films).
- Coefficient of variation **≥ 0.3**. Flag the plan if more than 70% of shots sit within ±10% of one length, unless metric montage is the idea.
- The **longest shot ≥ 2× ASL**. The **last shot is the longest or second longest**. `plan_check.py` warns on all three. Applied together and blindly they push every film into one shape; they describe good films, they do not make them.

**Runs and shape.**
- Arrange lengths in runs, not random order (Cutting's 1/f finding): short shots cluster with short, long with long.
- Shape the film like a scallop: a slightly longer opening beat, acceleration into the turn, shortest shots near the middle of the build, then a release.
- **Hold after the build.** The release shot is at least 3× the last short shot of the build.

**Acceleration ratios (Eisenstein).** When you accelerate, halve in clean ratios, never in arbitrary decrements:

| Step | @24 | @25 | @30 |
|---|---|---|---|
| 1 | 48 | 50 | 60 |
| 2 | 24 | 25 | 30 |
| 3 (the shortest shot) | 12 | 12 | 15 |
| Release hold (≥ 3× the last short shot) | ≥ 36, usually 48–96 | ≥ 36, usually 50–100 | ≥ 45, usually 60–120 |

Simple ratios (1:2, 3:4, 1:4) work. Complex ratios lose their physical effect.

**Motion and length.**
- Short shots need motion inside them. A static shot under 1 s is unreadable and looks like a flash.
- Static or low-motion shots hold longer. A locked architectural frame needs ≥ 2.5 s to be read.
- About 3 s (72 / 75 / 90 frames) with nothing changing is the dead-air limit. Cure it with motion in frame or a slow push, not with a cut for its own sake.

**Minimum durations** (`numbers.md` §2).

| Shot content | Minimum | @24 | @25 | @30 |
|---|---|---|---|---|
| Accent or breath insert (the shortest shot) | 12 frames | 12 | 12 | 15 |
| One clear subject that must be recognised | 0.5 s | 12 | 12–13 | 15 |
| New place or person introduced | 1.5 s | 36 | 38 | 45 |
| Shot carrying text | 2 s or 0.3 s per word + 0.5 s, whichever is longer | 48 | 50 | 60 |
| Final held shot or end card | 2 s | 48 | 50 | 60 |

**Accents.** Choose 2–3 accents per film (tightest framing, strongest sound hit, or longest hold). Never more than one accent per 3 s. A film where every shot is a hero has no accents.

## 9. Registers (ASL targets)

Pick the register from the brand's tone before cutting. Write it into the plan; `plan_check.py` warns when the ASL falls outside it. The table is identical to `numbers.md` §3.

| Register | ASL | Typical use | Notes |
|---|---|---|---|
| `luxury` | 2.5–5 s | luxury hotel, architecture, fine dining, high fashion | few, decisive cuts; slow motion on material and product; long holds 4–8 s |
| `premium` | 2–4 s | premium restaurant, boutique hotel, design product | process steps 1.3–2 s, one beautiful movement 2.5–7 s |
| `brand` | 1.2–2.5 s | general brand film, casual dining, lifestyle | hero 2–3 s with 1–2 longer holds |
| `social` | 0.8–1.8 s | organic Reels/TikTok for a brand | still needs a held payoff |
| `hype` | 0.4–1.2 s | fast food, nightlife, sport, events | cut on action and beat; hero 1.5–3 s |

- Pace follows the brand, not the platform average (the 2026 social-ad corpus averaged 1.2 s per shot; professional editors still called rapid cuts in a calm-brand ad "too intense").
- Sub-1 s shots look restless in hotel and architecture films: prefer ≥ 1 s there. In food and restaurant films (fine dining included), 12-frame breath inserts are allowed (`structures.md` §5).
- Shot count is a consequence of good footage, not a target. Do not pad and do not force cuts. When the good footage runs out, the film ends.

## 10. Sound across the cut: J and L cuts

- Sound continuity hides picture cuts. Without sound, edit blindness largely disappears (Smith & Martin-Portugues 2017).
- Run one continuous music bed or ambience across a montage. A hard audio cut is an accent and must coincide with a picture accent.
- **J-cut:** the incoming sound starts 6–12 frames before its picture (pour sound before the pour, sea before the terrace). **L-cut:** the outgoing sound trails 6–12 frames under the next picture.
- Never cut sound and picture on the same frame between scenes with VO or dialogue.
- Never cut a spoken sentence mid-word. With VO, the film continues about 2–3 s after the last word.
- Music: use one continuous section; never cut a phrase in the middle and never loop-extend a track. Map the whole song first, then pick the section with the right build.
- **Beat alignment.** 50–70% of cuts on beats or phrase starts; the rest on action or off-beat. No more than 4 consecutive cuts exactly on the beat. A cut 0–2 frames **before** the beat counts as on beat; never 2 frames or more after it (`numbers.md` §4; `plan_check.py` flags late cuts). Change cut density between song sections. One or two off-beat cuts at the climax are allowed for surprise. If nobody has heard the music, the beat grid is a guess: keep cuts on action and say so in the report.
- The end card lands on the music's resolution, never on an abrupt stop.
- Room tone and foley under the music in every film (pour, sizzle, cutlery, door, water). Real sounds stay barely there: 10–20 dB below the music's peaks (`numbers.md` §7; `sound_db` in the plan). No stock whooshes, ever. Ambient sound starts at frame 0; never open on silence. A short silence mid-film can be a strong accent.

## 11. Short-form specifics

- **Frame 0 is strong.** It is already one of the most beautiful or surprising images in the film: a physical event mid-action (pour, flame, steam, a door opening onto a view), strong light on texture, or an unexpected scale. No black, no logo, no flash, no zoom-punch on frame 1, no text wall.
- **Hook complete by 2 s.** In ads, at least 3 shots in the first 5 s for `brand`/`social`/`hype`; `luxury` may hold one long opening shot if it is in motion.
- **Product or brand visible within 2–5 s** (Google ABCD; Kantar). For a place, the place itself counts.
- **End on the longest held result:** the served dish, the first bite, the hero product, the room at its best light, the final pose. Never end on a filler detail. The final shot resolves; it does not freeze.
- **Structure compresses, it does not disappear.** 15 s = hook (0–2 s), development, turn, payoff with brand in the last 3–4 s. 6–10 s = question, then answer.
- **Loops (optional).** End on a calm frame whose composition and motion vector match frame 0. Avoid a final-sounding audio hit. Loops are not a guaranteed views multiplier.
- **Plant and pay off.** The opening image or gesture should rhyme with the final shot.
- Typical lengths that work: Instagram post and story 15–18 s; most saved premium references run 7–20 s. Make 30–60 s only when the footage and brief carry it.

## 12. Transitions policy

**Default: the hard cut.** Use `"transition": "cut"` unless a listed exception applies.

**Allowed, with a reason written in `reason`:**
- **Match cut:** shape, colour, material or motion-vector match (round plate → glass rim; melted butter → golden sauce; water reflection → bokeh). Plan it from the scan; do not hope for it.
- **Sound bridge:** a J or L cut carries the transition while the picture hard-cuts.
- **Motivated dissolve** (`"dissolve:N"`): time passing or day to night, N = 12–24 frames @24/25 (15–30 @30); a calm locked-frame object swap, N = 4–8 (`numbers.md` §6). At most 2 per film. A dissolve where a cut belongs reads amateur.
- **Wipe by object:** a foreground element (hand, door leaf, curtain, glass, passing person) fills the frame and the cut hides on it.
- **Focus reveal:** blur to sharp inside the shot itself, not as an added effect.
- **Water or reflection:** the surface becomes the transition.
- **Slow fill:** steam or flame fills the frame and the cut hides on it (slow, never a hard white flash).

**Never used:** white flashes and flash frames, stock whooshes, glitch, RGB split, spin, slide/push packs, zoom-blur, whip packs, pixelate, checkerboard, clock wipe, light-leak packs, beat zoom pulses, stripe or blind wipes. A single whip is allowed only if it is shot in camera and motivated by the action. Any effect that is identifiable as an effect is too strong: effects are barely there.

**Speed ramps:** about 1–2 per 15 s (`numbers.md` §1), across a real event, and the ramp direction must bridge into the next shot (slow → fast into a cut on action).

## 13. The three final tests

Run all three before `qc.py` and before showing anyone the cut.

1. **Remove-a-shot test.** For each shot, imagine it gone. If no emotion, story or rhythm is lost, remove it.
2. **Shuffle test.** If shuffling the order of the shots would not change the meaning, the cut has no structure. Rebuild around set-up, turn and payoff, and cause before effect.
3. **Silent / sound-only test.** Watch once muted: the picture alone must tell the story. Listen once without picture: the sound alone must carry the rhythm and the build. Then watch once on a phone, with sound, at real size.

## 14. Quick checklist

- [ ] One-sentence idea written; every cut labelled with a relation.
- [ ] Every shot finished (grade, straighten, reframe, stabilise or swap, speed, window); no raw shot.
- [ ] Iconic frame inside every window; no settling heads or releasing tails.
- [ ] Match-action offsets within 0 ± 4 frames; no ≥ 1 s skip inside an action.
- [ ] Eye-trace distance ≤ 1/3 frame width on sub-1 s cuts.
- [ ] ≤ 3 same-size shots in a row; 30° or clear size change between shots of the same subject.
- [ ] ASL inside the register; median ≈ 0.55–0.7 × ASL; CV ≥ 0.3; longest ≥ 2× ASL; last shot longest or second (or a written reason why not).
- [ ] Short shots have motion; text shots ≥ 2 s; final hold ≥ 2 s.
- [ ] 50–70% beat alignment (0–2 frames early counts); no cut ≥ 2 frames late; music section uncut.
- [ ] Hard cuts by default; every non-cut transition has a written reason.
- [ ] No repeated shot, face or moment; cause before effect.
- [ ] Remove-a-shot, shuffle and silent/sound-only tests passed.

## 15. Sources

- Murch, *In the Blink of an Eye* (Rule of Six): https://nofilmschool.com/2016/11/6-rules-good-cutting-according-oscar-winning-editor-walter-murch
- Murch interview on cut frames and blinks: https://www.provideocoalition.com/aotc-murch-bcpc/
- Dmytryk's rules (teaching summary): https://www.chicagomediaworks.com/2instructworks/3editing_doc/3editing_docdymytryk.html
- Eisenstein, *The Fourth Dimension in Cinema*: https://www.torch.ox.ac.uk/sitefiles/eisenstein-the-fourth-dimenson-in-cinema.pdf
- Smith & Henderson 2008, Edit Blindness: https://bop.unibe.ch/JEMR/article/view/2264
- Smith 2012, Attentional Theory of Cinematic Continuity: https://ualresearchonline.arts.ac.uk/id/eprint/21187/
- Langkjær et al. 2023, match-action preference: https://lup.lub.lu.se/record/cbd7788c-4320-4a5c-b0e6-e7a55742b782
- Salt 2011, The Metrics in Cinemetrics: https://cinemetrics.uchicago.edu/article/616e7ecc-7915-4768-b84d-7dec79aa77c2
- Cutting 2016, evolution of pace: https://link.springer.com/10.1186/s41235-016-0029-0
- Prétet et al. 2021, music-video cuts and beats: https://arxiv.org/abs/2108.00970
- Google ABCD guide: https://services.google.com/fh/files/misc/youtube_google_abcd_reference_guide_en.pdf
- Professional editors on AI cinematic ads (2026): https://arxiv.org/html/2608.24329
