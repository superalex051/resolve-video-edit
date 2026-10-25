# Resolve API recipes and traps

Tested on DaVinci Resolve Studio 21.1. Resolve adds features often: call the MCP's "what's new" tool or read the Scripting `README.md` before trusting anything here or in your own memory.

Contents: Connecting · Snapshot and backup · Placing clips · Ripple and head inserts · Editing through DRT · Titles in a duplicate · Adding time at the head · Rendering · Stills and frame checks · What the API cannot do · Traps

## Connecting

- Studio only. In Resolve: Preferences > System > General > **External scripting using: Local** (on None, connections fail with no error), then **File > Setup AI Assistants**, which registers Resolve's MCP server with Claude Code and Claude Desktop. A session only sees MCP servers that existed when it started; start a new one after setup.
- Prefer the MCP `run_script` tool. It times out after about 10 s while the script keeps running in Resolve: keep each call to one heavy action and re-read state after a timeout. Use the unsafe variant only when a script must write files.
- Fallback when the MCP hangs, from a shell:

```bash
export RESOLVE_SCRIPT_API="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
export RESOLVE_SCRIPT_LIB="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
export PYTHONPATH="$RESOLVE_SCRIPT_API/Modules"
python3 -c 'import DaVinciResolveScript as d; r=d.scriptapp("Resolve"); print(r.GetVersionString())'
```

  (Windows and Linux paths are in the same README.) `pgrep` may not see the process; the API still connects.

## Snapshot and backup

```python
tl = project.GetCurrentTimeline()
assert tl.GetName() == EXPECTED            # never act on the wrong timeline
tl.Export(path_drt, resolve.EXPORT_DRT)    # full backup, re-importable
snap = {}
for kind in ("video", "audio", "subtitle"):
    for t in range(1, tl.GetTrackCount(kind) + 1):
        snap[f"{kind}{t}"] = [(i.GetName(), i.GetStart(), i.GetEnd(), i.GetSourceStartFrame(), i.GetSourceEndFrame())
                              for i in (tl.GetItemListInTrack(kind, t) or [])]
```

Compare every track against the snapshot after each pass. Back up grades as DRX and the whole project as `.drp` (`ExportProject`) before color work.

## Placing clips

```python
media_pool.AppendToTimeline([{
    "mediaPoolItem": clip, "startFrame": src_in, "endFrame": src_out,   # source frames
    "trackIndex": 2, "recordFrame": tl_frame,                            # absolute timeline frame
    "mediaType": 1,                                                      # 1 = video only, 2 = audio only
}])
```

- Places an exact range at an exact frame and never ripples. Append one clip per call when a mistake could shove the next one.
- When the clip rate equals the timeline rate, `endFrame` is exclusive and lands frame exact. When it differs (30 fps phone clip in a 23.976 timeline, a WAV), Resolve may count in the clip's rate or the project's: read `GetClipProperty("FPS")`, compute, and verify the placed item's length after appending. Getting this wrong leaves one-frame black gaps or music that runs 20% short.

## Ripple and head inserts

There is no ripple insert call. Workaround: `SetMarkInOut(0, n-1)` at the head and `InsertGeneratorIntoTimeline("Solid Color")` ripples every unlocked track by n; verify every track moved by exactly n, delete the generator without ripple, fill the gap. Markers drift; re-place them. For a cold open on a finished timeline use the DRT route below instead, which is safer.

## Editing through DRT

The API cannot trim, split or move timeline items, but an exported `.drt` is XML you can edit and re-import:

- Each clip sits in its own `<Element>` wrapper inside a track's `<Items>`. Adding a clip without its own wrapper makes Resolve read only one of the pair, silently.
- To add a clip: copy a neighbour, give it fresh DbIds, wrap it in its own `<Element>`, set `<Start>` and `<Duration>`.
- To retime: change `<Start>` / `<Duration>` and the source in.
- `ImportTimelineFromFile(path)` with **no options** for a DRT (`timelineName` makes it return None); the new timeline is named after the file. Delete a timeline and import in **separate** calls.
- DRT import keeps grades, Fusion comps, generators, stabilization, markers and track locks. The imported timeline is a new object: render jobs must be made fresh from it.
- After import, prove items, markers and a few rendered frames match before renaming it to the working name. Keep the old one as "before <change> (backup)".

## Titles in a duplicate

Inserting a Text+ title with In/Out marks on a full timeline rippled and split every track on a finished edit, locks or not. Safe route:

