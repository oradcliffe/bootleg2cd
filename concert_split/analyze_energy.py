import os
import subprocess
import re
import click


def analyze_energy(audio_path, output_dir):
    """Analyze audio energy levels using ffmpeg to detect likely song boundaries.

    Runs the ebur128 loudness meter and identifies significant volume dips
    that often indicate transitions between songs.

    Outputs energy.txt with:
    - Detected dips (likely boundaries) with timestamps and dB drop
    - Full loudness timeline at 1-second intervals
    """
    click.echo(f"Analyzing energy levels: {audio_path}")

    # Run ffmpeg with ebur128 filter to get momentary loudness (every 100ms)
    result = subprocess.run(
        [
            "ffmpeg",
            "-i", audio_path,
            "-af", "ebur128",
            "-f", "null",
            "-",
        ],
        capture_output=True,
        text=True,
    )

    # Parse the ebur128 output — look for momentary loudness values
    # Format: "t: X.XXX    TARGET:-23 LUFS    M: -XX.X S: -XX.X ..."
    pattern = re.compile(r"t:\s*([\d.]+)\s+.*?M:\s*(-?[\d.]+)")
    measurements = []

    for line in result.stderr.splitlines():
        match = pattern.search(line)
        if match:
            time_sec = float(match.group(1))
            momentary_lufs = float(match.group(2))
            measurements.append((time_sec, momentary_lufs))

    if not measurements:
        click.echo("Warning: No loudness measurements found. Check ffmpeg output.")
        return

    # Aggregate to 1-second intervals (take max momentary loudness per second)
    max_time = int(measurements[-1][0]) + 1
    per_second = {}
    for t, lufs in measurements:
        sec = int(t)
        if sec not in per_second or lufs > per_second[sec]:
            per_second[sec] = lufs

    seconds = sorted(per_second.keys())

    # Detect dips: find windows where loudness drops significantly
    # Use a sliding window to find transitions
    dips = find_energy_dips(seconds, per_second)

    # Write output
    energy_path = os.path.join(output_dir, "energy.txt")
    with open(energy_path, "w") as f:
        f.write(f"# Energy analysis of: {os.path.basename(audio_path)}\n")
        f.write(f"# Total duration: {format_time(max_time)}\n")
        f.write(f"# Measurements: {len(measurements)} raw, {len(seconds)} per-second\n\n")

        f.write("=" * 60 + "\n")
        f.write("DETECTED ENERGY DIPS (likely song boundaries)\n")
        f.write("=" * 60 + "\n\n")

        if dips:
            for dip in dips:
                f.write(
                    f"  {format_time(dip['start'])} - {format_time(dip['end'])}  "
                    f"({dip['drop_db']:+.1f} dB drop, {dip['duration']}s duration)\n"
                )
        else:
            f.write("  No significant dips detected.\n")
            f.write("  This concert may have very short gaps between songs.\n")

        f.write(f"\n  Total dips found: {len(dips)}\n")

        f.write("\n\n")
        f.write("=" * 60 + "\n")
        f.write("FULL LOUDNESS TIMELINE (1-second intervals, LUFS)\n")
        f.write("=" * 60 + "\n\n")

        for sec in seconds:
            f.write(f"  {format_time(sec)}  {per_second[sec]:>7.1f} LUFS\n")

    click.echo(f"Found {len(dips)} energy dips (potential song boundaries)")
    click.echo(f"Saved to: {energy_path}")
    return energy_path


def find_energy_dips(seconds, per_second, window=5, threshold_db=6.0, min_gap=10):
    """Find significant drops in loudness that likely indicate song transitions.

    Args:
        seconds: Sorted list of second timestamps
        per_second: Dict of second → LUFS value
        window: Seconds to look back/ahead for comparison
        threshold_db: Minimum dB drop to count as a dip
        min_gap: Minimum seconds between detected dips
    """
    if len(seconds) < window * 2:
        return []

    dips = []

    for i in range(window, len(seconds) - window):
        sec = seconds[i]
        current = per_second[sec]

        # Average loudness in the windows before and after
        before = [per_second[seconds[j]] for j in range(i - window, i) if seconds[j] in per_second]
        after = [per_second[seconds[j]] for j in range(i + 1, i + window + 1) if seconds[j] in per_second]

        if not before or not after:
            continue

        avg_before = sum(before) / len(before)
        avg_after = sum(after) / len(after)
        surrounding_avg = (avg_before + avg_after) / 2

        drop = surrounding_avg - current

        if drop >= threshold_db:
            # Check minimum gap from last dip
            if dips and sec - dips[-1]["end"] < min_gap:
                # If this dip is deeper, replace the previous one
                if drop > dips[-1]["drop_db"]:
                    dips[-1] = {
                        "start": sec - 2,
                        "end": sec + 2,
                        "duration": 4,
                        "drop_db": drop,
                        "lowest_lufs": current,
                    }
                continue

            dips.append({
                "start": sec - 2,
                "end": sec + 2,
                "duration": 4,
                "drop_db": drop,
                "lowest_lufs": current,
            })

    return dips


def format_time(seconds):
    """Format seconds as MM:SS."""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"
