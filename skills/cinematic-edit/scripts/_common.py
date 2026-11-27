"""Shared helpers for the cinematic-edit scripts.

Only the Python standard library, numpy and Pillow are used. Media is read
through the user's own ffmpeg / ffprobe. Nothing here touches the network.
"""
import json
import os
import shutil
import subprocess
import sys

import numpy as np

_SEARCH_DIRS = [
    "/opt/homebrew/bin",
    "/usr/local/bin",
    "/usr/bin",
    os.path.expanduser("~/bin"),
]


def find_tool(name):
    """Locate ffmpeg or ffprobe: env var CE_FFMPEG / CE_FFPROBE, then PATH, then common dirs."""
    env = os.environ.get("CE_" + name.upper())
    if env and os.path.isfile(env):
        return env
    hit = shutil.which(name)
    if hit:
        return hit
    for d in _SEARCH_DIRS:
        p = os.path.join(d, name)
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    sys.exit(
        "cinematic-edit: '%s' was not found. Install ffmpeg (it includes ffprobe) "
        "or set CE_%s to its full path." % (name, name.upper())
    )


def run(cmd, capture=True):
    """Run a command list without a shell. Returns stdout text (or raises with stderr)."""
    p = subprocess.run(cmd, stdout=subprocess.PIPE if capture else None,
                       stderr=subprocess.PIPE)
    if p.returncode != 0:
        err = p.stderr.decode("utf-8", "replace")[-2000:]
        raise RuntimeError("command failed: %s\n%s" % (" ".join(cmd[:4]) + " ...", err))
    return p.stdout.decode("utf-8", "replace") if capture else ""


def ffprobe_json(path):
    out = run([find_tool("ffprobe"), "-v", "error", "-print_format", "json",
               "-show_format", "-show_streams", path])
    return json.loads(out)


def video_stream(info):
    for s in info.get("streams", []):
        if s.get("codec_type") == "video" and s.get("disposition", {}).get("attached_pic", 0) == 0:
            return s
    return None


def rational(r, default=0.0):
    try:
        if not r or r == "0/0":
            return default
        if "/" in r:
            a, b = r.split("/")
            return float(a) / float(b) if float(b) else default
        return float(r)
    except (ValueError, ZeroDivisionError):
        return default


def rotation_of(stream):
    """Display rotation in degrees (0, 90, -90, 180) from side data or tags."""
    for sd in stream.get("side_data_list", []) or []:
        if "rotation" in sd:
            try:
                return int(round(float(sd["rotation"])))
            except (TypeError, ValueError):
                pass
    tag = (stream.get("tags") or {}).get("rotate")
    if tag:
        try:
            return -int(tag)  # legacy tag is clockwise; side data is counter-clockwise
        except ValueError:
            pass
    return 0


