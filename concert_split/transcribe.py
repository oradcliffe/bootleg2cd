import os
import click


def format_timestamp(seconds):
    """Convert seconds to MM:SS.mmm format."""
    mins = int(seconds // 60)
    secs = seconds % 60
    return f"{mins:02d}:{secs:06.3f}"


def transcribe_audio(audio_path, output_dir, model="large-v3", device="auto"):
    """Transcribe audio using faster-whisper and write a human-readable transcript.

    Output format (transcript.txt):
        [00:00.000 → 00:04.200]  crowd noise and cheering
        [00:04.200 → 00:08.100]  alright uh this next one
        ...
    """
    from faster_whisper import WhisperModel

    # Auto-detect device
    if device == "auto":
        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            # No torch — check if ctranslate2 can see CUDA
            try:
                import ctranslate2
                device = "cuda" if "cuda" in ctranslate2.get_supported_compute_types("cuda") else "cpu"
            except Exception:
                device = "cpu"

    compute_type = "float16" if device == "cuda" else "int8"

    click.echo(f"Loading whisper model '{model}' on {device} ({compute_type})...")
    whisper = WhisperModel(model, device=device, compute_type=compute_type)

    click.echo(f"Transcribing: {audio_path}")
    click.echo("This may take a few minutes...")

    segments, info = whisper.transcribe(
        audio_path,
        beam_size=5,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters=dict(
            min_silence_duration_ms=500,
        ),
    )

    transcript_path = os.path.join(output_dir, "transcript.txt")
    segment_count = 0

    with open(transcript_path, "w") as f:
        f.write(f"# Transcription of: {os.path.basename(audio_path)}\n")
        f.write(f"# Language: {info.language} (probability: {info.language_probability:.2f})\n")
        f.write(f"# Duration: {format_timestamp(info.duration)}\n")
        f.write(f"# Model: {model} | Device: {device}\n")
        f.write("#\n\n")

        for segment in segments:
            start = format_timestamp(segment.start)
            end = format_timestamp(segment.end)
            text = segment.text.strip()
            line = f"[{start} → {end}]  {text}"
            f.write(line + "\n")
            segment_count += 1

            # Print progress every 50 segments
            if segment_count % 50 == 0:
                click.echo(f"  ...{segment_count} segments transcribed ({start})")

    click.echo(f"Transcription complete: {segment_count} segments")
    click.echo(f"Saved to: {transcript_path}")
    return transcript_path
