from __future__ import annotations

from ..segment import Segment
from ._time import format_timestamp_vtt


def render_vtt(segments_zh: list[Segment], *, segments_en: list[Segment] | None = None) -> str:
    if segments_en is not None and len(segments_en) != len(segments_zh):
        raise ValueError("Bilingual output requires equal-length zh/en segment lists.")

    lines: list[str] = ["WEBVTT", ""]
    for i, zh in enumerate(segments_zh):
        if segments_en is not None:
            en = segments_en[i]
            if (en.start_ms, en.end_ms) != (zh.start_ms, zh.end_ms):
                raise ValueError("Bilingual zh/en segments must share timestamps.")
            text = f"{zh.text}\n{en.text}"
        else:
            text = zh.text

        lines.extend(
            [
                f"{format_timestamp_vtt(zh.start_ms)} --> {format_timestamp_vtt(zh.end_ms)}",
                text,
                "",
            ]
        )
    return "\n".join(lines).rstrip("\n") + "\n"

