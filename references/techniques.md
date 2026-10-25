# Techniques

How each step is done. Read the section you need.

Contents: Transcription · Sync · Ums and pauses · B-roll · Zooms · Color · Graphics · Captions · Music · Sound effects · Loudness

## Transcription

- **Resolve's own transcription gives the best timings** (it matched the picture where Whisper put whole lines 20 s early, looped words over foreign speech, and translated takes into English):

```python
project.SetSetting("transcriptionLanguage", "ro")   # a language code; "Romanian" returns False
try:
    clip.ClearTranscription()
    clip.TranscribeAudio(False)                     # blocking, about 10 to 20 s per clip
    tx = clip.GetTranscription()                    # segments and words with timecodes in the clip's own TC
finally:
    project.SetSetting("transcriptionLanguage", "auto")
json.dump(tx, open(path, "w", encoding="utf-8"), ensure_ascii=False)
```

- On "auto", Resolve can misdetect a language and return nonsense, so always force it for anything but English. Write files as UTF-8 (diacritics fail in ASCII sandboxes).
- Resolve's per-word times can collapse on fillers. Cross-check cut points against the audio (`scripts/pauses.py`).
- **faster-whisper large-v3-turbo** (`compute_type int8`, CPU is fine) is the um detector and a second opinion on garbled words. Give it a prompt full of fillers so it writes them out, word timestamps on, VAD off, `condition_on_previous_text=False`.
- Create Subtitles from Audio for non-English languages needs Extended Language Support enabled in Resolve; without it Resolve silently translated Romanian into English.

## Sync

1. **Clock offset.** Each camera's metadata gives a creation time (Sony XML `CreationDate`). B start in A ≈ (B time − A time − clock offset). Find the clock offset once from one clip pair you sync by hand.
2. **Waveform.** `scripts/sync_gcc.py A.mp4 B.mp4 --predict <seconds> --window 12`. GCC-PHAT on 8 kHz mono, 150 to 3800 Hz. A long B clip is correlated from a middle slice.
3. **Confidence** = top peak / next peak more than 25 ms away. 2+ is frame exact; under 1.5 keep the clock estimate (±0.5 s) and color the clip so the editor can nudge it.
4. For one or two long takes, Resolve's own Auto Align works: stack A and B at the same record frame, then

```python
timeline.AutoAlignClips([vA, vB, aA, aB], {"SyncUsing": resolve.AUTO_ALIGN_CLIPS_USING_WAVEFORM,
                                           "UseTrack": resolve.AUTO_ALIGN_CLIPS_WAVEFORM_TRACK_AUTOMATIC})
```

B's new start minus A's start is the offset. Then cut B video-only over A so only the dialogue mic plays.

## Ums and pauses

- `scripts/pauses.py` gives the keep ranges with every pause of 5+ frames cut (reels) or 14+ (looser long form if the editor prefers).
- `scripts/held_vowels.py` finds held vowels. Cut holds of 10+ frames from their 4th frame to the end.
- From Whisper words: a word of 3 letters or fewer timed at 15+ frames is a stretched hesitation (keep its first 5 voiced frames). An 8 to 20 frame voiced run with little word coverage after 10+ silent frames is an orphan um. Count Resolve's words as coverage too, because Whisper drops whole lines over loud background.
- Never treat real short words as fillers (Romanian "am", "e", "a" are words).
- Hooks and visual beats keep their own pacing.

## B-roll

```python
item.SetSpeed({"Percentage": 50.0, "RippleTimeline": False})   # slot length kept, half the source frames play
item.SetProperty("RetimeProcess", resolve.RETIME_OPTICAL_FLOW)
item.SetProperty("MotionEstimation", resolve.MOTION_EST_ENHANCED_BETTER)
```

- After `SetSpeed`, save, then re-read `GetSourceStartFrame()` / `GetSourceEndFrame()`: on one edit Resolve anchored the slowed range to the end after the save (it played the second half of the source, not the first). Check the frames in the final render.
- A clip will not get longer through `SetSpeed` (it keeps its slot). Cover a long line with a second shot.
- `CopyGrades` copies the grade but not the transform; copy `Pan`, `Tilt`, `ZoomX`, `ZoomY`, crop with `GetProperty`/`SetProperty`.

## Zooms

- A "Smooth Zoom" style Fusion generator per shot, on an empty top track, spanning the shot exactly.
- Insert recipe: set the playhead to the shot start, `SetMarkInOut(off, off + dur - 1)` (relative frames), `InsertFusionGeneratorIntoTimeline(name)`, left to right. The insert lands on the edit page's **destination track**, which the API cannot set: ask the editor to move the destination patch to the empty zoom track (one click), then test one insert. It fails (returns None) on a track with items to the right of the playhead.
- Set the generator's inputs on the Media page (`resolve.OpenPage("media")`, never while the viewer shows a Fusion clip): direction, scale, easing via `comp.GetToolList(False)`.
- Every generator insert drags the timeline markers to its right by its length. Place markers last, or save and re-place them.

## Color

The editor grades a reference section; you match the rest.

