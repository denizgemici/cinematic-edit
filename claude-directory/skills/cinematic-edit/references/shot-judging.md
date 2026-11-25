# Judging a shot: beauty first, real defects second

Contents: 1 The principle · 2 Procedure · 3 Real defects · 4 Not defects · 5 Rubric · 6 Critic-agent prompt · 7 Worked examples

## 1. The principle

Every shot is judged as an image **on its own**, the way a director of photography or a fashion art director would judge it. Composition "rules" are beginner tools that masters break on purpose. A frame that shows only a hand, only a chest, only fabric, a back, a body cut by the frame edge, or a face lost in shadow can be the best shot in the film. The viewer completes what the frame leaves out (Gestalt closure); a part can stand for the whole (synecdoche).

Continuity is the editor's job, not a reason to reject a shot. Murch ranks emotion (51%) far above spatial continuity (4%). A daylight shot inside a night sequence, an ingredient that does not match the previous shot, a prop that moved: these go into a **placement note**, never into a fail verdict.

The asymmetry that matters: a wrongly rejected beautiful shot is a worse error than a wrongly passed mediocre one. The human can drop a weak shot in seconds but never sees the beautiful one you threw away. **When unsure, pass it and flag it for a human look.**

## 2. Procedure (run in this order, every shot)

1. **Look** at the frames: the scan strip, plus 3–5 frames across the chosen window (start, peak, end). Do not read the brief or metadata first.
2. **Describe in one sentence what the image does**: subject, light, feeling. ("Warm backlight catches steam over a torn bun; a hand enters from the bottom edge; intimate and appetising.")
3. **Judge beauty first** with rubric axes A–F (section 5).
4. **Only then check technical integrity** (axis G) against section 3. For each candidate flaw ask: is it in section 4? Does it hurt *this* image, or does it only break a rule?
5. Continuity and story-fit go into `editor_note`.
6. **Verdict**: PASS / PASS-WITH-NOTE / FAIL, with one sentence naming the decisive reason in visual terms.
7. If unsure: PASS and set `owner_look: true`.

## 3. Real defects (these fail unless clearly intended and beautiful)

| # | Defect | Exception |
|---|---|---|
| D1 | Unintended shake: jerks, bumps, micro-jitter, rolling-shutter jello, stabiliser wobble | Organic, consistent handheld energy that is clearly a style |
| D2 | Focus missed on the intended subject (plane lands on the wall/table) | A whole frame that is softly diffused as a look |
| D3 | Focus hunting or breathing during the shot | none |
| D4 | Compression blocks, banding, posterised gradients | none |
| D5 | Ghosting, frame blending, interpolation tears, AI morphing, warped hands, melting product or text | none |
| D6 | A colour cast that reads as an error: sick green/magenta skin, white balance drifting mid-shot | A motivated cast (sodium street light, neon) that keeps skin believable |
| D7 | Clipped skin or product: flat white patches with hard edges | Rim light that rolls off |
| D8 | Murk: a crushed subject with nothing readable, muddy lifted blacks | A clean silhouette with a readable shape |
| D9 | Crew, gear, light stands, mics, reflections of the camera; test people; production staff posing as guests | none |
| D10 | Dead moment: subject talking off-camera, looking at the crew, fidgeting, waiting | A held, composed stillness |
| D11 | Sensor dust, lens smudge, unintended drops on the lens, dead pixels | Rain on glass as the motif |
| D12 | Flare or veiling glare that hides the subject | Flare that frames the subject |
| D13 | Accidental sliver or tangent: a tiny piece of a head/hand at the edge, an object half-in with no tension | — |
| D14 | Lines that should be straight are off by 0.2–15° (`numbers.md` §5): horizon, counter, window, table edge | A strong, clearly deliberate Dutch angle |
| D15 | A vertically shot clip shown lying sideways, or zoomed to fill instead of rotated | none |
| D16 | A blown-out window dominating the frame | A soft high-key background that frames the subject |
| D17 | Brand problems: competitor logos, a readable alcohol brand where the brief forbids it, wrong product | per brief |

D14 and D15 are fixable in finishing (see `finishing.md`): fail the *untreated* shot, pass the treated one.

## 4. Not defects (never fail a shot for these alone)

