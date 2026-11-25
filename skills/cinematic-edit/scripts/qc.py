#!/usr/bin/env python3
"""qc.py: check a rendered film before anyone sees it.

The film is decoded once (every frame, small) and checked for:
  - length: video frames vs the plan's exact frame count, video vs audio duration
  - frame-repeat judder: in each shot, frame differences that alternate in a
    period of 2-4 (one frame moves, the next is a copy) - works on slow, gentle
    motion too, because it compares phases, not an absolute threshold
  - black frames, frozen stretches, sudden jumps inside shots (flash frame,
    warp, interpolation tear), flash shots under 0.25 s
  - picture that still measures like log (flat, grey, no colour)
  - loudness (integrated LUFS within +-1 LU of the target, true peak <= -1 dBTP)
  - colour tags (BT.709), size, fps
  - per shot: sharpness (contrast-normalised), exposure, colour; colour jump at each cut

Sheets (paged so every frame stays readable):
  contact.png, contact_p2.png ...  a frame every N frames
  cuts.png, cuts_p2.png ...        last frame before / first frame after every
                                   cut; for a dissolve, before it starts / after it ends
  slow_shotNN.png ...              every frame of each slowed or ramped shot (with --plan)
  still_hero.png, still_end.png    full-resolution frames for the critic (with --plan)
  qc.json                          all numbers

Usage:
  python3 qc.py film.mp4 --out qc/ [--plan edit_plan.json] [--every 4] [--lufs -14]

With --plan, cut points (dissolve-aware) and shot lengths come from the plan;
otherwise cuts are detected. Exit code 1 when a hard problem is found.
Read-only; no network.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (find_tool, ffprobe_json, video_stream, rational, write_json, fmt_tc, font,  # noqa: E402
                     scale_in_opts, layout, parse_fps, is_still)
from reference import cut_scores, detect_cuts  # noqa: E402

PAGE_FRAMES = 40


def decode_all(path, vs, width=240):
    """Every frame as small RGB (memmap on disk). Returns (frames, raw_path)."""
    w, h = int(vs["width"]), int(vs["height"])
    from _common import rotation_of
    if rotation_of(vs) in (90, -90, 270, -270):
        w, h = h, w
    W = width
    H = max(2, int(round(h * W / float(w))) // 2 * 2)
    fd, raw = tempfile.mkstemp(prefix="ce_qc_", suffix=".rgb")
    os.close(fd)
    p = subprocess.run([find_tool("ffmpeg"), "-v", "error", "-y", "-i", path, "-vf",
                        "scale=%d:%d:flags=area:%s,format=rgb24" % (W, H, scale_in_opts(vs)),
                        "-f", "rawvideo", "-pix_fmt", "rgb24", raw], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        os.unlink(raw)
        raise RuntimeError(p.stderr.decode("utf-8", "replace")[-800:])
    n = os.path.getsize(raw) // (W * H * 3)
    return np.memmap(raw, dtype=np.uint8, mode="r", shape=(n, H, W, 3)), raw


def sheet_pages(frames, idx, labels, out_base, title, cols, tw):
    """Paged grid of frames[idx]. Returns written paths."""
    from PIL import Image, ImageDraw
    if not idx:
        return []
    H, W = frames.shape[1:3]
    th = int(round(H * tw / float(W)))
    per = max(cols, PAGE_FRAMES // cols * cols)
    paths = []
    pages = [list(range(i, min(i + per, len(idx)))) for i in range(0, len(idx), per)]
    for pi, pg in enumerate(pages, 1):
        rows = (len(pg) + cols - 1) // cols
        pad, lab = 4, 16
        im = Image.new("RGB", (cols * (tw + pad) + pad, 26 + rows * (th + lab + pad) + pad), (14, 14, 14))
        d = ImageDraw.Draw(im)
        d.text((pad, 5), "%s  (page %d/%d)" % (title, pi, len(pages)), fill=(235, 235, 235), font=font(13))
        for k, j in enumerate(pg):
            x = pad + (k % cols) * (tw + pad)
            y = 26 + (k // cols) * (th + lab + pad)
            fr = Image.fromarray(np.asarray(frames[idx[j]])).resize((tw, th), Image.LANCZOS)
            im.paste(fr, (x, y))
            d.text((x + 2, y + th + 1), labels[j], fill=(255, 220, 110), font=font(11))
        p = out_base + (".png" if pi == 1 else "_p%d.png" % pi)
        im.save(p)
        paths.append(p)
    return paths


def judder(diffs, a, b):
    """Frame-repeat pattern inside frames a..b-1. Returns (period, ratio) or None.

    diffs[i] = change from frame i-1 to i. A repeated frame makes diffs that
    alternate (period 2: 1.4, 0.1, 1.5, 0.1 ...). For each period 2-4 the mean
    difference of every phase is compared: min/max far below 1 = repeats.
    """
    seg = diffs[a + 1:b]
    if len(seg) < 8:
        return None
    best = None
    for p in (2, 3, 4):
        if len(seg) < 3 * p:
            continue
        m = np.array([seg[ph::p].mean() for ph in range(p)])
        if m.max() < 0.35:            # nothing moves: a held frame is not judder
            continue
        ratio = m.min() / m.max()
        if ratio < 0.4:
            return (p, float(ratio))   # the shortest period that fits is the repeat pattern
    return best


def sharp_norm(gray):
    lap = (-4 * gray[1:-1, 1:-1] + gray[:-2, 1:-1] + gray[2:, 1:-1] + gray[1:-1, :-2] + gray[1:-1, 2:])
    p2, p98 = np.percentile(gray, [2, 98])
    H, W = lap.shape
    vals = [lap[r * H // 4:(r + 1) * H // 4, c * W // 4:(c + 1) * W // 4].var() for r in range(4) for c in range(4)]
    return float(np.percentile(vals, 90)) * (100.0 / max(p98 - p2, 20.0)) ** 2


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("film")
    ap.add_argument("--out", default="qc")
    ap.add_argument("--plan")
    ap.add_argument("--every", type=int, default=4, help="contact sheet: one frame every N frames (default 4)")
    ap.add_argument("--lufs", type=float, default=-14.0)
    a = ap.parse_args()
    if not os.path.isfile(a.film):
        sys.exit("film not found: %s" % a.film)
    os.makedirs(a.out, exist_ok=True)
    info = ffprobe_json(a.film)
    vs = video_stream(info)
    if vs is None:
        sys.exit("no video stream in %s" % a.film)
    fps = rational(vs.get("avg_frame_rate")) or rational(vs.get("r_frame_rate")) or 25.0
    dur = float(info["format"].get("duration", 0))
    hard, soft, notes = [], [], []
    tags = {k: vs.get(k) for k in ("color_primaries", "color_transfer", "color_space", "color_range")}
    notes.append("%sx%s, %.3f fps, %.3fs, %s %s, tags %s" % (vs["width"], vs["height"], fps, dur, vs.get("codec_name"),
                                                           vs.get("pix_fmt"), "/".join(str(v) for v in tags.values())))
    for k in ("color_primaries", "color_transfer", "color_space"):
        if vs.get(k) != "bt709":
            soft.append("%s is '%s' (expected bt709): phones may shift colours" % (k, vs.get(k)))

    frames, raw = decode_all(a.film, vs)
    try:
        n = len(frames)
        small = frames[:, ::2, ::2, :].astype(np.float32)
        diffs = np.zeros(n)
        for i in range(1, n):
            diffs[i] = float(np.abs(small[i] - small[i - 1]).mean())
        luma = small.mean(axis=(1, 2, 3))

        # --- length: video vs plan vs audio
        plan, lay = None, None
        if a.plan:
            with open(a.plan, encoding="utf-8") as fh:
                plan = json.load(fh)
            lay = layout(plan["shots"], parse_fps(plan.get("fps", 25)))
            if abs(n - lay["total"]) > 1:
                hard.append("video has %d frames, the plan needs %d (%+d): shots were cut short or padded"
                            % (n, lay["total"], n - lay["total"]))
            else:
                notes.append("frame count %d matches the plan" % n)
        aud = [s for s in info["streams"] if s.get("codec_type") == "audio"]
        if aud:
            ad = float(aud[0].get("duration") or dur)
            vd = n / fps
            if abs(ad - vd) > max(1.0 / fps, 0.05):
                hard.append("audio lasts %.3fs, video %.3fs: they differ by %.0f ms" % (ad, vd, 1000 * (ad - vd)))

        # --- cuts (dissolve-aware with a plan)
        regions = []   # (first frame of change, last frame of change) per transition
        if lay:
            for i in range(1, len(lay["starts"])):
                s0, d = lay["starts"][i], lay["dissolves"][i]
                regions.append((s0, s0 + max(d, 1) - 1))
            shot_spans = [(lay["starts"][i] + (lay["dissolves"][i] if i else 0),
                           (lay["starts"][i + 1] if i + 1 < len(lay["starts"]) else lay["total"]))
                          for i in range(len(lay["starts"]))]
        else:
            cuts = detect_cuts(cut_scores(small), fps, 0.32)
            regions = [(c, c) for c in cuts]
            b = [0] + sorted(cuts) + [n]
            shot_spans = [(b[i], b[i + 1]) for i in range(len(b) - 1)]
        near = set()
        for r0, r1 in regions:
            near.update(range(r0 - 2, r1 + 3))

        # --- black / frozen / judder / spikes
        black = np.where(luma < 6)[0]
        if len(black):
            hard.append("%d near-black frames (first at %s)" % (len(black), fmt_tc(black[0] / fps)))
        still_frames = set()
        if plan:
            for k, sh in enumerate(plan["shots"]):
                if is_still(sh):
                    still_frames.update(range(*shot_spans[k]))
        frozen_runs, r = [], 0
        for i in range(1, n):
            if diffs[i] < 0.15 and i not in still_frames:
                r += 1
            else:
                if r >= int(fps * 0.4):
                    frozen_runs.append((i - r) / fps)
                r = 0
        if frozen_runs:
            soft.append("frozen picture for >0.4s at: " + ", ".join(fmt_tc(x) for x in frozen_runs[:5]) +
                        " (fine for a held still, wrong for video)")
        jud = []
        for k, (s0, s1) in enumerate(shot_spans, 1):
            if plan and is_still(plan["shots"][k - 1]):
                continue
            j = judder(diffs, s0, s1)
            if j:
                jud.append({"shot": k, "period": j[0], "ratio": round(j[1], 2), "at": round(s0 / fps, 2)})
                soft.append("shot %d (%s): every %s frame repeats (phase ratio %.2f) = judder from slowing without "
                            "enough real frames; conform a higher-fps clip, interpolate, or play faster"
                            % (k, fmt_tc(s0 / fps), {2: "2nd", 3: "3rd", 4: "4th"}[j[0]], j[1]))
        mov = np.convolve(diffs, np.ones(5) / 5, mode="same")
        spikes = [i for i in range(2, n - 2) if i not in near and diffs[i] > 4 * (mov[i] + 1) and diffs[i] > 12]
        if spikes:
            soft.append("%d sudden picture jumps inside shots (flash frame / warp / interpolation tear), e.g. %s"
                        % (len(spikes), ", ".join(fmt_tc(i / fps) for i in spikes[:5])))
        for k, (s0, s1) in enumerate(shot_spans, 1):
            if 0 < s1 - s0 < int(0.25 * fps):
                hard.append("shot %d lasts only %d frames (flash frame?)" % (k, s1 - s0))

        # --- per shot numbers and colour jumps at cuts
        shots_info = []
        for k, (s0, s1) in enumerate(shot_spans, 1):
            mid = min(n - 1, (s0 + s1) // 2)
            fr = np.asarray(frames[mid]).astype(np.float32)
            g = 0.2126 * fr[..., 0] + 0.7152 * fr[..., 1] + 0.0722 * fr[..., 2]
            shots_info.append({"shot": k, "start_s": round(s0 / fps, 3), "frames": int(s1 - s0),
                               "sharpness": round(sharp_norm(g), 1),
                               "luma_p2_p50_p98": [round(float(v), 1) for v in np.percentile(g, [2, 50, 98])],
                               "chroma": round(float((fr.max(axis=2) - fr.min(axis=2)).mean()), 1),
                               "mean_rgb": [round(float(v), 1) for v in fr.reshape(-1, 3).mean(axis=0)]})
        if shots_info:
            # reference = MEDIAN of the real footage shots: stills, end cards / titles, shots under a
            # PNG overlay and (without a plan) the last shot are left out, because a crisp logo or card
            # would make every real shot look soft
            ov = [(float(o.get("start", 0)), float(o.get("end", 1e9))) for o in (plan or {}).get("overlays", []) or []
                  if isinstance(o, dict)]
            card_roles = ("end-card", "endcard", "end card", "card", "title", "logo", "outro", "super")
            elig = []
            for k, si in enumerate(shots_info):
                s0, s1 = shot_spans[k]
                t_mid = (s0 + s1) / 2.0 / fps
                if plan:
                    sh = plan["shots"][k]
                    if is_still(sh) or str(sh.get("role", "")).lower() in card_roles:
                        continue
                elif k == len(shots_info) - 1 and len(shots_info) > 1:
                    continue
                if any(o0 <= t_mid <= o1 for o0, o1 in ov):
                    continue
                elig.append(si)
            if len(elig) >= 3:
                ref = float(np.median([si["sharpness"] for si in elig]))
                for si in elig:
                    si["sharpness_vs_median"] = round(si["sharpness"] / (ref + 1e-6), 2)
                    if si["sharpness_vs_median"] < 0.3:
                        soft.append("shot %d is much softer than the film's typical shot (%.0f%% of the median): "
                                    "if it is the hero or last shot, check focus at full size (shallow focus, "
                                    "smoke and fire can be intended)" % (si["shot"], 100 * si["sharpness_vs_median"]))
        for k in range(1, len(shots_info)):
            a_, b_ = np.array(shots_info[k - 1]["mean_rgb"]), np.array(shots_info[k]["mean_rgb"])
            shots_info[k]["colour_jump_from_prev"] = round(float(np.abs((a_ - a_.mean()) - (b_ - b_.mean())).max()), 1)

        # --- still log-flat?
        samp = [np.asarray(frames[i]).astype(np.float32) for i in np.linspace(0, n - 1, min(8, n)).astype(int)]
        p2s = np.median([np.percentile(0.2126 * f[..., 0] + 0.7152 * f[..., 1] + 0.0722 * f[..., 2], 2) for f in samp])
        p98s = np.median([np.percentile(0.2126 * f[..., 0] + 0.7152 * f[..., 1] + 0.0722 * f[..., 2], 98) for f in samp])
        chs = np.median([(f.max(axis=2) - f.min(axis=2)).mean() for f in samp])
        # log keeps its blacks lifted (p2 well above display black) and its range compressed in every shot;
        # a converted film has deep blacks somewhere (calibrated on F-Log2 with and without the official LUT)
        if p2s > 25 and (p98s - p2s) < 140:
            soft.append("the picture still measures like LOG (blacks %.0f, range %.0f, colour %.0f): was the official "
                        "transform applied? check with lutcheck.py" % (p2s, p98s - p2s, chs))

        # --- loudness
        p = subprocess.run([find_tool("ffmpeg"), "-hide_banner", "-nostats", "-i", a.film, "-af", "ebur128=peak=true",
                            "-f", "null", "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        txt = p.stderr.decode("utf-8", "replace")
        mI = re.findall(r"I:\s+(-?[\d.]+) LUFS", txt)
        mP = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", txt)
        if aud and mI:
            li = float(mI[-1])
            notes.append("loudness %.1f LUFS integrated, true peak %s dBTP" % (li, mP[-1] if mP else "?"))
            if abs(li - a.lufs) > 1.0:
                soft.append("loudness %.1f LUFS is off the %.1f target by more than 1 LU" % (li, a.lufs))
            if mP and float(mP[-1]) > -1.0:
                hard.append("true peak %s dBTP above -1 dBTP: clipping on phones" % mP[-1])
        else:
            notes.append("no audio stream")

        # --- sheets
        every = max(1, a.every)
        cidx = list(range(0, n, every))
        H, W = frames.shape[1:3]
        vertical = H > W
        sheet_pages(frames, cidx, ["%s f%d" % (fmt_tc(i / fps), i) for i in cidx], os.path.join(a.out, "contact"),
                    "%s  every %d frames (%d frames in the film)" % (os.path.basename(a.film), every, n),
                    10 if vertical else 8, 170 if vertical else 220)
        pidx, plab = [], []
        for k, (r0, r1) in enumerate(regions, 2):
            i0, i1 = max(0, r0 - 1), min(n - 1, r1 + 1 if r1 > r0 else r0)
            pidx += [i0, i1]
            kind = "dissolve" if r1 > r0 else "cut"
            plab += ["%d before %s %s" % (k, kind, fmt_tc(i0 / fps)), "%d after %s" % (k, fmt_tc(i1 / fps))]
        sheet_pages(frames, pidx, plab, os.path.join(a.out, "cuts"),
                    "cut pairs: left = last frame before, right = first frame after (dissolves: before it starts / "
                    "after it ends). Check eye-trace and colour jumps", 6, 220 if vertical else 300)
        if plan:
            for k, s in enumerate(plan["shots"], 1):
                slow = (s.get("ramp") or float(s.get("speed", 1.0)) < 0.999) and not is_still(s)
                if not slow:
                    continue
                s0, s1 = shot_spans[k - 1]
                idx = list(range(s0, min(s1, n)))
                sheet_pages(frames, idx, ["f%d %s" % (i, fmt_tc(i / fps)) for i in idx],
                            os.path.join(a.out, "slow_shot%02d" % k),
                            "shot %d, every frame (%s): look for repeats, warps, tears" %
                            (k, "ramp" if s.get("ramp") else "speed %.2f" % float(s.get("speed", 1))),
                            8 if vertical else 6, 200 if vertical else 280)
            # full-resolution stills for the critic
            hero = [k for k, s in enumerate(plan["shots"]) if s.get("role") == "hero"]
            picks = {"still_end.png": shot_spans[-1]}
            if hero:
                picks["still_hero.png"] = shot_spans[hero[0]]
            for name, (s0, s1) in picks.items():
                t = ((s0 + s1) / 2.0) / fps
                subprocess.run([find_tool("ffmpeg"), "-v", "error", "-y", "-ss", "%.3f" % t, "-i", a.film,
                                "-frames:v", "1", os.path.join(a.out, name)])
    finally:
        try:
            del frames
        except Exception:
            pass
        os.unlink(raw)

    rep = {"film": a.film, "frames": n, "fps": fps, "colour_tags": tags, "notes": notes, "hard": hard, "soft": soft,
           "cut_regions_frames": regions, "judder": jud, "shots": shots_info}
    write_json(os.path.join(a.out, "qc.json"), rep)
    for x in notes:
        print("  - " + x)
    for x in hard:
        print("  FAIL  " + x)
    for x in soft:
        print("  WARN  " + x)
    print("written: %s/contact*.png, cuts*.png%s, qc.json. Now WATCH the sheets frame by frame."
          % (a.out, ", slow_shot*.png, still_*.png" if plan else ""))
    sys.exit(1 if hard else 0)


if __name__ == "__main__":
    main()
