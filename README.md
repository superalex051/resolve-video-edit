<!-- prettier-ignore -->
<div align="center">

# resolve-video-edit

*A Claude Code skill that edits video in DaVinci Resolve Studio the way a careful assistant editor would*

[![Claude Code skill](https://img.shields.io/badge/Claude_Code-skill-D97757?style=flat-square)](https://docs.anthropic.com/en/docs/claude-code)
[![DaVinci Resolve Studio](https://img.shields.io/badge/DaVinci_Resolve_Studio-21.1%2B-233A51?style=flat-square)](https://www.blackmagicdesign.com/products/davinciresolve)
[![Tested on macOS](https://img.shields.io/badge/tested_on-macOS-000?style=flat-square&logo=apple)](#good-to-know)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

[Features](#features) • [Getting started](#getting-started) • [Usage](#usage) • [Make it yours](#make-it-yours) • [What's inside](#whats-inside) • [Good to know](#good-to-know)

</div>

You decide taste; the agent does the heavy, measurable work. It drives Resolve through its scripting API and built-in MCP server to cut short form (Reels, TikTok, Shorts) and long form YouTube, while you watch, leave notes, grade one reference section, pick the music and approve anything that goes out.

It was built from a real week of editing a two camera YouTube video and a batch of reels with Claude driving Resolve. Every rule in it comes from something that went wrong once, and each one says why, so the agent can judge a new situation instead of following a checklist.

> [!IMPORTANT]
> This needs **DaVinci Resolve Studio**. The scripting API and the MCP server are not in the free version.

## Features

- **Two playbooks.** Short form for vertical video under about 90 seconds, and long form YouTube in 18 steps, from probing the footage to the upload kit.
- **The tight talking cut.** Every pause and held "ummm" comes out. Pauses are found by loudness and ums by sound, because a transcript hides most of them inside the word before.
- **Two camera sync.** B cam is placed inside A cam by audio, frame exact when the match is confident, with a clock sync fallback for noisy rooms.
- **Finishing passes.** B-roll, smooth zooms, color matched across cameras to your reference grade, Fusion graphics, captions timed to the words, music cut to length, sound effects, a cold open and chapters.
- **Delivery you can trust.** One file per reel, each checked with ffprobe and a contact sheet, and loudness levelled to -17 or -14 LUFS without re-encoding the picture.
- **Safe with your project.** It backs up the timeline before every pass, re-reads it to pick up your own edits, puts your Deliver page settings back after it renders, and never posts or publishes anything.
- **Learns your style.** Your paths, cameras, caption look and export settings live in one file, and every correction you give lands there with its reason.

## Getting started

### Prerequisites

- [DaVinci Resolve Studio](https://www.blackmagicdesign.com/products/davinciresolve) 21.1 or newer
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code), in the terminal, desktop app or an IDE extension
- `ffmpeg`, `python3` and [`uv`](https://docs.astral.sh/uv/). The Python scripts declare their own dependencies, so `uv run` installs numpy and scipy on the fly.
- Optional: `faster-whisper` and `whisperx` for um detection and caption timing, a licensed music library (Epidemic Sound has an MCP server), and an image model plus Figma for thumbnails

### Install

1. Clone the skill into your Claude Code skills folder:

   ```bash
   git clone https://github.com/superalex051/resolve-video-edit.git ~/.claude/skills/resolve-video-edit
   ```

   It is then available in every Claude Code session on your machine.

2. In Resolve, open **Preferences > System > General** and set **External scripting using** to **Local**.

3. In Resolve, choose **File > Setup AI Assistants**. This registers Resolve's MCP server with Claude Code.

4. Start a **new** Claude Code session. A session only sees MCP servers that existed when it started.

> [!WARNING]
> With external scripting left on **None**, every connection fails without an error message.

To update later:

```bash
git -C ~/.claude/skills/resolve-video-edit pull
```

## Usage

Open Resolve and ask in plain words. A few examples:

> Footage for the new video is in ~/Videos/Pasta shoot (A cam has the lav, B cam is the Sony, overhead is the GoPro). Project "Pasta", timeline "Pasta v1". Probe everything, sync the B cam, and build a first cut with the pauses and ums out. Stop for my review.

> Turn chapters 2 and 4 of the YouTube video into two 35 second reels with a hook up front, zooms and captions.

> Match the B cam and the overhead to my grade on the first two minutes.

Before anything broad (a whole-timeline transcription, a grade on every clip, a re-cut) the agent shows you a short plan and waits for your OK.

### Who does what

| You | The agent |
| --- | --- |
| Name the project, timeline and footage | Probes and logs every clip, transcribes, syncs cameras |
| Leave notes as timeline markers | Builds the cut, removes pauses and ums, lays b-roll and zooms |
| Grade one reference section | Matches the other cameras to it |
| Pick the music | Cuts it to length, adds sound effects, levels loudness |
| Approve the final export | Renders, verifies each file, writes the captions and upload kit |

### Using the scripts on their own

The scripts in `scripts/` read straight from video files and work without Resolve.

| Script | What it does | Example |
| --- | --- | --- |
| `sync_gcc.py` | Where B cam starts inside A cam, by audio | `uv run scripts/sync_gcc.py A_cam.mp4 B_cam.mp4 --fps 23.976` |
| `pauses.py` | The ranges to keep in a talking clip with every pause cut, in source frames | `uv run scripts/pauses.py take.mp4 --fps 23.976` |
| `held_vowels.py` | Held vowels ("ummm", "ăăă") the transcript hides, with suggested cuts | `uv run scripts/held_vowels.py take.mp4 --fps 23.976` |
| `contact_sheet.sh` | One image of a whole clip, each tile stamped with its time | `scripts/contact_sheet.sh clip.mp4 sheet.jpg 6 4` |
| `loudnorm_copy.sh` | Two-pass loudness levelling of a finished export, picture copied | `scripts/loudnorm_copy.sh in.mov "out (-14 LUFS).mov" -14 -1.0` |

> [!TIP]
> `sync_gcc.py` prints a confidence ratio. At 2 or more the match is frame exact. Under 1.5 the audio is too noisy (a grill, a fan), so sync by the cameras' clocks and check that clip by eye.

## Make it yours

Copy the house rules template and fill it in:

```bash
cp ~/.claude/skills/resolve-video-edit/HOUSE.example.md ~/.claude/skills/resolve-video-edit/HOUSE.md
```

`HOUSE.md` holds where your footage lives, your cameras, your caption look, your music taste and your export settings. The skill reads it first, and it overrides the defaults. It is gitignored, so pulling updates never touches it.

When you correct the agent ("the captions show up too early", "too teal"), it writes the correction into `HOUSE.md` with the date and the reason, so the next session doesn't repeat it.

## What's inside

```text
SKILL.md                     ground rules and which playbook to read
references/short-form.md     Reels, TikTok and Shorts, step by step
references/long-form.md      YouTube long form, 18 steps from probe to upload
references/techniques.md     how each step is done: sync, ums, b-roll, color, captions, music, loudness
references/resolve-api.md    Resolve scripting recipes and the traps we hit
scripts/                     sync, pause, um, contact sheet and loudness tools
HOUSE.example.md             template for your own house rules
```

## Good to know

- **Some edits the API cannot do.** Trim, split, moving a clip to another track and a few others have no reliable scripting call. The agent says so up front and hands you the one click instead. The full list is in [`references/resolve-api.md`](references/resolve-api.md#what-the-api-cannot-do).
- **Resolve can freeze after a script.** Changing timeline settings while the viewer shows a Fusion title can deadlock Resolve 21.1. The recovery is in the [traps table](references/resolve-api.md#traps).
- **Your files stay yours.** Renders get a new name (`v2`, `v3`) instead of overwriting, and rejected material moves to a `_rejected` folder instead of being deleted.
- **Tested on** macOS with Resolve Studio 21.1, Sony A6700 and A7C II S-Log3 footage, an Osmo action cam and iPhone HDR clips.