1. Back up (DRT + snapshot).
2. `DuplicateTimeline`, switch to the copy, assert its name, delete every item in it.
3. Put a throwaway title past the end so marks have room (`SetMarkInOut` fails on an empty timeline).
4. Insert titles in time order (`InsertFusionTitleIntoTimeline("Text+")` after `SetCurrentTimecode` + `SetMarkInOut`), set text and style through `item.GetFusionCompByIndex(1)` (`StyledText`, `Font`, `Size`, `Center`). Delete the filler.
5. Add an empty named track to the real timeline (`AddTrack` is safe).
6. Export both as DRT, move the copy's title `<Items>` into the empty track's `<Items/>` with fresh DbIds, import, verify, rename.

Title presets: a `.setting` macro in `Fusion/Templates/Edit/Titles/<folder>/` whose output is the TextPlus directly, with no MediaOut node inside (an extra MediaOut clashes with the one Resolve wraps around every title). New presets load only after a Resolve restart.

## Adding time at the head

Work in a duplicate. Stage the new pieces past the timeline end with `AppendToTimeline`, copy each source item's grade (`CopyGrades`) and transform (Pan, Tilt, Zoom, crop) onto the new pieces, export the DRT, shift every `<Start>` (staged pieces to the head, everything else plus N), add title copies in their own `<Element>`, import, verify every track against a snapshot, re-add markers plus N (the DRT keeps them at old frames) and a chapter at 0, re-lock tracks.

## Rendering

```python
# snapshot the editor's Deliver state: a throwaway job reads back the live settings
jid = project.AddRenderJob(); before = [j for j in project.GetRenderJobList() if j["JobId"] == jid][0]
project.DeleteRenderJob(jid)
try:
    project.SetRenderSettings({"SelectAllFrames": False, "MarkIn": a, "MarkOut": b, "TargetDir": d,
                               "CustomName": name, "ExportVideo": True, "ExportAudio": True})
    project.SetCurrentRenderFormatAndCodec("mov", "H265")
    jid = project.AddRenderJob(); project.StartRendering([jid])
    while project.IsRenderingInProgress(): time.sleep(2)        # or poll GetRenderJobStatus(jid)
finally:
    # restore format, codec, audio codec, resolution, range, name, folder from `before`, verify with
    # another throwaway job, delete your own job ids only
    ...
```

- Wait on `GetRenderJobStatus`, not on the file's size or duration (a file check stopped early once).
- Resolve will not overwrite an existing file on a network share; use a new name.
- Render only your own job ids. Do not touch the editor's queued jobs.
- Resolve adds a harmless timecode data track to MOV/MP4 exports.

## Stills and frame checks

- `project.ExportCurrentFrameAsStill(path)` after `SetCurrentTimecode` renders the viewer with generators applied, but it has returned stale frames at the wrong size on a timeline whose size differed from the project; verify the image.
- Gallery `GrabStill` + `ExportStills` can silently stop writing images. Grab into a dedicated album and keep one still in it at a time (the still order is not grab order).
- The most reliable check is a 1-frame render from the Deliver page (about 1 s at 1080p), with the Deliver state restored after.
- Clean frames for a thumbnail: disable graphics and caption tracks, grab, re-enable. One still per call; a timeout once left the tracks disabled.

## What the API cannot do

Say so up front and hand these to the editor: trim, split, move an item to another track (only delete and rebuild, which loses grade and stabilization unless copied), switch multicam angles, set the edit page destination patch, set stabilization mode (`Stabilize()` runs the clip's current mode), edit subtitle text (`SetName` returns False on subtitle items), add color nodes, delete gallery albums. For a one-drag job, offer the drag first instead of a scripted rebuild.

## Traps

| Symptom | Cause and fix |
|---|---|
| Resolve freezes after a script | Changing timeline settings or touching a Fusion comp while the viewer shows a Fusion title deadlocks it. Change settings on a fresh launch from the Media page. Recovery: force quit Resolve and its `fuscript` helper, reopen |
| Creating or importing a timeline hangs | Once a Text+ title has been inserted in the session, timeline creation can freeze. Create and import timelines first, insert titles last, or restart Resolve |
| A Text+ preset renders blank | The font is not installed |
| `SaveProject` returns None after a Fusion render | No current page; do edits before renders, ask the editor to click in Resolve or save by hand |
| A re-enabled Fusion clip renders blank | Stale comp; re-link its MediaOut |
| Markers moved | Generator inserts drag markers to their right; re-place markers last |
| `SetTrackEnable(..., True)` returns True but nothing changes | It does nothing on the Deliver page; switch to the Edit page first |
| A slowed clip shows different frames after saving | `SetSpeed` range re-anchored on save; re-read and re-place |
| Captions land early or all at the start | SRT read as source timecode; write absolute timeline timecode |
