#!/usr/bin/env python3
"""probe.py: technical inventory of camera clips before any editing.

For every clip it reports: camera, codec, bit depth, chroma subsampling,
resolution, frame rate (and variable-frame-rate risk), display rotation,
colour tags, and a best guess of the log/HDR profile. It prints warnings
that must be resolved before grading or cutting.

Usage:
  python3 probe.py CLIP_OR_FOLDER [...] [--json out.json] [--looks]

  --looks   also sample 5 frames per clip and estimate whether the picture
            "looks like log" (lifted blacks, low contrast, low saturation).

Read-only: never modifies media, never uses the network.
"""
import argparse
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (luma, ffprobe_json, video_stream, rational, rotation_of,  # noqa: E402
                     read_gray_frames, read_rgb_frame, write_json)

VIDEO_EXT = {".mov", ".mp4", ".mxf", ".m4v", ".mts", ".avi", ".mkv", ".braw", ".r3d", ".crm"}

# Log names that cameras write as TEXT into their metadata (QuickTime udta / meta / uuid
# atoms, XMP, Sony XML sidecars). Only long, distinctive spellings are kept: short
# ones such as "DLog", "NLog" or "LogC" occur by chance inside compressed video, and
# a finished H.264 render was once labelled "DJI D-Log" that way. These patterns are
# searched ONLY in metadata, never in the picture payload (mdat).
LOG_SIGNATURES = [
    (rb"[Ss]-[Ll]og3-[Cc]ine", "Sony S-Log3 / S-Gamut3.Cine"),
    (rb"[Ss]-[Ll]og3", "Sony S-Log3"),
    (rb"[Ss]-[Ll]og2", "Sony S-Log2"),
    (rb"F-Log2", "Fujifilm F-Log2"),
    (rb"F-Log(?![0-9A-Za-z])", "Fujifilm F-Log"),
    (rb"V-Log", "Panasonic V-Log"),
    (rb"Canon Log 3|CanonLog3", "Canon Log 3"),
    (rb"Canon Log 2|CanonLog2", "Canon Log 2"),
    (rb"N-Log(?![0-9A-Za-z])", "Nikon N-Log"),
    (rb"D-Log M", "DJI D-Log M"),
    (rb"D-Log(?![0-9A-Za-z ])", "DJI D-Log"),
    (rb"Apple Log", "Apple Log"),
    (rb"ARRI LogC4|LogC4", "ARRI LogC4"),
    (rb"ARRI LogC3|LogC3", "ARRI LogC3"),
    (rb"Log3G10", "RED Log3G10"),
]
# without readable metadata atoms (MXF, MTS ...) only names of 7+ characters are trusted
_LONG_ONLY = {"Sony S-Log3 / S-Gamut3.Cine", "Canon Log 3", "Canon Log 2", "Apple Log", "RED Log3G10"}

BIT_DEPTH = {
    "yuv420p": 8, "yuvj420p": 8, "yuv422p": 8, "yuvj422p": 8, "yuv444p": 8, "nv12": 8,
    "yuv420p10le": 10, "yuv422p10le": 10, "yuv444p10le": 10, "p010le": 10,
    "yuv420p12le": 12, "yuv422p12le": 12, "yuv444p12le": 12,
}


def chroma_of(pix_fmt):
    for c in ("420", "422", "444"):
        if c in (pix_fmt or ""):
            return "4:%s:%s" % (c[1], c[2])
    if pix_fmt in ("nv12", "p010le"):
        return "4:2:0"
    return "?"


_META_CONTAINERS = {b"moov", b"trak", b"mdia", b"minf", b"udta", b"meta", b"ilst", b"edts"}
_META_LEAVES = {b"udta", b"meta", b"uuid", b"XMP_", b"ilst", b"keys"}


def _metadata_blobs(path, cap=2 * 1024 * 1024):
    """Bytes of the metadata atoms of a QuickTime/MP4 file (udta, meta, uuid, XMP),
    never the media payload. Returns (blobs, is_isobmff)."""
    blobs, found = [], False
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as f:
            def walk(start, end, depth):
                nonlocal found
                for t, o, hl, n in _atoms(f, start, end):
                    found = True
                    if t in _META_LEAVES:
                        f.seek(o + hl)
                        blobs.append(f.read(min(n - hl, cap)))
                    elif t in _META_CONTAINERS and depth < 6:
                        walk(o + hl, o + n, depth + 1)
            first = f.read(8)
            if len(first) == 8 and first[4:8] in (b"ftyp", b"moov", b"wide", b"free", b"mdat", b"skip", b"pnot"):
                walk(0, size, 0)
    except (OSError, struct.error, RecursionError):
        pass
    return blobs, found


