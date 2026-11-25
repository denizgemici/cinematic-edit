#!/usr/bin/env python3
"""export_xml.py: hand the edit to a human editor/colourist as a timeline.

EXPERIMENTAL: not yet import-tested in Premiere Pro / DaVinci Resolve.

Writes a Final Cut Pro 7 XML (xmeml v4), the interchange format Premiere Pro
and DaVinci Resolve import with File > Import. NOT IMPORT-TESTED: this file
was written from the FCP7 XML specification and field notes, but this version
has not been imported into Premiere or Resolve by the tool's authors. Import
it, check the first slowed clip, the first vertical clip and the first
dissolve against the rendered film, and fix by hand if something differs.

What is written
  - every shot links to the ORIGINAL camera file at its real in/out
  - speed: a Time Remap effect with the constant speed. In FCP7 XML a clip's
    <in>/<out> are counted in the clip's timebase on the SPEED-ADJUSTED source:
    source second t at 50 % speed is frame t*fps/0.5, and out - in always
    equals end - start (the length on the timeline). Premiere and Resolve read
    and write slowed clips this way.
  - ramps: FCP7 keyframed time remap is not reliably interchanged, so a ramp
    is written as its AVERAGE constant speed (same in/out and length) with a
    "RAMP" marker listing the keys; rebuild the ramp in the NLE (a warning is
    printed for each ramped shot)
  - Basic Motion: scale for cover-fit (100 = native pixels) x reframe zoom x
    straighten zoom x push start; rotation for vertical files whose rotation
    flag the NLE ignores (Premiere does not apply the flag of most camera MOV/
    MP4 files) plus the extra 'rotate' and 'straighten'; center from 'reframe'
    (offset / source width and / source height, as Premiere reads it)
  - dissolves as <transitionitem> (Cross Dissolve, centred on the cut, the
    same frames render.py uses); clips abut at the middle of the dissolve
  - a marker at each clip's in point with role, reason and the finishing
    values (LUT, grade, push, stabilise) that are done in the NLE on purpose
  - music on audio tracks 1+2 as a linked stereo pair; designed PNG overlays
    on video track 2
  - exact NTSC rates (29.97 = timebase 30 + ntsc TRUE)

Usage:
  python3 export_xml.py edit_plan.json --out timeline.xml [--nle-applies-rotation]
                        [--flip-rotation] [--ascii-links DIR]
  python3 export_xml.py --selftest

--nle-applies-rotation  the NLE already rotates flagged files (do not add rotation)
--flip-rotation         write rotation with the opposite sign (if vertical clips land
                        upside down after import)
--ascii-links DIR       Premiere's XML import can silently fail on non-ASCII paths
                        (e.g. "Tüm", "EYLÜL"): make ASCII-named symlinks in DIR and
                        link those instead
No network.
"""
import argparse
import json
import math
import os
import re
import sys
from urllib.parse import quote
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (ffprobe_json, video_stream, rational, rotation_of, shot_timeline_seconds,  # noqa: E402
                     is_still, parse_fps, layout)


def pathurl(p):
    p = os.path.abspath(p).replace("\\", "/")
    if not p.startswith("/"):
        p = "/" + p  # Windows drive letters
    return "file://localhost" + quote(p, safe="/:")


def rate_xml(fps):
    """<rate>: integer timebase + NTSC flag (29.97 -> 30 TRUE, 25 -> 25 FALSE)."""
    fr = parse_fps(fps)
    ntsc = fr.denominator == 1001
    tb = int(round(float(fr) * (1.001 if ntsc else 1.0)))
    return "<rate><timebase>%d</timebase><ntsc>%s</ntsc></rate>" % (tb, "TRUE" if ntsc else "FALSE")


