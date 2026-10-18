#!/usr/bin/env python3
"""Create a 9:16 Chinese-to-Vietnamese short with locally-run open models."""
import os
import re
import subprocess
from pathlib import Path

from faster_whisper import WhisperModel
from transformers import pipeline

ROOT = Path.cwd()
INPUT = Path(os.environ.get("INPUT_VIDEO", ""))
SECONDS = max(1, min(60, int(os.environ.get("OUTPUT_SECONDS", "30"))))
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)


def run(cmd):
    print("+", " ".join(map(str, cmd)), flush=True)
    subprocess.run(list(map(str, cmd)), check=True)


def ffprobe_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True)
    return max(0.1, float(result.stdout.strip()))


def srt_time(seconds):
    ms = max(0, int(seconds * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def clean_text(text):
    return re.sub(r"\s+", " ", text or "").strip()


def main():
    if not INPUT.is_file():
        raise SystemExit(f"Input video not found: {INPUT}")
    duration = min(SECONDS, ffprobe_duration(INPUT))
    print(f"Input: {INPUT}; processing first {duration:.1f}s")

    # CPU inference; no paid transcription/translation API is used.
    asr = WhisperModel("small", device="cpu", compute_type="int8")
    segments, info = asr.transcribe(
        str(INPUT), language="zh", task="transcribe",
        vad_filter=True, beam_size=3, word_timestamps=False)
    zh_segments = []
    for seg in segments:
        start = max(0.0, float(seg.start))
        end = min(duration, float(seg.end))
        text = clean_text(seg.text)
        if start >= duration:
            break
        if text and end > start:
            zh_segments.append((start, end, text))
    if not zh_segments:
        raise SystemExit("No Chinese speech detected. Check that the video has audible Chinese speech.")

    print("Loading local Chinese-to-Vietnamese translation model...")
    translator = pipeline("translation", model="Helsinki-NLP/opus-mt-zh-vi", device=-1)
    translated = []
    for start, end, zh in zh_segments:
        try:
            result = translator(zh, max_length=256)
            vi = clean_text(result[0]["translation_text"])
        except Exception as exc:
            print(f"Translation warning at {start:.2f}s: {exc}")
            vi = ""
        if not vi:
            vi = "[Cần kiểm tra bản dịch]"
        translated.append((start, end, zh, vi))

    srt_path = OUT / "subtitles_vi.srt"
    with srt_path.open("w", encoding="utf-8-sig") as f:
        for i, (start, end, _, vi) in enumerate(translated, 1):
            f.write(f"{i}\n{srt_time(start)} --> {srt_time(end)}\n{vi}\n\n")

    txt_path = OUT / "transcript_zh_vi.txt"
    with txt_path.open("w", encoding="utf-8") as f:
        for start, end, zh, vi in translated:
            f.write(f"[{start:06.2f}-{end:06.2f}] 中文: {zh}\n")
            f.write(f"                  VI: {vi}\n\n")

    # Blurred background keeps landscape footage legible in 9:16 format.
    video_filter = (
        "split=2[bg][fg];"
        "[bg]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,boxblur=28:2,eq=brightness=-0.10[blur];"
        "[fg]scale=1080:1920:force_original_aspect_ratio=decrease[front];"
        "[blur][front]overlay=(W-w)/2:(H-h)/2,"
        "subtitles=output/subtitles_vi.srt:force_style="
        "'FontName=Noto Sans,FontSize=20,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00151515,BorderStyle=1,Outline=2,Shadow=0,"
        "Alignment=2,MarginV=100'"
    )
    out_video = OUT / "short_vi.mp4"
    run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "warning",
        "-i", INPUT, "-t", f"{duration:.3f}", "-vf", video_filter,
        "-map", "0:v:0", "-map", "0:a:0?",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
        "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "160k", "-af", "aresample=async=1:first_pts=0",
        "-movflags", "+faststart", "-shortest", out_video,
    ])
    print(f"Created {out_video}")
    print("Review translation and rights before uploading. This workflow does not publish to YouTube.")


if __name__ == "__main__":
    main()