def scan_signatures(path, chunk=1024 * 1024):
    """Log markers from metadata only: QuickTime metadata atoms and Sony XML sidecars
    (for files without atoms, such as MXF, the file head with long names only)."""
    hits = []
    blobs, iso = _metadata_blobs(path)
    if not iso:
        try:
            with open(path, "rb") as f:
                blobs.append(f.read(chunk))
        except OSError:
            pass
    base, _ = os.path.splitext(path)
    for side in (base + "M01.XML", base + "M01.xml", base + ".XML", base + ".xml"):
        if os.path.exists(side):
            with open(side, "rb") as f:
                blobs.append(f.read(256 * 1024))
    data = b"\n".join(blobs)
    m = re.search(rb'CaptureGammaEquation"?\s+value="([^"]+)"', data)
    if m:
        g = m.group(1).decode("latin1")
        cf = re.search(rb'captureFps="([\d.]+)[pi]?"\s+formatFps="([\d.]+)[pi]?"', data)
        if cf:
            hits.append("Capture: %s %s" % (cf.group(1).decode(), cf.group(2).decode()))
        dm = re.search(rb'<Device manufacturer="([^"]*)" modelName="([^"]*)"', data)
        if dm:
            hits.append("Device: %s %s" % (dm.group(1).decode("latin1"), dm.group(2).decode("latin1")))
        hits.append("Sony gamma: " + g)
        return hits  # authoritative for Sony; skip the name search
    for pat, name in LOG_SIGNATURES:
        if not iso and name not in _LONG_ONLY:
            continue
        if re.search(pat, data):
            hits.append(name)
            break
    return hits


# --- Fujifilm: the log profile is stored in the maker note (tag 0x3803) ----------
def _atoms(f, start, end):
    off = start
    while off < end - 8:
        f.seek(off)
        h = f.read(8)
        if len(h) < 8:
            return
        n, t = struct.unpack(">I4s", h)
        hl = 8
        if n == 1:
            n = struct.unpack(">Q", f.read(8))[0]
            hl = 16
        if n == 0:
            n = end - off
        if n < hl:
            return
        yield t, off, hl, n
        off += n


def _fuji_mvtg(path):
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as f:
            for t, o, hl, n in _atoms(f, 0, size):
                if t == b"moov":
                    for t2, o2, hl2, n2 in _atoms(f, o + hl, o + n):
                        if t2 == b"udta":
                            for t3, o3, hl3, n3 in _atoms(f, o2 + hl2, o2 + n2):
                                if t3 == b"MVTG":
                                    f.seek(o3)
                                    return f.read(min(n3, 2 * 1024 * 1024))
    except (OSError, struct.error):
        return None
    return None


def _ifd(b, base, off):
    out = {}
    if off < 0 or off + 2 > len(b):
        return out
    n = struct.unpack("<H", b[off:off + 2])[0]
    for i in range(min(n, 512)):
        e = off + 2 + 12 * i
        if e + 12 > len(b):
            break
        tag, typ, cnt = struct.unpack("<HHI", b[e:e + 8])
        val = struct.unpack("<I", b[e + 8:e + 12])[0]
        short = struct.unpack("<H", b[e + 8:e + 10])[0]
        out[tag] = (typ, cnt, short if typ == 3 and cnt == 1 else val)
    return out


def fuji_log(path):
    """Return 'F-Log', 'F-Log2', 'none' or None (not a Fujifilm clip / unreadable)."""
    b = _fuji_mvtg(path)
    if not b or b"FUJIFILM" not in b:
        return None
    i = b.find(b"\x0f\x01\x02\x00")  # IFD0 entry for Make (0x010f, ASCII)
    if i < 2:
        return None
    try:
        makeoff = struct.unpack("<I", b[i + 8:i + 12])[0]
        base = b.find(b"FUJIFILM") - makeoff
        d0 = _ifd(b, base, i - 2)
        exif = d0.get(0x8769)
        if not exif:
            return None
        ex = _ifd(b, base, base + exif[2])
        mn = ex.get(0x927C)
        if not mn:
            return None
        mstart = base + mn[2]
        if b[mstart:mstart + 8] != b"FUJIFILM":
            return None
        io = struct.unpack("<I", b[mstart + 8:mstart + 12])[0]
        maker = _ifd(b, mstart, mstart + io)
        v = maker.get(0x3803)
        if v is None:
            return None
        return {0: "none", 16: "F-Log", 32: "HLG", 48: "F-Log2"}.get(v[2], "unknown(%s)" % v[2])
    except (struct.error, IndexError):
        return None


