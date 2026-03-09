# Concert Splitter

Split bootleg concert recordings from YouTube into tagged, CD-ready WAV tracks — using Claude Code to do the heavy lifting.

## Prerequisites

- **Docker Desktop** with GPU passthrough
- **NVIDIA GPU driver** (you already have this if you have an NVIDIA GPU)
- **Claude Code** installed and authenticated

## Setup

1. Open this folder in VS Code
2. **Reopen in Container** when prompted (or Ctrl+Shift+P → "Dev Containers: Reopen in Container")
3. Wait for the container to build — first time includes a ~3 GB model download

## Usage

Open a terminal in the container and run:

```
claude
```

Then type:

```
/split-concert https://youtube.com/watch?v=...
```

Claude will download the audio, transcribe it, analyze energy levels, and produce a first-pass set of split tracks. This takes a few minutes depending on the length of the recording.

When it's done, you'll get a track list with timestamps and a folder of WAV files at `output/concert/tracks/`. Listen to them — on Windows, the files are at `<this-repo>\output\concert\tracks\` in Explorer.

Tell Claude what to fix:

- "Track 3 starts too late, you cut off the guitar intro"
- "Tracks 5 and 6 are actually one song"
- "There's a song between 2 and 3 you missed"
- "That's not Custom Concern, that's Trailer Trash"

Claude will update the splits and regenerate only the affected tracks. Repeat until it sounds right.

## Output

```
output/concert/
├── concert.flac           # source audio (lossless)
├── transcript.txt         # timestamped transcription
├── energy.txt             # volume analysis + detected dips
├── splits.json            # track boundaries
├── Artist - Album.cue     # CUE sheet for CD burning
└── tracks/
    ├── 01 - Song Name.wav
    ├── 02 - Song Name.wav
    └── ...
```

Tracks are **16-bit, 44.1kHz, stereo WAV** — Red Book CD standard, ready to burn. You also get a CUE sheet with embedded CD-Text, so if you burn the disc with software that supports it (ImgBurn, CDBurnerXP, etc.), your CD player will display the artist, album, and track titles.

## Permissions

Claude Code asks for approval before running shell commands. To keep the process hands-off, the repo ships with [`.claude/settings.json`](.claude/settings.json) which pre-approves the commands Claude needs (`concert-split`, `yt-dlp`, `ffmpeg`, etc.). Review that file before your first run — if you're comfortable with the whitelist, Claude will handle the entire pipeline without prompting you for permission.

## How it works

The `/split-concert` command is a [Claude Code custom slash command](https://docs.anthropic.com/en/docs/claude-code/tutorials#create-custom-slash-commands). The full prompt — including how Claude reads transcripts, picks split points, handles banter, and formats metadata — lives in [`.claude/commands/split-concert.md`](.claude/commands/split-concert.md). Read it if you want to understand the process, tweak the defaults, or change how Claude approaches the task.
