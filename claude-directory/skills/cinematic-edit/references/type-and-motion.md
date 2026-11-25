# Type and motion for cinematic films

**Most films carry text only on the end card**, and it arrives with one simple opacity rise. Everything else in this file is for the rarer films whose brief asks for more. Do not reach for the presets because they exist.

Read this before you put any word on screen. Text in a cinematic brand film is rare, small, still and exact. Frame counts are **@30 fps (@25 fps in brackets)**; for 24 fps use the 25 fps value. Shared numbers (read time, end-card hold) are in `numbers.md` §2 and §8.

**How text gets into the film.** `render.py` does not typeset. It overlays **pre-designed PNG layers** (end card, logo, slogan) through the plan's `overlays` field, with opacity fades only: no movement, no scale, no blur. Design those layers elsewhere: in Remotion or HyperFrames (sections 10–11), or in a design tool, or use the client's supplied end card exported 1:1. A still image (a supplied end card or photo) can also be a shot of its own. Exact keys: `templates/edit_plan.example.json` and `render.py --help`. Anything that animates beyond an opacity rise is rendered in Remotion/HyperFrames or the NLE.

## Contents
1. The rules that override everything
2. Font choice and pairing
3. Glyphs: Turkish and Latin Extended
4. Sizes, safe zones, tracking, leading
5. Placement and legibility without boxes
6. How text enters, holds and exits
7. The 14 cinematic presets
8. Stagger
9. Anti-patterns
10. Code: four presets in Remotion
11. HyperFrames / GSAP equivalents
12. Checklist
13. Sources

---

## 1. The rules that override everything

1. **Ads carry the slogan only.** No product names, no descriptor lines, no ingredient lists, no "new", no price unless the brief says so. A logo may sit in a corner or on the brand's own closing card.
2. **Never add words to client copy.** Use the brand's own slogan and closing text exactly as supplied: same words, same order, same capitalisation. Never invent a slogan.
3. **The final frame equals the supplied layout.** If the client supplied a PSD, AI, PNG or end card, export its layers 1:1 at their canvas positions and animate only those. Do not re-typeset supplied text in another font. Verify the last frame against the layout with a pixel diff.
4. **No dark boxes, gradients, vignettes, strokes or blotches behind text.** Legibility comes from choosing the place and the colour. At most a tight shadow: 1–2 px offset, ≤ 2 px blur, ≤ 40% opacity. A global grade of the whole shot is allowed; a local darkening patch is not.
5. **Text never moves while it is being read.** It arrives, lands and is dead still. Life in the frame comes from the footage or a slow camera push on the plate, never from the type.
6. **Effects are barely there.** If a viewer can name the effect, it is too strong.
7. **One idea, one treatment.** One typographic system per film, one entrance family per film, no decoration.
8. **Use brand assets.** Logo, font and colours come from the brand's files. Never redraw a logo with a font. Place a supplied logo file as-is (no shadow, halo, outline or recolouring), sized and positioned by measurement.
9. **Show one still of the final layout first** when the type is self-designed. Animate only after the layout works as a still. Offer one best design, not a fan of options.

## 2. Font choice and pairing

**If the brand has a font, use it.** Otherwise choose one of these two premium systems:

| System | Display line | Secondary line | Feels |
|---|---|---|---|
| A. Thin serif | Light or regular serif, or its italic (Cormorant, Playfair Display 400 italic, EB Garamond, Libre Caslon, Bodoni Moda 400) | none, or small tracked caps sans | hotel, fine dining, fashion, jewellery |
| B. Small tracked caps | Small all-caps sans, 400–500, tracked 0.15–0.3em (Inter, Manrope, Montserrat 500, Jost) | none, or one thin serif word | architecture, product, modern restaurant |

