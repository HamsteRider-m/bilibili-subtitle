from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from ..segment import Segment


Mode = Literal["noop", "anthropic"]


def default_summary() -> dict[str, Any]:
    return {
        "key_points": [],
        "outline": [],
        "entities": [],
        "timestamps": [],
    }


def load_summary_schema(schema_path: str | Path = Path("schemas/summary_schema.json")) -> dict[str, Any]:
    data = Path(schema_path).read_text(encoding="utf-8")
    return json.loads(data)


@dataclass(frozen=True, slots=True)
class SummarizeResult:
    summary: dict[str, Any]
    raw_text: str | None = None


class SummarizeAgent:
    def __init__(
        self,
        *,
        mode: Mode = "anthropic",
        model: str = "claude-3-5-sonnet-latest",
        api_key: str | None = None,
    ) -> None:
        self._mode = mode
        self._model = model
        self._api_key = api_key

    def summarize(self, segments: list[Segment], *, title: str | None = None) -> SummarizeResult:
        if self._mode == "noop":
            return SummarizeResult(summary=default_summary(), raw_text=None)

        api_key = self._api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("Missing ANTHROPIC_API_KEY (or pass api_key=...).")

        try:
            from anthropic import Anthropic  # type: ignore[import-not-found]
        except Exception as e:  # pragma: no cover
            raise RuntimeError("anthropic package is required for summarization. Install: pip install anthropic") from e

        client = Anthropic(api_key=api_key)
        schema = load_summary_schema()

        transcript = [
            {"index": i, "start_ms": s.start_ms, "end_ms": s.end_ms, "text": s.text}
            for i, s in enumerate(segments)
        ]

        system = (
            "You summarize transcripts into a structured JSON object.\n"
            "Return ONLY valid JSON matching the provided JSON Schema.\n"
            "Include timestamp references using {start_ms,end_ms,segment_indices[]}.\n"
        )
        user = {
            "title": title,
            "schema": schema,
            "transcript": transcript,
        }

        msg = client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": json.dumps(user, ensure_ascii=False)}],
        )

        content = ""
        for block in msg.content:
            if getattr(block, "type", None) == "text":
                content += block.text

        text = content.strip()
        try:
            summary = json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise ValueError("Model output did not contain a JSON object.")
            summary = json.loads(text[start : end + 1])

        if not isinstance(summary, dict):
            raise ValueError("Model output was not a JSON object.")

        return SummarizeResult(summary=summary, raw_text=text)