def media_info(path):
    """What the XML needs from a file (ffprobe), or a picture's size."""
    if is_still({"src": path}):
        from PIL import Image
        with Image.open(path) as im:
            return {"w": im.size[0], "h": im.size[1], "fps": None, "dur": None, "audio": False, "rot": 0,
                    "still": True}
    info = ffprobe_json(path)
    vs = video_stream(info)
    aud = [x for x in info["streams"] if x.get("codec_type") == "audio"]
    return {"w": int(vs["width"]) if vs else 0, "h": int(vs["height"]) if vs else 0,
            "fps": (rational(vs.get("r_frame_rate")) if vs else None),
            "dur": float(info["format"].get("duration", 0)), "audio": bool(aud),
            "channels": int(aud[0].get("channels", 2)) if aud else 0,
            "rate": int(aud[0].get("sample_rate", 48000)) if aud else 48000,
            "rot": rotation_of(vs) if vs else 0, "still": False, "video": vs is not None}


def _param(pid, name, value, vmin=None, vmax=None):
    lim = ""
    if vmin is not None:
        lim = "<valuemin>%s</valuemin><valuemax>%s</valuemax>" % (vmin, vmax)
    return "<parameter><parameterid>%s</parameterid><name>%s</name>%s<value>%s</value></parameter>" % (pid, name, lim, value)


def basic_motion(shot, m, W, H, nle_rotates=False, flip=False):
    """Basic Motion filter (scale %, rotation deg, center) reproducing render.py's framing."""
    sw, sh = m["w"], m["h"]                      # stored frame
    rot_cw = 0
    if not nle_rotates and m.get("rot"):
        rot_cw = -int(m["rot"])                  # ffprobe -90 = needs 90 deg clockwise for display
    rot_cw += int(shot.get("rotate", 0) or 0)
    rot_cw = ((rot_cw + 180) % 360) - 180
    dw, dh = sw, sh                              # displayed frame: flag (by us or the NLE) + extra rotate
    if m.get("rot") in (90, -90, 270, -270):
        dw, dh = dh, dw
    if int(shot.get("rotate", 0) or 0) % 180 == 90:
        dw, dh = dh, dw
    ang = float(shot.get("straighten", 0.0))
    k = 1.0
    if abs(ang) > 0.01:
        r = math.radians(abs(ang))
        k = math.cos(r) + math.sin(r) * max(dw, dh) / float(min(dw, dh))
    rf = shot.get("reframe") or {}
    z = max(1.0, float(rf.get("zoom", 1.0)))
    push = shot.get("push")
    p0 = float(push[0]) if push else 1.0
    s = max(W / float(dw), H / float(dh)) * k * z * p0
    Sw, Sh = dw * s, dh * s                      # displayed size on the sequence
    offx = (0.5 - float(rf.get("x", 0.5))) * Sw
    offy = (0.5 - float(rf.get("y", 0.5))) * Sh
    offx = max(-(Sw - W) / 2.0, min((Sw - W) / 2.0, offx))
    offy = max(-(Sh - H) / 2.0, min((Sh - H) / 2.0, offy))
    total_rot = rot_cw + ang                     # straighten: positive = clockwise, as render.py
    # FCP7 Basic Motion rotation is counter-clockwise positive; Premiere maps it to its own
    # clockwise-positive control. Use --flip-rotation if an import shows the opposite.
    xml_rot = (total_rot if flip else -total_rot)
    p = [_param("scale", "Scale", "%.4f" % (s * 100), 0, 1000),
         _param("rotation", "Rotation", "%.4f" % xml_rot, -8640, 8640),
         "<parameter><parameterid>center</parameterid><name>Center</name><value><horiz>%.6f</horiz>"
         "<vert>%.6f</vert></value></parameter>" % (offx / float(sw), offy / float(sh)),
         "<parameter><parameterid>centerOffset</parameterid><name>Anchor Point</name><value><horiz>0</horiz>"
         "<vert>0</vert></value></parameter>"]
    return ("<filter><effect><name>Basic Motion</name><effectid>basic</effectid><effectcategory>motion"
            "</effectcategory><effecttype>motion</effecttype><mediatype>video</mediatype>%s</effect></filter>"
            % "".join(p)), s, total_rot


def time_remap(speed):
    return ("<filter><effect><name>Time Remap</name><effectid>timeremap</effectid><effectcategory>motion</effectcategory>"
            "<effecttype>motion</effecttype><mediatype>video</mediatype>"
            + _param("variablespeed", "variablespeed", "0", 0, 1)
            + _param("speed", "speed", "%.4f" % (speed * 100), -100000, 100000)
            + _param("reverse", "reverse", "FALSE")
            + _param("frameblending", "frameblending", "FALSE")
            + "</effect></filter>")


