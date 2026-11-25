#!/usr/bin/env python3
"""scan.py: watch every clip from first to last frame and find its candidate moments.

Each clip is decoded ONCE (fps -> downscale -> LUT, so a LUT scan is cheap) and
every sample is measured:

  sharpness   Laplacian variance of the sharpest tiles, both ABSOLUTE (a clip
              that is soft from start to end is reported as soft) and relative
              to the clip's own best moment
  camera      robust camera motion: median of 3x3 tile shifts, trusted only when
              most tiles agree (fire, smoke, steam and a tossed pan make tiles
              disagree: that is subject action, not camera shake)
  jitter      high-frequency camera shake, % of width
  action      subject motion after removing camera motion (fire, toss, pour,
              smoke, falling herbs): counted as VALUE, not as a defect
  exposure    p2 / p98 luma, clipped and crushed share
  tilt        roll of the scene's long straight lines (deg, 640 px frames,
              projection-profile search over near-horizontal and near-vertical
              edges; checked by selftest.py with synthetic rotations)

It proposes CANDIDATES (never decisions): "clean" windows (sharp, steady) and
"event" windows (the action peaks, always including the clip's strongest
action second unless the take is junk), each with a meaningful peak_t.

Written per clip (names are unique even when two cards both have C0001.MP4):
  NAME.json            numbers, candidates, flags, series
  NAME_strip.png ...   dense contact pages: one frame every 0.5 s (1 s for
                       clips over 30 s), several rows, candidate spans marked;
                       more pages NAME_strip_p2.png ... for long clips
  NAME_c1.png ...      per candidate: in / peak / out at 640 px
and for the folder:
  _index.png (_index_p2.png ...)  one frame per clip with name, fps class,
                       duration, tilt and flags: the whole shoot at a glance
  _summary.json        every clip, ranked by its best candidate

Usage:
  python3 scan.py CLIP_OR_FOLDER [...] --out analysis/ [--fps 8] [--min 1.0]
                  [--lut official_log_to_709.cube] [--windows 3] [--events 2]
                  [--timeline-fps 25] [--no-strip]

Pass the camera maker's official log-to-Rec.709 LUT with --lut for log
footage (check it first with lutcheck.py). A long folder takes minutes: run it
in the background. Read-only for media; no network.
"""
import argparse
import os
import sys
import tempfile
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (write_json, fmt_tc, font, lut_filter, ffprobe_json, video_stream,  # noqa: E402
                     rational, rotation_of, scale_in_opts, find_tool, parse_fps)
from probe import collect  # noqa: E402

JITTER_BAD = 0.35      # % of frame width of high-frequency shake = visibly shaky
JITTER_OK = 0.15       # below this a shot reads as stable
STATIC_SPEED = 0.6     # % of width per second: below = locked-off look
FAST_SPEED = 8.0       # % of width per second: above = fast move / whip
# sharpness and action are contrast-normalised (x (100 / luma range)^2 and x 100 / range), so a
# log clip with or without its LUT reads the same; calibrated on Fuji X-S20 and Sony FX3 footage
SHARP_GOOD = 300.0     # tile-Laplacian variance (320 px gray) of a crisp frame
SHARP_SOFT = 150.0     # below this (90th percentile over the take) nothing in the take is crisp
ACT_GOOD = 18.0        # mean abs residual after camera compensation (320 px, 8 samples/s) of clear action
TILT_EVIDENCE = 1.0    # frame widths of long straight lines needed to trust a tilt reading


# ------------------------------------------------------------------------------------------
# measures
def laplacian_var(img, grid=4):
    """Focus of the SHARPEST part of the frame (shallow focus is not blur): 90th pct of tiles."""
    lap = (-4 * img[1:-1, 1:-1] + img[:-2, 1:-1] + img[2:, 1:-1] + img[1:-1, :-2] + img[1:-1, 2:])
    H, W = lap.shape
    th, tw = H // grid, W // grid
    vals = [lap[r * th:(r + 1) * th, c * tw:(c + 1) * tw].var() for r in range(grid) for c in range(grid)]
    return float(np.percentile(vals, 90))


def phase_shift(a, b, win):
    """Translation (dx, dy) in pixels from frame a to frame b, and the correlation peak height."""
    if win is None or win.shape != a.shape:
        win = np.outer(np.hanning(a.shape[0]), np.hanning(a.shape[1])).astype(np.float32)
    fa = np.fft.fft2((a - a.mean()) * win)
    fb = np.fft.fft2((b - b.mean()) * win)
    r = fa * np.conj(fb)
    r /= np.abs(r) + 1e-9
    c = np.fft.ifft2(r).real
    iy, ix = np.unravel_index(np.argmax(c), c.shape)
    h, w = c.shape

    def refine(v, i, n):
        lft, m, rr = v[(i - 1) % n], v[i], v[(i + 1) % n]
        d = (lft - 2 * m + rr)
        return i + (0.5 * (lft - rr) / d if abs(d) > 1e-12 else 0.0)
    fy = refine(c[:, ix], iy, h)
    fx = refine(c[iy, :], ix, w)
    if fy > h / 2:
        fy -= h
    if fx > w / 2:
        fx -= w
    return -fx, -fy, float(c[iy, ix])


