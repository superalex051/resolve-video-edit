# Short form playbook (Reels, TikTok, Shorts)

Vertical, usually 20 to 60 seconds, watched muted by most people, judged in the first second. Technique details are in `techniques.md`; API recipes in `resolve-api.md`.

## 0. Brief

- What is the reel, in one line, and what is the hook? If the editor gave a concept (a POV meme, a process, a talking piece), write the shot list with the text cards before cutting.
- Timeline: 2160x3840 (or 1080x1920) at the camera frame rate, named after the reel or the shoot. Several reels from one shoot can share one timeline: back to back, a 48 frame gap between them, a marker per reel named after it, so the editor reviews them in one place.
- Length targets that worked: POV and meme reels 11 to 20 s; talking or process reels 35 to 45 s after the tight cut.

## 1. Probe every clip before proposing it

```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,avg_frame_rate,color_transfer,color_primaries:stream_side_data=rotation -of json clip.mov
```

- **Resolution:** the short side should be at least 2160 px for a 4K reel. Phone "1.5K" copies and proxies look soft; skip them.
- **Frame rate:** 60 or below for normal-speed footage. Files reported as 120 fps can be variable frame rate averaging 30; check `avg_frame_rate`.
- **HDR:** `arib-std-b67` (HLG) or `smpte2084` (PQ) with bt2020 looks washed out in a timeline that is not color managed. Convert per clip with a HLG-to-Rec.709 LUT on node 1, or color manage the timeline (DaVinci Wide Gamut in, Rec.709 Gamma 2.4 out). Flag HDR clips in the shot list.
- **Orientation:** check per clip, never by folder. Action cams record 3:4 portrait (zoom about 1.334 fills 9:16) or 4:3 landscape (zoom about 2.37 fills, showing only the middle 42%). 16:9 4K footage fills 9:16 at zoom about 3.16. Emulate the crop on a frame with ffmpeg before setting Pan so the subject stays in shot.
- **Log footage** (S-Log3 and similar) is flat until graded; that is expected, the editor grades.

## 2. Find the moments

- Contact sheet each clip (`scripts/contact_sheet.sh`). For long point-of-view clips, sample every 1 to 2 seconds and pick windows where the subject fills the frame for the whole cut. Reject windows that land on a shelf, a wall, a fridge door, the floor, motion blur or a camera swing.
- Transcribe talking clips with Resolve, forcing the language for anything not English (`techniques.md`, Transcription).
- **Show the editor a contact sheet of your picks** (start, middle and end frame of each window) before cutting. A bad window caught on paper costs nothing.

## 3. Hook first

- Open on the strongest moment: the bite, the slice reveal, the pull from the smoker, the best line. If the take does not start there, lift a 4 to 5 second teaser from later and put it at the head. If the reel already opens on its best line, say so instead of duplicating it.
- A banner (the premise, e.g. "POV: ...") sits on frame zero for the whole reel when the concept uses one.
- Nothing over 1.5 s in the first three shots of a fast reel.

## 4. The tight talking cut

Learned from an editor re-cutting a 48 s draft to 38 s by hand.

- **Every pause goes**, not only long ones: silences of 5 frames or more are cut, about 2 frames kept after the last word and 2 before the next. Heads 2 frames before the first word, tails 3 after the last (`scripts/pauses.py`).
- **Ums go**: held vowels and stretched short words (`scripts/held_vowels.py`, plus the Whisper check in `techniques.md`). Real short words are not fillers.
- **No silent visual beats on the talking track.** A slice, a lift, a close-up with no speech comes out of the main track and goes back as b-roll over the line it belongs to.
- The editor's own trims in the live timeline always win over your plan.

## 5. B-roll

- On a track above the talking track, over the line it illustrates.
- 50% speed, Optical Flow, Enhanced Better, slot length unchanged (`techniques.md`, B-roll). Verify the frames after saving.

## 6. Smooth zooms

- One zoom per visible shot (a run of the same angle; a jump cut inside it stays one shot), on its own empty track.
- **Direction follows the beat:** IN for hooks, punchlines, reveals, invitations and every b-roll; OUT for a new topic starting, a settle after a bite, lists and the closing line. Two in a row is fine.
- **Amount:** 0.1 for shots of 3 s or more, 0.05 for shorter ones. Linear, no easing, unless `HOUSE.md` says otherwise.
- After any re-cut, rebuild every zoom from the live timeline rather than keeping fragments.

## 7. Text and captions

- **Text is Text+ on the timeline**, editable in the Inspector, never nested title timelines (they dim the viewer with "No frame available for MediaOut1").
- **Cards:** land on the cut, hold at least 0.8 s, two thirds down the frame, two lines at most, full diacritics. Keep text clear of the platform UI (the bottom 20% and the right edge).
- **Captions:** short phrases of 2 to 5 words, ALL CAPS, no commas or periods, a question mark only on a real question, names spelled right. One box style for the whole reel (a saved subtitle template or Text+ preset). Phrases swap on a hard cut.
- Timing and SRT rules: `techniques.md`, Captions.

## 8. Music and sound

- Instrumental, no vocals under speech, from a licensed library (unlicensed songs get muted or claimed on business accounts).
- Cut the track to the reel's exact length so it ends on a real ending; mix about 20 dB under the dialogue.
- Main pick on a "Music" track, an alternate on a disabled "Music alt" track for the editor to compare. Once they pick, remove the loser from the timeline and the media pool.
- Many editors add their own risers, impacts and dings after the music. Keep them, and measure true peak on export: impacts can push it over 0 dBTP. Flag it; do not remix their sound unasked.

## 9. Grade

The editor usually grades. If asked to match shots, see `techniques.md`, Color.

## 10. Export, one file per reel

- From each reel's marker range (check the marker still sits on the reel's first frame).
- H.264 or H.265, 1080x1920 or 2160x3840, AAC 48 kHz, subtitles burned in when captions live on a subtitle track.
- Snapshot and restore the Deliver page around your renders (`resolve-api.md`, Rendering).
- **Verify each file:** ffprobe (size, fps, audio present), a contact sheet at 2 frames a second (banner on frame zero, cards on their cuts, captions present), loudness about -14 LUFS with true peak under -1 dBTP (`scripts/loudnorm_copy.sh ... -14 -1.0` if needed).

## 11. Posting

Write the caption per platform and prepare drafts or scheduled posts in whatever tool the editor uses. The editor approves and publishes. A pattern that worked: the first reel to all platforms at once, the others as Instagram trial reels first, then scheduled on the other platforms over the following days around noon local time.