def build_xml(plan, P, minfo, nle_rotates=False, flip=False, log=print):
    """Pure builder: plan + media info dict (path -> media_info) -> XML text."""
    fps = parse_fps(plan.get("fps", 25))
    fpsf = float(fps)
    rx = rate_xml(fps)
    W, H = plan.get("size", [1080, 1920])
    shots = plan["shots"]
    lay = layout(shots, fps)
    files_done, fid = set(), {}

    def file_xml(path, m):
        if path not in fid:
            fid[path] = "file-%d" % (len(fid) + 1)
        if path in files_done:
            return '<file id="%s"/>' % fid[path]
        files_done.add(path)
        if m.get("still"):
            frate, fdur = rx, 1
        else:
            frate = rate_xml(m["fps"] or fpsf) if m.get("video", True) else rx
            fdur = int(round((m["dur"] or 0) * float(parse_fps(m["fps"] or fpsf)))) if m.get("video", True) \
                else int(round((m["dur"] or 0) * fpsf))
        media = ""
        if m.get("video", True):
            media += ("<video><samplecharacteristics>%s<width>%s</width><height>%s</height>"
                      "<pixelaspectratio>square</pixelaspectratio></samplecharacteristics></video>" % (frate, m["w"], m["h"]))
        if m.get("audio"):
            media += ("<audio><samplecharacteristics><depth>16</depth><samplerate>%d</samplerate></samplecharacteristics>"
                      "<channelcount>%d</channelcount></audio>" % (m.get("rate", 48000), max(1, m.get("channels", 2))))
        return ('<file id="%s"><name>%s</name><pathurl>%s</pathurl>%s<duration>%d</duration><media>%s</media></file>'
                % (fid[path], escape(os.path.basename(path)), escape(pathurl(path)), frate, fdur, media))

    n = len(shots)
    # clip boundaries on the timeline: abut at the middle of each dissolve
    bounds = []
    for i in range(n):
        st = lay["starts"][i] + (lay["dissolves"][i] // 2 if i > 0 else 0)
        bounds.append(st)
    bounds.append(lay["total"])
    vitems, warn = [], []
    for i, s in enumerate(shots):
        src = P(s["src"])
        m = minfo[src]
        start, end = bounds[i], bounds[i + 1]
        head = start - lay["starts"][i]           # frames of the shot hidden under the incoming dissolve
        if is_still(s):
            speed, cin = 1.0, head
            cdur = max(end - start + head + 1, int(round(float(s["duration"]) * fpsf)) + 1)
        else:
            if s.get("ramp"):
                speed = (float(s["out"]) - float(s["in"])) / shot_timeline_seconds(s)
                warn.append("shot %d: ramp written as constant %.1f%% speed (keys in the RAMP marker): rebuild the ramp "
                            "in the NLE" % (i + 1, speed * 100))
            else:
                speed = float(s.get("speed", 1.0))
            # speed-adjusted source frames in the clip (= sequence) timebase
            cin = int(round(float(s["in"]) * fpsf / speed)) + head
            cdur = int(round(m["dur"] * fpsf / speed))
        cout = cin + (end - start)
        motion, sc, rot = basic_motion(s, m, W, H, nle_rotates, flip)
        note = "%s | %s" % (s.get("role", ""), s.get("reason", ""))
        extra = []
        for k in ("lut", "grade", "push", "stabilize", "straighten", "reframe", "rotate", "interpolate", "sound_db"):
            if s.get(k) not in (None, 0, [], {}, False):
                extra.append("%s=%s" % (k, json.dumps(s[k], ensure_ascii=False)))
        if s.get("ramp"):
            extra.append("RAMP keys [source s, slowdown] = %s (written as constant average speed)" % json.dumps(s["ramp"]))
        if extra:
            note += " | " + "; ".join(extra)
        effects = motion + (time_remap(speed) if abs(speed - 1.0) > 1e-6 else "")
        still_tag = "<stillframe>TRUE</stillframe>" if is_still(s) else ""
        vitems.append(
            '<clipitem id="clipitem-%d"><name>%s</name><enabled>TRUE</enabled><duration>%d</duration>%s'
            '<start>%d</start><end>%d</end><in>%d</in><out>%d</out>%s%s%s'
            '<marker><name>%02d %s</name><comment>%s</comment><in>%d</in><out>-1</out></marker></clipitem>'
            % (i + 1, escape(os.path.basename(src)), cdur, rx, start, end, cin, cout, still_tag,
               file_xml(src, m), effects, i + 1, escape(s.get("role", "")), escape(note), cin))
        # dissolve INTO this shot: a transition centred on the cut
        d = lay["dissolves"][i]
        if i > 0 and d > 0:
            ts = lay["starts"][i]
            vitems.insert(len(vitems) - 1,
                          '<transitionitem><start>%d</start><end>%d</end><alignment>center</alignment>%s'
                          '<effect><name>Cross Dissolve</name><effectid>Cross Dissolve</effectid>'
                          '<effectcategory>Dissolve</effectcategory><effecttype>transition</effecttype>'
                          '<mediatype>video</mediatype><wipecode>0</wipecode><wipeaccuracy>100</wipeaccuracy>'
                          '<startratio>0</startratio><endratio>1</endratio><reverse>FALSE</reverse></effect>'
                          '</transitionitem>' % (ts, ts + d, rx))
    # overlays on video track 2
    oitems = []
    for j, o in enumerate(plan.get("overlays") or [], 1):
        p = P(o["png"])
        m = minfo[p]
        st, en = int(round(float(o["start"]) * fpsf)), min(lay["total"], int(round(float(o["end"]) * fpsf)))
        if en <= st:
            continue
        oitems.append('<clipitem id="overlay-%d"><name>%s</name><enabled>TRUE</enabled><duration>%d</duration>%s'
                      '<start>%d</start><end>%d</end><in>0</in><out>%d</out><stillframe>TRUE</stillframe>%s'
                      '<marker><name>overlay</name><comment>%s</comment><in>0</in><out>-1</out></marker></clipitem>'
                      % (j, escape(os.path.basename(p)), en - st + 1, rx, st, en, en - st, file_xml(p, m),
                         escape("designed PNG; opacity fade %s frames; x=%s y=%s scale=%s opacity=%s"
                                % (o.get("fade", 0), o.get("x", "centre"), o.get("y", "centre"),
                                   o.get("scale", "native"), o.get("opacity", 1)))))
    # music: stereo pair on audio tracks 1 and 2, linked
    atracks = ["", ""]
    mus = plan.get("music") or {}
    if mus.get("file"):
        mp = P(mus["file"])
        m = minfo[mp]
        m_in = int(round(float(mus.get("start", 0)) * fpsf))
        mdur = int(round((m["dur"] or 0) * fpsf))
        total = lay["total"]
        for ch in (1, 2):
            links = "".join('<link><linkclipref>music-%d</linkclipref><mediatype>audio</mediatype>'
                            '<trackindex>%d</trackindex><clipindex>1</clipindex><groupindex>1</groupindex></link>'
                            % (c, c) for c in (1, 2))
            atracks[ch - 1] = (
                '<clipitem id="music-%d"><name>%s</name><enabled>TRUE</enabled><duration>%d</duration>%s'
                '<start>0</start><end>%d</end><in>%d</in><out>%d</out>%s'
                '<sourcetrack><mediatype>audio</mediatype><trackindex>%d</trackindex></sourcetrack>%s</clipitem>'
                % (ch, escape(os.path.basename(mp)), mdur, rx, total, m_in, m_in + total,
                   file_xml(mp, m), ch, links))
    vtracks = "<track>%s</track>" % "".join(vitems)
    if oitems:
        vtracks += "<track>%s</track>" % "".join(oitems)
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n'
           '<!-- cinematic-edit export_xml.py: experimental, not yet import-tested in Premiere Pro / '
           'DaVinci Resolve. Check slowed, vertical and dissolved clips against the render. -->'
           '<xmeml version="4"><sequence id="sequence-1">'
           '<name>%s</name><duration>%d</duration>%s<media><video><format><samplecharacteristics>%s'
           '<width>%d</width><height>%d</height><pixelaspectratio>square</pixelaspectratio>'
           '<fielddominance>none</fielddominance></samplecharacteristics></format>%s</video>'
           '<audio><numOutputChannels>2</numOutputChannels><track>%s</track><track>%s</track></audio></media>'
           '</sequence></xmeml>\n'
           % (escape(plan.get("title", "cinematic-edit")), lay["total"], rx, rx, W, H, vtracks, atracks[0], atracks[1]))
    for w in warn:
        log("  ! " + w)
    return xml


