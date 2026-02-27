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
| 前置检查 | `pixi run python -m bilibili_subtitle --check` |
| 基本提取 | `pixi run python -m bilibili_subtitle "BV1234567890"` |
| 快速模式 | `pixi run python -m bilibili_subtitle "URL" --skip-proofread --skip-summary` |
| JSON 输出 | `pixi run python -m bilibili_subtitle "URL" --json-output` |
| 双语输出 | `pixi run python -m bilibili_subtitle "URL" --output-lang zh+en` |

## 执行层级

```
┌─────────────────────────────────────────────────────────┐
│ Layer 0: Preflight Check (前置检查)                      │
│   --check → 验证 BBDown/API Keys/登录状态               │
├─────────────────────────────────────────────────────────┤
│ Layer 1: Video Detection (视频检测)                      │
│   URL → BBDown → 字幕存在性检测                         │
├─────────────────────────────────────────────────────────┤
│ Layer 2: Content Extraction (内容提取)                   │
│   有字幕 → 加载 SRT → 校对                               │
│   无字幕 → 下载音频 → ASR 转录 → 校对                    │
├─────────────────────────────────────────────────────────┤
│ Layer 3: Enhancement (增强处理)                          │
│   校对(ANTHROPIC_API_KEY) → 摘要(ANTHROPIC_API_KEY)     │
└─────────────────────────────────────────────────────────┘
```

## 前置条件检查

**必须先运行**，验证环境配置：

```bash
pixi run python -m bilibili_subtitle --check
```

输出示例：
```
✅ BBDown: Installed (1.6.3)
✅ BBDown Auth: Logged in
✅ ffmpeg: Installed
⚠️  ANTHROPIC_API_KEY: Not set (required for proofreading)
⚠️  DASHSCOPE_API_KEY: Not set (required for ASR)
✅ Python Dependencies: All installed
```

JSON 格式输出（便于父 skill 解析）：
```bash
pixi run python -m bilibili_subtitle --check --check-json
```

## 错误分级

| Code | Level | 说明 | 修复建议 |
|------|-------|------|----------|
| E001 | FATAL | BBDown 未安装 | `./install.sh` |
| E002 | FATAL | BBDown 未登录 | `BBDown login` |
| E003 | RECOVERABLE | 下载失败 | 检查 URL/网络 |
| E004 | RECOVERABLE | 无字幕 | 自动触发 ASR |
| E005 | FATAL | ASR 未配置 | 设置 DASHSCOPE_API_KEY |
| E006 | RECOVERABLE | AI 功能未配置 | 使用 --skip-* 或设置 API Key |
| E007 | FATAL | ffmpeg 未安装 | `pixi install` |
| E008 | FATAL | URL 无效 | 提供正确的 BV/URL |
| E010 | FATAL | 视频不存在 | 检查视频是否删除/私有 |

**退出码**：
- `0` - 成功
- `1` - 致命错误（FATAL）
- `2` - 可恢复错误（RECOVERABLE，部分完成）
- `3` - 部分成功（有警告）

## 作为子 Skill 的调用契约

### 标准调用

```bash
pixi run python -m bilibili_subtitle "<URL>" \
  -o /tmp/bilibili_output \
  --skip-summary \
  --json-output
```

### 成功判定

1. 退出码为 `0` 或 `2`
2. 输出目录存在 `*.transcript.md`

### JSON 输出结构

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
      "summary_json": null
    }
  },
  "warnings": [],
  "errors": []
}
```

### 父 Skill 集成示例

```python
from bilibili_subtitle import build_cli_command, ExitCode

cmd = build_cli_command(
    "BV1xxx",
    output_dir="/tmp/output",
    skip_proofread=True,
    skip_summary=True,
)
# ['pixi', 'run', 'python', '-m', 'bilibili_subtitle', 'BV1xxx', ...]
```

## 输出文件

```
output/
├── {title}.srt          # SRT 字幕
├── {title}.vtt          # VTT 字幕
├── {title}.transcript.md   # Markdown 逐字稿
├── {title}.summary.json    # 结构化摘要 (可选)
└── {title}.summary.md      # 摘要 Markdown (可选)
```

## API Keys

| Key | Provider | 用途 | 必需性 |
|-----|----------|------|--------|
| `ANTHROPIC_API_KEY` | Anthropic | 校对/摘要 | 推荐 |
| `DASHSCOPE_API_KEY` | 阿里云 | ASR 转录 | 无字幕时必需 |

## 安装

```bash
cd ~/.agents/skills/bilibili-subtitle
./install.sh
BBDown login  # 扫码登录
```

## 详细文档

- [references/preflight.md](references/preflight.md) - 前置检查详解
- [references/errors.md](references/errors.md) - 错误处理指南
- [references/contract.md](references/contract.md) - 子 Skill 契约
- [references/agents.md](references/agents.md) - AI Agent 配置

---

**版本**: v0.2.0