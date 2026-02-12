import os
import subprocess
import click


def download_audio(url, output_dir):
    """Download best-quality audio from a YouTube URL as FLAC.

    Also saves the video description to description.txt.
    Returns the path to the downloaded audio file.
    """
    audio_path = os.path.join(output_dir, "concert.flac")

    # Download best audio, extract to FLAC
    click.echo(f"Downloading audio from: {url}")
    subprocess.run(
        [
            "yt-dlp",
            "-x",
            "--audio-format", "flac",
            "--audio-quality", "0",
            "-o", audio_path,
            "--no-playlist",
            url,
        ],
        check=True,
    )
    click.echo(f"Audio saved to: {audio_path}")

    # Save video description for reference
    desc_path = os.path.join(output_dir, "description.txt")
    click.echo("Saving video description...")
    result = subprocess.run(
        ["yt-dlp", "--skip-download", "--print", "description", url],
        capture_output=True,
        text=True,
    )
    with open(desc_path, "w") as f:
        f.write(result.stdout)
    click.echo(f"Description saved to: {desc_path}")

    # Save video title too
    result = subprocess.run(
        ["yt-dlp", "--skip-download", "--print", "title", url],
        capture_output=True,
        text=True,
    )
    title_path = os.path.join(output_dir, "title.txt")
    with open(title_path, "w") as f:
        f.write(result.stdout.strip())

    # Download comments — fans often post track breakdowns and timestamps
    comments_path = os.path.join(output_dir, "comments")
    click.echo("Downloading YouTube comments...")
    subprocess.run(
        [
            "yt-dlp",
            "--skip-download",
            "--write-info-json",
            "--write-comments",
            "-o", comments_path,
            url,
        ],
        check=True,
    )
    click.echo(f"Comments saved to: {comments_path}.info.json")

    return audio_path
