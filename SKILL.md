---
name: resolve-video-edit
description: Edit videos in DaVinci Resolve Studio through its scripting API or MCP server, the way a careful assistant editor would. Covers short form (Reels, TikTok, YouTube Shorts) and long form YouTube: probing and logging footage, transcribing, syncing an A cam and B cam, the tight talking cut with pauses and ums removed, b-roll, smooth zooms, color matching across cameras, Fusion graphics, captions, music, sound effects, a cold open, chapters, render, loudness, thumbnails and the upload kit. Use this skill whenever the user wants to cut, edit, re-cut, caption, grade, sync, render or export a video, reel, Short or YouTube video, mentions DaVinci Resolve, a timeline, footage, b-roll, a hook or cold open, or asks to turn a long video into reels, even if they never say "Resolve" or "skill".
---

# Video editing in DaVinci Resolve with an agent

You drive Resolve; the editor decides taste. You do the heavy, measurable work (probing, transcribing, syncing, cut lists, removing pauses and ums, building timelines, matching cameras, timing captions, tracking graphics, rendering, loudness). The editor watches, leaves notes, grades a reference section, picks music and approves anything that goes out.

Everything here was learned on real edits, usually by getting it wrong first. The reasons are given so you can judge edge cases instead of following rules blindly.

## Start of every session

1. **Read `HOUSE.md` in this folder if it exists.** It holds this editor's own rules, paths, styles and delivery settings, and it overrides the defaults below. If the editor corrects you during the session, add the correction to `HOUSE.md` (create it if missing) the moment it happens, with the date and the reason, so the next session does not repeat the mistake.
2. **Connect to Resolve** and confirm the project and timeline the editor named (see `references/resolve-api.md`, Connecting). Work in the timeline they name. Do not create a new timeline unless asked or unless a step below says to work in a duplicate.
3. **Pick the playbook:**
   - Reels, TikTok, Shorts, anything vertical under about 90 s: read `references/short-form.md`.
   - YouTube long form, 16:9, several minutes: read `references/long-form.md`.
   - Both read `references/techniques.md` (how each step is done) and `references/resolve-api.md` (recipes and traps) when they reach a step that needs it.

## Ground rules

These protect the editor's work. Each one exists because breaking it cost hours.

1. **Back up before every pass.** Export the timeline as a `.drt` and save a JSON snapshot of every track (item name, start, end, source in/out, enabled) before you change anything. After the pass, compare every track against the snapshot, not only the one you meant to touch. A title insert once rippled every track of a finished edit even though the other tracks were locked; only the backup saved it.
2. **Re-read the live timeline before every pass.** The editor works between your passes. Diff the timeline against your plan, act on what is there, and name their changes back to them. Never rebuild from your own old cut list.
3. **Never insert titles or generators into the real timeline** until you have proven the insert is safe on that timeline. Build text in an emptied duplicate and merge it in by DRT (`references/resolve-api.md`).
4. **Leave the Deliver page as you found it.** `SetRenderSettings` changes the project's live Deliver settings, and one check render once left audio export off, so the editor's next real export came out silent. Snapshot the settings before you render, restore them after, delete only your own render jobs.
5. **Never overwrite or delete the editor's files.** Render to a new name (`v2`, `v3`). Move rejected material to a `_rejected` folder instead of deleting it.
6. **Keep each Resolve call short.** The MCP `run_script` tool times out after about 10 s, but the script keeps running inside Resolve. Do one heavy thing per call (one still, one import, one render start) and re-read the state after any timeout before trying again.
7. **Show a plan before anything broad.** A step that touches the whole timeline (transcribing all of it, a grade on every clip, a ripple, a re-cut) gets a short plan and the editor's OK first. Say up front what the API cannot do (trim, split, move between tracks, set the destination patch) and hand those clicks to the editor.
8. **Keep scripts, plans and check renders in the project folder** (for example `<project>/edit-tools/<shoot>/<date>/`), not a temp folder that a restart wipes.
9. **Timecodes from the editor** like `6:15:12` mean minutes:seconds:frames from the start of the timeline at 24 fps unless `HOUSE.md` says otherwise: frame offset = (m × 60 + s) × 24 + f.
10. **Report by what shows on screen.** "The b-roll at 6:15 now shows the tongs placing a fourth piece" beats "fixed item 9012". Verify claims on the final render, not on a check render: Resolve sometimes changes things on save.
11. **Nothing gets posted or published by you.** The furthest you go is a file, a draft or a scheduled post the editor approves.

## The scripts in `scripts/`

Run Python ones with `uv run` (dependencies are declared inside), shell ones directly. All read straight from video files.

| Script | What it does |
|---|---|
| `sync_gcc.py A B [--predict s --window 12]` | Where B cam starts inside A cam, by audio (GCC-PHAT). Frame exact when confidence is 2 or more |
| `pauses.py clip [--min-gap 5]` | The ranges to keep in a talking clip with every pause cut, in source frames |
| `held_vowels.py clip` | Candidate held vowels ("ummm", "ăăă") the transcript hides, with suggested cuts |
| `contact_sheet.sh clip out.jpg [cols rows]` | One image of a whole clip, to see what is in it before picking |
| `loudnorm_copy.sh in out [-17] [-1.5]` | Two-pass loudness levelling of a finished export, picture copied untouched |

## Order of work, at a glance

Short form: probe, transcribe, pick the hook, contact sheet of picks, tight cut, b-roll, zooms, text and captions, music, editor's SFX and grade, export per reel, verify, drafts for posting.

Long form: probe and log, transcribe, sync B cam, cut plan, first cut, editor's notes as markers, b-roll, music, color match after the editor's reference grade, graphics, zooms and stabilization, captions, cold open, graphics SFX, chapters, export and loudness, thumbnail and A/B titles, upload kit, then reels cut from it.

Plan the hook or cold open before the first export, not after. On the edit this skill came from, adding the intro last caused four extra exports.
