from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Literal

from ..segment import Segment


Mode = Literal["noop", "anthropic"]


def diff_segments(before: list[Segment], after: list[Segment]) -> list[dict[str, Any]]:
    if len(before) != len(after):
        raise ValueError("diff_segments requires equal-length segment lists.")

    changes: list[dict[str, Any]] = []
    for i, (b, a) in enumerate(zip(before, after, strict=True)):
        if (b.start_ms, b.end_ms) != (a.start_ms, a.end_ms):
            raise ValueError("diff_segments requires timestamps to be unchanged.")
        if b.text != a.text:
            changes.append({"index": i, "before": b.text, "after": a.text})
    return changes


def _extract_json_array(text: str) -> Any:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Tolerate code fences / extra prose.
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Model output did not contain a JSON array.")
    return json.loads(text[start : end + 1])


@dataclass(frozen=True, slots=True)
class ProofreadResult:
    segments: list[Segment]
    changes: list[dict[str, Any]]


class ProofreadAgent:
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

    def proofread_segments(self, segments: list[Segment]) -> list[Segment]:
        return self.proofread(segments).segments

    def proofread(self, segments: list[Segment]) -> ProofreadResult:
        if self._mode == "noop":
            return ProofreadResult(segments=segments, changes=[])

        api_key = self._api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("Missing ANTHROPIC_API_KEY (or pass api_key=...).")

        try:
            from anthropic import Anthropic  # type: ignore[import-not-found]
        except Exception as e:  # pragma: no cover
            raise RuntimeError("anthropic package is required for proofreading. Install: pip install anthropic") from e

        client = Anthropic(api_key=api_key)

        payload = [
            {"index": i, "start_ms": s.start_ms, "end_ms": s.end_ms, "text": s.text}
            for i, s in enumerate(segments)
        ]

        system = (
            "You are a subtitle proofreader for Chinese content.\n"
            "Rules:\n"
            "- Do NOT change start_ms/end_ms.\n"
            "- Only fix typos, punctuation, spacing, and obvious ASR errors.\n"
            "- Keep proper nouns consistent.\n"
            "- Do NOT add or remove segments.\n"
            "- Output ONLY a JSON array, each item: {\"index\": number, \"text\": string}.\n"
        )

        user = (
            "Proofread these subtitle segments. Return corrected text per index as JSON array.\n\n"
            f"{json.dumps(payload, ensure_ascii=False)}"
        )

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

        corrected_text_by_index: dict[int, str] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            idx = item.get("index")
            text = item.get("text")
            if isinstance(idx, int) and isinstance(text, str):
                corrected_text_by_index[idx] = text

        out: list[Segment] = []
        for i, seg in enumerate(segments):
            text = corrected_text_by_index.get(i, seg.text)
            out.append(Segment(start_ms=seg.start_ms, end_ms=seg.end_ms, text=text))

        return ProofreadResult(segments=out, changes=diff_segments(segments, out))

