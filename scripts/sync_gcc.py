# /// script
# requires-python = ">=3.9"
# dependencies = ["numpy", "scipy"]
# ///
"""Find where a short B cam clip starts inside a longer A cam clip, by audio.

GCC-PHAT cross-correlation on 8 kHz mono, speech band only. PHAT weighting
gives a sharp peak even when the two mics sound different (lav vs on-camera).

    uv run sync_gcc.py A_cam.mp4 B_cam.mp4 --fps 23.976
    uv run sync_gcc.py A_cam.mp4 B_cam.mp4 --predict 38.5 --window 12

--predict is where you expect B to start in A (seconds), for example from the
two cameras' clock times. Searching only a window around it avoids false
matches on long takes. Without it the whole A clip is searched.

Prints JSON: offset in seconds and in A cam frames, and a confidence ratio
(highest peak / next highest peak more than 25 ms away). 2 or more is a
frame-exact match; under 1.5 means the audio is too noisy (a grill, a fan):
fall back to clock sync and mark the clip for a check by eye.
"""
import argparse, json, subprocess, sys
import numpy as np
from scipy.signal import butter, sosfiltfilt

SR = 8000


def load(path, start=None, dur=None):
    cmd = ["ffmpeg", "-nostdin", "-v", "error"]
    if start is not None:
        cmd += ["-ss", f"{max(0.0, start):.3f}"]
    if dur is not None:
        cmd += ["-t", f"{dur:.3f}"]
    cmd += ["-i", path, "-vn", "-map", "0:a:0", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    a = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
    if len(a) == 0:
        sys.exit(f"no audio read from {path}")
    sos = butter(4, [150, 3800], btype="band", fs=SR, output="sos")
    return sosfiltfilt(sos, a - a.mean())


def gcc_phat(a, b):
    n = 1 << int(np.ceil(np.log2(len(a) + len(b))))
    R = np.fft.rfft(a, n) * np.conj(np.fft.rfft(b, n))
    R /= np.abs(R) + 1e-12
    return np.fft.irfft(R, n)[: len(a) - len(b) + 1]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a_cam")
    ap.add_argument("b_cam")
    ap.add_argument("--fps", type=float, default=24000 / 1001, help="A cam frame rate (default 23.976)")
    ap.add_argument("--predict", type=float, help="expected B start inside A, seconds")
    ap.add_argument("--window", type=float, default=12.0, help="search +/- this many seconds around --predict")
    ap.add_argument("--max-b", type=float, default=60.0, help="use at most this many seconds of B (long clips)")
    args = ap.parse_args()

    b_skip = 0.0
    b = load(args.b_cam, dur=None)
    if len(b) > args.max_b * SR:  # a long B clip: correlate a middle slice and add its offset back
        b_skip = min(30.0, (len(b) / SR - args.max_b) / 2)
        b = b[int(b_skip * SR): int((b_skip + args.max_b) * SR)]
    if args.predict is not None:
        a0 = args.predict + b_skip - args.window
        a = load(args.a_cam, start=a0, dur=2 * args.window + len(b) / SR)
        a0 = max(0.0, a0)
    else:
        a0 = 0.0
        a = load(args.a_cam)
    if len(a) <= len(b):
        sys.exit("A audio is shorter than B in the search range; widen --window or drop --predict")

    c = gcc_phat(a, b)
    i = int(np.argmax(c))
    guard = int(0.025 * SR)
    rest = c.copy()
    rest[max(0, i - guard): i + guard] = -np.inf
    conf = float(c[i] / max(np.max(rest), 1e-12))
    off = a0 + i / SR - b_skip
    print(json.dumps({
        "b_starts_in_a_sec": round(off, 4),
        "b_starts_in_a_frames": round(off * args.fps),
        "confidence": round(conf, 2),
        "verdict": "exact" if conf >= 2 else ("probable" if conf >= 1.5 else "unreliable, use clock sync"),
    }))


if __name__ == "__main__":
    main()