Rules:
- Maximum two faces. Never a third. No monospace "label" chips.
- Text colour is taken from the image (cream, warm off-white, stone, a dark ink on light plates), not pure #FFFFFF.
- **Not by default:** Bebas Neue, Anton, Impact, heavy condensed sans, TikTok-caption styles (heavy uppercase, thick black stroke, neon active word), bouncy kinetic type, rotating titles. Use a heavy face only when it is the brand's own font or the brief asks for a loud register (fast food, sport, nightlife), and then keep the same restraint in motion.
- Avoid the "generated template" look: cream paper background + serif display + italic accent word + 01/02 numbering + mono caps labels + pill chips.
- At most one word in an accent colour, and only if the brand colours include it.

## 3. Glyphs: Turkish and Latin Extended

- Google fonts in Remotion: `loadFont("normal", { weights: ["400"], subsets: ["latin", "latin-ext"] })`. The `latin` subset alone lacks ğ, ş, ı, İ, ő, ł, ř and others.
- Local or brand fonts: `@remotion/fonts` `loadFont({ family, url: staticFile(...), weight, style, display: "block" })`, once per weight.
- Before measuring with `measureText` / `fitText`, wait for the fonts to load. Pass the same `fontWeight`, `letterSpacing` and `textTransform` to the measure call as to the element.
- Mask boxes (`overflow: hidden`) need about **1.5 em** of height, so the dot of İ, the breve of Ğ and the cedillas of Ç/Ş are not clipped.
- Uppercase Turkish needs the locale: `text.toLocaleUpperCase("tr-TR")` turns i into İ (a plain `toUpperCase()` gives I).
- Render a still containing every special glyph of the copy and zoom to 200% before rendering the film.
- Rotating or flipping letters can briefly form real words. If letters animate individually, scan the transition frame by frame.

## 4. Sizes, safe zones, tracking, leading

**Sizes (font size in px).**

| Element | 1080×1920 (9:16) | 1920×1080 (16:9) |
|---|---|---|
| Slogan, thin serif | 80–120 | 56–96 |
| Slogan, small tracked caps | 40–64 | 32–52 |
| Secondary caps line (if any) | 28–40 | 22–32 |
| Absolute floor for any text | 28 | 28 |
| Logo width (corner) | 140–220 | 160–260 |

Fit long lines with `Math.min(fitText(...).fontSize, MAX)`; never let fitting push a slogan above the table's maximum.

**Safe zones.**

| Format | Keep text out of | Usable band |
|---|---|---|
| 9:16 organic Reels/TikTok | top 250 px, bottom 340 px, sides 80 px | y 250–1580 |
| 9:16 paid ads | top 270 px, bottom 672 px, sides 65–80 px | y 270–1248 |
| 16:9 | top and bottom 100 px, sides 140 px | x 140–1780, y 100–980 |

Always preview the final frame with a platform UI overlay, or at least these rectangles drawn on a still.

**Tracking.**
- Thin serif display: 0 to +0.02em. Never negative on thin serifs.
- Small caps lines: +0.15 to +0.3em.
- Never track lowercase body text.

**Leading.**
- Display lines: 1.0–1.1. Captions: 1.2–1.4.
- One or two lines per card. Never split a sentence across scenes. No small secondary line under a hero sentence.

**Read time.** A line holds 0.5 s + 0.3 s per word after it has landed, and at least 2 s overall (60 [50] frames). The last text of the film holds ≥ 2 s.

## 5. Placement and legibility without boxes

1. Plan text space at the edit stage: choose a shot with calm negative space (sky, wall, sea, tablecloth, dark wood) where the text goes.
2. Measure the plate under the text box: mean luminance and its standard deviation across the whole hold (not one frame).
   - Mean L > 0.6: use dark ink. Mean L < 0.4: use light text. In between: move the text or choose another shot.
   - Std dev > 0.15 (busy texture): move the text.
3. Never place text over faces, the product or the plate centre.
4. Centre by measurement: compute the visible bounding box of the glyphs (not the line box) and centre that. Check top/bottom and left/right margins numerically.
5. A text that sits on a surface in the scene (a table, a wall, a bar top) may follow its perspective slightly. Only do this with a locked shot.
6. If legibility still fails, you may lift the shot's global exposure or contrast a little. Never paint a local patch.

