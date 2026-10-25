# /// script
# requires-python = ">=3.9"
# dependencies = ["numpy", "scipy"]
# ///
"""Find held vowels ("ăăă", "uhhh", a stretched "andddd") in a talking clip.

Speech-to-text hides most of these inside the word before them, so searching
the transcript for "um" finds almost nothing. A held vowel is acoustic: at
least --min-ms of voiced, low-frequency, low zero-crossing audio whose
spectrum barely changes from one 30 ms step to the next.

    uv run held_vowels.py take.mp4 --fps 23.976
    uv run held_vowels.py take.mp4 --from 1200 --to 4800

Prints JSON segments in the clip's source frames, plus a suggested cut that
keeps the first 3 frames (so the word before it still ends naturally). On real
footage it found 4 of the 5 ums an editor cut by hand. It also flags sung or
deliberately drawn-out words, so treat the list as candidates to check, and
never cut a short real word just because it is a vowel ("a", "e", "am" are
words in Romanian).
"""
import argparse, json, subprocess
import numpy as np

SR = 16000
HOP, WIN = 160, 512   # 10 ms hop, 32 ms window


def load(path):
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", path, "-vn", "-map", "0:a:0",
                          "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def melfb(n=40, nfft=WIN, lo=80, hi=5000):
    m = lambda f: 2595 * np.log10(1 + f / 700)
    im = lambda x: 700 * (10 ** (x / 2595) - 1)
    pts = im(np.linspace(m(lo), m(hi), n + 2))
    bins = np.floor((nfft + 1) * pts / SR).astype(int)
    fb = np.zeros((n, nfft // 2 + 1))
    for i in range(n):
        a, b, c = bins[i], bins[i + 1], bins[i + 2]
        fb[i, a:b] = (np.arange(a, b) - a) / max(1, b - a)
        fb[i, b:c] = (c - np.arange(b, c)) / max(1, c - b)
    return fb


def steady_segments(a, thr=0.06, min_ms=250, over_db=12, lag=3):
    n = (len(a) - WIN) // HOP
    out = []
    fb = melfb()
    f = np.fft.rfftfreq(WIN, 1 / SR)
    chunk = 20000  # frames per block, keeps memory flat on long takes
    feats = []
    for c0 in range(0, n, chunk):
        idx = np.arange(WIN)[None, :] + HOP * np.arange(c0, min(n, c0 + chunk))[:, None]
        fr = a[idx]
        S = np.abs(np.fft.rfft(fr * np.hanning(WIN), axis=1)) ** 2
        M = np.log(S @ fb.T + 1e-10)
        e = 10 * np.log10(S.sum(1) + 1e-12)
        zc = (np.diff(np.sign(fr), axis=1) != 0).mean(1)
        low = S[:, f < 1000].sum(1) / (S.sum(1) + 1e-12)
        feats.append((M, e, zc, low))
    M = np.concatenate([x[0] for x in feats]); e = np.concatenate([x[1] for x in feats])
    zc = np.concatenate([x[2] for x in feats]); low = np.concatenate([x[3] for x in feats])

    Mn = M - M.mean(1, keepdims=True)
    Mn /= np.linalg.norm(Mn, axis=1, keepdims=True) + 1e-9
    d = np.ones(len(M))
    d[lag:] = 1 - (Mn[lag:] * Mn[:-lag]).sum(1)
    floor = np.repeat([np.percentile(e[max(0, i - 1500): i + 1500], 10) for i in range(0, len(e), 100)], 100)[: len(e)]
    ok = (e - floor > over_db) & (d < thr) & (zc < 0.12) & (low > 0.6)

    i = 0
    while i < len(ok):
        if ok[i]:
            j, gap = i, 0
            while j < len(ok) and (ok[j] or gap < 3):
                gap = 0 if ok[j] else gap + 1
                j += 1
            j -= gap
            if (j - i) * HOP / SR * 1000 >= min_ms:
                out.append(((i * HOP + WIN / 2) / SR, (j * HOP + WIN / 2) / SR))
            i = j + 1
        else:
            i += 1
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("clip")
    ap.add_argument("--fps", type=float, default=24000 / 1001)
    ap.add_argument("--min-ms", type=int, default=250)
    ap.add_argument("--min-frames", type=int, default=10, help="only suggest a cut for holds this long")
    ap.add_argument("--from", dest="start", type=int, default=0)
    ap.add_argument("--to", dest="end", type=int)
    args = ap.parse_args()

    a = load(args.clip)
    s0 = int(args.start / args.fps * SR)
    s1 = int(args.end / args.fps * SR) if args.end else len(a)
    segs = steady_segments(a[s0:s1], min_ms=args.min_ms)
    rows = []
    for t0, t1 in segs:
        f0 = args.start + round(t0 * args.fps)
        f1 = args.start + round(t1 * args.fps)
        rows.append({"start": f0, "end": f1, "frames": f1 - f0,
                     "suggested_cut": [f0 + 3, f1] if f1 - f0 >= args.min_frames else None})
    print(json.dumps({"fps": args.fps, "holds": rows}))


if __name__ == "__main__":
    main()
