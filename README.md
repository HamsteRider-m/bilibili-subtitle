# bilibili-subtitle

Bilibili 字幕提取 Skill，支持：

- 优先下载原生字幕/AI 字幕
- 无字幕时自动走音频下载 + ASR 转录
- 输出 SRT / VTT / Markdown transcript / 结构化摘要

该仓库可独立使用，也可作为上层编排器（如 `anything-to-notebooklm`）的子 Skill。

## Quick Start

```bash
# Claude Code
# git clone https://github.com/HamsteRider-m/bilibili-subtitle.git ~/.claude/skills/bilibili-subtitle

# Codex/Agents
git clone https://github.com/HamsteRider-m/bilibili-subtitle.git ~/.agents/skills/bilibili-subtitle
cd ~/.agents/skills/bilibili-subtitle

# 一键安装（pixi + Python 依赖 + BBDown/ffmpeg 检查）
./install.sh
```

首次使用前：

```bash
BBDown login
```

安装后自检：

```bash
pixi run python -m bilibili_subtitle --help
pixi run python -m bilibili_subtitle "BV1xx411c7mD" --skip-proofread --skip-summary -o ./output
```

## 依赖说明

| 依赖 | 用途 | 是否必须 |
|---|---|---|
| pixi | 固定 Python/工具环境 | 是 |
| BBDown | B站元信息/字幕/音频抓取 | 是 |
| ffmpeg | 音频格式转换（ASR 路径） | 是 |
| `DASHSCOPE_API_KEY` | 无字幕视频时的 ASR | 条件必须 |
| `ANTHROPIC_API_KEY` | 校对与摘要 | 可选 |

说明：

- 如果不需要 LLM 校对/摘要，可加 `--skip-proofread --skip-summary`
- 如果视频本身有字幕，可不配置 `DASHSCOPE_API_KEY`

## CLI 用法

```bash
pixi run python -m bilibili_subtitle "URL_OR_BVID" [options]
```

常用参数：

- `-o, --output-dir` 输出目录（默认 `./output`）
- `--output-lang` `zh` / `en` / `zh+en`
- `--skip-proofread` 跳过校对
- `--skip-summary` 跳过摘要
- `--cache-dir` 缓存目录（默认 `./.cache`）
- `-v, --verbose` 打印详细日志

## 输出文件

- `{video_id}.zh.srt`
- `{video_id}.zh.vtt`
- `{video_id}.transcript.md`
- `{video_id}.summary.json`（未跳过摘要时）
- `{video_id}.summary.md`（未跳过摘要时）

## 作为子 Skill 被调用（集成契约）

推荐父 Skill 按以下契约调用：

- 输入：Bilibili URL 或 BV ID
- 命令：`pixi run python -m bilibili_subtitle "<url-or-bv>" -o /tmp --skip-summary`
- 成功条件：退出码 `0` 且输出目录存在 `*.transcript.md`
- 主产物：`{video_id}.transcript.md`

建议父 Skill：

- 把本 Skill 当作可选能力（没装就降级，不要中断全流程）
- 只依赖命令与输出文件，不耦合内部 Python 模块

## 常见问题

- `command not found: BBDown`
  - 重新执行 `./install.sh`
  - 或手动安装：`https://github.com/nilaoda/BBDown/releases`
- `Missing DASHSCOPE_API_KEY`
  - 仅在无字幕视频且需要转录时出现
- `Missing ANTHROPIC_API_KEY`
  - 设置 Key，或使用 `--skip-proofread --skip-summary`

## License

MIT