def robust_shift(a, b, win, grid=3):
    """Camera translation = median of per-tile shifts, plus the share of tiles that agree.

    Agreement < 0.5 means the tiles see different motions (flames, smoke, a big
    moving subject): the frame-to-frame change is subject action, not the camera.
    """
    H, W = a.shape
    th, tw = H // grid, W // grid
    sx, sy = [], []
    for r in range(grid):
        for c in range(grid):
            ta = a[r * th:(r + 1) * th, c * tw:(c + 1) * tw]
            tb = b[r * th:(r + 1) * th, c * tw:(c + 1) * tw]
            if ta.std() < 3 or tb.std() < 3:      # flat tile (sky, wall): no information
                continue
            x, y, _ = phase_shift(ta, tb, win)
            sx.append(x)
            sy.append(y)
    if len(sx) < 3:
        x, y, _ = phase_shift(a, b, None)
        return x, y, 0.5
    sx, sy = np.array(sx), np.array(sy)
    mx, my = float(np.median(sx)), float(np.median(sy))
    tol = 1.0 + 0.1 * np.hypot(mx, my)
    agree = float(np.mean(np.hypot(sx - mx, sy - my) <= tol)) if len(sx) >= 4 else 0.0
    return mx, my, agree


def _sobel(img):
    p = np.pad(img, 1, mode="edge")
    gx = (p[:-2, 2:] + 2 * p[1:-1, 2:] + p[2:, 2:]) - (p[:-2, :-2] + 2 * p[1:-1, :-2] + p[2:, :-2])
    gy = (p[2:, :-2] + 2 * p[2:, 1:-1] + p[2:, 2:]) - (p[:-2, :-2] + 2 * p[:-2, 1:-1] + p[:-2, 2:])
    return gx, gy


_K = np.exp(-0.5 * (np.arange(-12, 13) / 4.0) ** 2)


def _profile(xs, ys, w, vertical, grid, ret_h=False):
    """Projection-profile sharpness per candidate angle (a Hough-like accumulation).

    Edge points are projected across the line direction; at the true angle every
    long straight line collapses into one narrow peak. Quarter-pixel bins smoothed
    with a 1-px Gaussian keep the score shift-invariant (no bias towards 0 deg from
    the pixel grid)."""
    out = []
    for th in grid:
        t = np.radians(th)
        rho = xs * np.cos(t) + ys * np.sin(t) if vertical else -xs * np.sin(t) + ys * np.cos(t)
        i = np.round((rho - rho.min()) * 4).astype(np.int64)
        h = np.convolve(np.bincount(i, w), _K)
        out.append(h if ret_h else float((h * h).sum()))
    return out if ret_h else np.array(out)


def _tilt_family(xs, ys, w, vertical, span, dim):
    grid = np.arange(-span, span + 1e-9, 0.1)
    sc = _profile(xs, ys, w, vertical, grid)
    k = int(np.argmax(sc))
    fine = np.arange(grid[k] - 0.15, grid[k] + 0.1501, 0.01)
    fs = _profile(xs, ys, w, vertical, fine)
    best = float(fine[int(np.argmax(fs))])
    h = _profile(xs, ys, w, vertical, [best], ret_h=True)[0]
    L = h / (w.mean() * _K.max())                      # a straight edge of L px gives a peak of ~L
    pk = (L[1:-1] >= L[:-2]) & (L[1:-1] >= L[2:]) & (L[1:-1] >= 0.2 * dim)
    lines = np.sort(L[1:-1][pk])[::-1]
    return best, float(lines[:8].sum() / dim), int(len(lines))