def read_gray_frames(path, fps, width=320, start=None, duration=None, autorotate=True, pre_vf=None):
    """Decode frames as small grayscale float32 arrays at a fixed sample rate.

    Returns (frames[N,H,W] float32 0..255, times[N] seconds).
    """
    info = ffprobe_json(path)
    vs = video_stream(info)
    if vs is None:
        raise RuntimeError("no video stream in %s" % path)
    w, h = int(vs["width"]), int(vs["height"])
    rot = rotation_of(vs) if autorotate else 0
    if rot in (90, -90, 270, -270):
        w, h = h, w
    out_w = int(width) // 2 * 2
    out_h = max(2, int(round(h * out_w / float(w))) // 2 * 2)
    cmd = [find_tool("ffmpeg"), "-v", "error"]
    if start is not None:
        cmd += ["-ss", "%.3f" % start]
    cmd += ["-i", path]
    if duration is not None:
        cmd += ["-t", "%.3f" % duration]
    # fps and scale FIRST, then the LUT: applying a 3D LUT to every full-resolution
    # frame before sampling made LUT scans 4-5x slower for no visible gain.
    chain = "fps=%s,scale=%d:%d:flags=area:%s" % (fps, out_w, out_h, scale_in_opts(vs))
    if pre_vf:
        chain += ",format=rgb24," + pre_vf  # YUV->RGB done by OUR scale (right matrix)
    chain += ",format=gray"
    cmd += ["-vf", chain,
            "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    if not autorotate:
        cmd.insert(cmd.index("-i"), "-noautorotate")
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.decode("utf-8", "replace")[-1500:])
    buf = np.frombuffer(p.stdout, dtype=np.uint8)
    n = buf.size // (out_w * out_h)
    frames = buf[: n * out_w * out_h].reshape(n, out_h, out_w).astype(np.float32)
    t0 = start or 0.0
    times = t0 + np.arange(n) / float(fps)
    return frames, times


def read_rgb_frame(path, t, width=640, pre_vf=None, vs=None):
    """One RGB frame (uint8 HxWx3) at time t seconds (BT.709-correct decode)."""
    if vs is None:
        try:
            vs = video_stream(ffprobe_json(path))
        except Exception:
            vs = None
    chain = "scale=%d:-2:flags=lanczos:%s,format=rgb24" % (width, scale_in_opts(vs))
    if pre_vf:
        chain = chain + "," + pre_vf  # LUT after the downscale (same picture, far faster)
    cmd = [find_tool("ffmpeg"), "-v", "error", "-ss", "%.3f" % max(0.0, t), "-i", path,
           "-frames:v", "1", "-vf", chain,
           "-f", "image2pipe", "-vcodec", "png", "-"]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0 or not p.stdout:
        return None
    from io import BytesIO
    from PIL import Image
    return np.array(Image.open(BytesIO(p.stdout)).convert("RGB"))


def write_json(path, obj):
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def fmt_tc(sec):
    sec = max(0.0, float(sec))
    m, s = divmod(sec, 60)
    return "%d:%05.2f" % (int(m), s)


def font(size=14):
    """A readable font if available, else Pillow's default."""
    from PIL import ImageFont
    for p in ("/System/Library/Fonts/Supplemental/Arial.ttf",
              "/System/Library/Fonts/Helvetica.ttc",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "C:\\Windows\\Fonts\\arial.ttf"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def ff_path(p):
    """A file path made safe for an ffmpeg filter option on every OS.

    In a filter string ":" separates options and "\\" escapes, so a Windows path
    such as C:\\Users\\... breaks the filter. Use forward slashes, escape ":"
    and quote the whole path (also valid on macOS and Linux).
    """
    p = os.path.abspath(p).replace("\\", "/")
    p = p.replace("'", "'\\''").replace(":", "\\:")
    return "'%s'" % p


def lut_filter(lut_path):
    """ffmpeg filter string applying a .cube LUT with tetrahedral interpolation.

    ffmpeg filter syntax is fragile with spaces, colons and non-ASCII paths, so
    a LUT with an unsafe path is copied once to a temp file with a safe name.
    """
    import hashlib
    import re as _re
    import tempfile
    if not lut_path:
        return None
    if not os.path.isfile(lut_path):
        sys.exit("LUT not found: %s" % lut_path)
    p = os.path.abspath(lut_path)
    if not _re.match(r"^[A-Za-z0-9_./-]+$", p):
        # named by CONTENT hash: an edited LUT file never reuses a stale copy
        with open(p, "rb") as fh:
            h = hashlib.sha1(fh.read()).hexdigest()[:16]
        safe = os.path.join(tempfile.gettempdir(), "ce_lut_%s.cube" % h)
        if not os.path.exists(safe):
            shutil.copyfile(p, safe)
        p = safe
    return "lut3d=file=%s:interp=tetrahedral" % ff_path(p)


def luma(rgb):
    """Rec.709 luma of an (..., 3) array (explicit sum: avoids BLAS float32 matmul issues)."""
    rgb = np.asarray(rgb, dtype=np.float64)
    return 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]


def ramp_expr(keys):
    """Smooth speed ramp as one ffmpeg setpts expression.

    keys: [[source_time_s, k], ...] relative to the shot's in point, where k is the
    slowdown factor (1 = real time, 2 = half speed, 4 = quarter speed). Between keys
    k follows a smoothstep curve; output time is its exact integral, so every source
    frame lands at the right moment. Returns (expression, output_seconds).
    """
    keys = [(float(t), float(k)) for t, k in keys]
    if len(keys) < 2:
        raise ValueError("a ramp needs at least two keys")
    parts, acc = [], 0.0
    for (t0, k0), (t1, k1) in zip(keys, keys[1:]):
        L, d = t1 - t0, k1 - k0
        if L <= 0:
            raise ValueError("ramp keys must increase in time")
        u = "((X-%r)/%r)" % (t0, L)
        seg = "(%.9f+%r*(X-%r)+%.9f*(pow(%s,3)-0.5*pow(%s,4)))" % (acc, k0, t0, d * L, u, u)
        parts.append((t1, seg))
        acc += k0 * L + d * L * 0.5
    expr = parts[-1][1]
    for t1, seg in reversed(parts[:-1]):
        expr = "if(lt(X,%r),%s,%s)" % (t1, seg, expr)
    return expr.replace("X", "((PTS-STARTPTS)*TB)"), acc


STILL_EXT = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp", ".bmp")


def is_still(shot):
    """A shot whose source is a picture (end card, photo, designed frame), shown for 'duration' s."""
    if shot.get("still"):
        return True
    return os.path.splitext(str(shot.get("src", "")))[1].lower() in STILL_EXT


def shot_timeline_seconds(shot):
    """Length of a plan shot on the timeline (speed, ramp and still aware)."""
    if is_still(shot):
        return float(shot["duration"])
    if shot.get("ramp"):
        return ramp_expr(shot["ramp"])[1]
    sp = float(shot.get("speed", 1.0))
    if sp <= 0:
        raise ValueError("speed must be > 0")
    return (float(shot["out"]) - float(shot["in"])) / sp


# --- frame rates -------------------------------------------------------------------------
_NTSC = {23.976: (24000, 1001), 23.98: (24000, 1001), 29.97: (30000, 1001), 47.952: (48000, 1001),
         47.95: (48000, 1001), 59.94: (60000, 1001), 119.88: (120000, 1001)}


def parse_fps(v):
    """Frame rate as an exact Fraction. Accepts 25, 29.97, "30000/1001", "29.97".

    29.97 / 23.976 / 59.94 (and their usual roundings) become the exact NTSC
    rationals 30000/1001 etc., never 2997/100.
    """
    from fractions import Fraction
    if isinstance(v, Fraction):
        return v
    if isinstance(v, str):
        s = v.strip()
        if "/" in s:
            a, b = s.split("/", 1)
            fr = Fraction(int(a), int(b))
            if fr <= 0:
                raise ValueError("fps must be > 0")
            return fr
        v = float(s)
    f = float(v)
    if f <= 0:
        raise ValueError("fps must be > 0")
    for k, (n, d) in _NTSC.items():
        if abs(f - k) < 0.006:
            return Fraction(n, d)
    return Fraction(f).limit_denominator(1001)


def fps_str(fr):
    """ffmpeg-ready string: '25' or '30000/1001'."""
    fr = parse_fps(fr)
    return str(fr.numerator) if fr.denominator == 1 else "%d/%d" % (fr.numerator, fr.denominator)


def transition_frames(shot):
    """Dissolve length in frames from 'transition' ('cut', 'dissolve', 'dissolve:12')."""
    tr = str(shot.get("transition", "cut") or "cut").strip().lower()
    if tr in ("cut", ""):
        return 0
    if tr.startswith("dissolve"):
        if ":" in tr:
            return max(0, int(tr.split(":", 1)[1]))
        return 12
    raise ValueError("unknown transition '%s' (use cut or dissolve:FRAMES)" % tr)


def layout(shots, fps):
    """Exact frame layout of a plan, the same numbers render.py produces.

    Each shot lasts round(seconds * fps) frames. A dissolve of D frames into shot i
    overlaps the end of shot i-1 and the start of shot i (D is limited to half of
    either shot), so the film is shorter than the sum of the shots by every D.
    Returns dict with frames, starts, dissolves, total (frames) and cut_frames:
    the visual cut point of each transition (start of shot i for a hard cut, the
    middle of the dissolve otherwise), as float frames.
    """
    f = float(parse_fps(fps))
    frames = [max(1, int(round(shot_timeline_seconds(s) * f))) for s in shots]
    starts, dissolves, cuts = [], [], []
    for i, n in enumerate(frames):
        if i == 0:
            starts.append(0)
            dissolves.append(0)
            continue
        d = min(transition_frames(shots[i]), frames[i - 1] // 2, n // 2)
        dissolves.append(d)
        starts.append(starts[-1] + frames[i - 1] - d)
        cuts.append(starts[-1] + d / 2.0)
    total = (starts[-1] + frames[-1]) if frames else 0
    return {"frames": frames, "starts": starts, "dissolves": dissolves, "total": total, "cut_frames": cuts}


# --- colour-correct format conversion ----------------------------------------------------
# ffprobe colour-space tag -> value accepted by the scale filter's in_color_matrix.
# BT.601 variants (bt470bg is common on phones, screen recordings and web H.264) all
# map to "smpte170m", which every ffmpeg since 4.x accepts; "bt470bg" itself is NOT
# a valid scale option and would crash the filter graph. Anything else (unknown,
# reserved, rgb, ycgco, ...) falls back to BT.709 in scale_in_opts().
_MATRIX = {"bt709": "bt709", "bt2020nc": "bt2020", "bt2020c": "bt2020",
           "smpte170m": "smpte170m", "bt470bg": "smpte170m", "bt601": "smpte170m",
           "bt470": "smpte170m", "fcc": "fcc", "smpte240m": "smpte240m"}


def scale_in_opts(vs):
    """scale-filter options that decode YUV with the RIGHT matrix and range.

    ffmpeg assumes BT.601 for untagged video (Sony FX3 files are untagged); camera
    video is BT.709 (or BT.2020 when tagged so), so the matrix is always set here.
    """
    m = _MATRIX.get((vs or {}).get("color_space") or "", "bt709")
    rng = "pc" if (vs or {}).get("color_range") == "pc" else "tv"
    if str((vs or {}).get("pix_fmt", "")).startswith(("yuvj",)):
        rng = "pc"
    return "in_color_matrix=%s:in_range=%s" % (m, rng)