def looks_like_log(path, duration):
    """Heuristic from 5 frames: lifted blacks + compressed range + low chroma."""
    import numpy as np
    stats = []
    for k in range(5):
        t = duration * (k + 0.5) / 5.0
        rgb = read_rgb_frame(path, t, width=320)
        if rgb is None:
            continue
        y = luma(rgb.astype(np.float32))
        mx = rgb.max(axis=2).astype(np.float32)
        mn = rgb.min(axis=2).astype(np.float32)
        chroma = (mx - mn).mean()
        stats.append((np.percentile(y, 2), np.percentile(y, 98), chroma))
    if not stats:
        return None
    import numpy as np  # noqa: F811
    p2, p98, ch = [float(np.median([s[i] for s in stats])) for i in range(3)]
    # Log curves lift black far above display black; a dark display-referred
    # scene has low p2. So lifted blacks are required, plus flat range or low chroma.
    flat = p2 > 20 and ((p98 - p2) < 150 or ch < 30)
    return {"p2": round(p2, 1), "p98": round(p98, 1), "mean_chroma": round(ch, 1),
            "verdict": "likely log/flat" if flat else "looks display-referred"}


def probe(path, looks=False):
    info = ffprobe_json(path)
    vs = video_stream(info)
    fmt = info.get("format", {})
    tags = dict(fmt.get("tags") or {})
    r = {"file": path, "warnings": []}
    if vs is None:
        r["warnings"].append("no video stream")
        return r
    pix = vs.get("pix_fmt", "")
    fr = rational(vs.get("r_frame_rate"))
    afr = rational(vs.get("avg_frame_rate"))
    rot = rotation_of(vs)
    w, h = int(vs.get("width", 0)), int(vs.get("height", 0))
    dur = float(fmt.get("duration") or vs.get("duration") or 0)
    r.update({
        "camera": " ".join(x for x in (tags.get("make") or tags.get("com.apple.quicktime.make", ""),
                                        tags.get("model") or tags.get("com.apple.quicktime.model", ""),
                                        tags.get("comment", "") if "CAMERA" in tags.get("comment", "") else "")
                           if x).strip() or "?",
        "codec": vs.get("codec_name"), "profile": vs.get("profile"),
        "pix_fmt": pix, "bit_depth": BIT_DEPTH.get(pix, int(vs.get("bits_per_raw_sample") or 0) or None),
        "chroma": chroma_of(pix),
        "size": "%dx%d" % (w, h), "rotation": rot,
        "display_size": "%dx%d" % ((h, w) if rot in (90, -90, 270, -270) else (w, h)),
        "fps": round(fr, 3), "avg_fps": round(afr, 3),
        "duration": round(dur, 3),
        "bitrate_mbps": round(float(fmt.get("bit_rate") or 0) / 1e6, 1),
        "range": vs.get("color_range"), "primaries": vs.get("color_primaries"),
        "transfer": vs.get("color_transfer"), "matrix": vs.get("color_space"),
    })
    # log / HDR detection
    log = []
    fj = fuji_log(path)
    if fj is not None:
        log.append("Fujifilm maker note: " + fj)
    log += scan_signatures(path)
    if r["transfer"] in ("arib-std-b67",):
        log.append("HLG (transfer tag)")
    if r["transfer"] in ("smpte2084",):
        log.append("PQ / HDR10 (transfer tag)")
    dev = [x for x in log if x.startswith("Device: ")]
    cap = [x for x in log if x.startswith("Capture: ")]
    log = [x for x in log if not x.startswith(("Device: ", "Capture: "))]
    capture_fps = None
    if cap:
        try:
            capture_fps = float(cap[0].split()[1])
        except (IndexError, ValueError):
            capture_fps = None
    has_audio = any(x.get("codec_type") == "audio" for x in info.get("streams", []))
    r["has_audio"] = has_audio
    r["capture_fps"] = capture_fps
    # frame-rate class: the FIRST creative fact about a clip
    if capture_fps and capture_fps > fr * 1.05:
        r["fps_class"] = "in-camera slow motion (captured %.0f fps, plays at %.2f): already %.0f%% speed, do not slow again by accident" % (capture_fps, fr, 100 * fr / capture_fps)
    elif fr >= 47:
        r["fps_class"] = ("high frame rate, not conformed: real slow motion available "
                          "(25p timeline: %.0f%%, 30p timeline: %.0f%%)" % (100 * 25.0 / fr, 100 * 30.0 / fr))
    elif not has_audio and fr < 31:
        r["fps_class"] = "normal rate but NO AUDIO: possibly in-camera slow motion (S&Q / high-speed mode): check motion"
    else:
        r["fps_class"] = "normal speed (%.2f fps): slow motion only with frame interpolation" % fr
    if dev and r["camera"] == "?":
        r["camera"] = dev[0][8:]
    r["log_profile"] = log or ["not detected from metadata"]
    if looks:
        r["looks"] = looks_like_log(path, dur)

    # warnings
    W = r["warnings"]
    is_log = any(re.search(r"log", x, re.I) and not re.search(r"none|rec709|xvycc|not detected", x, re.I)
                 for x in log)
    r["is_log"] = bool(is_log)
    if is_log and r["bit_depth"] == 8:
        W.append("8-bit log: grade gently (banding/noise when pushed); avoid big exposure lifts")
    if is_log:
        W.append("LOG footage: apply the camera maker's official log-to-Rec.709 transform "
                 "(or NLE colour-space override) BEFORE judging or grading")
    if rot in (90, -90, 270, -270):
        W.append("rotated %d deg: this is a vertical shot stored landscape; rotate, do not zoom" % rot)
    if afr and fr and abs(afr - fr) / fr > 0.02:
        W.append("variable frame rate suspected (r=%.3f avg=%.3f): conform to constant fps first" % (fr, afr))
    if fr >= 47:
        W.append("high frame rate %.2f fps: can be conformed to slow motion "
                 "(speed = timeline_fps / %.2f)" % (fr, fr))
    if r["range"] == "pc":
        W.append("full-range video: make sure the NLE does not double-expand levels")
    if not r["primaries"] or r["primaries"] == "unknown":
        W.append("no colour primaries tag: NLE will guess; set colour space explicitly")
    if r["chroma"] == "4:2:0" and is_log:
        W.append("4:2:0 log: avoid heavy keying/secondaries on fine edges")
    return r


