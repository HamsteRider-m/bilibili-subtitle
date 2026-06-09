# Preflight Check Guide

Preflight checks validate that BBDown subtitle extraction can run.

## Usage

```bash
pixi run python -m bilibili_subtitle --check
pixi run python -m bilibili_subtitle --check-json
```

## Checks

| Check | Fatal If Missing | Purpose |
| --- | --- | --- |
| BBDown | Yes | Subtitle download |
| BBDown auth | Warning by default | Restricted videos may require login |
| Output directory | Yes | Ensures outputs can be written |

## JSON Example

```json
{
  "checks": [
    {"name": "BBDown", "status": "ok", "message": "Installed"},
    {"name": "BBDown auth", "status": "warning", "message": "Login not confirmed"}
  ],
  "summary": {"can_proceed": true}
}
```

## Parent Skill Handling

```python
import json
import subprocess

result = subprocess.run(
    ["pixi", "run", "python", "-m", "bilibili_subtitle", "--check-json"],
    capture_output=True,
    text=True,
)
report = json.loads(result.stdout)
if not report["summary"]["can_proceed"]:
    raise SystemExit(1)
```