def tilt_angle(img, span=10.0):
    """Roll of the scene's long straight lines in one gray frame (~640 px long side).

    Returns (angle_deg, confidence 0..1, detail). angle > 0 = the lines are turned
    clockwise (right side low); straighten with 'straighten': -angle.
    Near-horizontal and near-vertical edge families are measured separately; a
    family counts only with enough long straight line (TILT_EVIDENCE). When both
    count but disagree by > 1 deg (perspective), the stronger wins with low
    confidence. Organic frames (food from above, faces, foliage) return None.
    """
    img = np.asarray(img, np.float32)
    H, W = img.shape
    gx, gy = _sobel(img)
    mag = np.hypot(gx, gy)
    b = 6
    mag[:b] = 0
    mag[-b:] = 0
    mag[:, :b] = 0
    mag[:, -b:] = 0
    m = mag > max(np.percentile(mag, 90), 40.0)
    if m.sum() < 200:
        return None, 0.0, {}
    ys, xs = np.nonzero(m)
    xs, ys = xs.astype(np.float64), ys.astype(np.float64)
    gxs, gys, ws = gx[m], gy[m], np.sqrt(mag[m])
    tn = np.tan(np.radians(span + 5))
    res = {}
    for name, sel, vert, dim in (("h", np.abs(gxs) < np.abs(gys) * tn, False, W),
                                 ("v", np.abs(gys) < np.abs(gxs) * tn, True, H)):
        if sel.sum() >= 150:
            res[name] = _tilt_family(xs[sel], ys[sel], ws[sel], vert, span, dim)
    good = {k: v for k, v in res.items() if v[1] >= TILT_EVIDENCE}
    if not good:
        return None, 0.0, res
    k = max(good, key=lambda q: good[q][1])
    ang, ev = good[k][0], good[k][1]
    conf = min(1.0, ev / 4.0)
    if len(good) == 2 and abs(good["h"][0] - good["v"][0]) > 1.0:
        conf *= 0.4   # horizontals and verticals disagree: perspective, not roll
    return ang, conf, res


def moving_avg(x, n):
    if n <= 1 or len(x) < 3:
        return x.copy()
    n = min(n, len(x))
    k = np.ones(n) / n
    pad = n // 2
    xp = np.pad(x, (pad, n - 1 - pad), mode="edge")
    return np.convolve(xp, k, mode="valid")


def slowmo_advice(src_fps, timeline_fps=25.0):
    """How this clip can be slowed down, from the capture frame rate (checked FIRST)."""
    if src_fps > timeline_fps * 1.05:
        ratio = timeline_fps / src_fps
        return {"clean_speed": round(ratio, 4), "stretch": round(1 / ratio, 3),
                "how": "real slow motion: conform %.2f fps to %.3g fps = speed %.0f%% (every frame shown once, "
                       "nothing invented); a clean 1 s becomes %.2f s" % (src_fps, timeline_fps, ratio * 100, 1 / ratio)}
    return {"clean_speed": 1.0, "stretch": 1.0,
            "how": "%.2f fps capture on a %.3g fps timeline: no real slow-motion frames. A slow version needs frame "
                   "interpolation (references/slow-motion.md): ~60%% speed is usually safe on low-risk subjects, "
                   "check every frame for warping on hands, liquids, glass and flame" % (src_fps, timeline_fps)}