def validate_xml(xml, plan, fps):
    """Structural self-check of an xmeml string. Returns list of problems (empty = fine)."""
    import xml.etree.ElementTree as ET
    probs = []
    root = ET.fromstring(xml.split("\n", 2)[2] if xml.startswith("<?xml") else xml)
    seq = root.find("sequence")
    lay = layout(plan["shots"], fps)
    if int(seq.find("duration").text) != lay["total"]:
        probs.append("sequence duration %s != %d" % (seq.find("duration").text, lay["total"]))
    track = seq.find("media/video/track")
    clips = track.findall("clipitem")
    if len(clips) != len(plan["shots"]):
        probs.append("%d clipitems for %d shots" % (len(clips), len(plan["shots"])))
    prev_end = 0
    for c in clips:
        st, en = int(c.find("start").text), int(c.find("end").text)
        i, o = int(c.find("in").text), int(c.find("out").text)
        if st != prev_end:
            probs.append("%s starts at %d, previous ended at %d (gap/overlap)" % (c.get("id"), st, prev_end))
        if o - i != en - st:
            probs.append("%s: out-in %d != end-start %d" % (c.get("id"), o - i, en - st))
        if i < 0:
            probs.append("%s: negative in" % c.get("id"))
        mk = c.find("marker/in")
        if mk is None or int(mk.text) != i:
            probs.append("%s: marker not at the clip's in point" % c.get("id"))
        prev_end = en
    if prev_end != lay["total"]:
        probs.append("last clip ends at %d, film is %d frames" % (prev_end, lay["total"]))
    trs = track.findall("transitionitem")
    if len(trs) != sum(1 for d in lay["dissolves"] if d):
        probs.append("%d transitions for %d dissolves" % (len(trs), sum(1 for d in lay["dissolves"] if d)))
    return probs