1. **Back up** the project (`ExportProject` with stills, a `.drp`) and each grade you will touch (DRX) before changing anything.
2. **Measure, do not eyeball.** Render 720p, cut per shot, measure: blacks (10th percentile luma), midtones (median), white balance from bright, low-chroma pixels (R/G and B/G), saturation. Once captions are burned in, exclude the bottom 20% (a colored caption box reads as skin).
3. **Fix per section and camera** with a CDL on a node the editor does not use (a spare node before the LUT). The API cannot add nodes, and `SetCDL` replaces that node's values entirely; writing an identity CDL into the editor's white balance node once dropped blue by 20%. Test a node with an identity CDL against a still before using it. Restore any node with `Graph.ApplyGradeFromDRX(path, 0)`.
4. **Skin on the face, white balance on the whites.** Whole-frame saturation lies (white walls and raw meat push it), and a loop on it made faces orange. Find faces (OpenCV Haar cascade, check its boxes) and move only saturation toward the reference camera's face in the same scene. Never pull face warmth with a red offset: every neutral turns teal. Do not let a loop cut saturation hard on food.
5. **Pieces of one clip share one grade.** Copy from the good piece with `CopyGrades`.
6. **Review every shot** on labelled contact sheets (shot number, clip, time) from a full render; fix, re-render, repeat. Verify every shot the editor named on the final export, before vs after vs reference.
7. Gallery stills can silently stop exporting images; 1-frame renders from the Deliver page are a reliable measuring tool (restore Deliver after).

## Graphics

- Each graphic on its own track as a **copy of the shot** with its own Fusion comp; MediaOut gets only the graphic over a transparent background, so the editor's grade on the footage below never touches it.
- **Tracking:** OpenCV Lucas Kanade optical flow on features around the anchor, median motion, 7-frame smoothing, one Transform keyframe per frame. Build the graphic around the centre and let the Transform carry it, so the layout stays editable.
- **Panels:** a frame-size Solid Background with a soft RectangleMask, slid in by a Transform.
- **Keyframe handles are offsets from the key** (`{1: -dt/3, 2: 0}`), not absolute points. Absolute ones made a 0 to 1 fade overshoot to 1.55 and threw slides off screen while the settled frames looked fine; check values between keys.
- Background `Type` is a string ("Solid", "Horizontal"); a number renders nothing and leaves the tool broken, so make a fresh one.
- `AddModifier` keys the input's default at the current frame; delete strays with `spline.DeleteKeyFrames(t)`.
- A comp built by script can render stale (the raw copy clip) until its MediaOut input is re-linked. When a render shows the raw copy, that is the cause, not the editor changing things.
- `comp.Render()` can leave Resolve with no current page, after which `DeleteClips` and `SaveProject` silently do nothing. Do timeline edits first, renders last.
- Check graphics with 1-frame Deliver renders; Gallery stills ignore Fusion output.
- A font that is not installed renders blank. Check it exists first.

## Captions

- **Text:** from Resolve's transcript (translated when the audio is another language), house style per `HOUSE.md` or: ALL CAPS, no commas or periods, a question mark only on real questions, names and dish names spelled right. List the lines you are unsure of for the editor to check by ear. Merge flashes under 9 frames into a neighbour.
- **Timing from forced alignment**, because Whisper stretches a phrase's first word back into the silence and captions pop up early. Render a dialogue-only file (switch other audio tracks off on the Edit page; `SetTrackEnable` does nothing on the Deliver page), then

```bash
whisperx dialogue.wav --model large-v3-turbo --language ro --compute_type int8 --device cpu
```

  In = first aligned word − 2 frames, out = last word + 8 frames, at least 20 frames on screen, bridge gaps of 10 frames or less. The aligner can skip a short first word in noise, so never move an in past a clear burst of speech.
- **SRT times are absolute timeline timecode.** Resolve reads an SRT as source timecode; anything before the timeline start (often 01:00:00:00) gets parked at the start and shifts every caption. At 23.976 the timeline frame 86400 is 01:00:03,600 in SRT time, not 01:00:00,000 (NDF timecode runs 0.1% slow): ms = frame × 1001 / 24. Import with `ImportMedia([path])`; after importing, check the SRT clip's start TC equals the first caption's timeline TC. `AppendToTimeline` with an SRT ignores recordFrame; do not use it. The editor right-clicks the SRT > Insert Subtitles into Timeline Using Timecodes, then drags a subtitle style on.
- **Burned-in Text+ captions** (more control over the look): build in an emptied duplicate and merge by DRT (`resolve-api.md`). A box behind the text is Text+ element 4 Border Fill; its Offset does not scale with the text Size, so re-centre after any size change.

## Music

- Licensed library only; instrumentals tagged no vocals under speech (vocal chops fight words). Register the channel with the library so Content ID claims clear.
- Cut to exact length with the library's edit tool (Epidemic Sound's MCP: `EditRecording` with the target duration in ms, `forceDuration` true, WAV), so the track ends on a real ending.
- **Frame counting:** Resolve can count a WAV's frames at its own or the project rate, not the timeline rate. Read `GetClipProperty("FPS")` and scale `endFrame`, or the music runs short or long and shoves the next clip. Append one music clip per call.
- **Level:** clip `SetProperty("AudioVolume", dB)` so music sits about 20 dB under the raw dialogue loudness (dialogue about -15.5 LUFS, music about -35).
- Alternates on a disabled track; once picked, remove the losers from the timeline and pool and move their files to a `_rejected <genre>` folder.

## Sound effects

- Sources: the library's SFX search. Short glass pops, soft airy whooshes, light swooshes, a boom for title stings, natural sound (sizzle, pour).
- Place from the graphics' keyframes; fade natural sounds in and out (`SetFades` or clip fades).
- Measure true peak after adding impacts.

## Loudness

`scripts/loudnorm_copy.sh in.mov "out (-17 LUFS).mov" -17 -1.5`: two-pass, linear, picture copied. YouTube long form -17 to -14 LUFS, Reels and Shorts -14, true peak at or under -1 dBTP. Measure the output; very short or very quiet clips can miss the target.
