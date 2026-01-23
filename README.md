# bilibili-subtitle

A Claude Code Skill for extracting subtitles from Bilibili videos.

## What is a Skill?

Skills are modular packages that extend Claude Code's capabilities. This skill enables Claude to extract subtitles from Bilibili videos, with automatic fallback to ASR transcription.

## Installation

```bash
# Clone to Claude Code skills directory
git clone https://github.com/HamsteRider-m/bilibili-subtitle.git ~/.claude/skills/bilibili-subtitle
```

## Usage

Once installed, Claude Code will automatically trigger this skill when you:

- Provide a Bilibili URL: `https://www.bilibili.com/video/BV1xxx`
- Mention a BV ID: `BV1234567890`
- Ask to "extract subtitles from Bilibili"

## Skill Structure

```
bilibili-subtitle/
├── SKILL.md              # Main skill definition (triggers & workflow)
├── references/
│   └── setup.md          # Prerequisites & authentication guide
└── bilibili_subtitle/    # Python implementation
```

## Documentation

- **[SKILL.md](SKILL.md)** - Skill definition and quick start
- **[references/setup.md](references/setup.md)** - Setup prerequisites and BBDown authentication

## License

MIT
