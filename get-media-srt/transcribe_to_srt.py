# -*- coding: utf-8 -*-
"""Video/audio to SRT subtitles via SenseVoice (FunASR)."""
import os
import re
import sys
from pathlib import Path

# Hugging Face mirror (useful in China)
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

SENTENCE_END = set("。！？；")
CLAUSE_END = set("，、")
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".mp4", ".mkv", ".avi"}


def format_timestamp(ms):
    hours = ms // 3600000
    minutes = (ms % 3600000) // 60000
    secs = (ms % 60000) // 1000
    millis = ms % 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def clean_text(text):
    text = re.sub(r"<\|[^|]*\|>", "", text).strip()
    return text.lstrip("，、")


def write_srt(segments, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        for i, segment in enumerate(segments, start=1):
            start = format_timestamp(segment["start"])
            end = format_timestamp(segment["end"])
            text = segment["text"]
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")


def segments_from_sentence_info(result):
    segments = []
    for seg in result["sentence_info"]:
        text = clean_text(seg.get("text", ""))
        if text:
            segments.append(
                {
                    "start": seg.get("start", 0),
                    "end": seg.get("end", 0),
                    "text": text,
                }
            )
    return segments


def segments_from_words(words, timestamps, max_chars=36):
    segments = []
    buf = []
    buf_ts = []

    for word, ts in zip(words, timestamps):
        if not ts or not isinstance(ts, (list, tuple)) or len(ts) < 2:
            continue
        buf.append(word)
        buf_ts.append(ts)
        text = "".join(buf)
        if word in SENTENCE_END or (
            word in CLAUSE_END and len(text) >= max_chars
        ) or len(text) >= max_chars * 2:
            segments.append(
                {
                    "start": buf_ts[0][0],
                    "end": buf_ts[-1][1],
                    "text": text.strip(),
                }
            )
            buf = []
            buf_ts = []

    if buf:
        text = "".join(buf).strip()
        if text:
            segments.append(
                {
                    "start": buf_ts[0][0],
                    "end": buf_ts[-1][1],
                    "text": text,
                }
            )
    return segments


def extract_segments(result):
    if "sentence_info" in result:
        segments = segments_from_sentence_info(result)
        if segments:
            return segments

    words = result.get("words") or []
    timestamps = result.get("timestamp") or []
    if words and timestamps:
        return segments_from_words(words, timestamps)

    text = clean_text(result.get("text", ""))
    if text:
        return [{"start": 0, "end": 0, "text": text}]
    return []


def load_model(model_name):
    from funasr import AutoModel

    print(f"Loading model ({model_name}, CPU)...", flush=True)
    return AutoModel(
        model=model_name,
        vad_model="fsmn-vad",
        vad_kwargs={"max_single_segment_time": 30000},
        device="cpu",
        disable_update=True,
    )


def transcribe_one(model, input_path):
    output_path = input_path.with_suffix(".srt")
    print(f"Transcribing: {input_path}", flush=True)
    result = model.generate(
        input=str(input_path),
        cache={},
        language="zh",
        use_itn=True,
        batch_size_s=60,
        merge_vad=True,
        merge_length_s=15,
        output_timestamp=True,
    )

    segments = extract_segments(result[0])
    if not segments:
        print("No speech detected.", file=sys.stderr)
        return False

    write_srt(segments, output_path)
    print(f"Segments: {len(segments)}", flush=True)
    print(f"Saved: {output_path}", flush=True)
    return True


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


def main():
    if len(sys.argv) < 2:
        print("Usage: python transcribe_to_srt.py <file_or_dir> [model]")
        print("  model: iic/SenseVoiceSmall (default)")
        print("  directory: skip files that already have .srt")
        sys.exit(1)

    target = Path(sys.argv[1]).resolve()
    if not target.exists():
        print(f"Error: path not found: {target}", file=sys.stderr)
        sys.exit(1)

    model_name = sys.argv[2] if len(sys.argv) > 2 else "iic/SenseVoiceSmall"
    inputs = collect_inputs(target)
    if not inputs:
        print("No files to transcribe.", flush=True)
        sys.exit(0)

    model = load_model(model_name)
    ok = 0
    for i, input_path in enumerate(inputs, start=1):
        print(f"[{i}/{len(inputs)}]", flush=True)
        if transcribe_one(model, input_path):
            ok += 1

    print(f"Done: {ok}/{len(inputs)} files", flush=True)


if __name__ == "__main__":
    main()
