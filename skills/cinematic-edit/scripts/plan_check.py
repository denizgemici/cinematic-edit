#!/usr/bin/env python3
"""plan_check.py: check an edit plan BEFORE rendering.

Reads edit_plan.json (see templates/edit_plan.example.json) and reports, with
numbers (thresholds follow references/numbers.md), everything that usually
makes an edit look amateur:

  fields      every field is validated with a clear message (no tracebacks)
  structure   one-sentence idea present, every shot has a reason/role,
              the film ends on its result (last shot is the longest or 2nd longest)
  rhythm      ASL, median, spread (CV), longest/ASL vs the chosen register;
              uniform lengths; shots under 0.5 s (12 frames for role
              accent/breath); same shot size > 3 in a row; dissolves are
              subtracted (exact frames, the same numbers render.py produces)
  repeats     the same source range used twice; one clip overused
  pixels      effective upscale per shot (aspect crop + reframe + straighten +
              push-in + stabiliser zoom): soft hero shots are caught
  push-ins    more than ~1/3 of shots with a push = the "Ken Burns" AI-edit look
  source      rotation flag + extra 'rotate' (ffmpeg already applies the flag),
              conformed slow motion (k = capture/timeline, no quota) vs deep slow
              motion (k >= 4) and ramps (about 2 moments per 15 s), frame repeats
              when slowing without enough real frames, high-frame-rate clips used
              at real speed (info only)
  colour      log clips without a 'lut' (WARN) and LUTs that do not convert the
              log (FAIL, measured with lutcheck.py, cached)
  music       cuts on beat (2 frames early .. 0.5 frame late counts; the middle of
              a dissolve is its cut point), per-cut offset in frames, cuts 2+
              frames late, runs of cuts on CONSECUTIVE beats

render.py runs the same checks and refuses to render a plan with FAIL items
(unless --force).

Usage: python3 plan_check.py edit_plan.json [--strict] [--no-lutcheck]
Exit code 1 when there are FAIL items (2 in --strict when there are WARNs).
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (ffprobe_json, video_stream, rational, rotation_of,  # noqa: E402
                     is_still, parse_fps, layout, transition_frames, ramp_expr)

REGISTERS = {
    # name: (ASL min, ASL max) seconds on the timeline (references/numbers.md section 3)
    "luxury": (2.5, 5.0),
    "premium": (2.0, 4.0),
    "brand": (1.2, 2.5),
    "social": (0.8, 1.8),
    "hype": (0.4, 1.2),
}
SCALES = ("extreme-wide", "wide", "medium", "close", "detail")
ROLES = ("hook", "build", "turn", "hero", "end", "accent", "breath", "end-card")
GRADE_RANGES = {  # field: (hard min, hard max, gentle min, gentle max)
    "exposure": (-2.0, 2.0, -0.7, 0.7),
    "temp": (-1.0, 1.0, -1.0, 1.0),
    "tint": (-1.0, 1.0, -1.0, 1.0),
    "contrast": (0.5, 1.5, 0.8, 1.2),
    "saturation": (0.0, 2.0, 0.8, 1.2),
}
DEEP_PER_15S = 2          # deep slow moments / ramps per 15 s (numbers.md section 1)
PUSH_SHARE = 1.0 / 3.0    # push-ins on at most ~1/3 of shots (numbers.md section 5)


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def src_info(cache, p):
    if p not in cache:
        try:
            if is_still({"src": p}):
                from PIL import Image
                with Image.open(p) as im:
                    cache[p] = {"w": im.size[0], "h": im.size[1], "rot": 0, "fps": 0.0, "dur": 1e9, "still": True}
            else:
                info = ffprobe_json(p)
                vs = video_stream(info)
                w, h = int(vs["width"]), int(vs["height"])
                rot = rotation_of(vs)
                if rot in (90, -90, 270, -270):
                    w, h = h, w
                cache[p] = {"w": w, "h": h, "rot": rot, "fps": rational(vs.get("r_frame_rate")),
                            "dur": float(info.get("format", {}).get("duration") or 0)}
        except Exception as e:
            cache[p] = {"error": str(e)[:200]}
    return cache[p]


def effective_upscale(sw, sh, ow, oh, shot):
    """How many output pixels each source pixel must cover (1.0 = native)."""
    base = max(ow / float(sw), oh / float(sh))  # cover-fit the source into the output aspect
    zoom = float((shot.get("reframe") or {}).get("zoom", 1.0))
    ang = abs(float(shot.get("straighten", 0.0)))
    if ang:
        r = math.radians(ang)
        a = max(ow, oh) / float(min(ow, oh))
        zoom *= math.cos(r) + math.sin(r) * a
    push = shot.get("push")
    if push:
        zoom *= max(float(push[0]), float(push[-1]))
    if shot.get("stabilize") and shot.get("stabilize") != "deshake":
        zoom *= 1.06  # crop-safe zoom of the stabiliser (approximate)
    return base * zoom


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def validate(plan, P):
    """Field validation. Returns (fails, warns, bad_shot_indexes)."""
    fails, warns, bad = [], [], set()
    if not isinstance(plan, dict):
        return ["the plan is not a JSON object"], [], bad
    try:
        parse_fps(plan.get("fps", 25))
    except (ValueError, TypeError, ZeroDivisionError):
        fails.append("'fps' must be a number or a rational string like \"30000/1001\" (got %r)" % (plan.get("fps"),))
    size = plan.get("size", [1080, 1920])
    if not (isinstance(size, list) and len(size) == 2 and all(isinstance(v, int) and v > 0 and v % 2 == 0 for v in size)):
        fails.append("'size' must be [width, height] with even whole numbers, e.g. [1080, 1920] (got %r)" % (size,))
    shots = plan.get("shots")
    if not isinstance(shots, list) or not shots:
        fails.append("plan has no 'shots' list")
        return fails, warns, bad
    for i, s in enumerate(shots, 1):
        e = []
        if not isinstance(s, dict):
            fails.append("shot %d is not an object" % i)
            bad.add(i)
            continue
        src = s.get("src")
        if not isinstance(src, str) or not src:
            e.append("'src' (source file) is missing")
        elif not os.path.isfile(P(src)):
            e.append("source not found: %s" % src)
        if is_still(s):
            if not _num(s.get("duration")) or s["duration"] <= 0:
                e.append("a still (picture) shot needs 'duration' in seconds > 0")
            for k in ("speed", "ramp", "interpolate", "stabilize"):
                if s.get(k):
                    warns.append("shot %d: '%s' is ignored on a still picture" % (i, k))
        else:
            if not _num(s.get("in")) or not _num(s.get("out")):
                e.append("'in' and 'out' (source seconds) must both be numbers")
            elif s["out"] <= s["in"]:
                e.append("'out' (%.3f) must be after 'in' (%.3f)" % (s["out"], s["in"]))
            elif s["in"] < 0:
                e.append("'in' must be >= 0")
            if "speed" in s and (not _num(s["speed"]) or s["speed"] <= 0):
                e.append("'speed' must be a number > 0 (0.5 = half speed), got %r" % (s["speed"],))
            if s.get("ramp") is not None:
                r = s["ramp"]
                ok = isinstance(r, list) and len(r) >= 2 and all(
                    isinstance(k, (list, tuple)) and len(k) == 2 and _num(k[0]) and _num(k[1]) and k[1] > 0 for k in r)
                if not ok:
                    e.append("'ramp' must be [[source_s, k], ...] with at least 2 keys and k > 0 (1 = real time, 2 = half speed)")
                else:
                    try:
                        ramp_expr(r)
                    except ValueError as ex:
                        e.append("'ramp': %s" % ex)
                    if abs(float(r[0][0])) > 1e-6:
                        e.append("'ramp' must start at source time 0 (relative to 'in')")
                    if "speed" in s and abs(float(s["speed"]) - 1) > 1e-6:
                        warns.append("shot %d has both 'ramp' and 'speed': 'speed' is ignored" % i)
            st = s.get("stabilize")
            if st not in (None, False, True, "vidstab", "deshake"):
                e.append("'stabilize' must be true or \"vidstab\"")
            elif st == "deshake":
                warns.append("shot %d: \"deshake\" is not applied by render.py (no effect on log pictures); "
                             "use true (vid.stab), Gyroflow or the NLE's stabiliser" % i)
        try:
            transition_frames(s)
        except ValueError as ex:
            e.append(str(ex))
        if "rotate" in s and s["rotate"] not in (0, 90, 180, 270, -90):
            e.append("'rotate' must be 0, 90, 180 or 270 (extra rotation on top of the camera's flag)")
        if "straighten" in s and not _num(s["straighten"]):
            e.append("'straighten' must be degrees (number)")
        rf = s.get("reframe")
        if rf is not None:
            if not isinstance(rf, dict):
                e.append("'reframe' must be {\"x\":0-1, \"y\":0-1, \"zoom\":>=1}")
            else:
                for k in ("x", "y"):
                    if k in rf and (not _num(rf[k]) or not 0 <= rf[k] <= 1):
                        e.append("'reframe.%s' must be between 0 and 1" % k)
                if "zoom" in rf and (not _num(rf["zoom"]) or rf["zoom"] < 1):
                    e.append("'reframe.zoom' must be >= 1")
        pu = s.get("push")
        if pu is not None and not (isinstance(pu, list) and len(pu) == 2 and all(_num(v) and v >= 1 for v in pu)):
            e.append("'push' must be [start_scale, end_scale], both >= 1 (e.g. [1.0, 1.04])")
        g = s.get("grade")
        if g is not None:
            if not isinstance(g, dict):
                e.append("'grade' must be an object")
            else:
                for k, v in g.items():
                    if k not in GRADE_RANGES:
                        e.append("'grade.%s' is unknown (use %s)" % (k, ", ".join(GRADE_RANGES)))
                    elif not _num(v):
                        e.append("'grade.%s' must be a number" % k)
                    else:
                        lo, hi, glo, ghi = GRADE_RANGES[k]
                        if not lo <= v <= hi:
                            e.append("'grade.%s' %.2f is outside %.1f..%.1f" % (k, v, lo, hi))
                        elif not glo <= v <= ghi:
                            warns.append("shot %d: grade.%s %.2f is strong (gentle range %.1f..%.1f): heavy grading "
                                         "belongs in the NLE" % (i, k, v, glo, ghi))
        if s.get("lut") and not os.path.isfile(P(s["lut"])):
            e.append("LUT not found: %s (relative paths are read from the plan's folder)" % s["lut"])
        if "sound_db" in s and s["sound_db"] is not None and not _num(s["sound_db"]):
            e.append("'sound_db' must be a number (dB)")
        if s.get("role") and s["role"] not in ROLES:
            warns.append("shot %d: role '%s' is not one of %s" % (i, s["role"], ", ".join(ROLES)))
        for x in e:
            fails.append("shot %d: %s" % (i, x))
        if e:
            bad.add(i)
    ovs = plan.get("overlays") or []
    if not isinstance(ovs, list):
        fails.append("'overlays' must be a list")
        ovs = []
    for j, o in enumerate(ovs, 1):
        if not isinstance(o, dict):
            fails.append("overlay %d is not an object" % j)
            continue
        if not isinstance(o.get("png"), str) or not os.path.isfile(P(o["png"])):
            fails.append("overlay %d: 'png' not found: %s" % (j, o.get("png")))
        else:
            try:
                from PIL import Image
                with Image.open(P(o["png"])) as im:
                    if im.mode not in ("RGBA", "LA") and "transparency" not in im.info:
                        warns.append("overlay %d: %s has no alpha channel: it will cover the picture as a box"
                                     % (j, os.path.basename(o["png"])))
            except Exception:
                fails.append("overlay %d: cannot read %s as an image" % (j, o["png"]))
        if not _num(o.get("start")) or not _num(o.get("end")) or o["end"] <= o["start"] or o["start"] < 0:
            fails.append("overlay %d: 'start' and 'end' (film seconds) must be numbers with end > start >= 0" % j)
        for k in ("fade", "x", "y", "scale", "opacity"):
            if k in o and not _num(o[k]):
                fails.append("overlay %d: '%s' must be a number" % (j, k))
    mus = plan.get("music") or {}
    if mus:
        if not isinstance(mus, dict):
            fails.append("'music' must be an object")
        elif mus.get("file") and not os.path.isfile(P(mus["file"])):
            fails.append("music file not found: %s" % mus["file"])
        elif "start" in mus and (not _num(mus["start"]) or mus["start"] < 0):
            fails.append("'music.start' must be seconds >= 0")
    return fails, warns, bad


def check_plan(plan, base, lutcheck=True, verbose_cuts=True):
    """All checks. Returns dict(fails, warns, notes, layout). Never raises on bad plans."""
    def P(p):
        return p if os.path.isabs(p) else os.path.join(base, p)

    fails, warns, bad = validate(plan, P)
    notes = []
    out = {"fails": fails, "warns": warns, "notes": notes, "layout": None}
    if fails:
        return out  # numeric checks on a broken plan would only add noise
    fps = float(parse_fps(plan.get("fps", 25)))
    ow, oh = plan.get("size", [1080, 1920])
    reg = plan.get("register", "brand")
    shots = plan["shots"]

    # --- structure
    idea = (plan.get("idea") or "").strip()
    if len(idea.split()) < 5:
        fails.append("no one-sentence controlling idea ('idea'): write the sentence the whole film obeys")
    for i, s in enumerate(shots, 1):
        if not (s.get("reason") or "").strip():
            warns.append("shot %d has no 'reason' (why it is here, what it does for the idea)" % i)

    # --- lengths on the timeline (exact frames, dissolves subtracted)
    lay = layout(shots, fps)
    out["layout"] = lay
    L = [n / fps for n in lay["frames"]]
    total = lay["total"] / fps
    asl = total / len(L)
    mean_len = sum(L) / len(L)
    srt = sorted(L)
    med = srt[len(L) // 2] if len(L) % 2 else (srt[len(L) // 2 - 1] + srt[len(L) // 2]) / 2
    sd = (sum((x - mean_len) ** 2 for x in L) / len(L)) ** 0.5
    cv = sd / mean_len
    nd = sum(1 for d in lay["dissolves"] if d)
    notes.append("%d shots, %.2fs total (%d frames at %.3f fps%s), ASL %.2fs, median %.2fs, CV %.2f, longest %.2fs (%.1fx ASL)"
                 % (len(L), total, lay["total"], fps,
                    (", %d dissolve(s) overlap %d frames" % (nd, sum(lay["dissolves"]))) if nd else "",
                    asl, med, cv, max(L), max(L) / asl if asl else 0))
    lo, hi = REGISTERS.get(reg, REGISTERS["brand"])
    if not lo * 0.8 <= asl <= hi * 1.25:
        warns.append("ASL %.2fs is outside the '%s' register (%.1f-%.1fs)" % (asl, reg, lo, hi))
    if len(L) >= 5 and cv < 0.3:
        warns.append("shot lengths too even (CV %.2f < 0.30): vary them; hold one moment, compress another" % cv)
    if len(L) >= 4 and max(L) < 2.0 * asl:
        warns.append("no held moment: longest shot is only %.1fx the average (aim >= 2x)" % (max(L) / asl))
    order = sorted(range(len(L)), key=lambda i: -L[i])
    if len(L) >= 4 and (len(L) - 1) not in order[:2] and shots[-1].get("role") != "end-card":
        warns.append("the last shot is not the longest or second longest: end on the result and let it breathe")
    min_any = int(0.5 * fps)        # one readable subject: 0.5 s (12 f @25, 15 f @30)
    min_accent = int(0.48 * fps)    # accents / breath inserts: 12 frames @25
    for i, n in enumerate(lay["frames"], 1):
        role = shots[i - 1].get("role", "")
        x = n / fps
        if role in ("accent", "breath"):
            if n < min_accent:
                warns.append("shot %d lasts %d frames: even an accent/breath insert needs %d frames" % (i, n, min_accent))
        elif n < min_any:
            warns.append("shot %d lasts %.2fs (%d frames): under 0.5 s it does not read unless it is a deliberate "
                         "accent (role 'accent' or 'breath')" % (i, x, n))
        if shots[i - 1].get("text") and x < 2.0:
            warns.append("shot %d carries text but lasts %.2fs (< 2s): text needs time to be read" % (i, x))
    run, prev = 1, None
    for i, s in enumerate(shots, 1):
        sc = s.get("scale")
        if sc and sc == prev:
            run += 1
            if run == 4:
                warns.append("4+ shots in a row at the same size ('%s') ending at shot %d: vary scale" % (sc, i))
        else:
            run = 1
        prev = sc

    # --- push-ins: the Ken Burns look
    pushes = [i for i, s in enumerate(shots, 1)
              if s.get("push") and abs(float(s["push"][-1]) - float(s["push"][0])) > 0.004]
    if len(shots) >= 3 and len(pushes) > max(1, int(math.ceil(len(shots) * PUSH_SHARE))):
        warns.append("%d of %d shots have a digital push-in (%s): more than ~1/3 reads as the Ken Burns / AI-edit look; "
                     "keep locked frames as the default" % (len(pushes), len(shots), ", ".join(map(str, pushes))))

    # --- repeats
    seen = {}
    for i, s in enumerate(shots, 1):
        if is_still(s):
            continue
        src = P(s["src"])
        for j, (a0, a1) in seen.get(src, []):
            if min(a1, float(s["out"])) - max(a0, float(s["in"])) > 0.2:
                fails.append("shot %d repeats footage already used in shot %d (same clip, overlapping time)" % (i, j))
        seen.setdefault(src, []).append((i, (float(s["in"]), float(s["out"]))))
    for src, uses in seen.items():
        if len(uses) > 3:
            warns.append("%s is used %d times: the film may feel small" % (os.path.basename(src), len(uses)))

    # --- sources: ranges, pixels, rotation, speed, colour
    cache = {}
    conform_s, deep_s, deep_n, deep_run, deep_runmax = 0.0, 0.0, 0, 0, 0
    lut_pairs = {}
    for i, s in enumerate(shots, 1):
        info = src_info(cache, P(s["src"]))
        tl = L[i - 1]
        if "error" in info:
            fails.append("shot %d: cannot read source %s (%s)" % (i, s["src"], info["error"][:80]))
            continue
        still = info.get("still", False)
        if not still and (float(s["out"]) > info["dur"] + 0.02):
            fails.append("shot %d: out %.2fs is past the end of the clip (%.2fs): the render would be short"
                         % (i, s["out"], info["dur"]))
        up = effective_upscale(info["w"], info["h"], ow, oh, s)
        role = s.get("role", "")
        limit = 1.0 if role in ("hero", "end") or s.get("scale") in ("close", "detail") else 1.15
        if up > limit + 1e-6:
            (fails if up > 1.5 else warns).append(
                "shot %d upscales %.0f%% (source %dx%d -> %dx%d with reframe/straighten/push/stabilise): soft; reduce zoom or pick another shot"
                % (i, (up - 1) * 100, info["w"], info["h"], ow, oh))
        if still:
            deep_run = 0
            continue
        if info["rot"] and int(s.get("rotate", 0) or 0) != 0:
            warns.append("shot %d: the clip has a rotation flag (%d deg) that ffmpeg already applies; the extra "
                         "'rotate': %s turns it again - check the frame is upright" % (i, info["rot"], s["rotate"]))
        cap = info["fps"]
        sp = float(s.get("speed", 1.0))
        is_deep = False
        if s.get("ramp"):
            kmax = max(float(k) for _, k in s["ramp"])
            is_deep = True
            if cap and cap / kmax < fps * 0.95 and not s.get("interpolate"):
                warns.append("shot %d ramps to 1/%.1f speed but the clip is %.0f fps: frames will repeat "
                             "(add 'interpolate' and check every frame, or ramp less)" % (i, kmax, cap))
            last_t = float(s["ramp"][-1][0])
            if abs(last_t - (float(s["out"]) - float(s["in"]))) > 0.05:
                warns.append("shot %d: last ramp key (%.2fs) should equal out-in (%.2fs)" % (i, last_t, float(s["out"]) - float(s["in"])))
        elif sp < 0.999:
            k = 1.0 / sp
            real = bool(cap) and cap * sp >= fps * 0.95
            if k >= 4 or not real:
                is_deep = True
            else:
                conform_s += tl
            if not real and not s.get("interpolate"):
                clean = min(1.0, fps / cap) if cap else 1.0
                warns.append("shot %d slowed to %.0f%% but the clip has only %.0f fps (clean conform = %.0f%%): "
                             "frames will repeat (judder); use 'interpolate' or speed %.3f"
                             % (i, sp * 100, cap, 100 * clean, clean))
            elif real and abs(cap * sp / fps - round(cap * sp / fps)) > 0.02 and not s.get("optical_flow_ok"):
                warns.append("shot %d speed %.3f is not a clean conform of %.2f fps (clean = %.3f or a whole "
                             "multiple): frames are dropped unevenly" % (i, sp, cap, fps / cap))
        elif cap and cap > fps * 1.05:
            notes.append("shot %d: %.0f fps clip used at real speed (fine; it could also play at %.0f%%)"
                         % (i, cap, 100 * fps / cap))
        if is_deep:
            deep_s += tl
            deep_n += 1
            deep_run += 1
            deep_runmax = max(deep_runmax, deep_run)
        else:
            deep_run = 0
        if s.get("straighten") and abs(float(s["straighten"])) > 15:
            warns.append("shot %d straighten %.1f deg is large: is this tilt intentional (Dutch angle)?" % (i, s["straighten"]))
        # colour: log needs the official transform, and the LUT must really convert it
        try:
            from probe import log_profile
            prof = log_profile(P(s["src"]))
        except Exception:
            prof = None
        if prof and not s.get("lut"):
            warns.append("shot %d: log clip (%s) has no 'lut': it renders log-flat unless you convert it in the NLE"
                         % (i, prof))
        elif prof and s.get("lut") and lutcheck:
            lut_pairs.setdefault((P(s["src"]), P(s["lut"])), []).append(i)
    if conform_s or deep_s:
        notes.append("slow motion: conformed (real frames, no quota) %.1fs = %.0f%%; deep slow (k>=4) / ramps: "
                     "%d shot(s), %.1fs = %.0f%%" % (conform_s, 100 * conform_s / total, deep_n, deep_s, 100 * deep_s / total))
    allowed = max(DEEP_PER_15S, int(math.ceil(total / 15.0 * DEEP_PER_15S)))
    if deep_n > allowed:
        warns.append("%d deep-slow / ramp moments in %.0fs (about %d per 15 s is the norm): keep them for the real "
                     "moments; conformed slow motion is not counted" % (deep_n, total, DEEP_PER_15S))
    if deep_runmax >= 3:
        warns.append("%d deep-slow / ramp shots in a row: the film stalls; put a real-time shot between them" % deep_runmax)
    if lut_pairs:
        from lutcheck import check as lut_check
        for (src, lut), idx in lut_pairs.items():
            r = lut_check(src, lut)
            ids = ", ".join(map(str, idx))
            if r["verdict"] == "flat":
                fails.append("shot %s: %s (%s with %s)" % (ids, r["msg"], os.path.basename(src), os.path.basename(lut)))
            elif r["verdict"] == "error":
                warns.append("shot %s: LUT check could not run: %s" % (ids, r.get("msg")))
            elif r.get("still_flat"):
                warns.append("shot %s: %s" % (ids, r["msg"]))

    # --- overlays inside the film
    for j, o in enumerate(plan.get("overlays") or [], 1):
        if float(o["end"]) > total + 1e-3:
            warns.append("overlay %d ends at %.2fs, after the film (%.2fs): it is cut" % (j, o["end"], total))

    # --- music
    mus = plan.get("music") or {}
    bfile = mus.get("beats")
    if bfile and os.path.exists(P(bfile)):
        try:
            bj = load(P(bfile))
        except ValueError:
            bj = {}
            warns.append("beats file is not valid JSON: %s" % bfile)
        off = float(mus.get("start", 0.0))
        beats = [b - off for b in bj.get("beats", []) if b - off >= -0.5]
        cut_t = [c / fps for c in lay["cut_frames"]]
        on, late, runs, r, prev_bi, rows = 0, [], 0, 0, None, []
        for k, c in enumerate(cut_t, 2):
            if not beats:
                break
            bi = min(range(len(beats)), key=lambda j: abs(beats[j] - c))
            df = (c - beats[bi]) * fps  # positive = cut after the beat
            is_on = -2.0 <= df <= 0.5
            on += is_on
            rows.append("%d:%+.1f%s" % (k, df, "" if is_on else "!"))
            if 2.0 <= df < 6:
                late.append("cut into shot %d is %.1f frames after the beat" % (k, df))
            if is_on and prev_bi is not None and bi == prev_bi + 1:
                r += 1
            else:
                r = 1 if is_on else 0
            prev_bi = bi if is_on else None
            runs = max(runs, r)
        if cut_t and beats:
            share = on / float(len(cut_t))
            notes.append("cuts on beat (2 frames early .. 0.5 late): %d/%d (%.0f%%)" % (on, len(cut_t), 100 * share))
            if verbose_cuts:
                notes.append("cut offsets from nearest beat in frames (shot:offset, ! = off beat): " + "  ".join(rows))
            if share < 0.5 and reg not in ("luxury",):
                warns.append("only %.0f%% of cuts sit on a beat (aim 50-70%%; luxury may be freer)" % (100 * share))
            if share > 0.9 and len(cut_t) > 6:
                warns.append("%.0f%% of cuts on the beat: mechanical; move some cuts to action" % (100 * share))
        for x in late[:6]:
            warns.append(x + ": cut 0-2 frames early instead")
        if runs > 4:
            warns.append("%d cuts in a row on consecutive beats: vary density (fine inside a marked build)" % runs)
    elif mus:
        notes.append("music has no beats file: run beats.py and set music.beats to check cut timing")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--no-lutcheck", action="store_true", help="skip measuring whether LUTs convert log clips")
    a = ap.parse_args()
    try:
        plan = load(a.plan)
    except OSError as e:
        sys.exit("cannot open plan: %s" % e)
    except ValueError as e:
        sys.exit("plan is not valid JSON: %s" % e)
    base = os.path.dirname(os.path.abspath(a.plan))
    res = check_plan(plan, base, lutcheck=not a.no_lutcheck)
    fails, warns, notes = res["fails"], res["warns"], res["notes"]
    print("PLAN: %s" % (plan.get("title", os.path.basename(a.plan)) if isinstance(plan, dict) else a.plan))
    idea = (plan.get("idea") or "").strip() if isinstance(plan, dict) else ""
    print("idea: %s" % (idea or "(missing)"))
    for n in notes:
        print("  - " + n)
    for f in fails:
        print("  FAIL  " + f)
    for w in warns:
        print("  WARN  " + w)
    if not fails and not warns:
        print("  PASS  no problems found by the numbers. Now LOOK at the frames (sheets) and judge beauty.")
    elif not fails:
        print("  PASS with warnings: fix them or write down why each one is intentional.")
    sys.exit(1 if fails else (2 if (a.strict and warns) else 0))


if __name__ == "__main__":
    main()
