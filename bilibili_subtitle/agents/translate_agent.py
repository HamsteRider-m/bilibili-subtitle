from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Literal

from ..segment import Segment


Mode = Literal["noop", "anthropic"]


def _extract_json_array(text: str) -> Any:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Model output did not contain a JSON array.")
    return json.loads(text[start : end + 1])


@dataclass(frozen=True, slots=True)
class TranslateResult:
    segments: list[Segment]
    raw_text: str | None = None


class TranslateAgent:
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

    def translate_segments(self, segments: list[Segment]) -> list[Segment]:
        return self.translate(segments).segments

    def translate(self, segments: list[Segment]) -> TranslateResult:
        if self._mode == "noop":
            return TranslateResult(segments=segments, raw_text=None)

        api_key = self._api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("Missing ANTHROPIC_API_KEY (or pass api_key=...).")

        try:
            from anthropic import Anthropic  # type: ignore[import-not-found]
        except Exception as e:  # pragma: no cover
            raise RuntimeError("anthropic package is required for translation. Install: pip install anthropic") from e

        client = Anthropic(api_key=api_key)

        payload = [
            {"index": i, "start_ms": s.start_ms, "end_ms": s.end_ms, "text": s.text}
            for i, s in enumerate(segments)
        ]

        system = (
            "Translate Chinese subtitles to natural English.\n"
            "Rules:\n"
            "- Do NOT change timestamps.\n"
            "- Do NOT add or remove segments.\n"
            "- Output ONLY a JSON array: {\"index\": number, \"text\": string}.\n"
        )
        user = "Translate these segments to English:\n\n" + json.dumps(payload, ensure_ascii=False)

        msg = client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
        )

        content = ""
        for block in msg.content:
            if getattr(block, "type", None) == "text":
                content += block.text

        items = _extract_json_array(content)
        if not isinstance(items, list):
            raise ValueError("Model output was not a JSON array.")

        translated_by_index: dict[int, str] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            idx = item.get("index")
            text = item.get("text")
            if isinstance(idx, int) and isinstance(text, str):
                translated_by_index[idx] = text

        out: list[Segment] = []
        for i, seg in enumerate(segments):
            text = translated_by_index.get(i, seg.text)
            out.append(Segment(start_ms=seg.start_ms, end_ms=seg.end_ms, text=text))

        return TranslateResult(segments=out, raw_text=content.strip())

