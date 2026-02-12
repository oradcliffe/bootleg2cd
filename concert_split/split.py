import json
import os
import subprocess
import re
import click

FADE_DURATION = 0.15   # seconds — prevents clicks at cut points
TARGET_LUFS = -16.0    # album-level loudness target


def measure_loudness(audio_path):
    """Measure integrated loudness of the source audio."""
    result = subprocess.run(
        ["ffmpeg", "-i", audio_path, "-af", "loudnorm=print_format=json",
         "-f", "null", "-"],
        capture_output=True, text=True,
    )
    # loudnorm outputs a JSON block at the end of stderr
    stderr = result.stderr
    json_start = stderr.rfind("{")
    json_end = stderr.rfind("}") + 1
    if json_start >= 0 and json_end > json_start:
        data = json.loads(stderr[json_start:json_end])
        return float(data["input_i"])
    return None


def parse_timestamp(ts):
    """Parse a timestamp string to seconds.

    Accepts formats:
        "1:23.456"   → 83.456
        "01:23.456"  → 83.456
        "1:23:45.6"  → 5025.6
        "83.456"     → 83.456
        "83"         → 83.0
    """
    ts = ts.strip()

    # HH:MM:SS.mmm or MM:SS.mmm
    parts = ts.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    else:
        return float(ts)


def format_seconds(s):
    """Format seconds as HH:MM:SS.mmm for ffmpeg."""
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:06.3f}"


def split_tracks(audio_path, splits_path, artist=None, album=None, year=None):
    """Split an audio file into individual tracks based on splits.json.

    Each track is output as 16-bit 44.1kHz stereo WAV (CD-ready).
    Metadata is written as INFO chunks (not ID3 — ID3 on WAV breaks players).
    """
    with open(splits_path) as f:
        splits = json.load(f)

    tracks = splits["tracks"]
    meta_artist = artist or splits.get("artist")
    meta_album = album or splits.get("venue")
    meta_year = year or (int(splits["date"][:4]) if splits.get("date") else None)

    output_dir = os.path.join(os.path.dirname(splits_path), "tracks")
    os.makedirs(output_dir, exist_ok=True)

    click.echo(f"Splitting {len(tracks)} tracks from: {audio_path}")
    click.echo(f"Output: {output_dir}")

    # Album-level loudness normalization: measure once, apply same gain to all tracks
    click.echo("Measuring loudness for album-level normalization...")
    source_lufs = measure_loudness(audio_path)
    gain_db = None
    if source_lufs is not None:
        gain_db = TARGET_LUFS - source_lufs
        click.echo(f"  Source: {source_lufs:.1f} LUFS | Target: {TARGET_LUFS:.1f} LUFS | Gain: {gain_db:+.1f} dB")
    else:
        click.echo("  Warning: could not measure loudness, skipping normalization")

    for track in tracks:
        num = track["track"]
        title = track["title"]
        start = parse_timestamp(track["start"])
        end = parse_timestamp(track["end"])

        # Sanitize filename
        safe_title = re.sub(r'[<>:"/\\|?*]', "", title)
        filename = f"{num:02d} - {safe_title}.wav"
        output_path = os.path.join(output_dir, filename)

        click.echo(f"  [{num:02d}] {title}  ({format_seconds(start)} → {format_seconds(end)})")

        # Build audio filter chain: fades + album-level normalization
        duration = end - start
        filters = [f"afade=t=in:d={FADE_DURATION}"]
        if duration > FADE_DURATION * 2:
            fade_out_start = duration - FADE_DURATION
            filters.append(f"afade=t=out:st={fade_out_start:.3f}:d={FADE_DURATION}")
        if gain_db is not None and abs(gain_db) > 0.1:
            filters.append(f"volume={gain_db:.1f}dB")

        track_str = f"{num}/{len(tracks)}"
        cmd = [
            "ffmpeg", "-y",
            "-i", audio_path,
            "-ss", format_seconds(start),
            "-to", format_seconds(end),
            "-af", ",".join(filters),
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            "-ac", "2",
            "-metadata", f"title={title}",
        ]
        if meta_artist:
            cmd += ["-metadata", f"artist={meta_artist}"]
        if meta_album:
            cmd += ["-metadata", f"album={meta_album}"]
        if meta_year:
            cmd += ["-metadata", f"date={meta_year}"]
        cmd += ["-metadata", f"track={track_str}"]
        cmd.append(output_path)

        subprocess.run(cmd, check=True, capture_output=True)

    # Generate CUE sheet for CD-Text support when burning
    cue_name = f"{meta_artist} - {meta_album}.cue" if meta_artist and meta_album else "concert.cue"
    cue_name = re.sub(r'[<>:"/\\|?*]', "", cue_name)
    write_cue_sheet(os.path.join(output_dir, cue_name), tracks, meta_artist, meta_album)

    click.echo(f"\nDone! {len(tracks)} tracks saved to: {output_dir}")
    click.echo(f"CUE sheet: {cue_name}")


def write_cue_sheet(cue_path, tracks, artist=None, album=None):
    """Write a CUE sheet for CD burning with CD-Text metadata."""
    with open(cue_path, "w") as f:
        if artist:
            f.write(f'PERFORMER "{artist}"\n')
        if album:
            f.write(f'TITLE "{album}"\n')
        for track in tracks:
            num = track["track"]
            title = track["title"]
            safe_title = re.sub(r'[<>:"/\\|?*]', "", title)
            filename = f"{num:02d} - {safe_title}.wav"
            f.write(f'FILE "{filename}" WAVE\n')
            f.write(f"  TRACK {num:02d} AUDIO\n")
            f.write(f'    TITLE "{title}"\n')
            if artist:
                f.write(f'    PERFORMER "{artist}"\n')
            f.write(f"    INDEX 01 00:00:00\n")


