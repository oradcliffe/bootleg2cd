You are helping the user split a bootleg concert recording into individual tracks. This is a collaborative, taste-based process — the user knows the music and has opinions about where songs start and end. Your job is to do the grunt work (downloading, transcribing, analyzing) and then work together with the user to decide on the cuts.

The YouTube URL is: $ARGUMENTS

## Step 1: Download

Run the download command and wait for it to finish:
```
concert-split download --url "$ARGUMENTS" --output output/concert
```

## Step 2: Transcribe + Analyze (parallel)

Run both of these:
```
concert-split transcribe --input output/concert/concert.flac
concert-split analyze --input output/concert/concert.flac
```

## Step 3: Collaborate on splits

Once transcription and analysis are done, read both files:
- `output/concert/transcript.txt`
- `output/concert/energy.txt`

Also check `output/concert/description.txt` — the video description sometimes has useful info.

Now work WITH the user:
1. Share what you see — summarize the transcript, note where you think songs change based on banter, applause, energy dips, lyric content, etc.
2. Ask the user if they have a setlist (from setlist.fm or memory). If so, use it to match songs to segments.
3. If no setlist, propose song identifications based on lyrics you can pick out from the transcript. The user will know better than you — defer to them.
4. Walk through each proposed boundary together. The user may want to adjust cuts earlier or later based on how they want transitions to feel — some people want clean silence between tracks, others want to keep the crowd noise rolling into the next song. Ask about their preference.
5. Confirm the final track list with the user before writing anything.

## Step 4: Write splits.json

Once the user approves the track list, write `output/concert/splits.json`:
```json
{
  "artist": "...",
  "date": "...",
  "venue": "...",
  "tracks": [
    {"track": 1, "title": "...", "start": "M:SS.mmm", "end": "M:SS.mmm"},
    ...
  ]
}
```

Ask the user for artist, date, and venue if you don't already know.

## Step 5: Split

Run the split command with metadata from the user:
```
concert-split split \
  --input output/concert/concert.flac \
  --splits output/concert/splits.json \
  --artist "..." \
  --album "..." \
  --year ...
```

Let the user know where the finished tracks are and how many were created.
