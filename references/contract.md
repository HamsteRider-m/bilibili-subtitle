# Sub-Skill Invocation Contract

## Version: 1.0.0

## Standard Invocation

```bash
pixi run python -m bilibili_subtitle "<URL>" \
  -o /tmp/output \
  --skip-summary \
  --json-output
```

## Exit Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | SUCCESS | All outputs generated successfully |
| 1 | FATAL_ERROR | Cannot proceed, fix required |
| 2 | RECOVERABLE_ERROR | Partial success, some outputs missing |
| 3 | PARTIAL_SUCCESS | Success with warnings |

## Success Criteria

1. Exit code is 0 or 2
2. Output directory contains `*.transcript.md`

## Output Schema

```json
{
  "exit_code": 0,
  "success": true,
  "output": {
    "video_id": "BV1xxx",
    "title": "视频标题",
    "files": {
      "transcript": "/path/to/xxx.transcript.md",
      "srt": "/path/to/xxx.srt",
      "vtt": "/path/to/xxx.vtt",
      "summary_json": null,
      "summary_md": null
    }
  },
  "warnings": ["ANTHROPIC_API_KEY not set"],
  "errors": [],
  "metadata": {
    "url": "https://..."
  }
}
```

## Required Outputs

- `*.transcript.md` - Markdown transcript (always generated on success)

## Optional Outputs

- `*.srt` - SRT subtitles
- `*.vtt` - VTT subtitles  
- `*.summary.json` - Structured summary
- `*.summary.md` - Summary markdown

## Parent Skill Integration

### Python API

```python
from bilibili_subtitle import build_cli_command, run_preflight

# Build command
cmd = build_cli_command(
    "BV1xxx",
    output_dir="/tmp/output",
    skip_proofread=True,
    skip_summary=True,
)
# ['pixi', 'run', 'python', '-m', 'bilibili_subtitle', 'BV1xxx', ...]

# Check preflight
report = run_preflight(include_auth=True)
if not report.can_proceed:
    # Handle errors
    pass
```

### Shell Integration

```bash
# Run with JSON output
result=$(pixi run python -m bilibili_subtitle "$URL" --json-output -o /tmp/out)

# Parse exit code
exit_code=$?

# Check success
if [ $exit_code -eq 0 ] || [ $exit_code -eq 2 ]; then
  # Find transcript
  transcript=$(find /tmp/out -name "*.transcript.md" | head -1)
  echo "Transcript: $transcript"
fi
```

## Batch Processing Pattern

```python
import json
import subprocess
from pathlib import Path

def process_videos(urls: list[str], output_base: Path) -> dict:
    results = {}
    for url in urls:
        output_dir = output_base / url.split("/")[-1]
        result = subprocess.run(
            ["pixi", "run", "python", "-m", "bilibili_subtitle", 
             url, "-o", str(output_dir), "--json-output", "--skip-summary"],
            capture_output=True, text=True,
        )
        results[url] = json.loads(result.stdout)
    return results
```