# ------------------------------------------------------------------------------------------
# decoding: one pass, small RGB frames kept on disk (memmap)
def decode_rgb(path, fps, lut=None, long_side=640):
    vs = video_stream(ffprobe_json(path))
    if vs is None:
        raise RuntimeError("no video stream")
    w, h = int(vs["width"]), int(vs["height"])
    if rotation_of(vs) in (90, -90, 270, -270):
        w, h = h, w
    if w >= h:
        W, H = long_side, max(2, int(round(h * long_side / float(w))) // 2 * 2)
    else:
        H, W = long_side, max(2, int(round(w * long_side / float(h))) // 2 * 2)
    chain = "fps=%s,scale=%d:%d:flags=area:%s,format=rgb24" % (fps, W, H, scale_in_opts(vs))
    lf = lut_filter(lut) if lut else None
    if lf:
        chain += "," + lf + ",format=rgb24"        # LUT after fps+scale: same look, a fraction of the work
    fd, raw = tempfile.mkstemp(prefix="ce_scan_", suffix=".rgb")
    os.close(fd)
    import subprocess
    p = subprocess.run([find_tool("ffmpeg"), "-v", "error", "-y", "-i", path, "-vf", chain,
                        "-f", "rawvideo", "-pix_fmt", "rgb24", raw], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        os.unlink(raw)
        raise RuntimeError(p.stderr.decode("utf-8", "replace")[-600:])
    n = os.path.getsize(raw) // (W * H * 3)
    mm = np.memmap(raw, dtype=np.uint8, mode="r", shape=(n, H, W, 3)) if n else np.zeros((0, H, W, 3), np.uint8)
    return mm, raw, vs


def gray_small(rgb):
    """Rec.709 luma, 2x2-averaged (640 -> 320 px)."""
    y = 0.2126 * rgb[..., 0].astype(np.float32) + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    H, W = y.shape
    y = y[:H // 2 * 2, :W // 2 * 2]
    return y.reshape(H // 2, 2, W // 2, 2).mean(axis=(1, 3))


def gray_full(rgb):
    return 0.2126 * rgb[..., 0].astype(np.float32) + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]


# ------------------------------------------------------------------------------------------
def _pick_windows(score, used, L, n, times, fps, q, label):
    out = []
    N = len(score)
    for _ in range(n):
        cand = score.copy()
        for j in range(N):
            a = max(0, min(j - L // 2, N - L))
            if used[a:a + L].any():
                cand[j] = -1
        c = int(np.argmax(cand))
        if cand[c] <= 0:
            break
        a = max(0, min(c - L // 2, N - L))
        b = a + L
        lvl = score[c] * 0.85
        while a > 0 and not used[a - 1] and q[a - 1] >= lvl:
            a -= 1
        while b < N and not used[b] and q[b] >= lvl:
            b += 1
        used[max(0, a - 1):min(N, b + 1)] = True
        out.append((a, b, float(score[c]), label))
    return out


def analyse(path, fps=8.0, min_len=1.0, lut=None, n_windows=3, n_events=2, timeline_fps=25.0):
    rgb, raw, vs = decode_rgb(path, fps, lut)
    try:
        src_fps = rational(vs.get("r_frame_rate")) or 25.0
        n = len(rgb)
        if n < 3:
            return {"file": path, "error": "too short to analyse"}, None, raw
        times = np.arange(n) / float(fps)
        g_prev = None
        sharp = np.zeros(n)
        p2 = np.zeros(n)
        p98 = np.zeros(n)
        clip_hi = np.zeros(n)
        clip_lo = np.zeros(n)
        dx, dy, agree, local = np.zeros(n), np.zeros(n), np.ones(n), np.zeros(n)
        win = None
        for i in range(n):
            g = gray_small(rgb[i])
            if win is None:
                H, W = g.shape
                win = np.outer(np.hanning(H // 3), np.hanning(W // 3)).astype(np.float32)
            p2[i], p98[i] = np.percentile(g, [2, 98])
            # contrast-normalised focus: the same lens sharpness reads the same with or without a LUT
            sharp[i] = laplacian_var(g) * (100.0 / max(p98[i] - p2[i], 20.0)) ** 2
            clip_hi[i] = float((g >= 250).mean())
            clip_lo[i] = float((g <= 4).mean())
            if g_prev is not None:
                sx, sy, ag = robust_shift(g_prev, g, win)
                agree[i] = ag
                dx[i], dy[i] = sx, sy
                if ag < 0.6:
                    sx = sy = 0.0           # tiles disagree: the change is subject action, camera unknown
                sh = np.roll(np.roll(g_prev, int(round(sy)), axis=0), int(round(sx)), axis=1)
                bd = 8
                local[i] = float(np.abs(g[bd:-bd, bd:-bd] - sh[bd:-bd, bd:-bd]).mean()) * 100.0 / max(p98[i] - p2[i], 20.0)
            g_prev = g
        local[0] = local[1]
        agree[0] = agree[1]
        H, W = g_prev.shape
        # camera path only from samples where the tiles agree
        known = agree >= 0.6
        known[0] = True
        dx[~known] = 0.0    # unknown camera motion is not integrated into the path (it is not "shake")
        dy[~known] = 0.0
        px, py = np.cumsum(dx), np.cumsum(dy)
        sm = max(3, int(round(fps * 0.75)))
        jx, jy = px - moving_avg(px, sm), py - moving_avg(py, sm)
        jitter = moving_avg(np.hypot(jx, jy), sm) / W * 100.0
        jitter_known = moving_avg(known.astype(float), sm)   # how much of the jitter estimate is measured
        speed = np.hypot(np.gradient(moving_avg(px, sm)), np.gradient(moving_avg(py, sm))) * fps / W * 100.0

        # tilt from up to 9 evenly spaced 640-px frames, median of confident readings
        readings = []
        for i in np.linspace(0, n - 1, min(9, n)).astype(int):
            a, c, _ = tilt_angle(gray_full(rgb[i]))
            if a is not None and c >= 0.25:
                readings.append(a)
        tilt, tilt_spread = None, None
        if len(readings) >= max(2, min(9, n) // 3):
            tilt = float(np.median(readings))
            tilt_spread = float(np.median(np.abs(np.array(readings) - tilt)))
            if tilt_spread > 0.6:            # lines do not agree over the take (camera moves)
                tilt = None

        # scores
        sharp_p90 = float(np.percentile(sharp, 90))
        s_rel = np.clip(sharp / (sharp_p90 + 1e-6), 0, 1)
        s_abs = np.clip(sharp / SHARP_GOOD, 0, 1)
        s_term = 0.5 * s_rel + 0.5 * s_abs
        stab = np.clip(1.0 - (jitter - JITTER_OK) / (JITTER_BAD - JITTER_OK), 0, 1)
        stab = jitter_known * stab + (1 - jitter_known) * 0.6   # unmeasurable camera = neutral, not "steady"
        expo = np.clip(1.0 - 4 * np.maximum(clip_hi - 0.02, 0) - 4 * np.maximum(clip_lo - 0.08, 0), 0, 1)
        edge = np.ones(n)
        k = max(1, int(round(n * 0.08)))
        edge[:k] = np.linspace(0.8, 1.0, k)
        edge[-k:] = np.linspace(1.0, 0.8, k)
        fastmove = np.clip((speed - FAST_SPEED) / FAST_SPEED, 0, 1)
        act = moving_avg(np.clip(local / ACT_GOOD, 0, 1.5), max(1, int(round(fps * 0.25)))) / 1.5
        # clean: sharp and steady; action adds a little (a gesture is why a shot exists)
        q_clean = s_term * (0.35 + 0.65 * stab) * expo * edge * (0.8 + 0.2 * act) * (1 - 0.6 * fastmove)
        # event: subject action near a sharp-enough frame; camera shake costs less here
        q_event = act * (0.25 + 0.75 * s_term) * expo * (0.6 + 0.4 * stab) * (1 - 0.8 * fastmove)

        L = max(2, int(round(min_len * fps)))
        used = np.zeros(n, bool)
        picks = []
        if n >= L:
            picks += _pick_windows(moving_avg(q_clean, L), used, L, n_windows, times, fps, q_clean, "clean")
            picks += _pick_windows(moving_avg(q_event, L), used, L, n_events, times, fps, q_event, "event")
        fast_share = float(np.mean(speed > FAST_SPEED))
        blank_share = float(np.mean(sharp < 30.0))   # featureless or smeared: floor, ceiling, whip, lens cap
        junk = fast_share > 0.6 or blank_share > 0.5 or float(np.percentile(sharp, 90)) < SHARP_SOFT * 0.4
        # never leave the strongest action second out (unless the take is junk)
        if n >= L and not junk and act.max() > 0.25:
            top = int(np.argmax(moving_avg(q_event, L)))
            if not any(a <= top < b for a, b, _, _ in picks):
                a = max(0, min(top - L // 2, n - L))
                picks.append((a, a + L, float(moving_avg(q_event, L)[top]), "event"))
        cands = []
        for a, b, sc, label in sorted(picks):
            seg = slice(a, b)
            qq = (q_event if label == "event" else q_clean)[seg]
            pk = a + int(np.argmax(moving_avg(qq, max(1, int(fps * 0.25)))))
            cam = float(np.median(speed[seg]))
            cands.append({
                "in": round(float(times[a]), 2), "out": round(float(times[b - 1] + 1.0 / fps), 2),
                "type": label,
                "peak_t": round(float(times[pk]), 2),
                "score": round(sc, 3),
                "confidence": "low - look at the strip before using" if sc < 0.3 else "ok",
                "jitter_pct": round(float(np.median(jitter[seg])), 3),
                "camera": "static" if cam < STATIC_SPEED else ("fast move" if cam > FAST_SPEED else "slow move"),
                "subject_action": round(float(np.max(act[seg])), 2),
                "sharp_abs": round(float(np.max(sharp[seg])), 1),
            })
        dur = float(times[-1] + 1.0 / fps)
        sm_adv = slowmo_advice(src_fps, timeline_fps)
        flags = []
        if np.median(jitter[jitter_known > 0.5]) > JITTER_BAD if (jitter_known > 0.5).any() else False:
            flags.append("shaky for most of the take: stabilise (gyro data if the camera recorded it) or another take")
        if tilt is not None and 0.2 <= abs(tilt) <= 15.0:
            flags.append("lines tilted %.2f deg: straighten to exactly level ('straighten': %.2f)" % (tilt, -tilt))
        if np.median(clip_hi) > 0.03:
            flags.append("highlights clipped in %.0f%% of the frame (check windows/sky)" % (100 * np.median(clip_hi)))
        if sharp_p90 < SHARP_SOFT:
            flags.append("SOFT: nothing in this take is crisply in focus (absolute sharpness %.0f < %.0f)"
                         % (sharp_p90, SHARP_SOFT))
        if junk:
            flags.append("possible junk take (accidental recording?): %s" % (
                "camera moving fast for %.0f%% of it" % (100 * fast_share) if fast_share > 0.6 else
                ("%.0f%% of it featureless or smeared" % (100 * blank_share) if blank_share > 0.5 else "nothing sharp")))
        elif blank_share > 0.2:
            flags.append("%.0f%% of the take is featureless or smeared (camera carried, pointed away or whipping): "
                         "use only the candidates" % (100 * blank_share))
        if not cands or max(c["score"] for c in cands) < 0.3:
            flags.append("no clearly clean candidate >= %.1fs by the numbers: LOOK at the strip; a shallow-focus "
                         "or moving-subject shot can still be beautiful" % min_len)
        if src_fps > timeline_fps * 1.05:
            flags.insert(0, "HIGH FRAME RATE %.2f fps: %s" % (src_fps, sm_adv["how"]))
        res = {
            "file": path, "source_fps": round(src_fps, 3), "duration": round(dur, 2), "sample_fps": fps,
            "tilt_deg": None if tilt is None else round(tilt, 2),
            "tilt_spread_deg": None if tilt_spread is None else round(tilt_spread, 2),
            "median_jitter_pct": round(float(np.median(jitter)), 3),
            "median_camera_speed_pct_s": round(float(np.median(speed)), 2),
            "sharpness_abs_p90": round(sharp_p90, 1),
            "soft_clip": bool(sharp_p90 < SHARP_SOFT), "junk": bool(junk),
            "luma_p2_p98": [round(float(np.median(p2)), 1), round(float(np.median(p98)), 1)],
            "slow_motion": sm_adv,
            "candidates": cands, "windows": cands, "flags": flags,
            "series": {"t": [round(float(x), 2) for x in times], "q_clean": [round(float(x), 3) for x in q_clean],
                       "q_event": [round(float(x), 3) for x in q_event], "action": [round(float(x), 3) for x in act],
                       "jitter": [round(float(x), 3) for x in jitter], "sharp": [round(float(x), 1) for x in sharp],
                       "tile_agreement": [round(float(x), 2) for x in agree],
                       "motion": [round(float(x), 2) for x in local]},
        }
        return res, rgb, raw
    except Exception:
        _cleanup(rgb, raw)
        raise


def _cleanup(rgb, raw):
    try:
        del rgb
    except Exception:
        pass
    try:
        os.unlink(raw)
    except OSError:
        pass


# ------------------------------------------------------------------------------------------
# pictures
def _thumb(rgb_frame, tw):
    from PIL import Image
    im = Image.fromarray(np.asarray(rgb_frame))
    return im.resize((tw, max(2, int(round(im.height * tw / float(im.width))))), Image.LANCZOS)


def strip_pages(res, rgb, out_base, rows=5):
    """Dense pages: one frame every 0.5 s (1 s over 30 s), several rows, candidates marked."""
    from PIL import Image, ImageDraw
    fps, dur = res["sample_fps"], res["duration"]
    step = 0.5 if dur <= 30 else 1.0
    ts = list(np.arange(step / 2, dur, step))
    H, W = rgb.shape[1:3]
    vertical = H > W
    cols = 10 if vertical else 8
    tw = 150 if vertical else 210
    per = cols * rows
    pages = [ts[i:i + per] for i in range(0, len(ts), per)] or [[0.0]]
    f, fs = font(14), font(12)
    paths = []
    th = int(round(H * tw / float(W)))
    for pi, page in enumerate(pages, 1):
        nrows = (len(page) + cols - 1) // cols
        pad, lab = 6, 16
        graph_h = 60 if pi == 1 else 0
        im = Image.new("RGB", (cols * (tw + pad) + pad, 30 + graph_h + nrows * (th + lab + pad) + pad), (16, 16, 16))
        d = ImageDraw.Draw(im)
        d.text((pad, 6), "%s  |  %.1fs  |  page %d/%d, a frame every %.1fs  |  tilt %s  |  shake %.2f%%  |  sharp %.0f%s"
               % (os.path.basename(res["file"]), dur, pi, len(pages), step, res.get("tilt_deg"),
                  res.get("median_jitter_pct", 0), res.get("sharpness_abs_p90", 0),
                  "  SOFT" if res.get("soft_clip") else ""), fill=(235, 235, 235), font=f)
        if graph_h:
            gx0, gx1, gy0 = pad, im.width - pad, 28
            for c in res["candidates"]:
                col = (40, 85, 55) if c["type"] == "clean" else (95, 60, 30)
                d.rectangle([gx0 + (gx1 - gx0) * c["in"] / dur, gy0, gx0 + (gx1 - gx0) * c["out"] / dur, gy0 + graph_h - 8],
                            fill=col)
            s = res["series"]
            for key, col in (("q_clean", (120, 220, 140)), ("q_event", (250, 170, 80)), ("jitter", (230, 90, 80))):
                vals = np.array(s[key])
                if key == "jitter":
                    vals = np.clip(vals / (JITTER_BAD * 2), 0, 1)
                pts = [(gx0 + (gx1 - gx0) * t / dur, gy0 + (graph_h - 8) * (1 - v)) for t, v in zip(s["t"], vals)]
                if len(pts) > 1:
                    d.line(pts, fill=col, width=1)
        y0 = 30 + graph_h
        for k, t in enumerate(page):
            x = pad + (k % cols) * (tw + pad)
            y = y0 + (k // cols) * (th + lab + pad)
            i = min(len(rgb) - 1, int(round(t * fps)))
            im.paste(_thumb(rgb[i], tw), (x, y))
            inc = [c for c in res["candidates"] if c["in"] <= t < c["out"]]
            if inc:
                col = (90, 200, 120) if inc[0]["type"] == "clean" else (250, 160, 60)
                d.rectangle([x, y + th, x + tw - 1, y + th + 3], fill=col)
            d.text((x + 2, y + th + 3), fmt_tc(t), fill=(255, 225, 120), font=fs)
        p = out_base + ("_strip.png" if pi == 1 else "_strip_p%d.png" % pi)
        im.save(p)
        paths.append(p)
    return paths


def candidate_sheets(res, rgb, out_base):
    """For each candidate: in / peak / out frames at 640 px, side by side."""
    from PIL import Image, ImageDraw
    fps = res["sample_fps"]
    paths = []
    for ci, c in enumerate(res["candidates"], 1):
        ts = [c["in"], c["peak_t"], max(c["in"], c["out"] - 1.0 / fps)]
        frames = [Image.fromarray(np.asarray(rgb[min(len(rgb) - 1, int(round(t * fps)))])) for t in ts]
        w, h = frames[0].size
        im = Image.new("RGB", (3 * w + 4 * 6, h + 40), (16, 16, 16))
        d = ImageDraw.Draw(im)
        d.text((6, 6), "%s  candidate %d (%s)  %s - %s  score %.2f  action %.2f  %s" % (
            os.path.basename(res["file"]), ci, c["type"], fmt_tc(c["in"]), fmt_tc(c["out"]), c["score"],
            c["subject_action"], c["camera"]), fill=(235, 235, 235), font=font(15))
        for k, (fr, t, lbl) in enumerate(zip(frames, ts, ("IN", "PEAK", "OUT"))):
            x = 6 + k * (w + 6)
            im.paste(fr, (x, 34))
            d.text((x + 6, 40), "%s %s" % (lbl, fmt_tc(t)), fill=(255, 225, 120), font=font(16))
        p = "%s_c%d.png" % (out_base, ci)
        im.save(p)
        paths.append(p)
    return paths


def index_pages(entries, out_dir, cols=6, rows=5):
    """One frame per clip: the whole shoot at a glance."""
    from PIL import Image, ImageDraw
    if not entries:
        return []
    tw, th = 260, 260
    per = cols * rows
    paths = []
    for pi in range(0, len(entries), per):
        page = entries[pi:pi + per]
        nrows = (len(page) + cols - 1) // cols
        im = Image.new("RGB", (cols * (tw + 8) + 8, 30 + nrows * (th + 58) + 8), (16, 16, 16))
        d = ImageDraw.Draw(im)
        d.text((8, 6), "shoot index  %d-%d of %d" % (pi + 1, pi + len(page), len(entries)), fill=(235, 235, 235), font=font(15))
        for k, e in enumerate(page):
            x = 8 + (k % cols) * (tw + 8)
            y = 30 + (k // cols) * (th + 58)
            if e.get("thumb") is not None:
                t = Image.fromarray(e["thumb"])
                t.thumbnail((tw, th))
                im.paste(t, (x + (tw - t.width) // 2, y + (th - t.height) // 2))
            d.text((x + 2, y + th + 2), e["name"][:34], fill=(255, 225, 120), font=font(13))
            d.text((x + 2, y + th + 18), e["line"][:40], fill=(210, 210, 210), font=font(11))
            d.text((x + 2, y + th + 33), e["flag"][:42], fill=(240, 140, 120), font=font(11))
        p = os.path.join(out_dir, "_index.png" if pi == 0 else "_index_p%d.png" % (pi // per + 1))
        im.save(p)
        paths.append(p)
    return paths


def unique_names(files):
    """Output base name per file; duplicates get their parent folder (and a counter)."""
    base = [os.path.splitext(os.path.basename(f))[0] for f in files]
    out, seen = [], {}
    for f, b in zip(files, base):
        name = b
        if base.count(b) > 1:
            name = "%s__%s" % (os.path.basename(os.path.dirname(os.path.abspath(f))) or "dir", b)
        while name in seen:
            seen[name] += 1
            name = "%s_%d" % (name, seen[name])
        seen.setdefault(name, 1)
        out.append(name)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--out", default="analysis", help="output folder for JSON + PNG sheets")
    ap.add_argument("--fps", type=float, default=8.0, help="samples per second (>= 2; default 8)")
    ap.add_argument("--min", type=float, default=1.0,
                    help="minimum candidate length in SOURCE seconds (default 1.0: a clean second can be slowed to 2)")
    ap.add_argument("--timeline-fps", default="25", help="frame rate of the film you will cut (25, 30, 29.97 ...)")
    ap.add_argument("--windows", type=int, default=3, help="max clean candidates per clip")
    ap.add_argument("--events", type=int, default=2, help="max action/event candidates per clip")
    ap.add_argument("--lut", help="official log-to-Rec.709 .cube to judge exposure on the converted picture")
    ap.add_argument("--no-strip", action="store_true", help="numbers only, no PNG sheets")
    a = ap.parse_args()
    if a.fps < 2:
        sys.exit("--fps must be at least 2: every second of the take must be seen")
    if a.lut and not os.path.isfile(a.lut):
        sys.exit("LUT not found: %s" % a.lut)
    try:
        tl_fps = float(parse_fps(a.timeline_fps))
    except (ValueError, ZeroDivisionError):
        sys.exit("--timeline-fps must be like 25, 29.97 or 30000/1001")
    files = collect(a.paths)
    if not files:
        sys.exit("no video files found")
    os.makedirs(a.out, exist_ok=True)
    names = unique_names(files)
    summary, index = [], []
    t_start = time.time()
    for k, (fp, name) in enumerate(zip(files, names), 1):
        eta = ""
        if k > 1:
            eta = "  (about %.0f s left)" % ((time.time() - t_start) / (k - 1) * (len(files) - k + 1))
        print("[%d/%d] %s%s" % (k, len(files), name, eta), flush=True)
        rgb, raw = None, None
        try:
            r, rgb, raw = analyse(fp, a.fps, min_len=a.min, lut=a.lut, n_windows=a.windows, n_events=a.events,
                                  timeline_fps=tl_fps)
        except Exception as e:
            print("  ERROR %s" % str(e)[:200])
            continue
        try:
            write_json(os.path.join(a.out, name + ".json"), r)
            if "error" in r:
                print("  " + r["error"])
                continue
            base = os.path.join(a.out, name)
            if not a.no_strip:
                strip_pages(r, rgb, base)
                candidate_sheets(r, rgb, base)
            best = max(r["candidates"], key=lambda c: c["score"]) if r["candidates"] else None
            ti = int(round((best["peak_t"] if best else r["duration"] / 2) * r["sample_fps"]))
            index.append({"name": name, "thumb": np.array(rgb[min(len(rgb) - 1, ti)]),
                          "line": "%.0f fps | %.1fs | tilt %s" % (r["source_fps"], r["duration"], r["tilt_deg"]),
                          "flag": "JUNK?" if r["junk"] else ("SOFT" if r["soft_clip"] else
                                                             ("shaky" if r["median_jitter_pct"] > JITTER_BAD else ""))})
            summary.append({kk: r.get(kk) for kk in ("file", "duration", "source_fps", "tilt_deg", "median_jitter_pct",
                                                     "sharpness_abs_p90", "soft_clip", "junk", "candidates", "flags")})
            summary[-1]["name"] = name
            summary[-1]["best_score"] = best["score"] if best else 0.0
            for c in r["candidates"]:
                print("  %-5s %s - %s  peak %s  score %.2f  action %.2f  %s  shake %.2f%%"
                      % (c["type"], fmt_tc(c["in"]), fmt_tc(c["out"]), fmt_tc(c["peak_t"]), c["score"],
                         c["subject_action"], c["camera"], c["jitter_pct"]))
            for fl in r["flags"]:
                if not fl.startswith("HIGH FRAME RATE"):
                    print("  ! " + fl)
        finally:
            _cleanup(rgb, raw)
    adv = slowmo_advice(summary[0]["source_fps"], tl_fps)["how"] if summary else ""
    fps_set = sorted(set(round(s["source_fps"], 2) for s in summary))
    if not a.no_strip:
        index_pages(index, a.out)
    summary.sort(key=lambda s: -s["best_score"])
    write_json(os.path.join(a.out, "_summary.json"), summary)
    print("\nframe rates in this scan: %s fps. %s" % (", ".join(map(str, fps_set)), adv if len(fps_set) == 1 else
                                                      "see each clip's slow_motion advice"))
    print("written: %s/_summary.json (ranked), _index.png, and per clip NAME.json, NAME_strip*.png, NAME_c*.png "
          "(%.0f s). Candidates are suggestions: LOOK at the sheets." % (a.out, time.time() - t_start))


if __name__ == "__main__":
    main()
