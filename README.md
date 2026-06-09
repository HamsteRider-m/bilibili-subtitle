# bilibili-subtitle

BBDown-only Bilibili subtitle extractor. It downloads Bilibili subtitles with BBDown and renders transcript outputs for downstream skills or local use.

## Features

- Parse Bilibili URLs, BV IDs, and av IDs
- Download regular or AI subtitles via BBDown
- Render Markdown transcript, SRT, and VTT outputs
- Provide JSON output for parent-skill invocation
- Run preflight checks for BBDown and login state

## Install

```bash
git clone https://github.com/HamsteRider-m/bilibili-subtitle.git
cd bilibili-subtitle
./install.sh
```

The installer prepares the pixi/Python environment and installs the latest BBDown nightly build via `gh`.

## Usage

```bash
pixi run python -m bilibili_subtitle "BV1xx411c7mD" -o ./output
pixi run python -m bilibili_subtitle "https://www.bilibili.com/video/BV..." --language zh-Hans --json-output
pixi run python -m bilibili_subtitle --check
pixi run python -m bilibili_subtitle --check-json
```

## Requirements

| Requirement | Purpose |
| --- | --- |
| pixi | Python environment |
| BBDown | Subtitle download |
| gh CLI | Installer downloads BBDown nightly builds |
| BBDown login | Recommended for restricted videos |

Run `BBDown login` if downloads fail because of authentication or restricted access.

## Outputs

For each video, the CLI writes:

- `{title}.transcript.md`
- `{title}.srt`
- `{title}.vtt`

With `--json-output`, stdout contains the stable invocation contract including exit code, generated files, warnings, and errors.

## Parent Skill Invocation

```bash
pixi run python -m bilibili_subtitle "<URL>"   -o /tmp/output   --json-output
```

Exit codes:

- `0`: success
- `1`: fatal configuration/runtime error
- `2`: recoverable extraction error such as no downloadable subtitles

## Troubleshooting

- `BBDown not found`: run `./install.sh` and ensure `~/.local/bin` is on `PATH`
- `BBDown authentication required`: run `BBDown login`
- No subtitle files: confirm the video has downloadable subtitles or try `--language zh-Hans`
