# Sound and music: the engine of the cut

Read this before choosing music, cutting to it, or mixing. Numbers marked **[heuristic]** are working values from practice, not standards. Everything else comes from a standard, a vendor document, or published research. Shared numbers (on-beat window, loudness, foley level) are in `numbers.md` §4 and §7.

**If you cannot hear.** An agent cannot listen to music. Then the tempo and especially the downbeats from `beats.py` are a **guess**. Either ask the human to confirm the tempo and bar 1 (one sentence: "Is the first strong beat at 8.96 s?"), or keep cuts on action and phrase-level energy changes rather than on individual beats, and say in the report that the grid was not verified by ear.

## Contents
1. Music choice
2. Decode once
3. Cutting to music
4. Music edits
5. Sound design for premium films
6. Slow-motion sound
7. Loudness targets
8. Phone-speaker test
9. Checks an agent must run
10. Sources

---

## 1. Music choice

**Licence gate first.** Before a track goes on the timeline, confirm the licence explicitly covers: paid social ads (many subscription tiers exclude paid advertising or broadcast), the client's territory and term, broadcast if needed, and both master and publishing rights. Record the licence ID in the project notes. Never temp with music you cannot license: clients fall in love with the temp ("demo love").

**What to look for** [heuristic]:
- A clear arc inside the needed length: quiet first bar under the first shot, a structural change near 60–70 % of the duration for the reveal, energy in the last 25 % above the first 25 % (or a deliberate resolution).
- A real ending ("button"), not a fade.
- Room for VO or text: instrumental version or a vocal that leaves space.
- Not the library's top-trending tracks for premium brands.
- Sector starting points only: food warm acoustic or percussive; hospitality 70–100 BPM, room and air; fashion minimal electronic or strong groove; product precise rhythmic textures.

**Prefer tracks that ship with stems and 15/30/60 s cutdowns.** Check the library's own cutdowns before editing by hand. Stems let you drop vocals under VO, pull a distracting lead, or bring drums in at the reveal. Without stems, a separator (Demucs `htdemucs_ft`, `--two-stems=vocals`) works, but separated stems lose quality and bass bleeds; the Demucs repo is no longer maintained.

**Material first, music second.** Many top commercial editors find the action's natural pace before music, or mute the track until the picture works. Build the first assembly at the action's natural length; conform to phrases after the structure works. A track that dictates every cut makes the edit lazy.

## 2. Decode once

MP3 and AAC decoders add different start delays (LAME ≈ 1105 samples ≈ 25 ms at 44.1 kHz; AAC priming 2112 samples ≈ 48 ms). If analysis and edit use different decodes, the beat grid shifts by a frame or more.

- Run `scripts/beats.py track.mp3 --fps <timeline fps> --out music/`. It decodes **once** to `music/music.wav` and analyses that file.
- **Put `music/music.wav` in the edit**, not the MP3. Check: the analysed file and the timeline file have the same sample count.
- Use the exact timeline rate (23.976 / 29.97 as rationals 24000/1001, 30000/1001). Compute frames from seconds; never from timecode strings (drop-frame drops labels, not frames). Store `music_offset_frames` if the music does not start at frame 0.

**Tracker pitfalls:**
- Half/double tempo errors: if the BPM looks wrong, choose the tempo where one 4/4 bar lasts 1.6–3.2 s (75–150 BPM) and pass `--bpm`.
- Downbeats are much less reliable than beats (state of the art: downbeat F1 ≈ 78 vs beat F1 ≈ 89). `beats.py` downbeats are a **guess**: a human listens and you pass `--first-downbeat <seconds>` if bar 1 is wrong. Without a human ear, do not hang the hero moment on a single guessed downbeat; place it on a clear energy change in the curve.
- Benchmark tolerance is ±70 ms (≈ 2 frames at 25 fps). For hero hits, snap to the strongest onset within ±50 ms of the beat.
- Waltz or 6/8: `--beats-per-bar 3` (or 6).
- Rubato, ambient, orchestral without drums: trackers fail; cut on phrase swells, onsets and the energy curve instead of a grid.

## 3. Cutting to music

