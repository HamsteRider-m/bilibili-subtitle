from __future__ import annotations

import json
from typing import Any

from ..segment import Segment


def _ms(value: Any) -> int:
    if isinstance(value, int):
        return value * 1000
    if isinstance(value, float):
        return int(round(value * 1000))
    if isinstance(value, str):
        return int(round(float(value) * 1000))
    raise TypeError("Unsupported timestamp type.")


def _normalize_text(text: Any) -> str:
    if not isinstance(text, str):
        raise TypeError("Subtitle text must be a string.")
    return " ".join(text.replace("\n", " ").split())


def json_to_segments(json_text: str) -> list[Segment]:
    payload = json.loads(json_text)

    if isinstance(payload, dict) and isinstance(payload.get("body"), list):
        items = payload["body"]
    elif isinstance(payload, list):
        items = payload
    else:
        raise ValueError("Unsupported JSON subtitle format.")

    segments: list[Segment] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        start_ms = _ms(item.get("from"))
        end_ms = _ms(item.get("to"))
        text = item.get("content") or item.get("body") or item.get("text") or ""
        segments.append(Segment(start_ms=start_ms, end_ms=end_ms, text=_normalize_text(text)))

    return segments

