import os
import re
import click


def format_timestamp(seconds):
    """Convert seconds to MM:SS.mmm format."""
    mins = int(seconds // 60)
    secs = seconds % 60
    return f"{mins:02d}:{secs:06.3f}"


def detect_device():
    """Auto-detect the best available device for inference."""
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        pass
    try:
        import ctranslate2
        cuda_types = ctranslate2.get_supported_compute_types("cuda")
        return "cuda" if cuda_types else "cpu"
    except Exception:
        return "cpu"


def is_hallucination(text):
    """Detect common Whisper hallucination patterns in concert audio.

    Whisper tends to produce these artifacts when it hears music
    but can't make out lyrics:
    - Music note symbols (¶¶, ♪, etc.)
    - Short repeated filler phrases ("Here we go", "Thank you", "Let's go")
    - Completely empty or whitespace-only output
    """
    cleaned = text.strip()
    if not cleaned:
        return True

    # Music note symbols and similar artifacts
    if re.fullmatch(r'[\s¶♪♫♬🎵🎶.*]+', cleaned):
        return True

    # Very short generic phrases that Whisper hallucinates during music
    hallucination_phrases = {
        "thank you", "thanks", "here we go", "let's go",
        "you", "bye", "bye-bye", "bye bye", "okay",
        "oh", "ah", "uh", "hmm", "wow",
    }
    if cleaned.lower().rstrip('.!,') in hallucination_phrases:
        return True

    return False


def is_repetitive(text, max_ratio=0.6):
    """Detect if a segment is just the same phrase repeated.

    Returns True if any single short phrase accounts for more than
    max_ratio of the total words (e.g., "oh yeah" repeated 10 times).
    """
    words = text.lower().split()
    if len(words) < 6:
        return False

    # Check 2-grams and 3-grams for excessive repetition
    for n in (2, 3):
        if len(words) < n * 3:
            continue
        ngrams = [' '.join(words[i:i+n]) for i in range(len(words) - n + 1)]
        from collections import Counter
        counts = Counter(ngrams)
        most_common_count = counts.most_common(1)[0][1]
        # If one n-gram appears in more than max_ratio of possible positions
        if most_common_count / len(ngrams) > max_ratio:
            return True

    return False


def transcribe_audio(audio_path, output_dir, model="large-v3", device="auto"):
    """Transcribe a live concert recording using faster-whisper.

    Tuned for bootleg/live recordings where vocals are mixed with
    instruments and crowd noise. Key optimizations:

    - condition_on_previous_text=False prevents hallucination cascades
    - repetition_penalty + no_repeat_ngram_size fight looping output
    - VAD with low threshold filters pure instrumentals but keeps vocals
    - Post-processing removes common hallucination patterns
    """
    from faster_whisper import WhisperModel

    if device == "auto":
        device = detect_device()

    compute_type = "float16" if device == "cuda" else "int8"

    click.echo(f"Loading whisper model '{model}' on {device} ({compute_type})...")
    whisper = WhisperModel(model, device=device, compute_type=compute_type)

    click.echo(f"Transcribing: {audio_path}")
    click.echo("This may take a few minutes...")

    segments, info = whisper.transcribe(
        audio_path,
        language="en",
        beam_size=5,
        word_timestamps=True,

        # Anti-hallucination: don't let previous output prime next segment
        condition_on_previous_text=False,

        # Anti-repetition: penalize repeating tokens and block repeated phrases
        repetition_penalty=1.3,
        no_repeat_ngram_size=3,

        # Reject segments where the audio is mostly silence — likely hallucinated
        hallucination_silence_threshold=2.0,

        # Lower no-speech threshold: default 0.6 is too aggressive for vocals
        # mixed with instruments. 0.3 lets more borderline segments through.
        no_speech_threshold=0.3,

        # VAD off: Silero VAD can't detect singing over live instruments,
        # so it filters out all lyrics. We handle hallucinations via the
        # parameters above + post-processing instead.
        vad_filter=False,
    )

    transcript_path = os.path.join(output_dir, "transcript.txt")
    total_count = 0
    kept_count = 0

    with open(transcript_path, "w") as f:
        f.write(f"# Transcription of: {os.path.basename(audio_path)}\n")
        f.write(f"# Language: {info.language} (probability: {info.language_probability:.2f})\n")
        f.write(f"# Duration: {format_timestamp(info.duration)}\n")
        f.write(f"# Model: {model} | Device: {device}\n")
        f.write("#\n\n")

        for segment in segments:
            total_count += 1
            text = segment.text.strip()

            # Filter hallucinations and repetitive garbage
            if is_hallucination(text):
                continue
            if is_repetitive(text):
                continue

            start = format_timestamp(segment.start)
            end = format_timestamp(segment.end)
            f.write(f"[{start} → {end}]  {text}\n")
            kept_count += 1

            if total_count % 50 == 0:
                click.echo(f"  ...{total_count} segments processed, {kept_count} kept ({start})")

    filtered = total_count - kept_count
    click.echo(f"Transcription complete: {kept_count} segments kept, {filtered} filtered")
    click.echo(f"Saved to: {transcript_path}")
    return transcript_path
