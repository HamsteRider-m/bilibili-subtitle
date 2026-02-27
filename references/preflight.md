# Preflight Check Guide

## Overview

Preflight checks validate the execution environment before running the main extraction workflow.

## Usage

### Basic Check

```bash
pixi run python -m bilibili_subtitle --check
```

### JSON Output (for parent skills)

```bash
pixi run python -m bilibili_subtitle --check --check-json
```

Output:
```json
{
  "checks": [
    {"name": "BBDown", "status": "ok", "message": "Installed (1.6.3)"},
    {"name": "BBDown Auth", "status": "ok", "message": "Logged in"},
    {"name": "ffmpeg", "status": "ok", "message": "Installed"},
    {"name": "ANTHROPIC_API_KEY", "status": "warning", "message": "Not set"},
    {"name": "DASHSCOPE_API_KEY", "status": "warning", "message": "Not set"}
  ],
  "summary": {
    "can_proceed": true
  }
}
```

## Check Items

| Check | Status Impact | Required For |
|-------|---------------|--------------|
| BBDown | ERROR if missing | All operations |
| BBDown Auth | ERROR if not logged in | Video info, subtitle download |
| ffmpeg | ERROR if missing | ASR transcription |
| ANTHROPIC_API_KEY | WARNING if missing | Proofreading, summarization |
| DASHSCOPE_API_KEY | WARNING if missing | ASR transcription |

## Integration Pattern

Parent skills should run preflight checks with `--check-json` and parse the result:

```python
import subprocess
import json

result = subprocess.run(
    ["pixi", "run", "python", "-m", "bilibili_subtitle", "--check", "--check-json"],
    capture_output=True,
    text=True,
)
report = json.loads(result.stdout)

if not report["summary"]["can_proceed"]:
    # Handle fatal errors
    for check in report["checks"]:
        if check["status"] == "error":
            print(f"Fatal: {check['name']} - {check['remediation']}")
    exit(1)

# Check for optional features
has_asr = any(
    c["name"] == "DASHSCOPE_API_KEY" and c["status"] == "ok"
    for c in report["checks"]
)
```