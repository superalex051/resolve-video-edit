# Long form YouTube playbook (16:9)

The reference edit: a 7.5 minute, two camera cooking video with an overhead cam, dialogue in Romanian, English captions burned in. It took a week and seven exports because each lesson was learned live; this order avoids most of that. Technique details are in `techniques.md`, API recipes in `resolve-api.md`.

## Shooting notes to pass on (if the editor asks before the shoot)

- Put the lav receiver on the A cam. B cam audio is for sync only.
- A clap at the start of each take; note the B cam's clock offset (cameras drift, ours was 80 minutes off).
- An overhead or wide locked-off camera covers silent process shots and hides jump cuts.
- Shoot b-roll 16:9 at 4K: it cuts into the long form and still crops to 9:16 for reels.

## 1. Probe and log

- Footage per camera folder, a Resolve bin per camera, one 16:9 3840x2160 timeline at the camera rate, named after the shoot.
- ffprobe every clip (`short-form.md` step 1 lists what to check). Note which camera carries the dialogue, which is B cam, overhead, b-roll. Camera XML sidecars (Sony `M01.XML`) give each clip's creation time.
- Contact sheet every clip so you know what each one shows.

## 2. Transcribe

Resolve transcription per dialogue take, language forced. faster-whisper per take as the um detector only. Details: `techniques.md`, Transcription. Numbers the camera cannot show (a scale reading) come from the audio: transcript plus a sanity check (15 × 75 g = 1.1 kg).

## 3. Sync B cam

Clock offset first, then `scripts/sync_gcc.py` in a ±12 s window around the clock prediction. Confidence 2+ is frame exact. Clips where loud steady noise (a grill, a fan) defeats the waveform keep clock sync and get a distinct clip color (orange) so the editor can nudge them by eye. Details: `techniques.md`, Sync.

## 4. Cut plan as data, then build

- Write the cut as a data file first: keeps, drops, beats, b-roll anchors per take. Then build with `AppendToTimeline`, which places exact source ranges at exact frames and never ripples.
- Track layout that worked:

| Track | Content |
|---|---|
| V1 / A1 | A cam with the dialogue |
| V2 | Synced B cam angles, video only (`mediaType: 1`) |
| V3 | Overhead cam |
| V4 | Unsynced b-roll over the lines it illustrates |
| V5 and up | Graphics, zoom generators, captions (one track each) |
| A2 | Music |
| A3 and up | Sound effects |

- **Long form keeps every line** (reels cut harder). Pauses and ums are cut the tight way (`short-form.md` step 4). Silent process (slicing, grinding) stays as short beats of up to 3 s, only where B cam or overhead covers it and the audio there has no chatter.
- If the editor applies per-clip gain or effects on the dialogue clips, re-apply them on every new piece.
- Drop crew directions, retakes, chatter. List what you dropped, with times, so the editor can bring anything back.
- A marker at each section start, named after the section. These become chapters.
- Open with b-roll over the first few seconds if the start has jump cuts.

## 5. The editor's review

The editor watches and leaves notes as timeline markers (M, type the note, a duration for ranges). Read every marker, tell theirs from yours by name rather than color, read clip markers too, and reply with the timecode and a plan per note before touching anything.

## 6. B-roll

50% speed, Optical Flow, Enhanced Better, slot kept. Save, re-read the source range, verify in the final render. To cover a lens edge or a gap, put a matching shot on the B cam track and copy the grade from the same clip elsewhere. Details: `techniques.md`, B-roll.

## 7. Music

One instrumental per group of sections, so the music turns when the topic does; each cut to its exact section length. About 20 dB under the dialogue. Alternates on a disabled track. When the editor locks the music track, unlock, edit, relock. Details: `techniques.md`, Music.

## 8. Color

The editor grades one reference section. You match the rest by measurement, on an unused node, after backing up the project; skin on faces, white balance on whites; review every shot on contact sheets. Details: `techniques.md`, Color. Stabilize handheld close-ups (`TimelineItem.Stabilize()`).