## 6. How text enters, holds and exits

- **Entrances:** default is a soft opacity rise (8–12 frames). Only when the brief asks for more: a mask rise, a glyph-by-glyph form, or tracking-in caps. All entrances land fully crisp (blur exactly 0, scale exactly 1).
- **Hold:** dead still. No drift, no breathing, no pulse, no scale creep.
- **Exit:** 40–50% of the entrance length, or carried by the cut. A slogan may leave on a cut to the next shot; that is the cleanest exit.
- **Fixed-title system:** a thin serif title sits in one place while the shots underneath change by hard cuts (45–60 frames each @24/25). The title arrives with a 12-frame opacity rise, never moves, and fades over another shot at the end. This is the backbone of many premium place films.
- **Timing:** multi-element layouts have every element landed within 3 s (90 [75] frames), with irregular, overlapping starts. Name or slogan first; logo last.
- **Blur** is allowed only on large display layers or photos, ≤ 6 frames, ending at exactly 0. Never on thin serif or small caps.
- Text arrives on a calm moment of the shot, never during a fast camera move.

## 7. The 14 cinematic presets

Presets 1–2 and 13 cover almost every film. The rest exist for briefs that need them; one entrance family per film.

| # | Preset | Values | @30 fps | @25 fps | Use |
|---|---|---|---|---|---|
| 1 | `SETTLE` | `Easing.bezier(0.16, 1, 0.3, 1)` (expo-out) | 18–24 (punchy 9–12) | 15–20 (8–10) | default arrival of a line or layer |
| 2 | `SOFT_SETTLE` | `Easing.bezier(0.22, 1, 0.36, 1)` | 20–30 | 17–25 | prestige brands, supplied layout layers |
| 3 | `GLIDE` | `Easing.bezier(0.65, 0, 0.35, 1)` or `Easing.inOut(Easing.cubic)` | 22–40 | 18–33 | masks, wipes, repositioning |
| 4 | `PUSH` | scale 1.00 → 1.04–1.08 (on at most a third of shots, `numbers.md` §5), `Easing.inOut(Easing.sin)`, `output: "perceptual-scale"` | whole shot, 90–150 | 75–125 | the only continuous motion, on the plate |
| 5 | `EXIT` | `Easing.bezier(0.7, 0, 0.84, 0)` (expo-in) | 7–10 | 6–8 | lines leaving with the scene |
| 6 | `SPRING_PREMIUM` | `spring({ config: { damping: 200 } })`, or `{ damping: 17, stiffness: 100, mass: 1, overshootClamping: true }` (ζ ≈ 0.85) | 20–30 via `durationInFrames` | 17–25 | position or size only, never opacity |
| 7 | `MASK_RISE` | translate 100% → 0 inside an `overflow: hidden` 1.5em box, with SETTLE or SOFT_SETTLE; opacity over the first half | 20 (punchy 9 in / 7 out) | 17 (8 / 6) | slogan lines |
| 8 | `TRACK_IN` | letterSpacing `ls × 2.4 → ls` plus opacity, SOFT_SETTLE | 14–18 | 12–15 | small tracked caps |
| 9 | `GLYPH_FORM` | per-letter opacity 0 → 1, 1–3 frame stagger, no blur at rest | 12–20 total | 10–17 | names, brand words that must stay crisp |
| 10 | `FOCUS_PULL` | blur ≤ 8 px → 0 plus opacity, SOFT_SETTLE | 6–20 | 5–17 | large display layers and photos only |
| 11 | `FEATHER_WIPE` | gradient mask sweep, GLIDE | 22–30 | 18–25 | revealing a layout layer or photo region |
| 12 | `STAMP_SETTLE` | scale 1.08 → 1, `Easing.out(Easing.cubic)` | 6–8 | 5–7 | one date or figure on a beat, once per film |
| 13 | `XFADE` | `fade()` with `linearTiming` or `springTiming({ config: { damping: 200 }, durationRestThreshold: 0.001 })` | 15–45 | 13–38 | motivated scene seams only |
| 14 | `MOTION_BLUR` | `<HtmlInCanvasMotionBlur shutterAngle={180} samples={8}>` | — | — | only on moves faster than about 40 px/frame, never on resting type |

