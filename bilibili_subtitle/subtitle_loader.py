from __future__ import annotations

from pathlib import Path

from .converters.ass_converter import ass_to_segments
from .converters.json_converter import json_to_segments
from .converters.srt_converter import srt_to_segments
from .segment import Segment


def load_segments_from_subtitle_file(path: str | Path) -> list[Segment]:
    path = Path(path)
    ext = path.suffix.lower().lstrip(".")
    text = path.read_text(encoding="utf-8", errors="replace")
    if ext == "json":
        return json_to_segments(text)
    if ext == "ass":
        return ass_to_segments(text)
    if ext == "srt":
        return srt_to_segments(text)
    raise ValueError(f"Unsupported subtitle extension: .{ext}")