## 9. Graphics

Callouts tracked to the subject, list panels, number cards, a price card. Each on its own track as a copy of the shot with its own Fusion comp outputting only the graphic. Every on-screen number checked against the real source (menu, price list). Details: `techniques.md`, Graphics.

## 10. Zooms

As in short form, plus: list or marker shots ease in and out at 0.1, b-roll zooms in linearly at 0.05 to 0.1, no zoom on shots carrying tracked graphics. The insert goes to the edit page's destination track, which only the editor can set (one click). Details: `techniques.md`, Zooms.

## 11. Captions

Text from the transcript (translated if needed), timing from forced word alignment, built as Text+ in an emptied duplicate and merged by DRT. Collect the lines you are unsure of for the editor to check by ear. Details: `techniques.md`, Captions.

## 12. Cold open (decide this before the first export)

The best performing food and process channels sell the whole video in the first 20 to 25 seconds before any process starts. A structure that worked, built only from footage already shot:

1. **0 to 3 s, the payoff:** the most satisfying moment (the cut, the juice, the reveal) with its own sound up.
2. **3 to 6 s, the premise** in the speaker's own words: a curiosity line ("I wanted to show you what you don't eat").
3. **6 to 14 s, flash-forward montage:** 1 to 1.5 s per shot, a stat card and a whoosh on each.
4. **14 to 17 s, the stakes:** the line that says what can go wrong or why it matters.
5. **17 to 19 s, a title sting** with a music hit, then the video starts.

Give it its own intro music and sound design. Tease the payoff again at chapter breaks if the video runs long, and pay it off later. Build it without rippling: `resolve-api.md`, Adding time at the head.

## 13. Sound effects on graphics

A soft pop on every text landing, an airy whoosh as a panel slides, a short swish per callout line, a light swoosh under zooms into graphics, the natural sound (sizzle) under its shots. Take the frames from the comps' keyframes so every sound lands on its graphic.

## 14. Chapters

Markers on chapter frames, first at 0:00, each 10 s or longer, at least three. Write the description list from the markers after the cold open shifts everything.

## 15. Export and loudness

- QuickTime H.265 Main10 3840x2160 (or the editor's delivery spec), AAC, whole timeline, to `<shoot>/Exports/<name> vN.mov`. Wait on the render job status, not the file size.
- Measure loudness and true peak. Mixes often land around -18 LUFS with voice spikes over 0 dBTP, which can crackle after YouTube's re-encode.
- Level a copy with `scripts/loudnorm_copy.sh` (picture copied). -17 LUFS / -1.5 dBTP worked well; -14 is also fine. YouTube plays everything at about -14.
- Verify the final file: duration, loudness, peak, and a frame check of every shot the editor named in their notes. Restore the Deliver page.

## 16. Thumbnail and the A/B test

- Study a reference channel's last 50 thumbnails first. Patterns from a top food channel: the face looking into the lens with one clear expression, the hero food biggest and held toward the lens, 0 to 2 words, bright and sharp everywhere.
- Clean frames: grab stills with caption and graphics tracks switched off, one still per call, tracks back on after.
- An image model can build the hero image from real frames (face and food as references); fix the food from real frames when the model invents it, keep the real face. Type in a design tool: one heavy font, one accent color, a dark stroke. 1280x720, under 2 MB.
- YouTube Studio's Title and thumbnail test takes three pairs. Make each a different hypothesis so the result teaches something: face + curiosity, food only, versus. Record which won.

## 17. Upload kit

A text file next to the exports with: the file to upload (keep this line on the latest version), the three title and thumbnail pairs, the description (first two lines carry it; links; chapters; a line in the video's language; three hashtags), tags, category, audience, language, captions note, and a pinned comment that asks a question. The editor uploads and schedules.

## 18. Reels from the long form

Each chapter usually holds one reel. Open each on its strongest moment, crop 9:16 from the 4K, cut harder (30 to 40 s), about one a day, the cold open first as a Short. Follow `short-form.md`.
