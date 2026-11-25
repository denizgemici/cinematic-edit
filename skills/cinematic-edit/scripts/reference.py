#!/usr/bin/env python3
"""reference.py: deconstruct a reference film into a measured style card.

It finds the cuts, measures every shot, and writes:
  style_card.json   shot list + rhythm numbers (ASL, median, spread, curve),
                    per-shot light/colour/motion, and a short "read" of the style
  shots.png         one frame per shot, in order, with timing (the film at a glance)
  rhythm.png        the shot-length curve over the film

Use it to learn a reference's technique (rhythm, scale, light, palette),
never to copy its shots.

Usage:
  python3 reference.py REFERENCE.mp4 --out ref_card/ [--threshold 0.32]

Notes: hard cuts are found reliably; slow dissolves and very fast flash cuts
can be missed or merged, so always look at shots.png and correct by eye.
Read-only; no network.
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (luma, ffprobe_json, video_stream, rational, run, find_tool,  # noqa: E402
                     read_rgb_frame, write_json, fmt_tc, font)


def decode_small_rgb(path, w=96, h=54):
    """Every frame at native rate, tiny RGB, for cut detection."""
    import subprocess
    cmd = [find_tool("ffmpeg"), "-v", "error", "-i", path, "-vf",
           "scale=%d:%d:flags=area,format=rgb24" % (w, h), "-f", "rawvideo", "-"]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.decode("utf-8", "replace")[-800:])
    buf = np.frombuffer(p.stdout, np.uint8)
    n = buf.size // (w * h * 3)
    return buf[: n * w * h * 3].reshape(n, h, w, 3).astype(np.float32)


def cut_scores(fr):
    """Per-frame change score combining pixel difference and colour-histogram distance."""
    n = len(fr)
    d = np.zeros(n)
    hist = []
    for f in fr:
        q = (f // 32).astype(int)
        idx = q[..., 0] * 64 + q[..., 1] * 8 + q[..., 2]
        h = np.bincount(idx.ravel(), minlength=512).astype(np.float32)
        hist.append(h / h.sum())
    for i in range(1, n):
        pix = np.abs(fr[i] - fr[i - 1]).mean() / 255.0
        hd = 0.5 * np.abs(hist[i] - hist[i - 1]).sum()
        d[i] = 0.5 * pix * 3 + 0.5 * hd
    return d


def detect_cuts(score, fps, thr, min_gap=0.25):
    """Adaptive threshold: a cut is a spike well above the local median."""
    n = len(score)
    win = max(5, int(fps))
    cuts = []
    last = -1e9
    for i in range(1, n):
        a, b = max(1, i - win), min(n, i + win + 1)
        local = np.median(score[a:b])
        if score[i] > thr and score[i] > local * 3.0 + 0.02:
            if (i - last) / fps >= min_gap:
                cuts.append(i)
                last = i
            elif score[i] > score[last]:
                cuts[-1] = i
                last = i
    return cuts


def shot_stats(fr_small, a, b):
    seg = fr_small[a:b]
    rgb = seg.reshape(-1, 3)
    y = luma(rgb)
    mx, mn = rgb.max(1), rgb.min(1)
    chroma = float((mx - mn).mean())
    warm = float((rgb[:, 0] - rgb[:, 2]).mean())
    motion = float(np.abs(np.diff(seg, axis=0)).mean()) if len(seg) > 1 else 0.0
    return {
        "luma_p5": round(float(np.percentile(y, 5)), 1),
        "luma_p50": round(float(np.percentile(y, 50)), 1),
        "luma_p95": round(float(np.percentile(y, 95)), 1),
        "chroma": round(chroma, 1),
        "warmth_r_minus_b": round(warm, 1),
        "motion": round(motion, 2),
    }


def describe(card):
    s = card["rhythm"]
    lines = []
    asl = s["asl"]
    if asl >= 3.5:
        lines.append("slow, contemplative rhythm (premium/luxury register)")
    elif asl >= 2:
        lines.append("measured brand-film rhythm")
    elif asl >= 1.0:
        lines.append("lively social rhythm")
    else:
        lines.append("very fast, montage/hype rhythm")
    lines.append("shot lengths %s (CV %.2f)" % ("varied" if s["cv"] >= 0.45 else "fairly even", s["cv"]))
    if s["longest_over_asl"] >= 2.5:
        lines.append("has a clearly held moment (longest = %.1fx average)" % s["longest_over_asl"])
    curve = s["curve_thirds"]
    if curve[1] < curve[0] * 0.8 and curve[2] > curve[1]:
        lines.append("accelerates in the middle and releases at the end")
    elif curve[2] < curve[0] * 0.8:
        lines.append("gets faster toward the end")
    elif curve[2] > curve[0] * 1.25:
        lines.append("slows down toward the end")
    L = card["light"]
    lines.append("tonality: blacks %.0f, mids %.0f, highlights %.0f (0-255); %s"
                 % (L["p5"], L["p50"], L["p95"], "low-key" if L["p50"] < 85 else ("high-key" if L["p50"] > 150 else "mid-key")))
    lines.append("palette: %s, saturation %s" % ("warm" if L["warmth"] > 8 else ("cool" if L["warmth"] < -8 else "neutral"),
                                                 "restrained" if L["chroma"] < 35 else ("rich" if L["chroma"] > 60 else "moderate")))
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--out", default="ref_card")
    ap.add_argument("--threshold", type=float, default=0.32, help="cut sensitivity (lower = more cuts)")
    a = ap.parse_args()
    info = ffprobe_json(a.video)
    vs = video_stream(info)
    fps = rational(vs.get("avg_frame_rate")) or rational(vs.get("r_frame_rate")) or 25.0
    fr = decode_small_rgb(a.video)
    n = len(fr)
    dur = n / fps
    sc = cut_scores(fr)
    cuts = detect_cuts(sc, fps, a.threshold)
    bounds = [0] + cuts + [n]
    shots = []
    for i in range(len(bounds) - 1):
        s0, s1 = bounds[i], bounds[i + 1]
        if s1 - s0 < 1:
            continue
        st = shot_stats(fr, s0, s1)
        st.update({"n": len(shots) + 1, "in": round(s0 / fps, 3), "out": round(s1 / fps, 3),
                   "frames": s1 - s0, "seconds": round((s1 - s0) / fps, 3)})
        shots.append(st)
    L = np.array([s["seconds"] for s in shots])
    thirds = [float(np.mean([s["seconds"] for s in shots if k * dur / 3 <= s["in"] < (k + 1) * dur / 3] or [0]))
              for k in range(3)]
    allrgb = fr[:: max(1, n // 300)].reshape(-1, 3)
    y = luma(allrgb)
    card = {
        "file": a.video, "fps": round(fps, 3), "duration": round(dur, 2), "shots": len(shots),
        "rhythm": {
            "asl": round(float(L.mean()), 3), "median": round(float(np.median(L)), 3),
            "min": round(float(L.min()), 3), "max": round(float(L.max()), 3),
            "cv": round(float(L.std() / L.mean()), 3) if L.mean() else 0,
            "longest_over_asl": round(float(L.max() / L.mean()), 2) if L.mean() else 0,
            "median_over_asl": round(float(np.median(L) / L.mean()), 2) if L.mean() else 0,
            "cuts_per_10s": round(10 * (len(shots) - 1) / dur, 2) if dur else 0,
            "curve_thirds": [round(x, 2) for x in thirds],
        },
        "light": {
            "p5": round(float(np.percentile(y, 5)), 1), "p50": round(float(np.percentile(y, 50)), 1),
            "p95": round(float(np.percentile(y, 95)), 1),
            "chroma": round(float((allrgb.max(1) - allrgb.min(1)).mean()), 1),
            "warmth": round(float((allrgb[:, 0] - allrgb[:, 2]).mean()), 1),
        },
        "shot_list": shots,
        "caveat": "Automatic cut detection; dissolves and flash frames may be missed. Verify against shots.png.",
    }
    card["read"] = describe(card)
    os.makedirs(a.out, exist_ok=True)
    write_json(os.path.join(a.out, "style_card.json"), card)

    # shots.png: one frame per shot (middle), 6 per row
    from PIL import Image, ImageDraw
    tw, cols = 300, 6
    thumbs = []
    for s in shots:
        img = read_rgb_frame(a.video, (s["in"] + s["out"]) / 2, width=tw)
        thumbs.append(img)
    th = max((t.shape[0] for t in thumbs if t is not None), default=170)
    rows = (len(shots) + cols - 1) // cols
    pad, lab = 6, 18
    im = Image.new("RGB", (cols * (tw + pad) + pad, rows * (th + lab + pad) + pad + 26), (16, 16, 16))
    d = ImageDraw.Draw(im)
    f = font(12)
    d.text((pad, 6), "%s | %d shots | ASL %.2fs | median %.2fs | CV %.2f"
           % (os.path.basename(a.video), len(shots), card["rhythm"]["asl"], card["rhythm"]["median"],
              card["rhythm"]["cv"]), fill=(235, 235, 235), font=font(14))
    for i, (s, t) in enumerate(zip(shots, thumbs)):
        x = pad + (i % cols) * (tw + pad)
        y0 = 26 + pad + (i // cols) * (th + lab + pad)
        if t is not None:
            im.paste(Image.fromarray(t), (x, y0))
        d.text((x, y0 + th + 2), "%02d  %s  %.2fs" % (s["n"], fmt_tc(s["in"]), s["seconds"]),
               fill=(255, 225, 120), font=f)
    im.save(os.path.join(a.out, "shots.png"))

    # rhythm.png: bar per shot, height = length
    W, H = 1200, 260
    im = Image.new("RGB", (W, H), (16, 16, 16))
    d = ImageDraw.Draw(im)
    mx = max(L.max(), 0.1)
    for s in shots:
        x0 = 10 + (W - 20) * s["in"] / dur
        x1 = 10 + (W - 20) * s["out"] / dur
        h = (H - 50) * s["seconds"] / mx
        d.rectangle([x0, H - 30 - h, max(x0 + 1, x1 - 1), H - 30], fill=(110, 170, 230))
    d.text((10, 6), "shot length over time (bar height = seconds, max %.2fs)" % mx, fill=(220, 220, 220), font=font(13))
    d.text((10, H - 22), "0:00", fill=(180, 180, 180), font=f)
    d.text((W - 60, H - 22), fmt_tc(dur), fill=(180, 180, 180), font=f)
    im.save(os.path.join(a.out, "rhythm.png"))

    print("%d shots in %.1fs | ASL %.2fs median %.2fs CV %.2f | cuts/10s %.1f"
          % (len(shots), dur, card["rhythm"]["asl"], card["rhythm"]["median"], card["rhythm"]["cv"],
             card["rhythm"]["cuts_per_10s"]))
    for line in card["read"]:
        print(" - " + line)
    print("written: %s/style_card.json, shots.png, rhythm.png" % a.out)


if __name__ == "__main__":
    main()