def selftest():
    """Tiny offline test of the builder with invented media (no files needed)."""
    plan = {"title": "selftest", "fps": "30000/1001", "size": [1080, 1920],
            "music": {"file": "/m/music.wav", "start": 2.0},
            "overlays": [{"png": "/m/logo.png", "start": 3.0, "end": 5.0, "fade": 8}],
            "shots": [{"src": "/m/a.mov", "in": 1.0, "out": 2.0, "speed": 0.5, "role": "hook", "reason": "r"},
                      {"src": "/m/b.mov", "in": 3.0, "out": 4.5, "transition": "dissolve:10", "straighten": 1.5,
                       "reframe": {"x": 0.4, "y": 0.5, "zoom": 1.1}},
                      {"src": "/m/a.mov", "in": 5.0, "out": 6.0, "ramp": [[0, 1], [0.5, 2], [1.0, 1]]},
                      {"src": "/m/card.png", "duration": 2.0, "transition": "dissolve:6"}]}
    minfo = {"/m/a.mov": {"w": 3840, "h": 2160, "fps": 59.94, "dur": 10.0, "audio": True, "channels": 2,
                          "rate": 48000, "rot": -90, "still": False, "video": True},
             "/m/b.mov": {"w": 3840, "h": 2160, "fps": 29.97, "dur": 10.0, "audio": False, "rot": 0,
                          "still": False, "video": True},
             "/m/card.png": {"w": 1080, "h": 1920, "still": True, "rot": 0},
             "/m/logo.png": {"w": 400, "h": 200, "still": True, "rot": 0},
             "/m/music.wav": {"w": 0, "h": 0, "fps": None, "dur": 60.0, "audio": True, "channels": 2,
                              "rate": 48000, "rot": 0, "still": False, "video": False}}
    xml = build_xml(plan, lambda p: p, minfo, log=lambda *_: None)
    probs = validate_xml(xml, plan, plan["fps"])
    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml.split("\n", 2)[2])
    c1 = root.find("sequence/media/video/track/clipitem")
    # 1.0 s at 50 % on 29.97: in = 1.0 * 29.97 / 0.5 = 59.94 -> 60
    if int(c1.find("in").text) != 60:
        probs.append("speed-adjusted in: expected 60, got %s" % c1.find("in").text)
    if "<ntsc>TRUE</ntsc><timebase>" in xml or "<timebase>30</timebase><ntsc>TRUE</ntsc>" not in xml:
        probs.append("NTSC rate not written as timebase 30 + ntsc TRUE")
    if xml.count('<clipitem id="music-') != 2:
        probs.append("music is not a stereo pair")
    for p in probs:
        print("  FAIL " + p)
    print("export_xml selftest: %s" % ("PASS" if not probs else "FAIL"))
    return not probs


