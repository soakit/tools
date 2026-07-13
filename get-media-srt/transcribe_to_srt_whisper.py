# -*- coding: utf-8 -*-
"""Video/audio to SRT subtitles via faster-whisper."""
import os
import sys
from pathlib import Path

# Hugging Face mirror (useful in China) - MUST be set before importing faster_whisper
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from faster_whisper import WhisperModel


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


def get_device_and_compute_type():
    device = "cuda"
    compute_type = "float16"

    try:
        import torch
        if not torch.cuda.is_available():
            device = "cpu"
    except ImportError:
        try:
            import ctranslate2
            if ctranslate2.get_cuda_device_count() == 0:
                device = "cpu"
        except ImportError:
            device = "cpu"

    if device == "cpu":
        compute_type = "int8"

    return device, compute_type


AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".mp4", ".mkv", ".avi"}


def collect_inputs(path, skip_existing=True):
    path = path.resolve()
    if path.is_file():
        return [path]

    files = sorted(
        p for p in path.iterdir()
        if p.is_file() and p.suffix.lower() in AUDIO_EXTS
    )
    if skip_existing:
        files = [p for p in files if not p.with_suffix(".srt").exists()]
    return files


def transcribe_one(model, input_path):
    output_path = input_path.with_suffix(".srt")
    print(f"Transcribing: {input_path}", flush=True)
    try:
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
        return True
    except Exception as e:
        print(f"Error transcribing {input_path}: {e}", file=sys.stderr)
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python transcribe_to_srt_whisper.py <file_or_dir> [model]")
        print("  model: tiny | base | small | medium | large-v3 (default)")
        print("  directory: skip files that already have .srt")
        sys.exit(1)

    target = Path(sys.argv[1]).resolve()
    if not target.exists():
        print(f"Error: path not found: {target}", file=sys.stderr)
        sys.exit(1)

    model_name = sys.argv[2] if len(sys.argv) > 2 else "large-v3"
    inputs = collect_inputs(target)
    if not inputs:
        print("No files to transcribe.", flush=True)
        sys.exit(0)

    device, compute_type = get_device_and_compute_type()
    print(f"Loading model ({model_name}, {device}, {compute_type})...", flush=True)
    model = WhisperModel(model_name, device=device, compute_type=compute_type)

    ok = 0
    for i, input_path in enumerate(inputs, start=1):
        print(f"[{i}/{len(inputs)}]", flush=True)
        if transcribe_one(model, input_path):
            ok += 1

    print(f"Done: {ok}/{len(inputs)} files", flush=True)


if __name__ == "__main__":
    main()