**Timing: 0–2 frames early counts as on beat** (`numbers.md` §4). Viewers first detect sound leading picture at ≈ +45 ms and sound lagging picture at ≈ −125 ms (ITU-R BT.1359). One frame is 33–42 ms. So:
- Picture cut 0–1 frame early (picture leads by up to 42 ms): the beat lands "on" the shot. Default.
- 2 frames early: still on beat.
- 2 frames late (sound leads by 67–83 ms): beyond detection; the cut feels sluggish.
- Default `cut_frame = round(t_beat × fps) − k`, k = 0, 1 or 2. Never ≥ 2 frames late unless flagged as deliberate.

**Phrases for structure.** A 4-bar group is a phrase unit, 8 bars a full phrase. Bar seconds = 60 / BPM × beats per bar (120 BPM: bar 2.0 s, 4 bars 8.0 s).
- Act or scene changes go on 4- or 8-bar boundaries (`beats.py` lists phrase starts).
- Shot changes go on downbeats or beat 3.
- Accents (pour, door, fabric swing) can sit on an off-beat or snare.
- Room for change [heuristic]: 15 s spot 1–2 phrase changes, 30 s 3–4, 60 s intro / A / B / outro. No structural change more often than every 4 bars.

**Density variation.**
- Every-beat cutting is the densest setting: use it only in short builds (≤ 4 consecutive every-beat cuts outside a marked build) [heuristic].
- Median shot ≥ 2 beats for food and hospitality, ≥ 1 beat for fashion/product montage [heuristic].
- Shot lengths must vary; low variance reads mechanical. Use the `beats.py` energy curve: calm shots in low-energy sections, fast cuts and hero shots at peaks.

**On-beat share 50–70 %.** Viewers enjoy cuts aligned with beats more, but cutting every cut on the downbeat feels mechanical. Aim for roughly 50–70 % of cuts on a beat (on time or up to 2 frames early); let the rest fall on action or phrase. This is a warning, not a target: write why if a film needs another share. Cutting a few frames late on purpose relaxes a poetic or hospitality film.

**Hero moment.** Put exactly one hero moment (reveal, first bite, product, logo) on a downbeat that follows a drop, silence or stem change of ≥ 2 beats, or deliberately against the grid. Never let it fall 3–5 frames off by accident. Silence before key information improves recall (Olsen 1995). Taking music away at the peak is a legitimate move.

**Ending.** The end card lands on the music's resolution, never on an abrupt stop. For loops, avoid a final-sounding hit and match last frame to first.

## 4. Music edits

- **Splice on downbeats**, same beat position in the bar, ideally the same section type (verse to verse). Every seam within 10 ms of a downbeat.
- **Cut first, then crossfade the seam.** Crossfade lengths [heuristic]:
  - transient on the downbeat: 5–20 ms, so the hit survives;
  - pads or sustained sections: 50–200 ms equal-power;
  - never across a sung word.
- **Reverb tails:** if the removed section's tail cuts off, extend the outgoing clip under the incoming one at −10 to −15 dB for one beat.
- **Back-timing:** lay the track's real ending so it finishes on the film's last frame (plus ≥ 0.5 s tail or room tone under an end card), lay the real start, hide the join on a downbeat inside the body. Total music length = whole bars ±1 beat.
- **No clicks:** sample delta at each seam below −20 dBFS of the local level; listen on headphones.
- Remix tools that auto-stitch and time-stretch work better on instrumentals than on vocal tracks.
- Never cut a musical sentence mid-phrase to fit a shot; move the shot.

## 5. Sound design for premium films

Premium brand films are **reduction**: real room tone, foley and silence, with music that builds. Cheap films are wall-to-wall stock music, flat energy and no sound of the world.

**Barely-there real foley from on-screen objects.** Pour, sizzle, crunch, cutlery, glass on marble, cloth, footsteps on stone, a door latch.
- Sit it 10–20 dB below the music's peaks, felt more than noticed [heuristic].
- Hit 1–3 hero sounds harder (first bite, cork, product click).
- Every sound comes from an object visible in the shot (or the next one). Use the shot's own production sound where clean; `render.py` can mix real shot sound under the music.

**Room tone and ambience are glue.** A continuous low bed per location (room, kitchen hum, sea) hides edit points and makes a montage one place. No gaps of digital silence longer than 1 frame unless the silence is the effect. Ambient sound starts at frame 0; never open on accidental silence (viewers check their volume).

