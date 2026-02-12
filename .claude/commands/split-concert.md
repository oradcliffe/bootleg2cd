You are helping the user split a bootleg concert recording into individual tracks. This is a collaborative, taste-based process — the user knows the music and has opinions about where songs start and end. Your job is to do the grunt work, make a best-guess first cut, and then iterate with the user until the splits feel right.

The YouTube URL is: $ARGUMENTS

## Step 1: Download

Run the download command and wait for it to finish:
```
concert-split download --url "$ARGUMENTS" --output output/concert
```

## Step 2: Transcribe + Analyze + YouTube Comments (parallel)

Run all of these:
```
concert-split transcribe --input output/concert/concert.flac
concert-split analyze --input output/concert/concert.flac
```

Also grab YouTube comments — they often contain track breakdowns, timestamps, and song IDs from fans:
```
yt-dlp --skip-download --write-info-json --write-comments -o "output/concert/comments" "$ARGUMENTS"
```
The comments will be in `output/concert/comments.info.json` under the `"comments"` key. Skim them for timestamps, track lists, or song identifications.

## Step 3: First-pass split

Once transcription and analysis are done, read all three files:
- `output/concert/transcript.txt`
- `output/concert/energy.txt`
- `output/concert/description.txt`
- `output/concert/comments.info.json` (skim the `"comments"` array for track info)

Ask the user for any context that helps: Do they have a setlist? Know the artist/date/venue?

Your primary source of truth is the transcript and energy data — the actual recording in front of you. Do your own analysis first: read the transcript carefully, match lyrics to songs, find the banter boundaries, and build your track list from what you can hear. Internet setlists (setlist.fm, fan sites, etc.) and YouTube comments can be useful as secondary references for song names and ordering, but don't trust them over what the data shows — many posted setlists are wrong, partial, or from a different night on the same tour.

Using the transcript, energy dips, and any setlist/internet research, make your best guess at the full track list with split points. Write `output/concert/splits.json` and immediately run the split:

```
concert-split split \
  --input output/concert/concert.flac \
  --splits output/concert/splits.json \
  --artist "..." \
  --album "..." \
  --year ...
```

The split command handles WAV metadata automatically using INFO chunks (not ID3 — ID3 on WAV breaks players like Windows Media Player). No manual post-processing needed.

Format the album tag as: "Venue City ST M-D-YY" (e.g. "Mercury Theatre Knoxville TN 9-9-97").

Tell the user the tracks are ready to listen to in `output/concert/tracks/`. Show them the track list with timestamps so they can see what you came up with.

## Step 4: Fine-tune together

Now the user listens. They'll come back with feedback like:
- "Track 3 starts too late, there's a guitar intro you cut off"
- "Tracks 5 and 6 are actually one song"
- "There's a song between tracks 2 and 3 you missed"
- "I want more crowd noise at the end of track 4"
- "That's not Custom Concern, that's Trailer Trash"

When they give feedback:
1. Update `output/concert/splits.json` with the adjustments
2. Re-run the split command to regenerate the tracks
3. Let them know which tracks changed so they don't have to re-listen to everything

Repeat this loop as many times as the user wants. This is the part that matters — getting the cuts to feel right is a matter of taste, not math. Defer to the user on what sounds good.

## Notes

- The user is the authority on the music. If they say a split point is wrong, it's wrong.
- Err on the side of keeping more audio rather than less — it's easier to trim than to recover a cut intro.
- Between-song banter and crowd noise go at the **end** of the preceding track, not the start of the next one. If track A ends and there's banter before track B starts, include that banter at the tail of track A so track B opens clean with music.
- That said, let the flavor come through — if there's a quick shout, count-in, or moment that naturally leads into the song, it's fine to leave it at the top of the track. Use your judgment; the goal is that tracks don't open with a minute of dead air, not that every track starts on the first note.
- If a song bleeds into the next without a clear gap (common in live shows), ask the user where they'd like the cut rather than guessing.

### Reading the transcript

The Whisper transcript of a live bootleg will be **mostly wrong on exact words but right on cadence and sound**. Don't expect literal lyrics — expect phonetic approximations. For example, "Cowboy Dan goes to the reservation, drinks and gets mean" might come through as "goes to the red face and grins against me." The syllable count and vowel sounds are close even when the words are completely wrong.

When identifying songs from the transcript:
- Match by **sound and rhythm**, not exact text. Read the garbled lyrics out loud if it helps.
- Look for **distinctive phrases** that survive the noise — song titles mentioned in banter, repeated choruses, unique words.
- Banter between songs transcribes much more accurately than lyrics (clean speech vs. vocals over instruments). Use banter timestamps as reliable anchor points.
- Whisper sometimes hallucinates generic filler during instrumental sections. If you see a stretch of vague, repetitive text that doesn't match any song, it's probably an instrumental break.
