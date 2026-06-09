# Bilibili Subtitle Skill

Extract Bilibili subtitles with BBDown and render transcript outputs.

## When To Use

Use this skill when a Bilibili video already has downloadable subtitles, including Bilibili AI subtitles exposed by BBDown. This skill only extracts subtitle files exposed by BBDown.

## Commands

| Task | Command |
| --- | --- |
| Preflight | `pixi run python -m bilibili_subtitle --check` |
| JSON preflight | `pixi run python -m bilibili_subtitle --check-json` |
| Extract | `pixi run python -m bilibili_subtitle "URL" -o ./output` |
| Extract JSON | `pixi run python -m bilibili_subtitle "URL" -o ./output --json-output` |
| Select language | `pixi run python -m bilibili_subtitle "URL" --language zh-Hans -o ./output` |

## Workflow

1. Parse the Bilibili URL, BV ID, or av ID.
2. Run BBDown in subtitle-only mode.
3. Load the downloaded subtitle file.
4. Render Markdown transcript, SRT, and VTT files.
5. Optionally emit JSON for parent skills.

## Outputs

```text
output/
├── {title}.transcript.md
├── {title}.srt
└── {title}.vtt
```

## JSON Contract

```bash
pixi run python -m bilibili_subtitle "URL"   -o /tmp/output   --json-output
```

The response includes `exit_code`, `output.files`, `warnings`, and `errors`.

## Dependencies

- `pixi` for the Python environment
- `BBDown` for subtitle extraction
- `gh` for installer-driven BBDown nightly downloads

## Error Handling

| Code | Level | Meaning | Remediation |
| --- | --- | --- | --- |
| E001 | FATAL | BBDown missing | Run `./install.sh` |
| E002 | FATAL | BBDown auth required | Run `BBDown login` |
| E003 | RECOVERABLE | Download failed | Check URL/network/login/language |
| E004 | RECOVERABLE | No downloadable subtitles | Try another language or video |
| E005 | FATAL | Invalid URL/ID | Provide a Bilibili URL, BV ID, or av ID |
| E006 | FATAL | Output write failed | Check output directory permissions |
| E007 | RECOVERABLE | Invalid subtitle content | Retry or inspect BBDown output |