_LOG_CACHE = {}


def log_profile(path):
    """Log profile name from metadata (maker note, sidecar, tags) or None if not log."""
    key = os.path.abspath(path)
    if key not in _LOG_CACHE:
        try:
            r = probe(path)
            _LOG_CACHE[key] = "; ".join(r.get("log_profile", [])) if r.get("is_log") else None
        except Exception:
            _LOG_CACHE[key] = None
    return _LOG_CACHE[key]


def collect(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            for root, _, files in os.walk(p):
                for fn in sorted(files):
                    if os.path.splitext(fn)[1].lower() in VIDEO_EXT and not fn.startswith("._"):
                        out.append(os.path.join(root, fn))
        elif os.path.isfile(p):
            out.append(p)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--json", help="write full results to this JSON file")
    ap.add_argument("--looks", action="store_true", help="also sample frames for a 'looks like log' check")
    a = ap.parse_args()
    files = collect(a.paths)
    if not files:
        sys.exit("no video files found")
    results = []
    for f in files:
        try:
            r = probe(f, a.looks)
        except Exception as e:  # keep going on broken files
            r = {"file": f, "error": str(e)[:300], "warnings": ["could not read"]}
        results.append(r)
        print("\n%s" % os.path.basename(f))
        if "error" in r:
            print("  ERROR:", r["error"])
            continue
        print("  %s | %s %s | %s-bit %s | %s (display %s, rot %s) | %s fps | %.1fs | %s Mbps"
              % (r.get("camera"), r.get("codec"), r.get("profile") or "", r.get("bit_depth"),
                 r.get("chroma"), r.get("size"), r.get("display_size"), r.get("rotation"),
                 r.get("fps"), r.get("duration", 0), r.get("bitrate_mbps")))
        print("  FPS: " + r.get("fps_class", "?"))
        print("  colour tags: range=%s primaries=%s transfer=%s matrix=%s"
              % (r.get("range"), r.get("primaries"), r.get("transfer"), r.get("matrix")))
        print("  log/HDR: " + "; ".join(r.get("log_profile", [])))
        if r.get("looks"):
            print("  picture: %s" % r["looks"])
        for w in r["warnings"]:
            print("  ! " + w)
    if len(results) > 1:
        from collections import Counter
        ok = [r for r in results if "error" not in r]
        print("\nSUMMARY  %d clips (%d unreadable)" % (len(results), len(results) - len(ok)))
        def orient(r):
            dw, dh = [int(x) for x in r.get("display_size", "0x0").split("x")]
            kind = "vertical" if dh > dw else "landscape"
            return kind + (" (rotation flag %s)" % r["rotation"] if r.get("rotation") else "")
        print("  orientation: " + ", ".join("%s x%d" % kv for kv in Counter(orient(r) for r in ok).most_common()))
        print("  frame rates: " + ", ".join("%s fps x%d" % kv for kv in Counter(r.get("fps") for r in ok).most_common()))
        print("  log/HDR:     " + ", ".join("%s x%d" % kv for kv in Counter(
            "; ".join(r.get("log_profile", [])) for r in ok).most_common()))
        common = set.intersection(*[set(r["warnings"]) for r in ok]) if ok else set()
        if common:
            print("  every clip:  " + " | ".join(sorted(common)))
    if a.json:
        write_json(a.json, results)
        print("\nwritten:", a.json)


if __name__ == "__main__":
    main()
