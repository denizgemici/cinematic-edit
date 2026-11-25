#!/usr/bin/env python3
"""selftest.py: offline end-to-end test of the cinematic-edit scripts (about 15 seconds).

Everything is generated with ffmpeg and Pillow in a temp folder; no footage and
no network are needed. It checks:

  tilt        scan.tilt_angle on a frame rotated by 0, +-1, +-2, +-3 deg with
              ffmpeg's rotate filter (centre crop, no black corners): the
              recovered change of angle must be within +-0.3 deg. Uses
              --tilt-clip (a real clip with straight lines, frame at --tilt-t)
              when given, else a generated tiled-wall picture.
  lutcheck    an identity LUT on a flat "log-like" clip FAILS, an expanding LUT passes
  beats       a 120 bpm click track is found at 120 +- 2 bpm; --bpm 120 is kept
  plan_check  a good plan passes; a broken plan (speed 0, out past the clip,
              missing file) gives clear FAIL lines, no traceback
  render      50p source, speed 0.5, a ramp, dissolves, a push, grade,
              stabilise, a still end card, a PNG overlay, music: exact frame
              count, BT.709 tags, audio length = video length; a refused render
              for the broken plan; NTSC 30000/1001 output; colour accuracy of
              the YUV->RGB->YUV path; a smooth (non-stepping) push
  qc          frame count matches, no false judder; a 25 % slowdown of 50p
              without interpolation IS reported as judder
  export_xml  built-in XML self-test plus a structural check of the real plan
  bt470bg     a BT.601-tagged clip (phones, screen recordings) renders, scans
              and passes through lutcheck without a filter error

Usage: python3 selftest.py [--keep] [--tilt-clip CLIP --tilt-t SECONDS]
Exit code 0 when everything passes.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _common import find_tool, ffprobe_json, video_stream, layout  # noqa: E402

RESULTS = []


def ok(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", name, ("  (" + detail + ")") if detail else ""), flush=True)
    return cond


def ff(*args):
    p = subprocess.run([find_tool("ffmpeg"), "-v", "error", "-y"] + list(args), stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.decode("utf-8", "replace")[-800:])
    return p.stdout


def script(name, *args):
    p = subprocess.run([sys.executable, os.path.join(HERE, name)] + list(args), stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    return p.returncode, p.stdout.decode("utf-8", "replace") + p.stderr.decode("utf-8", "replace")


def count_frames(path):
    p = subprocess.run([find_tool("ffprobe"), "-v", "error", "-count_frames", "-select_streams", "v:0",
                        "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", path], stdout=subprocess.PIPE)
    return int(p.stdout.decode().strip().split(",")[0])


def gray_frames(path, w, h):
    raw = ff("-i", path, "-vf", "scale=%d:%d:in_color_matrix=bt709:in_range=tv,format=gray" % (w, h),
             "-f", "rawvideo", "-")
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)


# --------------------------------------------------------------------------------------------
def test_tilt(tmp, clip=None, t=1.0):
    from PIL import Image, ImageDraw
    import io
    from scan import tilt_angle
    if clip and os.path.isfile(clip):
        src = clip
        seek = ["-ss", "%.3f" % t]
        label = os.path.basename(clip)
    else:
        # generated tiled wall + counter line + noise, perfectly level
        rng = np.random.default_rng(1)
        im = Image.new("L", (1920, 1080), 150)
        d = ImageDraw.Draw(im)
        for x in range(0, 1920, 120):
            d.line([(x, 0), (x, 700)], fill=110, width=3)
        for y in range(0, 700, 120):
            d.line([(0, y), (1920, y)], fill=110, width=3)
        d.rectangle([0, 700, 1920, 1080], fill=200)
        d.line([(0, 700), (1920, 700)], fill=40, width=6)
        for k in range(40):
            cx, cy, r = rng.integers(0, 1920), rng.integers(720, 1080), rng.integers(10, 60)
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=int(rng.integers(60, 230)))
        arr = np.array(im, np.float32) + rng.normal(0, 4, (1080, 1920))
        src = os.path.join(tmp, "tilt_src.png")
        Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(src)
        seek = []
        label = "generated wall"
    est = {}
    for ang in (0, 1, -1, 2, -2, 3, -3):
        vf = ("rotate=%.8f:bilinear=1,crop=iw*0.72:ih*0.72,"
              "scale=640:640:force_original_aspect_ratio=decrease:flags=area,format=gray" % np.radians(ang))
        png = ff(*(seek + ["-i", src, "-frames:v", "1", "-vf", vf, "-f", "image2pipe", "-c:v", "png", "-"]))
        g = np.array(Image.open(io.BytesIO(png)).convert("L"), np.float32)
        a, c, _ = tilt_angle(g)
        est[ang] = a
    if est[0] is None or any(v is None for v in est.values()):
        return ok("tilt: readings on %s" % label, False, str(est))
    errs = {ang: round(est[ang] - est[0] - ang, 2) for ang in est if ang}
    worst = max(abs(v) for v in errs.values())
    ok("tilt: synthetic rotations recovered within 0.3 deg on %s" % label, worst <= 0.3,
       "base %.2f, errors %s" % (est[0], errs))
    if label == "generated wall":
        ok("tilt: level picture reads level", abs(est[0]) <= 0.3, "%.2f" % est[0])


def make_media(tmp):
    A = os.path.join(tmp, "clipA_50p.mov")
    ff("-f", "lavfi", "-i", "testsrc2=s=1280x720:r=50:d=8", "-f", "lavfi", "-i", "sine=f=440:d=8:sample_rate=48000",
       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", "-preset", "veryfast",
       "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-c:a", "aac", "-shortest", A)
    LOGC = os.path.join(tmp, "clip_loglike.mov")   # flat, grey "log-like" picture
    ff("-f", "lavfi", "-i", "testsrc2=s=640x360:r=25:d=3", "-vf", "eq=contrast=0.35:brightness=0.12:saturation=0.3",
       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", LOGC)
    # 120 bpm click track (8 s) with a quiet bed
    M = os.path.join(tmp, "music.wav")
    ff("-f", "lavfi", "-i", "aevalsrc='0.8*sin(2*PI*1000*t)*exp(-60*mod(t,0.5))+0.02*sin(2*PI*110*t)':s=48000:d=12",
       "-ac", "2", M)
    from PIL import Image, ImageDraw
    logo = os.path.join(tmp, "logo.png")
    im = Image.new("RGBA", (200, 80), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse([10, 10, 190, 70], fill=(255, 255, 255, 230))
    im.save(logo)
    card = os.path.join(tmp, "card.png")
    im = Image.new("RGB", (720, 1280), (30, 28, 26))
    ImageDraw.Draw(im).rectangle([200, 560, 520, 720], fill=(220, 200, 160))
    im.save(card)
    tex = os.path.join(tmp, "texture.png")   # fine texture for the push test
    rng = np.random.default_rng(3)
    t = rng.integers(0, 255, (360, 640)).astype(np.uint8)
    Image.fromarray(t).resize((1280, 720), Image.NEAREST).convert("RGB").save(tex)
    # cube LUTs: identity and a strong contrast/saturation expansion
    def expand(r, g, b):
        m = (r + g + b) / 3.0
        return tuple(min(1.0, max(0.0, (v + 0.6 * (v - m) - 0.5) * 2.4 + 0.5)) for v in (r, g, b))

    for name, fn in (("identity.cube", lambda r, g, b: (r, g, b)), ("expand.cube", expand)):
        N = 17
        lines = ["LUT_3D_SIZE %d" % N]
        for bi in range(N):
            for gi in range(N):
                for ri in range(N):
                    lines.append("%.6f %.6f %.6f" % fn(ri / (N - 1.0), gi / (N - 1.0), bi / (N - 1.0)))
        with open(os.path.join(tmp, name), "w") as fh:
            fh.write("\n".join(lines) + "\n")
    return A, LOGC, M, logo, card, tex


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--keep", action="store_true", help="keep the temp folder")
    ap.add_argument("--tilt-clip", help="real clip with straight lines for the tilt test")
    ap.add_argument("--tilt-t", type=float, default=1.0)
    a = ap.parse_args()
    t0 = time.time()
    tmp = tempfile.mkdtemp(prefix="ce_selftest_")
    try:
        print("tilt")
        test_tilt(tmp, a.tilt_clip, a.tilt_t)
        print("media")
        A, LOGC, M, logo, card, tex = make_media(tmp)

        print("lutcheck")
        from lutcheck import check
        r1 = check(LOGC, os.path.join(tmp, "identity.cube"), use_cache=False)
        r2 = check(LOGC, os.path.join(tmp, "expand.cube"), use_cache=False)
        ok("lutcheck: identity LUT on flat clip = FAIL", r1["verdict"] == "flat", r1.get("msg", ""))
        ok("lutcheck: expanding LUT = ok", r2["verdict"] == "ok", r2.get("msg", ""))

        print("beats")
        rc, out = script("beats.py", M, "--fps", "25", "--out", os.path.join(tmp, "music"))
        bj = json.load(open(os.path.join(tmp, "music", "beats.json")))
        ok("beats: 120 bpm click found", rc == 0 and abs(bj["bpm"] - 120) <= 2.0, "bpm %s, candidates %s"
           % (bj.get("bpm"), bj.get("tempo_candidates", [])[:3]))
        rc, out = script("beats.py", M, "--fps", "25", "--bpm", "120", "--out", os.path.join(tmp, "music2"))
        bj2 = json.load(open(os.path.join(tmp, "music2", "beats.json")))
        ok("beats: --bpm 120 kept", rc == 0 and abs(bj2["bpm"] - 120) <= 0.6, "bpm %s" % bj2.get("bpm"))
        rc, out = script("beats.py", os.path.join(tmp, "missing.mp3"))
        ok("beats: missing file -> clean error", rc != 0 and "Traceback" not in out, out.strip()[:80])

        print("plan_check / render / qc / export_xml")
        plan = {
            "title": "selftest", "idea": "A test pattern moves, slows down and ends on a card.",
            "register": "brand", "fps": 25, "size": [360, 640],
            "music": {"file": "music/music.wav", "start": 0.5, "fade_out": 0.5, "beats": "music/beats.json"},
            "shots": [
                {"src": A, "in": 1.0, "out": 2.0, "speed": 0.5, "role": "hook", "reason": "conform 50p", "sound_db": None},
                {"src": A, "in": 2.5, "out": 3.7, "ramp": [[0, 1], [0.4, 1], [0.5, 2], [0.9, 2], [1.0, 1], [1.2, 1]],
                 "role": "hero", "reason": "ramp", "transition": "dissolve:6", "grade": {"exposure": 0.2, "temp": 0.2,
                                                                                      "contrast": 1.05, "saturation": 1.05}},
                {"src": A, "in": 4.5, "out": 6.0, "push": [1.0, 1.05], "stabilize": True, "role": "build",
                 "reason": "push + stabilise", "sound_db": -12},
                {"src": card, "duration": 1.6, "transition": "dissolve:4", "role": "end-card", "reason": "end card"},
            ],
            "overlays": [{"png": logo, "start": 4.0, "end": 6.5, "fade": 6, "x": 80, "y": 500}],
        }
        pp = os.path.join(tmp, "plan.json")
        json.dump(plan, open(pp, "w"))
        rc, out = script("plan_check.py", pp)
        ok("plan_check: good plan passes (exit 0)", rc == 0, out.strip().splitlines()[-1][:120] if out.strip() else "")
        bad = json.loads(json.dumps(plan))
        bad["shots"][0]["speed"] = 0
        bad["shots"][2]["out"] = 99.0
        bad["shots"].append({"src": os.path.join(tmp, "nope.mov"), "in": 0, "out": 1})
        bp = os.path.join(tmp, "bad.json")
        json.dump(bad, open(bp, "w"))
        rc, out = script("plan_check.py", bp)
        ok("plan_check: broken plan FAILs cleanly", rc == 1 and "Traceback" not in out and "speed" in out
           and "source not found" in out, "%d FAIL lines" % out.count("FAIL"))
        bad2 = json.loads(json.dumps(plan))
        bad2["shots"][2]["out"] = 99.0
        bp2 = os.path.join(tmp, "bad2.json")
        json.dump(bad2, open(bp2, "w"))
        rc, out = script("render.py", bp2, "--out", os.path.join(tmp, "bad.mp4"))
        ok("render: refuses a FAIL plan", rc != 0 and "plan check FAILED" in out and not os.path.exists(
            os.path.join(tmp, "bad.mp4")))

        film = os.path.join(tmp, "film.mp4")
        t1 = time.time()
        rc, out = script("render.py", pp, "--out", film)
        lay = layout(plan["shots"], 25)
        ok("render: runs", rc == 0, "%.0fs" % (time.time() - t1) if rc == 0 else out[-600:])
        if rc == 0:
            nf = count_frames(film)
            info = ffprobe_json(film)
            vs = video_stream(info)
            au = [s for s in info["streams"] if s["codec_type"] == "audio"]
            ok("render: exact frame count", nf == lay["total"], "%d frames, plan %d" % (nf, lay["total"]))
            ok("render: BT.709 tags", vs.get("color_primaries") == vs.get("color_transfer") == vs.get("color_space") == "bt709")
            ok("render: audio length = video length", au and abs(float(au[0]["duration"]) - nf / 25.0) <= 0.045,
               "audio %s s, video %.3f s" % (au[0]["duration"] if au else None, nf / 25.0))
            rc, out = script("qc.py", film, "--out", os.path.join(tmp, "qc"), "--plan", pp)
            q = json.load(open(os.path.join(tmp, "qc", "qc.json")))
            ok("qc: no hard problems, frame count matches", rc == 0 and q["frames"] == lay["total"],
               "; ".join(q["hard"])[:200])
            ok("qc: no false judder", not q["judder"], str(q["judder"]))
            ok("qc: sheets written", os.path.exists(os.path.join(tmp, "qc", "contact.png")) and
               os.path.exists(os.path.join(tmp, "qc", "cuts.png")) and
               os.path.exists(os.path.join(tmp, "qc", "slow_shot01.png")))
            rc, out = script("export_xml.py", pp, "--out", os.path.join(tmp, "t.xml"))
            ok("export_xml: plan exported, structure valid", rc == 0 and "XML self-check" not in out, out.strip()[-160:])
        rc, out = script("export_xml.py", "--selftest")
        ok("export_xml: built-in self-test", rc == 0, out.strip().splitlines()[-1] if out.strip() else "")

        # judder must be caught: 50p at 25 % without interpolation repeats every frame twice
        jp = {"title": "judder", "idea": "A test pattern slowed too far without frames.", "fps": 25, "size": [320, 180],
              "shots": [{"src": A, "in": 1.0, "out": 2.0, "speed": 0.25, "reason": "too slow"}]}
        jpp = os.path.join(tmp, "judder.json")
        json.dump(jp, open(jpp, "w"))
        rc, out = script("render.py", jpp, "--out", os.path.join(tmp, "judder.mp4"))
        rc2, out2 = script("qc.py", os.path.join(tmp, "judder.mp4"), "--out", os.path.join(tmp, "qcj"), "--plan", jpp)
        qj = json.load(open(os.path.join(tmp, "qcj", "qc.json"))) if os.path.exists(os.path.join(tmp, "qcj", "qc.json")) else {}
        ok("qc: 25% slowdown of 50p without interpolation = judder", rc == 0 and bool(qj.get("judder")),
           str(qj.get("judder")))

        # BT.601-tagged source (bt470bg: phones, screen recordings, web H.264) must not crash
        B601 = os.path.join(tmp, "clip_bt470bg.mp4")
        ff("-f", "lavfi", "-i", "smptebars=s=640x360:r=25:d=3", "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-colorspace", "bt470bg", "-color_primaries", "bt470bg", "-color_trc", "smpte170m", B601)
        tag = video_stream(ffprobe_json(B601)).get("color_space")
        bp6 = os.path.join(tmp, "bt470bg.json")
        json.dump({"title": "bt470bg", "idea": "A BT.601 tagged phone clip renders like any other.", "fps": 25,
                   "size": [320, 180], "shots": [{"src": B601, "in": 0.5, "out": 1.5, "reason": "bt470bg"}]},
                  open(bp6, "w"))
        rc, out = script("render.py", bp6, "--out", os.path.join(tmp, "bt470bg_out.mp4"))
        rc2, out2 = script("scan.py", B601, "--out", os.path.join(tmp, "scan601"), "--no-strip")
        r3 = check(B601, os.path.join(tmp, "expand.cube"), use_cache=False)
        ok("bt470bg-tagged source: render, scan and lutcheck run", tag == "bt470bg" and rc == 0 and rc2 == 0
           and "ERROR" not in out2 and r3["verdict"] != "error",
           "tag %s; render %d; scan %d; lutcheck %s" % (tag, rc, rc2, r3.get("verdict")))

        # NTSC
        np_ = {"title": "ntsc", "idea": "One test shot at an exact NTSC frame rate.", "fps": "30000/1001",
               "size": [320, 180], "shots": [{"src": A, "in": 0.5, "out": 1.5, "reason": "ntsc"}]}
        npp = os.path.join(tmp, "ntsc.json")
        json.dump(np_, open(npp, "w"))
        rc, out = script("render.py", npp, "--out", os.path.join(tmp, "ntsc.mp4"))
        if ok("render: NTSC plan runs", rc == 0, out[-300:] if rc else ""):
            vs = video_stream(ffprobe_json(os.path.join(tmp, "ntsc.mp4")))
            nf = count_frames(os.path.join(tmp, "ntsc.mp4"))
            ok("render: 30000/1001 kept exactly, 30 frames", vs["r_frame_rate"] == "30000/1001" and nf == 30,
               "%s, %d frames" % (vs["r_frame_rate"], nf))

        # colour path: a plain shot must come out with the source's colours (BT.709 both ways)
        cp = {"title": "colour", "idea": "A plain shot keeps its exact colours through the pipeline.", "fps": 50,
              "size": [640, 360], "shots": [{"src": A, "in": 2.0, "out": 3.0, "reason": "colour"}]}
        cpp = os.path.join(tmp, "colour.json")
        json.dump(cp, open(cpp, "w"))
        rc, out = script("render.py", cpp, "--out", os.path.join(tmp, "colour.mp4"))
        if rc == 0:
            def rgb_at(path, ss):
                raw = ff("-ss", "%.3f" % ss, "-i", path, "-frames:v", "1", "-vf",
                         "scale=320:180:in_color_matrix=bt709:in_range=tv,format=rgb24", "-f", "rawvideo", "-")
                return np.frombuffer(raw, np.uint8).reshape(180, 320, 3).astype(np.float32)
            d = np.abs(rgb_at(os.path.join(tmp, "colour.mp4"), 0.5) - rgb_at(A, 2.5)).mean(axis=(0, 1))
            ok("render: colours preserved (mean abs RGB error < 3)", d.max() < 3.0, "per channel %s" % np.round(d, 2))
        else:
            ok("render: colour plan runs", False, out[-300:])

        # push smoothness: every frame must move (no 2-px stepping, no repeated frames)
        pp2 = {"title": "push", "idea": "A slow push on fine texture must glide without steps.", "fps": 25,
               "size": [640, 360], "shots": [{"src": tex, "duration": 4.0, "push": [1.0, 1.06], "reason": "push"}]}
        ppp = os.path.join(tmp, "push.json")
        json.dump(pp2, open(ppp, "w"))
        rc, out = script("render.py", ppp, "--out", os.path.join(tmp, "push.mp4"))
        if rc == 0:
            g = gray_frames(os.path.join(tmp, "push.mp4"), 640, 360)
            dd = np.array([np.abs(g[i] - g[i - 1]).mean() for i in range(1, len(g))])
            mid = dd[10:-10]
            still = int(np.sum(mid < 0.15 * np.median(mid)))
            cv = float(np.std(np.diff(mid)) / (np.mean(mid) + 1e-6))
            ok("render: push glides (no repeated/stepped frames)", still == 0 and cv < 0.35,
               "frames without motion %d, jerk %.2f" % (still, cv))
        else:
            ok("render: push plan runs", False, out[-300:])
    finally:
        if a.keep:
            print("kept:", tmp)
        else:
            shutil.rmtree(tmp, ignore_errors=True)
    bad = [r for r in RESULTS if not r[1]]
    print("\n%d/%d checks passed in %.0f s" % (len(RESULTS) - len(bad), len(RESULTS), time.time() - t0))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
