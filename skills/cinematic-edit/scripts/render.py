#!/usr/bin/env python3
"""render.py: render edit_plan.json to a finished film with ffmpeg.

The plan is checked first with the same rules as plan_check.py; a plan with
FAIL items is refused (use --force to render anyway, e.g. for a quick look).

Every shot is FINISHED before it is cut in (a camera shot is never used raw):
  extra rotate -> stabilise (optional) -> straighten (rotate + minimal zoom so
  no corners show) -> reframe to the output aspect (cover, focal point x/y,
  zoom) -> scale -> frame interpolation (optional, AFTER the downscale: fast)
  -> YUV to RGB with the right matrix (BT.709 for untagged camera files)
  -> official LUT (log -> Rec.709) -> gentle grade (optional) -> speed / ramp
  -> exact fps -> sub-pixel eased push-in (optional) -> exact frame count.
Stills (a .png/.jpg 'src' with 'duration') go through the same framing.
Shots are joined with hard cuts or dissolves ("transition": "dissolve:12" =
12 frames, overlapping both shots). Designed PNG overlays (end card, logo,
title made elsewhere) are laid on top with alpha and an opacity fade only.
Music is trimmed to the film, faded, optionally mixed with real shot sound,
and loudness-normalised in two passes (a silent track is left alone). The file
is tagged BT.709 so phones and Instagram show the colours you graded.

Usage:
  python3 render.py edit_plan.json --out film.mp4 [--draft] [--hevc10] [--lufs -14] [--keep] [--force]

--draft   half resolution, fast encode, for checking the cut
--hevc10  10-bit HEVC delivery (less banding) when libx265 is available
          (warns and falls back to H.264 when it is not, or with --draft)
--force   render even when the plan check FAILs

Plan fields handled here (all optional except src/in/out or src/duration):
  fps 25 | 29.97 | "30000/1001"   (NTSC rates are kept exact)
  lut       path, relative to the plan folder or absolute
  grade     {"exposure": stops, "temp": -1..1 (+ warm), "tint": -1..1 (+ magenta),
             "contrast": 0.8..1.2, "saturation": 0.8..1.2}  applied after the LUT,
             gentle by design; real grading belongs in the NLE
  stabilize true | "vidstab"   two-pass vid.stab with an automatic crop-safe zoom.
             When this ffmpeg has no vid.stab (or the plan says "deshake") the shot is
             NOT stabilised and a warning says so: ffmpeg's deshake does nothing on
             flat log pictures. Use Gyroflow or the NLE's stabiliser then.
             Limits: the shot is processed in 8-bit 4:2:0; rolling-shutter wobble
             and parallax are not fixed; strong shake needs Gyroflow or another take.
  overlays  [{"png": path, "start": s, "end": s, "fade": frames, "x": px, "y": px,
             "scale": fraction of output width, "opacity": 0-1}]  x/y are the
             top-left corner in output pixels (default: centred)
Push-ins use 8-bit RGB for the sub-pixel zoom (perspective filter) on a 2x canvas.
No network.
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (find_tool, lut_filter, ff_path, ffprobe_json, video_stream, rotation_of, rational,  # noqa: E402
                     ramp_expr, is_still, parse_fps, fps_str, layout, scale_in_opts)


def ease_expr(u):
    """Cosine ease-in-out of u (0..1) as an ffmpeg expression."""
    return "(0.5-0.5*cos(PI*min(max(%s,0),1)))" % u


def grade_filters(g):
    """Gentle per-shot grade after the LUT, in RGB, as ffmpeg filters (list).

    exposure: stops, applied as a display-gamma gain 2^(stops/2.2)
    temp:     +1 = warm (red +10 %, blue -10 %), -1 = cool
    tint:     +1 = magenta (green -8 %), -1 = green
    saturation: mix with Rec.709 luma;  contrast: around mid-grey 0.45
    """
    if not g:
        return []
    out = []
    e = 2.0 ** (float(g.get("exposure", 0.0)) / 2.2)
    t = float(g.get("temp", 0.0))
    ti = float(g.get("tint", 0.0))
    s = float(g.get("saturation", 1.0))
    gains = (e * (1 + 0.10 * t), e * (1 - 0.08 * ti), e * (1 - 0.10 * t))
    lw = (0.2126, 0.7152, 0.0722)
    m = []
    for r in range(3):
        row = [(1 - s) * lw[c] + (s if c == r else 0.0) for c in range(3)]
        m.append([gains[r] * v for v in row])
    if any(abs(m[r][c] - (1.0 if r == c else 0.0)) > 1e-4 for r in range(3) for c in range(3)):
        out.append("colorchannelmixer=rr=%.5f:rg=%.5f:rb=%.5f:gr=%.5f:gg=%.5f:gb=%.5f:br=%.5f:bg=%.5f:bb=%.5f"
                   % tuple(v for row in m for v in row))
    c = float(g.get("contrast", 1.0))
    if abs(c - 1.0) > 1e-4:
        ex = "clip((val-0.45*maxval)*%.5f+0.45*maxval\\,minval\\,maxval)" % c
        out.append("lutrgb=r=%s:g=%s:b=%s" % (ex, ex, ex))
    return out


def has_filter(name, _cache={}):
    if name not in _cache:
        p = subprocess.run([find_tool("ffmpeg"), "-hide_banner", "-filters"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _cache[name] = (" %s " % name) in p.stdout.decode("utf-8", "replace")
    return _cache[name]


def has_encoder(name):
    p = subprocess.run([find_tool("ffmpeg"), "-hide_banner", "-encoders"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return (" %s " % name) in p.stdout.decode("utf-8", "replace")


def run(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        sys.exit("ffmpeg failed:\n" + p.stderr.decode("utf-8", "replace")[-2500:])
    return p.stderr.decode("utf-8", "replace")


def shot_filter(s, src, vs, ow, oh, fps, nframes, stab=None):
    """Filter chain for one shot. vs = ffprobe video stream (None for stills).

    Returns the -vf string. Output: exactly nframes frames, yuv422p10le, BT.709.
    """
    fpsf = float(parse_fps(fps))
    w, h = int(vs["width"]), int(vs["height"])
    if not is_still(s):
        rot = rotation_of(vs)
        if rot in (90, -90, 270, -270):
            w, h = h, w  # ffmpeg applies the rotation flag on decode
    extra_rot = int(s.get("rotate", 0) or 0) % 360
    if extra_rot in (90, 270):
        w, h = h, w
    f = []
    if extra_rot == 90:
        f.append("transpose=1")
    elif extra_rot == 270:
        f.append("transpose=2")
    elif extra_rot == 180:
        f.append("transpose=1,transpose=1")
    if stab:
        f.append(stab)
    ang = float(s.get("straighten", 0.0))
    if abs(ang) > 0.01:
        r = math.radians(abs(ang))
        k = math.cos(r) + math.sin(r) * max(w, h) / float(min(w, h))
        # rotate keeps 10-bit only in 4:2:0 / 4:4:4 YUV (no colour-matrix step involved)
        f.append("format=yuv444p16le,rotate=%.7f:ow=iw:oh=ih:fillcolor=black:bilinear=1" % math.radians(ang))
        cw, ch = int(w / k) // 2 * 2, int(h / k) // 2 * 2
        f.append("crop=%d:%d" % (cw, ch))
        w, h = cw, ch
    # cover-crop to output aspect, then reframe zoom around a focal point
    rf = s.get("reframe") or {}
    z = max(1.0, float(rf.get("zoom", 1.0)))
    tgt = ow / float(oh)
    cw = min(w, h * tgt) / z
    ch = cw / tgt
    cx = float(rf.get("x", 0.5)) * w
    cy = float(rf.get("y", 0.5)) * h
    x0 = min(max(cx - cw / 2, 0), w - cw)
    y0 = min(max(cy - ch / 2, 0), h - ch)
    f.append("crop=%d:%d:%d:%d" % (int(cw) // 2 * 2, int(ch) // 2 * 2, int(x0), int(y0)))
    push = s.get("push")
    do_push = bool(push) and abs(float(push[-1]) - float(push[0])) > 1e-4
    # a push zooms on a 2x canvas so the per-frame crop is sub-pixel (no 2-px stepping)
    cwid, chei = (ow * 2, oh * 2) if do_push else (ow, oh)
    # scale in the source YUV (no matrix step yet)
    f.append("scale=%d:%d:flags=lanczos+accurate_rnd" % (cwid, chei))
    sp = float(s.get("speed", 1.0))
    still = is_still(s)
    src_fps = (rational(vs.get("r_frame_rate")) or fpsf) if not still else fpsf
    ramp = s.get("ramp") if not still else None
    if not still:
        if ramp:
            kmax = max(float(k) for _, k in ramp)
            if src_fps / kmax < fpsf * 0.95:
                if s.get("interpolate"):
                    f.append("format=yuv444p,minterpolate=fps=%.6f:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"
                             % (fpsf * kmax))
                else:
                    print("  ! ramp slows to 1/%.1f but the clip has %.0f fps: frames will repeat; add 'interpolate'"
                          % (kmax, src_fps))
        elif sp < 1.0 and src_fps * sp < fpsf * 0.95:
            if s.get("interpolate"):
                # motion-compensated interpolation AFTER crop+scale (far faster than at source size).
                # It can warp: check every frame; for hero shots prefer a dedicated interpolator.
                f.append("format=yuv444p,minterpolate=fps=%.6f:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"
                         % (fpsf / sp))
            else:
                print("  ! speed %.2f on %.0f fps footage without 'interpolate': frames will repeat (judder)"
                      % (sp, src_fps))
    # YUV -> RGB with the explicit matrix/range of the source (BT.709 when untagged)
    f.append("scale=%d:%d:%s,format=gbrp16le" % (cwid, chei, scale_in_opts(vs)))
    lf = lut_filter(s.get("lut"))
    if lf:
        f.append(lf)
    f += grade_filters(s.get("grade"))
    if ramp:
        expr, _ = ramp_expr(ramp)
        f.append("setpts='%s'/TB" % expr)
    elif not still and abs(sp - 1.0) > 1e-6:
        f.append("setpts=(PTS-STARTPTS)/%.8f" % sp)
    # pad a few cloned frames in case the source ends a hair early, then the exact rate
    # (tpad must come BEFORE fps: after it the mov muxer loses the last frame)
    f.append("tpad=stop_mode=clone:stop_duration=0.3")
    f.append("fps=%s" % fps_str(fps))
    if do_push:
        p0, p1 = float(push[0]), float(push[-1])
        D = max(nframes - 1, 1)
        zt = "(%.6f+(%.6f)*%s)" % (p0, p1 - p0, ease_expr("on/%d" % D))
        # corners of the zoom window in source pixels (sense=source), evaluated per frame with sub-pixel precision
        xo = "(W/2)*(1-1/%s)" % zt
        yo = "(H/2)*(1-1/%s)" % zt
        f.append("format=gbrp,perspective=x0='%s':y0='%s':x1='W-%s':y1='%s':x2='%s':y2='H-%s':x3='W-%s':y3='H-%s'"
                 ":interpolation=cubic:sense=source:eval=frame" % (xo, yo, xo, yo, xo, yo, xo, yo))
        f.append("scale=%d:%d:flags=lanczos+accurate_rnd" % (ow, oh))
    f.append("trim=end_frame=%d" % nframes)  # (every intermediate is written with -r: without frame durations the mov edit list hides the last frame)
    f.append("scale=out_color_matrix=bt709:out_range=tv,format=yuv422p10le")
    f.append("setsar=1")
    return ",".join(f)


_STAB_SKIP = ("  ! shot %d: stabilisation NOT applied (%s). ffmpeg's single-pass deshake was tested on real\n"
              "    log footage: it is a no-op on flat log pictures and chases subject motion on graded ones.\n"
              "    Stabilise this shot in Gyroflow (gyro data) or the NLE (Warp Stabilizer / Resolve\n"
              "    Stabilizer), or pick a steadier take.")


def stab_filters(s, src, tmp, i, start, length, ff):
    """Two-pass vid.stab when this ffmpeg has it. Returns the transform filter string,
    or None (with a printed warning) when vid.stab is missing or "deshake" was asked for."""
    mode = s.get("stabilize")
    have = has_filter("vidstabdetect") and has_filter("vidstabtransform")
    if mode == "deshake":
        print(_STAB_SKIP % (i, "\"deshake\" is not used"))
        return None
    if not have:
        print(_STAB_SKIP % (i, "this ffmpeg has no vid.stab"))
        return None
    pre = []
    er = int(s.get("rotate", 0) or 0) % 360
    if er == 90:
        pre.append("transpose=1")
    elif er == 270:
        pre.append("transpose=2")
    elif er == 180:
        pre.append("transpose=1,transpose=1")
    trf = os.path.join(tmp, "stab%03d.trf" % i)
    vf = ",".join(pre + ["format=yuv420p", "vidstabdetect=shakiness=6:accuracy=15:stepsize=6:result=%s" % ff_path(trf)])
    run([ff, "-v", "error", "-y", "-ss", "%.4f" % start, "-t", "%.4f" % length, "-i", src, "-vf", vf, "-f", "null", "-"])
    return "format=yuv420p,vidstabtransform=input=%s:smoothing=12:optzoom=1:interpol=bicubic:crop=black" % ff_path(trf)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan")
    ap.add_argument("--out", required=True)
    ap.add_argument("--draft", action="store_true")
    ap.add_argument("--hevc10", action="store_true")
    ap.add_argument("--lufs", type=float, default=-14.0)
    ap.add_argument("--keep", action="store_true", help="keep intermediate shot files")
    ap.add_argument("--force", action="store_true", help="render even when the plan check FAILs")
    ap.add_argument("--no-lutcheck", action="store_true", help="do not measure whether LUTs convert log clips")
    a = ap.parse_args()
    try:
        with open(a.plan, encoding="utf-8") as fh:
            plan = json.load(fh)
    except (OSError, ValueError) as e:
        sys.exit("cannot read plan: %s" % e)
    base = os.path.dirname(os.path.abspath(a.plan))
    P = lambda p: p if os.path.isabs(p) else os.path.join(base, p)  # noqa: E731

    from plan_check import check_plan
    chk = check_plan(plan, base, lutcheck=not a.no_lutcheck, verbose_cuts=False)
    if chk["fails"]:
        for x in chk["fails"]:
            print("  FAIL  " + x)
        if not a.force or chk["layout"] is None:
            sys.exit("plan check FAILED: fix the plan (plan_check.py shows everything)%s"
                     % (", or pass --force to render anyway" if chk["layout"] is not None else ""))
        print("  --force: rendering despite FAIL items")
    lay = chk["layout"]

    fps = parse_fps(plan.get("fps", 25))
    fpsf = float(fps)
    fs = fps_str(fps)
    PW, PH = plan.get("size", [1080, 1920])
    ow, oh = PW, PH
    if a.draft:
        ow, oh = ow // 2 // 2 * 2, oh // 2 // 2 * 2
    shots = [dict(s) for s in plan["shots"]]
    for s in shots:  # every path relative to the plan folder
        s["src"] = P(s["src"])
        if s.get("lut"):
            s["lut"] = P(s["lut"])
    tmp = tempfile.mkdtemp(prefix="ce_render_")
    ff = find_tool("ffmpeg")
    segs = []
    try:
        for i, s in enumerate(shots, 1):
            src = s["src"]
            n = lay["frames"][i - 1]
            tl = n / fpsf
            vs = video_stream(ffprobe_json(src))
            if is_still(s):
                inp = ["-loop", "1", "-framerate", fs, "-t", "%.4f" % (tl + 0.5), "-i", src]
                stab = None
            else:
                src_len = float(s["out"]) - float(s["in"])
                inp = ["-ss", "%.4f" % float(s["in"]), "-t", "%.4f" % (src_len + 0.3), "-i", src]
                stab = stab_filters(s, src, tmp, i, float(s["in"]), src_len + 0.3, ff) if s.get("stabilize") else None
            vf = shot_filter(s, src, vs, ow, oh, fs, n, stab=stab)
            out = os.path.join(tmp, "s%03d.mov" % i)
            run([ff, "-v", "error", "-y"] + inp + ["-vf", vf, "-an", "-frames:v", str(n), "-r", fs,
                 "-c:v", "prores_ks", "-profile:v", "3", "-vendor", "apl0", "-pix_fmt", "yuv422p10le",
                 "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", out])
            segs.append(out)
            print("  shot %d/%d  %d frames (%.2fs)  %s" % (i, len(shots), n, tl, os.path.basename(src)))

        # dissolves: each overlap is blended into its own short piece (exactly D frames, linear
        # opacity), then every piece is joined with one hard concat. (Chained xfade/concat in one
        # graph lost the last frame of a shot in tests; this way every frame is accounted for.)
        trans = {}
        for i in range(1, len(segs)):
            d = lay["dissolves"][i]
            if d <= 0:
                continue
            L0 = lay["frames"][i - 1]
            tp = os.path.join(tmp, "t%03d.mov" % i)
            run([ff, "-v", "error", "-y", "-i", segs[i - 1], "-i", segs[i], "-filter_complex",
                 "[0:v]trim=start_frame=%d,setpts=PTS-STARTPTS[a];[1:v]trim=end_frame=%d,setpts=PTS-STARTPTS[b];"
                 "[a][b]blend=all_expr='A*(1-(N+1)/%d)+B*(N+1)/%d'" % (L0 - d, d, d + 1, d + 1),
                 "-frames:v", str(d), "-r", fs, "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", tp])
            trans[i] = tp
        inputs, fc, pieces, k = [], [], [], 0
        for i, sgm in enumerate(segs):
            if i in trans:
                inputs += ["-i", trans[i]]
                fc.append("[%d:v]setpts=PTS-STARTPTS[p%d]" % (k, len(pieces)))
                pieces.append("[p%d]" % len(pieces))
                k += 1
            a0 = lay["dissolves"][i] if i else 0
            a1 = lay["frames"][i] - (lay["dissolves"][i + 1] if i + 1 < len(segs) else 0)
            inputs += ["-i", sgm]
            fc.append("[%d:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS[p%d]" % (k, a0, a1, len(pieces)))
            pieces.append("[p%d]" % len(pieces))
            k += 1
        fc.append("%sconcat=n=%d:v=1:a=0[vj]" % ("".join(pieces), len(pieces)))
        cur = "[vj]"
        total_frames = lay["total"]
        total = total_frames / fpsf
        # designed PNG overlays: alpha respected, opacity fade only (no boxes, no motion)
        ov_inputs = []
        for j, o in enumerate(plan.get("overlays") or []):
            st, en = float(o["start"]), min(float(o["end"]), total)
            if en <= st:
                continue
            dur = en - st
            fd = min(float(o.get("fade", 0)) / fpsf, dur / 2)
            ov_inputs += ["-loop", "1", "-framerate", fs, "-t", "%.4f" % (dur + 0.1), "-i", P(o["png"])]
            sc = ow / float(PW)
            chain = "[%d:v]format=rgba" % k
            if o.get("scale"):
                chain += ",scale=%d:-1:flags=lanczos" % max(2, int(round(ow * float(o["scale"]))))
            elif sc != 1.0:
                chain += ",scale=iw*%.4f:-1:flags=lanczos" % sc
            if float(o.get("opacity", 1.0)) < 1.0:
                chain += ",colorchannelmixer=aa=%.4f" % float(o["opacity"])
            if fd > 0:
                chain += ",fade=t=in:st=0:d=%.4f:alpha=1,fade=t=out:st=%.4f:d=%.4f:alpha=1" % (fd, dur - fd, fd)
            chain += (",scale=out_color_matrix=bt709:out_range=tv,format=yuva422p10le,"
                      "setpts=PTS-STARTPTS+%.6f/TB[ov%d]" % (st, j))
            fc.append(chain)
            x = ("%d" % int(round(float(o["x"]) * sc))) if "x" in o else "(W-w)/2"
            y = ("%d" % int(round(float(o["y"]) * sc))) if "y" in o else "(H-h)/2"
            lab = "[o%d]" % j
            fc.append("%s[ov%d]overlay=x=%s:y=%s:format=yuv422p10:eof_action=pass:enable='between(t,%.6f,%.6f)'%s"
                      % (cur, j, x, y, st, en, lab))
            cur = lab
            k += 1
        video_map = cur

        # audio: music + optional real shot sound
        amix_in, afc, ainputs = [], [], []
        mus = plan.get("music") or {}
        if mus.get("file"):
            ainputs += ["-ss", "%.4f" % float(mus.get("start", 0)), "-t", "%.4f" % (total + 0.5), "-i", P(mus["file"])]
            fo = float(mus.get("fade_out", 1.0))
            fi = float(mus.get("fade_in", 0.0))
            chain = "[%d:a]aresample=48000,atrim=0:%.6f,asetpts=PTS-STARTPTS" % (k, total)
            if fi > 0:
                chain += ",afade=t=in:d=%.3f" % fi
            if fo > 0:
                chain += ",afade=t=out:st=%.4f:d=%.3f" % (max(0, total - fo), fo)
            chain += ",volume=%.2fdB[mus]" % float(mus.get("gain_db", 0))
            afc.append(chain)
            amix_in.append("[mus]")
            k += 1
        for i, s in enumerate(shots):
            t = lay["starts"][i] / fpsf
            ln = lay["frames"][i] / fpsf
            if (s.get("sound_db") is not None and not is_still(s) and abs(float(s.get("speed", 1.0)) - 1.0) < 1e-6
                    and not s.get("ramp")):
                info = ffprobe_json(s["src"])
                if not any(x.get("codec_type") == "audio" for x in info.get("streams", [])):
                    print("  ! shot %d has sound_db but its clip has no audio" % (i + 1))
                    continue
                ainputs += ["-ss", "%.4f" % float(s["in"]), "-t", "%.4f" % ln, "-i", s["src"]]
                afc.append("[%d:a]aresample=48000,atrim=0:%.4f,asetpts=PTS-STARTPTS,afade=t=in:d=0.04,"
                           "afade=t=out:st=%.4f:d=0.08,volume=%.2fdB,adelay=%d:all=1[fx%d]"
                           % (k, ln, max(0, ln - 0.08), float(s["sound_db"]), int(round(t * 1000)), i))
                amix_in.append("[fx%d]" % i)
                k += 1
        if amix_in:
            afc.append("%samix=inputs=%d:normalize=0:duration=longest,apad,atrim=0:%.6f[aout]"
                       % ("".join(amix_in), len(amix_in), total))
        graph = ";".join(fc + afc)

        mix = os.path.join(tmp, "joined.mov")
        cmd = [ff, "-v", "error", "-y"] + inputs + ov_inputs + ainputs + ["-filter_complex", graph, "-map", video_map]
        if amix_in:
            cmd += ["-map", "[aout]", "-c:a", "pcm_s24le", "-ar", "48000"]
        cmd += ["-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-frames:v", str(total_frames),
                "-r", fs, mix]
        run(cmd)

        # loudness: two-pass loudnorm (skipped for silent / near-silent music, which would break it)
        audio_args = ["-an"]
        if amix_in:
            st = run([ff, "-hide_banner", "-i", mix, "-af",
                      "loudnorm=I=%.1f:TP=-1.5:LRA=11:print_format=json" % a.lufs, "-f", "null", "-"])
            try:
                m = json.loads(st[st.rfind("{"):st.rfind("}") + 1])
                ii = float(m["input_i"])
            except (ValueError, KeyError):
                m, ii = None, float("-inf")
            if m is None or not math.isfinite(ii) or ii < -60:
                print("  ! audio is silent or nearly silent (%s LUFS): loudness normalisation skipped" % ii)
                audio_args = ["-c:a", "aac", "-b:a", "320k", "-ar", "48000"]
            else:
                ln = ("loudnorm=I=%.1f:TP=-1.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:"
                      "measured_thresh=%s:offset=%s:linear=true" % (a.lufs, m["input_i"], m["input_tp"], m["input_lra"],
                                                                   m["input_thresh"], m["target_offset"]))
                audio_args = ["-af", ln + ",aresample=48000", "-c:a", "aac", "-b:a", "320k", "-ar", "48000"]
        tags = ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv"]
        use_hevc = a.hevc10 and not a.draft and has_encoder("libx265")
        if a.hevc10 and not use_hevc:
            print("  ! --hevc10 not used (%s): delivering 8-bit H.264 instead"
                  % ("--draft" if a.draft else "this ffmpeg has no libx265"))
        if use_hevc:
            venc = ["-c:v", "libx265", "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p10le", "-tag:v", "hvc1",
                    "-x265-params", "colorprim=bt709:transfer=bt709:colormatrix=bt709:range=limited:log-level=error"]
        else:
            venc = ["-c:v", "libx264", "-crf", "23" if a.draft else "16", "-preset", "veryfast" if a.draft else "slow",
                    "-pix_fmt", "yuv420p", "-profile:v", "high"]
        setp = ["-vf", "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv"]
        run([ff, "-v", "error", "-y", "-i", mix] + setp + venc + tags + audio_args +
            ["-frames:v", str(total_frames), "-r", fs, "-movflags", "+faststart", a.out])
        print("rendered %s  (%d frames = %.3fs, %dx%d @ %s fps)" % (a.out, total_frames, total, ow, oh, fs))
    finally:
        if a.keep:
            print("intermediates kept in", tmp)
        else:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
