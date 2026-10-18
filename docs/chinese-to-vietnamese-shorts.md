# Chinese → Vietnamese YouTube Shorts (local AI)

Manual GitHub Actions workflow to transcribe Chinese speech, translate it to Vietnamese with open models, burn Vietnamese subtitles into a vertical 9:16 MP4, and provide files as a downloadable artifact. It does **not** publish to YouTube.

## Requirements / cost
- GitHub Actions enabled.
- A video committed under `input/` (`.mp4`, `.mov`, `.mkv`, or `.webm`). GitHub blocks ordinary files over 100 MB; for larger sources, use Git LFS or a smaller file.
- Models run locally on the GitHub-hosted CPU runner: faster-whisper `small` and Helsinki-NLP `opus-mt-zh-vi`. No paid API key is needed. The first run downloads model weights and may take several minutes. Quality varies with slang, overlapping speech, music, and accents.

## How to run
1. In the repository, choose **Add file → Upload files** and upload a video into `input/`, then commit it. Only upload videos you own or are authorized/licensed to reuse.
2. Open **Actions → Chinese video to Vietnamese Shorts**.
3. Click **Run workflow**, select 30 seconds (or another listed duration), and run it.
4. When complete, open the run summary and download the `vietnamese-youtube-short` artifact ZIP.
5. Review `short_vi.mp4`, `subtitles_vi.srt`, and `transcript_zh_vi.txt`; correct errors before posting.

The workflow uses the first alphabetically sorted video in `input/`. Keep only one source video there for each run. If the source is shorter than the selected duration, the output will be shorter. The first N seconds are used; the workflow does not automatically identify the most interesting segment.

## Output
- `short_vi.mp4`: H.264/AAC, 1080×1920, 9:16, burned-in Vietnamese subtitles, original audio retained.
- `subtitles_vi.srt`: editable subtitles.
- `transcript_zh_vi.txt`: Chinese transcription and Vietnamese translation for review.

## Rights
Only process videos you own or have explicit permission/licensing to reuse. Translation, cropping, and subtitles do not themselves grant copyright permission. This workflow does not scrape TikTok, bypass restrictions, or automatically publish to YouTube. Review the rights to footage, music, voices, and embedded content before publishing.
