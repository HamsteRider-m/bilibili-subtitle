---
name: bilibili-subtitle-extraction
description: Use when you need to extract Bilibili video subtitles (BV/av/URL), generate SRT/VTT/Markdown transcripts, and optionally proofread/translate/summarize with Claude.
---

# Bilibili Subtitle Extraction

## Overview

This skill extracts subtitles from Bilibili videos via `yt-dlp`. If no subtitles are available, it can fall back to audio transcription (requires `ffmpeg` and an ASR provider).

## Safety / Compliance

- Do not bypass paywalls or DRM.
- Only use user-provided authentication (`--cookies-*`) when required.
- Avoid bulk scraping; handle rate limits responsibly.

## How to Run

From this repo root:

```bash
python -m bilibili_subtitle "<bilibili_url_or_bv_or_av>" --output-dir ./output --verbose
```

Common options:

- `--cookies-from-browser chrome|firefox|safari`
- `--cookies-file /path/to/cookies.txt`
- `--skip-proofread` / `--skip-summary`
- `--output-lang zh|en|zh+en`
- `--cache-dir ./.cache`

## Outputs

Writes to `--output-dir`:

- `{video_id}.zh.srt`, `{video_id}.zh.vtt`
- `{video_id}.transcript.md`
- `{video_id}.summary.json`, `{video_id}.summary.md` (unless `--skip-summary`)
- If `--output-lang zh+en`: `{video_id}.zh+en.srt` and bilingual transcript

## Notes

- Proofreading/translation/summarization require `ANTHROPIC_API_KEY`.
- Audio transcription fallback currently uses OpenAI Whisper API and requires `OPENAI_API_KEY`.

