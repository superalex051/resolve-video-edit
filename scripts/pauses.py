# /// script
# requires-python = ">=3.9"
# dependencies = ["numpy"]
# ///
"""Find the pauses in a talking clip and print the ranges to KEEP, in frames.

Loudness per video frame from the clip's audio. A frame is speech when it is
more than --over dB above the local quiet floor (10th percentile over +/-30 s,
so a noisy room still works). Every silent run of --min-gap frames or more
between two speech frames is cut, leaving --pad-after frames after the last
word and --pad-before frames before the next one.

    uv run pauses.py take.mp4 --fps 23.976                  # tight talking cut (reels)
    uv run pauses.py take.mp4 --min-gap 14 --pad-after 2 --pad-before 3   # looser

Frames are the clip's own source frames (0 = first frame of the file), so they
go straight into AppendToTimeline startFrame/endFrame. Use --from/--to to limit
the analysis to part of the take. Review the result: a deliberate beat (a bite,
a reveal, a slice) is silent too, and should be kept or reused as b-roll.
"""
import argparse, json, subprocess
import numpy as np

SR = 48000


def frame_db(path, fps):
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", path, "-vn", "-map", "0:a:0",
                          "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
    hop = SR / fps
    n = int(len(a) / hop)
    db = np.empty(n)
    for i in range(n):
        seg = a[int(i * hop): int((i + 1) * hop)]
        db[i] = 10 * np.log10(np.mean(seg * seg) + 1e-12)
    return db


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("clip")
    ap.add_argument("--fps", type=float, default=24000 / 1001)
    ap.add_argument("--over", type=float, default=9.0, help="dB over the quiet floor that counts as speech")
    ap.add_argument("--min-gap", type=int, default=5, help="cut silences at least this many frames long")
    ap.add_argument("--pad-after", type=int, default=2, help="frames kept after a word")
    ap.add_argument("--pad-before", type=int, default=2, help="frames kept before a word")
    ap.add_argument("--min-speech", type=int, default=3, help="ignore speech blips shorter than this")
    ap.add_argument("--from", dest="start", type=int, default=0)
    ap.add_argument("--to", dest="end", type=int)
    args = ap.parse_args()

    db = frame_db(args.clip, args.fps)
    end = min(args.end or len(db), len(db))
    win = int(30 * args.fps)
    step = max(1, int(args.fps))
    floor = np.empty(len(db))
    for i in range(0, len(db), step):
        floor[i:i + step] = np.percentile(db[max(0, i - win): i + win], 10)
    speech = db - floor > args.over

    runs, i = [], args.start
    while i < end:
        if speech[i]:
            j = i
            while j < end and speech[j]:
                j += 1
            if j - i >= args.min_speech:
                runs.append([i, j])
            i = j
        else:
            i += 1
    if not runs:
        print(json.dumps({"keep": [], "cuts": [], "note": "no speech found"}))
        return

    keep = [[max(args.start, runs[0][0] - args.pad_before), runs[0][1]]]
    cuts = []
    for s, e in runs[1:]:
        gap = s - keep[-1][1]
        if gap >= args.min_gap:
            keep[-1][1] = min(keep[-1][1] + args.pad_after, s)
            ns = max(s - args.pad_before, keep[-1][1])
            if ns > keep[-1][1]:
                cuts.append([keep[-1][1], ns])
            keep.append([ns, e])
        else:
            keep[-1][1] = e
    keep[-1][1] = min(end, keep[-1][1] + args.pad_after + 1)

    kept = sum(e - s for s, e in keep)
    print(json.dumps({
        "fps": args.fps,
        "keep": keep,          # [start, end) source frames, end exclusive
        "cuts": cuts,
        "kept_frames": kept,
        "kept_sec": round(kept / args.fps, 2),
        "analysed_sec": round((end - args.start) / args.fps, 2),
    }))


if __name__ == "__main__":
    main()