def ascii_link(path, d, made):
    if all(ord(ch) < 128 for ch in path):
        return path
    if path in made:
        return made[path]
    os.makedirs(d, exist_ok=True)
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", os.path.basename(path).encode("ascii", "ignore").decode() or "media")
    name, k = base, 1
    while os.path.lexists(os.path.join(d, name)) and os.path.realpath(os.path.join(d, name)) != os.path.realpath(path):
        k += 1
        name = "%d_%s" % (k, base)
    link = os.path.join(os.path.abspath(d), name)
    if not os.path.lexists(link):
        os.symlink(os.path.abspath(path), link)
    made[path] = link
    return link


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan", nargs="?")
    ap.add_argument("--out")
    ap.add_argument("--nle-applies-rotation", action="store_true")
    ap.add_argument("--flip-rotation", action="store_true")
    ap.add_argument("--ascii-links", metavar="DIR")
    ap.add_argument("--selftest", action="store_true", help="run the offline XML self-test and exit")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if not a.plan or not a.out:
        ap.error("plan and --out are required")
    try:
        with open(a.plan, encoding="utf-8") as fh:
            plan = json.load(fh)
    except (OSError, ValueError) as e:
        sys.exit("cannot read plan: %s" % e)
    base = os.path.dirname(os.path.abspath(a.plan))
    from plan_check import validate
    P0 = lambda p: p if os.path.isabs(p) else os.path.join(base, p)  # noqa: E731
    fails, _, _ = validate(plan, P0)
    if fails:
        for f in fails:
            print("  FAIL " + f)
        sys.exit("plan has field errors: fix them first (plan_check.py)")
    made = {}
    P = (lambda p: ascii_link(P0(p), a.ascii_links, made)) if a.ascii_links else P0
    paths = [P(s["src"]) for s in plan["shots"]] + [P(o["png"]) for o in plan.get("overlays") or []]
    if (plan.get("music") or {}).get("file"):
        paths.append(P(plan["music"]["file"]))
    minfo = {p: media_info(p) for p in set(paths)}
    xml = build_xml(plan, P, minfo, a.nle_applies_rotation, a.flip_rotation)
    probs = validate_xml(xml, plan, plan.get("fps", 25))
    for p in probs:
        print("  ! XML self-check: " + p)
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(xml)
    if not a.ascii_links and any(any(ord(ch) > 127 for ch in p) for p in paths):
        print("  ! some media paths contain non-ASCII characters: Premiere's XML import can fail silently on them; "
              "re-export with --ascii-links DIR")
    fps = parse_fps(plan.get("fps", 25))
    print("timeline written: %s (%d clips, %d frames = %.2fs at %s fps). NOT import-tested: check the first slowed, "
          "vertical and dissolved clip after File > Import." % (a.out, len(plan["shots"]), layout(plan["shots"], fps)["total"],
                                                                 layout(plan["shots"], fps)["total"] / float(fps), plan.get("fps", 25)))


if __name__ == "__main__":
    main()
