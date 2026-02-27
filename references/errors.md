# Error Handling Guide

## Error Levels

| Level | Meaning | Exit Code | Action |
|-------|---------|-----------|--------|
| FATAL | Cannot proceed | 1 | Fix before retry |
| RECOVERABLE | Degraded functionality | 2 | Proceed with warnings |
| WARNING | Non-critical | 0 | Log and continue |

## Error Codes

### FATAL Errors (Exit 1)

| Code | Error | Cause | Solution |
|------|-------|-------|----------|
| E001 | BBDownNotFoundError | BBDown not in PATH | Run `./install.sh` |
| E002 | BBDownAuthError | Not logged in to Bilibili | Run `BBDown login` |
| E005 | ASRConfigError | DASHSCOPE_API_KEY not set | Export API key |
| E007 | FFmpegNotFoundError | ffmpeg not installed | Run `pixi install` |
| E008 | InvalidURLError | Invalid BV/URL format | Provide correct URL |
| E010 | VideoNotFoundError | Video deleted/private | Check video availability |

### RECOVERABLE Errors (Exit 2)

| Code | Error | Cause | Solution |
|------|-------|-------|----------|
| E003 | BBDownDownloadError | Network/URL issue | Retry or check URL |
| E004 | NoSubtitleError | Video has no subtitles | ASR will be attempted |
| E006 | AnthropicConfigError | ANTHROPIC_API_KEY not set | Use `--skip-*` or set key |

## JSON Error Output

When using `--json-output`, errors are returned as:

```json
{
  "exit_code": 1,
  "error": {
    "code": "E002",
    "level": "fatal",
    "message": "BBDown authentication required",
    "remediation": {
      "hint": "Login to Bilibili via BBDown",
      "command": "BBDown login",
      "doc_url": null
    }
  }
}
```

## Programmatic Handling

```python
from bilibili_subtitle.errors import SkillError, exit_code_for_error

try:
    result = run_extraction(url, output_dir)
except SkillError as e:
    print(f"[{e.code}] {e.message}")
    if e.remediation:
        print(f"  → {e.remediation.hint}")
    exit(exit_code_for_error(e))
```

## Retry Strategy

| Error Level | Retry? | Wait Time |
|-------------|--------|-----------|
| FATAL | No | N/A |
| RECOVERABLE | Yes | 5-30s exponential backoff |
| WARNING | N/A | N/A |