**No stock whooshes, risers or impact hits. Ever.** They signal a template, announce the cut instead of hiding it, and come from no object. Premium alternative: the next shot's real sound started 2–8 frames before the cut (a J-cut). Zero whoosh/riser assets.

**Silence as a tool.** One sound-led moment or a short silence/dropout (0.5–2 s) mid-film in films ≥ 20 s: drop the music, let one real sound carry. Silence works mid-film, not at frame 0.

**J/L cuts.** J-cut: next shot's audio starts before its picture. L-cut: outgoing audio continues over the new picture. At least one 2–12 frame sound bridge in any film over 15 s [heuristic]. A missing bridge on an L-cut feels "incomplete".

**Murch layer budget.** About five sound layers spread across the spectrum stay clear; about 2.5 layers of the same kind merge into a group. At any moment: ≤ 5 concurrent families (e.g. music, VO, hero foley, ambience, one accent) and ≤ 2 layers in one family.

**Speech beats music.** While VO/dialogue plays, music sits ≥ 8 LU below speech (short-term): duck 6–10 dB with 100–300 ms ramps, or mute the music's vocal stem [heuristic].

**Source music in the venue** (a restaurant's speakers) should sound like the room, not a studio master: band-pass ≈ 150 Hz–6 kHz, small-room reverb, −6 to −12 dB [heuristic].

**First 3 seconds.** Sound-on hook plus a sound-off visual hook (many people watch muted). No harsh transient in the first 3 s (true peak > −3 dBTP with < 10 ms rise): TikTok's ad guidance warns against sudden harsh sounds and against fully silent ads.

## 6. Slow-motion sound

- **Never** let speed-changed audio through by accident: a conformed 50p/120p clip carries pitched-down, smeared or chipmunk sound. When a shot is retimed, **drop its sync sound** (mute or remove the audio of retimed shots by default).
- Either let music carry the slow section, or **design** the sound: real-speed foley of the same action placed to the slowed picture, low and soft, or a stretched texture made on purpose (time-stretch without pitch change), never an accidental artefact.
- Follow a slow-motion moment with real time and real sound: the room "rushes back in". This contrast is what makes slow motion feel premium.
- Speed ramps: design the sound into the ramp across a real event (pour, toss, flame); about 1–2 ramps per 15 s (`numbers.md` §1).

## 7. Loudness targets

Measure with ITU-R BS.1770 (ffmpeg `ebur128` or `loudnorm`). `render.py` normalises in two passes to `--lufs` (default −14) with true peak −1.5 dBTP; `qc.py` reports integrated LUFS and true peak.

| Destination | Integrated | True peak | Status |
|---|---|---|---|
| EBU R128 (EU and many other broadcasters) | −23 LUFS ±0.5 LU | ≤ −1 dBTP | official standard |
| ATSC A/85 (US broadcast, CALM Act) | −24 LKFS ±2 | ≤ −2 dBTP | official; check the current revision |
| Netflix (long-form reference) | −27 LKFS dialogue-gated ±2 | ≤ −2 dBTP | official delivery spec |
| YouTube | plays at a −14 LUFS reference; loud uploads turned down, quiet ones mostly not boosted | none published | observed behaviour, no published spec |
| Spotify (music) | −14 LUFS normal | below −2 dBTP if louder than −14 | official |
| Instagram / Facebook Reels | **no official spec**; convention −14 (−16 to −12) | −1 dBTP convention | convention only |
| TikTok | **no official number**; qualitative: sound on, no harsh sounds in first 3 s | — | qualitative official guidance |

Working rules:
- **Social/web master:** −14 ±1 LUFS, true peak ≤ −1 dBTP (−1.5 to −2 preferred, because platforms re-encode to AAC). Louder masters only get turned down and lose punch.
- **Broadcast:** use the broadcaster's spec (−23/−1 EBU, −24/−2 US). Never send the social master to TV.
- **Two-pass loudnorm:** pass 1 measures, pass 2 applies with `linear=true`. Linear mode is only a request: read `normalization_type` in the pass-2 JSON. If it says `dynamic`, the filter compressed the audio; lower the target, loosen the peak, or use plain gain plus a limiter.
- Do not trust NLE "auto-match" loudness for the master (fixed targets, fails on short clips); use a loudness meter or ffmpeg.
- With no VO, the music carries the integrated level and foley sits under it.

## 8. Phone-speaker test

Most social viewing is on phone speakers, which roll off below ≈ 150–200 Hz. Simulate it and listen:

```bash
ffmpeg -i film.mp4 -af "highpass=f=200,lowpass=f=7000" -c:v copy phone_check.mp4
```

Pass when the hero sounds and the music's identity (melody, groove) survive and VO intelligibility is unchanged. If the track's identity lives only in sub-bass, it will vanish on phones: pick another track or bring up a mid-range element (stem). Also do one real phone check before delivery.

## 9. Checks an agent must run

1. **Licence** recorded: paid social / territory / term / broadcast; master and publishing.
2. **Decode once:** timeline uses `music/music.wav` from `beats.py`; sample counts match.
3. **Tempo sanity:** bar length 1.6–3.2 s; otherwise fix with `--bpm`. Downbeat confirmed by a human ear and `--first-downbeat`, or reported as unverified.
4. **Frame math** from seconds with the exact timeline fps (rational for NTSC) plus music offset.
5. **Cut timing:** 50–70 % of cuts on a beat at 0–2 frames early; no cut ≥ 2 frames late unless flagged; ≤ 4 consecutive every-beat cuts outside a build.
6. **Structure:** act changes on 4/8-bar boundaries ±1 frame; music length whole bars ±1 beat; ending back-timed to the last frame; end card on the resolution.
7. **Splices:** on downbeats ±10 ms, same section type, crossfades per section 4, no click.
8. **Hero moment:** one, on a downbeat after a drop/silence/stem change ≥ 2 beats, or flagged against the grid.
9. **Sound design:** room tone under every location, no digital-silence gaps > 1 frame, ≥ 1 J/L cut in films > 15 s, one dropout or sound-led moment in films ≥ 20 s, zero stock whooshes/risers, ≤ 5 families and ≤ 2 layers per family.
10. **Slow motion:** no retimed sync audio in the mix.
11. **VO:** music ≥ 8 LU under speech while it plays.
12. **First 3 s:** sound-on hook, no harsh transient, not silent; a sound-off visual hook exists.
13. **Loudness:** `qc.py film.mp4 --lufs -14` (or the broadcast target): integrated within ±1 LU (±0.5 for EBU), true peak at or under the limit, `normalization_type` linear.
14. **Phone-speaker test** passed.
15. **Listen to the whole film once** on headphones and once on a phone speaker before anyone else sees it. If you cannot listen, ask the human to, and report it as not checked.

## 10. Sources

- ITU-R BT.1359 (audio/video sync detectability): https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.1359-1-199811-I!!PDF-E.pdf
- EBU R128: https://tech.ebu.ch/docs/r/r128-2014.pdf
- ATSC A/85: https://www.atsc.org/wp-content/uploads/2026/07/A85-2026-07.pdf
- Netflix sound mix spec: https://backlothelp.netflix.com/hc/en-us/articles/360001794307-Netflix-Sound-Mix-Specifications-Best-Practices-v1-5
- Spotify loudness normalisation: https://support.spotify.com/artists/article/loudness-normalization/
- YouTube loudness behaviour: https://productionadvice.co.uk/stats-for-nerds/
- TikTok ad sound guidance: https://ads.tiktok.com/help/article/tiktok-reservation-topview
- Walter Murch, "Dense Clarity – Clear Density": https://transom.org/2005/walter-murch/
- Olsen 1995, silence and recall in ads: https://asu.elsevierpure.com/en/publications/creating-the-contrast-the-influence-of-silence-and-background-mus/
- Beat This! beat tracker: https://arxiv.org/html/2407.21658v1
- AAC priming / encoder delay: https://developer.apple.com/documentation/quicktime-file-format/appendix_g_audio_priming_handling_encoder_delay_in_aac.md
- Two-pass loudnorm: https://dev.to/masonwritescode/two-pass-loudness-normalization-with-ffmpeg-loudnorm-the-right-way-1nm3
- Professional critiques of AI-made ads: https://arxiv.org/html/2608.24329
