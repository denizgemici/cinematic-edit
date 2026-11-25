#!/usr/bin/env python3
"""beats.py: turn a music track into a cut grid (beats, bars, phrases, energy) in video frames.

It decodes the track ONCE to a WAV that you should also use in the edit (MP3/AAC
decoders add different start delays, which shifts a beat grid), then finds:
  tempo, beat times, a bar grid (downbeat guess), 4- and 8-bar phrase starts,
  an energy curve (one value per video frame), and quiet moments.

Usage:
  python3 beats.py track.mp3 --fps 25 --out music/ [--bpm 96] [--first-downbeat 0.42]
                   [--beats-per-bar 4]

If librosa is installed it is used for onset strength; otherwise a numpy-only
spectral-flux detector is used. Automatic downbeats are a GUESS: listen and
pass --first-downbeat (seconds) when the bar grid sounds wrong. For the most
accurate tracking you may run a dedicated beat tracker yourself and pass --bpm.
Writes music/music.wav, music/beats.json, music/energy.png. No network.
"""
import argparse
import os
import subprocess
import sys
import wave

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import find_tool, write_json, font, fmt_tc  # noqa: E402

SR = 22050
HOP = 256


def decode(track, out_wav, sr=48000):
    p = subprocess.run([find_tool("ffmpeg"), "-v", "error", "-y", "-i", track, "-vn", "-ac", "2", "-ar", str(sr),
                        "-c:a", "pcm_s16le", out_wav], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        sys.exit("beats.py: cannot decode the audio of %s:\n%s" % (track, p.stderr.decode("utf-8", "replace")[-400:]))
    p = subprocess.run([find_tool("ffmpeg"), "-v", "error", "-i", out_wav, "-ac", "1", "-ar", str(SR),
                        "-f", "s16le", "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        sys.exit("beats.py: cannot read back %s" % out_wav)
    y = np.frombuffer(p.stdout, np.int16).astype(np.float32) / 32768.0
    if len(y) < SR * 2:
        sys.exit("beats.py: the track is shorter than 2 seconds or has no audio")
    return y


def onset_strength(y):
    """Returns (envelope, latency_seconds) where latency is added back to beat times."""
    try:
        import librosa  # optional
        env = librosa.onset.onset_strength(y=y, sr=SR, hop_length=HOP)
        return env.astype(np.float64), 0.0
    except Exception:
        pass
    n_fft = 1024
    win = np.hanning(n_fft)
    frames = 1 + (len(y) - n_fft) // HOP
    if frames < 4:
        return np.zeros(1), 0.0
    idx = np.arange(n_fft)[None, :] + HOP * np.arange(frames)[:, None]
    S = np.abs(np.fft.rfft(y[idx] * win, axis=1))
    # log-compressed mel-ish weighting: emphasise 30 Hz - 8 kHz
    S = np.log1p(100 * S)
    flux = np.maximum(S[1:] - S[:-1], 0).sum(axis=1)
    flux = np.concatenate([[0], flux])
    flux -= np.convolve(flux, np.ones(16) / 16, mode="same")
    # flux at index i compares window i-1 to window i, centred n_fft/2 after its start
    return np.maximum(flux, 0), (n_fft / 2.0) / SR


def tempo_candidates(env, lo=60, hi=200, top=5):
    """Tempo candidates from the onset autocorrelation: [(bpm, confidence 0..1), ...], best first.

    Confidence is the autocorrelation at that lag (relative to lag 0) with a mild
    preference for 90-140 bpm; half/double/3:4 relatives often score close, so
    an agent that cannot listen should compare the top two with the energy plot
    (or a human's ear) and pass --bpm."""
    sr_env = SR / HOP
    x = env - env.mean()
    n = len(x)
    f = np.fft.rfft(x, 2 * n)
    ac = np.fft.irfft(f * np.conj(f))[:n]
    ac = ac / (ac[0] + 1e-12)
    lags = np.arange(n)
    bpm = 60 * sr_env / np.maximum(lags, 1)
    weight = np.exp(-0.5 * (np.log2(np.maximum(bpm, 1) / 115.0) / 1.2) ** 2)
    sc = np.where((bpm >= lo) & (bpm <= hi), ac * weight, -np.inf)
    pk = [i for i in range(1, n - 1) if np.isfinite(sc[i]) and sc[i] >= sc[i - 1] and sc[i] >= sc[i + 1] and sc[i] > 0]
    pk.sort(key=lambda i: -sc[i])
    out = []
    for i in pk:
        # parabolic refinement of the lag
        a, b, c = ac[i - 1], ac[i], ac[i + 1]
        d = a - 2 * b + c
        li = i + (0.5 * (a - c) / d if abs(d) > 1e-12 else 0.0)
        t = 60 * sr_env / li
        if all(abs(t - o[0]) / o[0] > 0.03 for o in out):
            out.append((round(float(t), 2), round(float(max(sc[i], 0)), 3)))
        if len(out) >= top:
            break
    return out


def estimate_bpm(env, lo=70, hi=180):
    c = tempo_candidates(env, lo, hi, top=1)
    return c[0][0] if c else 120.0


def track_beats(env, bpm, tightness=100.0, spread=(0.5, 2.0)):
    """Dynamic-programming beat tracker (Ellis 2007). spread limits the beat-to-beat interval."""
    sr_env = SR / HOP
    period = 60.0 * sr_env / bpm
    n = len(env)
    score = env / (env.std() + 1e-9)
    cum = score.copy()
    back = -np.ones(n, dtype=int)
    lo, hi = max(1, int(np.floor(period * spread[0]))), int(np.ceil(period * spread[1]))
    for i in range(n):
        a, b = max(0, i - hi), i - lo
        if b <= a:
            continue
        prev = np.arange(a, b)
        pen = -tightness * (np.log((i - prev) / period)) ** 2
        cand = cum[prev] + pen
        j = int(np.argmax(cand))
        cum[i] = score[i] + cand[j]
        back[i] = prev[j]
    # start from the best end inside the last period
    tail = max(0, n - int(period))
    i = tail + int(np.argmax(cum[tail:]))
    beats = []
    while i >= 0:
        beats.append(i)
        i = back[i]
    return np.array(beats[::-1]) / sr_env


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("track")
    ap.add_argument("--fps", type=float, default=25.0, help="timeline frame rate (use 23.976/29.97 exactly if NTSC)")
    ap.add_argument("--out", default="music")
    ap.add_argument("--bpm", type=float, help="force tempo: the grid is tracked tightly at this tempo (fixes half/double/3:4 errors)")
    ap.add_argument("--first-downbeat", type=float, help="seconds of the first bar's downbeat, if you know it")
    ap.add_argument("--beats-per-bar", type=int, default=4)
    a = ap.parse_args()
    if not os.path.isfile(a.track):
        sys.exit("beats.py: track not found: %s" % a.track)
    if a.bpm is not None and not 30 <= a.bpm <= 300:
        sys.exit("beats.py: --bpm must be between 30 and 300")
    if a.fps <= 0:
        sys.exit("beats.py: --fps must be > 0")
    os.makedirs(a.out, exist_ok=True)
    wav = os.path.join(a.out, "music.wav")
    y = decode(a.track, wav)
    dur = len(y) / SR
    env, latency = onset_strength(y)
    if not np.any(env > 0):
        sys.exit("beats.py: no onsets found (silent or constant track)")
    cands = tempo_candidates(env)
    if a.bpm:
        bpm = a.bpm
        # forced tempo: the tracker may only vary the beat interval by +-4 %, with a stiff penalty
        beats = track_beats(env, bpm, tightness=2000.0, spread=(0.96, 1.04))
    else:
        bpm = cands[0][0] if cands else 120.0
        beats = track_beats(env, bpm)
    # drop weak leading/trailing "beats" produced by the tracker in silence
    sr_env = SR / HOP
    st = np.array([env[min(len(env) - 1, int(round(b * sr_env)))] for b in beats])
    if len(st) > 8:
        strong = st > 0.35 * np.median(st[st > 0]) if (st > 0).any() else np.ones(len(st), bool)
        i0 = int(np.argmax(strong))
        i1 = len(st) - int(np.argmax(strong[::-1]))
        beats = beats[i0:i1]
    beats = beats + latency
    if len(beats) > 4:
        bpm_measured = 60.0 / np.median(np.diff(beats))
    else:
        bpm_measured = bpm
    # downbeat guess: the beat phase (0..bpb-1) with the strongest onsets
    bpb = a.beats_per_bar
    strength = np.array([env[min(len(env) - 1, int(round((b - latency) * sr_env)))] for b in beats])
    if a.first_downbeat is not None:
        phase = int(np.argmin(np.abs(beats - a.first_downbeat))) % bpb
        db_note = "from --first-downbeat"
    else:
        phase = int(np.argmax([strength[p::bpb].mean() if len(strength[p::bpb]) else 0 for p in range(bpb)]))
        db_note = "guessed from onset strength: LISTEN and correct with --first-downbeat"
    downbeats = beats[phase::bpb]
    phrases4 = downbeats[::4]
    phrases8 = downbeats[::8]
    # energy per video frame (RMS, smoothed 0.5 s, normalised)
    spf = SR / a.fps
    nfr = int(dur * a.fps)
    rms = np.array([np.sqrt(np.mean(y[int(i * spf):int((i + 1) * spf)] ** 2) + 1e-12) for i in range(nfr)])
    k = max(1, int(a.fps / 2))
    energy = np.convolve(rms, np.ones(k) / k, mode="same")
    energy = energy / (energy.max() + 1e-12)
    quiet = []
    thr = 0.25
    i = 0
    while i < nfr:
        if energy[i] < thr:
            j = i
            while j < nfr and energy[j] < thr:
                j += 1
            if (j - i) / a.fps >= 0.4:
                quiet.append([round(i / a.fps, 2), round(j / a.fps, 2)])
            i = j
        i += 1

    def fr(t):
        return int(round(t * a.fps))

    res = {
        "track": a.track, "wav_for_edit": wav, "fps": a.fps, "duration": round(dur, 3),
        "bpm": round(float(bpm_measured), 2), "bpm_forced": a.bpm,
        "tempo_candidates": [{"bpm": b, "confidence": c} for b, c in cands],
        "beats_per_bar": bpb,
        "bar_seconds": round(60.0 / bpm_measured * bpb, 3),
        "downbeat_note": db_note,
        "beats": [round(float(b), 3) for b in beats],
        "beat_frames": [fr(b) for b in beats],
        "downbeats": [round(float(b), 3) for b in downbeats],
        "downbeat_frames": [fr(b) for b in downbeats],
        "phrase4_starts": [round(float(b), 3) for b in phrases4],
        "phrase8_starts": [round(float(b), 3) for b in phrases8],
        "quiet_moments": quiet,
        "energy_per_frame": [round(float(e), 3) for e in energy],
        "advice": [
            "Cut 0-1 frame BEFORE a beat, never 2+ frames late (sound late reads sluggish).",
            "Put structural changes on 4/8-bar phrase starts; splice the music on downbeats.",
            "Do not cut on every beat for more than 4 cuts in a row; vary density by section.",
            "Land the hero moment on a downbeat after a quiet moment or a drop.",
        ],
    }
    write_json(os.path.join(a.out, "beats.json"), res)

    from PIL import Image, ImageDraw
    W, H = 1400, 220
    im = Image.new("RGB", (W, H), (16, 16, 16))
    d = ImageDraw.Draw(im)
    X = lambda t: 10 + (W - 20) * t / max(dur, 1e-6)  # noqa: E731
    for q in quiet:
        d.rectangle([X(q[0]), 30, X(q[1]), H - 30], fill=(40, 40, 70))
    pts = [(X(i / a.fps), H - 30 - e * (H - 70)) for i, e in enumerate(energy)]
    if len(pts) > 1:
        d.line(pts, fill=(120, 200, 255), width=2)
    for b in beats:
        d.line([X(b), H - 30, X(b), H - 24], fill=(150, 150, 150))
    for b in downbeats:
        d.line([X(b), H - 30, X(b), H - 16], fill=(255, 210, 90), width=2)
    for b in phrases4:
        d.line([X(b), 30, X(b), H - 30], fill=(255, 120, 90))
    d.text((10, 6), "%s | %.1f bpm | bar %.2fs | blue=energy, red=4-bar phrase, gold=downbeat, shaded=quiet"
           % (os.path.basename(a.track), bpm_measured, res["bar_seconds"]), fill=(225, 225, 225), font=font(13))
    d.text((10, H - 14), "0:00", fill=(170, 170, 170), font=font(11))
    d.text((W - 60, H - 14), fmt_tc(dur), fill=(170, 170, 170), font=font(11))
    im.save(os.path.join(a.out, "energy.png"))
    print("tempo candidates (bpm, confidence): " + ", ".join("%.1f (%.2f)" % c for c in cands))
    if a.bpm:
        print("tempo forced to %.1f bpm; tracked grid averages %.2f bpm" % (a.bpm, bpm_measured))
    elif len(cands) > 1 and cands[1][1] > 0.85 * cands[0][1]:
        print("  ! the top tempos are close: %.1f vs %.1f bpm. Check one 4/4 bar lasts 1.6-3.2 s and pass --bpm "
              "if the grid looks wrong on energy.png" % (cands[0][0], cands[1][0]))
    print("tempo %.1f bpm, %d beats, %d bars, %d 4-bar phrases, %d quiet moments"
          % (bpm_measured, len(beats), len(downbeats), len(phrases4), len(quiet)))
    print("downbeats: " + db_note)
    print("written: %s/music.wav (use THIS file in the edit), beats.json, energy.png" % a.out)


if __name__ == "__main__":
    main()
