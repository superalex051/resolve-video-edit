# resolve-video-edit

A Claude Code skill that edits videos in **DaVinci Resolve Studio** the way a careful assistant editor would: short form (Reels, TikTok, Shorts) and long form YouTube.

It was built from a real week of editing a two camera YouTube video and a batch of reels with Claude driving Resolve. Every rule in it comes from something that went wrong once, and each one says why, so the agent can judge new situations instead of following a checklist blindly.

**You decide taste, the agent does the heavy lifting.** It probes and logs footage, transcribes, syncs B cam to A cam by audio, cuts out every pause and "ummm", builds the timeline, lays b-roll at half speed, adds smooth zooms, matches color across cameras to your reference grade, tracks graphics, times captions to the words, cuts music to length, levels loudness, and writes the upload kit. You watch, leave notes as timeline markers, grade one reference section, pick the music and approve anything that goes out.

## What's inside

```
SKILL.md                     ground rules and which playbook to read
references/short-form.md     reels, TikTok, Shorts, step by step
references/long-form.md      YouTube long form, 18 steps from probe to upload
references/techniques.md     how each step is done (sync, ums, color, captions, music...)
references/resolve-api.md    Resolve scripting recipes and the traps we hit
scripts/sync_gcc.py          where B cam starts inside A cam, by audio, frame exact
scripts/pauses.py            keep ranges for a talking clip with every pause cut
scripts/held_vowels.py       finds held "ummm" / "ăăă" sounds the transcript hides
scripts/contact_sheet.sh     one image of a whole clip
scripts/loudnorm_copy.sh     level an export to -17 or -14 LUFS without re-encoding the picture
HOUSE.example.md             template for your own house rules
```

## Requirements

- **DaVinci Resolve Studio 21.1 or newer** (the scripting API and the built-in MCP server are Studio only)
- **Claude Code** (works in the terminal, desktop app and IDE extensions)
- `ffmpeg`, `python3`, and [`uv`](https://docs.astral.sh/uv/) (the Python scripts declare their own dependencies, so `uv run` installs numpy and scipy on the fly)
- Optional: `faster-whisper` and `whisperx` for um detection and caption timing, a licensed music library (Epidemic Sound has an MCP server), an image model and Figma for thumbnails

## Install

```bash
git clone https://github.com/superalex051/resolve-video-edit.git ~/.claude/skills/resolve-video-edit
```

That makes it available in every Claude Code session on your machine. Update later with `git -C ~/.claude/skills/resolve-video-edit pull`.

Then in Resolve:

1. **Preferences > System > General > External scripting using: Local.** On "None" every connection fails without an error.
2. **File > Setup AI Assistants.** This registers Resolve's MCP server with Claude Code.
3. Start a **new** Claude Code session (a session only sees MCP servers that existed when it started).

## Make it yours

Copy `HOUSE.example.md` to `HOUSE.md` in the same folder and fill it in: where your footage lives, your cameras, your caption look, your music taste, your export settings. The skill reads it first and it overrides the defaults. `HOUSE.md` is gitignored, so pulling updates never touches it.

When you correct the agent ("the captions show up too early", "too teal"), it writes the correction into `HOUSE.md` with the reason, so the next session doesn't repeat it.

## Using it

Just ask in plain words with Resolve open. For example:

> Footage for the new video is in ~/Videos/Pasta shoot (A cam has the lav, B cam is the Sony, overhead is the GoPro). Project "Pasta", timeline "Pasta v1". Probe everything, sync the B cam, and build a first cut with the pauses and ums out. Stop for my review.

> Turn chapters 2 and 4 of the YouTube video into two 35 second reels with a hook up front, zooms and captions.

> Match the B cam and the overhead to my grade on the first two minutes.

The agent backs up the timeline before every pass, re-reads it to pick up your own edits, shows a plan before anything broad, and never posts or publishes anything itself.

## Good to know

- Some things the Resolve API simply cannot do (trim, split, move a clip between tracks, set the destination track). The agent tells you and hands you the one click instead.
- Keep Resolve's viewer off Fusion titles while the agent works on timeline settings; Resolve 21.1 can freeze otherwise (the recovery is in `references/resolve-api.md`).
- Tested on macOS with Resolve Studio 21.1, Sony A6700 / A7C II S-Log3 footage, an Osmo action cam and iPhone HDR clips.

## License

MIT
