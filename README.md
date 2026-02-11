# Concert Splitter

A CLI tool for splitting long bootleg concert recordings into individual tracks. Designed for messy, lively shows with no chapters — audience recordings, soundboard boots, whatever.

Downloads audio from YouTube, transcribes everything (banter, lyrics, crowd noise) with timestamps, detects energy dips between songs, and outputs files for human + AI review. You decide where to cut, then the tool splits and tags CD-ready WAV files.

## How It Works

```
YouTube URL
     │
     ▼
  yt-dlp          →  concert.flac (best quality audio)
     │
     ├──────────────────────┐
     ▼                      ▼
  Whisper (GPU)         ffmpeg energy analysis
     │                      │
     ▼                      ▼
  transcript.txt        energy.txt
     │                      │
     └──────┬───────────────┘
            ▼
   You + Claude Code     →  splits.json (track boundaries)
            │
            ▼
   ffmpeg split + tag    →  01 - Song.wav, 02 - Song.wav, ...
```

The key step is the human review. The transcript and energy analysis give you the signal — you and Claude Code figure out the actual cut points.

## Prerequisites

- **Docker Desktop**
- **NVIDIA GPU driver** (latest Windows version — Docker Desktop handles GPU passthrough)

That's it. Everything else runs inside the dev container.

## Getting Started

1. Open this folder in VS Code
2. When prompted, **Reopen in Container** (or Ctrl+Shift+P → "Dev Containers: Reopen in Container")
3. Wait for the container to build (first time includes ~3 GB whisper model download)

## Usage

### Full pipeline (download + transcribe + analyze)

```bash
concert-split run \
  --url "https://youtube.com/watch?v=..." \
  --output output/my-show
```

### Step-by-step

```bash
# 1. Download best-quality audio
concert-split download --url "https://youtube.com/watch?v=..." --output output/my-show/

# 2. Transcribe with Whisper (runs on GPU)
concert-split transcribe --input output/my-show/concert.flac

# 3. Analyze energy levels
concert-split analyze --input output/my-show/concert.flac

# 4. Review transcript.txt and energy.txt
#    Create splits.json (manually or with Claude Code)

# 5. Split into tracks
concert-split split \
  --input output/my-show/concert.flac \
  --splits output/my-show/splits.json \
  --artist "Band Name" \
  --album "Venue, City — Date" \
  --year 1997
```

## Output Structure

Each concert gets its own directory:

```
output/my-show/
├── concert.flac        # downloaded audio (lossless)
├── description.txt     # YouTube video description
├── transcript.txt      # timestamped transcription
├── energy.txt          # volume analysis + detected dips
├── splits.json         # track boundaries (you create this)
└── tracks/
    ├── 01 - Song Name.wav
    ├── 02 - Song Name.wav
    └── ...
```

Track files are **16-bit, 44.1kHz, stereo WAV** — Red Book CD standard, ready to burn.

## splits.json Format

```json
{
  "artist": "Band Name",
  "date": "1997-09-09",
  "venue": "Venue, City, ST",
  "tracks": [
    {"track": 1, "title": "Song Name", "start": "0:00.000", "end": "3:22.500"},
    {"track": 2, "title": "Another Song", "start": "3:22.500", "end": "7:45.000"}
  ]
}
```

Timestamps can be in `MM:SS.mmm`, `H:MM:SS.mmm`, or just seconds.

## Tips

- **setlist.fm** is great for finding setlists to cross-reference against the transcript
- The energy dips are a starting point — live concerts often have very short gaps, so trust the transcript more
- If a setlist isn't available, Claude Code can often identify songs from transcribed lyrics
- Use `--model medium.en` for faster (but less accurate) transcription on longer recordings
- Run `concert-split transcribe --device cpu` to force CPU if GPU isn't working

## Tech Stack

- **yt-dlp** — YouTube download
- **faster-whisper** — GPU-accelerated transcription (CTranslate2)
- **ffmpeg** — audio extraction, analysis, splitting
- **mutagen** — ID3 metadata tagging
- **NVIDIA CUDA 12.2** — GPU acceleration (in container)
