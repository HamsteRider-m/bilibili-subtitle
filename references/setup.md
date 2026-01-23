# Setup Guide

## Prerequisites

- **BBDown**: Download from https://github.com/nilaoda/BBDown/releases
- **ffmpeg**: Required for audio transcription path

## API Keys

| Key | Provider | Purpose |
|-----|----------|---------|
| `DASHSCOPE_API_KEY` | [Aliyun DashScope](https://dashscope.console.aliyun.com/) | Audio transcription (Qwen ASR) |
| `ANTHROPIC_API_KEY` | [Anthropic](https://console.anthropic.com/) | Proofreading/translation/summarization |

**Note**: `DASHSCOPE_API_KEY` only required when video has no subtitles (ASR fallback path).

## Installation

```bash
# macOS
brew install bbdown

# Or download binary
# https://github.com/nilaoda/BBDown/releases
```

## Authentication

BBDown uses internal cookie management. Login required on first use:

```bash
BBDown login
```

Scan QR code to complete login. Cookie saved in `BBDown.data`.
