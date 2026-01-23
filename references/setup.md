# Setup Guide

## Prerequisites

- **BBDown**: Download from https://github.com/nilaoda/BBDown/releases
- **ffmpeg**: Required for audio transcription path
- **DASHSCOPE_API_KEY**: Required for audio transcription (Qwen ASR)
- **ANTHROPIC_API_KEY**: Required for proofreading/translation/summarization

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