| # | Looks like a violation | It fails only if… |
|---|---|---|
| N1 | Body cropped: half a person, chest only, torso, nape, feet | the crop is a sliver/tangent with nothing to read |
| N2 | Head or eyes cut by the top of the frame | it looks accidental (tiny forehead cut, empty bottom) |
| N3 | Only a hand / only fabric / only texture | the hand does nothing and the light is flat |
| N4 | Faceless subject, back to camera, face in shadow | the face was the point of this shot (a testimonial) |
| N5 | Off-centre, extreme edge placement | the weight feels unplaced |
| N6 | Dead-centre, symmetrical | — |
| N7 | Strong intentional tilt (a deliberate Dutch angle) | it reads as an accident rather than a choice (D14) |
| N8 | Dark, low-key, deep shadows | D8 murk |
| N9 | Fine, even grain or noise | blotchy chroma noise or compression mush |
| N10 | Motion blur | a shapeless smear with nothing to anchor the eye |
| N11 | Shallow depth of field, most of the frame soft | D2 |
| N12 | Mixed colour temperatures | D6 |
| N13 | Lens flare, haze, bloom | D12 |
| N14 | **Any continuity mismatch** (day/night, ingredients, props, hair, story order) | never: it is a placement note |
| N15 | Low contrast, faded look | it is really unconverted log footage |
| N16 | Foreground occlusion: glass, leaves, passers-by | the occluder is crew or hides the key moment |
| N17 | Hard direct flash look | skin clips (D7) |
| N18 | Tiny subject in a big space | the subject is unreadable at phone size |

## 5. Rubric (1–10 per axis)

Axes A–F are artistic; G is a gate for real defects only.

- **A Light** (direction, quality, contrast, shape). 1–3 flat or muddy · 4–6 clean but ordinary · 7–8 clear direction, shadows shape the subject, highlights roll off · 9–10 light *is* the subject (backlit steam, rim on skin, window falloff, silhouette).
- **B Composition** (structure, edges, depth). 1–3 unplaced, clutter, tangents · 4–6 readable but generic · 7–8 clear hierarchy, chosen edges, layers or negative space · 9–10 would stand as a printed photograph. Cropped bodies, off-centre, centred and strong tilts are neutral here.
- **C Moment & gesture.** 1–3 dead time · 4–6 something happens, no peak · 7–8 a gesture at its peak (the pour, the bite, the turn, fabric released) · 9–10 a decisive micro-moment that carries emotion alone.
- **D Texture & material truth.** 1–3 plastic, smeared, AI-melted · 4–6 acceptable · 7–8 you can feel crumb, pores, weave, condensation · 9–10 almost touchable.
- **E Colour.** 1–3 casts that read as errors · 4–6 correct but unremarkable · 7–8 coherent palette with one purposeful accent, skin alive · 9–10 colour carries the mood alone.
- **F Emotion & mystery.** 1–3 purely informational · 4–6 pleasant · 7–8 a detail or a withholding pulls you in · 9–10 lingers; suggests more than it shows.
- **G Technical integrity (gate).** 1–3 a real defect damages the subject · 4–6 a minor defect that finishing fixes (note it) · 7–10 clean, or its "flaws" are intentional.

**Scoring.** Artistic score = mean of A–F with the **two highest axes counted double** (a shot can be great on light or gesture alone).
- PASS: artistic ≥ 6.5 and G ≥ 4.
- PASS-WITH-NOTE: artistic ≥ 6.5 and G 4–6 (fixable), or any placement remark.
- FAIL: G ≤ 3 (real, unfixable defect on the subject), or artistic < 5 with no axis ≥ 8.
- Any single axis ≥ 9 cannot fail on artistic grounds.
- Never FAIL for any N-item alone.
These thresholds are a starting point [heuristic]; tune them against the human's real keep/drop decisions.

## 6. Critic-agent prompt (copy into an independent sub-agent)

