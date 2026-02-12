import click
import os

from concert_split.download import download_audio
from concert_split.transcribe import transcribe_audio
from concert_split.analyze_energy import analyze_energy
from concert_split.split import split_tracks


@click.group()
def cli():
    """Bootleg concert splitter — download, transcribe, analyze, and split live recordings."""
    pass


@cli.command()
@click.option("--url", required=True, help="YouTube video URL")
@click.option("--output", required=True, help="Output directory for this concert")
def download(url, output):
    """Download best-quality audio from a YouTube video."""
    os.makedirs(output, exist_ok=True)
    download_audio(url, output)


@cli.command()
@click.option("--input", "input_file", required=True, help="Path to audio file (FLAC/WAV)")
@click.option("--model", default="large-v3", help="Whisper model size (default: large-v3)")
@click.option("--device", default="auto", help="Device: auto, cuda, or cpu")
def transcribe(input_file, model, device):
    """Transcribe audio with timestamps using Whisper."""
    output_dir = os.path.dirname(input_file)
    transcribe_audio(input_file, output_dir, model=model, device=device)


@cli.command()
@click.option("--input", "input_file", required=True, help="Path to audio file (FLAC/WAV)")
def analyze(input_file):
    """Analyze audio energy levels to detect song boundaries."""
    output_dir = os.path.dirname(input_file)
    analyze_energy(input_file, output_dir)


@cli.command()
@click.option("--input", "input_file", required=True, help="Path to source audio file")
@click.option("--splits", required=True, help="Path to splits.json")
@click.option("--artist", default=None, help="Artist name for metadata")
@click.option("--album", default=None, help="Album/show name for metadata")
@click.option("--year", default=None, type=int, help="Year for metadata")
def split(input_file, splits, artist, album, year):
    """Split audio into individual tracks from a splits.json file."""
    split_tracks(input_file, splits, artist=artist, album=album, year=year)


@cli.command()
@click.option("--url", required=True, help="YouTube video URL")
@click.option("--output", required=True, help="Output directory for this concert")
@click.option("--model", default="large-v3", help="Whisper model size")
@click.option("--device", default="auto", help="Device: auto, cuda, or cpu")
def run(url, output, model, device):
    """Run the full pipeline: download, transcribe, and analyze.

    After this completes, review transcript.txt and energy.txt,
    then create splits.json and run 'concert-split split' to cut tracks.
    """
    os.makedirs(output, exist_ok=True)

    click.echo("=== Step 1/3: Downloading audio ===")
    audio_file = download_audio(url, output)

    click.echo("\n=== Step 2/3: Transcribing with Whisper ===")
    transcribe_audio(audio_file, output, model=model, device=device)

    click.echo("\n=== Step 3/3: Analyzing energy levels ===")
    analyze_energy(audio_file, output)

    click.echo(f"\n=== Done! ===")
    click.echo(f"Output directory: {output}")
    click.echo(f"  transcript.txt  — timestamped transcription")
    click.echo(f"  energy.txt      — volume analysis with detected dips")
    click.echo(f"\nNext steps:")
    click.echo(f"  1. Review transcript.txt and energy.txt")
    click.echo(f"  2. Create splits.json with track boundaries")
    click.echo(f"  3. Run: concert-split split --input {audio_file} --splits {output}/splits.json")


if __name__ == "__main__":
    cli()
