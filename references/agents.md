# AI Agent Configuration

## Overview

This skill uses AI agents for optional enhancement features:

1. **ProofreadAgent** - Fix ASR errors, punctuation
2. **SummarizeAgent** - Generate structured summaries
3. **TranscribeAgent** - ASR for videos without subtitles

## API Keys

| Agent | Key | Environment Variable | Required For |
|-------|-----|---------------------|--------------|
| ProofreadAgent | Anthropic | `ANTHROPIC_API_KEY` | `--skip-proofread=false` |
| SummarizeAgent | Anthropic | `ANTHROPIC_API_KEY` | `--skip-summary=false` |
| TranscribeAgent (Qwen) | DashScope | `DASHSCOPE_API_KEY` | ASR fallback |
| TranscribeAgent (OpenAI) | OpenAI | `OPENAI_API_KEY` | ASR fallback (alternative) |

## Agent Details

### ProofreadAgent

**Model**: Claude 3.5 Sonnet
**Purpose**: Fix typos, punctuation, ASR errors in subtitles
**Input**: List of segments with timestamps
**Output**: Corrected segments (timestamps unchanged)

```python
from bilibili_subtitle.agents.proofread_agent import ProofreadAgent

agent = ProofreadAgent(model="claude-3-5-sonnet-latest")
result = agent.proofread(segments)
print(result.changes)  # List of corrections made
```

**Skip**: `--skip-proofread`

### SummarizeAgent

**Model**: Claude 3.5 Sonnet
**Purpose**: Generate structured summary with key points, outline, entities
**Input**: Transcript segments
**Output**: JSON summary matching `schemas/summary_schema.json`

```python
from bilibili_subtitle.agents.summarize_agent import SummarizeAgent

agent = SummarizeAgent()
result = agent.summarize(segments, title="Video Title")
print(result.summary["key_points"])
```

**Skip**: `--skip-summary`

### TranscribeAgent

**Modes**:
- `qwen` (default) - Uses Qwen ASR via DashScope
- `openai` - Uses OpenAI Whisper

```python
from bilibili_subtitle.agents.transcribe_agent import TranscribeAgent

agent = TranscribeAgent(mode="qwen", model="qwen3-asr-flash")
result = agent.transcribe("audio.wav")
print(len(result.segments))
```

## Configuration

### Environment Variables

```bash
# Required for proofreading/summarization
export ANTHROPIC_API_KEY="sk-ant-..."

# Required for ASR (when video has no subtitles)
export DASHSCOPE_API_KEY="sk-..."

# Alternative ASR backend
export OPENAI_API_KEY="sk-..."
```

### Cost Optimization

| Use Case | Recommended Flags |
|----------|-------------------|
| Bulk extraction, no AI | `--skip-proofread --skip-summary` |
| Quick check | `--skip-summary` |
| Full processing | (default) |

## Error Handling

Agents raise `RuntimeError` when API key is missing:

```python
try:
    result = agent.proofread(segments)
except RuntimeError as e:
    if "ANTHROPIC_API_KEY" in str(e):
        # Skip or prompt user
        pass
```

## Custom Models

```python
# Use different Claude model
agent = ProofreadAgent(model="claude-3-opus-latest")

# Use different Qwen ASR model
agent = TranscribeAgent(mode="qwen", model="qwen-asr-large")
```