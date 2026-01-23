# Bilibili Subtitle

从 Bilibili 视频提取字幕，支持 AI 字幕和音频转录。

## 安装

```bash
# 安装 BBDown
brew install bbdown

# 安装 Python 依赖
pip install -e .
```

## 认证

首次使用需登录 Bilibili：

```bash
BBDown login
```

扫描二维码完成登录。

## 使用

```bash
# 基本用法
python -m bilibili_subtitle "https://www.bilibili.com/video/BV1234567890/"

# 使用 BV 号
python -m bilibili_subtitle BV1234567890

# 双语输出
python -m bilibili_subtitle BV1234567890 --output-lang zh+en

# 快速提取（跳过校对和摘要）
python -m bilibili_subtitle BV1234567890 --skip-proofread --skip-summary
```

## 参数

| 参数 | 说明 |
|------|------|
| `--output-dir` | 输出目录（默认 `./output`） |
| `--output-lang` | 输出语言：`zh` / `en` / `zh+en` |
| `--skip-proofread` | 跳过 AI 校对 |
| `--skip-summary` | 跳过摘要生成 |
| `--cache-dir` | 缓存目录（默认 `./.cache`） |
| `--verbose` | 显示详细信息 |

## 输出

```
output/
├── {video_id}.zh.srt          # SRT 字幕
├── {video_id}.zh.vtt          # VTT 字幕
├── {video_id}.transcript.md   # Markdown 逐字稿
├── {video_id}.summary.json    # 结构化摘要
└── {video_id}.summary.md      # 摘要
```

## 处理流程

```
URL → BBDown 检测 → [有字幕?]
                     ├─ YES → 加载 SRT → 校对 → 输出
                     └─ NO  → 下载音频 → ASR 转录 → 校对 → 输出
```

## 环境变量

- `DASHSCOPE_API_KEY` - 音频转录（Qwen ASR）
- `ANTHROPIC_API_KEY` - AI 校对/翻译/摘要

## License

MIT
