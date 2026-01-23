---
name: bilibili-subtitle
description: Use when extracting subtitles from Bilibili videos, transcribing videos without subtitles, or generating structured summaries from video content. Triggers on Bilibili URLs (bilibili.com), BV IDs (BV1xxx), or requests to "extract subtitles from Bilibili".
---

# Bilibili Subtitle Extraction

Extract subtitles from Bilibili videos. Supports AI subtitles and falls back to ASR when unavailable.

## Setup

See [references/setup.md](references/setup.md) for prerequisites and authentication.

## Quick Start

```bash
python -m bilibili_subtitle "<URL>" [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `--output-dir DIR` | Output directory (default: `./output`) |
| `--output-lang LANG` | `zh` / `en` / `zh+en` (default: `zh`) |
| `--skip-proofread` | Skip Claude proofreading |
| `--skip-summary` | Skip summarization |
| `--cache-dir DIR` | Cache directory (default: `./.cache`) |
| `--verbose` | Show detection details |

## Outputs

```
output/
├── {video_id}.zh.srt          # SRT 字幕
├── {video_id}.zh.vtt          # VTT 字幕
├── {video_id}.transcript.md   # Markdown 逐字稿
├── {video_id}.summary.json    # 结构化摘要
└── {video_id}.summary.md      # 摘要 (Markdown)
```

## Processing Flow

```
URL → BBDown 检测/下载 → [有字幕?]
                          ├─ YES → 加载 SRT → 校对 → 输出
                          └─ NO  → 下载音频 → ASR 转录 → 校对 → 输出
```

## Examples

```bash
# 基本用法
python -m bilibili_subtitle "https://www.bilibili.com/video/BV1234567890/"

# 跳过校对和摘要（快速提取）
python -m bilibili_subtitle "BV1234567890" --skip-proofread --skip-summary

# 双语输出
python -m bilibili_subtitle "BV1234567890" --output-lang zh+en
```
