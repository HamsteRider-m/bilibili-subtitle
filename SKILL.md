---
name: bilibili-subtitle
description: 从 Bilibili 视频提取字幕、转录无字幕视频、生成结构化摘要。触发条件：Bilibili URL (bilibili.com)、BV ID (BV1xxx)、或"提取B站字幕"等请求。
user-invocable: true
---

# Bilibili 字幕提取工具

从 Bilibili 视频提取字幕，支持 AI 字幕检测和 ASR 转录回退。

## Quick Reference

| 任务 | 命令 |
|------|------|
| 基本提取 | `pixi run python -m bilibili_subtitle "BV1234567890"` |
| 快速模式 | `pixi run python -m bilibili_subtitle "URL" --skip-proofread --skip-summary` |
| 双语输出 | `pixi run python -m bilibili_subtitle "URL" --output-lang zh+en` |
| 指定目录 | `pixi run python -m bilibili_subtitle "URL" -o ./subtitles` |

## 角色定位（可独立运行，也可做子 Skill）

- 独立使用：直接 `pixi run python -m bilibili_subtitle ...`
- 子 Skill 使用：由主编排器（例如 `anything-to-notebooklm`）调用
- 对外契约：输入 B 站 URL/BV，输出 `{video_id}.transcript.md` 等文件

## 前置条件

### 1. 安装

```bash
# Claude Code
cd ~/.claude/skills/bilibili-subtitle
./install.sh

# Codex/Agents（如使用该目录）
cd ~/.agents/skills/bilibili-subtitle
./install.sh
```

### 2. 外部工具

| 工具 | 用途 | 安装 |
|------|------|------|
| BBDown | 视频信息/字幕下载 | `./install.sh` 自动检查/安装 |
| ffmpeg | 音频转换 | `pixi` 环境内提供 |

### 3. API Keys

| Key | Provider | 用途 |
|-----|----------|------|
| `ANTHROPIC_API_KEY` | [Anthropic](https://console.anthropic.com/) | 校对/翻译/摘要 |
| `DASHSCOPE_API_KEY` | [阿里云 DashScope](https://dashscope.console.aliyun.com/) | ASR 转录（仅无字幕时需要） |

```bash
# 添加到 ~/.zshrc
export ANTHROPIC_API_KEY="your-key"
export DASHSCOPE_API_KEY="your-key"  # 可选
```

### 4. BBDown 认证

```bash
BBDown login  # 扫码登录，Cookie 保存在 BBDown.data
```

### 5. 安装后自检

```bash
pixi run python -m bilibili_subtitle --help
pixi run python -m bilibili_subtitle "BV1xx411c7mD" --skip-proofread --skip-summary -o ./output
```

## 触发方式

- `/bilibili-subtitle [URL]`
- "提取这个B站视频的字幕 [URL]"
- "把这个视频转成文字 BV1234567890"
- "生成这个视频的摘要 [URL]"

## CLI 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `url` | Bilibili URL 或 BV ID | 必填 |
| `--output-dir, -o` | 输出目录 | `./output` |
| `--output-lang` | 输出语言 `zh`/`en`/`zh+en` | `zh` |
| `--skip-proofread` | 跳过校对 | false |
| `--skip-summary` | 跳过摘要 | false |
| `--cache-dir` | 缓存目录 | `./.cache` |
| `--verbose, -v` | 详细输出 | false |

## 输出文件

```
output/
├── {video_id}.zh.srt          # SRT 字幕
├── {video_id}.zh.vtt          # VTT 字幕
├── {video_id}.transcript.md   # Markdown 逐字稿
├── {video_id}.summary.json    # 结构化摘要
└── {video_id}.summary.md      # 摘要 (Markdown)
```

## 处理流程

```
URL → BBDown 检测 → [有字幕?]
                     ├─ YES → 加载 SRT → 校对 → 输出
                     └─ NO  → 下载音频 → ASR 转录 → 校对 → 输出
```

## 作为子 Skill 的调用契约

父 Skill 推荐执行：

```bash
pixi run python -m bilibili_subtitle "<URL或BV>" -o /tmp --skip-summary
```

成功判定：

- 退出码为 `0`
- 输出目录存在 `*.transcript.md`

## 错误处理

### 1. BBDown 未安装
- **错误**: `command not found: BBDown`
- **原因**: BBDown 未安装或不在 PATH 中
- **解决**: 重新运行 `./install.sh` 或手动安装 BBDown

### 2. BBDown 认证失败
- **错误**: `需要登录` 或下载失败
- **原因**: Cookie 过期或未登录
- **解决**: 运行 `BBDown login` 重新扫码

### 3. ASR 转录失败
- **错误**: `Missing DASHSCOPE_API_KEY`
- **原因**: 视频无字幕且未配置 DashScope
- **解决**: 设置 `DASHSCOPE_API_KEY` 环境变量

### 4. 校对/摘要失败
- **错误**: `Missing ANTHROPIC_API_KEY`
- **原因**: 未配置 Anthropic API
- **解决**: 设置 `ANTHROPIC_API_KEY` 或使用 `--skip-proofread --skip-summary`

## 示例

### 基本用法

```bash
pixi run python -m bilibili_subtitle "https://www.bilibili.com/video/BV1234567890/"
```

### 快速提取（跳过 AI 处理）

```bash
pixi run python -m bilibili_subtitle "BV1234567890" --skip-proofread --skip-summary -v
```

### 双语输出

```bash
pixi run python -m bilibili_subtitle "BV1234567890" --output-lang zh+en
```

---

**版本**: v0.1.0