```
You are a senior cinematographer and editorial photo director reviewing shots for
an advertising film. Judge each shot as an image ON ITS OWN, the way a senior
director of photography or a top fashion art director would, not with a
beginner's rule book.

INPUT: per shot, 3-5 frames (start / peak / end) and separately the brief,
plus 2-3 full-resolution stills of the hero shot and the last shot.
Look at the frames BEFORE reading the brief. If you only have small thumbnails
for a shot, say that your focus and texture calls on it are provisional.

1. LOOK. One sentence: what the image does (subject, light, feeling).
2. BEAUTY FIRST. Score A Light, B Composition, C Moment/Gesture, D Texture,
   E Colour, F Emotion/Mystery (1-10).
3. DEFECTS SECOND. Score G against REAL defects only: unintended shake/jello,
   missed focus on the intended subject, focus hunting, compression/banding,
   ghosting/interpolation tears/AI morphing/warped hands or product, error-like
   colour cast or sick skin, clipped skin/product, murky crushed subject, crew or
   gear in frame, dead moment (talking/looking away/fidgeting), dust/smudge,
   flare hiding the subject, accidental sliver crop, an accidental 0.2-15 deg
   tilt of lines that should be straight (not a deliberate Dutch angle),
   sideways vertical source, dominant blown window, brand violation.
4. NEVER fail a shot for: a cropped body (half a person, chest, hands, feet,
   nape), head or eyes out of frame, only a hand / fabric / texture, faceless or
   back to camera, off-centre or centred, strong intentional tilt, darkness,
   fine grain, expressive motion blur, shallow focus on a meaningful detail,
   mixed light, flare or haze that frames the subject, a faded look, foreground
   occlusion, a tiny subject in a big space, or ANY continuity mismatch (day shot
   in a night film, props/ingredients differ, story order). Continuity goes to
   "editor_note" only.
5. VERDICT. Artistic = mean of A-F with the two highest counted double.
   PASS if artistic >= 6.5 and G >= 4. FAIL only if G <= 3 or (artistic < 5 and
   no axis >= 8). Any axis >= 9 cannot fail on artistic grounds.
   When in doubt: PASS and "owner_look": true.
6. JUSTIFY in one visual sentence naming the decisive axis.
   Forbidden reasons: "person is cut", "head is cropped", "only a hand",
   "doesn't match the previous shot", "should be night", "ingredient differs",
   "not centred", "rule of thirds".

OUTPUT (JSON per shot):
{"shot": "", "describe": "", "scores": {"A":0,"B":0,"C":0,"D":0,"E":0,"F":0,"G":0},
 "artistic": 0, "verdict": "PASS|PASS-WITH-NOTE|FAIL", "reason": "",
 "defects": ["D#: ..."], "editor_note": "", "owner_look": false}
```

The critic sees only frames, sheets and numbers, never your reasoning, so it is not anchored on your choice. Give it 2–3 full-resolution stills of the hero and the ending; thumbnails alone cannot show focus. Its approval is evidence, not proof: you still watch the film yourself. **If the film changes after the review** (a shot swapped, trimmed or retimed, a new grade), run the critic again on the new version, or state in the report that the critic did not see the final file.

## 7. Worked examples: looks like a violation, is a great shot

1. Only the chef's forearm and a knife in hard side light, face out of frame: gesture 9, light 8 → PASS.
2. A waiter's back walking into a bright doorway, almost a silhouette: mystery 8, light 9 → PASS.
3. Model cropped at the chin, collar and fabric fold in focus: texture 9 → PASS.
4. Daylight terrace shot inside an evening sequence: PASS, note "place before the night block".
5. Steam half-hiding a plate, the plate soft: mood 8, light 9 → PASS (the steam is the subject).
6. Glass of water occluding the foreground, table soft behind: layers 8 → PASS.
7. Hand entering frame bottom-left, only fingers visible: closure → PASS.
8. Strong 20° Dutch angle on a fashion walk, clearly chosen: deliberate energy → PASS. The same shot at an accidental 2° tilt → straighten.
9. Extreme negative space, a tiny figure at the edge of a white wall: scale contrast → PASS if readable on a phone.
10. Grainy night street, mixed sodium and neon: colour 8, mood 9 → PASS.
11. Motion-blurred dancer with a sharp face: gesture 9 → PASS.
12. Bun torn apart, crumbs flying, slightly soft background: moment 9 → PASS.
13. Faceless couple's hands touching over a table: emotion 8 → PASS.
14. Centred symmetrical corridor: composition 9 → PASS.
15. Dark low-key bar, only the bottles' rims lit: light 9 → PASS.
16. Fabric filling the frame, no body: texture 9 → PASS.
17. Feet on stone steps, the rest of the person unseen: story by part → PASS.
18. Out-of-focus foreground leaves framing a pool: layers → PASS.
19. Lens flare kissing a model's cheek, face readable: warmth → PASS.
20. A shot where the hero dish differs from the previous plate: PASS, placement note only.

And real fails: the same beautiful pour shot with a crew member's reflection in the glass (D9); a shallow-focus portrait where the focus plane sits on the ear behind the eye (D2); a "slow motion" made from 25 fps footage whose hands melt between frames (D5).