Damping ratio ζ = damping / (2 × √(stiffness × mass)). Remotion's default spring (damping 10, stiffness 100) is ζ = 0.5: playful. Never leave `config` empty. Use ζ ≥ 0.85 or `damping: 200`, with `overshootClamping: true`.

Always clamp `interpolate()` with `extrapolateLeft` and `extrapolateRight: "clamp"`. Derive every value from the frame; no CSS animations.

## 8. Stagger

| Unit | Stagger @30 | @25 |
|---|---|---|
| Letters (GLYPH_FORM) | 1 frame (names: 3) | 1 (names: 2–3) |
| Words | 2–4 frames | 2–3 |
| Lines or layout elements | irregular, e.g. 0 / 4 / 9 / 11 / 17 / 26 | 0 / 3 / 8 / 9 / 14 / 22 |

Never use a constant step: it reads robotic. The next element starts when the previous one is 30–50% done. Everything has landed by 90 [75] frames.

## 9. Anti-patterns

**Type.** Text moving while it is read; titles drifting after they land; breathing or pulsing loops; beat-pulsing type; bouncing letters; slot-machine digits; spinning clocks; rotating titles; heavy captions with black strokes; big text over faces; many words; blur on thin type; glow, bloom or neon; soft drop shadows; upscaled raster text; decorative dashes, rules, brackets, underlines or frames around text; numbering such as 01/02; extra words added to client copy; product descriptor lines in ads.

**Layout.** Dark boxes, local gradients, vignettes or lower-third bars behind text; everything centred and fading in at once; every element fading and sliding up the same way; layers revealed one by one from top to bottom; PowerPoint-like sequential cards; a sentence split across scenes; a small secondary line under the hero line; corner labels and HUD furniture.

**Motion.** Overshoot, back, elastic or bounce easing; the default spring; fast jumpy moves; an element changing position between scenes; small unmotivated jumps of a few pixels; linear digital zooms; zoom pulses on the beat; decorative transitions (glitch, RGB split, pixelate, checkerboard, clock wipe, light-leak packs) as default seams; painterly or watercolour filters on real footage.

## 10. Code: four presets in Remotion

```ts
// motion.ts — premium presets; frame values @30 fps
import { Easing, interpolate, spring } from "remotion";

const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
export const EASE = {
  settle: Easing.bezier(0.16, 1, 0.3, 1),
  soft: Easing.bezier(0.22, 1, 0.36, 1),
  glide: Easing.bezier(0.65, 0, 0.35, 1),
  exit: Easing.bezier(0.7, 0, 0.84, 0),
};

/** 0 → 1 over [start, start + len] with a named curve. */
export const t = (frame: number, start: number, len: number, ease = EASE.settle) =>
  interpolate(frame, [start, start + len], [0, 1], { ...CLAMP, easing: ease });

/** Settled spring for position/size. Never for opacity. */
export const settled = (frame: number, fps: number, start: number, len = 24) =>
  spring({ frame: frame - start, fps, durationInFrames: len,
    config: { damping: 17, stiffness: 100, mass: 1, overshootClamping: true } });
```

```tsx
// SloganRise.tsx — MASK_RISE: line rises from behind its own baseline, then stays still
import { useCurrentFrame } from "remotion";
import { t, EASE } from "./motion";

export const SloganRise: React.FC<{ text: string; start: number; size: number;
  family: string; color: string }> = ({ text, start, size, family, color }) => {
  const frame = useCurrentFrame();
  const p = t(frame, start, 20, EASE.soft);
  return (
    <div style={{ height: size * 1.5, overflow: "hidden" }}>{/* room for İ Ğ Ş Ç */}
      <div style={{ fontFamily: family, fontSize: size, lineHeight: 1.5, color,
        translate: `0 ${(1 - p) * 100}%`, opacity: Math.min(1, p * 2) }}>
        {text}
      </div>
    </div>
  );
};
```

