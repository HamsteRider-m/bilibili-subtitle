# Sub-Skill Invocation Contract

## Version: 1.0.0

## Standard Invocation

```bash
pixi run python -m bilibili_subtitle "<URL>"   -o /tmp/output   --json-output
```

## Exit Codes

| Code | Meaning | Description |
| --- | --- | --- |
| 0 | SUCCESS | Transcript outputs generated |
| 1 | FATAL | Configuration or runtime error |
| 2 | RECOVERABLE | Extraction failed but caller may retry |

## Output Files

Required:

- `*.transcript.md`

Optional:

- `*.srt`
- `*.vtt`

## JSON Shape

```json
{
  "exit_code": 0,
  "output": {
    "video_id": "BV...",
    "title": "Video Title",
    "language": "zh-Hans",
    "files": {
      "transcript_md": "/tmp/output/Video.transcript.md",
      "srt": "/tmp/output/Video.srt",
      "vtt": "/tmp/output/Video.vtt"
    }
  },
  "warnings": [],
  "errors": []
}
```

## Python Helper

```python
import json
import subprocess
from pathlib import Path


def extract_subtitles(url: str, output_dir: Path) -> dict:
    result = subprocess.run(
        [
            "pixi", "run", "python", "-m", "bilibili_subtitle",
            url, "-o", str(output_dir), "--json-output",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return json.loads(result.stdout)
```
