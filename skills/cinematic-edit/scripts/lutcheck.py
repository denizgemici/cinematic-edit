#!/usr/bin/env python3
"""lutcheck.py: does this LUT really convert this log clip to a display picture?

A log clip is flat: lifted blacks, compressed highlights, little colour. The
camera maker's official log-to-Rec.709 transform must expand the tonal range
and the colour a lot. A wrong LUT (a look LUT, a "Rec709 flat" profile LUT)
leaves the picture flat and every later step - judging
exposure, grading, the critic - is done on log. This happened in a field test:
every tool said PASS and the film went out as ungraded log.

For each clip it measures 3 frames WITHOUT and WITH the LUT:
  luma p2 / p50 / p98 (0-255) and mean chroma (max(RGB) - min(RGB))
and fails when the LUT barely changes the picture:
  range ratio  (p98-p2 after / before)  < 1.20   and
  chroma ratio (after / before)          < 1.60   and
  mid-tone shift |p50 after - before|    < 12
It warns when the converted picture still measures like log (p2 > 20 with a
range under 110 and chroma under 30), which can also be a genuinely foggy scene.

It only catches a LUT that does NOT convert. Another camera's official log
LUT usually expands the picture too and passes: confirm yourself that the LUT
matches the camera and curve that probe.py reported.

Results are cached (clip size+mtime, LUT content) in the temp folder, so
plan_check.py can call it on every run.

Usage:
  python3 lutcheck.py CLIP [CLIP ...] --lut official.cube [--json out.json]
Exit code 1 when a LUT does not convert a clip. Read-only; no network.
"""
import argparse
import hashlib
import json
import os
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (luma, ffprobe_json, video_stream, read_rgb_frame, lut_filter, write_json)  # noqa: E402

RANGE_MIN = 1.20
CHROMA_MIN = 1.60
MID_SHIFT = 12.0
_CACHE = os.path.join(tempfile.gettempdir(), "ce_lutcheck_cache.json")


def _stats(rgb):
    y = luma(rgb.astype(np.float32))
    ch = (rgb.max(axis=2).astype(np.float32) - rgb.min(axis=2).astype(np.float32)).mean()
    return [float(np.percentile(y, 2)), float(np.percentile(y, 50)), float(np.percentile(y, 98)), float(ch)]


def _key(src, lut):
    st = os.stat(src)
    with open(lut, "rb") as fh:
        lh = hashlib.sha1(fh.read()).hexdigest()
    return hashlib.sha1(("%s|%d|%d|%s|v1" % (os.path.abspath(src), st.st_size, int(st.st_mtime), lh)).encode()).hexdigest()


def _load_cache():
    try:
        with open(_CACHE, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def check(src, lut, use_cache=True):
    """Measure src without/with lut. Returns a dict with 'verdict' ok | flat | error."""
    if not os.path.isfile(src):
        return {"verdict": "error", "msg": "clip not found: %s" % src}
    if not os.path.isfile(lut):
        return {"verdict": "error", "msg": "LUT not found: %s" % lut}
    key = _key(src, lut)
    cache = _load_cache() if use_cache else {}
    if key in cache:
        return cache[key]
    try:
        info = ffprobe_json(src)
        vs = video_stream(info)
        dur = float(info.get("format", {}).get("duration") or 0)
    except Exception as e:
        return {"verdict": "error", "msg": str(e)[:200]}
    lf = lut_filter(lut)
    before, after = [], []
    for frac in (0.25, 0.5, 0.75):
        t = dur * frac
        a = read_rgb_frame(src, t, width=320, vs=vs)
        b = read_rgb_frame(src, t, width=320, pre_vf=lf, vs=vs)
        if a is None or b is None:
            continue
        before.append(_stats(a))
        after.append(_stats(b))
    if not before:
        return {"verdict": "error", "msg": "could not decode frames"}
    B = np.median(np.array(before), axis=0)
    A = np.median(np.array(after), axis=0)
    rr = (A[2] - A[0]) / max(B[2] - B[0], 1.0)
    cr = A[3] / max(B[3], 1.0)
    shift = A[1] - B[1]
    res = {"before": {"p2": round(B[0], 1), "p50": round(B[1], 1), "p98": round(B[2], 1), "chroma": round(B[3], 1)},
           "after": {"p2": round(A[0], 1), "p50": round(A[1], 1), "p98": round(A[2], 1), "chroma": round(A[3], 1)},
           "range_ratio": round(float(rr), 2), "chroma_ratio": round(float(cr), 2), "mid_shift": round(float(shift), 1)}
    if rr < RANGE_MIN and cr < CHROMA_MIN and abs(shift) < MID_SHIFT:
        res["verdict"] = "flat"
        res["msg"] = ("LUT does not convert this log: range x%.2f, chroma x%.2f, mid-tone %+.0f "
                      "(an official log-to-709 transform expands both a lot). Wrong LUT for this camera/curve?"
                      % (rr, cr, shift))
    else:
        res["verdict"] = "ok"
        res["msg"] = "LUT converts: range x%.2f, chroma x%.2f, mid-tone %+.0f" % (rr, cr, shift)
        if A[0] > 20 and (A[2] - A[0]) < 110 and A[3] < 30:
            res["still_flat"] = True
            res["msg"] += "; but the result still measures flat (p2 %.0f, range %.0f, chroma %.0f): check by eye" % (
                A[0], A[2] - A[0], A[3])
    if use_cache:
        cache = _load_cache()
        cache[key] = res
        try:
            with open(_CACHE, "w", encoding="utf-8") as fh:
                json.dump(cache, fh)
        except OSError:
            pass
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("clips", nargs="+")
    ap.add_argument("--lut", required=True, help=".cube file to test")
    ap.add_argument("--json", help="write results to this JSON file")
    ap.add_argument("--no-cache", action="store_true")
    a = ap.parse_args()
    if not os.path.isfile(a.lut):
        sys.exit("LUT not found: %s" % a.lut)
    out, bad = {}, 0
    for c in a.clips:
        r = check(c, a.lut, use_cache=not a.no_cache)
        out[c] = r
        tag = {"ok": "OK  ", "flat": "FAIL", "error": "ERR "}[r["verdict"]]
        bad += r["verdict"] != "ok"
        print("%s %s: %s" % (tag, os.path.basename(c), r.get("msg")))
        if "before" in r:
            print("       without LUT p2/p50/p98 %s/%s/%s chroma %s  ->  with LUT %s/%s/%s chroma %s" % (
                r["before"]["p2"], r["before"]["p50"], r["before"]["p98"], r["before"]["chroma"],
                r["after"]["p2"], r["after"]["p50"], r["after"]["p98"], r["after"]["chroma"]))
    if a.json:
        write_json(a.json, out)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