```tsx
// CapsTrackIn.tsx — TRACK_IN: small caps tighten into place
import { useCurrentFrame } from "remotion";
import { t, EASE } from "./motion";

export const CapsTrackIn: React.FC<{ text: string; start: number; size: number;
  trackEm: number; family: string; color: string }> = ({ text, start, size, trackEm, family, color }) => {
  const frame = useCurrentFrame();
  const p = t(frame, start, 16, EASE.soft);
  const ls = size * trackEm;
  return (
    <div style={{ fontFamily: family, fontSize: size, color, opacity: p,
      letterSpacing: ls * (2.4 - 1.4 * p) }}>
      {text.toLocaleUpperCase("tr-TR")}
    </div>
  );
};
```

```tsx
// PlatePush.tsx — PUSH: the only continuous motion lives on the footage
import { AbsoluteFill, Easing, OffthreadVideo, interpolate, staticFile,
  useCurrentFrame, useVideoConfig } from "remotion";

export const PlatePush: React.FC<{ src: string; to?: number }> = ({ src, to = 1.05 }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const scale = interpolate(frame, [0, durationInFrames - 1], [1, to], {
    extrapolateRight: "clamp", easing: Easing.inOut(Easing.sin), output: "perceptual-scale" });
  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <OffthreadVideo src={staticFile(src)} style={{ width: "100%", height: "100%",
        objectFit: "cover", scale }} />
    </AbsoluteFill>
  );
};
```

Keep the push inside the source's resolution headroom (see the finishing limits: never above 100% of native pixels on hero, face or product shots). Do not push shots that already have a camera move.

## 11. HyperFrames / GSAP equivalents

| Preset | GSAP |
|---|---|
| SETTLE | `ease: "expo.out"` |
| SOFT_SETTLE | `CustomEase.create("soft", "0.22,1,0.36,1")` |
| GLIDE | `ease: "power2.inOut"` or `CustomEase "0.65,0,0.35,1"` |
| EXIT | `ease: "expo.in"` |
| PUSH | `gsap.fromTo(plate, { scale: 1 }, { scale: 1.05, ease: "sine.inOut", duration: shotSeconds })` |

Never use `back`, `elastic` or `bounce` eases. Durations in GSAP are seconds: frames ÷ fps.

## 12. Checklist

- [ ] Text is the brand's slogan only, exactly as supplied; no added words; no descriptor lines.
- [ ] Final frame matches the supplied layout (pixel diff) or the approved still.
- [ ] Brand font, or one of the two premium systems; ≤ 2 faces; no Bebas/heavy caption style by default.
- [ ] `latin-ext` loaded; every special glyph checked at 200%; masks 1.5 em tall.
- [ ] Sizes inside the table; text inside the safe band for the placement.
- [ ] Plate luminance and texture measured under the text box; no box, gradient, stroke or patch; shadow ≤ 2 px.
- [ ] Every element landed within 90 [75] frames, irregular starts; text still while read; hold ≥ 2 s.
- [ ] Eases from the preset table; springs ζ ≥ 0.85 with overshoot clamped.
- [ ] No anti-pattern from section 9; every effect barely there.
- [ ] Stepped through frame by frame: no clipped glyphs, no accidental words, no jumps.

## 13. Sources

- Remotion timing and easing: https://www.remotion.dev/docs/interpolate
- Remotion spring: https://www.remotion.dev/docs/spring
- Remotion fonts: https://www.remotion.dev/docs/fonts
- Remotion layout utils (`fitText`): https://www.remotion.dev/docs/layout-utils/fit-text
- Remotion transitions: https://www.remotion.dev/docs/transitions/presentations
- Remotion motion blur: https://www.remotion.dev/docs/motion-blur
- GSAP eases: https://gsap.com/docs/v3/Eases/
- Instagram Reels safe zones (ads): https://www.socialync.io/tools/safe-zones/instagram-reels
