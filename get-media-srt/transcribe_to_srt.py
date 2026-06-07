# -*- coding: utf-8 -*-
"""Video/audio to SRT subtitles via faster-whisper."""
import os
import sys
from pathlib import Path

from faster_whisper import WhisperModel

# Hugging Face mirror (useful in China)
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")


def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def write_srt(segments, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        for i, segment in enumerate(segments, start=1):
            start = format_timestamp(segment.start)
            end = format_timestamp(segment.end)
            text = segment.text.strip()
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python transcribe_to_srt.py <video_or_audio> [model]")
        print("  model: tiny | base | small (default) | medium | large-v3")
        sys.exit(1)

    input_path = Path(sys.argv[1]).resolve()
    if not input_path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    model_name = sys.argv[2] if len(sys.argv) > 2 else "small"
    output_path = input_path.with_suffix(".srt")

    print(f"Loading model ({model_name}, CPU)...", flush=True)
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    print(f"Transcribing: {input_path}", flush=True)
    segments, info = model.transcribe(
        str(input_path),
        language="zh",
        beam_size=5,
        vad_filter=True,
    )
    segment_list = list(segments)
    write_srt(segment_list, output_path)
    print(f"Language: {info.language} (prob={info.language_probability:.2f})", flush=True)
    print(f"Duration: {info.duration:.1f}s", flush=True)
    print(f"Segments: {len(segment_list)}", flush=True)
    print(f"Saved: {output_path}", flush=True)


if __name__ == "__main__":
    main()