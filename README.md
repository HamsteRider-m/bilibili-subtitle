# bilibili-subtitle

A Claude Code Skill for extracting subtitles from Bilibili videos.

## What is a Skill?

Skills are modular packages that extend Claude Code's capabilities. This skill enables Claude to extract subtitles from Bilibili videos, with automatic fallback to ASR transcription.

## Installation

```bash
# Clone to Claude Code skills directory
git clone https://github.com/HamsteRider-m/bilibili-subtitle.git ~/.agents/skills/bilibili-subtitle
cd ~/.agents/skills/bilibili-subtitle

# Install dependencies (uses pixi for a pinned Python 3.11 environment)
./install.sh
```

### API Keys

Set these environment variables (add to `~/.zshrc` or `~/.bashrc`):

```bash
export ANTHROPIC_API_KEY="your-api-key"
export DASHSCOPE_API_KEY="your-api-key" # Optional: only needed for ASR fallback
```

### BBDown Login

```bash
BBDown login
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
├── install.sh            # Installer (pixi + dependencies)
├── pixi.toml             # Pixi environment (Python 3.11 + ffmpeg)
└── bilibili_subtitle/    # Python implementation
```

## Documentation

- **[SKILL.md](SKILL.md)** - Skill definition and quick start
- **[install.sh](install.sh)** - Environment setup and dependency install

## License

MIT
